"""Rediseño F2 — Benchmarking a pantalla completa: contrato /api/bench7 (validación, persistencia tras reinicio, viewer RO, Keepa sin clave ni llamadas), UI en Chromium 1920/1440/390
con usuario autorizado y viewer, exportación, capturas. Sin red externa, sin gasto, 0 tokens Keepa."""
import json, os, re, socket, sys, tempfile, threading, http.cookiejar, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in list(os.environ):
    if k.startswith(("AMAZON_PRO_", "KEEPA_", "OPENAI_", "ANTHROPIC_")): os.environ.pop(k)
FAKEKEY = "FAKEKEEPAKEY0123456789abcdefSECRET"
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0", KEEPA_API_KEY=FAKEKEY, AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m", PLAYWRIGHT_BROWSERS_PATH=os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
EXT = []; _c = socket.socket.connect
def _nn(self, a, *x, **k):
    if a[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(a); raise AssertionError("RED PROHIBIDA")
    return _c(self, a, *x, **k)
socket.socket.connect = _nn
R = []
def check(n, c, e=""): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n + ((" → " + str(e)[:200]) if (e and not c) else ""))
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "rediseno", "capturas"); os.makedirs(OUT, exist_ok=True)
tmp = tempfile.mkdtemp(); DB = os.path.join(tmp, "s.db")
def start():
    srv = S.make_server(0, admin_token="t", db_path=DB, cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, srv.server_address[1]
class C:
    def __init__(s, port): s.p = port; s.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())); s.h = {}
    def req(s, m, u, b=None):
        r = urllib.request.Request(f"http://127.0.0.1:{s.p}" + u, data=json.dumps(b).encode() if b is not None else None, method=m, headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{s.p}", **s.h})
        try: x = s.op.open(r); return x.status, json.loads(x.read() or b"{}")
        except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")
    def login(s, u, p): c, j = s.req("POST", "/api/login", {"username": u, "password": p}); s.h = {"X-CSRF-Token": j.get("csrf", "")}; return c
srv, port = start(); a = C(port); check("login admin", a.login("admin", "admin-password-123") == 200)
c, o = a.req("GET", "/api/bench7/opciones"); check("opciones: productos del catálogo, países y periodos", c == 200 and any(p["id"] == "PRD-ACTIVCORE-V2" for p in o["productos"]) and "ES" in o["paises"] and len(o["periodos"]) == 4)
c, k = a.req("GET", "/api/bench7/keepa"); ks = json.dumps(k)
check("estado de Keepa: clave presente SIN exponerla, sin llamadas, aviso suscripción ≠ API", c == 200 and k["clave_presente"] is True and (FAKEKEY not in ks and "SECRET" not in ks) and k["consulta_real_realizada_ahora"] is False and k["red"] == 0 and "≠" in k["nota"])
CTX = {"product": "PRD-ACTIVCORE-V2", "country": "ES", "period": "mes", "pvp": 49.9, "coste_unit": 8.99, "comision_pct": 0.15, "logistica_unit": 5.41, "ads_unit": 4.99}
c, r = a.req("POST", "/api/bench7/run", {"prompt": "Compara ACTIVCORE frente a la competencia", "context": CTX}); rid = r.get("id")
res = r.get("result", {}); secs = {x["id"]: x for x in res.get("sections", [])}
check("ejecutar: resultado LOCAL con 0 llamadas de red y 0 tokens, 4 secciones", c == 200 and res["mode"].startswith("LOCAL") and res["network_calls"] == 0 and res["tokens_spent_now"] == 0 and list(secs) == ["fuentes", "mercado", "ventas", "escenarios"])
check("fuentes: Keepa/Amazon/web con estado, fecha y evidencia; Amazon y web NO CONSULTADAS", [f["fuente"] for f in secs["fuentes"]["filas"]][:3] == ["Keepa", "Amazon (SP-API/Ads)", "Web"] and all("evidencia" in f and "fecha" in f for f in secs["fuentes"]["filas"]) and all(f["estado"] == "NO CONSULTADA" for f in secs["fuentes"]["filas"][1:]))
check("mercado: datos REALES solo desde caché local con origen y fecha; resumen con mediana", secs["mercado"]["estado"].startswith("REAL") and all(f["origen"].startswith("REAL") and f["fecha_precio"] for f in secs["mercado"]["filas"] if f["precio_eur"] is not None) and secs["mercado"]["resumen"]["mediana_precio_fresco_eur"] is not None)
check("ventas estimadas: NO DISPONIBLE y separadas de las reales", secs["ventas"]["estado"] == "NO DISPONIBLE" and "ESTIMADO" in secs["ventas"]["texto"])
f0 = secs["escenarios"]["filas"][0]
check("escenarios: ESTIMADO con 3 filas; contribución base = 49,90−8,99−7,485−5,41−4,99 = 23,02", secs["escenarios"]["state"] == "ESTIMADO" and len(secs["escenarios"]["filas"]) == 3 and f0["contribucion_unit"] == 23.02 and abs(f0["contribucion_pct"] - 46.14) < 0.01)
c, r2 = a.req("POST", "/api/bench7/run", {"prompt": "sin costes", "context": {"product": "PRD-PHIVITAL-MAGNESIO", "country": "DE", "period": "dia"}}); s2 = {x["id"]: x for x in r2["result"]["sections"]}
check("sin costes: NO CALCULABLE y lista lo que falta; producto sin evidencia → mercado NO DISPONIBLE (nada inventado)", s2["escenarios"]["state"] == "NO CALCULABLE" and set(s2["escenarios"]["faltan"]) == {"pvp", "coste_unit", "comision_pct", "logistica_unit", "ads_unit"} and s2["mercado"]["estado"] == "NO DISPONIBLE" and s2["mercado"]["filas"] == [])
bad = [{"prompt": "", "context": {}}, {"prompt": "x" * 4001, "context": {}}, {"prompt": "x", "context": {"country": "XX"}}, {"prompt": "x", "context": {"period": "decada"}}, {"prompt": "x", "context": {"asin": "no"}}, {"prompt": "x", "context": {"foo": 1}}, {"prompt": "x", "context": {"comision_pct": 5}}, {"prompt": "x", "context": {"pvp": "caro"}}, {"prompt": "x", "context": "texto"}, {"prompt": 5, "context": {}}]
check("validación: 10 entradas inválidas → 400", [a.req("POST", "/api/bench7/run", b)[0] for b in bad] == [400] * 10)
c, h = a.req("GET", "/api/bench7/historial"); check("historial: 2 ejecuciones, más reciente primero, con SQLite", c == 200 and len(h["items"]) == 2 and h["items"][0]["prompt"] == "sin costes" and "SQLite" in h["persistencia"])
vc = C(port); check("login viewer", vc.login("auditor", "viewer-pass-x7Qk2m") == 200)
check("viewer: puede leer historial y resultados pero NO ejecutar (403)", vc.req("GET", "/api/bench7/historial")[0] == 200 and vc.req("GET", "/api/bench7/run?id=" + rid)[0] == 200 and vc.req("POST", "/api/bench7/run", {"prompt": "x", "context": {}})[0] == 403)
check("sin sesión: 401", C(port).req("GET", "/api/bench7/historial")[0] == 401 and C(port).req("POST", "/api/bench7/run", {"prompt": "x"})[0] in (401, 403))
srv.shutdown(); srv.server_close()
srv, port = start(); a = C(port); a.login("admin", "admin-password-123")
c, h = a.req("GET", "/api/bench7/historial"); c2, r = a.req("GET", "/api/bench7/run?id=" + rid)
check("persistencia: tras REINICIAR el servidor el historial y el resultado siguen (SQLite)", len(h["items"]) == 2 and c2 == 200 and r["result"]["sections"][3]["filas"][0]["contribucion_unit"] == 23.02 and r["prompt"].startswith("Compara"))
from backend import respaldo100 as RB
data, sha = RB.exportar_bytes(DB); check("el respaldo existente incluye el historial (el .db contiene bench7_run)", b"bench7_run" in data and len(sha) == 64)
from playwright.sync_api import sync_playwright
def logged(br, w, h, user, pw):
    pg = br.new_page(viewport={"width": w, "height": h}, is_mobile=(w < 500), has_touch=(w < 500)); errs = []; ext = []; wr = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("request", lambda r: (ext.append(r.url) if not r.url.startswith(("http://localhost", "data:", "blob:")) else None, wr.append(r.method + r.url) if r.method != "GET" and "/api/login" not in r.url and "bench7/run" not in r.url else None))
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#lgOpen", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", user); pg.fill("#lgP", pw); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(900)
    return pg, errs, ext, wr
with sync_playwright() as p:
    br = p.chromium.launch()
    for vp, w, h in (("1920x1080", 1920, 1080), ("1440x900", 1440, 900), ("390x844", 390, 844)):
        pg, errs, ext, wr = logged(br, w, h, "admin", "admin-password-123")
        pg.click("#h7Bench"); pg.wait_for_selector("#b7In"); pg.wait_for_timeout(700)
        check(f"[{vp}] Benchmarking abre desde la cabecera, pantalla propia sin menú lateral", pg.locator("#tab-bench.on").count() == 1 and not any(pg.locator(s).first.is_visible() for s in ("#nav6bar", "#subnav6", "#bnav") if pg.locator(s).count()))
        check(f"[{vp}] prompt libre multilínea, adjuntos/voz rotulados PENDIENTE, ejecutar, exportar y contexto producto/ASIN/país/periodo", pg.locator("#b7In").evaluate("e=>e.tagName") == "TEXTAREA" and "PENDIENTES" in pg.inner_text("#b7Form") and pg.locator("#b7Run").count() == 1 and all(pg.locator(s).count() == 1 for s in ("#b7Prod", "#b7Asin", "#b7Cty", "#b7Per", "#b7Md", "#b7Csv", "#b7Js")) and pg.locator("#b7Mic").is_disabled())
        check(f"[{vp}] estado de Keepa visible sin clave y sin llamadas", "Keepa: clave presente" in pg.inner_text("#b7Kp") and FAKEKEY not in pg.content())
        n0 = pg.locator("#b7Hist [data-rid]").count(); check(f"[{vp}] historial previo cargado (persistente, ≥2)", n0 >= 2)
        pg.select_option("#b7Prod", "PRD-ACTIVCORE-V2")
        for k, v in (("pvp", "49,90"), ("coste_unit", "8.99"), ("comision_pct", "0.15"), ("logistica_unit", "5.41"), ("ads_unit", "4.99")): pg.fill(f"#b7h_{k}", v) if pg.locator(f"#b7h_{k}").is_visible() else pg.evaluate("([k,v])=>{document.getElementById('b7h_'+k).value=v}", [k, v])
        pg.fill("#b7In", "Benchmark de ACTIVCORE en ES\nlínea 2"); pg.keyboard.press("Control+Enter"); pg.wait_for_selector(".rs7", timeout=8000); pg.wait_for_timeout(500)
        t = pg.inner_text("#b7Res")
        check(f"[{vp}] resultado en área conversacional: respuesta, fuentes, mercado con gráfico y tabla, ventas, escenarios", all(x in t for x in ("Fuentes y evidencia", "BSR, precios, ofertas", "Ventas estimadas", "Costes y escenarios", "LOCAL · SIN RED · SIN KEEPA", "ESTIMADO", "NO CONSULTADA")) and pg.locator("#b7Res .ch7 svg").count() == 1 and pg.locator("#b7Res table").count() >= 3)
        check(f"[{vp}] el borrador se vació y el historial creció en 1", pg.input_value("#b7In") == "" and pg.locator("#b7Hist [data-rid]").count() == n0 + 1)
        with pg.expect_download() as d: pg.click("#b7Md")
        fn = d.value.path(); md = open(fn, encoding="utf-8").read(); check(f"[{vp}] exportar Markdown con trazabilidad", "NO CONSULTADA" in md and "Escenarios" in md or "escenarios" in md.lower())
        with pg.expect_download() as d: pg.click("#b7Csv")
        check(f"[{vp}] exportar CSV con precios y origen REAL", "REAL (Keepa, caché local)" in open(d.value.path(), encoding="utf-8-sig").read())
        pg.click("#b7Hist [data-rid] >> nth=-1"); pg.wait_for_timeout(400)
        check(f"[{vp}] abrir un resultado antiguo del historial lo muestra", "Compara ACTIVCORE" in pg.inner_text("#b7Res"))
        check(f"[{vp}] sin desbordamiento horizontal ni errores de página ni red externa ni escrituras ajenas", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1") and not errs and not ext and not wr, (errs, ext[:2], wr))
        if w == 1920 or w == 1440: check(f"[{vp}] sin desplazamiento vertical de página (la conversación desplaza dentro)", pg.evaluate("document.documentElement.scrollHeight<=innerHeight+2"), pg.evaluate("document.documentElement.scrollHeight"))
        pg.select_option("#b7Prod", "PRD-ACTIVCORE-V2"); pg.evaluate("document.getElementById('b7Res').scrollTop=0"); pg.screenshot(path=os.path.join(OUT, f"benchmarking_{vp}.png"), full_page=(w < 500)); pg.close()
    pg, errs, ext, wr = logged(br, 1440, 900, "auditor", "viewer-pass-x7Qk2m"); pg.click("#h7Bench"); pg.wait_for_selector("#b7In"); pg.wait_for_timeout(700)
    check("viewer: historial legible, ejecutar y prompt deshabilitados con aviso de solo lectura", pg.locator("#b7Hist [data-rid]").count() >= 2 and pg.locator("#b7Run").is_disabled() and pg.locator("#b7In").is_disabled() and pg.locator("#b7Ro").is_visible())
    pg.click("#b7Hist [data-rid] >> nth=0"); pg.wait_for_timeout(300); check("viewer: puede abrir resultados del historial", pg.locator("#b7Res .rs7").count() >= 4 and not wr and not errs)
    pg.evaluate("document.getElementById('h7Brand').click()"); pg.wait_for_timeout(300); check("la marca AHT vuelve al dashboard desde Benchmarking", pg.locator("#tab-dash.on").count() == 1)
    br.close()
check("0 conexiones externas durante toda la prueba (0 tokens Keepa)", not EXT)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
