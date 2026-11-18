"""K4 · Analista de precios: dictamen trazable de 5 tipos. Determinista. No inventa elasticidad, ventas ni precio.
Reglas: BSR≠ventas · histórico≠vigente · nunca PVP desde una mediana sola (intervalo = rango de mercado ∩ margen mínimo) · elasticidad solo observada (≥2 niveles de precio con ≥3 días) o rango SUPUESTO rotulado ·
sin ventas base no hay escenarios en unidades · confianza = la del input más débil. Umbrales editables en CFG (rotulados UMBRAL CONFIGURABLE)."""
from . import eu, k4_contracts as C

CFG = {"margen_min": 0.15, "ratio_bajo": 0.85, "ratio_alto": 1.15, "conv_baja": 0.05, "cobertura_min_dias": 14, "dias_ventas_min": 14, "elast_supuesta": (-2.0, -0.5), "paso": 0.5, "nota": "UMBRAL CONFIGURABLE (decisión AHT); no es un hecho de mercado"}
RANK = {"ALTA": 3, "MEDIA": 2, "BAJA": 1, "MUY_BAJA": 0}


def _min_conf(*cs):
    cs = [c for c in cs if c]; return min(cs, key=lambda c: RANK[c]) if cs else "MUY_BAJA"


def elasticidad(niveles):
    """Elasticidad de arco entre el nivel más bajo y el más alto observados. None si <2 niveles."""
    if len(niveles) < 2: return None
    n = sorted(niveles, key=lambda x: x["precio"]); a, b = n[0], n[-1]
    if a["precio"] == b["precio"] or a["uds_dia"] <= 0 or b["uds_dia"] <= 0: return None
    import math
    return round(math.log(b["uds_dia"] / a["uds_dia"]) / math.log(b["precio"] / a["precio"]), 2)


def dictamen(ctx, cfg=None):
    """ctx: producto, pais, entorno, own{pvp,ml,pvp_estado}, panel_premium (k3.panels['premium']) , costes (assumptions eu), kpis (Data.kpis), niveles (Data.niveles_precio), fecha."""
    cfg = dict(CFG, **(cfg or {})); pais = ctx["pais"]; own = ctx["own"]; pvp, ml = own.get("pvp"), own.get("ml"); fecha = ctx["fecha"]; ent = ctx.get("entorno", "PRODUCCION")
    kp = ctx["kpis"]; pan = ctx.get("panel_premium") or {}; st = pan.get("estadisticos")
    tr, faltan, just, riesgos = [], [], [], []
    # --- evidencia de mercado
    if st:
        tr.append({"input": "mediana premium vigente €/100 ml", "valor": st["mediana_100ml"], "n": st["n"], "estado": "OBSERVADO", "fuente": "K3 · precios ACTUAL/RECIENTE (≤30 d) de segmento premium", "fecha": fecha})
        just.append(C.afirmacion("HECHO", "Premium vigente: mediana %.2f €/100 ml (n=%d, rango %.2f–%.2f)." % (st["mediana_100ml"], st["n"], st["min_100ml"], st["max_100ml"]), ["K3 premium"]))
    else:
        faltan.append({"dato": "Precios vigentes del segmento premium (≥3)", "como": "Refrescar Keepa de pago con autorización o cargar precios documentados con fecha"})
        just.append(C.afirmacion("HECHO", pan.get("estadisticos_nota") or "Sin estadísticos premium vigentes (muestra insuficiente).", ["K3 premium"]))
    tr.append({"input": "equivalencia", "valor": "ESTIMADA", "estado": "ESTIMADO", "fuente": "K3 (título/marca/formato); no es validación comercial independiente", "fecha": fecha})
    # --- costes
    eco = eu.unit_economics(pvp, ctx["costes"], None) if pvp else {"complete": False, "missing": ["pvp"]}
    comp = bool(eco.get("complete")); hip = bool(eco.get("hypothetical"))
    if comp:
        tr.append({"input": "margen de contribución antes de ads", "valor": eco["margin_before_ads"], "estado": "ESTIMADO" if hip else "DERIVADO", "fuente": "eu.unit_economics con costes de la ficha", "fecha": fecha})
    else:
        faltan.append({"dato": "Costes obligatorios: " + ", ".join(eu.LABEL[k] for k in eco.get("missing", []) if k in eu.LABEL), "como": "Completar la ficha de costes (fuente, fecha, unidad, moneda) y validarla"})
    # --- ventas
    u = kp["unidades"]; conv = kp["conversion"]; ses = kp["sesiones"]; acos = kp["acos"]; stock = kp["stock"]
    ventas_ok = u["estado"] != "SIN_DATO"
    if ventas_ok: tr.append({"input": "unidades observadas", "valor": u["valor"], "estado": u["estado"], "fuente": u["fuente"], "fecha": u["fecha_dato"], "periodo": u["periodo"]})
    else: faltan.append({"dato": "Ventas, sesiones y conversión reales por producto/país", "como": "Importar informe de negocio de Seller Central (CSV) o activar SP-API tras autorización"})
    el = elasticidad(ctx.get("niveles") or []) if ventas_ok else None
    if el is None:
        faltan.append({"dato": "Elasticidad observada (≥2 niveles de precio con ≥3 días cada uno)", "como": "Experimento: 2 semanas a un precio y 2 semanas a otro, con presupuesto Ads y stock constantes; medir unidades/día y conversión"})
    conf_in = [("MEDIA" if st and st["n"] >= 3 else "MUY_BAJA"), ("MEDIA" if comp and not hip else ("BAJA" if comp else "MUY_BAJA")), (conv["confianza"] if ventas_ok else "MUY_BAJA")]
    base = {"precio_actual": {"pvp_propuesto": pvp, "estado": own.get("pvp_estado"), "nota": "El PVP es una PROPUESTA de AHT, no un precio vigente en Amazon"}, "producto": ctx["producto"], "pais": pais, "entorno": ent, "fuentes": sorted({t["fuente"] for t in tr}),
            "escenarios": [], "riesgos": riesgos, "trazabilidad": tr, "faltantes": faltan, "umbrales": cfg, "fecha": fecha, "margen_estimado": ({"antes_ads": eco.get("margin_before_ads"), "hipotetico": hip} if comp else None)}
    # --- Tipo 5: evidencia insuficiente
    insuf = (not st) or (not comp and not ventas_ok) or not pvp
    if insuf:
        riesgos.append("Fijar precio con esta evidencia sería adivinar.")
        base.update(tipo=5, justificacion=just + [C.afirmacion("HECHO", "Faltan: " + "; ".join(f["dato"] for f in faltan), [])], confianza=_min_conf(*conf_in), proxima_accion="Obtener los datos de «faltantes»; no modificar precio mientras tanto.",
                    criterion_revision=None, criterio_revision="Re-evaluar al cargar costes validados y ≥%d días de ventas" % cfg["dias_ventas_min"], intervalo_recomendado=None)
        return _fin(base)
    # --- tipo 4: otra causa
    causas = []
    if acos["estado"] != "SIN_DATO" and comp and eco.get("breakeven_acos_inc_vat") is not None and acos["valor"] > eco["breakeven_acos_inc_vat"]:
        causas.append("ACoS %.0f %% > ACoS de equilibrio %.0f %%: corregir campañas antes que precio" % (acos["valor"] * 100, eco["breakeven_acos_inc_vat"] * 100))
    if stock["estado"] != "SIN_DATO" and ventas_ok and u["valor"] and ctx.get("dias_periodo"):
        cob = stock["valor"] / (u["valor"] / ctx["dias_periodo"]) if u["valor"] > 0 else None
        if cob is not None and cob < cfg["cobertura_min_dias"]: causas.append("Cobertura de stock %.0f días < %d: reponer antes de tocar precio" % (cob, cfg["cobertura_min_dias"]))
    if conv["estado"] != "SIN_DATO" and conv["valor"] < cfg["conv_baja"] and ses["estado"] != "SIN_DATO":
        causas.append("Conversión %.1f %% baja con tráfico: revisar contenido/imágenes/reseñas antes de bajar precio" % (conv["valor"] * 100))
    own100 = pvp / ml * 100 if ml else None; ratio = own100 / st["mediana_100ml"] if own100 else None
    # intervalo = rango de mercado ∩ margen mínimo
    lo_m, hi_m = st["min_100ml"] * ml / 100, st["max_100ml"] * ml / 100; ok = []
    p = round(max(lo_m, pvp * 0.7), 2)
    while p <= min(hi_m, pvp * 1.5) + 1e-9:
        e = eu.unit_economics(p, ctx["costes"], None)
        if e.get("complete") and e["margin_before_ads"] >= cfg["margen_min"]: ok.append(p)
        p = round(p + cfg["paso"], 2)
    interval = {"min": ok[0], "max": ok[-1], "base": "rango premium vigente ∩ margen ≥ %d %%" % (cfg["margen_min"] * 100)} if ok else None
    base["intervalo_recomendado"] = interval; base["base_solo_mediana"] = False
    base["posicion_100ml"] = {"propio": round(own100, 2), "mediana": st["mediana_100ml"], "ratio": round(ratio, 2)}
    if causas:
        just.append(C.afirmacion("CAUSA_POSIBLE", "; ".join(causas), [k for k in ("acos", "stock", "conversion")]))
        base.update(tipo=4, justificacion=just, confianza=_min_conf(*conf_in), proxima_accion="Corregir: " + causas[0], criterio_revision="Re-evaluar precio tras corregir la causa y medir 14 días")
        return _fin(base)
    if not interval:
        riesgos.append("Ningún precio del rango premium alcanza el margen mínimo configurado.")
        just.append(C.afirmacion("HECHO", "Con los costes actuales ningún precio dentro del rango premium alcanza margen ≥ %d %%." % (cfg["margen_min"] * 100), ["costes"]))
        base.update(tipo=4, justificacion=just, confianza=_min_conf(*conf_in), proxima_accion="Revisar costes/Amazon fees antes de fijar precio (el problema no es el PVP)", criterio_revision="Tras actualizar costes validados")
        return _fin(base)
    # escenarios
    esc = []
    for p in sorted({interval["min"], round(pvp, 2) if interval["min"] <= pvp <= interval["max"] else interval["min"], interval["max"]}):
        e = eu.unit_economics(p, ctx["costes"], None); row = {"pvp": p, "margen_antes_ads": e.get("margin_before_ads"), "contribucion_ud": e.get("contribution_before_ads"), "etiqueta": e.get("label")}
        if ventas_ok and ctx.get("dias_periodo") and u["valor"] is not None:
            b = u["valor"] / ctx["dias_periodo"]; rg = [el] * 2 if el is not None else list(cfg["elast_supuesta"])
            row["uds_dia"] = sorted(round(b * (p / pvp) ** x, 2) for x in rg); row["uds_dia_estado"] = "OBSERVADA" if el is not None else "SUPUESTO (elasticidad %s a %s)" % cfg["elast_supuesta"]
        else: row["uds_dia"] = None; row["uds_dia_estado"] = "SIN DATOS: sin ventas base no se proyectan unidades"
        esc.append(row)
    base["escenarios"] = esc
    conv_baja = conv["estado"] != "SIN_DATO" and conv["valor"] < cfg["conv_baja"]
    if ratio <= cfg["ratio_bajo"] and ventas_ok:
        t = 1; just.append(C.afirmacion("HECHO", "Tu precio/100 ml es %.0f %% de la mediana premium." % (ratio * 100), ["K3"])); just.append(C.afirmacion("HIPOTESIS", "Hay margen de subida sin salir del rango premium; el efecto en unidades depende de una elasticidad " + ("observada" if el is not None else "NO observada"), []))
        acc = "Subir hasta %.2f € como ensayo controlado (máx. %.2f €) y medir 14 días" % (max(interval["min"], min(interval["max"], round(pvp * 1.1, 2))), interval["max"])
    elif ratio >= cfg["ratio_alto"] and ventas_ok and (conv_baja or el is not None):
        t = 3; just.append(C.afirmacion("HECHO", "Tu precio/100 ml es %.0f %% de la mediana premium." % (ratio * 100), ["K3"])); acc = "Ensayar una promoción o bajar hasta %.2f € (mínimo con margen ≥ %d %%)" % (interval["min"], cfg["margen_min"] * 100)
    else:
        t = 2; just.append(C.afirmacion("HECHO", "Precio/100 ml al %.0f %% de la mediana premium; margen estimado %.0f %%." % (ratio * 100, (eco["margin_before_ads"] or 0) * 100), ["K3", "costes"])); acc = "Mantener %.2f € y medir; revisar al cumplir %d días de ventas" % (pvp, cfg["dias_ventas_min"])
    if not ventas_ok: just.append(C.afirmacion("HECHO", "Sin ventas reales: el dictamen se limita a posición de mercado y margen.", [])); t = 2 if t != 2 else t; acc = "Mantener y obtener ventas reales: " + acc if t == 2 else acc
    if el is None: riesgos.append("Elasticidad no observada: cualquier proyección de unidades es SUPUESTO.")
    if hip: riesgos.append("Margen calculado con datos no verificados (HIPÓTESIS/histórico).")
    base.update(tipo=t, justificacion=just, confianza=_min_conf(*conf_in), proxima_accion=acc, criterio_revision="Revisar tras %d días con ≥%d días de ventas observadas y costes validados" % (14, cfg["dias_ventas_min"]))
    return _fin(base)


def _fin(d):
    d["tipo_nombre"] = C.TIPOS_DICTAMEN[d["tipo"]]
    if d["tipo"] in (1, 2, 3) and d["confianza"] == "MUY_BAJA": d["tipo"] = 5; d["tipo_nombre"] = C.TIPOS_DICTAMEN[5]; d["justificacion"].append(C.afirmacion("HECHO", "Confianza insuficiente para recomendar un cambio de precio.", []))
    d["errores_contrato"] = C.validar_dictamen(d)
    return d
