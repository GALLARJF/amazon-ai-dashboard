"""V0.3.4 — confirmación previa, procedencia OpenAI, registro mínimo, explicaciones de error y ACL de /api/ai/calls. SIN red (host oficial parcheado)."""
import datetime, http.client, json, os, re, sys, tempfile, threading, urllib.error, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, director as D, synthetic as SY, pilot as P
from backend.store import Store
import server as S
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
TODAY = datetime.date.today().isoformat(); KEY = "sk-proj-CENTINELA-V034-aabbccddeeff00112233-NO-REAL"
ENV = {"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": KEY, "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "2", "AMAZON_PRO_AI_MAX_COST": "0.02"}
SENT = []; RESP = {"obj": "response", "id": "resp_abc", "text": "Decisión GO [F1]."}
def fake(url, h, body, t):
    SENT.append(json.loads(body)); r = {"status": "completed", "model": "gpt-6-luna", "output": [{"type": "message", "content": [{"type": "output_text", "text": RESP["text"]}]}], "usage": {"input_tokens": 1000, "output_tokens": 60}}
    if RESP["obj"]: r["object"] = RESP["obj"]
    if RESP["id"]: r["id"] = RESP["id"]
    return 200, json.dumps(r)
AI._post = fake
st = Store(); sid = SY.ensure(st); dr = D.Director(st, lambda: AI.config(ENV)); OK = {"accepted": True, "model": "gpt-6-luna"}
n_tasks = lambda: len(st.list(SY.ACCOUNT_ID, "task", limit=500))
r = dr.analyze(SY.ACCOUNT_ID, sid, "t", "resumen", today=TODAY)
check("primera llamada facturable: se pide confirmación y NO se envía ni se crea nada", r.get("needs_confirmation") is True and not SENT and n_tasks() == 0 and st.ai_usage()["real_calls"] == 0)
check("la petición de confirmación informa de modelo, coste máximo, tope, presupuesto y datos enviados", r["model"] == "gpt-6-luna" and 0 < r["estimated_worst_case"] <= r["max_cost_per_run"] == 0.02 and r["monthly_budget"] == 2 and "SINTÉTICO" in r["data_sent"] and "Nada de PHIVITAL" in r["data_sent"])
for bad in (None, {}, {"accepted": False, "model": "gpt-6-luna"}, {"accepted": "true", "model": "gpt-6-luna"}, {"accepted": True, "model": "gpt-6.1-sol"}, {"accepted": True}):
    check(f"confirmación inválida {bad!r} → sigue pidiendo confirmación", dr.analyze(SY.ACCOUNT_ID, sid, "t", "r", today=TODAY, confirm=bad).get("needs_confirmation") is True and not SENT)
# procedencia: sin object/id → no verificada
RESP.update(obj=None, id=None); r = dr.analyze(SY.ACCOUNT_ID, sid, "t", "resumen", today=TODAY, confirm=OK)
check("respuesta sin forma documentada (sin id/object): se muestra pero procedencia NO verificada y la IA real NO queda verificada", r["ai_summary"]["origin_verified"] is False and not st.real_ai_verified())
check("tras esa llamada se vuelve a pedir confirmación (sigue sin verificarse)", dr.analyze(SY.ACCOUNT_ID, sid, "t", "r", today=TODAY).get("needs_confirmation") is True)
RESP.update(obj="response", id="resp_abc"); r = dr.analyze(SY.ACCOUNT_ID, sid, "t", "resumen", today=TODAY, confirm=OK)
s = r["ai_summary"]
check("respuesta con id y object=response vía HTTPS al host oficial: procedencia verificada", s["origin_verified"] is True and s["response_id"] == "resp_abc" and s["mode"] == "REAL" and st.real_ai_verified())
check("se registran estado, duración, tokens y coste estimado", s["duration_ms"] is not None and (s["tokens_in"], s["tokens_out"]) == (1000, 60) and abs(s["cost_estimate"] - (1000 * 0.1 + 60 * 0.5) / 1e6) < 1e-12)
check("verificada la IA real, ya no se pide confirmación", "needs_confirmation" not in dr.analyze(SY.ACCOUNT_ID, sid, "t", "r", today=TODAY))
calls = st.ai_calls()
check("registro mínimo (auditoría ai.call): solo campos permitidos, sin texto, sin prompt, sin clave", calls and all(set(c) <= {"status", "error", "mode", "model", "duration_ms", "tokens_in", "tokens_out", "cost_estimate", "currency", "response_id", "origin_verified", "ts"} for c in calls) and KEY not in json.dumps(calls) and "Decisión" not in json.dumps(calls))
check("el prompt enviado solo contiene datos del sintético (nada de PHIVITAL)", all("PHIVITAL" not in json.dumps(x).upper() and "PHIVITAL" not in x["input"].upper() for x in SENT))
# PHIVITAL no sale antes de verificar y su expediente no se altera
st2 = Store(); sid2 = SY.ensure(st2); st2.create_account("ph", "PhiVital", "POR CONFIRMAR"); ph = st2.put("ph", "dossier", {"origin": "INCOMPLETO", "dossier": P.template(), "name": "PHIVITAL Magnesio · piloto"})
dump = json.dumps(st2.get("ph", ph), sort_keys=True); SENT.clear(); d2 = D.Director(st2, lambda: AI.config(ENV))
r = d2.analyze("ph", ph, "t", "resumen", today=TODAY)
check("PHIVITAL no necesita confirmación porque NO puede salir: queda SIN IA con explicación comprensible", r["ai"]["reason"] == "PRIMERA_LLAMADA_SOLO_SINTETICO" and "SINTÉTICO · PRUEBA API" in r["ai"]["reason_text"] and not SENT)
check("el expediente PHIVITAL no cambia tras analizarlo (sus resultados van a tareas/consultas aparte)", json.dumps(st2.get("ph", ph), sort_keys=True) == dump)
# renombrado de BD antigua
st3 = Store(); st3.create_account(SY.ACCOUNT_ID, "x", "SINTÉTICO", None, []); old = st3.put(SY.ACCOUNT_ID, "dossier", {"origin": "PRUEBA", "synthetic": True, "name": "SINTÉTICO · Magnesio PRUEBA (única para la primera llamada real)", "fixture_sha256": SY.digest(SY.fixture(TODAY)), "dossier": SY.fixture(TODAY)})
SY.ensure(st3); rec = st3.get(SY.ACCOUNT_ID, old)
check("BD de V0.3.3: el sintético se renombra a «SINTÉTICO · PRUEBA API» y sigue siendo elegible (huella intacta)", rec["data"]["name"] == "SINTÉTICO · PRUEBA API" and SY.eligible(SY.ACCOUNT_ID, rec) and len(st3.list(SY.ACCOUNT_ID, "dossier")) == 1)
# explicaciones
src = open(os.path.join(ROOT, "backend", "ai.py")).read() + open(os.path.join(ROOT, "backend", "director.py")).read()
codes = set(re.findall(r'AIError\("([A-Z_0-9]+)"\)', src)) | {"PRIMERA_LLAMADA_SOLO_SINTETICO", "CONFIRMACION_REQUERIDA", "HTTP_401", "HTTP_404", "HTTP_429", "HTTP_500", "RESPUESTA_INCOMPLETA_max_output_tokens", "RESPUESTA_NO_ANCLADA: x"}
missing = [c for c in codes if AI.explain(c) == c]
check("TODO código de error que el sistema puede producir tiene explicación en español llano", not missing)
check("las explicaciones no contienen datos sensibles ni la clave", all(KEY not in AI.explain(c) and "sk-" not in AI.explain(c) for c in codes))
check("los 4xx explican que no se cobra; los timeouts/5xx avisan de consumo INCIERTO", all("No se cobra nada" in AI.explain(c) for c in ("HTTP_401", "HTTP_403", "HTTP_404", "HTTP_429")) and all("INCIERTO" in AI.explain(c) for c in ("TIMEOUT", "HTTP_500", "HTTP_503", "RESPUESTA_NO_JSON")))
# error real mapeado en el Director (401)
def p401(url, h, body, t): raise urllib.error.HTTPError(url, 401, "x", {}, io.BytesIO(b"eco " + h["Authorization"].encode()))
AI._post = p401; st4 = Store(); sid4 = SY.ensure(st4); r = D.Director(st4, lambda: AI.config(ENV)).analyze(SY.ACCOUNT_ID, sid4, "t", "r", today=TODAY, confirm=OK)
check("Director con 401: SIN IA + explicación comprensible, sin cuerpo del error ni clave", r["ai"]["reason"] == "HTTP_401" and "no aceptó la clave" in r["ai"]["reason_text"] and KEY not in json.dumps(r, default=str) and r["answer"])
# ACL /api/ai/calls
AI._post = fake
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tempfile.mkdtemp(), "a.db"), cfg_fn=lambda: AI.config(ENV), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); S.APP["store"].create_user("ana", "analista-pass-1", "analyst", ["phivital-pendiente"])
def login(u, p):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10); c.request("POST", "/api/login", json.dumps({"username": u, "password": p}), {"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"}); r = c.getresponse(); r.read()
    return r.getheader("Set-Cookie").split("apisid=")[1].split(";")[0] if r.status == 200 else None
def get(path, ck=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10); c.request("GET", path, headers=dict({"Host": f"127.0.0.1:{port}"}, **({"Cookie": "apisid=" + ck} if ck else {}))); r = c.getresponse(); return r.status, r.read().decode()
check("/api/ai/calls: sin sesión 401, analista 403, admin 200", get("/api/ai/calls")[0] == 401 and get("/api/ai/calls", login("ana", "analista-pass-1"))[0] == 403 and get("/api/ai/calls", login("admin", "admin-password-123"))[0] == 200)
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
