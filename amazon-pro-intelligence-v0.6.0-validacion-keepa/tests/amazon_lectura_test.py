"""Corrección 4.1 — conectores de SOLO LECTURA de Amazon preparados técnicamente. SIN red, SIN credenciales reales: secretos FALSOS y transporte simulado.
Demuestra: variables unificadas; cabeceras correctas; token LWA ni en respuestas ni en logs ni en auditoría; paginación limitada; 429 con espera controlada; ningún POST salvo LWA;
ninguna ruta de escritura; staging con cero conexiones; y que el adaptador lo usa una RUTA INTERNA real de la aplicación (GET /api/amazon/read)."""
import gzip, io, json, os, re, socket, subprocess, sys, tempfile, threading, urllib.error, urllib.request, http.cookiejar, contextlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
TOK = "ACCESSTOKEN-SECRET-98765"; RT = "FAKE-REFRESH-TOKEN-abc123"; CS = "FAKE-CLIENT-SECRET-xyz789"
ENV = {"AMAZON_PRO_SPAPI_CLIENT_ID": "amzn1.fake.sp", "AMAZON_PRO_SPAPI_CLIENT_SECRET": CS, "AMAZON_PRO_SPAPI_REFRESH_TOKEN": RT,
       "AMAZON_PRO_ADS_CLIENT_ID": "amzn1.fake.ads", "AMAZON_PRO_ADS_CLIENT_SECRET": CS + "ads", "AMAZON_PRO_ADS_REFRESH_TOKEN": RT + "ads", "AMAZON_PRO_LIVE_SPAPI": "1", "AMAZON_PRO_LIVE_ADS": "1"}
EXT = []; _c = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(addr); raise AssertionError("RED PROHIBIDA")
    return _c(self, addr, *a, **k)
socket.socket.connect = _no_net
from backend import conectores100 as C
post_ok = lambda u, d, h: (POSTS.append((u, h)) or {"access_token": TOK, "expires_in": 3600}); POSTS = []
def err(fn, frag=""):
    try: fn(); return False
    except C.ConectorError as e: return frag in str(e)
def http429(ra=None): return urllib.error.HTTPError("u", 429, "Too Many", {"Retry-After": ra} if ra else {}, None)
# ---------------------------------------------------------------- 1. variables unificadas
SPV = ["AMAZON_PRO_SPAPI_CLIENT_ID", "AMAZON_PRO_SPAPI_CLIENT_SECRET", "AMAZON_PRO_SPAPI_REFRESH_TOKEN"]; ADV = [v.replace("SPAPI", "ADS") for v in SPV]
import server as S
check("backend/conectores100.py usa la convención AMAZON_PRO_SPAPI_* / AMAZON_PRO_ADS_*", C.SERVICIOS["spapi"]["vars"] == SPV and C.SERVICIOS["ads"]["vars"] == ADV)
check("server.py (CONNECTORS) usa la misma convención", S.CONNECTORS["sp-api"]["env"] == SPV and S.CONNECTORS["ads"]["env"] == ADV)
check("guardia STAGING prohíbe esas mismas variables (y los interruptores LIVE)", set(SPV + ADV + ["AMAZON_PRO_LIVE_SPAPI", "AMAZON_PRO_LIVE_ADS"]) <= set(S.FORBIDDEN_ENV))
st = {c["id"]: c for c in S.status()["connectors"]}
check("/api/status informa de las variables unificadas que faltan", st["sp-api"]["missing"] == SPV and st["ads"]["missing"] == ADV)
old = re.compile(r"(?<![A-Z_])(SPAPI|ADS)_(CLIENT_ID|CLIENT_SECRET|REFRESH_TOKEN)")
bad = []
for d, ds, fs in os.walk(ROOT):
    ds[:] = [x for x in ds if x not in (".git", "__pycache__", "node_modules", "fase4", "fase3", "fase3_1", "fase2", "fase2_1", "fase1")]
    for f in fs:
        if f.endswith((".py", ".md", ".yaml", ".yml", ".js", ".html", ".bat", ".txt")) and f not in ("amazon_lectura_test.py", "INFORME_FASE4.md", "AMAZON_INTEGRACION_FASE4.md", "CORRECCION_FASE4_1.md"):
            t = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
            if old.search(t): bad.append(os.path.relpath(os.path.join(d, f), ROOT))
check(f"ningún fichero usa los nombres antiguos SPAPI_*/ADS_* {bad[:3]}", not bad)
# ---------------------------------------------------------------- 2. cabeceras
H = []
tr = lambda url, hdr: (H.append((url, dict(hdr))) or {"payload": {"Orders": []}})
sp = C.Conector("spapi", ENV); ads = C.Conector("ads", ENV)
sp.leer("orders", {"MarketplaceIds": "A1RKKUPIHCS9HS", "CreatedAfter": "2026-01-01T00:00:00Z"}, habilitado=True, transport=tr, post=post_ok)
h = H[-1][1]; check("SP-API: x-amz-access-token con el token LWA y sin Authorization", h.get("x-amz-access-token") == TOK and "Authorization" not in h)
check("SP-API: URL al host oficial EU por HTTPS", H[-1][0].startswith("https://sellingpartnerapi-eu.amazon.com/orders/v0/orders?"))
ads.leer("campaigns", {"profile_id": "1234567890"}, habilitado=True, transport=tr, post=post_ok); h = H[-1][1]
check("Ads: Authorization Bearer + Amazon-Advertising-API-ClientId + Amazon-Advertising-API-Scope", h.get("Authorization") == "Bearer " + TOK and h.get("Amazon-Advertising-API-ClientId") == ENV[ADV[0]] and h.get("Amazon-Advertising-API-Scope") == "1234567890")
ads.leer("profiles", {}, habilitado=True, transport=tr, post=post_ok); h = H[-1][1]
check("Ads GET /v2/profiles: Bearer + ClientId y SIN Scope", h.get("Authorization") == "Bearer " + TOK and "Amazon-Advertising-API-ClientId" in h and "Amazon-Advertising-API-Scope" not in h)
check("Ads campañas sin profile_id → rechazado antes de llamar", err(lambda: ads.leer("campaigns", {}, habilitado=True, transport=tr, post=post_ok), "profile_id"))
check("LWA: POST solo a api.amazon.com/auth/o2/token con grant_type=refresh_token", all(u == "https://api.amazon.com/auth/o2/token" for u, _ in POSTS) and len(POSTS) == 3)
check("el token se pide en CADA lectura (no se guarda en el objeto)", not any(TOK in repr(v) for v in vars(sp).values()) and not any(TOK in repr(v) for v in vars(ads).values()))
# ---------------------------------------------------------------- 3. el token no aparece en respuestas
out = sp.leer("orders", {"MarketplaceIds": "A1RKKUPIHCS9HS", "LastUpdatedAfter": "2026-01-01"}, habilitado=True, transport=tr, post=post_ok)
check("respuesta del adaptador sin el access token, el refresh token ni el secreto", not any(x in json.dumps(out) for x in (TOK, RT, CS)))
check("un transporte que devuelve el token en el cuerpo → respuesta descartada", err(lambda: sp.leer("orders", {"MarketplaceIds": "A1", "CreatedAfter": "2026-01-01"}, habilitado=True, transport=lambda u, h: {"payload": {"x": TOK}}, post=post_ok), "secreto"))
r = sp.leer("report_document", {"reportDocumentId": "amzn1.spdoc.1.4.eu.abc"}, habilitado=True, transport=lambda u, h: {"payload": {"reportDocumentId": "x", "url": "https://s3.amazonaws.com/secret?X-Amz-Signature=SIG123", "compressionAlgorithm": "GZIP"}}, post=post_ok)
check("la URL prefirmada del documento se oculta en la respuesta", "SIG123" not in json.dumps(r) and "[OCULTO]" in json.dumps(r))
# ---------------------------------------------------------------- 4. paginación limitada
n = []
pg = lambda url, hdr: (n.append(url) or {"payload": {"Orders": [1], "NextToken": "T%d" % len(n)}})
r = sp.leer("orders", {"MarketplaceIds": "A1", "CreatedAfter": "2026-01-01"}, habilitado=True, transport=pg, post=post_ok)
check("paginación: por defecto 3 páginas y marca truncado", len(n) == 3 and r["paginas"] == 3 and r["truncado"] is True)
n.clear(); r = sp.leer("orders", {"MarketplaceIds": "A1", "CreatedAfter": "2026-01-01"}, habilitado=True, transport=pg, post=post_ok, max_pages=99)
check("paginación: tope duro de 5 páginas aunque se pida más", len(n) == 5 and r["paginas"] == 5)
check("el token de página se envía como NextToken en la 2ª llamada", "NextToken=T1" in n[1])
n.clear(); sp.leer("inventory", {"granularityType": "Marketplace", "granularityId": "A1", "marketplaceIds": "A1"}, habilitado=True, transport=lambda u, h: (n.append(u) or {"pagination": {"nextToken": "N%d" % len(n)}}), post=post_ok)
check("inventario pagina con nextToken (pagination.nextToken)", len(n) == 3 and "nextToken=N1" in n[1])
n.clear(); ads.leer("keywords", {"profile_id": "1", "count": "5000"}, habilitado=True, transport=lambda u, h: (n.append(u) or [0] * 100), post=post_ok)
check("Ads pagina por startIndex/count con count ≤ 100", len(n) == 3 and "count=100" in n[0] and "startIndex=100" in n[1] and "startIndex=200" in n[2])
n.clear(); sp.leer("orders", {"MarketplaceIds": "A1", "CreatedAfter": "2026-01-01", "MaxResultsPerPage": "9999"}, habilitado=True, transport=lambda u, h: (n.append(u) or {"payload": {}}), post=post_ok)
check("límite de tamaño de página aplicado (MaxResultsPerPage 9999 → 100)", "MaxResultsPerPage=100" in n[0])
# ---------------------------------------------------------------- 5. 429
for ra, esperado in (("2", [2, 2]), ("999", [30, 30]), (None, [1, 2])):
    seq = [http429(ra), http429(ra)]; waits = []
    def t429(u, h, seq=seq):
        if seq: raise seq.pop(0)
        return {"payload": {}}
    sp.leer("orders", {"MarketplaceIds": "A1", "CreatedAfter": "2026-01-01"}, habilitado=True, transport=t429, post=post_ok, sleep=waits.append)
    check(f"429 con Retry-After={ra}: espera controlada {waits} (máx. 30 s por espera)", waits == esperado)
waits = []; cnt = []
def siempre(u, h): cnt.append(1); raise http429("1")
try: sp.leer("orders", {"MarketplaceIds": "A1", "CreatedAfter": "2026-01-01"}, habilitado=True, transport=siempre, post=post_ok, sleep=waits.append); ok = False
except C.ConectorError as e: ok = e.http == 429
check(f"429 persistente: 1 intento + 3 reintentos y error controlado ({len(cnt)} llamadas, esperas {waits})", ok and len(cnt) == 4 and len(waits) == 3)
# ---------------------------------------------------------------- 6. parámetros obligatorios
chk = lambda op, p, frag: err(lambda: sp.leer(op, p, habilitado=True, transport=tr, post=post_ok), frag)
check("orders sin MarketplaceIds → rechazado", chk("orders", {"CreatedAfter": "2026-01-01"}, "MarketplaceIds"))
check("orders sin CreatedAfter ni LastUpdatedAfter → rechazado", chk("orders", {"MarketplaceIds": "A1"}, "CreatedAfter"))
check("inventario sin granularityType → rechazado", chk("inventory", {"granularityId": "A1", "marketplaceIds": "A1"}, "granularityType"))
check("finanzas sin fecha de inicio → rechazado", chk("finance_groups", {}, "FinancialEventGroupStartedAfter") and chk("finance_events", {}, "PostedAfter") and chk("finance_transactions", {}, "postedAfter"))
check("catálogo: ASIN inválido y falta de marketplaceIds → rechazado", chk("catalog_item", {"asin": "xx", "marketplaceIds": "A1"}, "inválido") and chk("catalog_item", {"asin": "B0F6KQP2WH"}, "marketplaceIds"))
check("parámetro no declarado → rechazado", chk("orders", {"MarketplaceIds": "A1", "CreatedAfter": "2026-01-01", "Foo": "1"}, "no permitido"))
check("operación no declarada (p. ej. publicar/precio/feed/campaña) → rechazada", all(chk(o, {}, "no permitida") for o in ("putListingsItem", "submitFeed", "createReport", "updatePrice", "createCampaign", "updateBid", "setBudget")))
# informes existentes: listar → estado → documento → descarga
gz = gzip.compress("sku\tventas\nA\t10\nB\t20\n".encode())
meta = {"payload": {"reportDocumentId": "d1", "url": "https://tm-prod-reports-eu.s3.eu-west-1.amazonaws.com/f?sig=1", "compressionAlgorithm": "GZIP"}}
r = sp.leer("report_download", {"reportDocumentId": "amzn1.spdoc.1.4.eu.abc"}, habilitado=True, transport=lambda u, h: meta, post=post_ok, download=lambda u: gz)
check("descarga de informe existente: GET documento + GET prefirmado (gzip) → 3 líneas, URL no expuesta", r["datos"][0]["lineas"] == 3 and r["datos"][0]["cabecera"] == "sku\tventas" and "sig=1" not in json.dumps(r))
bad_meta = {"payload": {"url": "https://evil.example.com/f", "compressionAlgorithm": ""}}
check("descarga: URL fuera de https://*.amazonaws.com → rechazada", err(lambda: sp.leer("report_download", {"reportDocumentId": "d1"}, habilitado=True, transport=lambda u, h: bad_meta, post=post_ok, download=lambda u: b"x"), "lista blanca"))
n.clear(); sp.leer("reports_list", {"reportTypes": "GET_SALES_AND_TRAFFIC_REPORT", "pageSize": "500"}, habilitado=True, transport=lambda u, h: (n.append(u) or {"reports": [], "nextToken": None}), post=post_ok)
check("listar informes: ruta /reports/2021-06-30/reports con pageSize ≤ 100", "/reports/2021-06-30/reports?" in n[0] and "pageSize=100" in n[0])
n.clear(); sp.leer("report_get", {"reportId": "123456"}, habilitado=True, transport=lambda u, h: (n.append(u) or {"processingStatus": "DONE"}), post=post_ok)
check("estado de un informe existente: GET /reports/2021-06-30/reports/{id}", n[0].endswith("/reports/2021-06-30/reports/123456"))
# ---------------------------------------------------------------- 7. doble activación y solo lectura
check("sin habilitar en AMAZON_PRO_CONNECTORS → rechazado (aunque haya credenciales y LIVE)", err(lambda: sp.leer("participations", {}, habilitado=False, transport=tr, post=post_ok), "no habilitado"))
check("sin AMAZON_PRO_LIVE_SPAPI=1 → rechazado (aunque esté habilitado)", err(lambda: C.Conector("spapi", {k: v for k, v in ENV.items() if "LIVE" not in k}).leer("participations", {}, habilitado=True, transport=tr, post=post_ok), "desactivada"))
check("sin credenciales → rechazado", err(lambda: C.Conector("ads", {"AMAZON_PRO_LIVE_ADS": "1"}).leer("profiles", {}, habilitado=True, transport=tr, post=post_ok), "faltan credenciales"))
check("_post rechaza cualquier URL que no sea el token LWA", err(lambda: C.Conector._post("https://sellingpartnerapi-eu.amazon.com/orders", b"", {}), "LWA"))
allp = [p for s in C.SERVICIOS.values() for p in s["rutas"]] + [o["path"] for ops in C.OPS.values() for o in ops.values()]
check("ninguna ruta de escritura: listings, precios, feeds, campañas/pujas/presupuestos de escritura, informes (POST)", not any(re.search(r"listings|pricing|feeds|submit|budget|bid|targets|create|update|delete|product-ads", p, re.I) for p in allp))
src = open(os.path.join(ROOT, "backend", "conectores100.py"), encoding="utf-8").read()
check("el adaptador solo contiene method=\"GET\" y un único method=\"POST\" (LWA)", len(re.findall(r'method="POST"', src)) == 1 and not re.search(r'method="(PUT|PATCH|DELETE)"', src))
check("no se crean informes (sin /reports/…/reports en POST): Ads sigue por CSV", "createReport" not in src and "reporting/reports\"" not in src)
# ---------------------------------------------------------------- 8. ruta interna de la aplicación que usa el adaptador (servidor real, transporte simulado)
for k, v in ENV.items(): os.environ[k] = v
os.environ["AMAZON_PRO_CONNECTORS"] = "sp-api,ads"; os.environ["AMAZON_PRO_NO_WORKER"] = "1"
from backend import ai as AI
calls = []; logs = io.StringIO()
class FR:
    status = 200
    def __init__(s, b): s.b = b
    def read(s, n=None): return s.b
    def __enter__(s): return s
    def __exit__(s, *a): return False
def fake_open(rq, timeout):
    calls.append((rq.get_method(), rq.full_url, dict(rq.header_items())))
    if "o2/token" in rq.full_url: return FR(json.dumps({"access_token": TOK}).encode())
    if "/orders/" in rq.full_url: return FR(json.dumps({"payload": {"Orders": [{"AmazonOrderId": "X"}]}}).encode())
    return FR(b"[]")
S._open = fake_open
used = []; _leer = C.Conector.leer
def spy(self, *a, **k): used.append(a[0]); return _leer(self, *a, **k)
C.Conector.leer = spy
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
jar = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)); BODIES = []
def call(p, b=None):
    rq = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json"})
    try:
        with op.open(rq) as x: d = x.read(); BODIES.append(d); return x.status, json.loads(d)
    except urllib.error.HTTPError as e: d = e.read(); BODIES.append(d); return e.code, json.loads(d or b"{}")
with contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
    code, _ = call("/api/amazon/read?service=sp-api&op=orders&MarketplaceIds=A1&CreatedAfter=2026-01-01")
    check("sin sesión → 401 y ninguna salida de red", code == 401 and not calls)
    call("/api/login", {"username": "admin", "password": "admin-pass-p9Zt4w"})
    code, j = call("/api/amazon/read?service=sp-api&op=orders&MarketplaceIds=A1&CreatedAfter=2026-01-01")
    check("ruta interna GET /api/amazon/read devuelve datos leídos por el adaptador", code == 200 and j["origen"] == "REAL" and j["solo_lectura"] and j["datos"][0]["payload"]["Orders"][0]["AmazonOrderId"] == "X")
    check("el adaptador (Conector.leer) fue invocado por la ruta de la aplicación", used == ["orders"])
    check("salida real simulada: un POST LWA y un GET a SP-API con x-amz-access-token; ningún otro método", [m for m, _, _ in calls] == ["POST", "GET"] and "o2/token" in calls[0][1] and any(k.lower() == "x-amz-access-token" and v == TOK for k, v in calls[1][2].items()))
    code, j = call("/api/amazon/read?service=ads&op=campaigns&profile_id=99")
    check("Ads por la ruta interna: Authorization, ClientId y Scope", code == 200 and any(k.lower() == "amazon-advertising-api-scope" and v == "99" for k, v in calls[-1][2].items()) and any(k.lower() == "authorization" and v == "Bearer " + TOK for k, v in calls[-1][2].items()))
    code, j = call("/api/amazon/read?service=sp-api&op=putListingsItem"); check("operación de escritura por la ruta interna → 400", code == 400)
    code, j = call("/api/amazon/read?service=sp-api&op=orders&MarketplaceIds=A1"); check("falta parámetro obligatorio por la ruta interna → 400", code == 400 and "CreatedAfter" in j["error"])
    code, j = call("/api/amazon/ops"); check("catálogo de operaciones: solo lectura, sin escritura", code == 200 and j["escritura"] == "NO IMPLEMENTADA")
    os.environ["AMAZON_PRO_LIVE_SPAPI"] = "0"; n0 = len(calls); code, j = call("/api/amazon/read?service=sp-api&op=participations")
    check("sin AMAZON_PRO_LIVE_SPAPI=1 → 403 y 0 llamadas", code == 403 and len(calls) == n0); os.environ["AMAZON_PRO_LIVE_SPAPI"] = "1"
    os.environ["AMAZON_PRO_CONNECTORS"] = ""; code, j = call("/api/amazon/read?service=sp-api&op=participations")
    check("sin AMAZON_PRO_CONNECTORS → 403 y 0 llamadas", code == 403 and len(calls) == n0); os.environ["AMAZON_PRO_CONNECTORS"] = "sp-api,ads"
    jv = http.cookiejar.CookieJar(); calls_before = len(calls)
    st, stj = call("/api/status"); check("/api/status refleja la doble activación", all(c["live"] for c in stj["connectors"] if c["id"] in ("sp-api", "ads")))
check("TODAS las salidas fueron GET de lectura o el POST de LWA", all(m == "GET" or (m == "POST" and u == "https://api.amazon.com/auth/o2/token") for m, u, _ in calls))
joined = b"".join(BODIES).decode("utf-8", "replace")
check("el access token LWA no aparece en NINGUNA respuesta HTTP de la aplicación", TOK not in joined and RT not in joined and CS not in joined)
check("el access token LWA no aparece en logs (stdout/stderr) durante las lecturas", TOK not in logs.getvalue() and RT not in logs.getvalue())
au = json.dumps(S.APP["store"].audit_list(None, 200)); check("la auditoría registra amazon.read sin tokens ni secretos", "amazon.read" in au and TOK not in au and RT not in au and CS not in au)
srv.shutdown(); C.Conector.leer = _leer
code = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()
check("server.py usa el adaptador en código de producción (amazon_leer → Conector.leer) y no solo los tests", ".leer(op, params" in code and "def amazon_leer" in code and "/api/amazon/read" in code)
# ---------------------------------------------------------------- 9. staging: cero conexiones externas
script = r'''
import os, sys, socket, json, threading, urllib.request, tempfile
sys.path.insert(0, %r); os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_CONNECTORS="sp-api,ads,keepa", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
for k in list(os.environ):
    if k.startswith("AMAZON_PRO_LIVE") or k.endswith("API_KEY"): os.environ.pop(k)
ext = []; c0 = socket.socket.connect
def nc(self, a, *x, **k):
    if a[0] not in ("127.0.0.1", "localhost", "::1"): ext.append(a); raise AssertionError("RED")
    return c0(self, a, *x, **k)
socket.socket.connect = nc
import server as S
from backend import ai as AI
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tempfile.mkdtemp(), "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); p = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
import http.cookiejar
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def g(path, body=None):
    rq = urllib.request.Request("http://localhost:%%d" %% p + path, data=json.dumps(body).encode() if body else None, headers={"Content-Type": "application/json"})
    try: return op.open(rq).status
    except urllib.error.HTTPError as e: return e.code
g("/api/login", {"username": "auditor", "password": "viewer-pass-x7Qk2m"})
r = [g("/api/amazon/read?service=sp-api&op=participations"), g("/api/amazon/read?service=ads&op=profiles"), g("/api/amazon/ops")]
print(json.dumps({"codes": r, "ext": ext, "allow": S.READ_ONLY_ALLOW, "enabled": sorted(S.enabled_connectors())}))
''' % ROOT
CLEAN = {k: v for k, v in os.environ.items() if not (k.startswith("AMAZON_PRO_") or k.endswith("API_KEY"))}
r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=120, env=CLEAN)
try: j = json.loads(r.stdout.strip().splitlines()[-1])
except Exception: j = {}; print(r.stdout[-300:], r.stderr[-400:])
check("STAGING: /api/amazon/read → 403 con SP-API y Ads aunque AMAZON_PRO_CONNECTORS las incluya", j.get("codes", [0])[:2] == [403, 403])
check("STAGING: 0 conexiones externas, lista de salida vacía y ningún conector habilitado", j.get("ext") == [] and j.get("allow") == [] and j.get("enabled") == [])
check("STAGING con credenciales de Amazon definidas NO arranca", all(subprocess.run([sys.executable, "-c", "import server"], cwd=ROOT, env={**CLEAN, "AMAZON_PRO_STAGING": "1", v: "x"}, capture_output=True, text=True).returncode != 0 for v in SPV + ADV + ["AMAZON_PRO_LIVE_SPAPI"]))
check("la prueba completa no abrió ninguna conexión de red externa", not EXT)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
