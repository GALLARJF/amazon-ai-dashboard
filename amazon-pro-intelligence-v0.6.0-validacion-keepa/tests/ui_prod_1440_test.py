"""Corrección 4.1 · Productos a 1440 px: scrollX=0, sin desbordamiento horizontal y borde izquierdo de las fichas completo. Captura en docs/p0_hoy/fase4_1/desktop/."""
import json, os, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "fase4_1", "desktop"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tempfile.mkdtemp(), "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(args=[], ignore_default_args=["--hide-scrollbars"]); pg = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1).new_page()
    pg.goto(f"http://localhost:{port}/?shell=6"); pg.wait_for_selector("#nav6", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
    for via in ("menú", "enlace del Director"):
        if via == "menú": pg.evaluate("NAV6.go('prod',0)")
        else:
            pg.evaluate("NAV6.go('dir',0)"); pg.wait_for_selector("#d2top .h2c", state="visible"); pg.wait_for_timeout(800); pg.click("#dir2 [data-h2prod]")
        pg.wait_for_selector("#prod2 .x4prod", state="visible"); pg.wait_for_timeout(1200)
        if via == "menú": pg.evaluate("scrollTo(0,0)")
        m = pg.evaluate("""()=>({sx:scrollX,sw:document.documentElement.scrollWidth,iw:document.documentElement.clientWidth,min:Math.min(...[...document.querySelectorAll('#prod2 .x4prod,#prod2top,#nav6')].map(e=>e.getBoundingClientRect().left)),
          sc:[...document.querySelectorAll('*')].filter(e=>e.scrollLeft>0).length,cut:[...document.querySelectorAll('#prod2 .x4prod')].filter(e=>e.getBoundingClientRect().left<1||e.getBoundingClientRect().right>document.documentElement.clientWidth).length})""")
        check(f"Productos 1440 ({via}): scrollX=0 y ningún contenedor desplazado {m['sx']}/{m['sc']}", m["sx"] == 0 and m["sc"] == 0)
        check(f"Productos 1440 ({via}): sin desbordamiento horizontal (scrollWidth {m['sw']} ≤ {m['iw']})", m["sw"] <= m["iw"])
        check(f"Productos 1440 ({via}): borde izquierdo completo (mín. left {m['min']:.0f} ≥ 0; fichas recortadas {m['cut']})", m["min"] >= 0 and m["cut"] == 0)
        if via == "menú": pg.screenshot(path=os.path.join(OUT, "prod.png"))
    json.dump(m, open(os.path.join(OUT, "prod_medidas.json"), "w"))
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
