"""STAGING · viewer en navegador real: recorre TODAS las pantallas, captura cada una, comprueba etiqueta permanente, controles de escritura bloqueados y ninguna petición de escritura. Capturas en CAPTURAS_UI/viewer/."""
import glob, json, os, re, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
import _nav_shim  # Fase 4: navegación nueva (sin ?legacy=1)
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "CAPTURAS_UI", "viewer"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "*.png")): os.remove(f)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1600, "height": 1000}); pg = ctx.new_page(); errs = []; writes = []; ext = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.on("request", lambda r: (r.method != "GET" and not r.url.endswith(("/api/login", "/api/logout")) and writes.append((r.method, r.url))) or (not re.match(r"^(http://(localhost|127\.0\.0\.1):%d/|data:|blob:)" % port, r.url) and ext.append(r.url)))
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#tabs")
    check("etiqueta STAGING visible ANTES de iniciar sesión", pg.locator("#envBanner").is_visible() and S.STAGING_LABEL in pg.inner_text("#envBanner"))
    pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1200)
    check("sesión visible como «auditor · viewer»", "auditor · viewer" in pg.inner_text("#sess"))
    tabs = pg.eval_on_selector_all("#tabs button[data-tab]", "els=>els.map(e=>[e.dataset.tab,e.textContent.trim()])")
    check(f"navegación completa: {len(tabs)} pestañas visibles y habilitadas", len(tabs) >= 12 and pg.eval_on_selector_all("#tabs button[data-tab]", "els=>els.every(e=>!e.disabled && e.offsetParent!==null)"))
    for i, (tab, name) in enumerate(tabs, 1):
        pg.click(f'#tabs button[data-tab="{tab}"]'); pg.wait_for_timeout(1500)
        txt = pg.inner_text("body")
        check(f"pantalla «{name}»: carga, etiqueta visible y sin «restringido»/«solo administrador»/undefined", pg.locator("#envBanner").is_visible() and not re.search(r"restringido|solo administrador|undefined|\[object", txt, re.I))
        pg.screenshot(path=os.path.join(OUT, f"{i:02d}_{tab}.png"), full_page=True)
    # la navegación interna de pantallas (sub-vistas) NO debe quedar bloqueada para el viewer (defecto corregido tras e914144)
    pg.click('#tabs button[data-tab="k4"]'); pg.wait_for_timeout(1500)
    nav_ok = True
    for v in ("bench", "precio", "dir", "centro"):
        nav_ok &= pg.eval_on_selector(f"[data-k4v={v}]", "e=>!e.disabled")
        pg.click(f"[data-k4v={v}]", timeout=5000); pg.wait_for_timeout(700)
    check("K4: las 4 sub-vistas (Centro, Benchmarking, Pricing, Director·Datos) son navegables para el viewer", nav_ok)
    # controles de escritura bloqueados
    pg.click('#tabs button[data-tab="k4"]'); pg.wait_for_timeout(1500)
    dis = pg.eval_on_selector_all("button:disabled.vro", "e=>e.length"); check(f"controles de escritura desactivados en la interfaz ({dis})", dis >= 1)
    r = pg.evaluate("window.V03.api('POST','/api/k4/consejero/investigar',{}).then(r=>[r.status,r.ok])"); check("cliente: api() de escritura devuelve 403 sin enviar nada", r == [403, False])
    r = pg.evaluate("fetch('/api/k4/consejero/investigar',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':window.V03.V.csrf},body:'{}'}).then(r=>r.status)"); check("servidor: fetch POST forzado desde la consola → 403", r == 403)
    r = pg.evaluate("fetch('/api/connectors/test',{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':'x'},body:'{\"name\":\"keepa\"}'}).then(r=>r.status)"); check("servidor: prueba de conector → 403", r == 403)
    check("sin errores de consola ni excepciones de página", not errs); 
    if errs: print(errs[:5])
    check("sin peticiones externas a Internet", not ext)
    check("las únicas escritura enviadas al servidor son las 2 forzadas a propósito (ambas 403)", len(writes) == 2)
    b.close()
print(f"\n{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
