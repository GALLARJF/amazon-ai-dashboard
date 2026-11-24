"""V0.3.2 — Presupuesto ante concurrencia, reintentos, timeouts y consumo incierto. SIN red real (servidor local + _post parcheado para el host oficial)."""
import datetime, json, os, sys, tempfile, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, director as D, pilot as P
from backend.store import Store
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
TODAY = datetime.date.today().isoformat()
HITS = []; B = {"mode": "ok", "delay": 0.0, "tin": 1300, "tout": 100}
class F(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n); HITS.append(time.time()); time.sleep(B["delay"])
        m = B["mode"]
        if m.startswith("http"):
            code = int(m[4:]); self.send_response(code); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"{}"); return
        if m == "notjson": body = b"<html>gateway</html>"
        else:
            out = {"status": "completed", "model": "gpt-6-luna", "output": [{"type": "message", "content": [{"type": "output_text", "text": "Decisión REVISAR [F1]."}]}], "usage": {"input_tokens": B["tin"], "output_tokens": B["tout"]}}
            if m == "nousage": del out["usage"]
            if m == "incomplete": out["status"] = "incomplete"; out["incomplete_details"] = {"reason": "max_output_tokens"}; out["output"] = []
            body = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
fs = ThreadingHTTPServer(("127.0.0.1", 0), F); threading.Thread(target=fs.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{fs.server_address[1]}"
def env(**o):
    e = {"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": "sk-FALSA", "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "5", "AMAZON_PRO_AI_BASE_URL": URL, "AMAZON_PRO_AI_ALLOW_LOOPBACK": "1", "AMAZON_PRO_AI_TIMEOUT": "1"}
    e.update(o); return e
def reset(**k): HITS.clear(); B.update(mode="ok", delay=0.0, tin=1300, tout=100); B.update(k)
def call(st, e, **kw):
    try: return AI.complete(AI.config(e), "s" * 40, "u" * 4000, ledger=st)
    except AI.AIError as ex: return ex
def committed(st, real=False):
    r = st.db.execute("SELECT COALESCE(SUM(CASE WHEN state='settled' THEN actual ELSE worst END),0) c FROM ai_budget WHERE real=? AND state IN ('reserved','uncertain','settled')", (int(real),)).fetchone(); return r["c"]
WORST = AI.cost(AI.config(env()), AI.est_tokens("s" * 40 + "u" * 4000), 2500)

# 1 reserva atómica en el store (carrera pura, 60 hilos)
st = Store(); ok = []
def worker(): ok.append(st.reserve(0.01, 0.2, True, "m"))
ts = [threading.Thread(target=worker) for _ in range(60)]; [t.start() for t in ts]; [t.join() for t in ts]
check("60 hilos reservando 0,01 con presupuesto 0,2 → exactamente 20 reservas", sum(1 for x in ok if x) == 20)
check("lo comprometido nunca supera el presupuesto", committed(st, True) <= 0.2 + 1e-9)
check("reservas REAL y LOCAL se contabilizan por separado", st.reserve(0.15, 0.2, False, "m") is not None)
# 2 Director con hilos y servidor lento: el caso que fallaba en V0.3.1 (5 peticiones con presupuesto para 1)
def director_race(n, **e):
    reset(delay=0.5); s = Store(); s.create_account("a", "a", "x"); did = s.put("a", "dossier", {"origin": "INCOMPLETO", "dossier": P.template()})
    dr = D.Director(s, lambda: AI.config(env(**e))); res = []
    ts = [threading.Thread(target=lambda: res.append(dr.analyze("a", did, "u", "resumen", today=TODAY))) for _ in range(n)]; [t.start() for t in ts]; [t.join() for t in ts]
    return res, s
# (a) 4 hilos con tope de concurrencia 4 (el máximo permitido por ai.config): la puerta de concurrencia no interviene y el motivo del rechazo es DETERMINISTA (solo presupuesto)
res, s = director_race(4, AMAZON_PRO_AI_MONTHLY_BUDGET="0.0035", AMAZON_PRO_AI_MAX_CONCURRENT="4")
check("4 análisis simultáneos, presupuesto para 2 peores casos → solo 2 llegan al proveedor", len(HITS) == 2)
check("el resto queda SIN IA con motivo PRESUPUESTO_MENSUAL_EXCEDIDO", sum(1 for r in res if r["ai"]["reason"] == "PRESUPUESTO_MENSUAL_EXCEDIDO") == 2)
# (b) con 6 hilos y tope 4 el reparto del motivo entre las dos puertas (concurrencia/presupuesto) depende del orden de los hilos; lo que NO puede variar es el gasto
res, s = director_race(6, AMAZON_PRO_AI_MONTHLY_BUDGET="0.0035", AMAZON_PRO_AI_MAX_CONCURRENT="4")
check("6 hilos / tope 4: nunca más de 2 llamadas al proveedor (el gasto no depende del orden de los hilos)", len(HITS) <= 2 and len(HITS) >= 1)
check("6 hilos / tope 4: todo rechazo es SIN IA con motivo PRESUPUESTO_MENSUAL_EXCEDIDO o IA_OCUPADA, y no hay otros", all(r["ai"]["reason"] in ("PRESUPUESTO_MENSUAL_EXCEDIDO", "IA_OCUPADA") for r in res if r["ai"]["mode"] == "SIN_IA") and sum(1 for r in res if r["ai"]["mode"] != "SIN_IA") == len(HITS))
check("todas las respuestas incluyen el resumen determinista (la app no se bloquea)", all(r["answer"] for r in res))
res, s = director_race(6, AMAZON_PRO_AI_MONTHLY_BUDGET="5")
check("concurrencia por defecto = 1: 6 simultáneos → 1 llamada, resto IA_OCUPADA", len(HITS) == 1 and sum(1 for r in res if r["ai"]["reason"] == "IA_OCUPADA") == 5)
check("el hueco se libera: una llamada posterior sí pasa", (reset() or True) and not isinstance(call(s, env()), AI.AIError))
# 3 ciclo de vida de la reserva según el resultado
def life(mode, **k):
    reset(mode=mode, **k); s = Store(); r = call(s, env()); return r, s
r, s = life("ok"); check("OK: se liquida con el coste real reportado", not isinstance(r, AI.AIError) and abs(committed(s) - (1300 * 0.10 + 100 * 0.50) / 1e6) < 1e-12)
for code in (400, 401, 403, 404, 429):
    r, s = life("http%d" % code); check("HTTP %d: rechazado → reserva LIBERADA (0 comprometido), 1 sola petición, sin reintento" % code, r.code == "HTTP_%d" % code and committed(s) == 0 and len(HITS) == 1)
for code in (500, 502, 503, 408):
    r, s = life("http%d" % code); check("HTTP %d: consumo INCIERTO → se retiene el peor caso, 1 sola petición" % code, r.code == "HTTP_%d" % code and abs(committed(s) - WORST) < 1e-12 and s.ai_usage()["uncertain_calls"] == 0 and len(HITS) == 1)
r, s = life("ok", delay=2.0); check("timeout → TIMEOUT, retenido peor caso (incierto), sin reintento", r.code == "TIMEOUT" and abs(committed(s) - WORST) < 1e-12 and len(HITS) == 1)
r, s = life("notjson"); check("200 no-JSON → incierto (peor caso)", r.code == "RESPUESTA_NO_JSON" and abs(committed(s) - WORST) < 1e-12)
r, s = life("nousage"); check("200 sin usage → se acepta pero se retiene el peor caso como incierto", not isinstance(r, AI.AIError) and r["token_source"] == "estimado_peor_caso" and abs(committed(s) - WORST) < 1e-12)
r, s = life("incomplete"); check("incompleto: se liquida el consumo parcial reportado", r.code.startswith("RESPUESTA_INCOMPLETA") and abs(committed(s) - (1300 * 0.10 + 100 * 0.50) / 1e6) < 1e-12)
s = Store(); dead = ThreadingHTTPServer(("127.0.0.1", 0), F); port = dead.server_address[1]; dead.server_close()
r = call(s, env(AMAZON_PRO_AI_BASE_URL=f"http://127.0.0.1:{port}")); check("conexión rechazada (nunca llegó) → ERROR_DE_RED con reserva LIBERADA", r.code == "ERROR_DE_RED" and committed(s) == 0)
# 4 incierto bloquea presupuesto hasta conciliar
reset(mode="http500"); s = Store(); b = str(WORST * 1.5)
call(s, env(AMAZON_PRO_AI_MONTHLY_BUDGET=b), ); reset(); 
# el incierto debe ser REAL para contar contra el presupuesto real: se verifica con scope local equivalente
r2 = call(s, env(AMAZON_PRO_AI_MONTHLY_BUDGET=b)); check("tras un incierto, el siguiente que no cabe se rechaza SIN llamar", isinstance(r2, AI.AIError) and r2.code == "PRESUPUESTO_MENSUAL_EXCEDIDO" and len(HITS) == 0)
rid = s.db.execute("SELECT id FROM ai_budget WHERE state='uncertain'").fetchone()["id"]
s.reconcile(rid, 0.0); r3 = call(s, env(AMAZON_PRO_AI_MONTHLY_BUDGET=b)); check("conciliar el incierto (coste real 0) libera presupuesto y vuelve a permitir llamar", not isinstance(r3, AI.AIError))
try: s.reconcile(rid, 0.0); check("solo se concilian inciertos", False)
except ValueError: check("solo se concilian inciertos (no dos veces)", True)
try: s.reconcile("x", -1); check("coste negativo", False)
except ValueError: check("conciliación valida el coste", True)
# 5 recuperación tras caída
path = os.path.join(tempfile.mkdtemp(), "b.db"); s = Store(path); rid = s.reserve(0.01, 1, True, "m"); s.db.close()
s2 = Store(path); row = s2.db.execute("SELECT state, note FROM ai_budget WHERE id=?", (rid,)).fetchone()
check("reserva en vuelo + reinicio → INCIERTA (se sigue cobrando el peor caso)", row["state"] == "uncertain" and "REINICIO" in row["note"] and abs(committed(s2, True) - 0.01) < 1e-12)
# 6 camino REAL sin red: _post parcheado SOLO para el host oficial
OFF = []
def fake_post(url, headers, body, timeout):
    h = urllib.parse.urlparse(url).hostname
    if h == "api.openai.com":
        OFF.append(url); return 200, json.dumps({"status": "completed", "model": "gpt-6-luna", "output": [{"type": "message", "content": [{"type": "output_text", "text": "Decisión REVISAR [F1]."}]}], "usage": {"input_tokens": 1000, "output_tokens": 50}})
    raise AssertionError("host no previsto " + h)
AI._post = fake_post
s = Store(); r = AI.complete(AI.config({"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": "sk-FALSA", "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "1"}), "s", "u", ledger=s)
u = s.ai_usage()
check("host oficial (parcheado, sin red): modo REAL y cuenta como gasto real en el libro", r["mode"] == "REAL" and u["real_calls"] == 1 and abs(u["real_cost"] - (1000 * 0.1 + 50 * 0.5) / 1e6) < 1e-12 and OFF == ["https://api.openai.com/v1/responses"])
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
