"""K4 · planificador robusto (opción A de la comparativa: proceso + arrendamiento en BD). SOLO trabajos INTERNOS (leer, calcular, generar dossiers, medir): ninguna acción externa, ningún gasto.
Garantías (verificadas en tests/k4_planner_test.py): ejecución única (dedupe + lease atómico), persistencia (SQLite), recuperación de trabajos huérfanos, reintentos con espera, registro de errores,
tope de gasto (0 €), parada de emergencia, medición posterior. No arranca hilos por sí solo: `tick()` lo invoca un hilo opcional o el vigilante externo."""
import json, threading, time, uuid
from .k4_store import now

BACKOFF = (30, 120, 600)
LEASE_S = 300


class Planner:
    def __init__(self, k4, handlers=None, ops=None, clock=time.time, owner=None):
        self.k = k4; self.h = dict(handlers or {}); self.ops = ops; self.clock = clock; self.owner = owner or ("w-" + uuid.uuid4().hex[:6]); self.thread = None; self.stop = threading.Event()
        if not self._get("tope_eur"): self._set("tope_eur", "0"); self._set("gasto_eur", "0")

    # ---- estado
    def _get(self, k, d=None):
        r = self.k.q("SELECT v FROM k4_planner WHERE k=?", (k,)); return r[0]["v"] if r else d
    def _set(self, k, v): self.k.x("INSERT INTO k4_planner(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, str(v)))
    def _log(self, jid, nivel, msg): self.k.x("INSERT INTO k4_joblog(job_id,ts,nivel,mensaje) VALUES(?,?,?,?)", (jid, now(), nivel, str(msg)[:500]))

    def parada(self, on=None, actor="sistema", motivo=""):
        if on is not None:
            self._set("parada", "1" if on else "0"); self._set("parada_por", actor); self._set("parada_motivo", motivo[:200]); self.k.audit(actor, "k4.planner.parada", {"on": bool(on), "motivo": motivo[:120]})
        return {"activa": self._get("parada") == "1" or self._ops_kill(), "por": self._get("parada_por"), "motivo": self._get("parada_motivo")}

    def _ops_kill(self):
        try: return bool(self.ops and self.ops.kill_switch()["on"])
        except Exception: return False

    def tope(self, eur=None, actor="sistema"):
        if eur is not None:
            if eur < 0: raise ValueError("tope inválido")
            self._set("tope_eur", eur); self.k.audit(actor, "k4.planner.tope", {"eur": eur})
        return {"tope_eur": float(self._get("tope_eur", "0")), "gasto_eur": float(self._get("gasto_eur", "0"))}

    # ---- cola
    def encolar(self, kind, producto=None, pais=None, params=None, dedupe=None, delay=0, max_intentos=3, coste_eur=0.0, actor="sistema"):
        if kind not in self.h: raise ValueError("tipo de trabajo desconocido")
        dedupe = dedupe or "%s|%s|%s" % (kind, producto, pais)
        with self.k.s.lock:
            ex = self.k.s.db.execute("SELECT id FROM k4_job WHERE dedupe=? AND estado IN ('PENDIENTE','EN_CURSO')", (dedupe,)).fetchone()
            if ex: return {"id": ex["id"], "duplicado": True}
            c = self.k.s.db.execute("INSERT INTO k4_job(kind,producto,pais,params,estado,max_intentos,next_at,dedupe,coste_eur,creado) VALUES(?,?,?,?,'PENDIENTE',?,?,?,?,?)", (kind, producto, pais, json.dumps(params or {}), max_intentos, self.clock() + delay, dedupe, coste_eur, now()))
            self.k.s.db.commit(); jid = c.lastrowid
        self.k.audit(actor, "k4.job.encolado", {"id": jid, "kind": kind}); return {"id": jid, "duplicado": False}

    def recuperar(self):
        """Trabajos EN_CURSO con lease vencido (proceso caído/reiniciado) → PENDIENTE (o ERROR si agotaron intentos). Devuelve cuántos."""
        t = self.clock(); n = 0
        for r in self.k.q("SELECT * FROM k4_job WHERE estado='EN_CURSO' AND lease_until<?", (t,)):
            if r["intentos"] >= r["max_intentos"]: self.k.x("UPDATE k4_job SET estado='ERROR', error='lease vencido y sin intentos', terminado=? WHERE id=?", (now(), r["id"])); self._log(r["id"], "ERROR", "huérfano sin intentos")
            else: self.k.x("UPDATE k4_job SET estado='PENDIENTE', lease_owner=NULL, lease_until=NULL, next_at=? WHERE id=?", (t, r["id"])); self._log(r["id"], "AVISO", "recuperado tras lease vencido")
            n += 1
        return n

    def _tomar(self):
        t = self.clock()
        with self.k.s.lock:
            r = self.k.s.db.execute("SELECT * FROM k4_job WHERE estado='PENDIENTE' AND next_at<=? ORDER BY next_at,id LIMIT 1", (t,)).fetchone()
            if not r: return None
            u = self.k.s.db.execute("UPDATE k4_job SET estado='EN_CURSO', lease_owner=?, lease_until=?, intentos=intentos+1, empezado=? WHERE id=? AND estado='PENDIENTE'", (self.owner, t + LEASE_S, now(), r["id"]))
            self.k.s.db.commit()
            if u.rowcount != 1: return None
        return dict(r, intentos=r["intentos"] + 1)

    def tick(self):
        """Ejecuta como máximo UN trabajo. Devuelve dict con lo ocurrido."""
        if self.parada()["activa"]: return {"ejecutado": False, "motivo": "PARADA_DE_EMERGENCIA"}
        rec = self.recuperar(); j = self._tomar()
        if not j: return {"ejecutado": False, "recuperados": rec, "motivo": "sin trabajos"}
        tope = float(self._get("tope_eur", "0")); gasto = float(self._get("gasto_eur", "0"))
        if j["coste_eur"] > 0 and gasto + j["coste_eur"] > tope + 1e-9:
            self.k.x("UPDATE k4_job SET estado='BLOQUEADO_GASTO', error=?, terminado=?, lease_owner=NULL WHERE id=?", ("coste %.2f € supera el tope %.2f €" % (j["coste_eur"], tope), now(), j["id"])); self._log(j["id"], "BLOQUEO", "límite de gasto"); return {"ejecutado": False, "id": j["id"], "motivo": "BLOQUEADO_GASTO"}
        try:
            res = self.h[j["kind"]](json.loads(j["params"]), j)
            self.k.x("UPDATE k4_job SET estado='OK', resultado=?, terminado=?, lease_owner=NULL, lease_until=NULL, error=NULL WHERE id=?", (json.dumps(res, ensure_ascii=False, default=str)[:2000], now(), j["id"]))
            if j["coste_eur"] > 0: self._set("gasto_eur", gasto + j["coste_eur"])
            self._log(j["id"], "OK", j["kind"]); return {"ejecutado": True, "id": j["id"], "estado": "OK", "resultado": res}
        except Exception as e:
            msg = "%s: %s" % (type(e).__name__, str(e)[:200]); self._log(j["id"], "ERROR", msg)
            if j["intentos"] >= j["max_intentos"]: self.k.x("UPDATE k4_job SET estado='ERROR', error=?, terminado=?, lease_owner=NULL, lease_until=NULL WHERE id=?", (msg, now(), j["id"])); return {"ejecutado": True, "id": j["id"], "estado": "ERROR", "error": msg}
            self.k.x("UPDATE k4_job SET estado='PENDIENTE', error=?, next_at=?, lease_owner=NULL, lease_until=NULL WHERE id=?", (msg, self.clock() + BACKOFF[min(j["intentos"] - 1, len(BACKOFF) - 1)], j["id"])); return {"ejecutado": True, "id": j["id"], "estado": "REINTENTO", "error": msg}

    def cancelar(self, jid, actor="sistema"):
        self.k.x("UPDATE k4_job SET estado='CANCELADA', terminado=? WHERE id=? AND estado IN ('PENDIENTE','BLOQUEADO_GASTO')", (now(), jid)); self.k.audit(actor, "k4.job.cancelado", {"id": jid})

    def estado(self):
        c = {r["estado"]: r["n"] for r in self.k.q("SELECT estado, COUNT(*) n FROM k4_job GROUP BY estado")}
        return {"trabajos": c, "parada": self.parada(), "gasto": self.tope(), "propietario": self.owner, "hilo_activo": bool(self.thread and self.thread.is_alive()), "ultimos": self.k.q("SELECT id,kind,producto,pais,estado,intentos,error,terminado FROM k4_job ORDER BY id DESC LIMIT 20"),
                "registro": self.k.q("SELECT job_id,ts,nivel,mensaje FROM k4_joblog ORDER BY id DESC LIMIT 20"), "alcance": "Solo trabajos internos (generar dossiers, medir seguimientos, conciliar datos). Sin acciones externas ni gasto."}

    # ---- hilo opcional (desactivado por defecto)
    def iniciar(self, cada=60):
        if self.thread and self.thread.is_alive(): return False
        self.stop.clear()
        def loop():
            while not self.stop.wait(cada):
                try: self.tick()
                except Exception: pass
        self.thread = threading.Thread(target=loop, daemon=True); self.thread.start(); return True

    def detener(self): self.stop.set()
