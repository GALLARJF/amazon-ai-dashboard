"""V1.1 — Motor económico comercial por SKU / lote / canal (auditoría comercial ACTIVCORE 25/11/2026). Funciones PURAS: sin red, sin escritura, sin IA, sin gasto.
Reglas: (1) todos los parámetros llevan fuente, fecha y estado (verificado | estimado | pendiente); NINGUNO se declara «verificado» sin evidencia oficial (por defecto ninguno lo está).
(2) Redondeo por partida a céntimos (ROUND_HALF_UP). (3) Se separan margen bruto, contribución, resultado operativo, neto, caja e IVA. (4) Sin doble imputación de regulación, muestras ni fijos.
(5) Lo que falta es «NO CALCULABLE» y se dice qué falta; no se inventan cifras. (6) Presupuestos y escalados son PROPUESTAS no autorizadas; ejecución humana externa."""
import math
from decimal import Decimal, ROUND_HALF_UP

FUENTE_AUDITORIA = "Auditoría comercial ACTIVCORE (José/ChatGPT), 25/11/2026"
FECHA = "2026-11-25"
ESTADOS = ("verificado", "estimado", "pendiente")
ORDEN = {"verificado": 0, "estimado": 1, "pendiente": 2}


def _p(v, unidad, estado="estimado", nota=None, **kw):
    d = {"v": v, "unidad": unidad, "fuente": FUENTE_AUDITORIA, "fecha": FECHA, "estado": estado}
    if nota: d["nota"] = nota
    d.update(kw); return d


# Parámetros base. «estimado» = dato comunicado por la auditoría sin evidencia oficial adjunta; «pendiente» = falta confirmar. Ninguno es «verificado».
PARAMS = {
    "pvp_bruto": _p(49.90, "€ con IVA", nota="PVP propuesto; decisión de José"),
    "iva": _p(0.21, "fracción", nota="tipo aplicable al producto POR CONFIRMAR con asesor fiscal"),
    "coste_lote_1": _p(12.55, "€/ud", incluye_regulacion=True, nota="incluye regulación (no sumar regulación aparte)"),
    "coste_lote_2": _p(8.99, "€/ud", "pendiente", incluye_regulacion=None, nota="lote 2 pendiente de confirmar; si incluye regulación está POR CONFIRMAR (PR6 y PR7 se contradicen): no se asume"),
    "comision_pct": _p(0.15, "fracción del PVP bruto", nota="escenario; porcentaje de Belleza y base (con IVA) POR CONFIRMAR en tarifas vigentes de Amazon.es"),
    "fba_tarifa": _p(3.81, "€/ud", "pendiente", nota="condicionada a peso y dimensiones reales; POR CONFIRMAR si incluye el recargo FBA 1,5 % vigente desde 17/04/2026. Fuente a contrastar: https://sell.amazon.es/precios (plan 39 € sin IVA; Belleza >10 € = 15 % sobre precio total con IVA; categoría del SKU pendiente)"),
    "fba_entrada": _p(0.30, "€/ud"), "fba_preparacion": _p(0.15, "€/ud"), "fba_almacen": _p(0.15, "€/ud"),
    "plan_mensual": _p(39.0, "€/mes", nota="se prorratea por ventas reales y horizonte; no es coste por unidad fijo"),
    "promociones": _p(0.50, "€/ud", nota="provisión; se anula si se aplica un descuento efectivo explícito (sin doble provisión)"),
    "incidencias": _p(0.50, "€/ud", nota="provisión"),
    "fbm_envio": _p(4.0, "€/ud", "pendiente", nota="provisional"), "fbm_preparacion": _p(1.0, "€/ud", "pendiente", nota="provisional"),
    "ventana_atribucion_dias": _p(7, "días", "pendiente", nota="ventana del informe de Ads a confirmar en el informe real"),
    "ventas_ads_base": _p("bruto", "bruto|neto", "pendiente", nota="si las ventas del informe de Ads incluyen IVA: POR CONFIRMAR en el informe real"),
}
LOTES = {1: "coste_lote_1", 2: "coste_lote_2"}
TACOS_ESCENARIOS = (0.0, 0.05, 0.10, 0.15, 0.25)
OBJETIVOS_CONTRIBUCION = (10.0, 15.0, 18.0, 20.0)   # € de contribución POR UNIDAD (no porcentajes); no garantizados
PILOTO = {"fba": 100, "reserva_flexible_aht": 100, "otros_canales_reserva": 350}   # propuesta, NO autorizada
TRAMOS_PRESUPUESTO = ({"tramo": "prueba", "dias": "1–10", "importe": 150}, {"tramo": "hasta día 30", "dias": "11–30", "importe": 350},
                      {"tramo": "días 31–60", "dias": "31–60", "importe": 750}, {"tramo": "días 61–90", "dias": "61–90", "importe": 1000})


def r2(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def mul(a, b):
    """Producto en Decimal (evita 49,9×0,15 = 7,48499… en coma flotante) y redondeo a céntimos."""
    return float((Decimal(str(a)) * Decimal(str(b))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _num(v, nombre, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not (lo <= v <= hi) or v != v:
        raise ValueError("%s: número entre %s y %s" % (nombre, lo, hi))
    return float(v)


def parametros(overrides=None):
    """Parámetros efectivos. `overrides` = {nombre: valor} (simulación; el estado pasa a «estimado» si estaba «verificado» no existe; se marca origen «simulado»)."""
    p = {k: dict(v) for k, v in PARAMS.items()}
    for k, v in (overrides or {}).items():
        if k not in p: raise ValueError("parámetro desconocido: " + str(k)[:40])
        if k == "ventas_ads_base":
            if v not in ("bruto", "neto"): raise ValueError("ventas_ads_base: bruto|neto")
        elif k in ("iva", "comision_pct"): _num(v, k, 0, 1)
        elif k == "pvp_bruto":
            if _num(v, k, 0, 100000) <= 0: raise ValueError("pvp_bruto: debe ser positivo")
        elif k == "ventana_atribucion_dias":
            if _num(v, k, 1, 365) != int(v): raise ValueError("ventana_atribucion_dias: entero")
        else: _num(v, k, 0, 100000)
        p[k]["v"] = v; p[k]["origen"] = "simulado por la petición (no es el valor de la auditoría)"
    return p


def _peor(estados):
    return max(estados, key=lambda e: ORDEN[e]) if estados else "pendiente"


def economia_unitaria(canal="FBA", lote=1, pvp=None, ventas=300, dias=90, tacos=None, descuento_pct=0.0, incentivos=None, regulacion_aparte=0.0,
                      muestras_coste_total=0.0, costes_fijos_periodo=None, overrides=None):
    """Economía por unidad, a PVP con IVA. Devuelve partidas redondeadas, niveles de margen separados y el estado más débil de los parámetros usados."""
    if canal not in ("FBA", "FBM"): raise ValueError("canal: FBA | FBM (web y farmacia: NO CALCULABLE, faltan parámetros)")
    if lote not in LOTES: raise ValueError("lote: 1 | 2")
    P = parametros(overrides)
    pvp = P["pvp_bruto"]["v"] if pvp is None else _num(pvp, "pvp", 0.5, 5000)
    ventas = _num(ventas, "ventas", 1, 1_000_000); dias = _num(dias, "dias", 1, 3650)
    if ventas != int(ventas) or dias != int(dias): raise ValueError("ventas y dias: números enteros")
    descuento_pct = _num(descuento_pct, "descuento_pct", 0, 0.9); regulacion_aparte = _num(regulacion_aparte, "regulacion_aparte", 0, 1000)
    muestras_coste_total = _num(muestras_coste_total, "muestras_coste_total", 0, 1e7)
    if tacos is not None: tacos = _num(tacos, "tacos", 0, 1)
    cl = P[LOTES[lote]]
    if lote == 2 and regulacion_aparte > 0 and cl.get("incluye_regulacion") is None:
        raise ValueError("lote 2: no se sabe si el coste incluye regulación (POR CONFIRMAR); confirmar antes de imputar regulación aparte")
    if cl.get("incluye_regulacion") and regulacion_aparte > 0:
        raise ValueError("doble imputación: el coste del lote ya incluye la regulación; no se puede añadir regulación aparte")
    pvp_ef = mul(pvp, 1 - descuento_pct); iva = P["iva"]["v"]; neto = r2(pvp_ef / (1 + iva))
    comision = mul(pvp_ef, P["comision_pct"]["v"]); plan = r2(Decimal(str(P["plan_mensual"]["v"])) * Decimal(str(dias)) / Decimal(30) / Decimal(str(ventas)))
    promo = 0.0 if descuento_pct > 0 else P["promociones"]["v"]
    usados = ["pvp_bruto", "iva", LOTES[lote], "comision_pct", "plan_mensual", "incidencias"] + ([] if descuento_pct > 0 else ["promociones"])
    lineas = {"coste_producto": r2(cl["v"]), "comision_referencia": comision, "plan_profesional_prorrateado": plan, "promociones": r2(promo), "incidencias": r2(P["incidencias"]["v"])}
    if canal == "FBA":
        lineas.update(fba_tarifa=r2(P["fba_tarifa"]["v"]), fba_entrada=r2(P["fba_entrada"]["v"]), fba_preparacion=r2(P["fba_preparacion"]["v"]), fba_almacen=r2(P["fba_almacen"]["v"]))
        usados += ["fba_tarifa", "fba_entrada", "fba_preparacion", "fba_almacen"]
    else:
        lineas.update(fbm_envio=r2(P["fbm_envio"]["v"]), fbm_preparacion=r2(P["fbm_preparacion"]["v"])); usados += ["fbm_envio", "fbm_preparacion"]
    if regulacion_aparte: lineas["regulacion_aparte"] = r2(regulacion_aparte)
    total_variables = r2(sum(v for k, v in lineas.items() if k != "coste_producto"))
    contrib = r2(neto - lineas["coste_producto"] - total_variables)
    res = {"canal": canal, "lote": lote, "pvp_bruto": pvp_ef, "descuento_efectivo_pct": descuento_pct, "ventas_horizonte": ventas, "horizonte_dias": dias, "precio_neto_sin_iva": neto,
           "iva_repercutido_ud": r2(pvp_ef - neto), "partidas": lineas,
           "margen_bruto_ud": r2(neto - lineas["coste_producto"]), "margen_bruto_pct_neto": round((neto - lineas["coste_producto"]) / neto, 4) if neto else None,
           "contribucion_antes_ads_ud": contrib, "contribucion_antes_ads_pct_neto": round(contrib / neto, 4) if neto else None,
           "estado_parametros": _peor([P[k]["estado"] for k in usados]), "parametros_usados": {k: {x: P[k][x] for x in ("v", "unidad", "fuente", "fecha", "estado")} for k in usados},
           "niveles": {"margen_bruto": "neto − coste del producto", "contribucion": "neto − coste − comisión − logística − plan prorrateado − provisiones (antes de Ads)",
                       "resultado_operativo": "contribución tras Ads − costes fijos del periodo (solo si se informan)", "neto": "NO CALCULABLE: exige impuesto sobre beneficios y costes de estructura",
                       "caja": "ver tesorería del simulador (inversión, cobros, IVA aparte)", "iva": "IVA repercutido por unidad, aparte de todo margen"}}
    if tacos is not None:
        ads = mul(tacos, neto)   # denominador EXPLÍCITO de TACoS: ventas totales netas (sin IVA) del periodo
        res.update(tacos=tacos, tacos_denominador="ventas totales netas sin IVA", ads_ud=ads, contribucion_tras_ads_ud=r2(contrib - ads), contribucion_tras_ads_pct_neto=round((contrib - ads) / neto, 4) if neto else None)
    fijos = None
    if costes_fijos_periodo is not None:
        fijos = _num(costes_fijos_periodo, "costes_fijos_periodo", 0, 1e7)
        base = res.get("contribucion_tras_ads_ud", contrib)
        res["resultado_operativo_periodo"] = r2(base * ventas - fijos - (muestras_coste_total or 0))
        res["resultado_operativo_base"] = "contribución tras Ads" if "contribucion_tras_ads_ud" in res else "contribución ANTES de Ads (Ads no informado: no se supone 0 € de Ads real)"
        res["resultado_operativo_nota"] = "costes fijos informados explícitamente y muestras restadas UNA vez; el plan profesional ya está prorrateado en la contribución y NO debe repetirse aquí"
    else:
        res["resultado_operativo_periodo"] = None; res["resultado_operativo_nota"] = "NO CALCULABLE: costes fijos del periodo no informados (sin doble imputación del plan profesional)"
    muestras = r2(muestras_coste_total) if muestras_coste_total else 0.0
    res["contribucion_total_periodo"] = r2(res.get("contribucion_tras_ads_ud", contrib) * ventas - muestras)
    res["muestras_coste_total"] = muestras; res["muestras_nota"] = "se resta UNA vez del total del periodo; no se reparte en la contribución unitaria"
    # Incentivos: confirmados y simulados NUNCA se mezclan
    conf = sim = 0.0
    for it in (incentivos or []):
        imp = _num(it.get("importe_ud"), "incentivo.importe_ud", 0, 1000)
        if it.get("estado") not in ("confirmado", "simulado"): raise ValueError("incentivo.estado: confirmado | simulado")
        if it["estado"] == "confirmado": conf += imp
        else: sim += imp
    base_c = res.get("contribucion_tras_ads_ud", contrib)
    res["incentivos"] = {"por_defecto": 0.0, "confirmados_ud": r2(conf), "simulados_ud": r2(sim), "contribucion_con_confirmados": r2(base_c + conf),
                         "contribucion_con_simulados": r2(base_c + conf + sim) if sim else None,
                         "nota": "incentivos temporales: cero por defecto; elegibilidad y compatibilidad pendientes; los simulados no son dinero cobrado"}
    res["devoluciones"] = "provisión de devoluciones PENDIENTE: no incluida (requiere tasa real y coste por devolución)"
    return res


def objetivos(eco, lista=OBJETIVOS_CONTRIBUCION):
    """CPA máximo y presupuesto residual de Ads para alcanzar cada objetivo de contribución en € POR UNIDAD (10, 15, 18, 20 €). No garantizado."""
    neto, c0, ventas = eco["precio_neto_sin_iva"], eco["contribucion_antes_ads_ud"], eco["ventas_horizonte"]
    out = []
    for o in lista:
        o = _num(o, "objetivo (€/ud)", 0, 1000); cpa = r2(c0 - o)
        out.append({"objetivo_contribucion_ud": o, "unidad_objetivo": "€/ud", "cpa_maximo_ud": cpa if cpa >= 0 else None, "tacos_maximo": round(cpa / neto, 4) if cpa >= 0 and neto else None,
                    "presupuesto_residual_ads": r2(cpa * ventas) if cpa >= 0 else None, "estado": "alcanzable con estos parámetros" if cpa >= 0 else "INALCANZABLE con estos parámetros (la contribución antes de Ads ya queda por debajo del objetivo)",
                    "garantia": "NO garantizado: depende de parámetros estimados/pendientes"})
    return out


def inventario(enviadas, vine=0, vendidas=0, devueltas=0, devueltas_reintegradas=0):
    """Separa unidades enviadas, Vine, vendidas, devueltas y stock. Stock = enviadas − Vine − vendidas + devueltas reintegradas al stock."""
    vals = {k: int(_num(v, k, 0, 10_000_000)) for k, v in (("enviadas", enviadas), ("vine", vine), ("vendidas", vendidas), ("devueltas", devueltas), ("devueltas_reintegradas", devueltas_reintegradas))}
    if vals["devueltas"] > vals["vendidas"]: raise ValueError("devueltas no puede superar a vendidas")
    if vals["devueltas_reintegradas"] > vals["devueltas"]: raise ValueError("devueltas_reintegradas no puede superar a devueltas")
    stock = vals["enviadas"] - vals["vine"] - vals["vendidas"] + vals["devueltas_reintegradas"]
    if stock < 0: raise ValueError("stock negativo: enviadas insuficientes para Vine + vendidas")
    return {**vals, "vendidas_netas": vals["vendidas"] - vals["devueltas"], "stock": stock}


def simulador(canales=("FBA", "FBM"), lotes=(1, 2), tacos_lista=TACOS_ESCENARIOS, ventas_lista=(100, 200, 300), pvps=None, dias=90, overrides=None):
    """Rejilla de sensibilidad (canal × lote × TACoS × ventas × precio). Farmacia/web: NO CALCULABLE. Máx. 600 celdas."""
    P = parametros(overrides); base = P["pvp_bruto"]["v"]; pvps = tuple(pvps) if pvps else (r2(base - 5), base, r2(base + 5))
    n = len(canales) * len(lotes) * len(tacos_lista) * len(ventas_lista) * len(pvps)
    if n > 600: raise ValueError("rejilla demasiado grande (%d > 600 celdas)" % n)
    celdas = []
    for c in canales:
        for l in lotes:
            for v in ventas_lista:
                for pv in pvps:
                    for t in tacos_lista:
                        e = economia_unitaria(c, l, pv, v, dias, t, overrides=overrides)
                        celdas.append({"canal": c, "lote": l, "ventas": v, "pvp": pv, "tacos": t, "contribucion_antes_ads_ud": e["contribucion_antes_ads_ud"], "contribucion_tras_ads_ud": e["contribucion_tras_ads_ud"],
                                       "contribucion_tras_ads_pct_neto": e["contribucion_tras_ads_pct_neto"], "estado_parametros": e["estado_parametros"]})
    return {"celdas": celdas, "n": len(celdas), "canales_no_calculables": {"farmacia": "NO CALCULABLE: faltan margen del distribuidor, logística y condiciones", "web": "NO CALCULABLE: faltan pasarela de pago, envío y captación propios"},
            "tacos_denominador": "ventas totales netas sin IVA", "aviso": "Sensibilidad ilustrativa con parámetros estimados/pendientes; no es previsión ni garantía."}


def tesoreria(unidades_compradas, lote=1, ventas_cobradas=0, tacos=0.0, canal="FBA", pvp=None, dias=90, overrides=None):
    """Exposición de caja simplificada (sin plazos de pago ni de liquidación, que son POR CONFIRMAR). IVA aparte."""
    u = int(_num(unidades_compradas, "unidades_compradas", 1, 10_000_000)); v = int(_num(ventas_cobradas, "ventas_cobradas", 0, u))
    e = economia_unitaria(canal, lote, pvp, max(v, 1), dias, tacos, overrides=overrides); p = e["partidas"]
    inversion = r2(u * p["coste_producto"]); ads = mul(tacos * v, e["precio_neto_sin_iva"])
    cobros_netos = r2(v * (e["precio_neto_sin_iva"] - sum(x for k, x in p.items() if k != "coste_producto")))
    return {"unidades_compradas": u, "ventas_cobradas": v, "inversion_producto": inversion, "ads_periodo": ads, "cobros_netos_tras_costes_amazon": cobros_netos,
            "caja_acumulada": r2(cobros_netos - inversion - ads), "iva_repercutido_aparte": r2(v * e["iva_repercutido_ud"]),
            "nota": "caja simplificada: sin plazo de pago al proveedor ni calendario de liquidaciones de Amazon (POR CONFIRMAR); el IVA se liquida aparte y no es margen"}


def piloto(ventas=100, dias=90, overrides=None):
    """Piloto PROPUESTO (no autorizado): 100 FBA / 100 reserva flexible AHT / 350 otros canales o reserva. No aplica el presupuesto de 300 unidades a 100."""
    ventas = int(_num(ventas, "ventas", 1, PILOTO["fba"]))
    eco = economia_unitaria("FBA", 1, None, ventas, dias, None, overrides=overrides)
    c = eco["contribucion_antes_ads_ud"]
    ads_piloto = 150
    return {"estado": "PROPUESTO · NO AUTORIZADO · no se autoriza ningún envío", "reparto_unidades": dict(PILOTO), "total_unidades": sum(PILOTO.values()),
            "separacion_unidades": inventario(PILOTO["fba"], 0, ventas, 0, 0), "economia_fba": eco, "objetivos": objetivos(eco),
            "ads_piloto": {"importe": ads_piloto, "dias": 10, "ventas_para_cubrir_ads": math.ceil(ads_piloto / c) if c > 0 else None,
                           "lectura": "unidades que hay que vender solo para igualar el gasto del piloto con la contribución antes de Ads; no es un objetivo ni una previsión"},
            "plan_prorrateado": {"ventas_100": economia_unitaria("FBA", 1, None, 100, 90, None, overrides=overrides)["partidas"]["plan_profesional_prorrateado"],
                                 "ventas_300": economia_unitaria("FBA", 1, None, 300, 90, None, overrides=overrides)["partidas"]["plan_profesional_prorrateado"]},
            "regla_presupuesto": "no aplicar automáticamente el presupuesto de 300 unidades a 100; ampliar solo con evidencia y aprobación humana"}


def presupuesto_escalonado():
    acum = 0; out = []
    for t in TRAMOS_PRESUPUESTO:
        acum += t["importe"]; out.append({**t, "acumulado": acum, "estado": "PROPUESTO · NO AUTORIZADO", "condicion": "evidencia del tramo anterior + aprobación humana expresa; ejecución manual fuera de la herramienta"})
    return {"tramos": out, "total": acum, "autorizado": False}


def evaluar_escalado(indice_tramo, aprobacion_humana=False, evidencia=None):
    """Un tramo solo puede pasar a «listo para decidir» con evidencia (contribución tras Ads ≥ 0 y términos con ventas) Y aprobación humana. Nunca ejecuta nada."""
    tr = presupuesto_escalonado()["tramos"]
    if not isinstance(indice_tramo, int) or not 0 <= indice_tramo < len(tr): raise ValueError("tramo inexistente")
    ev = evidencia or {}
    faltan = [k for k in ("contribucion_tras_ads_ud", "ventas_atribuidas") if ev.get(k) is None]
    ok_ev = not faltan and ev["contribucion_tras_ads_ud"] >= 0 and ev["ventas_atribuidas"] > 0
    if indice_tramo == 0: ok_ev = True
    return {"tramo": tr[indice_tramo]["tramo"], "evidencia_suficiente": bool(ok_ev), "faltan": faltan, "aprobacion_humana": bool(aprobacion_humana),
            "decision": "LISTO PARA DECIDIR POR UNA PERSONA" if (ok_ev and aprobacion_humana) else "BLOQUEADO", "ejecuta_algo": False}


def alertas(gasto_acumulado=None, presupuesto_tramo=None, contribucion_tras_ads_ud=None, stock=None, demanda_diaria=None, plazo_reposicion_dias=None,
            terminos=None, dias_desde_ultimo_clic=None, ventana_atribucion_dias=None):
    out = []; add = lambda c, sev, msg, ev: out.append({"codigo": c, "severidad": sev, "mensaje": msg, "evidencia": ev})
    if gasto_acumulado is not None and presupuesto_tramo:
        if gasto_acumulado > presupuesto_tramo: add("GASTO_SUPERA_TRAMO", "alta", "El gasto supera el tramo propuesto", {"gasto": gasto_acumulado, "tramo": presupuesto_tramo})
        elif gasto_acumulado >= 0.8 * presupuesto_tramo: add("GASTO_80_PCT", "media", "El gasto alcanzó el 80 % del tramo", {"gasto": gasto_acumulado, "tramo": presupuesto_tramo})
    if contribucion_tras_ads_ud is not None and contribucion_tras_ads_ud < 0:
        add("CONTRIBUCION_NEGATIVA", "alta", "La contribución tras Ads es negativa: cada venta pierde dinero", {"contribucion_tras_ads_ud": contribucion_tras_ads_ud})
    if None not in (stock, demanda_diaria, plazo_reposicion_dias) and demanda_diaria > 0:
        cobertura = stock / demanda_diaria
        if cobertura < plazo_reposicion_dias: add("STOCK_BAJO_PARA_REPOSICION", "alta", "La cobertura de stock es menor que el plazo de reposición", {"cobertura_dias": round(cobertura, 1), "plazo_reposicion_dias": plazo_reposicion_dias})
    for t in (terminos or []):
        if t.get("ventas", 0) == 0 and t.get("clics", 0) > 0:
            if None in (dias_desde_ultimo_clic, ventana_atribucion_dias) or dias_desde_ultimo_clic < ventana_atribucion_dias:
                add("TERMINO_SIN_VENTAS_VENTANA_ABIERTA", "info", "Término sin ventas, pero la ventana de atribución puede seguir abierta: no concluir", {"termino": t.get("termino"), "clics": t.get("clics")})
            else:
                add("TERMINO_SIN_VENTAS_TRAS_VENTANA", "media", "Término con clics y sin ventas tras la ventana de atribución", {"termino": t.get("termino"), "clics": t.get("clics"), "gasto": t.get("gasto")})
    return out


CHECKLIST = (
    ("Seller verificado (verificación facial de Carlos, Nota Informativa)", "Seller", "PENDIENTE", "launch-control checklist §Seller"),
    ("Marca ACTIVCORE: disponibilidad y registro; Brand Registry", "Marca", "POR CONFIRMAR", "launch-control PAQUETE2_LISTING"),
    ("Incentivos temporales: elegibilidad y compatibilidad", "Incentivos", "POR CONFIRMAR", "modelo: cero por defecto"),
    ("Regulación: INCI, CPSR/PIF/CPNP, Persona Responsable (Klein)", "Regulación", "PENDIENTE", "SOLICITUD_CONSOLIDADA_KLEIN"),
    ("Listing sin marcadores ni claims condicionados", "Listing", "BORRADOR", "PAQUETE2_LISTING_KEYWORDS"),
    ("FBA: peso, medidas, líquidos, caducidad/PAO, GTIN, trazabilidad", "FBA", "NO DISPONIBLE", "PROPUESTA_FBA_550_UNIDADES"),
    ("Vine: elegibilidad y unidades reservadas", "Vine", "POR CONFIRMAR", "inventario separa Vine"),
    ("Contenidos: imágenes, A+, vídeo (concepto sin elegir)", "Contenidos", "PENDIENTE", "PAQUETE2_CONCEPTOS_Y_MATRIZ"),
    ("Coste lote 2 (8,99 €) confirmado", "Costes", "PENDIENTE", "parámetro coste_lote_2"),
    ("Tarifa FBA 3,81 € verificada con peso/medidas reales", "Costes", "PENDIENTE", "parámetro fba_tarifa"),
    ("Presupuesto Ads escalonado 150+350+750+1000: aprobación humana por tramo", "Ads", "NO AUTORIZADO", "presupuesto_escalonado"),
)


def checklist():
    return [{"item": a, "area": b, "estado": c, "referencia": d} for a, b, c, d in CHECKLIST]
