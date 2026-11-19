"""K4 · comparativa ejecutiva (ACTIVCORE + 5 competidores de referencia) en columnas, con filas comparativas. Cada celda lleva estado: OBSERVADO / MAQUETA (no verificado) / DECLARADO (ficha propia) / DERIVADO / ESTIMADO / SIN_DATO.
No se inventan imágenes, ventas, concentraciones ni claims: lo que no existe se muestra SIN DATO."""

FILAS = [("precio", "Precio (€)"), ("volumen", "Volumen (mL)"), ("precio_100ml", "Precio normalizado (€/100 mL)"), ("activos", "Activos"), ("dosis", "Dosis"), ("duracion", "Duración (días)"), ("coste_dia", "Coste por día (€)"),
         ("posicionamiento", "Posicionamiento"), ("evidencia", "Evidencia"), ("equivalencia", "Equivalencia K3 (estimada)"), ("ventajas", "Ventajas / diferencias")]


def c(texto, estado, nota=None): return {"texto": texto, "estado": estado, "nota": nota}
def eur(x): return ("%.2f" % x).replace(".", ",") + " €"


def _comp(r):
    a = r["automatic"]; inf = r.get("infografia") or {}; vig = r["price_class"] in ("ACTUAL", "RECIENTE") and r["price"] is not None
    ml = a.get("volumen_ml"); pm = inf.get("pvp_maqueta_eur")
    if vig: precio = c(eur(r["price"]), "OBSERVADO", "%s · %s" % (r["price_class"], str(r["price_as_of"])[:10])); p100 = c(eur(r["price_100ml"]), "OBSERVADO", r["price_class"])
    elif r["price"] is not None: precio = c(eur(r["price"]), "HISTORICO", "%s · solo referencia" % r["price_class"]); p100 = c(eur(r["price_100ml"]) if r["price_100ml"] is not None else "SIN DATO", "HISTORICO", "solo referencia, fuera de estadísticos")
    elif pm is not None: precio = c(eur(pm), "MAQUETA", "infografía de maqueta, NO verificado"); p100 = c(eur(pm / ml * 100) if ml else "SIN DATO", "MAQUETA", "derivado de la maqueta; fuera de estadísticos") if ml else c("SIN DATO", "SIN_DATO")
    else: precio = c("SIN DATO", "SIN_DATO"); p100 = c("SIN DATO", "SIN_DATO")
    act = ", ".join(a.get("activos") or []) or None
    return {"key": r["key"], "marca": r["brand"], "titulo": r["title"], "asin": r["asin"], "pais": r["country"], "segmento": r["segmento"], "codigo": r["codigo"], "origen": r["grupo_origen"],
            "celdas": {"precio": precio, "volumen": c("%g mL" % ml, "ESTIMADO", str(a.get("volumen_fuente") or "")) if ml else c("SIN DATO", "SIN_DATO"), "precio_100ml": p100,
                       "activos": c((act or "SIN DATO") + ((" · " + inf["concentracion"]) if inf.get("concentracion") else ""), "MAQUETA" if inf.get("concentracion") else ("ESTIMADO" if act else "SIN_DATO"), "por título/maqueta K3; no verificado" if act else None),
                       "dosis": c(inf["dosis"], "MAQUETA", "no verificado") if inf.get("dosis") else c("SIN DATO", "SIN_DATO"), "duracion": c(str(inf["duracion_dias"]), "MAQUETA") if inf.get("duracion_dias") else c("SIN DATO", "SIN_DATO"),
                       "coste_dia": c(eur(r["cost_day"]), "DERIVADO", "precio vigente / duración") if r.get("cost_day") is not None else c("SIN DATO", "SIN_DATO"),
                       "posicionamiento": c(inf["posicionamiento_maqueta"], "MAQUETA", "no verificado") if inf.get("posicionamiento_maqueta") else c("SIN DATO", "SIN_DATO"),
                       "evidencia": c("%s · %s" % (r.get("evidence_kind") or "n/d", "ASIN real (Keepa)" if r["asin"] else "referencia sin ASIN"), "OBSERVADO" if r["asin"] and r.get("evidence_kind") != "MAQUETA" else "MAQUETA"),
                       "equivalencia": c("%.1f/100 · confianza %s" % (r["equivalencia"], (r["confianza"] or {}).get("nivel", "n/d")), "ESTIMADO", "no es validación comercial independiente"), "ventajas": c("SIN DATO", "SIN_DATO")}, "_activos": set(a.get("activos") or []), "_p100": r["price_100ml"] if vig else None}


def ejecutivo(own, filas_sel, tiene_imagen):
    """own: K3Service.own(); filas_sel: [{'row': fila K3, 'sel': dict seleccion}]. tiene_imagen(asin|None)->dict resuelto."""
    f = own["ficha"]; cols = [_comp(x["row"]) for x in filas_sel]
    for col, x in zip(cols, filas_sel): col["seleccion"] = x["sel"]; col["imagen"] = tiene_imagen(col["asin"], False)
    mine = set(f["activos"]); otros = set().union(*[x["_activos"] for x in cols]) if cols else set(); excl = sorted(mine - otros)
    p100s = [x["_p100"] for x in cols if x["_p100"] is not None]; mp = own.get("pvp_100ml")
    vent = []
    if excl: vent.append("Activos presentes en ACTIVCORE y ausentes en los %d de referencia (según título/maqueta; no verificado): %s" % (len(cols), ", ".join(excl)))
    if mp and p100s:
        mas_caros = sum(1 for p in p100s if p > mp); vent.append("Precio/100 mL propuesto inferior a %d de %d referencias con precio vigente (PVP propuesto, no vigente en Amazon)" % (mas_caros, len(p100s)))
    elif mp: vent.append("Posición de precio NO EVALUABLE: ninguna referencia seleccionada tiene precio vigente")
    for col, x in zip(cols, filas_sel):
        dif = sorted(col["_activos"] - mine)
        col["celdas"]["ventajas"] = c(("Activos que ACTIVCORE no declara: " + ", ".join(dif)) if dif else "SIN DATO", "ESTIMADO" if dif else "SIN_DATO", "por título/maqueta K3" if dif else None)
        col.pop("_activos"); col.pop("_p100")
    propio = {"nombre": own["nombre"], "key": "ACTIVCORE", "imagen": tiene_imagen(None, True), "celdas": {
        "precio": c(eur(own["pvp"]) if own.get("pvp") else "SIN DATO", "DECLARADO", own["pvp_estado"]), "volumen": c("%g mL" % own["ml"], "DECLARADO", "ficha propia") if own.get("ml") else c("SIN DATO", "SIN_DATO"),
        "precio_100ml": c(eur(mp), "DERIVADO", "PVP propuesto / volumen") if mp else c("SIN DATO", "SIN_DATO"), "activos": c(", ".join(f["activos"]), "DECLARADO", "ficha interna; sin estudio clínico"),
        "dosis": c("%g mL/día" % f["dosis_ml_dia"], "DECLARADO", own["coste_dia_estado"]) if f.get("dosis_ml_dia") else c("SIN DATO", "SIN_DATO"),
        "duracion": c("%g" % (own["ml"] / f["dosis_ml_dia"]), "DERIVADO", "teórico: volumen / dosis") if f.get("dosis_ml_dia") and own.get("ml") else c("SIN DATO", "SIN_DATO"),
        "coste_dia": c(eur(own["coste_dia"]), "DERIVADO", own["coste_dia_estado"]) if own.get("coste_dia") else c("SIN DATO", "SIN_DATO"),
        "posicionamiento": c(f["posicionamiento"], "DECLARADO"), "evidencia": c(f["evidencia"], "DECLARADO"), "equivalencia": c("referencia (producto propio)", "DECLARADO"),
        "ventajas": c(" · ".join(vent) if vent else "SIN DATO", "DERIVADO" if vent else "SIN_DATO", "no son claims verificados")}}
    return {"filas": [{"id": k, "etiqueta": e} for k, e in FILAS], "propio": propio, "competidores": cols, "ventajas_lista": vent}
