"""P0 Fase 1 · selector DATOS REALES / DATOS DEMO-SINTÉTICOS (entorno NO staging, usuario admin): nunca se mezclan; ?legacy=1 transitorio."""
import os, re, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0"); os.environ.pop("AMAZON_PRO_STAGING", None)
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
def login(pg):
    pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"http://localhost:{port}/?shell=6"); pg.wait_for_selector("#nav6", state="attached"); login(pg)
    check("fuera de staging NO hay etiqueta de staging", pg.locator("#envBanner").count() == 0)
    check("por defecto: DATOS REALES (selector, barra verde, sin datos demo)", pg.eval_on_selector("#dmode", "s=>s.value") == "real" and "DATOS REALES" in pg.inner_text("#modeBar") and pg.locator(".v6demo").count() == 0)
    check("en modo REAL no existe «Laboratorio DEMO» (no es una pestaña)", pg.locator("#subnav6 [data-sub]", has_text="Laboratorio DEMO").count() == 0 and "Laboratorio DEMO" not in pg.inner_text("#nav6"))
    pg.click('#nav6 [data-sec="ventas"]'); pg.wait_for_timeout(1000); check("Ventas (REAL) muestra la pantalla de ventas reales", pg.locator("#tab-ventas.on").count() == 1 and pg.locator("#subnav6 [data-sub]", has_text="Panel DEMO").count() == 0)
    pg.select_option("#dmode", "demo"); pg.wait_for_timeout(1500)
    check("al pasar a DEMO: barra ámbar «DATOS DEMO/SINTÉTICOS … no se mezclan con los reales»", "DATOS DEMO/SINTÉTICOS" in pg.inner_text("#modeBar") and "no se mezclan" in pg.inner_text("#modeBar"))
    pg.click('#nav6 [data-sec="adm"]'); pg.wait_for_timeout(700); check("en DEMO aparece «Administración › Laboratorio DEMO» (modo de datos, no pestaña principal) y ya no hay «Panel DEMO» en Ventas", pg.locator("#subnav6 [data-sub]", has_text="Laboratorio DEMO").count() == 1); pg.click('#nav6 [data-sec="ventas"]'); pg.wait_for_timeout(500); check("Ventas ya no contiene «Panel DEMO»", pg.locator("#subnav6 [data-sub]", has_text="Panel DEMO").count() == 0)
    pg.click('#nav6 [data-sec="hoy"]'); pg.wait_for_timeout(1500)
    check("Hoy en DEMO muestra el conjunto demo (Fase 2: bloques rotulados DEMO, aviso «no describen el negocio real») y ninguna tarjeta real; el Inicio heredado se conserva en segundo nivel", pg.locator(".v6demo").count() == 1 and pg.locator("#h2top .h2b-demo").count() >= 2 and "datos sintéticos" in pg.inner_text("#h2top").lower() and "no describen el negocio real" in pg.inner_text(".h2sit"))
    for sid, lab in (("prod", "Productos"), ("lanz", "Lanzamientos"), ("dir", "Director IA")):
        pg.click(f'#nav6 [data-sec="{sid}"]'); pg.wait_for_timeout(700)
        check(f"{lab} en DEMO: NO se muestran datos reales (guarda visible, ninguna pantalla activa)", pg.locator("#modeGuard:not([hidden])").count() == 1 and pg.locator("main.tab.on").count() == 0)
    pg.click('#nav6 [data-sec="adm"]'); pg.click('#subnav6 [data-sub="1"]'); pg.wait_for_timeout(1200)
    check("Administración › Laboratorio DEMO accesible en DEMO", pg.locator("#tab-panel.on").count() == 1 and pg.locator("#modeGuard:not([hidden])").count() == 0)
    pg.click('#nav6 [data-sec="adm"]'); pg.wait_for_timeout(800); check("Administración sigue accesible en DEMO (no es una vista de datos)", pg.locator("#modeGuard:not([hidden])").count() == 0 and pg.locator("main.tab.on").count() == 1)
    pg.click('#nav6 [data-sec="prod"]'); pg.wait_for_timeout(500); pg.click("[data-togreal]"); pg.wait_for_timeout(1500)
    check("«Cambiar a DATOS REALES» desde la guarda: vuelve a REAL y Hoy ya no contiene datos demo", pg.eval_on_selector("#dmode", "s=>s.value") == "real" and pg.locator(".v6demo").count() == 0)
    check("el modo persiste en la sesión del navegador", pg.evaluate("sessionStorage.getItem('apiMode')") == "real")
    check("sin errores de página", not errs)
    # legacy transitorio
    lg = b.new_context(viewport={"width": 1440, "height": 900}).new_page(); lg.goto(f"http://localhost:{port}/?legacy=1"); lg.wait_for_selector("#tabs"); lg.wait_for_timeout(600)
    check("?legacy=1: navegación antigua visible, sin nav nueva y con aviso de transición", lg.locator("#tabs").is_visible() and lg.locator("#nav6").count() == 0 and "se retirará en la Fase 5" in lg.inner_text(".legacybar"))
    pl = open(os.path.join(ROOT, "docs", "p0_hoy", "PLAN_RETIRADA_LEGACY.md"), encoding="utf-8").read()
    check("existe el plan de retirada de ?legacy=1 con fase concreta (Fase 5) y criterios", "Fase 5" in pl and "Criterios" in pl and "Fase de retirada" in pl)
    b.close()
print(f"\n{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
