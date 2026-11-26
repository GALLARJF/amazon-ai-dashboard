"""P0 Fase 2 · HOY, DECISIONES y DIRECTOR en el selector de datos (entorno NO staging, admin): REAL muestra solo lo real (SIN DATOS ≠ 0, ventas importadas como REAL);
DEMO muestra solo lo sintético y NUNCA nombres/decisiones/riesgos reales; volver a REAL restaura. Datos de prueba en una BD temporal."""
import base64, json, os, re, sys, tempfile, threading, urllib.request, http.cookiejar
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
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def call(p, b=None, csrf=""):
    r = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}); return json.loads(op.open(r).read())
csrf = call("/api/login", {"username": "admin", "password": "admin-password-123"})["csrf"]
def blocks(pg): return {b: pg.inner_text(f'[data-blk="{b}"]') for b in ("ventas", "margen", "stock", "decisiones", "prioridades")}
def badge(pg, b): return pg.inner_text(f'[data-blk="{b}"] .h2b').strip()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.goto(f"http://localhost:{port}/?shell=6"); pg.wait_for_selector("#nav6", state="attached")
    pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_selector("#h2top .h2sit", timeout=10000); pg.wait_for_timeout(1500)
    # --- REAL sin ventas importadas: nada de ceros
    B = blocks(pg)
    check("REAL (sin informes): Ventas = SIN DATOS (badge SIN DATOS), no 0 €", badge(pg, "ventas") == "SIN DATOS" and "SIN DATOS" in B["ventas"] and not re.search(r"\b0([.,]00)? €", B["ventas"]))
    check("REAL (sin informes): Margen = SIN DATOS y explica que no es un 0", badge(pg, "margen") == "SIN DATOS" and "no es un 0" in B["margen"])
    check("REAL: Stock y riesgos rotulado REAL con el desglose por criticidad", badge(pg, "stock") == "REAL" and re.search(r"\d+ riesgos abiertos: \d+ críticos · \d+ altos · \d+ medios · \d+ bajos", B["stock"]))
    check("REAL: «Importar un informe de ventas» aparece entre las prioridades (hueco de datos, no un 0)", "Importar un informe de ventas" in B["prioridades"])
    check("REAL: situación rotulada REAL", "REAL" in pg.inner_text(".h2sit h2"))
    # --- REAL con ventas importadas
    raw = "Fecha;ASIN;Ventas de productos pedidos;Unidades pedidas;Sesiones - total\n2026-10-01;B0F6KQP2WH;120,50 €;8;100\n2026-10-02;B0F6KQP2WH;80,00 €;5;60\n2026-10-03;B0F6KQP2WH;95,00 €;6;80\n".encode()
    r = call("/api/v06/import", {"product": "PRD-PHIVITAL-OMEGA3", "filename": "ventas.csv", "content_b64": base64.b64encode(raw).decode()}, csrf); call("/api/v06/order", {"product": "PRD-PHIVITAL-MAGNESIO"}, csrf)
    pg.evaluate("NAV6.go('adm',0)"); pg.wait_for_timeout(400); pg.evaluate("NAV6.go('hoy',0)"); pg.wait_for_timeout(1800); B = blocks(pg)
    check(f"REAL con informe importado: Ventas = 295,50 € rotulado REAL (importadas, sin mezclar demo)", badge(pg, "ventas") == "REAL" and "295,50" in B["ventas"])
    check("REAL con ventas: Margen = NO DETERMINABLE (exige costes y liquidaciones), nunca un número inventado", "NO DETERMINABLE" in B["margen"] and not re.search(r"\d+,\d\d €", B["margen"]))
    check("REAL: 1 decisión pendiente (la sembrada) en HOY, chip y DECISIONES", "(1)" in B["decisiones"] and pg.inner_text("#decN") == "1")
    real_names = ["PHIVITAL Magnesio", "ACTIVCORE"]
    # --- DEMO: nunca real
    pg.select_option("#dmode", "demo"); pg.wait_for_timeout(1800); B = blocks(pg); top = pg.inner_text("#h2top")
    check("DEMO: Ventas y Margen rotulados DEMO con importes sintéticos (6942,82 € / 1943,98 €)", badge(pg, "ventas") == "DEMO" and "6942,82" in B["ventas"] and badge(pg, "margen") == "DEMO" and "1943,98" in B["margen"])
    check("DEMO: las ventas REALES (295,50 €) NO aparecen mezcladas", "295,50" not in top)
    check("DEMO: Stock/riesgos, Decisiones y Prioridades = SIN DATOS (el dataset demo no las tiene)", all(badge(pg, k) == "SIN DATOS" for k in ("stock", "decisiones", "prioridades")))
    check("DEMO: ningún producto, riesgo ni decisión REAL aparece (ni «PHIVITAL», ni «ACTIVCORE», ni «riesgos abiertos»)", not re.search(r"PHIVITAL|ACTIVCORE|riesgos? abiertos?|Keepa", top))
    check("DEMO: la situación dice que son datos demo, no del negocio real", "DEMO" in pg.inner_text(".h2sit h2") and "no describen el negocio real" in pg.inner_text(".h2sit"))
    check("DEMO: el chip de decisiones no cuenta decisiones reales (0)", pg.inner_text("#decN") == "0")
    pg.click("#decChip"); pg.wait_for_selector("#tab-decisiones.on", timeout=5000); pg.wait_for_timeout(800); dt = pg.inner_text("#dec2")
    check("DEMO › DECISIONES: sin tarjetas reales; mensaje de que no se mezclan", pg.locator("#dec2 .h2dec").count() == 0 and "no se mezclan" in dt and "SIN DATOS" in dt)
    pg.evaluate("NAV6.go('dir',0)"); pg.wait_for_selector("#modeGuard:not([hidden])", timeout=8000); gtxt = pg.inner_text("#modeGuard")
    check("DEMO › DIRECTOR IA: la sección de datos reales queda tapada por el aviso de modo DEMO (no se mezcla) y no muestra productos reales", "Modo DATOS DEMO/SINTÉTICOS" in gtxt and not re.search(r"PHIVITAL|ACTIVCORE", gtxt) and not pg.locator("#tab-dir.on").count())
    # --- vuelta a REAL
    pg.select_option("#dmode", "real"); pg.evaluate("NAV6.go('dir',0)"); pg.wait_for_selector("#d2top .h2conc", timeout=8000); pg.wait_for_timeout(500)
    check("Vuelta a REAL › DIRECTOR: conclusión del negocio real (con «Datos insuficientes» expreso)", "Datos insuficientes" in pg.inner_text("#d2top .h2conc"))
    pg.evaluate("NAV6.go('hoy',0)"); pg.wait_for_timeout(1800); B = blocks(pg)
    check("Vuelta a REAL: se restauran las ventas reales y desaparece lo demo", badge(pg, "ventas") == "REAL" and "295,50" in B["ventas"] and "6942,82" not in pg.inner_text("#h2top"))
    pg.evaluate("NAV6.go('dec',0)"); pg.wait_for_timeout(1200)
    check("Vuelta a REAL › DECISIONES: reaparecen la decisión real y los 8 campos", pg.locator("#dec2 .h2dec").count() == 1 and pg.eval_on_selector_all("#dec2 .h2dec dt", "e=>e.length") == 8)
    # --- admin: acciones activas y ejecución real de «Rechazar» desde la bandeja (no gasta: rechaza)
    bt = pg.eval_on_selector_all("#dec2 .h2act button", "e=>e.map(x=>[x.textContent.trim(),x.disabled])")
    check(f"ADMIN: Aprobar/Rechazar ACTIVOS en la bandeja {bt}", bt == [["Aprobar", False], ["Rechazar", False]])
    pg.click('[data-h2dec][data-ok="0"]'); pg.wait_for_timeout(1800)
    check("ADMIN: «Rechazar» desde DECISIONES se registra en el servidor y la decisión sale de Pendientes", call("/api/v06/decisions")["decisions"] == [] and pg.locator("#dec2 .h2dec").count() == 0)
    pg.click('[data-h2f="res"]'); pg.wait_for_timeout(1200)
    check("ADMIN: aparece en «Resueltas» con estado RECHAZADA", "RECHAZADA" in pg.inner_text("#dec2"))
    check("sin errores de consola ni excepciones", errs == [])
    b.close()
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
