"""Demostraciones V0.3 (reproducibles): (1) Director en sus 3 modos sin clave real; (2) coordinación de los 7 coworkers.
Datos: expediente FICTICIO «Magnesio PRUEBA». Ninguna ejecución de esta demo es IA real ni usa datos reales de PhiVital."""
import datetime, json, os, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, coworkers as C, director as D, pilot as P
from backend.store import Store
OUT = os.path.join(ROOT, "demos"); TODAY = datetime.date.today().isoformat()
ago = lambda n: (datetime.date.today() - datetime.timedelta(days=n)).isoformat()

def fixture():
    d = P.template(); d["product"]["name"] = "Magnesio PRUEBA (ficticio)"
    d["econ"].update(price=19.9, cost=3.0, fbaFee=3.2, acosTarget=18, vatPct=10, feeSchedule="generico_15", storageMonthly=0.1, storageMonths=2, returnsPct=3, returnProcessing=1.5)
    for k in d["costDocs"]: d["costDocs"][k] = {"evidence": "PRUEBA ficticia " + k, "date": ago(5)}
    d["competitors"] = [{"name": f"C{i}", "asin": f"A{i}", "priceGross": p, "shipping": 0, "packUnits": 1, "contentValue": 120, "source": "PRUEBA", "date": ago(4), "rating": 4.4, "reviews": 200 * i} for i, p in enumerate([18.5, 21, 23.9, 26], 1)]
    d["keywords"] = [{"keyword": k, "volume": v, "source": "PRUEBA", "date": ago(10)} for k, v in [("magnesio", 9000), ("magnesio 120 capsulas", 2000), ("citrato de magnesio", 4000), ("magnesio sueño", 1500), ("magnesio cansancio", 900)]]
    for it in list(d["regulatory"].values()) + list(d["content"].values()) + list(d["logistics"]["items"].values()): it.update(status="cumplido", evidence="PRUEBA", date=ago(3))
    d["content"]["video"].update(status="pendiente", evidence="")
    d["logistics"].update(stockAvailable=900, forecastUnitsMonth=300, leadTimeDays=30, coverTargetDays=45)
    d["listing"] = {"title": "Magnesio 120 capsulas citrato de magnesio", "bullets": ["magnesio sueño"], "backend": ""}; d["cvrPct"] = 10; d["adBudgetMonth"] = 300
    return d

class Fake(BaseHTTPRequestHandler):  # proveedor LOCAL de pruebas: ejercita el camino HTTP del adaptador; NO es un proveedor real
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); json.loads(self.rfile.read(n)); time.sleep(0.15)
        out = {"model": "proveedor-local-de-pruebas", "content": [{"type": "text", "text": "Síntesis de prueba: la decisión determinista es la indicada en [F1]; revisar los bloqueos listados."}], "usage": {"input_tokens": 1500, "output_tokens": 60}}
        b = json.dumps(out).encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
fs = HTTPServer(("127.0.0.1", 0), Fake); threading.Thread(target=fs.serve_forever, daemon=True).start()

st = Store(); st.create_account("demo", "Demo", "DEMO"); did = st.put("demo", "dossier", {"origin": "PRUEBA", "dossier": fixture()})
envs = {"1_sin_ia": {}, "2_proveedor_simulado_mock": {"AMAZON_PRO_AI_PROVIDER": "mock", "AMAZON_PRO_AI_PRICE_IN": "3", "AMAZON_PRO_AI_PRICE_OUT": "15"},
        "3_proveedor_local_de_pruebas_(camino_HTTP_real_del_adaptador)": {"AMAZON_PRO_AI_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "clave-FALSA-solo-pruebas", "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MODEL": "proveedor-local-de-pruebas", "AMAZON_PRO_AI_BASE_URL": f"http://127.0.0.1:{fs.server_address[1]}", "AMAZON_PRO_AI_ALLOW_LOOPBACK": "1", "AMAZON_PRO_AI_PRICE_IN": "3", "AMAZON_PRO_AI_PRICE_OUT": "15"},
        "4_anthropic_sin_clave_(estado_real_de_este_entorno)": {"AMAZON_PRO_AI_PROVIDER": "anthropic"}}
runs = {}
for name, env in envs.items():
    dr = D.Director(st, lambda e=env: AI.config(e)); t0 = time.time()
    r = dr.analyze("demo", did, "demo", "resumen general de precio, competencia y cumplimiento", today=TODAY)
    run = st.get("demo", r["ai_run"])["data"] if r["ai_run"] else None
    runs[name] = {"estado_proveedor": AI.public_status(AI.config(env))["status"], "modo_resultado": r["ai"]["mode"], "motivo": r["ai"]["reason"], "decision_determinista": r["decision"], "respuesta": r["answer"],
                  "ai_run_registrado": ({k: run[k] for k in ("model", "mode", "started_at", "finished_at", "duration_ms", "tokens_in", "tokens_out", "token_source", "cost_estimate", "currency", "prices_configured", "grounding", "error", "limitations", "datasets_consulted")} if run else None), "duracion_total_ms": int((time.time() - t0) * 1000)}
json.dump({"aviso": "NINGUNA de estas ejecuciones es IA real. Las ejecuciones reales con proveedor están PENDIENTES (falta clave).", "ejecuciones": runs}, open(os.path.join(OUT, "demo_director_ia.json"), "w"), ensure_ascii=False, indent=1)
md = ["# Demostración del Director IA (V0.3)", "", "> **Ninguna de estas ejecuciones es IA real.** Faltan clave y proveedor en este entorno: las ejecuciones reales están **pendientes**. Datos: expediente ficticio «Magnesio PRUEBA».", ""]
for k, v in runs.items():
    md += [f"## {k.replace('_', ' ')}", f"- Estado del proveedor: {v['estado_proveedor']}", f"- Modo del resultado: **{v['modo_resultado']}**" + (f" (motivo: {v['motivo']})" if v["motivo"] else ""), f"- Decisión determinista: {v['decision_determinista']}"]
    r = v["ai_run_registrado"]
    if r: md += [f"- Modelo: {r['model']} · modo registrado: {r['mode']} · duración {r['duration_ms']} ms", f"- Tokens: {r['tokens_in']} entrada / {r['tokens_out']} salida ({r['token_source']})", f"- Coste estimado: {r['cost_estimate']} {r['currency']} (precios de ejemplo 3/15 por millón de tokens, NO verificados)" if r["cost_estimate"] is not None else "- Coste estimado: no calculado", f"- Anclaje de cifras: {'OK' if r['grounding'] and r['grounding']['ok'] else r['grounding']}", f"- Limitaciones: {' | '.join(r['limitations'])}"]
    else: md.append("- No se registra ejecución de IA (no hubo llamada).")
    md += ["", "```", v["respuesta"][:700], "```", ""]
open(os.path.join(OUT, "demo_director_ia.md"), "w").write("\n".join(md))

# ---- coordinación de coworkers ----
st2 = Store(); st2.create_account("demo", "Demo", "DEMO"); did2 = st2.put("demo", "dossier", {"origin": "PRUEBA", "dossier": fixture()})
dr = D.Director(st2, lambda: AI.config({})); r = dr.analyze("demo", did2, "demo", "ejecuta la campaña de publicidad (ppc)", coworkers=["ppc", "cumplimiento"], today=TODAY)
tasks = [t for t in st2.list("demo", "task") if t["data"]["state"] == "done"][::-1]
coord = {"aviso": "Datos ficticios (origen PRUEBA). Los coworkers son deterministas: sin IA ni datos externos.", "peticion": "ppc + cumplimiento", "plan_con_dependencias": r["plan"], "flujo_pizarra": r["blackboard_flow"],
         "tareas": [{"coworker": t["data"]["coworker"], "depende_de": t["data"]["depends_on"], "estado": t["data"]["result"]["status"], "verificaciones_ok": t["data"]["result"]["checks_ok"], "duracion_ms": t["data"]["duration_ms"], "hallazgos": len(t["data"]["result"]["findings"]), "faltan": t["data"]["result"]["needs"]} for t in tasks],
         "estado_coworkers_tras_ejecutar": {k: v["label"] for k, v in dr.coworker_status("demo")["coworkers"].items()}}
json.dump(coord, open(os.path.join(OUT, "demo_coordinacion_coworkers.json"), "w"), ensure_ascii=False, indent=1)
lines = ["# Demostración de coordinación de coworkers (V0.3)", "", "Petición al Director: «ejecuta la campaña de publicidad (ppc)» + cumplimiento. El Director añade las dependencias, asigna las tareas y las ejecuta en orden compartiendo resultados (pizarra).", "", f"**Plan con dependencias:** {' → '.join(r['plan'])}", "", "**Flujo de resultados entre coworkers:** " + ", ".join(f"{x['from']}→{x['to']}" for x in r["blackboard_flow"]), "", "| Coworker | Depende de | Estado | Verificaciones | ms | Hallazgos |", "|---|---|---|---|---|---|"]
lines += [f"| {t['coworker']} | {', '.join(t['depende_de']) or '—'} | {t['estado']} | {t['verificaciones_ok']} | {t['duracion_ms']} | {t['hallazgos']} |" for t in coord["tareas"]]
lines += ["", "**Estado de coworkers tras la ejecución (deducido de ejecuciones registradas):**", ""] + [f"- {k}: {v}" for k, v in coord["estado_coworkers_tras_ejecutar"].items()]
lines += ["", "**Hallazgos del PPC que consumen resultados de Precios y SEO:**", ""] + [f"- {f['text']}" for f in next(t for t in tasks if t["data"]["coworker"] == "ppc")["data"]["result"]["findings"]]
open(os.path.join(OUT, "demo_coordinacion_coworkers.md"), "w").write("\n".join(lines))
print("demos generadas:", ", ".join(sorted(os.listdir(OUT))))
