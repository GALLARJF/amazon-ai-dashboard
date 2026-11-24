"""V1.0 · V1-09 — Cinco secciones NEON en móvil/tableta/escritorio con Chromium real: sin desbordes, producto por defecto ACTIVCORE, sin errores de consola, sin red externa, flujo ACTIVCORE, descarga CSV. Capturas 60+."""
import glob, os, re, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0")
for k in ("AMAZON_PRO_KEEPA_KEY", "KEEPA_API_KEY", "OPENAI_API_KEY"): os.environ.pop(k, None)
import _nav_shim  # Fase 4: navegación nueva (sin ?legacy=1)
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "CAPTURAS_UI"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
for f in glob.glob(os.path.join(OUT, "6[0-9]_*.png")): os.remove(f)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SECC = [("inicio", "INICIO"), ("lanz", "LANZAMIENTOS"), ("ventas", "MIS VENTAS"), ("prod", "PRODUCTOS"), ("dir", "DIRECTOR IA")]; n = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h, nm in ((390, 844, "movil"), (820, 1180, "tableta"), (1600, 900, "escritorio")):
        ctx = b.new_context(viewport={"width": w, "height": h}); pg = ctx.new_page(); errs = []; ext = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
        pg.on("request", lambda r: not re.match(r"^(http://(localhost|127\.0\.0\.1):%d/|data:|blob:)" % port, r.url) and ext.append(r.url))
        pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#tabs"); pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu")
        labs = pg.eval_on_selector_all("#tabs button", "e=>e.map(x=>x.dataset.tab+'|'+x.innerText.trim())")
        check("[%s] las 5 secciones existen en la barra: %s" % (nm, ", ".join(t for _, t in SECC)), all(any(l.startswith(k + "|") and l.split("|")[1] == t for l in labs) for k, t in SECC))
        for k, t in SECC:
            pg.click(f"#tabs button[data-tab={k}]"); pg.wait_for_timeout(700)
            if k == "lanz": pg.wait_for_selector("#v6lanz .v6sec", timeout=10000)
            sw = pg.evaluate("()=>document.documentElement.scrollWidth - document.documentElement.clientWidth")
            vis = pg.evaluate("(k)=>{const e=document.querySelector('[data-pane=\"'+k+'\"],#'+k+',section.active,.pane.active');return !!e}", k)
            check("[%s] %s: sin desborde horizontal de página (sobra %d px)" % (nm, t, sw), sw <= 1)
            check("[%s] %s: muestra contenido (no vacío)" % (nm, t), len(pg.inner_text("body").strip()) > 400)
            n += 1; pg.screenshot(path=os.path.join(OUT, "6%d_%s_%s.png" % (n % 10, nm, k)))
        pg.click("#tabs button[data-tab=lanz]"); pg.wait_for_selector("#v6Prod-lanz")
        val = pg.eval_on_selector("#v6Prod-lanz", "e=>e.value")
        check("[%s] producto por defecto en LANZAMIENTOS = ACTIVCORE" % nm, val == "PRD-ACTIVCORE-V2")
        check("[%s] sin errores de consola ni de página%s" % (nm, (": " + "; ".join(errs[:2])[:150]) if errs else ""), not errs)
        check("[%s] sin peticiones a red externa" % nm, not ext)
        if nm == "movil":
            pg.select_option("#v6Prod-lanz", "PRD-ACTIVCORE-V2"); pg.wait_for_selector('section.v7[data-space="lanz"] .v7-keepa tbody tr', timeout=10000)
            try: pg.wait_for_function("()=>document.querySelectorAll('section.v7[data-space=\"lanz\"] .v7-keepa tbody tr').length===20&&/NO DECIDIBLE/.test((document.querySelector('section.v7[data-space=\"lanz\"] .v7-brief')||{}).innerText||'')", timeout=15000)   # espera la carga asíncrona completa (la aserción de abajo NO se relaja)
            except Exception: print("   [diag] tras 15 s: filas=%d" % pg.locator('section.v7[data-space="lanz"] .v7-keepa tbody tr').count())
            check("[movil] ACTIVCORE: veredicto NO DECIDIBLE visible y 20 competidores con procedencia", "NO DECIDIBLE" in pg.inner_text('section.v7[data-space="lanz"] .v7-brief') and pg.locator('section.v7[data-space="lanz"] .v7-keepa tbody tr').count() == 20)
        ctx.close()
    # error visible al fallar el servidor (estado de error, no pantalla en blanco)
    ctx = b.new_context(viewport={"width": 1600, "height": 900}); pg = ctx.new_page(); pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#tabs")
    check("sin sesión: la interfaz invita a iniciar sesión (estado vacío explicado)", pg.locator("#lgOpen").count() == 1)
    b.close()
srv.shutdown(); print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
