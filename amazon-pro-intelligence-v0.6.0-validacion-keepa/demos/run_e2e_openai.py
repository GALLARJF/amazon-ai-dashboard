"""Prueba E2E V0.3.1 SIN consumo real: PHIVITAL MAGNESIO → 7 coworkers → motor → Director → adaptador OpenAI (Responses) contra servidor LOCAL que imita la API.
Genera demos/e2e_phivital_openai.{json,md} y el presupuesto estimado de pruebas. Ninguna ejecución es IA real."""
import json, os, sys, threading, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, director as D, pilot as P
from backend.store import Store
TODAY = datetime.date.today().isoformat()
SEEN = []
class Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); b = json.loads(self.rfile.read(n)); SEEN.append(b)
        out = {"status": "completed", "model": b["model"], "output": [{"type": "message", "content": [{"type": "output_text", "text": "Decisión determinista: REVISAR [F1]. El expediente tiene datos pendientes de documentar [F2]; no se puede declarar GO."}]}],
               "usage": {"input_tokens": 2100, "output_tokens": 140, "output_tokens_details": {"reasoning_tokens": 60}}}
        r = json.dumps(out).encode(); self.send_response(200); self.send_header("Content-Length", str(len(r))); self.end_headers(); self.wfile.write(r)
    def log_message(self, *a): pass
fs = HTTPServer(("127.0.0.1", 0), Fake); threading.Thread(target=fs.serve_forever, daemon=True).start()
env = {"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": "sk-FALSA-SOLO-PRUEBAS", "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "5",
       "AMAZON_PRO_AI_BASE_URL": f"http://127.0.0.1:{fs.server_address[1]}", "AMAZON_PRO_AI_ALLOW_LOOPBACK": "1"}
st = Store(); st.create_account("phivital", "PhiVital", "POR CONFIRMAR")
did = st.put("phivital", "dossier", {"origin": "INCOMPLETO", "dossier": P.template(), "name": "PHIVITAL MAGNESIO"})
dr = D.Director(st, lambda: AI.config(env)); r = dr.analyze("phivital", did, "e2e", "resumen general", today=TODAY)
run = st.get("phivital", r["ai_run"])["data"]; prompt_tokens = AI.est_tokens(D.SYSTEM + SEEN[0]["input"] + SEEN[0]["instructions"] if False else SEEN[0]["instructions"] + SEEN[0]["input"])
tasks = [{"coworker": c, "estado": v["status"], "verificaciones_ok": v["checks_ok"], "faltan": v["needs"][:2]} for c, v in r["coworkers"].items()]
# presupuesto estimado: entrada medida (chars/4 del prompt real) y salida máxima configurada (incluye razonamiento)
rows = []
for prof, m in AI.PROFILES.items():
    pi, _, po = AI.PRICES[m]; cap = 2500
    rows.append({"perfil": prof, "modelo": m, "usd_por_ejecucion_tipica": round((prompt_tokens * pi + 600 * po) / 1e6, 6), "usd_por_ejecucion_peor_caso": round((prompt_tokens * pi + cap * po) / 1e6, 6),
                 "permitido_por_tope_por_ejecucion_0.05": (prompt_tokens * pi + cap * po) / 1e6 <= 0.05})
plan = {"luna": 10, "sol": 5}; tl = next(x for x in rows if x["modelo"] == "gpt-6-luna"); ts = next(x for x in rows if x["modelo"] == "gpt-6.1-sol")
presupuesto = {"supuesto": "10 ejecuciones con gpt-6-luna + 5 con gpt-6.1-sol", "tipico_usd": round(10 * tl["usd_por_ejecucion_tipica"] + 5 * ts["usd_por_ejecucion_tipica"], 4), "peor_caso_usd": round(10 * tl["usd_por_ejecucion_peor_caso"] + 5 * ts["usd_por_ejecucion_peor_caso"], 4)}
out = {"aviso": "SIN CONSUMO REAL: servidor local que imita la Responses API. No es IA real.", "tokens_entrada_prompt_estimados": prompt_tokens, "decision_motor": r["decision"], "coworkers": tasks, "peticion_enviada": {k: (v if k != "input" and k != "instructions" else f"<{len(v)} caracteres>") for k, v in SEEN[0].items()},
       "modo": r["ai"]["mode"], "ai_run": {k: run[k] for k in ("model", "mode", "tokens_in", "tokens_out", "reasoning_tokens", "token_source", "cost_estimate", "price_source", "grounding", "evidence", "limitations", "datasets_consulted")},
       "tabla_coste": rows, "presupuesto_pruebas": presupuesto}
json.dump(out, open(os.path.join(ROOT, "demos", "e2e_phivital_openai.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({"prompt_tokens": prompt_tokens, "mode": r["ai"]["mode"], "decision": r["decision"], "tabla": rows, "presupuesto": presupuesto}, ensure_ascii=False, indent=1))
