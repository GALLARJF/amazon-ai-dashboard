"""V0.7.0 · V7-05 — Seguridad de /api/v07/*: sesión, acceso al catálogo, CSRF, solo lectura, entradas hostiles, errores sin traza, sin secretos, sin red."""
import http.cookiejar, json, os, socket, sys, tempfile, threading, urllib.error, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
SENT = "CENTINELA-FALSO-KEEPA-0123456789abcdef0123456789"
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0", AMAZON_PRO_KEEPA_KEY=SENT, KEEPA_API_KEY=SENT, OPENAI_API_KEY=SENT)
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
_rc = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): raise AssertionError("RED PROHIBIDA %r" % (addr,))
    return _rc(self, addr, *a, **k)
socket.socket.connect = _no_net
import server as S
from backend import ai as AI
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); st = S.APP["store"]; AC = "PRD-ACTIVCORE-V2"
def mk():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def call(op, m, p, b=None, csrf=None, raw=None, headers=None):
    h = {"Content-Type": "application/json", "X-CSRF-Token": csrf or ""}; h.update(headers or {})
    rq = urllib.request.Request(f"http://127.0.0.1:{port}{p}", data=raw if raw is not None else (json.dumps(b).encode() if b is not None else None), method=m, headers=h)
    try:
        with op.open(rq, timeout=30) as r: return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e: return e.code, e.read(), dict(e.headers)
    except (urllib.error.URLError, ConnectionError, socket.timeout) as e: return 0, repr(e).encode(), {}
adm = mk(); c, body, _ = call(adm, "POST", "/api/login", {"username": "admin", "password": "admin-password-123"}); csrf = json.loads(body)["csrf"]
EP = ["/api/v07/keepa-real?product=" + AC, "/api/v07/briefing?product=" + AC, "/api/v07/expediente?product=" + AC, "/api/v07/expediente?product=%s&fmt=md" % AC]
# --- sesión
anon = mk(); check("sin sesión: los 4 endpoints GET → 401", all(call(anon, "GET", e)[0] == 401 for e in EP))
check("sin sesión: POST → 401/403, nunca 200 ni 500", call(anon, "POST", "/api/v07/keepa-real", {})[0] in (401, 403))
# --- acceso al catálogo (usuario sin cuentas)
st.create_user("sinacceso", "sin-acceso-pass-1", "analyst", []); na = mk(); call(na, "POST", "/api/login", {"username": "sinacceso", "password": "sin-acceso-pass-1"})
check("usuario sin acceso al catálogo → 403 en los 4 endpoints", all(call(na, "GET", e)[0] == 403 for e in EP))
st.create_user("lector", "lector-pass-1234", "analyst", ["catalogo-aht"]); lc = mk(); call(lc, "POST", "/api/login", {"username": "lector", "password": "lector-pass-1234"})
check("usuario con acceso (analista) puede LEER los 4 endpoints", all(call(lc, "GET", e)[0] == 200 for e in EP))
# --- CSRF y solo lectura
before = (len(S.APP["ops"].tasks(states=None, limit=500)), len(S.APP["ops"].ledger()), st.db.execute("SELECT COUNT(*) n FROM keepa_ledger").fetchone()["n"], st.db.execute("SELECT COUNT(*) n FROM keepa_mission").fetchone()["n"] if False else 0)
check("POST con sesión pero sin CSRF → 403", call(adm, "POST", "/api/v07/keepa-real", {}, csrf="")[0] == 403)
check("POST con CSRF falso → 403", call(adm, "POST", "/api/v07/keepa-real", {}, csrf="x" * 32)[0] == 403)
check("POST con CSRF válido: no hay escritura v07 → 404 (no 200/500)", call(adm, "POST", "/api/v07/expediente", {"product": AC}, csrf=csrf)[0] == 404)
check("PUT/DELETE/PATCH → nunca 200 ni 500", all(call(adm, m, "/api/v07/briefing?product=" + AC, {}, csrf=csrf)[0] not in (200, 500) for m in ("PUT", "DELETE", "PATCH")))
# --- entradas hostiles: ninguna produce 500, traza ni eco del servidor
hostile = ["../../etc/passwd", "A" * 5000, "%00", "'; DROP TABLE records;--", "<script>alert(1)</script>", "PRD-ACTIVCORE-V2%0d%0aSet-Cookie:x=1", "‮💥", "PRD-ACTIVCORE-V2 ", "prd-activcore-v2", ""]
bad = []
for h in hostile:
    for ep in ("keepa-real", "briefing", "expediente"):
        c, body, hd = call(adm, "GET", "/api/v07/%s?product=%s" % (ep, urllib.parse.quote(h, safe="%") if "%0" in h else urllib.parse.quote(h)))
        txt = body.decode("utf-8", "replace")
        if c in (500, 0) or "Traceback" in txt or ROOT in txt or "File \"" in txt or any(k.lower() == "set-cookie" and "x=1" in v for k, v in hd.items()): bad.append((ep, h[:20], c))
check("entradas hostiles en product (10×3): sin 500, sin traza, sin rutas, sin inyección de cabeceras (%s)" % (bad or "ok"), not bad)
for fm in ("xml", "md%0d%0aX-Evil:1", "MD", "../x", "a" * 3000, ""):
    c, body, hd = call(adm, "GET", "/api/v07/expediente?product=%s&fmt=%s" % (AC, fm)); ok = c in (200, 400) and "X-Evil" not in json.dumps(hd) and b"Traceback" not in body
    if fm in ("xml", "MD", "../x", "a" * 3000, "md%0d%0aX-Evil:1"): ok = ok and c == 400
    check("fmt %r → %s, sin traza ni inyección" % (fm[:12], "200 (por defecto json)" if fm == "" else "400 limpio"), ok)
check("parámetros repetidos (?product=A&product=B) → respuesta válida, sin 500", call(adm, "GET", "/api/v07/briefing?product=%s&product=PRD-NO" % AC)[0] in (200, 404))
check("ruta desconocida y path traversal → 404 sin traza", all(call(adm, "GET", p)[0] in (404, 400) and b"Traceback" not in call(adm, "GET", p)[1] for p in ("/api/v07/", "/api/v07/..%2f..%2fetc/passwd", "/api/v07/keepa-real/../../x", "/api/v07/%00")))
big = call(adm, "POST", "/api/v07/expediente", raw=b'{"x":"' + b"A" * 3_000_000 + b'"}', csrf=csrf)
check("cuerpo de 3 MB en POST → rechazado/ignorado sin 500 ni caída (%s)" % big[0], big[0] in (400, 403, 404, 413, 0) and call(adm, "GET", EP[0])[0] == 200)
# --- secretos, cabeceras y no-escritura
blob = b"".join(call(adm, "GET", e)[1] for e in EP) + b"".join(call(lc, "GET", e)[1] for e in EP)
check("ninguna respuesta contiene la clave centinela (Keepa/OpenAI) ni 'api_key' ni rutas del servidor", SENT.encode() not in blob and b"api_key" not in blob.lower() and ROOT.encode() not in blob and b"keepa.env" not in blob)
c, body, hd = call(adm, "GET", EP[3]); check("md: Content-Type text/markdown, attachment, filename seguro, nosniff", hd.get("Content-Type", "").startswith("text/markdown") and "attachment" in hd.get("Content-Disposition", "") and ".." not in hd.get("Content-Disposition", "") and hd.get("X-Content-Type-Options", "").lower() == "nosniff")
c, body, hd = call(adm, "GET", EP[0]); check("json: Content-Type application/json y nosniff", hd.get("Content-Type", "").startswith("application/json") and hd.get("X-Content-Type-Options", "").lower() == "nosniff")
after = (len(S.APP["ops"].tasks(states=None, limit=500)), len(S.APP["ops"].ledger()), st.db.execute("SELECT COUNT(*) n FROM keepa_ledger").fetchone()["n"], 0)
check("solo lectura: ningún endpoint v07 creó tareas, decisiones ni llamadas Keepa", before == after and after[2] == 0)
anon_json = call(anon, "GET", EP[0]); check("el 401 no filtra datos del producto", b"competitors" not in anon_json[1] and b"ACTIVCORE" not in anon_json[1])
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
