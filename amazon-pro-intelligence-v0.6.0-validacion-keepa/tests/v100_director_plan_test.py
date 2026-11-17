"""V1.0 · V1-07 — Plan de coordinación de especialistas del Director IA: determinista, derivado del expediente, nunca GO, con bloqueos, propietarios y dependencias. Sin red."""
import http.cookiejar, json, os, socket, sys, tempfile, threading, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0")
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
_rc = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): raise AssertionError("RED PROHIBIDA")
    return _rc(self, addr, *a, **k)
socket.socket.connect = _no_net
import server as S
from backend import ai as AI, plan100 as P, expediente7 as EX
tmp = tempfile.mkdtemp(); AC = "PRD-ACTIVCORE-V2"
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
d = P.build(S.APP, AC); E = {e["id"]: e for e in d["especialistas"]}
check("6 especialistas con entradas, salidas y dependencias", len(E) == 6 and all(e["entradas"] and e["salidas"] for e in E.values()))
check("nunca GO; veredicto heredado NO DECIDIBLE", d["go"] is False and d["veredicto"] == "NO DECIDIBLE")
check("ACTIVCORE hoy: todos BLOQUEADOS con acción, propietario y coste", all(e["estado"] == "BLOQUEADO" and e["bloqueos"] for e in E.values()) and all(b["propietario"] and b["coste_eur"] is not None for e in E.values() for b in e["bloqueos"]))
check("no hay siguiente tarea inventada mientras todo está bloqueado", d["siguiente"] is None)
check("orden topológico: cada especialista va después de sus dependencias", all(d["orden"].index(x) < d["orden"].index(e["id"]) for e in E.values() for x in e["depende_de"]))
check("determinista: dos construcciones idénticas", P.build(S.APP, AC) == d)
check("0 llamadas de red, 0 tokens, 0 €", d["network_calls"] == 0 and d["tokens_spent_now"] == 0 and d["cost_now_eur"] == 0.0)
# escenario resuelto (expediente simulado SOLO para probar la lógica del plan)
orig = EX.build
def resuelto(APP, pid):
    x = orig(APP, pid); x = json.loads(json.dumps(x)); x["unlocks"] = []
    for s in x["sections"]: s["state"] = "CALCULADO"
    return x
EX.build = resuelto; d2 = P.build(S.APP, AC); EX.build = orig
check("simulado sin bloqueos: independientes COMPLETADO y el plan sigue sin emitir GO", d2["go"] is False and all(e["estado"] == "COMPLETADO" for e in d2["especialistas"]))
def parcial(APP, pid):
    x = orig(APP, pid); x = json.loads(json.dumps(x)); x["unlocks"] = [u for u in x["unlocks"] if u["id"] == "U-REG"]
    for s in x["sections"]: s["state"] = "CALCULADO" if s["id"] != "regulatorio" else s["state"]
    return x
EX.build = parcial; d3 = P.build(S.APP, AC); EX.build = orig; E3 = {e["id"]: e for e in d3["especialistas"]}
check("solo regulatorio bloqueado: listing queda EN ESPERA o BLOQUEADO; mercado y finanzas COMPLETADOS", E3["mercado"]["estado"] == "COMPLETADO" and E3["finanzas"]["estado"] == "COMPLETADO" and E3["regulatorio"]["estado"] == "BLOQUEADO" and E3["listing"]["estado"] in ("EN ESPERA", "BLOQUEADO") and "regulatorio" in E3["listing"]["espera_a"])
check("ads y operaciones COMPLETADOS si sus dependencias lo están", E3["ads"]["estado"] == "COMPLETADO" and E3["operaciones"]["estado"] == "COMPLETADO")
def listo(APP, pid):
    x = orig(APP, pid); x = json.loads(json.dumps(x)); x["unlocks"] = []
    for s_ in x["sections"]: s_["state"] = "PARCIAL"
    return x
EX.build = listo; d4 = P.build(S.APP, AC); EX.build = orig
check("sin bloqueos pero con secciones PARCIALES: el primero sin dependencias es LISTO PARA TRABAJAR y aparece como siguiente", d4["siguiente"] == "mercado" and {e["id"]: e["estado"] for e in d4["especialistas"]}["mercado"] == "LISTO PARA TRABAJAR" and {e["id"]: e["estado"] for e in d4["especialistas"]}["listing"] == "EN ESPERA")
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
rq = urllib.request.Request(f"http://127.0.0.1:{port}/api/login", data=json.dumps({"username": "admin", "password": "admin-password-123"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
csrf = json.loads(op.open(rq).read())["csrf"]
def get(p, o=None):
    try:
        with (o or op).open(urllib.request.Request(f"http://127.0.0.1:{port}{p}", headers={"X-CSRF-Token": csrf}), timeout=30) as r: return r.status, r.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8", "replace")
c, b = get("/api/v07/plan?product=" + AC); check("endpoint /api/v07/plan 200 y coherente", c == 200 and json.loads(b)["orden"] == d["orden"])
check("sin sesión 401", get("/api/v07/plan?product=" + AC, urllib.request.build_opener())[0] == 401)
c, b = get("/api/v07/plan?product=NO-EXISTE"); check("producto inexistente: error controlado sin traza ni rutas", c in (400, 404) and "Traceback" not in b and ROOT not in b)
srv.shutdown(); print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
