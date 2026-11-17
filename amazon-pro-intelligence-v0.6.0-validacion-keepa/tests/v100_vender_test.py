"""V1.0 · V1-04 — VENDER Y OPTIMIZAR con informes CSV importados. Los CSV de esta prueba son SIMULADOS (inventados solo para probar el cálculo); el sistema los marca IMPORTADO, nunca REAL de API."""
import base64, http.cookiejar, json, os, socket, sys, tempfile, threading, urllib.error, urllib.request
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
AC = "PRD-ACTIVCORE-V2"; tmp = tempfile.mkdtemp()
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())); csrf = [""]
def call(m, p, b=None):
    rq = urllib.request.Request(f"http://127.0.0.1:{port}{p}", data=json.dumps(b).encode() if b is not None else None, method=m, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf[0]})
    try:
        with op.open(rq, timeout=60) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b"{}")
        except Exception: return e.code, {}
    except (urllib.error.URLError, ConnectionError): return 599, {}   # el servidor cortó la conexión (cuerpo sobredimensionado)
csrf[0] = call("POST", "/api/login", {"username": "admin", "password": "admin-password-123"})[1]["csrf"]
VENTAS = "Fecha;(Child) ASIN;Ventas de productos pedidos;Unidades pedidas;Sesiones - Total\n2026-10-01;B0SIMULADO1;100,00;5;50\n2026-10-02;B0SIMULADO1;200,00;10;100\n2026-10-03;B0SIMULADO1;300,00;15;150\n"
ADS = "Fecha,Gasto,Clics,Impresiones,Pedidos,Ventas\n2026-10-01,10.00,20,1000,2,100.00\n2026-10-02,20.00,40,2000,4,200.00\n"
imp = lambda name, txt, **k: call("POST", "/api/v06/import", {"product": AC, "filename": name, "content": txt, **k})
c, s0 = call("GET", "/api/v06/imports?product=" + AC)
check("sin informes: SIN DATOS (no ceros inventados)", c == 200 and s0["summary"]["state"] == "SIN DATOS")
c, a = imp("ventas_simulado.csv", VENTAS); check("importa ventas (CSV con ; y coma decimal)", c == 200 and a.get("type") == "ventas")
check("clase IMPORTADO y hash SHA-256 conservado, nunca REAL/API", a.get("class") == "IMPORTADO" and len(a.get("sha256", "")) == 64 and "No es una conexión API" in a.get("provenance", ""))
check("ASIN no declarado → advertencia explícita", any("ASIN" in w for w in a.get("warnings", [])))
check("métricas de ventas exactas: 600,00 € · 30 uds · conversión 0,1", a["metrics"]["sales"] == 600.0 and a["metrics"]["units"] == 30 and a["metrics"]["conversion"] == 0.1)
c, b = imp("ads_simulado.csv", ADS); check("importa publicidad", c == 200 and b.get("type") == "publicidad")
check("ACOS exacto: 30/300 = 0,1", b["metrics"]["acos"] == 0.1)
c, s = call("GET", "/api/v06/imports?product=" + AC); sm = s["summary"]
check("TACoS = gasto ÷ ventas totales = 30/600 = 0,05, con nota de periodos", sm["tacos"]["valor"] == 0.05 and "periodos" in sm["tacos"]["nota"])
check("el resumen declara su clase IMPORTADO", sm.get("class") == "IMPORTADO")
c, d = imp("ventas_simulado.csv", VENTAS); check("duplicado rechazado (mismo contenido)", c >= 400)
c, d = imp("basura.csv", "a,b\n1,2\n"); check("CSV no reconocido rechazado con columnas halladas", c >= 400 and "columnas" in json.dumps(d, ensure_ascii=False).lower())
c, d = imp("vacio.csv", ""); check("CSV vacío rechazado", c >= 400)
c, d = call("POST", "/api/v06/import", {"product": "PRD-NO-EXISTE", "filename": "x.csv", "content": VENTAS}); check("producto inexistente rechazado", c >= 400)
c, d = imp("grande.csv", "Fecha,Ventas\n" + "2026-10-01,1\n" * 600000); check("archivo >5 MB rechazado", c >= 400)
c, d = imp("hostil.csv", "Fecha,Gasto,Clics\n=cmd|' /C calc'!A0,1,1\n"); check("fórmula hostil: no se ejecuta ni rompe (aceptada como dato o rechazada, nunca 500)", c in (200, 400, 409, 422))
anon = urllib.request.build_opener()
try: anon.open(f"http://127.0.0.1:{port}/api/v06/imports?product={AC}", timeout=10); st = 200
except urllib.error.HTTPError as e: st = e.code
check("sin sesión: 401", st == 401)
srv.shutdown(); print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
