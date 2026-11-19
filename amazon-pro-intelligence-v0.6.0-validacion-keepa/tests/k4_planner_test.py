"""K4 · planificador: ejecución única, persistencia, recuperación, reintentos, errores, tope de gasto, parada de emergencia."""
import os, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend.store import Store
from backend import k4_store as KS, k4_planner as P
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
class Clock:
    t = 1000.0
    def __call__(self): return self.t
clk = Clock(); calls = []
db = os.path.join(tempfile.mkdtemp(), "t.db"); st = Store(db); k = KS.K4Store(st)
flaky = {"n": 0}
def ok(prm, job): calls.append(job["id"]); return {"hecho": True}
def flak(prm, job):
    flaky["n"] += 1
    if flaky["n"] < 3: raise RuntimeError("fallo transitorio")
    return {"ok": 1}
def boom(prm, job): raise RuntimeError("siempre falla")
pl = P.Planner(k, {"ok": ok, "flaky": flak, "boom": boom}, None, clock=clk)
try: pl.encolar("x_ext"); r = False
except ValueError: r = True
check("solo tipos internos registrados", r)
a = pl.encolar("ok", "P", "ES"); b = pl.encolar("ok", "P", "ES")
check("dedupe: segundo encolado es duplicado", b["duplicado"] and a["id"] == b["id"])
# ejecución única con hilos concurrentes
ths = [threading.Thread(target=pl.tick) for _ in range(8)]; [t.start() for t in ths]; [t.join() for t in ths]
check("ejecución única bajo concurrencia", calls == [a["id"]])
check("estado OK persistido", k.q("SELECT estado FROM k4_job WHERE id=?", (a["id"],))[0]["estado"] == "OK")
# reintentos con espera
f = pl.encolar("flaky"); r1 = pl.tick()
check("fallo → REINTENTO con espera", r1["estado"] == "REINTENTO" and pl.tick()["ejecutado"] is False)
clk.t += 31; r2 = pl.tick(); clk.t += 121; r3 = pl.tick()
check("se reintenta y termina OK al tercer intento", r2["estado"] == "REINTENTO" and r3["estado"] == "OK")
e = pl.encolar("boom", max_intentos=2); pl.tick(); clk.t += 31; r = pl.tick()
check("agota intentos → ERROR y queda registrado", r["estado"] == "ERROR" and any("siempre falla" in x["mensaje"] for x in k.q("SELECT mensaje FROM k4_joblog WHERE job_id=?", (e["id"],))))
# persistencia + recuperación de huérfanos
c = pl.encolar("ok", "Q", "ES", dedupe="q1"); j = pl._tomar()
check("trabajo tomado queda EN_CURSO con lease", j["id"] == c["id"] and k.q("SELECT estado FROM k4_job WHERE id=?", (c["id"],))[0]["estado"] == "EN_CURSO")
clk.t += 400; st2 = Store(db); k2 = KS.K4Store(st2); pl2 = P.Planner(k2, {"ok": ok}, None, clock=clk, owner="w2")
check("tras reinicio recupera el huérfano y lo ejecuta una vez", pl2.recuperar() == 1 and pl2.tick()["estado"] == "OK" and calls.count(c["id"]) == 1)
# tope de gasto
g = pl2.encolar("ok", dedupe="gasto", coste_eur=1.0); res = pl2.tick()
check("coste > tope (0 €) → BLOQUEADO_GASTO sin ejecutar", res["motivo"] == "BLOQUEADO_GASTO" and g["id"] not in calls and pl2.tope()["gasto_eur"] == 0)
# parada de emergencia
h = pl2.encolar("ok", dedupe="par"); pl2.parada(True, "t", "prueba")
check("parada de emergencia impide ejecutar", pl2.tick()["motivo"] == "PARADA_DE_EMERGENCIA" and h["id"] not in calls)
pl2.parada(False, "t"); check("al levantar la parada se ejecuta", pl2.tick()["estado"] == "OK" and h["id"] in calls)
class OpsK:
    def kill_switch(self): return {"on": True}
pl3 = P.Planner(k2, {"ok": ok}, OpsK(), clock=clk); pl3.encolar("ok", dedupe="k3")
check("el kill switch general también detiene el planificador", pl3.tick()["motivo"] == "PARADA_DE_EMERGENCIA")
check("sin hilo propio por defecto", pl3.estado()["hilo_activo"] is False and "internos" in pl3.estado()["alcance"])
print("%d/%d" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
