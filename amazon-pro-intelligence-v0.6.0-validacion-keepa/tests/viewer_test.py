"""STAGING · rol viewer SOLO LECTURA — 403 en toda escritura (bloqueo central + segunda barrera), lectura completa como administrador, sin red, sin servicios de pago."""
import http.cookiejar, json, os, re, socket, subprocess, sys, tempfile, threading, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AMAZON_PRO_SPAPI_CLIENT_ID", "AMAZON_PRO_SPAPI_CLIENT_SECRET", "AMAZON_PRO_SPAPI_REFRESH_TOKEN", "AMAZON_PRO_ADS_CLIENT_ID", "AMAZON_PRO_ADS_CLIENT_SECRET", "AMAZON_PRO_ADS_REFRESH_TOKEN", "H10_API_KEY"):
    os.environ.pop(k, None)
VPW = "viewer-pass-" + "x7Qk2m"; APW = "admin-pass-" + "p9Zt4w"
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR=VPW, AMAZON_PRO_CONNECTORS="keepa,sp-api,ads", AMAZON_PRO_AI_ENABLE="1")
os.environ.pop("AMAZON_PRO_PUBLIC_HOST", None); os.environ.pop("RENDER_EXTERNAL_HOSTNAME", None)
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
_rc = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): raise AssertionError("RED PROHIBIDA %r" % (addr,))
    return _rc(self, addr, *a, **k)
socket.socket.connect = _no_net
import server as S
from backend import ai as AI, api6, api7, api_k4
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "v.db"), cfg_fn=lambda: AI.config({}), admin_password=APW)
port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start(); st = S.APP["store"]
def mk(): return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def call(op, m, p, b=None, csrf=None, headers=None):
    h = {"Content-Type": "application/json", "X-CSRF-Token": csrf or ""}; h.update(headers or {})
    rq = urllib.request.Request(f"http://127.0.0.1:{port}{p}", data=(json.dumps(b).encode() if b is not None else None), method=m, headers=h)
    try:
        with op.open(rq, timeout=30) as r: return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e: return e.code, e.read(), dict(e.headers)
def login(u, p):
    op = mk(); c, body, _ = call(op, "POST", "/api/login", {"username": u, "password": p}); return op, (json.loads(body).get("csrf") if c == 200 else None), c
adm, acsrf, c1 = login("admin", APW); vw, vcsrf, c2 = login("auditor", VPW)
check("admin de staging y auditor (viewer) inician sesión", c1 == 200 and c2 == 200)
me = json.loads(call(vw, "GET", "/api/me")[1]); check("/api/me informa role=viewer (el rol real, no el efectivo)", me["role"] == "viewer" and me["user"] == "auditor")
check("el usuario viewer existe con rol viewer en la BD", st.db.execute("SELECT role FROM users WHERE username='auditor'").fetchone()["role"] == "viewer")

# ---- 1) ESCRITURA: toda ruta POST → 403 (incluidas rutas que no existen: denegación por defecto)
src = "".join(open(os.path.join(ROOT, f), encoding="utf-8").read() for f in ("server.py", "backend/api6.py", "backend/api7.py", "backend/api_k4.py"))
legacy = sorted(set(re.findall(r'"(/api/[a-z0-9/_\-]+)"', src)))
POST = set(legacy)
for base, f in (("/api/v06/", "backend/api6.py"), ("/api/v07/", "backend/api7.py"), ("/api/k4/", "backend/api_k4.py")):
    POST |= {base + x for x in re.findall(r'p == "([a-z0-9/_\-]+)"', open(os.path.join(ROOT, f), encoding="utf-8").read())}
POST |= {"/api/ruta-inventada", "/api/k4/consejero/investigar", "/api/k4/consejero/limites", "/api/k4/consejero/reanudar", "/api/connectors/test", "/api/v07/respaldo/subir", "/api/ai/reconcile", "/api/catalog/product", "/api/eu/director", "/api/discovery/run", "/api/keepa/fetch", "/api/v06/decide", "/api/v06/run", "/api/v06/kill", "/api/v06/order"}
POST -= {"/api/login", "/api/logout"}
before = {t: st.db.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in [r["name"] for r in st.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")] if t not in ("sessions", "audit", "audit_log")}
bad = []
for p in sorted(POST):
    for csrf in (vcsrf, "", "falso" * 8):
        c, body, _ = call(vw, "POST", p, {"x": 1}, csrf=csrf)
        if c != 403: bad.append((p, c))
check(f"{len(POST)} rutas POST × 3 variantes de CSRF → siempre 403 para viewer (fallos: {bad[:5]})", not bad)
check("POST sin cookie de sesión de viewer sigue siendo 401/403 (no se abre nada)", call(mk(), "POST", "/api/v06/decide", {"x": 1})[0] in (401, 403))
check("PUT/DELETE/PATCH de viewer → 403", all(call(vw, m, "/api/v06/decide", {"x": 1}, csrf=vcsrf)[0] == 403 for m in ("PUT", "DELETE", "PATCH")))
after = {t: st.db.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in before}
check("ninguna tabla de datos cambió tras todos los intentos de escritura", before == after)
check("los intentos quedan auditados (viewer.write_blocked)", st.db.execute("SELECT COUNT(*) n FROM audit WHERE action='viewer.write_blocked'").fetchone()["n"] >= len(POST))
check("cierre de sesión (logout) sí está permitido al viewer", call(vw, "POST", "/api/logout", {}, csrf=vcsrf)[0] == 200)
vw, vcsrf, _ = login("auditor", VPW)

# ---- 2) SEGUNDA BARRERA (backend, aunque la primera fallase)
sv = {"username": "auditor", "role": "admin", "viewer": True, "accounts": [], "csrf": "c"}
for nm, mod in (("v06", api6), ("v07", api7), ("k4", api_k4)):
    try: mod.handle(S.APP, sv, "POST", "/api/%s/x" % nm.replace("v", "v"), {}, {}); ok = False
    except PermissionError: ok = True
    except Exception: ok = False
    check(f"segunda barrera api {nm}: handle(POST) de viewer → PermissionError", ok)
# _sess(write=True) con viewer → 403 aunque la ruta no estuviera en el bloqueo central
check("_v06 rechaza método no-GET con s.viewer", "s.get(\"viewer\") and method != \"GET\"" in open(os.path.join(ROOT, "server.py"), encoding="utf-8").read())

# ---- 3) LECTURA: el viewer ve lo mismo que el administrador (sin secretos)
GET = ["/api/me", "/api/accounts", "/api/ai/status", "/api/ai/usage", "/api/ai/calls", "/api/coworkers/status?account=ACC", "/api/records?kind=dossier&account=ACC", "/api/audit?account=ACC", "/api/news?account=ACC", "/api/keepa/status", "/api/keepa/ledger", "/api/keepa/export?fmt=json",
       "/api/eu/overview", "/api/eu/economics", "/api/eu/benchmark", "/api/eu/k3", "/api/eu/export", "/api/catalog", "/api/discovery/plan", "/api/discovery/last", "/api/status",
       "/api/v06/home", "/api/v06/demo", "/api/v06/launch", "/api/v06/tasks", "/api/v06/decisions", "/api/v06/ledger", "/api/v06/ops", "/api/v06/ai/calls", "/api/v06/imports", "/api/v06/connections", "/api/v06/econ", "/api/v06/inventory",
       "/api/v07/keepa-real?product=PRD-ACTIVCORE-V2", "/api/v07/briefing?product=PRD-ACTIVCORE-V2", "/api/v07/expediente?product=PRD-ACTIVCORE-V2", "/api/v07/plan?product=PRD-ACTIVCORE-V2",        "/api/k4/estado", "/api/k4/kpis", "/api/k4/costes", "/api/k4/medios", "/api/k4/dictamen", "/api/k4/dossiers", "/api/k4/seguimientos", "/api/k4/benchmark/ejecutivo", "/api/k4/umbrales", "/api/k4/planificador",
       "/api/k4/consejero/estado", "/api/k4/consejero/investigaciones", "/api/k4/benchmark/explorador", "/api/k4/benchmark", "/api/k4/centro"]
ACC = json.loads(call(adm, "GET", "/api/accounts")[1])["accounts"][0]["id"]; GET = [x.replace("ACC", ACC) for x in GET]
diff = []; faltan = []; secretos = []
SENT = re.compile(r"(sk-[A-Za-z0-9]{10,}|pw_hash|pw_salt|" + re.escape(VPW) + "|" + re.escape(APW) + ")")
sess_n = st.db.execute("SELECT COUNT(*) n FROM sessions").fetchone()["n"]
b0 = {t: st.db.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in before}
for p in GET:
    ca, ba, _ = call(adm, "GET", p); cv, bv, _ = call(vw, "GET", p)
    if p == "/api/me": continue
    if ca != cv: diff.append((p, ca, cv))
    if cv == 403 or b"restringido" in bv.lower() or b"solo administrador" in bv.lower(): faltan.append((p, cv))
    if SENT.search(bv.decode("utf-8", "ignore")): secretos.append(p)
check(f"{len(GET)} rutas GET: el viewer recibe el mismo estado HTTP que el admin (diferencias: {diff[:4]})", not diff)
check(f"ninguna ruta GET responde 403/«solo administrador»/«restringido» al viewer ({faltan[:4]})", not faltan)
check(f"ninguna respuesta contiene contraseñas, hashes ni claves ({secretos[:3]})", not secretos)
check("EXCEPCIÓN DE SECRETOS: el viewer NO puede descargar el respaldo (contiene hashes y sesiones) → 403; el admin sí → 200", call(vw, "GET", "/api/v07/respaldo")[0] == 403 and call(adm, "GET", "/api/v07/respaldo")[0] == 200)
check("/api/ai/usage y /api/keepa/status son legibles por el viewer (200)", call(vw, "GET", "/api/ai/usage")[0] == 200 and call(vw, "GET", "/api/keepa/status")[0] == 200)
b1 = {t: st.db.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in before}
check("recorrer todas las pantallas (GET) no escribe en ninguna tabla de datos", b0 == b1 and before == after)

# ---- 4) STAGING: etiqueta, sin conectores, sin red, sin servicios de pago
c, html, hd = call(mk(), "GET", "/"); html = html.decode()
check("la etiqueta «STAGING · DATOS SINTÉTICOS · NO USAR PARA DECISIONES REALES» está en el HTML servido (antes de iniciar sesión)", S.STAGING_LABEL in html and 'id="envBanner"' in html)
check("cabecera X-Env: staging", hd.get("X-Env") == "staging")
check("navegación completa visible (12 pestañas)", all(x in html for x in ("INICIO", "LANZAMIENTOS", "MIS VENTAS", "PRODUCTOS", "DIRECTOR IA", "Panel DEMO", "Piloto PHIVITAL", "Pre-Launch", "K4", "EUROPA · MERCADOS", "Historial · Auditoría", "Estado · Conexiones", "Aprobaciones")))
check("enabled_connectors() vacío aunque AMAZON_PRO_CONNECTORS=keepa,sp-api,ads", S.enabled_connectors() == set())
check("lista blanca de salida vacía (sin Internet)", S.READ_ONLY_ALLOW == [])
check("IA y Keepa forzados a desactivados en staging", os.environ["AMAZON_PRO_AI_ENABLE"] == "0" and os.environ["AMAZON_PRO_KEEPA_ENABLE"] == "0" and os.environ["AMAZON_PRO_NO_WORKER"] == "1")
st_ = json.loads(call(vw, "GET", "/api/status")[1]); check("estado de conexiones: ningún conector CONECTADO/HABILITADO", bool(st_.get("connectors")) and not any(c.get("enabled") or "CONECTADO" in str(c.get("status", "")) for c in st_["connectors"]))
check("conectores: POST /api/connectors/test → 403 incluso con token de admin", call(adm, "POST", "/api/connectors/test", {"name": "keepa"}, headers={"X-Admin-Token": "t"})[0] == 403)
for var in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AMAZON_PRO_SPAPI_CLIENT_ID"):
    env = {**os.environ, "AMAZON_PRO_STAGING": "1", var: "x"}
    r = subprocess.run([sys.executable, "-c", "import server"], cwd=ROOT, env=env, capture_output=True, text=True)
    check(f"con {var} definida, staging NO arranca (y no imprime su valor)", r.returncode != 0 and "x\n" not in r.stderr.split("variables")[-1][-4:] and var in r.stderr)
# archivos estáticos: la UI bloquea además del backend
js = open(os.path.join(ROOT, "js/v03.js"), encoding="utf-8").read()
check("UI: api() no envía escrituras del viewer y lockUi desactiva controles de escritura", "(V.viewer || V.ro) && method !== 'GET'" in js and "function lockUi" in js)
print(f"\n{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
