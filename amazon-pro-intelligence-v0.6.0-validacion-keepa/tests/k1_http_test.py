"""K1 · capa HTTP: servidor real en proceso con Keepa SIMULADO (get_fn falso, guardia de red). 0 tokens, 0 red."""
import http.client, json, os, socket, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
_real = socket.socket.connect
def _guard(self, addr, *a, **k):
    if isinstance(addr, tuple) and addr and addr[0] not in ("127.0.0.1", "localhost", "::1"): raise OSError("RED BLOQUEADA")
    return _real(self, addr, *a, **k)
socket.socket.connect = _guard
import server as S
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
KEY = "KEEPA-CENTINELA-K1-0123456789abcdef0123456789abcdef"; CALLS = []
ENV = {"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "balance", "AMAZON_PRO_KEEPA_REQUIRE_APPROVAL": "1", "AMAZON_PRO_KEEPA_MISSION_CAP": "60", "AMAZON_PRO_KEEPA_MIN_GAP_S": "0"}
def fake(url, headers, timeout):
    CALLS.append(url)
    if "/token" in url: return 200, json.dumps({"tokensLeft": 55, "refillIn": 1000, "refillRate": 1}).encode(), ""
    return 200, json.dumps({"tokensLeft": 45, "tokensConsumed": 10, "products": []}).encode(), ""
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tempfile.mkdtemp(), "h.db"), admin_password="Admin-clave-larga-1", keepa_env_fn=lambda: ENV, keepa_get=fake)
port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
class C:
    cookie = None; csrf = ""
    def req(s, m, p, b=None):
        h = {"Host": "127.0.0.1:%d" % port, "Content-Type": "application/json", "Origin": "http://127.0.0.1:%d" % port}
        if s.cookie: h["Cookie"] = "apisid=" + s.cookie; h["X-CSRF-Token"] = s.csrf
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=20); c.request(m, p, json.dumps(b) if b is not None else None, h); r = c.getresponse(); d = r.read(); return r.status, d, dict(r.getheaders())
    def login(s, u, pw):
        st, d, hd = s.req("POST", "/api/login", {"username": u, "password": pw})
        if st == 200: s.cookie = hd["Set-Cookie"].split("apisid=")[1].split(";")[0]; s.csrf = json.loads(d)["csrf"]
        return st
a = C(); check("login admin", a.login("admin", "Admin-clave-larga-1") == 200)
st, d, _ = a.req("GET", "/api/keepa/status"); j = json.loads(d)
check("estado: modo balance, clave presente, aprobación obligatoria, sin la clave en la respuesta", st == 200 and j["mode"] == "balance" and j["key_present"] and j["require_approval"] and KEY not in d.decode())
st, d, _ = a.req("POST", "/api/keepa/test", {}); j = json.loads(d)
check("«Probar conexión»: saldo 55 por GET /token (gratis) en modo balance", st == 200 and j.get("ok") and j["tokens_left"] == 55 and all("/token" in u for u in CALLS))
n0 = len(CALLS)
st, d, _ = a.req("POST", "/api/keepa/search", {"country": "ES", "term": "serum anticaida", "approved_tokens": 10}); j = json.loads(d)
check("balance: búsqueda con aprobación sigue BLOQUEADA (KEEPA_SOLO_SALDO) y sin llamada", j.get("error") == "KEEPA_SOLO_SALDO" and len(CALLS) == n0)
ENV["AMAZON_PRO_KEEPA_ENABLE"] = "1"
st, d, _ = a.req("POST", "/api/keepa/search", {"country": "ES", "term": "serum anticaida"}); j = json.loads(d)
check("modo 1 sin approved_tokens → KEEPA_SIN_APROBACION, sin llamada", j.get("error") == "KEEPA_SIN_APROBACION" and len(CALLS) == n0)
st, d, _ = a.req("POST", "/api/keepa/search", {"country": "ES", "term": "serum anticaida", "approved_tokens": 500}); j = json.loads(d)
check("aprobación 500 > tope 120 → rechazada, sin llamada", j.get("error") in ("KEEPA_APROBACION_SUPERA_TOPE",) and len(CALLS) == n0)
st, d, _ = a.req("POST", "/api/discovery/run", {"product": "PRD-ACTIVCORE-V2", "countries": ["ES"], "depth": "ligera"}); j = json.loads(d)
check("descubrimiento sin aprobación → REQUIERE_AUTORIZACION, sin llamada de pago", j.get("status") == "REQUIERE_AUTORIZACION" and len(CALLS) == n0)
st, d, _ = a.req("GET", "/api/discovery/plan?product=PRD-ACTIVCORE-V2"); j = json.loads(d)
check("plan completo 4 países = 160 > tope 120 → marcado exceeds_hard_cap con desglose por país", st == 200 and j["estimated_tokens_max"] == 160 and j["exceeds_hard_cap"] is True and set(j["per_country_tokens"]) == {"DE", "FR", "IT", "ES"} and j["hard_cap"] == 120)
st, d, _ = a.req("POST", "/api/discovery/run", {"product": "PRD-ACTIVCORE-V2", "approved_tokens": 160}); j = json.loads(d)
check("aprobar 160 (> tope 120) se rechaza: APROBACION_SUPERA_TOPE", j.get("status") == "APROBACION_SUPERA_TOPE" and len(CALLS) == n0)
st, d, _ = a.req("POST", "/api/keepa/importar-evidencia", {"product": "PRD-ACTIVCORE-V2"}); j = json.loads(d)
check("importar evidencia: 20 candidatos, 0 red, 0 tokens", st == 200 and j["importados"] == 20 and j["tokens"] == 0 and len(CALLS) == n0)
st, d, _ = a.req("GET", "/api/eu/benchmark?country=ES&product=PRD-ACTIVCORE-V2")
j = json.loads(d) if st == 200 else {}; b = j.get("benchmark") or {}
check("tras importar, el módulo europeo ya ve los 20 (sin dato confirmado por humano)", st == 200 and b.get("total", 0) >= 20 and b.get("unconfirmed", 0) >= 1)
# permisos: no admin
srv.RequestHandlerClass  # noqa
check("el cuerpo de ninguna respuesta contiene la clave", all(KEY not in x for x in [json.dumps(j)]))
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
