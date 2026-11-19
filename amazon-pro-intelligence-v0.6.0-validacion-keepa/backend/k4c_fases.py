"""K4 · Consejero F2.1 — FASES SEPARADAS del razonamiento: 1) generación de hipótesis (configurable por producto/categoría/problema) · 2) investigación (en el motor, vía router) ·
3) evaluación de evidencias · 4) análisis económico · 5) recomendación. Las reglas deterministas actúan como CONTROLES; las hipótesis NO se reutilizan entre categorías.
En F3 la fase 1 podrá ampliarse con hipótesis propuestas por investigación real (`extensiones`)."""
from .k4c_ledger import RANGO_CAL

PLANTILLAS = ("COSMETICO_CAPILAR", "SUPLEMENTO_ORAL", "GENERICA")
PLANTILLA_DE = {"COSMETICO_CAPILAR": "COSMETICO_CAPILAR", "SUPLEMENTO_ORAL": "SUPLEMENTO_ORAL"}
FICHA_ACTIVCORE = {"producto": "ACTIVCORE", "categoria": "COSMETICO_CAPILAR", "problema": "PRECIO", "formato_ml": 100.0, "pvp": 49.90, "normalizacion": "100ML", "ingredientes": ["cafeina", "luteolina"],
                   "claims": ["crecimiento capilar", "anticaida"], "sustitutos_indirectos": [{"nombre": "minoxidil", "tipo": "MEDICAMENTO"}], "formatos_competidores": ["serum", "tratamiento", "ampollas"], "categorias_comparables": ["COSMETICO_CAPILAR_PREMIUM"]}
FICHA_PHIVITAL_MG = {"producto": "PhiVital Magnesio", "categoria": "SUPLEMENTO_ORAL", "problema": "PRECIO", "formato_ml": None, "pvp": None, "normalizacion": "DOSIS_DIARIA", "ingredientes": ["magnesio bisglicinato"],
                     "claims": ["fatiga", "funcion muscular"], "sustitutos_indirectos": [{"nombre": "alimentos ricos en magnesio", "tipo": "ALIMENTACION"}, {"nombre": "magnesio de farmacia", "tipo": "SUPLEMENTO_FARMACIA"}], "formatos_competidores": ["capsulas", "polvo", "comprimidos"], "categorias_comparables": ["SUPLEMENTO_MAGNESIO"]}
def _h(i, origen, tipo, texto, refuta, q, qc, plantilla): return {"id": i, "origen": origen, "tipo": tipo, "texto": texto, "refutaria": refuta, "consultas": q, "consultas_contrarias": qc, "plantilla": plantilla, "fase": "GENERACION"}


def generar_hipotesis(ficha):
    """Hipótesis configurables por producto, categoría y problema. Devuelve lista; cada hipótesis declara qué la refutaría y consultas favorables y contrarias."""
    pl = PLANTILLA_DE.get(ficha.get("categoria"), "GENERICA"); n = ficha["producto"]; ings = ficha.get("ingredientes") or []; sus = ficha.get("sustitutos_indirectos") or []; fm = ficha.get("formatos_competidores") or []
    if pl == "COSMETICO_CAPILAR":
        hs = [_h("H0", "AHT", "TESIS_INGREDIENTE", "El precio premium de %s se sostiene por la evidencia de sus ingredientes (%s)." % (n, ", ".join(ings)), "Evidencia clínica del ingrediente y, sobre todo, de la fórmula final; si falta lo segundo, la tesis solo puede ser parcial.",
                 ["%s topica evidencia ingrediente ensayo revision" % i for i in ings], ["%s topica evidencia ingrediente limites ensayo" % i for i in ings], pl),
              _h("H1", "ALTERNATIVA", "TRASLADO", "La evidencia del ingrediente no se traslada a la fórmula final y no justifica por sí sola un sobreprecio.", "Existe un ensayo de la fórmula final con resultados favorables.", [], [], pl),
              _h("H2", "ALTERNATIVA", "COMPARABLES", "El mercado comparable vigente (cosméticos capilares premium equivalentes) fija un rango de precio por 100 ml del que %s puede quedar dentro o fuera; el rango no decide por sí solo." % n, "Menos de 3 comparables vigentes y equivalentes → no se puede fijar rango.",
                 ["competidor precio %s capilar premium mercado" % f for f in fm], ["competidor precio capilar premium mercado alfa"], pl)]
        for s in sus: hs.append(_h("H3", "ALTERNATIVA", "SUSTITUTO", "%s es un sustituto %s indirecto que condiciona la disposición a pagar, no un competidor cosmético equivalente." % (s["nombre"].capitalize(), "terapéutico" if s["tipo"] == "MEDICAMENTO" else ""), "Datos de uso/sustitución que lo desmientan.", ["%s precio medicamento alopecia sustituto" % s["nombre"]], ["%s precio alopecia medicamento sustituto" % s["nombre"]], pl))
        hs += [_h("H4", "ALTERNATIVA", "REGULATORIO", "La clasificación regulatoria depende de la presentación completa, la composición y las alegaciones (%s); una alegación de crecimiento puede cambiarla." % ", ".join(ficha.get("claims") or []), "Texto oficial aplicable al caso concreto.",
                 ["clasificacion cosmetico medicamento alegaciones regulatoria normativa", "alegaciones crecimiento capilar medicinales normativa blog"], ["clasificacion cosmetico medicamento alegaciones normativa"], pl),
               _h("H5", "ALTERNATIVA", "SENALES", "No se pueden inferir ventas reales a partir del BSR ni atribuir causalidad a correlaciones de BSR y precio.", "Fuente de calibración BSR→unidades con datos propios.", ["bsr ranking ventas demanda unidades metodo"], ["bsr ranking ventas demanda metodo"], pl)]
        return hs
    if pl == "SUPLEMENTO_ORAL":
        return [_h("S0", "AHT", "TESIS_INGREDIENTE", "La forma química de %s de %s (biodisponibilidad, tolerancia) sostiene un precio superior al magnesio básico." % (", ".join(ings), n), "Datos de biodisponibilidad comparada humana; sin ellos solo es una tesis de ingrediente.", ["%s biodisponibilidad humana ensayo" % i for i in ings], ["%s biodisponibilidad comparada limites" % i for i in ings], pl),
                _h("S1", "ALTERNATIVA", "DOSIS", "La dosis diaria aportada y los límites de ingesta determinan qué se puede alegar y cuántas unidades por día se recomiendan; el precio por envase no es comparable sin la dosis.", "Dosis diaria equivalente y alegaciones autorizadas coinciden con las de los comparables.", ["magnesio dosis diaria ingesta maxima complemento"], ["magnesio dosis diaria limite superior seguridad"], pl),
                _h("S2", "ALTERNATIVA", "COMPARABLES", "El precio por dosis diaria y por mg de magnesio elemental de los comparables vigentes y equivalentes ({}) fija el rango relevante; precio por envase o por 100 ml no es la métrica.".format(", ".join(fm)), "Menos de 3 comparables vigentes con la misma forma y dosis.", ["magnesio %s precio por dosis diaria" % f for f in fm], ["magnesio precio dosis diaria mercado"], pl),
                _h("S3", "ALTERNATIVA", "SUSTITUTO", "La demanda se reparte con sustitutos (%s) que fijan una referencia de coste diario mucho menor." % ", ".join(s["nombre"] for s in sus), "Datos de elección del consumidor que muestren que no sustituyen.", ["%s coste diario" % s["nombre"] for s in sus], ["magnesio sustitutos coste diario consumidor"], pl),
                _h("S4", "ALTERNATIVA", "REGULATORIO", "Como complemento alimenticio solo pueden usarse alegaciones de salud autorizadas (%s) y existen restricciones de marketplace para suplementos." % ", ".join(ficha.get("claims") or []), "Lista de alegaciones autorizadas y política vigente del marketplace.", ["alegaciones salud autorizadas magnesio complemento alimenticio", "amazon politica complementos alimenticios"], ["alegaciones salud magnesio no autorizadas"], pl),
                _h("S5", "ALTERNATIVA", "SENALES", "La demanda de magnesio es estacional y está dominada por reseñas y recompra; el BSR no permite inferir ventas ni la recompra.", "Serie propia de ventas/recompra.", ["magnesio demanda estacionalidad recompra"], ["magnesio demanda estacionalidad bsr"], pl)]
    return [_h("G0", "AHT", "TESIS_INGREDIENTE", "Las propiedades declaradas de %s están respaldadas por evidencia." % n, "Evidencia de la fórmula final.", ["%s evidencia eficacia" % n], ["%s evidencia limites" % n], pl),
            _h("G1", "ALTERNATIVA", "COMPARABLES", "Existen comparables vigentes y equivalentes que fijan un rango relevante.", "Menos de 3 comparables equivalentes.", ["competidor precio %s mercado" % n], ["competidor precio mercado"], pl),
            _h("G2", "ALTERNATIVA", "REGULATORIO", "La clasificación y las alegaciones de %s tienen restricciones aplicables." % n, "Texto oficial aplicable.", ["%s normativa alegaciones" % n], ["%s normativa limites" % n], pl)]


def coherencia(maestro, declarado, tol=0.005):
    """Comprueba el dato declarado contra la ficha maestra. Una discrepancia BLOQUEA la conclusión (no basta recalcular bien un dato erróneo)."""
    d = []
    if not maestro or maestro.get("volumen_ml") in (None, 0) or maestro.get("pvp") in (None, 0): d.append({"campo": "ficha_maestra", "detalle": "la ficha maestra no tiene volumen o PVP: no se puede validar el dato usado; requiere confirmación"})
    else:
        for c, m, x in (("volumen_ml", maestro["volumen_ml"], declarado.get("volumen_ml")), ("pvp", maestro["pvp"], declarado.get("precio"))):
            if x is None or abs(float(x) - float(m)) > tol: d.append({"campo": c, "maestro": m, "declarado": x, "detalle": "%s declarado (%s) ≠ ficha maestra (%s)" % (c, x, m)})
        p100m = maestro["pvp"] / maestro["volumen_ml"] * 100
        if declarado.get("precio") and declarado.get("volumen_ml") and abs(declarado["precio"] / declarado["volumen_ml"] * 100 - p100m) > 0.01: d.append({"campo": "precio_100ml", "maestro": round(p100m, 2), "declarado": round(declarado["precio"] / declarado["volumen_ml"] * 100, 2), "detalle": "precio normalizado distinto del de la ficha maestra"})
    return {"coherente": not d, "discrepancias": d, "maestro": maestro, "declarado": declarado}


def evaluar_evidencia(extractos, hipotesis):
    """Fase 3: puntúa cada hipótesis con evidencia favorable/contraria ponderada por calidad; no decide el precio."""
    out = []
    for h in hipotesis:
        fav = [x for x in extractos if x["hipotesis"] == h["id"] and x["efecto"] > 0 and x["tipo_dato"] != "HISTORICO"]; con = [x for x in extractos if x["hipotesis"] == h["id"] and x["efecto"] < 0]
        w = lambda x: RANGO_CAL.get(x["calidad"], 0) + 1; s = sum(w(x) for x in fav) - sum(w(x) for x in con)
        if h["tipo"] == "TESIS_INGREDIENTE": est = "PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE" if s >= 3 else ("DEBILITADA" if s <= -3 else "INDECISA")
        elif h["tipo"] == "TRASLADO": est = "INDECISA"
        else: est = "SOPORTADA" if s >= 3 else ("DEBILITADA" if s <= -3 else "INDECISA")
        out.append(dict(h, estado=est, puntuacion=s, favorables=[x["id"] for x in fav], desfavorables=[x["id"] for x in con]))
    tes = next((h for h in out if h["tipo"] == "TESIS_INGREDIENTE"), None); tr = next((h for h in out if h["tipo"] == "TRASLADO"), None)
    if tr: tr["estado"] = "SOPORTADA" if tes and tes["estado"] != "SOPORTADA" else "INDECISA"; tr["nota"] = "No se localizó ningún ensayo de la fórmula final (alcance: consultas del libro); es ausencia de evidencia localizada, no prueba de ausencia de efecto."
    return out


def analisis_economico(propio100, comparables, datos_internos, ficha):
    """Fase 4: solo hechos económicos; NO emite recomendación. Solo cuentan comparables vigentes y de categoría equivalente."""
    cats = set(ficha.get("categorias_comparables") or []); eq = [c for c in comparables if c["vigente"] and c["categoria"] in cats]; ex = [c for c in comparables if c not in eq]
    v = sorted(c["p100"] for c in eq); di = datos_internos or {}
    r = {"precio_propio_100": propio100, "n_equivalentes_vigentes": len(eq), "equivalentes": [c["nombre"] for c in eq], "excluidos": [{"nombre": c["nombre"], "motivo": ("histórico" if not c["vigente"] else "categoría no equivalente: %s" % c["categoria"])} for c in ex], "rango": [v[0], v[-1]] if v else None,
         "posicion": None if not v else ("dentro del rango" if v[0] <= propio100 <= v[-1] else ("por encima del rango" if propio100 > v[-1] else "por debajo del rango")), "datos_internos_completos": bool(di.get("ventas_dia") and di.get("margen_unitario"))}
    el = di.get("elasticidad"); r["respuesta_precio"] = bool(el and el.get("valor") is not None and el.get("n_obs", 0) >= 8 and el.get("fuente")); r["elasticidad"] = el if r["respuesta_precio"] else None
    return r


def recomendar(ev_tesis, econ, di, coherente, pvp):
    """Fase 5: recomendación. La posición frente al rango NUNCA basta para SUBIR/BAJAR: hace falta evidencia de respuesta del volumen al precio (elasticidad medida con n≥8 observaciones y fuente)."""
    if not coherente: return {"decision": "BLOQUEADO", "confianza": "BAJA", "motivo": "discrepancia con la ficha maestra: confirmar el dato antes de concluir"}
    falta = []
    if econ["n_equivalentes_vigentes"] < 3: falta.append("≥3 comparables vigentes y equivalentes (hoy %d)" % econ["n_equivalentes_vigentes"])
    if not econ["datos_internos_completos"]: falta.append("ventas y margen unitario internos")
    if falta: return {"decision": "NO_CONCLUIBLE", "confianza": "BAJA", "motivo": "Faltan " + " y ".join(falta) + "."}
    if not econ["respuesta_precio"]: return {"decision": "DISENAR_EXPERIMENTO", "confianza": "BAJA", "motivo": "El precio propio está %s (%.2f–%.2f €/100 ml), pero la posición frente a la competencia no indica en qué sentido mover el precio: falta medir cómo responde la demanda. Se recomienda diseñar un experimento, no cambiar el precio." % (econ["posicion"], econ["rango"][0], econ["rango"][1])}
    e = econ["elasticidad"]["valor"]; c = pvp - di["margen_unitario"]
    if e >= -1: return {"decision": "SUBIR", "confianza": "MEDIA", "motivo": "Demanda medida inelástica (e=%.2f): subir el precio aumenta el margen total; mover en pasos y reevaluar." % e, "optimo": None}
    popt = c * e / (1 + e); dif = popt / pvp - 1
    d = "MANTENER" if abs(dif) <= 0.10 else ("SUBIR" if dif > 0 else "BAJAR")
    return {"decision": d, "confianza": "MEDIA", "motivo": "Con elasticidad medida e=%.2f y coste variable %.2f €, el precio óptimo de margen es %.2f € (%+.0f %% vs actual)." % (e, c, popt, dif * 100), "optimo": round(popt, 2)}
