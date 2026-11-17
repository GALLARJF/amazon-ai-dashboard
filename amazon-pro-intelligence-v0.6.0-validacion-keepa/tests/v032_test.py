"""V0.3.2 — control de acceso a /api/ai/usage, la clave nunca aparece (logs, respuestas HTTP, BD, exportables), expediente sintético y guardia de primera llamada. SIN red real."""
import http.client, json, os, subprocess, sys, tempfile, threading, time, urllib.parse, datetime, glob
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, director as D, synthetic as SY, pilot as P
from backend.store import Store
import server as S
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
TODAY = datetime.date.today().isoformat()
KEY = "sk-proj-CENTINELA-9f3a7c1e5b2d4a60-NO-ES-REAL"

# ---------- A. expediente sintético + guardia de primera llamada (host oficial parcheado, sin red) ----------
OFF = []; MODE = {"echo": False}
def fake_post(url, headers, body, timeout):
    if urllib.parse.urlparse(url).hostname != "api.openai.com": raise AssertionError("host no previsto")
    OFF.append(json.loads(body))
    txt = "Decisión [F1]." + (" clave=" + headers["Authorization"][7:] if MODE["echo"] else "")
    return 200, json.dumps({"id": "resp_test123", "object": "response", "status": "completed", "model": "gpt-6-luna", "output": [{"type": "message", "content": [{"type": "output_text", "text": txt}]}], "usage": {"input_tokens": 1000, "output_tokens": 50}})
AI._post = fake_post
ENVR = {"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": KEY, "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "1"}
st = Store(); sid = SY.ensure(st); sid2 = SY.ensure(st)
check("expediente sintético ÚNICO e idempotente", sid == sid2 and len(st.list(SY.ACCOUNT_ID, "dossier")) == 1)
acc = [a for a in st.db.execute("SELECT * FROM accounts").fetchall() if a["id"] == SY.ACCOUNT_ID][0]
check("cuenta sintética sin titular real ni marketplaces", "SINTÉTICO" in acc["legal_entity"] and acc["marketplaces"] == "[]" and acc["seller_central_ref"] is None)
rec = st.get(SY.ACCOUNT_ID, sid)
check("el sintético es elegible mientras está intacto", SY.eligible(SY.ACCOUNT_ID, rec))
check("contenido 100 % ficticio (todas las fuentes/evidencias son SINTÉTICO)", all(c["source"] == "SINTÉTICO" for c in rec["data"]["dossier"]["competitors"]) and "PhiVital" not in json.dumps(rec["data"]) and "PHIVITAL" not in json.dumps(rec["data"]))
tam = json.loads(json.dumps(rec)); tam["data"]["dossier"]["econ"]["price"] = 25.0
check("sintético ALTERADO → no elegible", not SY.eligible(SY.ACCOUNT_ID, tam))
st.create_account("otra", "o", "x"); other = st.put("otra", "dossier", {"origin": "PRUEBA", "synthetic": True, "fixture_sha256": rec["data"]["fixture_sha256"], "dossier": rec["data"]["dossier"]})
check("copia con la marca sintética en OTRA cuenta → no elegible", not SY.eligible("otra", st.get("otra", other)))
real = st.put("otra", "dossier", {"origin": "INCOMPLETO", "dossier": P.template(), "name": "PHIVITAL MAGNESIO"})
dr = D.Director(st, lambda: AI.config(ENVR))
r = dr.analyze("otra", real, "t", "resumen", today=TODAY)
check("ANTES de verificar la IA real, PHIVITAL no puede salir hacia OpenAI (guardia)", r["ai"]["reason"] == "PRIMERA_LLAMADA_SOLO_SINTETICO" and not OFF)
r = dr.analyze(SY.ACCOUNT_ID, sid, "t", "resumen", today=TODAY, dry_run=True)
check("vista previa (dry_run): muestra el prompt exacto, no llama y no reserva presupuesto", r["user"].startswith("Pregunta") and not OFF and st.ai_usage()["real_calls"] == 0)
r = dr.analyze(SY.ACCOUNT_ID, sid, "t", "resumen general", today=TODAY, confirm={"accepted": True, "model": "gpt-6-luna"})
run = st.get(SY.ACCOUNT_ID, r["ai_run"])["data"]
check("el sintético SÍ puede salir: 1 llamada, modo REAL, tokens del proveedor", len(OFF) == 1 and run["mode"] == "REAL" and run["token_source"] == "reportado_por_proveedor" and r["ai"]["mode"] == "REAL")
check("primera petición real: store=false, max_output_tokens, sin clave en el cuerpo", OFF[0]["store"] is False and OFF[0]["max_output_tokens"] == 2500 and KEY not in json.dumps(OFF[0]))
check("tras una ejecución REAL verificada, la IA real queda verificada", st.real_ai_verified() and dr.coworker_status(SY.ACCOUNT_ID)["ai"]["real_verified"])
r = dr.analyze("otra", real, "t", "resumen", today=TODAY)
check("con IA real verificada la guardia se levanta para el resto de expedientes", len(OFF) == 2 and r["ai"]["reason"] != "PRIMERA_LLAMADA_SOLO_SINTETICO")
u = st.ai_usage(); check("libro: 2 llamadas REAL liquidadas con coste real calculado", u["real_calls"] == 2 and u["uncertain_calls"] == 0 and abs(u["real_cost"] - 2 * (1000 * 0.1 + 50 * 0.5) / 1e6) < 1e-12)
# la guardia NO se activa por una ejecución simulada/local: se prueba con un store limpio
st2 = Store(); sid_b = SY.ensure(st2); st2.create_account("o2", "o", "x"); r_b = st2.put("o2", "dossier", {"origin": "INCOMPLETO", "dossier": P.template()})
st2.put(SY.ACCOUNT_ID, "ai_run", {"mode": "PRUEBA_LOCAL", "error": None, "token_source": "reportado_por_proveedor"}); st2.put(SY.ACCOUNT_ID, "ai_run", {"mode": "SIMULADA", "error": None})
st2.put(SY.ACCOUNT_ID, "ai_run", {"mode": "REAL", "error": "TIMEOUT", "token_source": None}); st2.put(SY.ACCOUNT_ID, "ai_run", {"mode": "REAL", "error": None, "token_source": "estimado_peor_caso"})
check("PRUEBA_LOCAL, SIMULADA, REAL con error o con tokens estimados NO verifican la IA real", not st2.real_ai_verified())
# redacción defensiva: proveedor que devuelve la clave en el texto
MODE["echo"] = True; OFF.clear()
st3 = Store(); sid3 = SY.ensure(st3); dr3 = D.Director(st3, lambda: AI.config(ENVR)); r = dr3.analyze(SY.ACCOUNT_ID, sid3, "t", "resumen", today=TODAY, confirm={"accepted": True, "model": "gpt-6-luna"})
dump = json.dumps([x["data"] for x in st3.list(SY.ACCOUNT_ID, "ai_run")]) + json.dumps(r, default=str) + json.dumps([x["data"] for x in st3.list(SY.ACCOUNT_ID, "query")])
check("si el proveedor devolviera la clave en su texto, no se guarda ni se muestra", KEY not in dump and OFF)
MODE["echo"] = False; AI._post = None

# ---------- B. servidor REAL en subproceso: ACL de /api/ai/usage y ausencia de la clave en todo ----------
LOGS = []
class Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n); auth = self.headers.get("Authorization", "")
        if LOGS and LOGS[-1] == "401":  # proveedor «torpe» que devuelve en el cuerpo de error la cabecera recibida
            self.send_response(401); b = json.dumps({"error": {"message": "Incorrect API key provided: " + auth}}).encode()
        else:
            self.send_response(200); b = json.dumps({"status": "completed", "model": "gpt-6-luna", "output": [{"type": "message", "content": [{"type": "output_text", "text": "Decisión [F1]. eco: " + auth}]}], "usage": {"input_tokens": 900, "output_tokens": 40}}).encode()
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
fs = ThreadingHTTPServer(("127.0.0.1", 0), Fake); threading.Thread(target=fs.serve_forever, daemon=True).start()
tmp = tempfile.mkdtemp(); dbp = os.path.join(tmp, "leak.db")
free = ThreadingHTTPServer(("127.0.0.1", 0), Fake); PORT = free.server_address[1]; free.server_close()
env = dict(os.environ, AMAZON_PRO_DB=dbp, AMAZON_PRO_ADMIN_PASSWORD="admin-password-123", AMAZON_PRO_AI_PROVIDER="openai", OPENAI_API_KEY=KEY, AMAZON_PRO_AI_ENABLE="1", AMAZON_PRO_AI_MONTHLY_BUDGET="1",
           AMAZON_PRO_AI_BASE_URL=f"http://127.0.0.1:{fs.server_address[1]}", AMAZON_PRO_AI_ALLOW_LOOPBACK="1", PYTHONDONTWRITEBYTECODE="1")
proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "server.py"), str(PORT)], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
for _ in range(60):
    try: http.client.HTTPConnection("127.0.0.1", PORT, timeout=1).request("GET", "/api/status"); break
    except OSError: time.sleep(0.2)
class C:
    def __init__(s): s.cookie = None; s.csrf = None; s.seen = []
    def req(s, m, path, body=None):
        h = {"Host": f"127.0.0.1:{PORT}"}
        if s.cookie: h["Cookie"] = "apisid=" + s.cookie
        data = json.dumps(body).encode() if body is not None else None
        if data: h["Content-Type"] = "application/json"
        if m == "POST" and s.csrf: h["X-CSRF-Token"] = s.csrf
        c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=30); c.request(m, path, data, h); r = c.getresponse(); t = r.read().decode(); s.seen.append(t + str(r.getheaders()))
        try: return r.status, json.loads(t)
        except Exception: return r.status, t
    def login(s, u, p):
        c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=10); c.request("POST", "/api/login", json.dumps({"username": u, "password": p}), {"Host": f"127.0.0.1:{PORT}", "Content-Type": "application/json"})
        r = c.getresponse(); t = r.read().decode(); s.seen.append(t + str(r.getheaders()))
        if r.status == 200: s.cookie = r.getheader("Set-Cookie").split("apisid=")[1].split(";")[0]; s.csrf = json.loads(t)["csrf"]
        return r.status
adm = C(); check("login admin", adm.login("admin", "admin-password-123") == 200)
# usuarios no admin (se crean en la misma BD con un Store aparte; SQLite permite escritores secuenciales)
s_ = Store(dbp); s_.create_user("ana", "analista-pass-1", "analyst", [SY.ACCOUNT_ID]); s_.create_user("pablo", "aprobador-pass-1", "approver", [SY.ACCOUNT_ID]); s_.db.close()
ana, pab = C(), C(); ana.login("ana", "analista-pass-1"); pab.login("pablo", "aprobador-pass-1")
check("/api/ai/usage sin sesión → 401", C().req("GET", "/api/ai/usage")[0] == 401)
check("/api/ai/usage analista → 403", ana.req("GET", "/api/ai/usage")[0] == 403)
check("/api/ai/usage aprobador → 403", pab.req("GET", "/api/ai/usage")[0] == 403)
code, u = adm.req("GET", "/api/ai/usage"); check("/api/ai/usage admin → 200 con presupuesto y sin clave", code == 200 and u["monthly_budget"] == 1.0 and "key" not in json.dumps(u).lower())
check("/api/ai/reconcile: analista 403, sin sesión 401, id inválido (admin) 400", ana.req("POST", "/api/ai/reconcile", {"id": "x", "actual_cost": 0})[0] == 403 and C().req("POST", "/api/ai/reconcile", {"id": "x", "actual_cost": 0})[0] in (401, 403) and adm.req("POST", "/api/ai/reconcile", {"id": "x", "actual_cost": 0})[0] == 400)
check("/api/ai/usage no admite POST ni métodos de escritura sin CSRF", adm.req("POST", "/api/ai/usage", {})[0] in (404, 405, 403))
st_code, stt = adm.req("GET", "/api/ai/status"); check("/api/ai/status: sin clave, con fecha de verificación de tarifas", st_code == 200 and stt["key_present"] is True and stt["prices_verified_on"] == "2026-11-16")
accts = adm.req("GET", "/api/accounts")[1]["accounts"]; check("la cuenta sintética aparece al admin", any(a["id"] == SY.ACCOUNT_ID for a in accts))
did = adm.req("GET", f"/api/records?account={SY.ACCOUNT_ID}&kind=dossier")[1]["records"][0]["id"]
c1, j1 = adm.req("POST", "/api/director/ask", {"account": SY.ACCOUNT_ID, "dossier": did, "question": "resumen general"})
runs = adm.req("GET", f"/api/records?account={SY.ACCOUNT_ID}&kind=ai_run")[1]["records"]
check("Director vía HTTP: el proveedor devolvió la cabecera en su texto y quedó REDACTADA ([CLAVE-OCULTA])", c1 == 200 and any("[CLAVE-OCULTA]" in (r["data"].get("response") or "") for r in runs))
LOGS.append("401"); c2, j2 = adm.req("POST", "/api/director/ask", {"account": SY.ACCOUNT_ID, "dossier": did, "question": "otra"}); LOGS.clear()
check("proveedor que devuelve la clave en el cuerpo de un 401 → solo HTTP_401, sin cuerpo", c2 == 200 and j2["ai"]["reason"] == "HTTP_401" and KEY not in json.dumps(j2))
for k in ("dossier", "task", "ai_run", "query", "approval", "evidence", "news"): adm.req("GET", f"/api/records?account={SY.ACCOUNT_ID}&kind={k}")
adm.req("GET", f"/api/audit?account={SY.ACCOUNT_ID}"); adm.req("GET", "/api/coworkers/status?account=" + SY.ACCOUNT_ID); adm.req("GET", "/api/status")
time.sleep(0.3); proc.terminate()
try: out = proc.communicate(timeout=10)[0]
except Exception: proc.kill(); out = ""
allhttp = "\n".join(adm.seen + ana.seen + pab.seen)
check("la clave NO aparece en la salida del servidor (stdout/stderr = logs)", KEY not in out and len(out) > 50)
check("la clave NO aparece en ninguna respuesta HTTP ni cabecera", KEY not in allhttp and "sk-proj" not in allhttp)
blob = b"".join(open(f, "rb").read() for f in glob.glob(dbp + "*"))
check("la clave NO aparece en la base de datos (registros, auditoría, WAL)", KEY.encode() not in blob and len(blob) > 1000)
exp = []
for dp, _, fs_ in os.walk(ROOT):
    if any(x in dp for x in (".git", "__pycache__", "node_modules")): continue
    for f in fs_:
        if f.endswith((".db", ".zip", ".png")): continue
        try: exp.append((os.path.join(dp, f), open(os.path.join(dp, f), "r", errors="ignore").read()))
        except OSError: pass
leaks = [p for p, t in exp if KEY in t and not p.endswith("v032_test.py")]
check("la clave NO aparece en ningún archivo del proyecto (código, docs, demos, capturas de texto, exportables)", not leaks)
check("el servidor de verdad escucha solo en 127.0.0.1 y los conectores siguen desactivados", "Conectores habilitados: NINGUNO" in out and "solo 127.0.0.1" in out)
# preflight: sin red y sin clave en su salida
pf = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "preflight_primera_llamada.py")], env=env, capture_output=True, text=True, timeout=60, cwd=ROOT)
check("preflight: termina bien, no imprime la clave, no hace red y declara LISTO", pf.returncode == 0 and KEY not in pf.stdout + pf.stderr and "LISTO PARA LLAMAR" in pf.stdout)
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
