"""K4 · Consejero · F2 — MOTOR: plan de investigación + árbol de hipótesis (con búsqueda deliberada de evidencia contraria), libro de evidencias, informe estructurado,
verificación, evaluación adversarial, decisión por reglas explícitas, diseño de experimento, predicciones para seguimiento e integración con el Director/expedientes.
Honestidad: con proveedores SIMULADOS el motor demuestra trazabilidad y sensibilidad a la evidencia; NO demuestra razonamiento autónomo de un modelo real."""
import json, re, statistics
from .k4_store import now
from .k4c_ledger import Libro, RANGO_CAL
from .k4c_providers import Router
from .k4c_verifier import Verificador, numeros
from . import k4c_fases as F
from .k4c_pred import Predicciones
import datetime

CAT = {"PRODUCTO": "PRECIO", "MEDICAMENTO": "PRECIO", "NORMA": "NORMATIVA", "INGREDIENTE": "INGREDIENTE", "METODO": "GENERAL"}


def _precio_100(txt):
    n = numeros(txt)  # heurística sintética: «NN ml … PP,PP EUR»
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*ml", txt, re.I); p = re.search(r"(\d+(?:[.,]\d+)?)\s*EUR", txt)
    if not (m and p): return None
    return float(m.group(1).replace(",", ".")), float(p.group(1).replace(",", "."))


class Motor:
    def __init__(self, k4, router, director=None):
        self.k = k4; self.R = router; self.L = Libro(k4); self.V = Verificador(self.L); self.D = director

    def investigar(self, pregunta, producto, propio, datos_internos=None, actor="sistema", hoy="2026-11-19", premisas=None, ficha=None, maestro=None, confirmacion=None):
        """Orquesta las fases: (0) coherencia con ficha maestra · (1) generación de hipótesis · (2) investigación · (3) evaluación de evidencias · (4) análisis económico · (5) recomendación · verificación."""
        di = datos_internos or {}; ficha = ficha or F.FICHA_ACTIVCORE
        try: modo = self.R.proveedor("busqueda").modo
        except LookupError: modo = "SIMULADO"
        entorno = "SINTETICO" if modo == "SIMULADO" else "REAL"
        iid = self.L.nueva_inv(pregunta, producto, entorno, modo, actor)
        coh = F.coherencia(maestro, propio); conf_usada = None
        if not coh["coherente"]:
            if confirmacion and len(str(confirmacion.get("motivo") or "")) >= 10 and confirmacion.get("usar") in ("MAESTRO", "DECLARADO") and confirmacion.get("actor"):
                conf_usada = dict(confirmacion, fecha=now()); self.k.audit(confirmacion["actor"], "k4c.confirma_discrepancia", {"inv": iid, "usar": confirmacion["usar"], "motivo": confirmacion["motivo"], "discrepancias": coh["discrepancias"]})
                if confirmacion["usar"] == "MAESTRO" and maestro and maestro.get("pvp"): propio = {"precio": maestro["pvp"], "volumen_ml": maestro["volumen_ml"]}
            else:
                inf = {"id": iid, "pregunta": pregunta, "producto": producto, "fecha": hoy, "afirmaciones": [], "hipotesis": [], "busquedas": [], "no_investigado": [], "premisas": [], "coherencia_maestro": coh,
                       "conclusion": {"decision": "BLOQUEADO", "confianza": "BAJA", "motivo": "Discrepancia con la ficha maestra: " + "; ".join(x["detalle"] for x in coh["discrepancias"]) + ". No se investiga ni se concluye hasta confirmar el dato (usar ficha maestra o confirmar el declarado con motivo).", "base": [], "tesis_aht": None, "alternativas_consideradas": [], "cambia_si": ["Se corrige o confirma el dato maestro."]},
                       "publicacion": {"estado": "NO_PUBLICABLE", "entorno": entorno, "aviso": "BLOQUEADO POR DATO MAESTRO"}}
                self.L.guardar_inv(iid, "BLOQUEADA_DATO_MAESTRO", informe=inf); self.k.audit(actor, "k4c.bloqueo_maestro", {"inv": iid, "discrepancias": coh["discrepancias"]})
                return {"id": iid, "entorno": entorno, "estado": "BLOQUEADA_DATO_MAESTRO", "informe": inf, "verificacion": {"veredicto": "NO_APLICA", "bloqueantes": 0, "avisos": 0, "problemas": []}, "adversarial": {"veredicto": "NO_APLICA", "problemas": []}, "gasto_eur": 0.0}
        hipo = F.generar_hipotesis(ficha) + [dict(h, fase="CONFIGURADA") for h in (ficha.get("extensiones") or [])]
        plan = {"hipotesis": hipo, "principio": "evaluar las hipótesis de AHT sin contradecirlas artificialmente: buscar evidencia favorable Y desfavorable y admitir que no se puede decidir", "limites": "corpus sintético; extractos etiquetados por el corpus",
                "fases": ["generacion_hipotesis", "investigacion", "evaluacion_evidencias", "analisis_economico", "recomendacion"], "plantilla": hipo[0]["plantilla"]}
        self.L.guardar_inv(iid, "EN_CURSO", plan=plan)
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
        hips = F.evaluar_evidencia(self.L.extractos_de(iid), plan["hipotesis"])
        informe = self._componer(iid, pregunta, producto, propio, di, vistos, hips, busquedas, hoy, ficha, maestro)
        informe["no_investigado"] = no_inv; informe["premisas"] = self._premisas(iid, premisas or []); informe["coherencia_maestro"] = dict(coh, confirmada=conf_usada); informe["maestro"] = maestro; informe["ficha"] = ficha
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
        inf["predicciones"] = self._predicciones(iid, inf, hoy, entorno, di)
        self.L.guardar_inv(iid, "COMPLETADA" if pub != "NO_PUBLICABLE" else "RECHAZADA", informe=inf)
        self.k.audit(actor, "k4c.investigacion", {"id": iid, "veredicto": ver["veredicto"], "adversarial": adv["veredicto"], "entorno": entorno})
        return {"id": iid, "entorno": entorno, "informe": inf, "verificacion": ver, "adversarial": adv, "gasto_eur": self.R.gasto_inv(iid)}

    def _plan(self, ficha=None):
        hs = F.generar_hipotesis(ficha or F.FICHA_ACTIVCORE); return {"hipotesis": hs, "principio": "evaluar las hipótesis de AHT sin contradecirlas artificialmente", "limites": "corpus sintético"}

    # -- informe
    def _componer(self, iid, pregunta, producto, propio, di, vistos, hips, busquedas, hoy, ficha, maestro):
        afs, n = [], [0]
        def A(tipo, texto, **kw): n[0] += 1; a = dict(id="AF-%02d" % n[0], tipo=tipo, texto=texto, citas=kw.pop("citas", []), relacion=kw.pop("relacion", "CONTEXTO"), **kw); afs.append(a); return a["id"]
        precios = []
        for u, v in sorted(vistos.items()):
            d = v["doc"]
            for hh, e, t in d.get("tags", []):
                x = "X-" + __import__("hashlib").sha256((v["fid"] + t).encode()).hexdigest()[:10]; cat = CAT.get(d["objeto"], "GENERAL")
                aid = A("HECHO", t[0].upper() + t[1:], citas=[x], relacion="FAVORABLE" if e > 0 else ("DESFAVORABLE" if e < 0 else "NEUTRA"), categoria_dato=cat, vigencia_afirmada=("ACTUAL" if d["tipo_dato"] == "ACTUAL" else "HISTORICO" if d["tipo_dato"] == "HISTORICO" else None), nivel_fuente=d["tipo_fuente"], nivel_fuente_afirmado=d["tipo_fuente"], fecha_dato=d["fecha_publicacion"], hipotesis=hh)
                if cat == "PRECIO" and d["objeto"] in ("PRODUCTO", "MEDICAMENTO"):
                    vp = _precio_100(t)
                    if vp: precios.append(dict(a=aid, x=x, vol=vp[0], pre=vp[1], doc=d))
        comps = []
        for p in precios:
            a = next(z for z in afs if z["id"] == p["a"]); va = p["doc"]["tipo_dato"] == "ACTUAL"; cat = p["doc"].get("categoria") or p["doc"]["objeto"]
            cid = A("HECHO", "Precio por 100 ml calculado: %s" % (p["doc"]["titulo"].replace("[SINTÉTICO] ", "")), citas=[p["x"]], relacion="CONTEXTO", categoria_dato="PRECIO", vigencia_afirmada="ACTUAL" if va else "HISTORICO", fecha_dato=p["doc"]["fecha_publicacion"], nivel_fuente=p["doc"]["tipo_fuente"], texto_verificable=a["texto"], categoria_comparable=cat,
                    calculo={"inputs": {"precio": {"valor": p["pre"], "origen": {"extracto": p["x"]}}, "volumen": {"valor": p["vol"], "origen": {"extracto": p["x"]}}}, "expr": "precio / volumen * 100", "resultado": round(p["pre"] / p["vol"] * 100, 2)})
            if p["doc"]["objeto"] == "PRODUCTO": comps.append({"nombre": p["doc"]["titulo"].replace("[SINTÉTICO] ", ""), "p100": afs[-1]["calculo"]["resultado"], "vigente": va, "categoria": cat, "aid": cid})
            if p["doc"]["objeto"] == "MEDICAMENTO": afs[-1]["comparacion"] = {"a": {"categoria": "COSMETICO_PREMIUM", "unidad_base": "100ML"}, "b": {"categoria": "MEDICAMENTO", "unidad_base": "100ML"}, "relacion_declarada": "SUSTITUTO_INDIRECTO"}; afs[-1]["texto"] += " (sustituto terapéutico indirecto, no competidor cosmético equivalente)"
        precio, vol = propio["precio"], propio["volumen_ml"]; propio100 = round(precio / vol * 100, 2)
        origen = {"maestro": True} if maestro else {"interno": "declarado"}
        id_propio = A("HECHO", "Precio propio por 100 ml (%s): %s EUR" % ("ficha maestra" if maestro else "dato declarado sin ficha maestra", propio100), dato_interno=True, categoria_dato="PRECIO", vigencia_afirmada="ACTUAL", relacion="CONTEXTO", calculo={"inputs": {"precio": {"valor": precio, "origen": dict(origen)}, "volumen": {"valor": vol, "origen": dict(origen)}}, "expr": "precio / volumen * 100", "resultado": propio100})
        # fase 4: análisis económico (sin recomendar)
        econ = F.analisis_economico(propio100, comps, di, ficha)
        faltan = [("Ensayo clínico o prueba de eficacia/seguridad de la fórmula final de %s" % ficha["producto"], "No se localizó evidencia en las consultas del libro (no equivale a ausencia de efecto)."), ("Clasificación regulatoria del caso concreto con fuente oficial", "Pendiente de análisis de la presentación completa y las alegaciones.")]
        if not econ["datos_internos_completos"]: faltan.append(("Ventas y margen unitario reales de %s" % ficha["producto"], "No hay datos internos: sin ellos no se puede decidir el precio."))
        if econ["n_equivalentes_vigentes"] < 3: faltan.append(("Al menos 3 comparables vigentes y equivalentes", "Solo %d vigentes y equivalentes localizados%s." % (econ["n_equivalentes_vigentes"], ("; excluidos: " + ", ".join("%s (%s)" % (x["nombre"], x["motivo"]) for x in econ["excluidos"])) if econ["excluidos"] else "")))
        if econ["datos_internos_completos"] and not econ["respuesta_precio"]: faltan.append(("Respuesta de la demanda al precio (elasticidad medida, n≥8 observaciones y fuente)", "Sin ella la posición frente al rango no indica en qué sentido mover el precio."))
        idf = [A("FALTANTE", t + ". " + m, relacion="AUSENCIA") for t, m in faltan]
        for a in afs:
            if a["id"] in idf and "fórmula final" in a["texto"]: a["tipo_hallazgo"] = "AUSENCIA_LOCALIZADA"
        A("INFERENCIA", "Las señales de BSR no permiten estimar ventas reales ni demostrar causalidad con el precio.", relacion="CONTEXTO", estimacion_declarada=True)
        tes = next((h for h in hips if h["tipo"] == "TESIS_INGREDIENTE"), hips[0])
        # fase 5: recomendación
        rec = F.recomendar(tes, econ, di, True, precio)
        exp = self._experimento(di); base = list(idf)
        if rec["decision"] in ("DISENAR_EXPERIMENTO", "SUBIR", "BAJAR", "MANTENER"):
            base = [id_propio] + [c["aid"] for c in comps if c["vigente"] and c["categoria"] in set(ficha.get("categorias_comparables") or [])] + [i for i in idf if "demanda" in next(a["texto"] for a in afs if a["id"] == i).lower()]
            next(a for a in afs if a["id"] == id_propio)["dato_interno"] = True
        if rec["decision"] in ("SUBIR", "BAJAR", "MANTENER") and rec.get("optimo") is not None:
            e = econ["elasticidad"]; cvar = round(precio - di["margen_unitario"], 4)
            ido = A("HECHO", "Precio óptimo de margen con elasticidad medida e=%s (n=%d, %s): %s EUR" % (e["valor"], e["n_obs"], e["fuente"], rec["optimo"]), dato_interno=True, respuesta_precio=True, relacion="CONTEXTO", categoria_dato="PRECIO", vigencia_afirmada="ACTUAL",
                    calculo={"inputs": {"coste": {"valor": cvar, "origen": {"interno": "precio - margen unitario"}}, "e": {"valor": e["valor"], "origen": {"interno": "elasticidad medida"}}}, "expr": "coste * e / (1 + e)", "resultado": rec["optimo"]}); base.append(ido)
        elif rec["decision"] == "SUBIR": ido = A("HECHO", "Elasticidad medida e=%s (n=%d, %s): demanda inelástica" % (econ["elasticidad"]["valor"], econ["elasticidad"]["n_obs"], econ["elasticidad"]["fuente"]), dato_interno=True, respuesta_precio=True, relacion="CONTEXTO", categoria_dato="PRECIO"); base.append(ido)
        cambia = ["Aparecen ≥3 comparables vigentes y equivalentes (cambia el rango de referencia).", "Se obtienen ventas y margen reales y una medida de la respuesta de la demanda al precio.", "Se localiza evidencia de la fórmula final, a favor o en contra.", "Una corrección o retractación de la evidencia del ingrediente (debilita la tesis de AHT)."]
        concl = {"decision": rec["decision"], "confianza": rec["confianza"], "motivo": rec["motivo"], "base": base, "tesis_aht": {"hipotesis": tes["id"], "estado": tes["estado"], "alcance": "evidencia de INGREDIENTE; no equivale a eficacia de la fórmula final"}, "alternativas_consideradas": [h["id"] for h in hips if h["id"] != tes["id"]], "cambia_si": cambia}
        return {"id": iid, "pregunta": pregunta, "producto": producto, "fecha": hoy, "afirmaciones": afs, "hipotesis": hips, "conclusion": concl, "experimento": exp, "busquedas": busquedas, "analisis_economico": econ,
                "fases": {"1_generacion_hipotesis": [h["id"] for h in hips], "2_investigacion": "%d búsquedas" % len(busquedas), "3_evaluacion_evidencias": {h["id"]: h["estado"] for h in hips}, "4_analisis_economico": "sin recomendación", "5_recomendacion": rec["decision"]},
                "secciones": ["1_pregunta", "2_resumen", "3_hechos", "4_hipotesis", "5_inferencias", "6_datos_faltantes", "7_evidencia_desfavorable", "8_decision", "9_experimento", "10_riesgos_y_cambia_si"],
                "correcciones_incorporadas": ["minoxidil=sustituto indirecto", "clasificación regulatoria según presentación completa", "experimento según tráfico/variabilidad (no 3 días fijos)", "ingrediente≠fórmula final", "ausencia localizada≠ausencia de efecto", "BSR≠ventas; correlación≠causa", "rango de competidores no decide SUBIR/BAJAR", "coherencia con ficha maestra"]}

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

    # -- predicciones evaluables
    def _predicciones(self, iid, inf, hoy, entorno, di):
        c = inf["conclusion"]; P = Predicciones(self.k); ini = hoy; d0 = datetime.date.fromisoformat(hoy); out = []
        try:
            if c["decision"] == "NO_CONCLUIBLE": out.append(P.registrar(iid, "H-datos", "Con ventas y margen cargados se podrá decidir el precio", "datos_internos_disponibles (1=sí)", "DISPONIBLE", None, ini, (d0 + datetime.timedelta(days=14)).isoformat(), None, entorno))
            elif c["decision"] in ("DISENAR_EXPERIMENTO", "SUBIR", "BAJAR", "MANTENER") and di.get("conv_base"):
                dias = int(inf["experimento"].get("dias_estimados") or 28); out.append(P.registrar(iid, c["tesis_aht"]["hipotesis"], "Tras «%s» la conversión no cae más de un 5 %% respecto a la base" % c["decision"], "conversion", "NO_CAE_MAS_DE", 0.05, ini, (d0 + datetime.timedelta(days=dias)).isoformat(), di["conv_base"], entorno))
        except ValueError as e: inf.setdefault("avisos", []).append("predicción no registrable: %s" % e)
        return out

    def resultado_prediccion(self, pid, valor, fuente, metodo, incertidumbre, fecha, actor): return Predicciones(self.k).resultado(pid, valor, fuente, metodo, incertidumbre, fecha, actor)
    def revisar_prediccion(self, pid, actor, decision, nota): return Predicciones(self.k).revisar(pid, actor, decision, nota)
    def calibracion(self, entorno="REAL"): return Predicciones(self.k).calibracion(entorno)

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
