"""V1.0 · V1-06 — Exportaciones CSV/HTML/MD con trazabilidad y escapado seguro (unidad + servidor real, sin red)."""
import csv, http.cookiejar, io, json, os, socket, sys, tempfile, threading, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0")
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
_rc = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): raise AssertionError("RED PROHIBIDA")
    return _rc(self, addr, *a, **k)
socket.socket.connect = _no_net
from backend import export100 as X
check("CSV neutraliza = + - @ (inyección de fórmulas)", all(X.celda(v).startswith("'") for v in ("=1+1", "+cmd", "-2", "@SUM(A1)", "\tx")) and X.celda("normal") == "normal" and X.celda(None) == "")
rows = list(csv.reader(io.StringIO(X.a_csv(["a", "b"], [["=HYPERLINK(\"http://x\")", "ok"]], {"fuente": "Keepa"}))))
check("CSV: metadatos de fuente en cabecera y fila hostil neutralizada", rows[0][0].startswith("# fuente") and rows[2][0].startswith("'="))
h = X.a_html("t<script>", ["c"], [["<img src=x onerror=alert(1)>"]], {"k": "<b>"})
check("HTML escapa etiquetas y atributos", "<script>" not in h and "<img" not in h and "&lt;img" in h and "scope=\"col\"" in h)
m = X.a_md("t", ["a|b"], [["x|y\nz"]]); check("MD escapa | y saltos de línea", "a\\|b" in m and "x\\|y z" in m)
check("nombre de fichero saneado (sin rutas ni caracteres peligrosos)", X.nombre("../../etc/passwd", "csv") == "etc_passwd.csv" and "/" not in X.nombre("a/b\\c", "md") and X.nombre("", "csv") == "export.csv" and len(X.nombre("x" * 500, "csv")) <= 64)
import server as S
from backend import ai as AI
tmp = tempfile.mkdtemp(); AC = "PRD-ACTIVCORE-V2"
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())); csrf = ""
def get(p, o=None):
    try:
        with (o or op).open(urllib.request.Request(f"http://127.0.0.1:{port}{p}", headers={"X-CSRF-Token": csrf}), timeout=30) as r: return r.status, r.read().decode("utf-8"), dict(r.headers)
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)
rq = urllib.request.Request(f"http://127.0.0.1:{port}/api/login", data=json.dumps({"username": "admin", "password": "admin-password-123"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
csrf = json.loads(op.open(rq).read())["csrf"]
c, body, hd = get("/api/v07/export?product=%s&fmt=csv" % AC)
filas = list(csv.reader(io.StringIO(body))); datos = [r for r in filas if r and not r[0].startswith("#")]
check("endpoint CSV: 200, adjunto, nosniff", c == 200 and "attachment" in hd.get("Content-Disposition", "") and hd.get("X-Content-Type-Options") == "nosniff")
check("CSV: 20 competidores + cabecera, con fuente, fecha y procedencia REAL · NO CONFIRMADO", len(datos) == 21 and all("REAL" in r[-1] and "Keepa" in r[9] and r[10] for r in datos[1:]))
check("CSV: metadatos de procedencia al inicio", body.startswith("# producto") and "Keepa" in body.split("\n")[2] and "sin gasto" in body)
c, b2, hd = get("/api/v07/export?product=%s&fmt=html" % AC); check("endpoint HTML: tabla con caption y 20 filas", c == 200 and b2.count("<tr>") == 21 and "<caption>" in b2)
c, b3, hd = get("/api/v07/export?product=%s&fmt=md" % AC); check("endpoint MD: tabla markdown", c == 200 and b3.count("\n| ") >= 20)
check("formato inválido → 400", get("/api/v07/export?product=%s&fmt=exe" % AC)[0] == 400)
check("producto inexistente → 404", get("/api/v07/export?product=NO-EXISTE&fmt=csv")[0] == 404)
check("sin sesión → 401", get("/api/v07/export?product=%s&fmt=csv" % AC, urllib.request.build_opener())[0] == 401)
check("sin trazas ni rutas del servidor en errores", "Traceback" not in get("/api/v07/export?product=x&fmt=csv")[1] and ROOT not in get("/api/v07/export?product=x&fmt=csv")[1])
srv.shutdown(); print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
