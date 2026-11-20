"""P0 Fase 3 · LANZAMIENTOS con el selector REAL/DEMO (entorno NO staging, admin): REAL rotula REAL y SIN DATOS; DEMO jamás muestra lanzamientos/nombres reales; volver a REAL restaura; admin conserva sus controles."""
import json, os, re, sys, tempfile, threading, urllib.request, http.cookiejar
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
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
    pg.evaluate("NAV6.go('lanz',0)"); pg.wait_for_selector("#lanz2 .lzc", timeout=10000); pg.wait_for_timeout(800)
    t = pg.inner_text("#lanz2")
    check("REAL: cabecera rotulada REAL (no DEMO) y 3 lanzamientos", "REAL" in pg.inner_text("#lanz2 .h2head h2") and "DEMO" not in pg.inner_text("#lanz2 .h2head h2") and pg.locator("#lanz2 .lzc").count() == 3)
    check("REAL: pasos del expediente rotulados SIN DATOS cuando no hay dato (nunca 0)", pg.locator("#lanz2 .lzstep .h2b-nd").count() >= 5 and not re.search(r"(?<![\d.,])0([.,]00)? ?€", t))
    pg.click("#lanz2 #lzevi > summary"); check("REAL: pasos con datos del catálogo rotulados REAL", pg.locator("#lanz2 .lzstep .h2b-real").count() >= 1)
    check("REAL admin: «Preparar lanzamiento» sigue activo en la metodología (no se bloquea a quien puede escribir)", pg.evaluate("[...document.querySelectorAll('#lzlegacy button')].some(b=>/Preparar lanzamiento/.test(b.textContent)&&!b.disabled&&!b.classList.contains('vro'))"))
    pg.select_option("#dmode", "demo"); pg.wait_for_timeout(1500)
    vis = pg.inner_text("main.tab.on") if pg.locator("main.tab.on").count() else ""; body = pg.inner_text("body")
    check("DEMO: Lanzamientos no muestra datos reales (aviso de modo, sin tarjetas de producto)", pg.locator("#lanz2 .lzc:visible").count() == 0 and "Modo DATOS DEMO/SINTÉTICOS" in pg.inner_text("#modeGuard"))
    check("DEMO: ningún nombre de producto real visible en la pantalla de Lanzamientos", not any(n in vis for n in ("ACTIVCORE", "PHIVITAL")))
    pg.select_option("#dmode", "real"); pg.wait_for_timeout(1800); pg.evaluate("NAV6.go('lanz',0)"); pg.wait_for_timeout(1500)
    check("volver a REAL restaura los 3 lanzamientos", pg.locator("#lanz2 .lzc:visible").count() == 3)
    m = pg.evaluate("[scrollX, document.documentElement.scrollWidth, innerWidth]"); check(f"sin desplazamiento horizontal {m}", m[0] == 0 and m[1] <= m[2])
    check("sin errores de consola", errs == []); b.close()
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
