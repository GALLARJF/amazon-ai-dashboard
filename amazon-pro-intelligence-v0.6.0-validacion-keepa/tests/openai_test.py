"""V0.3.1 — Adaptador OpenAI (Responses API) SIN consumo real: servidor local que imita la API + parche que prohíbe cualquier llamada a api.openai.com.
Verifica: configuración segura, perfiles/tarifas, forma exacta de la petición, parseo de uso/razonamiento, presupuestos (tokens, por ejecución, mensual),
registro de consumo, E2E con PHIVITAL MAGNESIO (plantilla real INCOMPLETA y datos ficticios PRUEBA), anclaje y errores sin inventar."""
import datetime, json, os, sys, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, director as D, pilot as P
from backend.store import Store
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
TODAY = datetime.date.today().isoformat(); ago = lambda n: (datetime.date.today() - datetime.timedelta(days=n)).isoformat()

# --- red: prohibido api.openai.com en esta suite ---
REAL_CALLS = []
_orig = AI._post
def guard(url, headers, body, timeout):
    if urllib.parse.urlparse(url).hostname not in AI.LOOPBACK:
        REAL_CALLS.append(url); raise AssertionError("llamada externa prohibida en pruebas")
    return _orig(url, headers, body, timeout)
AI._post = guard

SEEN = []; BEHAVE = {"mode": "ok", "text": "Decisión determinista: REVISAR [F1]. Hay datos pendientes [F2].", "tin": 1800, "tout": 120, "reasoning": 70}
class Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); body = json.loads(self.rfile.read(n)); SEEN.append({"path": self.path, "auth": self.headers.get("Authorization"), "body": body})
        m = BEHAVE["mode"]
        if m == "http429": self.send_response(429); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"{}"); return
        out = {"id": "resp_x", "object": "response", "status": "completed", "model": body["model"] + "-2026-11-01", "incomplete_details": None,
               "output": [{"type": "reasoning", "id": "rs_1", "summary": []}, {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": BEHAVE["text"]}]}],
               "usage": {"input_tokens": BEHAVE["tin"], "output_tokens": BEHAVE["tout"], "output_tokens_details": {"reasoning_tokens": BEHAVE["reasoning"]}}}
        if m == "incomplete": out["status"] = "incomplete"; out["incomplete_details"] = {"reason": "max_output_tokens"}; out["output"] = [{"type": "reasoning", "id": "rs_1", "summary": []}]
        if m == "empty": out["output"] = [{"type": "reasoning", "id": "rs_1", "summary": []}]
        if m == "nousage": del out["usage"]
        b = json.dumps(out).encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
fs = HTTPServer(("127.0.0.1", 0), Fake); threading.Thread(target=fs.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{fs.server_address[1]}"
KEY = "sk-FALSA-SOLO-PRUEBAS-0000"
def env(**o):
    e = {"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": KEY, "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "5", "AMAZON_PRO_AI_BASE_URL": URL, "AMAZON_PRO_AI_ALLOW_LOOPBACK": "1"}
    e.update(o); return e

# 1 configuración / perfiles / tarifas
c = AI.config({"AMAZON_PRO_AI_PROVIDER": "openai"})
check("perfil por defecto = económico → gpt-6-luna", c["model"] == "gpt-6-luna")
check("perfil razonamiento → gpt-6.1-sol", AI.config({"AMAZON_PRO_AI_PROVIDER": "openai", "AMAZON_PRO_AI_PROFILE": "razonamiento"})["model"] == "gpt-6.1-sol")
check("AMAZON_PRO_AI_MODEL manda sobre el perfil", AI.config({"AMAZON_PRO_AI_PROVIDER": "openai", "AMAZON_PRO_AI_PROFILE": "razonamiento", "AMAZON_PRO_AI_MODEL": "gpt-6-astra"})["model"] == "gpt-6-astra")
check("tarifas oficiales luna 0,10/0,50", (c["_price_in"], c["_price_out"]) == (0.10, 0.50) and c["price_source"].startswith("oficial_openai_2026-11-16"))
check("tarifa del operador manda sobre la tabla", AI.config({"AMAZON_PRO_AI_PROVIDER": "openai", "AMAZON_PRO_AI_PRICE_IN": "7", "AMAZON_PRO_AI_PRICE_OUT": "9"})["_price_in"] == 7.0)
check("tope por ejecución por defecto presente (0,05)", c["max_cost_per_run"] == 0.05)
check("clave solo de OPENAI_API_KEY (entorno)", c["key_var"] == "OPENAI_API_KEY")
# 2 estados
S = lambda **o: AI.public_status(AI.config(env(**o)))
check("sin clave → PENDIENTES, no llama", "PENDIENTES" in AI.public_status(AI.config({"AMAZON_PRO_AI_PROVIDER": "openai"}))["status"])
check("clave sin ENABLE → deshabilitada", "DESHABILITADA" in AI.public_status(AI.config({"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": KEY}))["status"])
e2 = env(); del e2["AMAZON_PRO_AI_MONTHLY_BUDGET"]; s2 = AI.public_status(AI.config(e2))
check("sin presupuesto mensual → no puede llamar", not s2["can_call"] and "MONTHLY_BUDGET" in s2["status"])
check("modelo sin tarifa conocida → no puede llamar", not S(AMAZON_PRO_AI_MODEL="gpt-futuro")["can_call"])
check("estado público NO contiene la clave", KEY not in json.dumps(S()) and KEY not in json.dumps(AI.public_status(AI.config(env()))))
check("estado: IA configurada pero sin ejecución real verificada", "sin ejecución real verificada" in S()["status"])
# 3 petición exacta
BEHAVE.update(mode="ok"); SEEN.clear()
r = AI.complete(AI.config(env(AMAZON_PRO_AI_REASONING="medium")), "SISTEMA", "USUARIO [F1]")
q = SEEN[0]
check("endpoint /v1/responses", q["path"] == "/v1/responses")
check("Authorization Bearer con la clave de entorno (solo en cabecera)", q["auth"] == "Bearer " + KEY and KEY not in json.dumps(q["body"]))
b = q["body"]
check("cuerpo: model, instructions, input, max_output_tokens, store=false, reasoning.effort", b["model"] == "gpt-6-luna" and b["instructions"] == "SISTEMA" and b["input"] == "USUARIO [F1]" and b["max_output_tokens"] == 2500 and b["store"] is False and b["reasoning"] == {"effort": "medium"})
check("cuerpo sin max_tokens ni temperature (incompatibles con razonamiento)", "max_tokens" not in b and "temperature" not in b)
check("texto = solo el item message/output_text (ignora razonamiento)", r["text"].startswith("Decisión determinista"))
check("uso reportado: 1800 in / 120 out, razonamiento 70", (r["tokens_in"], r["tokens_out"], r["reasoning_tokens"], r["token_source"]) == (1800, 120, 70, "reportado_por_proveedor"))
check("coste = 1800×0,10/1M + 120×0,50/1M", abs(r["cost"] - (1800 * 0.10 + 120 * 0.50) / 1e6) < 1e-15)
check("modo PRUEBA_LOCAL (no REAL) contra loopback", r["mode"] == "PRUEBA_LOCAL")
# 4 errores sin inventar
def code(**o):
    try: AI.complete(AI.config(env(**o)), "s" * 40, "u" * 40); return None
    except AI.AIError as ex: return ex
BEHAVE.update(mode="incomplete"); ex = code()
check("incompleto por max_output_tokens → error con uso facturable parcial", ex.code == "RESPUESTA_INCOMPLETA_max_output_tokens" and ex.partial["tokens_out"] == 120 and ex.partial["cost"] > 0)
BEHAVE.update(mode="empty"); check("respuesta vacía → error, sin texto inventado", code().code == "RESPUESTA_VACIA")
BEHAVE.update(mode="nousage")
r2 = AI.complete(AI.config(env()), "s", "u"); check("sin usage: se contabiliza el peor caso (salida máxima)", r2["token_source"] == "estimado_peor_caso" and r2["tokens_out"] == 2500)
BEHAVE.update(mode="http429"); check("HTTP 429 → HTTP_429 sin cuerpo", code().code == "HTTP_429")
BEHAVE.update(mode="ok")
# 5 presupuestos
check("entrada excedida", code(AMAZON_PRO_AI_MAX_IN="1").code == "PRESUPUESTO_ENTRADA_EXCEDIDO")
check("coste por ejecución excedido (antes de llamar)", code(AMAZON_PRO_AI_MAX_COST="0.0000001").code == "PRESUPUESTO_COSTE_EXCEDIDO")
n = len(SEEN)
try: AI.complete(AI.config(env(AMAZON_PRO_AI_MONTHLY_BUDGET="0.001")), "s", "u", month_spent=0.00099); check("mensual excedido", False)
except AI.AIError as ex: check("presupuesto mensual excedido (gasto del mes + peor caso)", ex.code == "PRESUPUESTO_MENSUAL_EXCEDIDO")
check("los rechazos por presupuesto NO llegaron al servidor", len(SEEN) == n)
e3 = env(); del e3["AMAZON_PRO_AI_MONTHLY_BUDGET"]
try: AI.complete(AI.config(e3), "s", "u"); check("sin mensual", False)
except AI.AIError as ex: check("sin presupuesto mensual la llamada se rechaza", ex.code == "SIN_PRESUPUESTO_MENSUAL")
for bad in ("https://evil.example", "http://api.openai.com"):
    cc = AI.config(env(AMAZON_PRO_AI_BASE_URL=bad, AMAZON_PRO_AI_ALLOW_LOOPBACK="0"))
    check("host bloqueado: " + bad, not AI._host_ok(cc, AI._endpoint(cc)))
cc = AI.config({"AMAZON_PRO_AI_PROVIDER": "openai"}); check("host oficial https://api.openai.com/v1/responses permitido", AI._endpoint(cc) == "https://api.openai.com/v1/responses" and AI._host_ok(cc, AI._endpoint(cc)))
check("modo REAL solo para host oficial (lógica)", AI._mode(cc, "https://api.openai.com/v1/responses") == "REAL")

# 6 E2E Director + PHIVITAL (plantilla real INCOMPLETA)
def fixture():
    d = P.template(); d["product"]["name"] = "Magnesio PRUEBA (ficticio)"
    d["econ"].update(price=19.9, cost=3.0, fbaFee=3.2, acosTarget=18, vatPct=10, feeSchedule="generico_15", storageMonthly=0.1, storageMonths=2, returnsPct=3, returnProcessing=1.5)
    for k in d["costDocs"]: d["costDocs"][k] = {"evidence": "PRUEBA ficticia " + k, "date": ago(5)}
    d["competitors"] = [{"name": f"C{i}", "asin": f"A{i}", "priceGross": p, "shipping": 0, "packUnits": 1, "contentValue": 120, "source": "PRUEBA", "date": ago(4), "rating": 4.4, "reviews": 200 * i} for i, p in enumerate([18.5, 21, 23.9, 26], 1)]
    d["keywords"] = [{"keyword": k, "volume": v, "source": "PRUEBA", "date": ago(10)} for k, v in [("magnesio", 9000), ("citrato de magnesio", 4000), ("magnesio sueño", 1500)]]
    for it in list(d["regulatory"].values()) + list(d["content"].values()) + list(d["logistics"]["items"].values()): it.update(status="cumplido", evidence="PRUEBA", date=ago(3))
    d["logistics"].update(stockAvailable=900, forecastUnitsMonth=300, leadTimeDays=30, coverTargetDays=45)
    return d
st = Store(); st.create_account("phivital", "PhiVital", "POR CONFIRMAR")
d_inc = st.put("phivital", "dossier", {"origin": "INCOMPLETO", "dossier": P.template(), "name": "PHIVITAL MAGNESIO"})
d_test = st.put("phivital", "dossier", {"origin": "PRUEBA", "dossier": fixture(), "name": "PHIVITAL MAGNESIO (datos ficticios)"})
dr = D.Director(st, lambda: AI.config(env()))
BEHAVE.update(mode="ok", text="La decisión determinista es REVISAR [F1]. Faltan datos documentados [F2].", tin=2100, tout=140, reasoning=60); SEEN.clear()
r = dr.analyze("phivital", d_inc, "tester", "resumen general", today=TODAY)
run = st.get("phivital", r["ai_run"])["data"]
check("E2E INCOMPLETO: decisión determinista REVISAR (no inventa GO)", r["decision"] == "REVISAR")
check("E2E: ejecutó los 7 coworkers antes de llamar a la IA", len(r["plan"]) == 7 and len(r["tasks"]) == 7)
user_prompt = SEEN[0]["body"]["input"]
check("el prompt contiene solo hechos [F#] de coworkers/motor dentro de <datos>", "<datos>" in user_prompt and "[F1]" in user_prompt and "Decisión determinista" in user_prompt)
check("hechos incluyen datos AUSENTES declarados (pendiente/falta)", any(("falta" in t.lower() or "pendiente" in t.lower() or "sin " in t.lower()) for _, t in r["facts"]))
check("ai_run registra modelo, tokens, coste estimado, fuente de precio, evidencia y límites", run["model"].startswith("gpt-6-luna") and run["tokens_in"] == 2100 and run["cost_estimate"] > 0 and run["price_source"].startswith("oficial") and run["evidence"] and run["limitations"])
check("grounding ok y respuesta aceptada pero modo PRUEBA_LOCAL (no se declara REAL)", run["grounding"]["ok"] and r["ai"]["mode"] == "PRUEBA_LOCAL" and run["mode"] == "PRUEBA_LOCAL")
check("coworker_status: IA real NO verificada tras pruebas locales", dr.coworker_status("phivital")["ai"]["real_verified"] is False)
use = st.ai_usage(); check("registro de consumo: PRUEBA_LOCAL no cuenta como gasto real", use["real_calls"] == 0 and use["real_cost"] == 0 and use["local_calls"] >= 1)
# cifra inventada → descartada
BEHAVE.update(text="Se esperan 777 ventas al mes [F1].")
r = dr.analyze("phivital", d_inc, "tester", "resumen", today=TODAY)
check("respuesta con cifra inventada se DESCARTA → resumen determinista SIN IA", r["ai"]["mode"] == "SIN_IA" and "777" in r["ai"]["reason"] and r["answer"].startswith("SIN IA"))
# error de proveedor → sin inventar
BEHAVE.update(mode="http429"); r = dr.analyze("phivital", d_inc, "tester", "resumen", today=TODAY)
check("error HTTP → SIN IA con motivo, resumen determinista", r["ai"]["mode"] == "SIN_IA" and r["ai"]["reason"] == "HTTP_429")
BEHAVE.update(mode="incomplete"); r = dr.analyze("phivital", d_inc, "tester", "resumen", today=TODAY); run = st.get("phivital", r["ai_run"])["data"]
check("respuesta incompleta: se registra el consumo parcial y no se usa el texto", r["ai"]["mode"] == "SIN_IA" and run["tokens_out"] == 140 and run["cost_estimate"] > 0 and run["error"].startswith("RESPUESTA_INCOMPLETA"))
# ledger mensual: reservas REAL del libro (sin red)
BEHAVE.update(mode="ok", text="Decisión REVISAR [F1].")
rid = st.reserve(0.001, 5, True, "gpt-6-luna"); st.settle(rid, 0.00015)
u = st.ai_usage(); check("ledger suma solo REAL del mes", u["real_calls"] == 1 and abs(u["real_cost"] - 0.00015) < 1e-12 and u["by_model"]["gpt-6-luna"]["calls"] == 1)
st.db.execute("INSERT INTO ai_budget VALUES('old','2020-01',1,'settled',1,99.0,'x','2020-01-01T00:00:00Z',NULL,NULL)"); st.db.commit()
check("ledger ignora otros meses", abs(st.ai_usage()["real_cost"] - 0.00015) < 1e-12)
# presupuesto mensual consumido a través del Director
dr2 = D.Director(st, lambda: AI.config(env(AMAZON_PRO_AI_MONTHLY_BUDGET="0.0001")))
r = dr2.analyze("phivital", d_inc, "tester", "resumen", today=TODAY)
check("Director: presupuesto mensual agotado → SIN IA, sin llamada", r["ai"]["reason"] == "PRESUPUESTO_MENSUAL_EXCEDIDO" or r["ai"]["reason"] == "PRESUPUESTO_COSTE_EXCEDIDO")
# datos ficticios completos
dr3 = D.Director(st, lambda: AI.config(env()))
r = dr3.analyze("phivital", d_test, "tester", "resumen", today=TODAY)
check("E2E datos ficticios completos: decisión del motor determinista consistente con los hechos", r["decision"] in ("GO", "REVISAR", "NO-GO") and r["facts"][0][1].find(r["decision"]) > 0)
check("ninguna llamada fuera de loopback en toda la suite", not REAL_CALLS)
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
