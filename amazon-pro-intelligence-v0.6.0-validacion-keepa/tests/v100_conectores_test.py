"""V1.0 · V1-13 — Adaptadores SP-API / Ads API (solo lectura). Pruebas SIMULADAS (servidor local 127.0.0.1), identificadas como tales. NO prueban conexión real con Amazon."""
import json, os, socket, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
_rc = socket.socket.connect; EXT = []
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(addr); raise AssertionError("RED PROHIBIDA %r" % (addr,))
    return _rc(self, addr, *a, **k)
socket.socket.connect = _no_net
from backend import conectores100 as C
VISTO = []
class H(BaseHTTPRequestHandler):
    def do_GET(self): VISTO.append((self.command, self.path, self.headers.get("Authorization"))); self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps({"simulado": True, "ruta": self.path}).encode())
    def log_message(self, *a): pass
srv = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start(); base = "http://127.0.0.1:%d" % srv.server_address[1]
check("sin credenciales: NO CONECTADO, no operativo, dice qué faltan", all(e["estado"] == "NO CONECTADO" and e["operativo"] is False and e["faltan"] for e in C.estados({})))
FAKE = {v: "FALSO-%d" % i for i, s in enumerate(C.SERVICIOS.values()) for v in s["vars"]}
st = C.Conector("spapi", FAKE).estado(); check("con credenciales: CONFIGURADO · SIN VERIFICAR, NUNCA operativo", st["estado"].startswith("CONFIGURADO · SIN VERIFICAR") and st["operativo"] is False)
check("el estado no revela valores de credenciales", "FALSO-" not in json.dumps(C.estados(FAKE)))
c = C.Conector("spapi", {})
r = c.get("/orders/v0/orders", {"CreatedAfter": "2026-01-01"}, modo="SIMULADO", base_url=base)
check("SIMULADO: respuesta marcada origen=SIMULADO, solo lectura, 0 €, aviso 'no proviene de Amazon'", r["origen"] == "SIMULADO" and r["solo_lectura"] and r["coste_eur"] == 0.0 and "no proviene de Amazon" in r["aviso"] and r["datos"]["simulado"])
check("el servidor simulado solo recibió GET, sin cabecera Authorization", VISTO and all(v[0] == "GET" and v[2] is None for v in VISTO))
a = C.Conector("ads", {}).get("/v2/profiles", modo="SIMULADO", base_url=base); check("Ads API simulada: perfiles", a["origen"] == "SIMULADO" and a["servicio"] == "Amazon Ads API")
def falla(fn, frag=""):
    try: fn(); return False
    except C.ConectorError as e: return frag in str(e)
check("ruta fuera de la lista blanca (escritura/otros) rechazada", falla(lambda: c.get("/orders/v0/orders/123/shipment", modo="SIMULADO", base_url=base), "lista blanca") and falla(lambda: C.Conector("ads", {}).get("/sp/campaigns", modo="SIMULADO", base_url=base), "lista blanca"))
check("ruta absoluta, traversal o sin '/' rechazadas", all(falla(lambda p=p: c.get(p, modo="SIMULADO", base_url=base)) for p in ("http://evil.com/orders/v0/orders", "//evil.com/x", "orders/v0/orders", "/orders/../etc/passwd")))
check("SIMULADO solo con 127.0.0.1 (otro host rechazado)", falla(lambda: c.get("/orders/v0/orders", modo="SIMULADO", base_url="http://evil.example.com"), "127.0.0.1") and falla(lambda: c.get("/orders/v0/orders", modo="SIMULADO"), "servidor local"))
check("REAL sin credenciales: imposible", falla(lambda: c.get("/orders/v0/orders", modo="REAL"), "faltan credenciales"))
check("REAL con credenciales pero sin AMAZON_PRO_LIVE_*=1: desactivado", falla(lambda: C.Conector("spapi", FAKE).get("/orders/v0/orders", modo="REAL"), "desactivada"))
cap = []
r2 = C.Conector("spapi", {**FAKE, "AMAZON_PRO_LIVE_SPAPI": "1"}).get("/orders/v0/orders", modo="REAL", habilitado=True, post=lambda u, d, h: {"access_token": "ACC-LWA-TEST-123"}, transport=lambda url, hdr: cap.append(url) or {"x": 1})
check("REAL habilitado: URL al host oficial de Amazon por HTTPS (transporte inyectado, SIN red en la prueba)", cap == ["https://sellingpartnerapi-eu.amazon.com/orders/v0/orders"] and r2["origen"] == "REAL" and "sin verificar" in r2["aviso"])
check("la prueba no contactó ninguna red externa", not EXT)
check("modo inválido y servicio desconocido rechazados", falla(lambda: c.get("/orders/v0/orders", modo="X")) and falla(lambda: C.Conector("zzz")))
src = open(os.path.join(ROOT, "backend", "conectores100.py"), encoding="utf-8").read()
re = __import__("re")
check("el código no contiene PUT/PATCH/DELETE y el ÚNICO POST es el de token LWA (protegido por comprobación de URL)", not re.search(r"method=\"(PUT|PATCH|DELETE)\"", src) and len(re.findall(r"method=\"POST\"", src)) == 1 and "url != LWA_URL" in src)
check("transporte caído → error controlado", falla(lambda: c.get("/v2/profiles", modo="SIMULADO", base_url="http://127.0.0.1:1"), "transporte") if False else falla(lambda: C.Conector("ads", {}).get("/v2/profiles", modo="SIMULADO", base_url=base, transport=lambda u, h: (_ for _ in ()).throw(OSError("x"))), "transporte"))
srv.shutdown(); print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
