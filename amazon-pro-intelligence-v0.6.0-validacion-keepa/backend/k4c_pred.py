"""K4 · Consejero F2.1 — PREDICCIONES evaluables. Una predicción solo se puntúa con evidencia de resultado (valor observado + fuente + método + incertidumbre) y, cuando procede, revisión humana.
La calibración comercial REAL nunca incluye predicciones SINTÉTICAS."""
import json
from .k4_store import now

SCHEMA = """CREATE TABLE IF NOT EXISTS k4c_pred(id INTEGER PRIMARY KEY AUTOINCREMENT, inv_id TEXT, hipotesis TEXT, prediccion TEXT, metrica TEXT, direccion TEXT, umbral_rel REAL, inicio TEXT, fin TEXT, valor_inicial REAL, entorno TEXT,
 estado TEXT, valor_observado REAL, fecha_observacion TEXT, fuente_resultado TEXT, metodo_evaluacion TEXT, incertidumbre REAL, evaluacion TEXT, revision TEXT, creado TEXT);"""
DIRECCIONES = ("NO_CAE_MAS_DE", "SUBE_AL_MENOS", "BAJA_AL_MENOS", "DISPONIBLE")
def _f(x): return float(x)


class Predicciones:
    def __init__(self, k4): self.k = k4; k4.s.db.executescript(SCHEMA); k4.s.db.commit()

    def registrar(self, inv_id, hipotesis, prediccion, metrica, direccion, umbral_rel, inicio, fin, valor_inicial, entorno):
        if direccion not in DIRECCIONES: raise ValueError("dirección inválida")
        if entorno not in ("SINTETICO", "REAL"): raise ValueError("entorno inválido")
        if not (hipotesis and prediccion and metrica and inicio and fin) or fin <= inicio: raise ValueError("faltan hipótesis, predicción, métrica o periodo válido")
        if direccion != "DISPONIBLE" and valor_inicial is None: raise ValueError("sin valor inicial no hay predicción evaluable")
        c = self.k.x("INSERT INTO k4c_pred(inv_id,hipotesis,prediccion,metrica,direccion,umbral_rel,inicio,fin,valor_inicial,entorno,estado,creado) VALUES(?,?,?,?,?,?,?,?,?,?,'REGISTRADA',?)", (inv_id, hipotesis, prediccion, metrica, direccion, umbral_rel, inicio, fin, valor_inicial, entorno, now()))
        return c.lastrowid

    def get(self, pid):
        r = self.k.q("SELECT * FROM k4c_pred WHERE id=?", (pid,))
        if not r: raise LookupError("predicción inexistente")
        return r[0]

    def resultado(self, pid, valor, fuente, metodo, incertidumbre, fecha, actor):
        """Registra la evidencia del resultado y propone una evaluación; NUNCA acepta un booleano de acierto."""
        p = self.get(pid)
        if p["estado"] not in ("REGISTRADA", "PENDIENTE_REVISION"): raise ValueError("la predicción ya está cerrada")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)): raise ValueError("el valor observado debe ser numérico (no un booleano de acierto)")
        if valor is None or not str(fuente or "").strip() or not str(metodo or "").strip() or incertidumbre is None: raise ValueError("el resultado exige valor observado, fuente, método de evaluación e incertidumbre")
        if fecha < p["fin"]: raise ValueError("la observación es anterior al fin de la ventana (%s): no evaluable aún" % p["fin"])
        v0, vo, inc = p["valor_inicial"], _f(valor), abs(_f(incertidumbre)); ev = {"veredicto": None}
        if p["direccion"] == "DISPONIBLE": ev["veredicto"] = "CUMPLIDA" if vo >= 1 else "NO_CUMPLIDA"
        else:
            if not v0: raise ValueError("valor inicial nulo: cambio relativo no calculable")
            cambio = (vo - v0) / abs(v0); lo, hi = cambio - inc / abs(v0), cambio + inc / abs(v0); u = p["umbral_rel"]
            ok = {"NO_CAE_MAS_DE": lambda x: x >= -abs(u), "SUBE_AL_MENOS": lambda x: x >= u, "BAJA_AL_MENOS": lambda x: x <= -abs(u)}[p["direccion"]]
            ev = {"cambio_relativo": round(cambio, 4), "intervalo": [round(lo, 4), round(hi, 4)], "veredicto": "CUMPLIDA" if ok(lo) and ok(hi) else ("NO_CUMPLIDA" if not ok(lo) and not ok(hi) else "INCONCLUSA")}
        est = "PENDIENTE_REVISION" if (ev["veredicto"] == "INCONCLUSA" or p["entorno"] == "REAL") else ("EVALUADA_ACERTADA" if ev["veredicto"] == "CUMPLIDA" else "EVALUADA_FALLIDA")
        self.k.x("UPDATE k4c_pred SET estado=?, valor_observado=?, fecha_observacion=?, fuente_resultado=?, metodo_evaluacion=?, incertidumbre=?, evaluacion=? WHERE id=?", (est, vo, fecha, fuente, metodo, inc, json.dumps(ev), pid))
        self.k.audit(actor, "k4c.pred_resultado", {"id": pid, "estado": est}); return self.get(pid)

    def revisar(self, pid, actor, decision, nota):
        p = self.get(pid)
        if p["estado"] != "PENDIENTE_REVISION": raise ValueError("la predicción no está pendiente de revisión")
        if decision not in ("ACERTADA", "FALLIDA", "NO_EVALUABLE") or len(str(nota or "")) < 10: raise ValueError("decisión y nota (≥10 caracteres) obligatorias")
        est = {"ACERTADA": "EVALUADA_ACERTADA", "FALLIDA": "EVALUADA_FALLIDA", "NO_EVALUABLE": "NO_EVALUABLE"}[decision]
        self.k.x("UPDATE k4c_pred SET estado=?, revision=? WHERE id=?", (est, json.dumps({"actor": actor, "decision": decision, "nota": nota, "fecha": now()}), pid)); self.k.audit(actor, "k4c.pred_revision", {"id": pid, "decision": decision}); return self.get(pid)

    def calibracion(self, entorno="REAL"):
        r = {x["estado"]: x["n"] for x in self.k.q("SELECT estado, COUNT(*) n FROM k4c_pred WHERE entorno=? GROUP BY estado", (entorno,))}
        ac, fa = r.get("EVALUADA_ACERTADA", 0), r.get("EVALUADA_FALLIDA", 0)
        return {"entorno": entorno, "registradas": sum(r.values()), "pendientes_resultado": r.get("REGISTRADA", 0), "pendientes_revision": r.get("PENDIENTE_REVISION", 0), "acertadas": ac, "fallidas": fa, "no_evaluables": r.get("NO_EVALUABLE", 0), "tasa_acierto": (ac / (ac + fa)) if ac + fa else None,
                "nota": "Con menos de 20 predicciones evaluadas la tasa no es estadísticamente interpretable." + (" Las predicciones SINTÉTICAS no cuentan para la calibración comercial real." if entorno == "REAL" else " Calibración SINTÉTICA: solo para probar el motor.")}
