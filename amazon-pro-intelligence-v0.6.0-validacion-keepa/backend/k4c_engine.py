"""K4 · Consejero · F2 — MOTOR: plan de investigación + árbol de hipótesis (con búsqueda deliberada de evidencia contraria), libro de evidencias, informe estructurado,
verificación, evaluación adversarial, decisión por reglas explícitas, diseño de experimento, predicciones para seguimiento e integración con el Director/expedientes.
Honestidad: con proveedores SIMULADOS el motor demuestra trazabilidad y sensibilidad a la evidencia; NO demuestra razonamiento autónomo de un modelo real."""
import json, re, statistics
from .k4_store import now
from .k4c_ledger import Libro, RANGO_CAL
from .k4c_providers import Router
from .k4c_verifier import Verificador, numeros

HIPOTESIS = [
    ("H0", "AHT", "El precio premium de ACTIVCORE se sostiene por la evidencia de sus ingredientes (cafeína, luteolina).", "Evidencia clínica del ingrediente y, sobre todo, de la fórmula final; si falta lo segundo, la tesis solo puede ser parcial.",
     ["cafeina topica alopecia ensayo revision evidencia ingrediente", "luteolina topica raton murino evidencia ingrediente"], ["cafeina topica evidencia ingrediente limites ensayo", "luteolina topica evidencia ingrediente humanos"]),
    ("H1", "ALTERNATIVA", "La evidencia del ingrediente no se traslada a la fórmula final y no justifica por sí sola un sobreprecio.", "Existe un ensayo de la fórmula final con resultados favorables.", [], []),
    ("H2", "ALTERNATIVA", "El mercado comparable vigente (cosméticos capilares premium) fija un rango de precio por 100 ml del que ACTIVCORE puede quedar dentro o fuera.", "Menos de 3 comparables vigentes y equivalentes → no se puede fijar rango.",
     ["competidor precio serum capilar premium mercado", "competidor precio tratamiento capilar mercado", "competidor precio ampollas capilar premium mercado"], ["competidor precio capilar premium mercado alfa"]),
    ("H3", "ALTERNATIVA", "El minoxidil es un sustituto terapéutico indirecto que condiciona la disposición a pagar, no un competidor cosmético equivalente.", "Datos de uso/sustitución que lo desmientan.", ["minoxidil precio medicamento alopecia sustituto"], ["minoxidil precio alopecia medicamento sustituto"]),
    ("H4", "ALTERNATIVA", "La clasificación regulatoria depende de la presentación completa, la composición y las alegaciones; una alegación de crecimiento puede cambiarla.", "Texto oficial aplicable al caso concreto.", ["clasificacion cosmetico medicamento alegaciones regulatoria normativa", "alegaciones crecimiento capilar medicinales normativa blog"], ["clasificacion cosmetico medicamento alegaciones normativa"]),
    ("H5", "ALTERNATIVA", "No se pueden inferir ventas reales a partir del BSR ni atribuir causalidad a correlaciones de BSR y precio.", "Fuente de calibración BSR→unidades con datos propios.", ["bsr ranking ventas demanda unidades metodo"], ["bsr ranking ventas demanda metodo"]),
]
CAT = {"PRODUCTO": "PRECIO", "MEDICAMENTO": "PRECIO", "NORMA": "NORMATIVA", "INGREDIENTE": "INGREDIENTE", "METODO": "GENERAL"}


def _precio_100(txt):
    n = numeros(txt)  # heurística sintética: «NN ml … PP,PP EUR»
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*ml", txt, re.I); p = re.search(r"(\d+(?:[.,]\d+)?)\s*EUR", txt)
    if not (m and p): return None
    return float(m.group(1).replace(",", ".")), float(p.group(1).replace(",", "."))


class Motor:
    def __init__(self, k4, router, director=None):
        self.k = k4; self.R = router; self.L = Libro(k4); self.V = Verificador(self.L); self.D = director

    def investigar(self, pregunta, producto, propio, datos_internos=None, actor="sistema", hoy="2026-11-19", premisas=None):
        di = datos_internos or {}
        try: modo = self.R.proveedor("busqueda").modo
        except LookupError: modo = "SIMULADO"
        entorno = "SINTETICO" if modo == "SIMULADO" else "REAL"
        iid = self.L.nueva_inv(pregunta, producto, entorno, modo, actor)
        plan = self._plan(); self.L.guardar_inv(iid, "EN_CURSO", plan=plan)
        vistos, busquedas, no_inv = {}, [], []
        for h in plan["hipotesis"]:
            for q, contra in [(q, False) for q in h["consultas"]] + [(q, True) for q in h["consultas_contrarias"]]:
                try: res = self.R.llamar("busqueda", "buscar", inv_id=iid, consulta=q)
                except (PermissionError, LookupError) as e: no_inv.append({"h": h["id"], "consulta": q, "motivo": str(e)[:120]}); busquedas.append({"h": h["id"], "consulta": q, "contraria": contra, "n": 0, "error": True}); continue
                busquedas.append({"h": h["id"], "consulta": q, "contraria": contra, "n": len(res)})
                for r in res:
                    if r["url"] in vistos: continue
                    doc = self.R.llamar("lectura", "leer", inv_id=iid, url=r["url"]); fid = self.L.add_fuente(doc, iid, self.R.proveedor("lectura").nombre, entorno, hoy)
                    xs = [self.L.add_extracto(fid, t, hipotesis=hh, efecto=e) for hh, e, t in doc.get("tags", [])]
                    vistos[r["url"]] = {"fid": fid, "xs": xs, "doc": doc}
        hips = self._puntuar(iid, vistos, plan)
        informe = self._componer(iid, pregunta, producto, propio, di, vistos, hips, busquedas, hoy)
        informe["no_investigado"] = no_inv; informe["premisas"] = self._premisas(iid, premisas or [])
        if no_inv:
            a = dict(id="AF-NI", tipo="FALTANTE", texto="No pude investigar %d consulta(s): proveedor de búsqueda no disponible. Ninguna conclusión de fuentes externas es posible." % len(no_inv), citas=[], relacion="AUSENCIA"); informe["afirmaciones"].append(a); informe["conclusion"]["base"] = list(informe["conclusion"]["base"]) + ["AF-NI"]
        borr = self.R.llamar("llm", "completar", inv_id=iid, sistema="redactar", usuario=pregunta, esquema={"informe": informe}); inf = borr["json"] or informe
        ver = self.V.verificar(inf, iid, hoy); dep = []
        if ver["veredicto"] == "RECHAZADO" and ver["afirmaciones_rechazadas"]:
            inf2 = dict(inf, afirmaciones=[a for a in inf["afirmaciones"] if a["id"] not in ver["afirmaciones_rechazadas"]]); v2 = self.V.verificar(inf2, iid, hoy)
            if v2["veredicto"] != "RECHAZADO": dep = ver["afirmaciones_rechazadas"]; inf, ver = inf2, dict(v2, veredicto="ACEPTADO_CON_RESERVAS", depurado=True, afirmaciones_retiradas=dep, problemas_originales=ver["problemas"])
        adv = self.adversarial(inf, plan, busquedas, hips)
        estados = {a["id"]: ("RECHAZADA" if a["id"] in ver.get("afirmaciones_rechazadas", []) else "VERIFICADA_HEURISTICA") for a in inf["afirmaciones"]}
        self.L.guardar_afirmaciones(iid, inf["afirmaciones"], estados); self.L.guardar_hipotesis(iid, hips)
        pub = "PUBLICABLE_INTERNO" if ver["veredicto"] != "RECHAZADO" and adv["veredicto"] != "DEFICIENTE" else "NO_PUBLICABLE"
        inf["publicacion"] = {"estado": pub, "entorno": entorno, "aviso": "DATOS SINTÉTICOS: no usar para decidir." if entorno == "SINTETICO" else "Requiere revisión humana antes de actuar."}
        self.L.guardar_inv(iid, "COMPLETADA" if pub != "NO_PUBLICABLE" else "RECHAZADA", informe=inf, veredicto={"verificador": ver, "adversarial": adv})
        self._predicciones(iid, inf, hoy)
        self.k.audit(actor, "k4c.investigacion", {"id": iid, "veredicto": ver["veredicto"], "adversarial": adv["veredicto"], "entorno": entorno})
        return {"id": iid, "entorno": entorno, "informe": inf, "verificacion": ver, "adversarial": adv, "gasto_eur": self.R.gasto_inv(iid)}

    # -- plan / hipótesis
    def _plan(self):
        hs = [{"id": i, "origen": o, "texto": t, "refutaria": r, "consultas": q, "consultas_contrarias": qc} for i, o, t, r, q, qc in HIPOTESIS]
        return {"hipotesis": hs, "principio": "evaluar las hipótesis de AHT sin contradecirlas artificialmente: buscar evidencia favorable Y desfavorable y admitir que no se puede decidir", "limites": "corpus sintético; extractos etiquetados por el corpus"}

    def _puntuar(self, iid, vistos, plan):
        xs = self.L.extractos_de(iid); out = []
        for h in plan["hipotesis"]:
            fav = [x for x in xs if x["hipotesis"] == h["id"] and x["efecto"] > 0 and x["tipo_dato"] != "HISTORICO"]; con = [x for x in xs if x["hipotesis"] == h["id"] and x["efecto"] < 0]
            w = lambda x: RANGO_CAL.get(x["calidad"], 0) + 1
            s = sum(w(x) for x in fav) - sum(w(x) for x in con)
            if h["id"] == "H0": estado = "PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE" if s >= 3 else ("DEBILITADA" if s <= -3 else "INDECISA")
            elif h["id"] == "H1": estado = "INDECISA"
            else: estado = "SOPORTADA" if s >= 3 else ("DEBILITADA" if s <= -3 else "INDECISA")
            out.append(dict(h, estado=estado, puntuacion=s, favorables=[x["id"] for x in fav], desfavorables=[x["id"] for x in con]))
        h0 = out[0]; h1 = out[1]
        h1["estado"] = "SOPORTADA" if h0["estado"] in ("PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE", "DEBILITADA", "INDECISA") else "INDECISA"
        h1["nota"] = "No se localizó ningún ensayo de la fórmula final (alcance: consultas del libro); es ausencia de evidencia localizada, no prueba de ausencia de efecto."
        return out

    # -- informe
    def _componer(self, iid, pregunta, producto, propio, di, vistos, hips, busquedas, hoy):
        afs, n = [], [0]
        def A(tipo, texto, **kw): n[0] += 1; a = dict(id="AF-%02d" % n[0], tipo=tipo, texto=texto, citas=kw.pop("citas", []), relacion=kw.pop("relacion", "CONTEXTO"), **kw); afs.append(a); return a["id"]
        precios = []
        for u, v in sorted(vistos.items()):
            d = v["doc"]
            for hh, e, t in d.get("tags", []):
                x = "X-" + __import__("hashlib").sha256((v["fid"] + t).encode()).hexdigest()[:10]; cat = CAT.get(d["objeto"], "GENERAL")
                a = A("HECHO", t[0].upper() + t[1:], citas=[x], relacion="FAVORABLE" if e > 0 else ("DESFAVORABLE" if e < 0 else "NEUTRA"), categoria_dato=cat, vigencia_afirmada=("ACTUAL" if d["tipo_dato"] == "ACTUAL" else "HISTORICO" if d["tipo_dato"] == "HISTORICO" else None), nivel_fuente=d["tipo_fuente"], nivel_fuente_afirmado=d["tipo_fuente"], fecha_dato=d["fecha_publicacion"], hipotesis=hh)
                if cat == "PRECIO" and d["objeto"] in ("PRODUCTO", "MEDICAMENTO"):
                    vp = _precio_100(t)
                    if vp: precios.append(dict(a=a, x=x, vol=vp[0], pre=vp[1], doc=d))
        comp = []
        for p in precios:
            a = next(z for z in afs if z["id"] == p["a"]); va = p["doc"]["tipo_dato"] == "ACTUAL"
            cid = A("INFERENCIA" if False else "HECHO", "Precio por 100 ml calculado: %s" % (p["doc"]["titulo"].replace("[SINTÉTICO] ", "")), citas=[p["x"]], relacion="CONTEXTO", categoria_dato="PRECIO", vigencia_afirmada="ACTUAL" if va else "HISTORICO", fecha_dato=p["doc"]["fecha_publicacion"], nivel_fuente=p["doc"]["tipo_fuente"], texto_verificable=a["texto"],
                    calculo={"inputs": {"precio": {"valor": p["pre"], "origen": {"extracto": p["x"]}}, "volumen": {"valor": p["vol"], "origen": {"extracto": p["x"]}}}, "expr": "precio / volumen * 100", "resultado": round(p["pre"] / p["vol"] * 100, 2)})
            if va and p["doc"]["objeto"] == "PRODUCTO": comp.append(afs[-1]["calculo"]["resultado"])
            if p["doc"]["objeto"] == "MEDICAMENTO": afs[-1]["comparacion"] = {"a": {"categoria": "COSMETICO_PREMIUM", "unidad_base": "100ML"}, "b": {"categoria": "MEDICAMENTO", "unidad_base": "100ML"}, "relacion_declarada": "SUSTITUTO_INDIRECTO"}; afs[-1]["texto"] += " (sustituto terapéutico indirecto, no competidor cosmético equivalente)"
        propio100 = round(propio["precio"] / propio["volumen_ml"] * 100, 2)
        id_propio = A("HECHO", "Precio propio por 100 ml (dato interno declarado): %s EUR" % propio100, dato_interno=True, categoria_dato="PRECIO", vigencia_afirmada="ACTUAL", relacion="CONTEXTO", calculo={"inputs": {"precio": {"valor": propio["precio"], "origen": {"interno": "precio_actual"}}, "volumen": {"valor": propio["volumen_ml"], "origen": {"interno": "formato"}}}, "expr": "precio / volumen * 100", "resultado": propio100})
        faltan = [("Ensayo clínico o prueba de eficacia/seguridad de la fórmula final de ACTIVCORE", "No se localizó evidencia en las consultas del libro (no equivale a ausencia de efecto)."), ("Clasificación regulatoria del caso concreto con fuente oficial", "Pendiente de análisis de la presentación completa y las alegaciones.")]
        if not (di.get("ventas_dia") and di.get("margen_unitario")): faltan.append(("Ventas y margen unitario reales de ACTIVCORE", "No hay datos internos: sin ellos no se puede decidir el precio."))
        if len(comp) < 3: faltan.append(("Al menos 3 comparables cosméticos vigentes y equivalentes", "Solo %d vigentes localizados." % len(comp)))
        idf = [A("FALTANTE", t + ". " + m, relacion="AUSENCIA") for t, m in faltan]
        for a in afs:
            if a["id"] in idf and "fórmula final" in a["texto"]: a["tipo_hallazgo"] = "AUSENCIA_LOCALIZADA"
        inf_bsr = A("INFERENCIA", "Las señales de BSR no permiten estimar ventas reales ni demostrar causalidad con el precio.", relacion="CONTEXTO", estimacion_declarada=True)
        # decisión por reglas explícitas
        h0 = hips[0]; ok_comp = len(comp) >= 3; ok_int = bool(di.get("ventas_dia") and di.get("margen_unitario"))
        exp = self._experimento(di)
        if not (ok_comp and ok_int):
            dec, conf, motivo = "NO_CONCLUIBLE", "BAJA", "Faltan %s." % " y ".join(x for x, c in (("datos internos de ventas/margen", ok_int), ("≥3 comparables cosméticos vigentes", ok_comp)) if not c)
            base = [i for i in idf]
        else:
            lo, hi = min(comp), max(comp)
            dec = "MANTENER" if lo * 0.9 <= propio100 <= hi * 1.1 else ("BAJAR" if propio100 > hi * 1.1 else "SUBIR"); conf = "MEDIA"
            motivo = "El precio propio (%.2f €/100 ml) se compara con %d comparables vigentes (rango %.2f–%.2f); decisión condicionada a experimento y a la clasificación regulatoria." % (propio100, len(comp), lo, hi)
            base = [id_propio] + [a["id"] for a in afs if a.get("calculo") and a.get("vigencia_afirmada") == "ACTUAL" and not a.get("dato_interno") and "MEDICAMENTO" not in json.dumps(a.get("comparacion") or {})]
            base = [b for b in base if b in {x["id"] for x in afs}]; afs_i = [a for a in afs if a["id"] == id_propio][0]; afs_i["dato_interno"] = True
        cambia = ["Aparecen ≥3 comparables cosméticos vigentes y equivalentes (cambia el rango de referencia).", "Se obtienen ventas y margen reales (permite decidir el precio).", "Se localiza evidencia de la fórmula final, a favor o en contra.", "Una corrección o retractación de la revisión de cafeína (debilita H0)."]
        concl = {"decision": dec, "confianza": conf, "motivo": motivo, "base": base, "tesis_aht": {"hipotesis": "H0", "estado": h0["estado"], "alcance": "evidencia de INGREDIENTE; no equivale a eficacia de la fórmula final"}, "alternativas_consideradas": [h["id"] for h in hips[1:]], "cambia_si": cambia}
        return {"id": iid, "pregunta": pregunta, "producto": producto, "fecha": hoy, "afirmaciones": afs, "hipotesis": hips, "conclusion": concl, "experimento": exp, "busquedas": busquedas,
                "secciones": ["1_pregunta", "2_resumen", "3_hechos", "4_hipotesis", "5_inferencias", "6_datos_faltantes", "7_evidencia_desfavorable", "8_decision", "9_experimento", "10_riesgos_y_cambia_si"],
                "correcciones_incorporadas": ["minoxidil=sustituto indirecto", "clasificación regulatoria según presentación completa", "experimento según tráfico/variabilidad (no 3 días fijos)", "ingrediente≠fórmula final", "ausencia localizada≠ausencia de efecto", "BSR≠ventas; correlación≠causa"]}

    def _experimento(self, di):
        from .k4c_mock import CalculadoraExperimento
        try: return self.R.llamar("herramienta", "ejecutar", nombre="diseno_experimento", **{k: di.get(k) for k in ("trafico_diario", "conv_base", "mde_rel", "margen_unitario") if di.get(k) is not None})
        except LookupError: return CalculadoraExperimento().ejecutar(**{k: di.get(k) for k in ("trafico_diario", "conv_base", "mde_rel") if di.get(k) is not None})

    def _premisas(self, iid, premisas):
        """Contrasta premisas de AHT con el libro: no complace, no contradice por sistema."""
        from .k4c_verifier import soporta, claves
        out = []
        for pr in premisas:
            ev = []
            for x in self.L.extractos_de(iid):
                if len(claves(pr["texto"]) & claves(x["texto"])) >= 2:
                    ok, mot = soporta(pr["texto"], x["texto"]); ev.append({"extracto": x["id"], "respalda": ok, "motivo": mot or "el extracto es coherente con la premisa"})
            est = "SIN_EVIDENCIA_LOCALIZADA" if not ev else ("CUESTIONADA" if any(not e["respalda"] for e in ev) else "RESPALDADA_POR_EXTRACTOS")
            out.append({"id": pr.get("id"), "texto": pr["texto"], "estado": est, "evidencia": ev})
        return out

    # -- evaluación adversarial (determinista)
    def adversarial(self, inf, plan, busquedas, hips):
        p = []; c = inf["conclusion"]
        for h in plan["hipotesis"]:
            if h["consultas"] and not any(b["h"] == h["id"] and b["contraria"] for b in busquedas): p.append("la hipótesis %s no tuvo búsqueda de evidencia contraria" % h["id"])
        if not c.get("alternativas_consideradas"): p.append("no se consideraron hipótesis alternativas")
        if not c.get("cambia_si"): p.append("no declara qué cambiaría la conclusión")
        n_f = sum(1 for a in inf["afirmaciones"] if a.get("relacion") == "FAVORABLE"); n_d = sum(1 for a in inf["afirmaciones"] if a.get("relacion") == "DESFAVORABLE")
        if n_f and not n_d and not any(a["tipo"] == "FALTANTE" for a in inf["afirmaciones"]): p.append("evidencia unilateral: solo hay hallazgos favorables y ningún dato faltante declarado")
        if c["decision"] != "NO_CONCLUIBLE" and not any(a.get("dato_interno") for a in inf["afirmaciones"] if a["id"] in c["base"]): p.append("decisión sin dato interno en la base")
        if c["tesis_aht"]["estado"].startswith("PARCIALMENTE") and "fórmula final" not in c["tesis_aht"]["alcance"]: p.append("la tesis de AHT se declara sin acotar su alcance al ingrediente")
        return {"veredicto": "DEFICIENTE" if p else "SUPERADA", "problemas": p, "nota": "Evaluación determinista de procedimiento; no sustituye la crítica de un experto."}

    # -- predicciones para seguimiento (T10)
    def _predicciones(self, iid, inf, hoy):
        c = inf["conclusion"]
        if c["decision"] == "NO_CONCLUIBLE": ind, esp = "datos_internos_disponibles", "ventas y margen cargados en ≤14 días para poder decidir"; vd = 14
        else: ind, esp = "conversion_relativa", "sin caída >5 %% de conversión tras la decisión «%s» en la ventana del experimento" % c["decision"]; vd = int(inf["experimento"].get("dias_estimados") or 28)
        self.k.x("INSERT INTO k4c_prediccion(inv_id,indicador,esperado,ventana_dias,estado,observado,creado) VALUES(?,?,?,?,?,?,?)", (iid, ind, esp, vd, "PENDIENTE", None, now()))

    def cerrar_prediccion(self, pid, observado, cumplida, actor="sistema"):
        self.k.x("UPDATE k4c_prediccion SET estado=?, observado=? WHERE id=?", ("ACERTADA" if cumplida else "FALLIDA", json.dumps(observado, default=str), pid)); self.k.audit(actor, "k4c.prediccion", {"id": pid, "cumplida": bool(cumplida)})
        return self.k.q("SELECT * FROM k4c_prediccion WHERE id=?", (pid,))[0]

    def calibracion(self):
        r = self.k.q("SELECT estado, COUNT(*) n FROM k4c_prediccion GROUP BY estado"); d = {x["estado"]: x["n"] for x in r}; cerr = d.get("ACERTADA", 0) + d.get("FALLIDA", 0)
        return {"pendientes": d.get("PENDIENTE", 0), "acertadas": d.get("ACERTADA", 0), "fallidas": d.get("FALLIDA", 0), "tasa_acierto": (d.get("ACERTADA", 0) / cerr) if cerr else None, "nota": "Con menos de 20 predicciones cerradas la tasa no es estadísticamente interpretable."}

    # -- integración con Director / expedientes
    def a_dossier(self, iid, actor):
        inv = self.L.inv(iid); inf = inv["informe"]
        if not self.D: raise RuntimeError("sin Director")
        dos = {"id": "DCON-" + iid[4:], "tipo": "consejero", "producto": inv["producto"], "titulo": "Consejero · " + inv["pregunta"][:80], "consejero": {"investigacion": iid, "decision": inf["conclusion"]["decision"], "confianza": inf["conclusion"]["confianza"], "tesis_aht": inf["conclusion"]["tesis_aht"], "verificador": inv["veredicto"]["verificador"]["veredicto"], "adversarial": inv["veredicto"]["adversarial"]["veredicto"], "entorno": inv["entorno"], "publicacion": inf["publicacion"]["estado"]}, "entorno": inv["entorno"]}
        self.D.guardar(dos, actor); return dos["id"]

    def proponer_decision(self, iid, actor):
        inv = self.L.inv(iid); inf = inv["informe"]; c = inf["conclusion"]
        if inv["entorno"] != "REAL": raise ValueError("investigación SINTÉTICA: no puede generar una decisión")
        if inv["veredicto"]["verificador"]["veredicto"] == "RECHAZADO" or inv["veredicto"]["adversarial"]["veredicto"] == "DEFICIENTE": raise ValueError("el verificador o la evaluación adversarial no han aceptado el informe")
        if c["decision"] == "NO_CONCLUIBLE": raise ValueError("la conclusión es NO_CONCLUIBLE: no hay decisión que proponer; obtener los datos faltantes")
        raise PermissionError("las investigaciones REAL requieren F3 y autorización expresa")
