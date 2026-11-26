"""Rediseño F1 (correcciones PR8) — usuario AUTORIZADO (admin, no viewer): chat real del Director IA con proveedor simulado + contexto de filtros validado por el servidor,
borrador/fullscreen estables, carrera de respuestas, notificaciones (HTTP fallido → «Sin datos»), modo real sin gráficos. Sin red externa, sin gasto."""
import json, os, re, socket, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in list(os.environ):
    if k.startswith(("AMAZON_PRO_", "KEEPA_", "OPENAI_", "ANTHROPIC_")): os.environ.pop(k)
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0", AMAZON_PRO_AI_PROVIDER="mock", PLAYWRIGHT_BROWSERS_PATH=os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
_c = socket.socket.connect
def _nn(self, a, *x, **k):
    if a[0] not in ("127.0.0.1", "localhost", "::1"): raise AssertionError("RED PROHIBIDA")
    return _c(self, a, *x, **k)
socket.socket.connect = _nn
R = []
def check(n, c, e=""): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n + ((" → " + str(e)) if (e and not c) else ""))
import server as S
from backend import ai as AI
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config(dict(os.environ)), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
# contrato del servidor (unidad)
v = S.validate_dash_context
check("contrato: contexto válido aceptado", v({"line": "phivital", "sub": "sup", "region": "eu", "country": "ES", "period": "mes"})[1] is None)
check("contrato: país incompatible con región, línea/periodo fuera de catálogo, campos extra, sub sin PHIVITAL y tipos erróneos → rechazados",
      all(v(x)[1] for x in ({"region": "eu", "country": "US"}, {"line": "x"}, {"period": "decada"}, {"foo": 1}, {"line": "cosm", "sub": "sup"}, {"region": ["eu"]}, "texto libre", {"country": "CA", "region": "am"}, {"country": "MX"})))
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1920, "height": 1080}); errs = []; asks = []; ext = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("request", lambda r: (asks.append(json.loads(r.post_data)) if r.url.endswith("/api/director/ask") and r.post_data else None, ext.append(r.url) if not r.url.startswith(("http://localhost", "data:", "blob:")) else None))
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#lgOpen", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1200)
    r = pg.evaluate("async()=>{const a=V03.V.account||document.getElementById('acSel')?.value;const r=await V03.api('POST','/api/pilot/phivital/init',{account:a});if(r.ok){V03.V.dossierId=r.j.id;V03.V.account=a}return [r.ok,r.status,a]}")
    check("usuario autorizado: expediente creado y compositor HABILITADO", pg.evaluate("!!V03.V.dossierId") and not pg.locator("#c7In").is_disabled() and not pg.locator("#c7Ro").is_visible(), r)
    pg.select_option("#f7Line", "phivital"); pg.select_option("#f7Sub", "sup"); pg.select_option("#f7Reg", "eu"); pg.select_option("#f7Cty", "ES"); pg.select_option("#f7Per", "semana")
    pg.fill("#c7In", "resumen general"); pg.keyboard.press("Enter"); pg.wait_for_timeout(2500)
    ask = asks[-1] if asks else {}
    check("chat real (proveedor SIMULADO): la pregunta viaja con el contexto de filtros", ask.get("question") == "resumen general" and ask.get("context") == {"line": "phivital", "sub": "sup", "region": "eu", "country": "ES", "period": "semana"}, ask)
    t = pg.inner_text("#c7Log")
    check("respuesta en el chat con modo SIMULADA/SIN IA etiquetado (nunca IA real) y contexto validado por el servidor", ("SIN IA" in t or "SIMULADA" in t.upper()) and "contexto validado por el servidor" in t and "phivital/sup/eu/ES/semana" in t, t[-300:])
    pg.evaluate("window.__n=document.getElementById('c7In');document.getElementById('c7In').value='borrador pendiente'")
    pg.select_option("#f7Line", "all"); pg.select_option("#f7Reg", "all"); pg.wait_for_timeout(300)
    check("tras cambiar filtros: historial del chat y borrador conservados", pg.evaluate("window.__n===document.getElementById('c7In')&&document.getElementById('c7In').value==='borrador pendiente'") and "resumen general" in pg.inner_text("#c7Log"))
    r = pg.evaluate("""async()=>{const j=async(c)=>{const r=await V03.api('POST','/api/director/ask',{account:V03.V.account,dossier:V03.V.dossierId,question:'resumen',context:c});return r.status};return [await j({region:'eu',country:'US'}),await j({line:'zzz'}),await j('x'),await j({period:'mes'})]}""")
    check("el servidor rechaza contextos inválidos (400) y acepta uno válido (200)", r[:3] == [400, 400, 400] and r[3] == 200, r)
    # fullscreen por interacción real, estado conservado al cambiar filtros
    pg.click("#c7Full"); pg.select_option("#f7Line", "cosm"); pg.wait_for_timeout(300)
    check("pantalla completa (clic real) se conserva al cambiar filtros", pg.evaluate("document.getElementById('chat7card').classList.contains('full')") and pg.evaluate("document.getElementById('chat7card').getBoundingClientRect().width>innerWidth-40"))
    pg.keyboard.press("Escape"); pg.select_option("#f7Line", "all")
    # carrera de respuestas asíncronas: se responde a la 1.ª petición de decisiones DESPUÉS de la 2.ª; debe prevalecer la última
    pg.evaluate("NAV6.state.mode='real'")
    state = {"n": 0}
    def route(rt):
        state["n"] += 1
        if state["n"] == 1:
            import time; time.sleep(0.8); rt.fulfill(status=200, content_type="application/json", body=json.dumps({"items": [{"title": "ANTIGUA", "estado": "x", "evidencia": "y"}]}))
        else: rt.fulfill(status=200, content_type="application/json", body=json.dumps({"items": [{"title": "NUEVA", "estado": "abierta", "evidencia": "informe 12/11"}]}))
    pg.route("**/api/v06/decisions", route)
    pg.evaluate("DASH7.render()"); pg.evaluate("DASH7.render()"); pg.wait_for_timeout(1800)
    n = pg.inner_text("#n7")
    check("carrera asíncrona: prevalece la respuesta más reciente; notificación con estado, evidencia y alcance", "NUEVA" in n and "ANTIGUA" not in n and "Estado: abierta" in n and "Evidencia: informe 12/11" in n and "Alcance:" in n, n)
    pg.unroute("**/api/v06/decisions"); pg.route("**/api/v06/decisions", lambda rt: rt.fulfill(status=500, content_type="application/json", body="{}"))
    pg.evaluate("DASH7.render()"); pg.wait_for_timeout(700)
    n = pg.inner_text("#n7")
    check("fallo HTTP en notificaciones → «Sin datos» (no «Sin notificaciones»)", "Sin datos" in n and "Sin notificaciones" not in n and "500" in n, n)
    pg.unroute("**/api/v06/decisions"); pg.route("**/api/v06/decisions", lambda rt: rt.fulfill(status=200, content_type="application/json", body='{"items":[]}'))
    pg.evaluate("DASH7.render()"); pg.wait_for_timeout(500)
    check("respuesta correcta vacía → «Sin notificaciones»", "Sin notificaciones" in pg.inner_text("#n7"))
    check("modo DATOS DE AHT: KPI «Sin datos», ningún gráfico inventado, donut sin datos", pg.locator("svg.sp7").count() == 0 and pg.locator(".sp7.none").count() == 6 and "Sin datos" in pg.inner_text("#kg7") and pg.locator("#dn7w svg").count() == 0)
    check("sin errores de página ni red externa", not errs and not ext, (errs, ext[:2]))
    br.close()
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
