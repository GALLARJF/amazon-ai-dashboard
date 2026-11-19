"""K4 · Director IA — dossiers analíticos TRAZABLES (hoy 100 % determinista; IA externa DESACTIVADA).
Detecta → investiga con datos ya disponibles → propone → registra decisión (Ops N3, sin ejecución externa) → mide resultado (sin atribución automática)."""
import json, uuid
from . import k4_pricing as P, k4_contracts as C
from .k4_store import now


def capacidades(ai_cfg=None, planner=None):
    return {"deterministas_actuales": ["Dictamen de precio de 5 tipos (K4)", "Segmentación K3", "Economía por unidad (eu)", "7 coworkers deterministas", "Dossiers analíticos", "Cola de tareas y decisiones N3 (Ops)", "Registro hipótesis→resultado"],
            "ia_externa": "DESACTIVADA (0 € de gasto; sin llamadas a modelos externos)",
            "autonomia_verificada": planner or {"estado": "NO VERIFICADA", "detalle": "Planificador autónomo definitivo pendiente de implementar (opción A + vigilante C1). Hoy: ejecución bajo demanda y cola Ops existente."},
            "no_operativo": ["SP-API (solo adaptador de lectura probado con simulador)", "Amazon Ads (idem)", "Keepa de pago (desactivado)", "Acciones comerciales externas (bloqueadas)"],
            "aviso": "Un informe periódico NO es dirección comercial autónoma: el Director detecta, investiga, propone y mide con los datos disponibles; las acciones externas exigen aprobación humana y siguen bloqueadas."}


def construir(dict_, ctx, medios=None):
    d = dict_; falt = d.get("faltantes", [])
    inv = [{"paso": "Leer panel premium K3", "resultado": ("n vigente = %s" % (ctx.get("panel_premium") or {}).get("n_precio_vigente", "n/d"))},
           {"paso": "Leer ficha de costes", "resultado": "%d conceptos sin dato · %d pendientes de validar" % (sum(1 for c in ctx["ficha"] if c["estado"] == "FALTA"), sum(1 for c in ctx["ficha"] if c["estado"] == "PENDIENTE_VALIDAR"))},
           {"paso": "Leer KPIs comerciales importados", "resultado": "ventas: " + ("SIN_DATO" if ctx["kpis"]["unidades"]["estado"] == "SIN_DATO" else "%s uds (%s)" % (ctx["kpis"]["unidades"]["valor"], ctx["kpis"]["unidades"]["periodo"]))},
           {"paso": "Comprobar imagen verificada del propio producto", "resultado": (medios or {}).get("estado", "n/d")}]
    problema = {5: "No hay evidencia suficiente para decidir el precio de %s en %s", 4: "El problema de %s en %s no se corrige con el precio", 1: "%s en %s: precio por debajo de premium con margen disponible", 3: "%s en %s: precio alto frente a premium con señal de baja conversión", 2: "%s en %s: precio coherente con el mercado"}[d["tipo"]] % (d["producto"], d["pais"])
    exp = [{"experimento": f["como"], "para": f["dato"]} for f in falt]
    dos = {"id": "DOS-" + uuid.uuid4().hex[:8], "tipo": "precio", "producto": d["producto"], "pais": d["pais"], "entorno": d["entorno"], "problema_detectado": problema, "evidencias": d["trazabilidad"], "hipotesis_alternativas": [h for h in P.hipotesis_alt(d)],
           "investigacion_realizada": inv, "dictamen": {"tipo": d["tipo"], "nombre": d["tipo_nombre"], "justificacion": d["justificacion"], "intervalo_recomendado": d.get("intervalo_recomendado")}, "confianza": d["confianza"],
           "escenarios": d["escenarios"], "accion_recomendada": d["proxima_accion"], "responsable": "Dirección comercial AHT (aprobador)", "criterio_exito": _exito(d), "revision_posterior": d["criterio_revision"],
           "datos_faltantes": falt, "como_obtenerlos": exp, "riesgos": d["riesgos"], "imagen_propia": medios, "capacidad": "DETERMINISTA · IA externa desactivada", "generado": now()}
    return dos


def _exito(d):
    return {5: "Costes validados y ≥14 días de ventas cargadas → dictamen distinto de «evidencia insuficiente»", 4: "La causa detectada desaparece (ACoS ≤ equilibrio / cobertura ≥ mínimo / conversión recuperada) durante 14 días",
            1: "Margen ≥ umbral y unidades/día no caen más de lo previsto en el rango de elasticidad durante 14 días", 3: "Conversión y unidades suben sin bajar el margen por debajo del umbral", 2: "Margen y unidades estables 14 días"}[d["tipo"]]


class Director:
    def __init__(self, k4, ops, data):
        self.k, self.ops, self.data = k4, ops, data

    def guardar(self, dos, actor):
        self.k.x("INSERT OR REPLACE INTO k4_dossier VALUES(?,?,?,?,?,?,?,?,?)", (dos["id"], dos["tipo"], dos.get("producto"), dos.get("problema_detectado") or dos.get("titulo") or "", self.k.j(dos), "ABIERTO", actor, now(), now()))
        self.k.audit(actor, "k4.dossier", {"id": dos["id"], "tipo": dos["tipo"], "producto": dos.get("producto")})
        return dos["id"]

    def listar(self, producto=None, tipo=None):
        rows = self.k.q("SELECT id,tipo,producto,titulo,estado,creado FROM k4_dossier WHERE (?1 IS NULL OR producto=?1) AND (?2 IS NULL OR tipo=?2) ORDER BY creado DESC LIMIT 100", (producto, tipo))
        return rows

    def obtener(self, did):
        r = self.k.q("SELECT * FROM k4_dossier WHERE id=?", (did,))
        if not r: raise LookupError("dossier inexistente")
        return dict(json.loads(r[0]["datos"]), estado=r[0]["estado"])

    def proponer(self, did, actor):
        """Registra una decisión N3 para una persona (no ejecuta nada). Solo dictámenes 1–4 con acción: el tipo 5 genera tarea de obtención de datos, no decisión de precio."""
        dos = self.obtener(did); t = dos["dictamen"]["tipo"]
        if t == 5: raise ValueError("el dictamen es EVIDENCIA INSUFICIENTE: no hay decisión de precio que proponer; obtén los datos faltantes")
        kind = "cambiar_precio" if t in (1, 3) else "revisar_causa"
        item = {"dossier": did, "pais": dos["pais"], "dictamen": dos["dictamen"]["nombre"], "accion": dos["accion_recomendada"], "confianza": dos["confianza"]}
        decid = self.ops.request_decision(dos["producto"], "k4_" + kind, "K4 · " + dos["dictamen"]["nombre"] + " · " + dos["pais"], item)
        lid = self.ops.ledger_add(dos["producto"], decid, "Dictamen K4 %s" % dos["dictamen"]["nombre"], hypothesis=dos["problema_detectado"], evidence=dos["evidencias"][:5], recommendation=dos["accion_recomendada"], approval="PENDIENTE", action="PROPUESTA (sin ejecución externa)")
        f = self.k.x("INSERT INTO k4_followup(decision_id,ledger_id,producto,pais,accion,estado,creado,entorno,metrica,ventana_dias) VALUES(?,?,?,?,?,'PROPUESTA',?,?,?,?)", (decid, lid, dos["producto"], dos["pais"], dos["accion_recomendada"], now(), dos["entorno"], "unidades,conversion,margen", 14))
        self.k.audit(actor, "k4.propuesta", {"dossier": did, "decision": decid, "ledger": lid})
        return {"decision_id": decid, "ledger_id": lid, "followup_id": f.lastrowid, "nota": "Decisión registrada para aprobación humana. Ninguna acción externa se ejecuta."}

    def registrar_ejecucion(self, fid, ejecutor, fecha, actor):
        if not C.iso_date(fecha): raise ValueError("fecha inválida")
        r = self.k.q("SELECT * FROM k4_followup WHERE id=?", (fid,))
        if not r: raise LookupError("seguimiento inexistente")
        base = self.data.kpis({"producto": r[0]["producto"], "pais": r[0]["pais"], "hasta": fecha}, r[0]["entorno"])
        self.k.x("UPDATE k4_followup SET estado='EJECUTADA_POR_PERSONA', ejecutor=?, ejecutada_en=?, base=? WHERE id=?", (ejecutor[:80], fecha, self.k.j({k: base[k]["valor"] for k in ("unidades", "conversion", "acos")}), fid))
        self.k.audit(actor, "k4.seguimiento.ejecucion", {"id": fid, "fecha": fecha})

    def medir(self, fid, actor):
        r = self.k.q("SELECT * FROM k4_followup WHERE id=?", (fid,))
        if not r or r[0]["estado"] != "EJECUTADA_POR_PERSONA": raise ValueError("el seguimiento no tiene ejecución registrada por una persona")
        f = r[0]; post = self.data.kpis({"producto": f["producto"], "pais": f["pais"], "desde": f["ejecutada_en"]}, f["entorno"])
        pv = {k: post[k]["valor"] for k in ("unidades", "conversion", "acos")}; b = json.loads(f["base"] or "{}")
        res = {"base": b, "posterior": pv, "atribucion": "NO_ATRIBUIDO_AUTOMATICAMENTE: la comparación es descriptiva; otros factores (estacionalidad, Ads, stock) pueden explicar el cambio",
               "suficiente": all(v is not None for v in pv.values())}
        self.k.x("UPDATE k4_followup SET post=?, resultado=?, estado=? WHERE id=?", (self.k.j(pv), self.k.j(res), "MEDIDA" if res["suficiente"] else "MEDIDA_PARCIAL", fid))
        if f["ledger_id"]: self.ops.ledger_observe(f["ledger_id"], "Medición descriptiva (sin atribución causal)", followup="Revisar con ≥14 días de datos")
        self.k.audit(actor, "k4.seguimiento.medicion", {"id": fid})
        return res

    def seguimientos(self, producto=None):
        return self.k.q("SELECT * FROM k4_followup WHERE (?1 IS NULL OR producto=?1) ORDER BY id DESC LIMIT 100", (producto,))

    # ---- nuevos productos
    def nuevo_producto(self, d, actor):
        if not d.get("titulo"): raise ValueError("falta título")
        faltan = []
        for k, q in (("necesidad", "Necesidad del cliente y evidencia (búsquedas, reseñas, ventas de referencia)"), ("competidores", "Competidores directos con ASIN (K3/Keepa con autorización)"), ("coste_objetivo", "Coste unitario objetivo con alcance validado"), ("pvp_objetivo", "PVP objetivo y margen mínimo"), ("regulacion", "Requisitos regulatorios/claims (cosmético UE, suplemento)")):
            if not d.get(k): faltan.append({"dato": q, "estado": "SIN_DATO"})
        dos = {"id": "NPR-" + uuid.uuid4().hex[:8], "tipo": "nuevo_producto", "producto": d.get("producto"), "titulo": str(d["titulo"])[:160], "categoria": str(d.get("categoria") or "")[:80], "datos": {k: d.get(k) for k in ("necesidad", "competidores", "coste_objetivo", "pvp_objetivo", "regulacion")},
               "datos_faltantes": faltan, "hipotesis": [C.afirmacion("HIPOTESIS", d["necesidad"])] if d.get("necesidad") else [], "estado_decision": "NO_EVALUADO", "regla": "Sin necesidad, competidores, costes y regulación documentados no se emite recomendación de lanzar.", "entorno": "PRODUCCION", "generado": now()}
        dos["problema_detectado"] = dos["titulo"]
        return self.guardar(dos, actor)
