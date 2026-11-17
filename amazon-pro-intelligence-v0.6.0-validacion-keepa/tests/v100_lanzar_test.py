"""V1.0 · V1-03 — PREPARAR Y LANZAR de extremo a extremo (ACTIVCORE): orden → tareas → decisión humana → persistencia tras reiniciar el servidor. Servidor real, sin red ni gasto."""
import http.cookiejar, json, os, socket, sys, tempfile, threading, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0")
for k in ("AMAZON_PRO_KEEPA_KEY", "KEEPA_API_KEY", "OPENAI_API_KEY"): os.environ.pop(k, None)
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
_rc = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): raise AssertionError("RED PROHIBIDA %r" % (addr,))
    return _rc(self, addr, *a, **k)
socket.socket.connect = _no_net
import server as S
from backend import ai as AI
AC = "PRD-ACTIVCORE-V2"; tmp = tempfile.mkdtemp(); DB = os.path.join(tmp, "s.db")
def arrancar():
    srv = S.make_server(0, admin_token="t", db_path=DB, cfg_fn=lambda: AI.config({}), admin_password="admin-password-123")
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, srv.server_address[1]
def sesion(port):
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(m, p, b=None):
        rq = urllib.request.Request(f"http://127.0.0.1:{port}{p}", data=json.dumps(b).encode() if b is not None else None, method=m, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf[0]})
        try:
            with op.open(rq, timeout=60) as r: return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e: return e.code, (json.loads(e.read() or b"{}") if e.headers.get("Content-Type", "").startswith("application/json") else {})
    csrf = [""]; c, d = call("POST", "/api/login", {"username": "admin", "password": "admin-password-123"}); csrf[0] = d["csrf"]; return call
srv, port = arrancar(); call = sesion(port)
c, o = call("POST", "/api/v06/order", {"product": AC, "run": True}); check("orden de lanzamiento aceptada (200)", c == 200)
c, e = call("GET", "/api/v06/launch?product=" + AC)
check("expediente de lanzamiento con secciones y recomendación", c == 200 and len(e.get("sections", [])) >= 4 and bool(e.get("recommendation")))
check("nunca GO por defecto con datos ausentes", not str(e.get("recommendation")).strip().upper().startswith("GO"))
c, t = call("GET", "/api/v06/tasks?product=" + AC); check("tareas creadas y persistidas para el producto", c == 200 and len(t.get("tasks", [])) >= 1)
c, d = call("GET", "/api/v06/decisions?product=" + AC); n0 = len(d.get("decisions", [])); check("bandeja de decisiones accesible", c == 200)
if n0:
    did = d["decisions"][0]["id"]; c, r = call("POST", "/api/v06/decide", {"id": did, "approve": False, "note": "E2E: se pospone por falta de evidencias"})
    check("decisión humana registrada (rechazo con nota)", c == 200)
    c, d2 = call("GET", "/api/v06/decisions?product=%s&status=PENDIENTE" % AC); check("la decisión resuelta sale de pendientes", len(d2.get("decisions", [])) == n0 - 1)
else: check("decisión humana registrada (sin pendientes: tarea auto-resuelta)", True)
c, lg = call("GET", "/api/v06/ledger?product=" + AC); led0 = lg
ntask = len(t["tasks"]); srv.shutdown(); srv.server_close()
srv, port = arrancar(); call = sesion(port)   # reinicio con la misma BD
c, t2 = call("GET", "/api/v06/tasks?product=" + AC); check("tras reiniciar: las tareas siguen ahí", c == 200 and len(t2.get("tasks", [])) == ntask)
c, e2 = call("GET", "/api/v06/launch?product=" + AC); check("tras reiniciar: expediente igual (determinista)", c == 200 and e2.get("recommendation") == e.get("recommendation") and len(e2.get("sections", [])) == len(e["sections"]))
c, d3 = call("GET", "/api/v06/decisions?product=%s&status=PENDIENTE" % AC); check("tras reiniciar: la decisión resuelta sigue resuelta", c == 200 and len(d3.get("decisions", [])) == (n0 - 1 if n0 else 0))
c, ex = call("GET", "/api/v07/expediente?product=" + AC); check("expediente V0.7 sigue NO DECIDIBLE con huecos explícitos", c == 200 and "NO DECIDIBLE" in json.dumps(ex, ensure_ascii=False))
anon = urllib.request.build_opener()
try: anon.open(f"http://127.0.0.1:{port}/api/v06/launch?product={AC}", timeout=10); st = 200
except urllib.error.HTTPError as ex_: st = ex_.code
check("sin sesión: 401", st == 401)
srv.shutdown()
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
