"""Pruebas de seguridad del servidor V0.2. Usa SECRETOS FALSOS y transporte simulado: no hay red ni credenciales reales."""
import json, os, sys, threading, urllib.request, urllib.error, importlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
FAKE = {"KEEPA_API_KEY": "FAKESECRET_keepa_9f3a", "AMAZON_PRO_SPAPI_CLIENT_ID": "FAKESECRET_spid", "AMAZON_PRO_SPAPI_CLIENT_SECRET": "FAKESECRET_spsec",
        "AMAZON_PRO_SPAPI_REFRESH_TOKEN": "FAKESECRET_sprt", "AMAZON_PRO_ADS_CLIENT_ID": "FAKESECRET_adid", "AMAZON_PRO_ADS_CLIENT_SECRET": "FAKESECRET_adsec", "AMAZON_PRO_ADS_REFRESH_TOKEN": "FAKESECRET_adrt"}
os.environ.update(FAKE); os.environ.pop("AMAZON_PRO_CONNECTORS", None); os.environ.pop("AMAZON_PRO_ADMIN_TOKEN", None)
import server
res = []; ALLBODIES = []
def check(name, cond):
    res.append((name, bool(cond))); print(("OK   " if cond else "FAIL ") + name)

calls = []
class FakeResp:
    status = 200
    def __init__(s, body): s.b = body
    def read(s): return s.b
    def __enter__(s): return s
    def __exit__(s, *a): return False
def fake_open(req, timeout):
    calls.append((req.get_method(), req.full_url)); u = req.full_url
    if "o2/token" in u: return FakeResp(b'{"access_token":"FAKEACCESS"}')
    if "keepa" in u: return FakeResp(b'{"tokensLeft": 10}')
    return FakeResp(b'[]')
server._open = fake_open

TOKEN = "tok-test-123"
srv = server.make_server(0, TOKEN); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = f"http://localhost:{port}"
def req(method, path, body=None, headers=None, host=None):
    h = {"Host": host or f"localhost:{port}"}; h.update(headers or {})
    r = urllib.request.Request(B + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r) as x: d = x.read(); ALLBODIES.append(d); return x.status, d, dict(x.headers)
    except urllib.error.HTTPError as e:
        d = e.read(); ALLBODIES.append(d); return e.code, d, dict(e.headers)
J = {"Content-Type": "application/json", "X-Admin-Token": TOKEN}

# 1. Estático
s, d, h = req("GET", "/"); check("index.html se sirve", s == 200 and b"Amazon" in d)
check("cabeceras de seguridad (CSP, nosniff, frame, no-store)", all(k in h for k in ["Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Cache-Control"]) and "default-src 'none'" in h["Content-Security-Policy"])
for p in ["/server.py", "/tests/economics.test.js", "/docs/AUDITORIA.md", "/INFORME.md", "/README.md", "/run.bat", "/data/", "/../server.py", "/js/../server.py", "/js/%2e%2e/server.py", "/%2e%2e/server.py", "/js/app.js/../../server.py", "/js/.hidden.js", "/schemas/"]:
    s, d, h = req("GET", p); check(f"no expone {p}", s in (404, 400) and b"import" not in d)
s, d, h = req("GET", "/js/calc.js"); check("js/calc.js sí se sirve", s == 200)

# 2. Estado sin secretos, conectores deshabilitados por defecto
s, d, h = req("GET", "/api/status"); j = json.loads(d)
check("por defecto TODOS los conectores deshabilitados", all(not c["enabled"] for c in j["connectors"]))
check("por defecto ninguno es probable", all(not c["testable"] for c in j["connectors"]))
check("write_actions declarado como no implementado", "NO IMPLEMENTADAS" in j["write_actions"])

# 3. Endpoint de prueba protegido
s, _, _ = req("GET", "/api/connectors/test?name=keepa"); check("GET de prueba ya no existe (sin efectos por GET)", s == 404)
s, _, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', {"Content-Type": "application/json"}); check("POST sin token → 401", s == 401)
s, _, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', {**J, "X-Admin-Token": "mal"}); check("POST con token erróneo → 401", s == 401)
s, _, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', {**J, "Origin": "http://evil.example"}); check("Origin externo → 403 (CSRF)", s == 403)
s, _, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', J, host="evil.example"); check("Host externo → 403 (DNS rebinding)", s == 403)
s, _, _ = req("POST", "/api/connectors/test", b'name=keepa', {"Content-Type": "application/x-www-form-urlencoded", "X-Admin-Token": TOKEN}); check("form-urlencoded → 415 (CSRF simple)", s == 415)
s, _, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', J); check("conector deshabilitado → 403 aunque haya credenciales y token", s == 403)
check("con conectores deshabilitados NO hubo ninguna llamada de red", len(calls) == 0)
s, _, _ = req("POST", "/api/connectors/test", b'{"name":"helium10"}', J); check("helium10 no probable → 404", s == 404)
s, _, _ = req("POST", "/api/connectors/test", b'x' * 5000, J); check("cuerpo >2KB → 413", s == 413)
for m in ("PUT", "DELETE", "PATCH"): 
    s, _, _ = req(m, "/api/connectors/test", b"{}", J); check(f"{m} → 405", s == 405)

# 4. Habilitación explícita
os.environ["AMAZON_PRO_CONNECTORS"] = "keepa,sp-api,ads"; os.environ["AMAZON_PRO_LIVE_SPAPI"] = "1"; os.environ["AMAZON_PRO_LIVE_ADS"] = "1"   # doble activación (Corrección 4.1)
s, d, _ = req("GET", "/api/status"); j = json.loads(d); check("tras habilitar explícitamente, aparecen como probables", all(c["testable"] for c in j["connectors"] if c["id"] != "helium10"))
s, d, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', J); check("prueba keepa (simulada) OK", s == 200 and json.loads(d)["ok"] is True)
s, _, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', J); check("segunda prueba inmediata → 429", s == 429)
server.STATE["cool"].clear(); server.STATE["recent"].clear()
s, d, _ = req("POST", "/api/connectors/test", b'{"name":"sp-api"}', J); check("prueba sp-api simulada OK", s == 200 and json.loads(d)["ok"])
s, d, _ = req("POST", "/api/connectors/test", b'{"name":"ads"}', J); check("prueba ads simulada OK", s == 200 and json.loads(d)["ok"])
check("todas las llamadas salientes fueron GET de lectura o el POST de token LWA", all((m == "GET") or (m == "POST" and "o2/token" in u) for m, u in calls))

# 5. Lista blanca de solo lectura en el transporte
for m, u in [("PUT", "https://advertising-api-eu.amazon.com/v2/profiles"), ("POST", "https://advertising-api-eu.amazon.com/sp/campaigns"), ("DELETE", "https://sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/X/Y"),
             ("PUT", "https://sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/X/Y"), ("POST", "https://sellingpartnerapi-eu.amazon.com/pricing"), ("GET", "http://api.keepa.com/token"), ("GET", "https://evil.example/token"), ("PATCH", "https://api.keepa.com/token")]:
    try: server.guarded_request(m, u, b"{}"); ok = False
    except server.Blocked: ok = True
    check(f"transporte bloquea {m} {u[:60]}", ok)

# 6. Sin secretos en ninguna respuesta (incluida la ruta de error con excepción que contiene el secreto)
def boom(req, timeout): raise RuntimeError("fallo con " + FAKE["KEEPA_API_KEY"] + " " + req.full_url)
server._open = boom; server.STATE["cool"].clear(); server.STATE["recent"].clear()
s, d, _ = req("POST", "/api/connectors/test", b'{"name":"keepa"}', J); j = json.loads(d)
check("error de red: respuesta con código fijo, sin texto de excepción", j["ok"] is False and j["detail"] == "ERROR_DE_RED_O_RESPUESTA")
joined = b"".join(ALLBODIES)
check("NINGÚN secreto (FAKESECRET) apareció en ninguna respuesta HTTP", b"FAKESECRET" not in joined and TOKEN.encode() not in joined)
src = "".join(open(os.path.join(ROOT, "js", f), encoding="utf-8").read() for f in os.listdir(os.path.join(ROOT, "js"))) + open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
import re
check("frontend sin patrones de secretos (client_secret, refresh_token, api key literal, Bearer)", not re.search(r"client_secret|refresh_token|Bearer |KEEPA_KEY|api[_-]?key\s*[:=]\s*['\"]\w", src, re.I))
check("frontend sin llamadas a hosts externos", not re.search(r"https?://(?!localhost)(?!www\.w3\.org)", src))
check("servidor escucha solo en 127.0.0.1", srv.server_address[0] == "127.0.0.1")
code = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()
check("el código no contiene endpoints de escritura comercial (campaigns, putListings, pricing writes)", not re.search(r"/sp/campaigns|putListingsItem|patchListingsItem|submitFeed|createFeed", code))
srv.shutdown()
fails = [n for n, ok in res if not ok]; print(f"\n{len(res)-len(fails)}/{len(res)} pruebas de seguridad OK")
json.dump(res, open(os.path.join(ROOT, "tests", "security_results.json"), "w"), ensure_ascii=False, indent=1); sys.exit(1 if fails else 0)
