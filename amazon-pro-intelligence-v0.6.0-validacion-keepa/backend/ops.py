"""V0.6 — Operación del Director: tareas persistentes (F8), autonomía N1–N4 y bandeja única de decisiones (F9),
puerta de modelos IA con política por tarea (F10) y libro de decisiones (F11).

Principios: determinista por defecto; nada se ejecuta fuera sin autorización; todo queda registrado en SQLite y en la auditoría encadenada.
Este módulo NO realiza llamadas externas por sí mismo: la IA solo se invoca vía ModelGate (con presupuesto, caché y aprobación N3 para gasto real)."""
import hashlib, json, re, time
from . import ai as AI

SCHEMA6 = """
CREATE TABLE IF NOT EXISTS tasks6(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, product TEXT, decision_label TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}',
  dedup_key TEXT, state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3, not_before REAL NOT NULL DEFAULT 0,
  urgency_days REAL, impact_lo REAL, impact_hi REAL, confidence REAL, cost_eur REAL NOT NULL DEFAULT 0, budget_eur REAL NOT NULL DEFAULT 0, spent_eur REAL NOT NULL DEFAULT 0,
  approved INTEGER NOT NULL DEFAULT 0, error TEXT, result TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, created_by TEXT NOT NULL DEFAULT 'sistema');
CREATE INDEX IF NOT EXISTS ix_t6 ON tasks6(state, dedup_key);
CREATE TABLE IF NOT EXISTS events6(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, task_id INTEGER, type TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS flags6(k TEXT PRIMARY KEY, v TEXT NOT NULL, by TEXT, at TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS policies6(action TEXT PRIMARY KEY, enabled INTEGER NOT NULL, max_per_day INTEGER NOT NULL, max_eur REAL NOT NULL, reversible INTEGER NOT NULL, by TEXT, at TEXT);
CREATE TABLE IF NOT EXISTS decisions6(id INTEGER PRIMARY KEY AUTOINCREMENT, group_key TEXT NOT NULL, product TEXT, kind TEXT NOT NULL, title TEXT NOT NULL, items TEXT NOT NULL,
  options TEXT NOT NULL, status TEXT NOT NULL, task_ids TEXT NOT NULL DEFAULT '[]', requested_at TEXT NOT NULL, decided_by TEXT, decided_at TEXT, note TEXT, level TEXT NOT NULL DEFAULT 'N3');
CREATE TABLE IF NOT EXISTS ledger6(id INTEGER PRIMARY KEY AUTOINCREMENT, product TEXT, decision_id INTEGER, objective TEXT NOT NULL, hypothesis TEXT, evidence TEXT NOT NULL DEFAULT '[]',
  recommendation TEXT, model_used TEXT, cost_eur REAL, approval TEXT, action TEXT, observed_result TEXT, expected TEXT, observed TEXT, difference TEXT, lessons TEXT, followup TEXT,
  attribution TEXT NOT NULL DEFAULT 'NO_ATRIBUIDO_AUTOMATICAMENTE', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS aicalls6(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, task_type TEXT, product TEXT, task_id INTEGER, tier TEXT, model TEXT, mode TEXT,
  tokens_in INTEGER, tokens_out INTEGER, cost REAL, latency_ms INTEGER, state TEXT NOT NULL, error_class TEXT, attempt INTEGER, cache_hit INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS aicache6(k TEXT PRIMARY KEY, model TEXT, text TEXT NOT NULL, created_at TEXT NOT NULL);
"""

TASK_STATES = ("PENDIENTE", "EN_CURSO", "ESPERA_APROBACION", "BLOQUEADA", "COMPLETADA", "FALLIDA", "CANCELADA")
TERMINAL = ("COMPLETADA", "FALLIDA", "CANCELADA")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ============================================================================================================
# F9 — Autonomía N1–N4
# ============================================================================================================
LEVELS = {
    "N1": "Automático: leer, clasificar, investigar con datos ya disponibles, calcular, preparar borradores, generar alertas.",
    "N2": "Automático SOLO bajo política expresa: acciones de bajo riesgo, con límites, registro y reversibilidad.",
    "N3": "Aprobación obligatoria de una persona: publicar, precios fuera de límites, gasto nuevo, campañas, claims, compromisos, cambios regulatorios.",
    "N4": "Bloqueo: datos críticos ausentes, riesgo legal, fallo de autenticación, presupuesto excedido o acción no autorizada.",
}
ACTION_LEVEL = {
    "leer_datos": "N1", "clasificar": "N1", "investigar_con_cache": "N1", "calcular": "N1", "preparar_borrador": "N1", "generar_alerta": "N1", "construir_expediente": "N1",
    "consulta_keepa_en_presupuesto": "N2", "ajuste_menor_reversible": "N2", "ia_dentro_de_presupuesto": "N2",
    "publicar_listing": "N3", "cambiar_precio": "N3", "gasto_nuevo": "N3", "llamada_keepa_nueva": "N3", "llamada_ia_real_nueva": "N3", "activar_campana": "N3",
    "cambio_mayor_campana": "N3", "publicar_claim": "N3", "compromiso_comercial": "N3", "cambio_regulatorio": "N3",
}
EXTERNAL = {"publicar_listing", "cambiar_precio", "activar_campana", "cambio_mayor_campana", "publicar_claim", "compromiso_comercial", "consulta_keepa_en_presupuesto", "llamada_keepa_nueva", "llamada_ia_real_nueva", "ajuste_menor_reversible"}


class Ops:
    def __init__(self, store):
        self.store = store; self.db = store.db; self.lock = store.lock
        with self.lock:
            self.db.executescript(SCHEMA6)
            self.handlers = {}
            self.recover()

    # ------------------------------------------------------------------ utilidades --------------------------------------------------------------
    def _ev(self, tid, typ, detail):
        with self.lock:
            self.db.execute("INSERT INTO events6(ts,task_id,type,detail) VALUES(?,?,?,?)", (_now(), tid, typ, json.dumps(detail, ensure_ascii=False, default=str)[:600])); self.db.commit()
        self.store.audit("catalogo-aht", "director", "ops." + typ, {"task": tid, **(detail if isinstance(detail, dict) else {"d": str(detail)[:200]})})

    def _row(self, r):
        if r is None:
            return None
        d = dict(r)
        for k in ("payload", "result"):
            try:
                d[k] = json.loads(d[k]) if d.get(k) else None
            except ValueError:
                pass
        return d

    # ------------------------------------------------------------------ kill switch -------------------------------------------------------------
    def kill_switch(self, on=None, by="sistema", reason=""):
        with self.lock:
            if on is not None:
                self.db.execute("INSERT INTO flags6(k,v,by,at,reason) VALUES('kill',?,?,?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v, by=excluded.by, at=excluded.at, reason=excluded.reason", ("1" if on else "0", by, _now(), reason[:200]))
                self.db.commit()
                self._ev(None, "kill_switch", {"on": bool(on), "by": by, "reason": reason[:120]})
            r = self.db.execute("SELECT * FROM flags6 WHERE k='kill'").fetchone()
        return {"on": bool(r and r["v"] == "1"), "by": r["by"] if r else None, "at": r["at"] if r else None, "reason": r["reason"] if r else None}

    # ------------------------------------------------------------------ políticas N2 ------------------------------------------------------------
    def set_policy(self, action, enabled, max_per_day, max_eur, reversible, by):
        if ACTION_LEVEL.get(action) != "N2":
            raise ValueError("solo las acciones de nivel N2 admiten política: " + ", ".join(a for a, l in ACTION_LEVEL.items() if l == "N2"))
        if not isinstance(max_per_day, int) or not 0 <= max_per_day <= 1000 or not isinstance(max_eur, (int, float)) or not 0 <= max_eur <= 10000:
            raise ValueError("límites inválidos")
        if enabled and not reversible and action != "consulta_keepa_en_presupuesto":
            raise ValueError("una política N2 de acción no reversible no está permitida: pasa a N3")
        with self.lock:
            self.db.execute("INSERT INTO policies6 VALUES(?,?,?,?,?,?,?) ON CONFLICT(action) DO UPDATE SET enabled=excluded.enabled,max_per_day=excluded.max_per_day,max_eur=excluded.max_eur,reversible=excluded.reversible,by=excluded.by,at=excluded.at",
                            (action, 1 if enabled else 0, max_per_day, float(max_eur), 1 if reversible else 0, by, _now())); self.db.commit()
        self._ev(None, "policy", {"action": action, "enabled": bool(enabled), "max_per_day": max_per_day, "max_eur": max_eur, "by": by})
        return self.policies()

    def policies(self):
        with self.lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM policies6 ORDER BY action").fetchall()]

    def authorize(self, action, ctx=None):
        """Decide qué hacer con una acción. Devuelve {level, decision: EJECUTAR|PEDIR_APROBACION|BLOQUEAR, reason}. Nunca ejecuta nada."""
        ctx = ctx or {}
        lvl = ACTION_LEVEL.get(action)
        if lvl is None:
            return {"level": "N4", "decision": "BLOQUEAR", "reason": "acción no reconocida/no autorizada: %s" % action}
        # N4: condiciones de bloqueo (se evalúan antes que nada)
        if self.kill_switch()["on"] and action in EXTERNAL:
            return {"level": "N4", "decision": "BLOQUEAR", "reason": "interruptor de emergencia ACTIVO: automatizaciones externas detenidas"}
        for flag, why in (("missing_critical_data", "faltan datos críticos"), ("legal_risk", "riesgo legal/regulatorio detectado"), ("auth_failure", "fallo de autenticación del conector"), ("budget_exceeded", "presupuesto excedido")):
            if ctx.get(flag):
                return {"level": "N4", "decision": "BLOQUEAR", "reason": "%s: %s" % (why, ctx[flag] if isinstance(ctx[flag], str) else "se bloquea hasta resolverlo")}
        if lvl == "N1":
            return {"level": "N1", "decision": "EJECUTAR", "reason": "acción interna sin efectos externos"}
        if lvl == "N2":
            with self.lock:
                p = self.db.execute("SELECT * FROM policies6 WHERE action=? AND enabled=1", (action,)).fetchone()
                if not p:
                    return {"level": "N3", "decision": "PEDIR_APROBACION", "reason": "sin política N2 expresa para esta acción: se trata como N3"}
                today = time.strftime("%Y-%m-%d", time.gmtime())
                n = self.db.execute("SELECT COUNT(*) c FROM events6 WHERE type='n2_exec' AND substr(ts,1,10)=? AND detail LIKE ?", (today, '%"action": "' + action + '"%')).fetchone()["c"]
            if n >= p["max_per_day"]:
                return {"level": "N3", "decision": "PEDIR_APROBACION", "reason": "límite diario de la política N2 alcanzado (%d)" % p["max_per_day"]}
            if (ctx.get("eur") or 0) > p["max_eur"]:
                return {"level": "N3", "decision": "PEDIR_APROBACION", "reason": "importe %.2f € > límite de la política (%.2f €)" % (ctx.get("eur") or 0, p["max_eur"])}
            if not p["reversible"] and action != "consulta_keepa_en_presupuesto":
                return {"level": "N3", "decision": "PEDIR_APROBACION", "reason": "acción no reversible"}
            return {"level": "N2", "decision": "EJECUTAR", "reason": "dentro de la política N2 vigente (límites, registro)", "policy": dict(p)}
        if ctx.get("approved"):
            return {"level": "N3", "decision": "EJECUTAR", "reason": "aprobada por una persona"}
        return {"level": "N3", "decision": "PEDIR_APROBACION", "reason": "acción de nivel N3: requiere aprobación expresa"}

    def log_n2(self, action, detail=None):
        self._ev(None, "n2_exec", {"action": action, **(detail or {})})

    # ------------------------------------------------------------------ bandeja única de decisiones ---------------------------------------------
    def request_decision(self, product, kind, title, item, options=None, task_id=None, level="N3"):
        """Crea o AGRUPA una petición: misma (producto, tipo) pendiente → se añade como ítem (sin notificación repetida)."""
        gk = "%s|%s" % (product or "-", kind)
        with self.lock:
            r = self.db.execute("SELECT * FROM decisions6 WHERE group_key=? AND status='PENDIENTE'", (gk,)).fetchone()
            if r:
                items = json.loads(r["items"]); tids = json.loads(r["task_ids"])
                if item not in items:
                    items.append(item)
                if task_id and task_id not in tids:
                    tids.append(task_id)
                self.db.execute("UPDATE decisions6 SET items=?, task_ids=? WHERE id=?", (json.dumps(items, ensure_ascii=False), json.dumps(tids), r["id"])); self.db.commit()
                return r["id"]
            cur = self.db.execute("INSERT INTO decisions6(group_key,product,kind,title,items,options,status,task_ids,requested_at,level) VALUES(?,?,?,?,?,?,'PENDIENTE',?,?,?)",
                                  (gk, product, kind, title[:160], json.dumps([item], ensure_ascii=False), json.dumps(options or ["APROBAR", "RECHAZAR"], ensure_ascii=False), json.dumps([task_id] if task_id else []), _now(), level))
            self.db.commit(); did = cur.lastrowid
        self._ev(task_id, "decision_requested", {"id": did, "kind": kind, "product": product})
        return did

    def decisions(self, status="PENDIENTE", product=None):
        q = "SELECT * FROM decisions6 WHERE 1=1"; a = []
        if status:
            q += " AND status=?"; a.append(status)
        if product:
            q += " AND product=?"; a.append(product)
        with self.lock:
            rows = self.db.execute(q + " ORDER BY id DESC LIMIT 200", a).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            for k in ("items", "options", "task_ids"):
                d[k] = json.loads(d[k])
            out.append(d)
        return out

    def decide(self, did, approve, by, note=""):
        with self.lock:
            r = self.db.execute("SELECT * FROM decisions6 WHERE id=?", (did,)).fetchone()
            if not r:
                raise ValueError("decisión inexistente")
            if r["status"] != "PENDIENTE":
                raise ValueError("la decisión ya está resuelta")
            self.db.execute("UPDATE decisions6 SET status=?, decided_by=?, decided_at=?, note=? WHERE id=?", ("APROBADA" if approve else "RECHAZADA", by, _now(), note[:300], did))
            for tid in json.loads(r["task_ids"]):
                if approve:
                    self.db.execute("UPDATE tasks6 SET approved=1, state='PENDIENTE', updated_at=? WHERE id=? AND state IN ('ESPERA_APROBACION','BLOQUEADA')", (_now(), tid))
                else:
                    self.db.execute("UPDATE tasks6 SET state='CANCELADA', error='rechazada por una persona', updated_at=? WHERE id=? AND state='ESPERA_APROBACION'", (_now(), tid))
            self.db.commit()
        self._ev(None, "decision_resolved", {"id": did, "approved": bool(approve), "by": by})
        lid = self.ledger_add(r["product"], did, "Decisión «%s»" % r["title"], approval="%s por %s" % ("APROBADA" if approve else "RECHAZADA", by), action="REGISTRADA (sin ejecución externa: no hay conectores operativos)", evidence=json.loads(r["items"]))
        return {"ok": True, "status": "APROBADA" if approve else "RECHAZADA", "ledger_id": lid, "nota": "La aprobación queda registrada; esta versión no ejecuta acciones comerciales externas."}

    # ------------------------------------------------------------------ F8 — tareas persistentes -----------------------------------------------
    def register(self, kind, fn, action="calcular", external=False):
        self.handlers[kind] = {"fn": fn, "action": action}

    def add_task(self, kind, product, decision_label, payload=None, dedup=None, urgency_days=None, impact_eur=None, confidence=None, cost_eur=0.0, budget_eur=0.0, max_attempts=3, by="sistema"):
        """Toda tarea debe colgar de una decisión de negocio (decision_label). Deduplica por dedup_key mientras haya una activa."""
        if not str(decision_label or "").strip():
            raise ValueError("toda investigación/tarea debe estar ligada a una decisión de negocio")
        if kind not in self.handlers:
            raise ValueError("tipo de tarea desconocido: " + kind)
        dk = dedup or "%s|%s|%s" % (kind, product, hashlib.sha1(json.dumps(payload or {}, sort_keys=True).encode()).hexdigest()[:10])
        with self.lock:
            ex = self.db.execute("SELECT id FROM tasks6 WHERE dedup_key=? AND state NOT IN ('COMPLETADA','FALLIDA','CANCELADA')", (dk,)).fetchone()
            if ex:
                return {"id": ex["id"], "duplicate": True}
            lo, hi = (impact_eur or (None, None))
            cur = self.db.execute("INSERT INTO tasks6(kind,product,decision_label,payload,dedup_key,state,max_attempts,urgency_days,impact_lo,impact_hi,confidence,cost_eur,budget_eur,created_at,updated_at,created_by) VALUES(?,?,?,?,?,'PENDIENTE',?,?,?,?,?,?,?,?,?,?)",
                                  (kind, product, decision_label[:200], json.dumps(payload or {}, ensure_ascii=False), dk, max_attempts, urgency_days, lo, hi, confidence, cost_eur, budget_eur, _now(), _now(), by))
            self.db.commit(); tid = cur.lastrowid
        self._ev(tid, "task_created", {"kind": kind, "product": product, "decision": decision_label[:80]})
        return {"id": tid, "duplicate": False}

    @staticmethod
    def priority(t):
        """Prioridad EXPLICABLE (sin puntuaciones arbitrarias): 1) urgencia por fecha límite, 2) valor esperado por € (rango × confianza ÷ coste) si está dimensionado, 3) antigüedad.
        Devuelve (clave_orden, explicación). Si no hay impacto en € → «NO DIMENSIONADO» (se ordena tras los dimensionados del mismo tramo de urgencia)."""
        u = t.get("urgency_days")
        bucket = 0 if u is not None and u <= 3 else (1 if u is not None and u <= 14 else 2)
        lo, hi, conf = t.get("impact_lo"), t.get("impact_hi"), t.get("confidence")
        if lo is not None and hi is not None and conf is not None:
            ev = (lo + hi) / 2 * conf; ratio = ev / max(t.get("cost_eur") or 0.0, 0.01)
            why = "valor esperado %.0f € (impacto %.0f–%.0f € × confianza %.0f %%) ÷ coste %.2f €" % (ev, lo, hi, conf * 100, t.get("cost_eur") or 0)
            return (bucket, 0, -ratio, t["id"]), "urgencia %s · %s" % (("≤3 días" if bucket == 0 else "≤14 días" if bucket == 1 else "sin fecha próxima"), why)
        return (bucket, 1, 0, t["id"]), "urgencia %s · impacto NO DIMENSIONADO (no se inventa un valor)" % ("≤3 días" if bucket == 0 else "≤14 días" if bucket == 1 else "sin fecha próxima")

    def tasks(self, states=None, product=None, limit=200):
        q = "SELECT * FROM tasks6 WHERE 1=1"; a = []
        if states:
            q += " AND state IN (%s)" % ",".join("?" * len(states)); a += list(states)
        if product:
            q += " AND product=?"; a.append(product)
        with self.lock:
            rows = [self._row(r) for r in self.db.execute(q + " ORDER BY id DESC LIMIT ?", a + [limit]).fetchall()]
        for t in rows:
            t["priority_why"] = self.priority(t)[1]
        return rows

    def queue(self):
        """Cola ordenada por prioridad explicable (solo tareas ejecutables ahora)."""
        now = time.time()
        with self.lock:
            rows = [self._row(r) for r in self.db.execute("SELECT * FROM tasks6 WHERE state='PENDIENTE' AND not_before<=?", (now,)).fetchall()]
        rows.sort(key=lambda t: self.priority(t)[0])
        for t in rows:
            t["priority_why"] = self.priority(t)[1]
        return rows

    def cancel(self, tid, by="sistema"):
        with self.lock:
            self.db.execute("UPDATE tasks6 SET state='CANCELADA', updated_at=? WHERE id=? AND state NOT IN ('COMPLETADA','FALLIDA','CANCELADA')", (_now(), tid)); self.db.commit()
        self._ev(tid, "task_cancelled", {"by": by})

    def recover(self):
        """Recuperación tras reinicio: lo que quedó EN_CURSO vuelve a PENDIENTE (cuenta el intento) o falla si agotó reintentos."""
        with self.lock:
            rows = self.db.execute("SELECT id, attempts, max_attempts FROM tasks6 WHERE state='EN_CURSO'").fetchall()
            for r in rows:
                if r["attempts"] >= r["max_attempts"]:
                    self.db.execute("UPDATE tasks6 SET state='FALLIDA', error='INTERRUMPIDA_POR_REINICIO (sin reintentos)', updated_at=? WHERE id=?", (_now(), r["id"]))
                else:
                    self.db.execute("UPDATE tasks6 SET state='PENDIENTE', error='INTERRUMPIDA_POR_REINICIO: se reintenta', updated_at=? WHERE id=?", (_now(), r["id"]))
            self.db.commit()
        return len(rows)

    def run_next(self, backoff_s=30):
        """Ejecuta UNA tarea (la de mayor prioridad). Comprueba autorización, presupuesto y parada antes de ejecutar."""
        q = self.queue()
        if not q:
            return None
        t = q[0]; tid = t["id"]; h = self.handlers[t["kind"]]
        auth = self.authorize(h["action"], {"approved": bool(t["approved"]), "eur": t["cost_eur"], "budget_exceeded": t["budget_eur"] and t["spent_eur"] > t["budget_eur"] and "gasto %.2f € > presupuesto %.2f €" % (t["spent_eur"], t["budget_eur"])})
        with self.lock:
            if auth["decision"] == "BLOQUEAR":
                self.db.execute("UPDATE tasks6 SET state='BLOQUEADA', error=?, updated_at=? WHERE id=?", ("N4: " + auth["reason"], _now(), tid)); self.db.commit(); st = "BLOQUEADA"
            elif auth["decision"] == "PEDIR_APROBACION":
                self.db.execute("UPDATE tasks6 SET state='ESPERA_APROBACION', error=?, updated_at=? WHERE id=?", (auth["reason"], _now(), tid)); self.db.commit(); st = "ESPERA_APROBACION"
            else:
                st = None
        if st == "ESPERA_APROBACION":
            self.request_decision(t["product"], h["action"], "Aprobar: %s" % t["decision_label"], {"tarea": tid, "tipo": t["kind"], "motivo": auth["reason"], "decision_de_negocio": t["decision_label"]}, task_id=tid)
            self._ev(tid, "task_waiting_approval", {"reason": auth["reason"]}); return {"id": tid, "state": st}
        if st == "BLOQUEADA":
            self._ev(tid, "task_blocked", {"reason": auth["reason"]}); return {"id": tid, "state": st}
        with self.lock:
            self.db.execute("UPDATE tasks6 SET state='EN_CURSO', attempts=attempts+1, updated_at=? WHERE id=?", (_now(), tid)); self.db.commit()
        try:
            res = h["fn"](t) or {}
            if auth["level"] == "N2":
                self.log_n2(h["action"], {"task": tid})
            with self.lock:
                self.db.execute("UPDATE tasks6 SET state='COMPLETADA', result=?, error=NULL, spent_eur=spent_eur+?, updated_at=? WHERE id=?", (json.dumps(res, ensure_ascii=False, default=str)[:4000], float(res.get("cost_eur") or 0) if isinstance(res, dict) else 0, _now(), tid)); self.db.commit()
            self._ev(tid, "task_done", {"kind": t["kind"]}); return {"id": tid, "state": "COMPLETADA", "result": res}
        except Exception as e:  # noqa: BLE001 — se registra y se reintenta de forma limitada
            msg = ("%s: %s" % (type(e).__name__, e))[:300]
            with self.lock:
                a = self.db.execute("SELECT attempts, max_attempts FROM tasks6 WHERE id=?", (tid,)).fetchone()
                if a["attempts"] >= a["max_attempts"]:
                    self.db.execute("UPDATE tasks6 SET state='FALLIDA', error=?, updated_at=? WHERE id=?", (msg, _now(), tid)); fin = "FALLIDA"
                else:
                    self.db.execute("UPDATE tasks6 SET state='PENDIENTE', error=?, not_before=?, updated_at=? WHERE id=?", (msg, time.time() + backoff_s * a["attempts"], _now(), tid)); fin = "PENDIENTE"
                self.db.commit()
            self._ev(tid, "task_error", {"error": msg, "next": fin}); return {"id": tid, "state": fin, "error": msg}

    def run_all(self, limit=50, backoff_s=30):
        out = []
        for _ in range(limit):
            r = self.run_next(backoff_s)
            if r is None:
                break
            out.append(r)
        return out

    def events(self, limit=100):
        with self.lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM events6 ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    # ------------------------------------------------------------------ F11 — libro de decisiones ------------------------------------------------
    def ledger_add(self, product, decision_id, objective, hypothesis="", evidence=None, recommendation="", model_used=None, cost_eur=None, approval="", action=""):
        with self.lock:
            cur = self.db.execute("INSERT INTO ledger6(product,decision_id,objective,hypothesis,evidence,recommendation,model_used,cost_eur,approval,action,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                                  (product, decision_id, objective[:300], hypothesis[:400], json.dumps(evidence or [], ensure_ascii=False, default=str)[:3000], recommendation[:600], model_used, cost_eur, approval[:200], action[:300], _now(), _now()))
            self.db.commit()
        return cur.lastrowid

    def ledger_observe(self, lid, observed_result, expected=None, observed=None, lessons="", followup=""):
        """Registra el resultado observado. NO atribuye automáticamente un cambio de ventas a una acción de la IA y NO modifica políticas comerciales."""
        diff = None
        if isinstance(expected, (int, float)) and isinstance(observed, (int, float)) and not isinstance(expected, bool) and not isinstance(observed, bool):
            diff = "%+.2f (observado − esperado)" % (observed - expected)
        elif expected is not None or observed is not None:
            diff = "NO CUANTIFICABLE (valores no numéricos)"
        with self.lock:
            self.db.execute("UPDATE ledger6 SET observed_result=?, expected=?, observed=?, difference=?, lessons=?, followup=?, updated_at=? WHERE id=?",
                            (observed_result[:400], None if expected is None else str(expected), None if observed is None else str(observed), diff, lessons[:400], followup[:300], _now(), lid)); self.db.commit()
        return self.ledger(lid)

    def ledger(self, lid=None, product=None, limit=100):
        with self.lock:
            if lid is not None:
                r = self.db.execute("SELECT * FROM ledger6 WHERE id=?", (lid,)).fetchone()
                rows = [r] if r else []
            elif product:
                rows = self.db.execute("SELECT * FROM ledger6 WHERE product=? ORDER BY id DESC LIMIT ?", (product, limit)).fetchall()
            else:
                rows = self.db.execute("SELECT * FROM ledger6 ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r); d["evidence"] = json.loads(d["evidence"] or "[]"); d["policy_note"] = "Un resultado aislado NO modifica políticas comerciales; los cambios de política los decide una persona."; out.append(d)
        return out[0] if lid is not None and out else (None if lid is not None else out)

    # ------------------------------------------------------------------ resumen para la interfaz -----------------------------------------------
    def summary(self):
        with self.lock:
            c = {r["state"]: r["n"] for r in self.db.execute("SELECT state, COUNT(*) n FROM tasks6 GROUP BY state").fetchall()}
            pend = self.db.execute("SELECT COUNT(*) n FROM decisions6 WHERE status='PENDIENTE'").fetchone()["n"]
        return {"tasks": c, "decisions_pending": pend, "kill_switch": self.kill_switch(), "levels": LEVELS}


# ============================================================================================================
# F10 — Puerta de modelos IA (política por tarea, sin router complejo)
# ============================================================================================================
TASK_POLICY = {
    # tier: none = SOLO código determinista (la IA nunca calcula) · cheap = modelo económico · strong = modelo potente (solo si se justifica)
    "calculo_economico": {"tier": "none", "why": "los cálculos los hace el motor determinista"},
    "validacion_reglas": {"tier": "none", "why": "reglas/validaciones en código"},
    "clasificar_competidor": {"tier": "cheap", "validator": "json", "max_retries": 1, "escalate": False, "budget_eur": 0.02},
    "borrador_listing": {"tier": "cheap", "validator": "claims_lint", "max_retries": 1, "escalate": True, "budget_eur": 0.05},
    "guion_video": {"tier": "cheap", "validator": "claims_lint", "max_retries": 1, "escalate": False, "budget_eur": 0.05},
    "informe_director": {"tier": "strong", "validator": "grounding", "max_retries": 1, "escalate": False, "budget_eur": 0.10},
}
ERROR_CLASSES = ("ERROR_DE_MODELO", "ERROR_DE_PROMPT", "FALTAN_DATOS", "ERROR_DE_HERRAMIENTA", "ERROR_DE_CALCULO", "INCERTIDUMBRE_LEGITIMA")
MAX_ESCALATIONS = 1
_PROMPT_ERR = {"PRESUPUESTO_ENTRADA_EXCEDIDO", "REASONING_NO_SOPORTADO"}
_TOOL_ERR = {"SIN_PROVEEDOR", "SIN_CLAVE", "IA_DESHABILITADA", "SIN_MODELO", "HOST_NO_PERMITIDO", "PRECIO_DESCONOCIDO"}


def classify_error(code=None, validation=None, missing=None):
    """Distingue la causa: error de modelo / de prompt / faltan datos / herramienta / cálculo / incertidumbre legítima."""
    if missing:
        return "FALTAN_DATOS"
    if code in _PROMPT_ERR:
        return "ERROR_DE_PROMPT"
    if code in _TOOL_ERR or (code and code.startswith(("HTTP", "RED", "TIMEOUT"))):
        return "ERROR_DE_HERRAMIENTA"
    if validation and validation.get("kind") == "calc":
        return "ERROR_DE_CALCULO"
    if validation and validation.get("kind") == "uncertain":
        return "INCERTIDUMBRE_LEGITIMA"
    return "ERROR_DE_MODELO"


def _v_json(text, facts=""):
    try:
        json.loads(text); return {"ok": True}
    except ValueError:
        return {"ok": False, "why": "la respuesta no es JSON válido", "kind": "model"}


def _v_grounding(text, facts=""):
    g = AI.grounding(text, facts)
    return {"ok": bool(g.get("ok", g.get("grounded", True))), "why": "cifras no ancladas a los hechos: %s" % (g.get("ungrounded") or g.get("missing") or ""), "kind": "model", "raw": g}


class ModelGate:
    """Una única puerta para toda llamada a IA: política por tarea, caché, presupuestos (tarea/expediente/mes), reintentos y escalado limitados,
    validación independiente y registro de tokens/coste/latencia/errores. El gasto REAL nuevo exige aprobación (N3)."""
    def __init__(self, store, ops, cfg_fn=AI.config, lint=None):
        self.store, self.ops, self.cfg_fn = store, ops, cfg_fn
        self.validators = {"json": _v_json, "grounding": _v_grounding}
        if lint:
            self.validators["claims_lint"] = lint

    def _log(self, **k):
        with self.store.lock:
            self.store.db.execute("INSERT INTO aicalls6(ts,task_type,product,task_id,tier,model,mode,tokens_in,tokens_out,cost,latency_ms,state,error_class,attempt,cache_hit) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                  (_now(), k.get("task_type"), k.get("product"), k.get("task_id"), k.get("tier"), k.get("model"), k.get("mode"), k.get("tin"), k.get("tout"), k.get("cost"), k.get("ms"), k["state"], k.get("err"), k.get("attempt"), 1 if k.get("cache") else 0))
            self.store.db.commit()

    def spent(self, product=None, task_id=None, month=None):
        q, a = "SELECT COALESCE(SUM(cost),0) s FROM aicalls6 WHERE cache_hit=0 AND state='OK'", []
        if product:
            q += " AND product=?"; a.append(product)
        if task_id:
            q += " AND task_id=?"; a.append(task_id)
        if month:
            q += " AND substr(ts,1,7)=?"; a.append(month)
        with self.store.lock:
            return self.store.db.execute(q, a).fetchone()["s"]

    def _model_for(self, cfg, tier):
        import os
        env = {"cheap": "AMAZON_PRO_AI_MODEL_CHEAP", "strong": "AMAZON_PRO_AI_MODEL_STRONG"}[tier]
        with self.store.lock:
            pin = self.store.db.execute("SELECT v FROM flags6 WHERE k=?", ("model_" + tier,)).fetchone()
        return (pin["v"] if pin else None) or os.environ.get(env) or cfg.get("model")  # modelo fijado; nunca «latest» implícito

    def run(self, task_type, system, user, product=None, task_id=None, facts="", allow_real=False, missing=None):
        pol = TASK_POLICY.get(task_type)
        if pol is None:
            return {"state": "RECHAZADA", "error_class": "ERROR_DE_PROMPT", "detail": "tipo de tarea sin política: " + task_type}
        if pol["tier"] == "none":
            self._log(task_type=task_type, product=product, task_id=task_id, tier="none", state="NO_USA_IA")
            return {"state": "NO_USA_IA", "detail": pol["why"]}
        if missing:  # falta información: cambiar de modelo NO la crea
            self._log(task_type=task_type, product=product, task_id=task_id, tier=pol["tier"], state="SIN_LLAMADA", err="FALTAN_DATOS")
            return {"state": "FALTAN_DATOS", "error_class": "FALTAN_DATOS", "missing": missing, "detail": "No se llama a ningún modelo: faltan datos (%s)." % ", ".join(missing)}
        cfg = self.cfg_fn()
        key = hashlib.sha256(json.dumps([task_type, system, user, cfg.get("provider"), cfg.get("model")], ensure_ascii=False).encode()).hexdigest()
        with self.store.lock:
            hit = self.store.db.execute("SELECT * FROM aicache6 WHERE k=?", (key,)).fetchone()
        if hit:
            self._log(task_type=task_type, product=product, task_id=task_id, tier=pol["tier"], model=hit["model"], state="OK", cache=True, cost=0)
            return {"state": "OK", "text": hit["text"], "model": hit["model"], "cache": True, "cost": 0.0}
        if cfg["provider"] == "none":
            self._log(task_type=task_type, product=product, task_id=task_id, tier=pol["tier"], state="SIN_PROVEEDOR", err="ERROR_DE_HERRAMIENTA")
            return {"state": "SIN_PROVEEDOR", "error_class": "ERROR_DE_HERRAMIENTA", "detail": "No hay proveedor de IA configurado."}
        real = cfg["provider"] != "mock"
        if real and not allow_real:
            did = self.ops.request_decision(product, "llamada_ia_real_nueva", "Autorizar llamada de IA de pago (%s)" % task_type, {"tarea": task_type, "tope_eur": pol["budget_eur"], "proveedor": cfg["provider"]}, task_id=task_id)
            return {"state": "REQUIERE_APROBACION", "decision_id": did, "detail": "Gasto de IA real = nivel N3: aprobación pendiente en la bandeja."}
        month = time.strftime("%Y-%m")
        if cfg.get("monthly_budget") is not None and self.spent(month=month) >= cfg["monthly_budget"]:
            self._log(task_type=task_type, product=product, task_id=task_id, tier=pol["tier"], state="PRESUPUESTO_MENSUAL", err="ERROR_DE_HERRAMIENTA")
            return {"state": "BLOQUEADA_POR_PRESUPUESTO", "detail": "Presupuesto mensual agotado (N4)."}
        tier, attempt, escal, last = pol["tier"], 0, 0, None
        while True:
            attempt += 1
            if task_id and self.spent(task_id=task_id) >= pol["budget_eur"] or (product and self.spent(product=product, month=month) >= pol["budget_eur"] * 20):
                return {"state": "BLOQUEADA_POR_PRESUPUESTO", "detail": "Presupuesto de tarea/expediente agotado (N4)."}
            c2 = dict(cfg); c2["model"] = self._model_for(cfg, tier)
            try:
                r = AI.complete(c2, system, user, month_spent=self.spent(month=month))
            except AI.AIError as e:
                ec = classify_error(code=e.args[0] if e.args else None)
                self._log(task_type=task_type, product=product, task_id=task_id, tier=tier, model=c2["model"], state="ERROR", err=ec, attempt=attempt)
                return {"state": "ERROR", "error_class": ec, "code": e.args[0] if e.args else None}
            v = self.validators.get(pol["validator"], lambda t, f="": {"ok": True})(r["text"], facts)
            self._log(task_type=task_type, product=product, task_id=task_id, tier=tier, model=r["model"], mode=r["mode"], tin=r["tokens_in"], tout=r["tokens_out"], cost=r["cost"], ms=r["duration_ms"], state="OK" if v["ok"] else "VALIDACION_FALLIDA", err=None if v["ok"] else classify_error(validation=v), attempt=attempt)
            if v["ok"]:
                with self.store.lock:
                    self.store.db.execute("INSERT OR REPLACE INTO aicache6 VALUES(?,?,?,?)", (key, r["model"], r["text"], _now())); self.store.db.commit()
                return {"state": "OK", "text": r["text"], "model": r["model"], "tier": tier, "attempts": attempt, "escalations": escal, "cost": r["cost"], "mode": r["mode"], "validated": pol["validator"]}
            last = v
            if attempt <= pol["max_retries"]:
                continue
            if pol["escalate"] and tier == "cheap" and escal < MAX_ESCALATIONS:
                tier, escal = "strong", escal + 1; continue
            return {"state": "RECHAZADA_POR_VALIDACION", "error_class": classify_error(validation=last), "detail": last.get("why"), "attempts": attempt, "escalations": escal}

    def calls(self, limit=100):
        with self.store.lock:
            return [dict(r) for r in self.store.db.execute("SELECT * FROM aicalls6 ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def pin_model(self, tier, model, evidence, by):
        """El modelo de producción NO cambia solo: exige evidencia de pruebas suficiente y una persona administradora."""
        if tier not in ("cheap", "strong") or not re.match(r"^[A-Za-z0-9._\-]{3,60}$", model or "") or model.lower().endswith("latest"):
            raise ValueError("modelo inválido (se exige un identificador fijado, nunca «latest»)")
        if len(str(evidence or "").strip()) < 30:
            raise ValueError("cambio de modelo rechazado: falta evidencia de pruebas suficiente (≥30 caracteres que citen resultados)")
        with self.store.lock:
            self.store.db.execute("INSERT INTO flags6(k,v,by,at,reason) VALUES(?,?,?,?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v,by=excluded.by,at=excluded.at,reason=excluded.reason", ("model_" + tier, model, by, _now(), evidence[:300])); self.store.db.commit()
        return {"tier": tier, "model": model, "by": by}
