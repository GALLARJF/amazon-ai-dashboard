"""P0 Fase 1 · navegación nueva con el usuario VIEWER en staging: 6 secciones × sub-secciones, selector de datos, barra inferior Android que NO oculta contenido,
0 escrituras, capturas reales de las seis secciones en escritorio y Android (docs/p0_hoy/fase1/)."""
import glob, os, re, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "fase2", "nav"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "*.png")): os.remove(f)
SECS = [("hoy", "Hoy", ["Hoy"]), ("ventas", "Ventas", ["Mis ventas", "Indicadores"]), ("prod", "Productos", ["Catálogo", "Precio", "Competencia", "Expediente PHIVITAL"]),
        ("lanz", "Lanzamientos", ["Expediente", "Pre-Launch", "Europa · Mercados"]), ("dir", "Director IA", ["Director", "Datos del Director"]), ("adm", "Administración", ["Administración", "Laboratorio DEMO"])]
K4 = {"Indicadores": "centro", "Precio": "precio", "Competencia": "bench", "Datos del Director": "dir"}
BAR_JS = """() => { const bar = document.querySelector('#bnav'); const cs = getComputedStyle(bar); if (cs.display === 'none') return {err: 'barra oculta'};
  window.scrollTo(0, document.documentElement.scrollHeight); const top = bar.getBoundingClientRect().top; 
  const root = document.querySelector('main.tab.on') || document.querySelector('#modeGuard:not([hidden])'); if (!root) return {err: 'sin contenido'};
  const clip = (e) => { let b = e.getBoundingClientRect().bottom, p = e.parentElement; while (p && p !== document.body) { const s = getComputedStyle(p); if (/(hidden|auto|scroll|clip)/.test(s.overflowY)) { b = Math.min(b, p.getBoundingClientRect().bottom); } p = p.parentElement; } return b; };
  let maxB = 0, who = ''; root.querySelectorAll('*').forEach(e => { const r = e.getBoundingClientRect(); const st = getComputedStyle(e); if (r.width < 1 || r.height < 1 || st.visibility === 'hidden' || st.display === 'none' || st.position === 'fixed') return; const sm = e.closest('summary'), dt = (e.tagName === 'SUMMARY' ? e.parentElement.parentElement : e).closest('details:not([open])'); if (dt && !(sm && sm.parentElement === dt && !dt.parentElement.closest('details:not([open])'))) return; const bb = clip(e); if (bb > maxB) { maxB = bb; who = e.tagName + '.' + (e.className || '').toString().slice(0, 30); } });
  return {barTop: Math.round(top), maxBottom: Math.round(maxB), who, fixed: cs.position === 'fixed', scrollable: document.documentElement.scrollHeight > innerHeight}; }"""
def run(pw, name, vp, mobile):
    ctx = pw.new_context(viewport=vp, device_scale_factor=1, is_mobile=mobile, has_touch=mobile); pg = ctx.new_page(); errs = []; writes = []; ext = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.on("request", lambda r: (r.method != "GET" and not r.url.endswith(("/api/login", "/api/logout")) and writes.append((r.method, r.url))) or (not re.match(r"^(http://(localhost|127\.0\.0\.1):%d/|data:|blob:)" % port, r.url) and ext.append(r.url)))
    pg.goto(f"http://localhost:{port}/?shell=6"); pg.wait_for_selector("#nav6", state="attached")
    pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
    nav = "#bnav" if mobile else "#nav6"
    check(f"[{name}] etiqueta STAGING visible y sesión «auditor · viewer»", pg.locator("#envBanner").is_visible() and "auditor · viewer" in pg.inner_text("#sess"))
    labs = pg.eval_on_selector_all(f"{nav} [data-sec]", "e=>e.map(x=>x.textContent.trim())")
    check(f"[{name}] barra de navegación con exactamente las 6 secciones ({labs})", len(labs) == 6)
    check(f"[{name}] navegación antigua (#tabs) oculta y sin desbordamiento horizontal", not pg.locator("#tabs").is_visible() and pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    check(f"[{name}] selector de datos: REAL deshabilitado en staging, modo DEMO/SINTÉTICO activo y rotulado", pg.eval_on_selector("#dmode option[value=real]", "o=>o.disabled") and pg.eval_on_selector("#dmode", "s=>s.value") == "demo" and "DATOS FICTICIOS — NO REPRESENTAN RESULTADOS DE AHT" in pg.inner_text("#modeBar") and "DATOS DEMO/SINTÉTICOS" in pg.eval_on_selector("#dmode", "s=>s.selectedOptions[0].textContent"))
    for i, (sid, lab, subs) in enumerate(SECS, 1):
        pg.click(f'{nav} [data-sec="{sid}"]'); pg.wait_for_timeout(1300)
        for j, sl in enumerate(subs):
            if len(subs) > 1: pg.click(f'#subnav6 [data-sub="{j}"]')
            pg.wait_for_timeout(1000)
            if sl in K4:
                ok = pg.wait_for_function(f"document.querySelector('.k4views button.on') && document.querySelector('.k4views button.on').dataset.k4v==='{K4[sl]}'", timeout=8000) is not None
                check(f"[{name}] {lab} › {sl}: abre la vista K4 «{K4[sl]}» (navegación interna)", ok)
            txt = pg.inner_text("main.tab.on") if pg.locator("main.tab.on").count() else ""
            check(f"[{name}] {lab} › {sl}: pantalla visible, con contenido, sin «restringido»/undefined", len(txt) > 40 and not re.search(r"restringido|solo administrador|undefined|\[object", txt, re.I) and pg.locator("#envBanner").is_visible())
            if mobile:
                pg.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)'); pg.wait_for_timeout(500); r = pg.evaluate(BAR_JS)
                check(f"[{name}] {lab} › {sl}: la barra inferior NO oculta contenido (último elemento {r.get('maxBottom')} ≤ barra {r.get('barTop')})", "err" not in r and r["fixed"] and r["maxBottom"] <= r["barTop"] + 1)
                pg.evaluate("window.scrollTo(0,0)")
        if len(subs) > 1: pg.click('#subnav6 [data-sub="0"]'); pg.wait_for_timeout(900)
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(200)
        pg.screenshot(path=os.path.join(OUT, f"{name}_{i}_{sid}.png"), full_page=(not mobile))
        if mobile: pg.screenshot(path=os.path.join(OUT, f"{name}_{i}_{sid}_completa.png"), full_page=True)
    if mobile:   # control negativo: SIN el espacio inferior la prueba debe detectar que la barra tapa contenido (demuestra que la prueba es sensible)
        pg.click(f'{nav} [data-sec="lanz"]'); pg.wait_for_timeout(1200); pg.evaluate("document.body.style.paddingBottom='0px'"); pg.wait_for_timeout(300); pg.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)'); pg.wait_for_timeout(300)
        r0 = pg.evaluate(BAR_JS); check(f"[{name}] control negativo: sin espacio inferior la barra SÍ taparía contenido (prueba sensible: {r0.get('maxBottom')} > {r0.get('barTop')})", r0.get("maxBottom", 0) > r0.get("barTop", 0) + 1)
        pg.evaluate("document.body.style.paddingBottom=''")
    pg.click(f'{nav} [data-sec="hoy"]'); pg.wait_for_timeout(600)
    chip = pg.locator("#decChip"); check(f"[{name}] chip «Decisiones · n» visible; abre la bandeja única DECISIONES (Fase 2)", chip.is_visible() and (chip.click() or True) and pg.wait_for_function("document.querySelector('#tab-decisiones.on')", timeout=5000) is not None)
    r = pg.evaluate("fetch('/api/k4/consejero/investigar',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':window.V03.V.csrf},body:'{}'}).then(r=>r.status)"); check(f"[{name}] servidor: POST forzado del viewer → 403", r == 403)
    check(f"[{name}] sin errores de consola y sin peticiones externas", not errs and not ext)
    if errs: print(errs[:4])
    check(f"[{name}] navegar por las 6 secciones no envió ninguna escritura (solo el POST forzado, 403)", len(writes) == 1)
    ctx.close()
with sync_playwright() as p:
    b = p.chromium.launch()
    run(b, "desktop", {"width": 1440, "height": 900}, False)
    run(b, "android", {"width": 412, "height": 915}, True)
    run(b, "android360", {"width": 360, "height": 640}, True)
    b.close()
print(f"\n{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
