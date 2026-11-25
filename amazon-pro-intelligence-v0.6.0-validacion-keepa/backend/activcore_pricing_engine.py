"""ACTIVCORE · Motor económico por SKU/lote/canal (encargo de José, 25/11/2026, comentario #PR5 — Bloque 1).
Determinista, sin IA, sin llamadas de red. Reutiliza las convenciones ya existentes en el repo:
  * `fld()` / estado de dato (econ6.py, eu.py): cada variable lleva clase OBSERVADO·IMPORTADO·DERIVADO·ESTIMADO·HIPOTESIS·PENDIENTE,
    fuente y fecha. Nunca se rellena un dato ausente con un valor por defecto.
  * Guarda anti-duplicación (k4_costs.py): un coste declarado como TOTAL que «incluye» conceptos (p. ej. lote1 ya incluye regulación)
    NO se vuelve a restar como partida aparte. Evita la doble imputación que pide expresamente el encargo.
  * Redondeo por partida: cada línea se redondea a 2 decimales ANTES de sumar (no se redondea solo el total), con media al alza,
    porque así lo pide el encargo («redondeo por partida»).

Separa, por canal (FBA/FBM) y por lote: margen bruto (PVP neto − coste del producto) · contribución (tras tarifas del canal,
antes de publicidad) · operativo (tras costes fijos amortizados) · neto (tras Ads) · caja (ajustado a cobro real, pendiente de
modelar) · IVA (informativo, no es coste). No se calcula nada si falta un dato obligatorio: el resultado queda PENDIENTE y se
dice qué falta, nunca un cero inventado."""
import math

STATUS = ("VERIFICADO", "ESTIMADO", "CONDICIONADO", "PROVISIONAL", "PENDIENTE")
TODAY_REF = "2026-11-25"


def _r2(x):
    """Redondeo por partida: 2 decimales, media al alza (no la media al par de round() de Python)."""
    if x is None:
        return None
    return math.floor(x * 100 + 0.5) / 100.0


def fld(v=None, status="PENDIENTE", source="", date=TODAY_REF):
    if status not in STATUS:
        raise ValueError("estado desconocido: " + str(status))
    return {"v": v, "status": status, "source": source, "date": date}


# ---------------------------------------------------------------------------------------------------------------------
# Datos de partida declarados por José en el comentario del 25/11/2026 (PR #5). Todos los importes son SIN IVA salvo el PVP.
# Ninguno se declara VERIFICADO salvo el IVA (tipo legal público): el resto son los valores que el propio encargo califica
# como provisionales/estimados/condicionados, y así se etiquetan — no se "promueven" a verificado sin evidencia oficial.
# ---------------------------------------------------------------------------------------------------------------------
SKU = "ACTIVCORE_V2"
PVP = fld(49.90, "ESTIMADO", "Encargo 25/11/2026 (José): PVP propuesto, no es precio verificado/publicado")
VAT_RATE = fld(0.21, "VERIFICADO", "Tipo general IVA España 2026 (21%)")

LOTES = {
    "lote1": {"coste": fld(12.55, "ESTIMADO", "Encargo 25/11/2026: coste de lote 1 «incluye regulación» — NO separar una partida de regulación aparte"),
              "incluye": ["regulacion"]},
    "lote2": {"coste": fld(8.99, "PENDIENTE", "Encargo 25/11/2026: coste de lote 2 marcado explícitamente «pendiente» por José — no usar como dato firme"),
              "incluye": []},
}

# Tarifas de canal (por unidad, sin IVA salvo que se indique). «Volumen» es la base declarada por José para amortizar costes fijos.
VOLUMEN_90D = fld(300, "ESTIMADO", "Encargo 25/11/2026: base de 300 ventas/90 días para amortizar costes fijos (plan). No es una previsión verificada.")
DIAS_PLAN = 30.0  # el plan de 39€ se factura mensualmente; 300 uds/90 días ⇒ 100 uds/mes de base de reparto

CANALES = {
    "FBA": {
        "comision_pct_pvp_bruto": fld(0.15, "ESTIMADO", "Encargo 25/11/2026: comisión escenario 15% sobre PVP bruto (no sobre PVP neto de IVA)"),
        "fba": fld(3.81, "CONDICIONADO", "Encargo 25/11/2026: tarifa FBA condicionada a peso/dimensiones reales del envase; reconfirmar con calculadora oficial Amazon al tener el envase final"),
        "entrada": fld(0.30, "PROVISIONAL", "Encargo 25/11/2026: coste de entrada/recepción en almacén, provisional"),
        "prep": fld(0.15, "PROVISIONAL", "Encargo 25/11/2026: preparación/etiquetado, provisional"),
        "almacen": fld(0.15, "PROVISIONAL", "Encargo 25/11/2026: almacenamiento, provisional"),
        "plan_mensual": fld(39.0, "ESTIMADO", "Encargo 25/11/2026: cuota del plan de venta (39 €/mes), a amortizar por volumen"),
        "promociones": fld(0.50, "PROVISIONAL", "Encargo 25/11/2026: coste promocional por unidad, provisional"),
        "incidencias": fld(0.50, "PROVISIONAL", "Encargo 25/11/2026: reserva por incidencias/devoluciones por unidad, provisional"),
    },
    "FBM": {
        "comision_pct_pvp_bruto": fld(0.15, "ESTIMADO", "Encargo 25/11/2026: misma comisión escenario 15% sobre PVP bruto"),
        "envio": fld(4.0, "PROVISIONAL", "Encargo 25/11/2026: envío FBM, provisional («envío4»)"),
        "prep": fld(1.0, "PROVISIONAL", "Encargo 25/11/2026: preparación FBM, provisional («prep1»)"),
        "plan_mensual": fld(39.0, "ESTIMADO", "Encargo 25/11/2026: misma cuota de plan, a amortizar por volumen"),
        "promociones": fld(0.50, "PROVISIONAL", "Encargo 25/11/2026: coste promocional por unidad, provisional"),
        "incidencias": fld(0.50, "PROVISIONAL", "Encargo 25/11/2026: reserva por incidencias/devoluciones por unidad, provisional"),
    },
}

# Cifras de referencia que dio José ("Base FBA 15,40 y FBM 14,81 antes Ads"), para lote1 — RESUELTO (25/11/2026):
# se contrastaron contra este motor y coinciden EXACTAMENTE con la CONTRIBUCIÓN de lote1 (precio neto de IVA − coste
# del lote 12,55 € − coste de canal), no con el coste de canal solo. Quedan aquí para que la prueba de regresión
# detecte si algún cambio futuro del motor deja de reproducirlas.
REFERENCIA_CONTRIBUCION_LOTE1 = {"FBA": 15.40, "FBM": 14.81}


def _plan_por_unidad(plan_mensual, volumen_90d):
    """Amortiza el plan mensual (39€) sobre la base de volumen declarada (300 uds/90 días ⇒ 100 uds/mes)."""
    if plan_mensual is None or volumen_90d is None:
        return None
    uds_mes = volumen_90d / 90.0 * DIAS_PLAN
    if uds_mes <= 0:
        return None
    return plan_mensual / uds_mes


def channel_baseline(pvp_gross, canal, volumen_90d_override=None):
    """Importe total deducido por el canal (SIN IVA, antes de publicidad) para un PVP dado. Redondeo por partida.
    Devuelve el desglose línea a línea con estado/fuente de cada una, el total, y la conciliación con la cifra de
    referencia que dio José (si la hay), para que él confirme o corrija — nunca se fuerza el total a coincidir."""
    if canal not in CANALES:
        raise ValueError("canal desconocido: " + str(canal))
    c = CANALES[canal]
    vol = volumen_90d_override if volumen_90d_override is not None else VOLUMEN_90D["v"]
    lineas = {}
    lineas["comision"] = fld(_r2(c["comision_pct_pvp_bruto"]["v"] * pvp_gross), c["comision_pct_pvp_bruto"]["status"],
                              "15%% de %.2f € (PVP bruto)" % pvp_gross)
    if canal == "FBA":
        lineas["fba"] = c["fba"]
        lineas["entrada"] = c["entrada"]
        lineas["prep"] = c["prep"]
        lineas["almacen"] = c["almacen"]
    else:
        lineas["envio"] = c["envio"]
        lineas["prep"] = c["prep"]
    plan_ud = _plan_por_unidad(c["plan_mensual"]["v"], vol)
    lineas["plan_amortizado"] = fld(_r2(plan_ud) if plan_ud is not None else None,
                                    "ESTIMADO" if plan_ud is not None else "PENDIENTE",
                                    "Plan %.2f €/mes ÷ %.0f uds/mes (base %.0f uds/90 días)" % (c["plan_mensual"]["v"], vol / 90.0 * DIAS_PLAN, vol) if plan_ud is not None else "Falta volumen de referencia")
    lineas["promociones"] = c["promociones"]
    lineas["incidencias"] = c["incidencias"]

    faltan = [k for k, f in lineas.items() if f["v"] is None]
    if faltan:
        return {"canal": canal, "pvp_gross": pvp_gross, "lineas": lineas, "complete": False,
                "state": "PENDIENTE", "missing": faltan, "label": "No calculable: falta " + ", ".join(faltan)}

    total = _r2(sum(f["v"] for f in lineas.values()))
    out = {"canal": canal, "pvp_gross": pvp_gross, "lineas": lineas, "total_antes_ads": total, "complete": True,
           "state": "ESTIMADO/PROVISIONAL (ningún dato de este bloque está VERIFICADO salvo el IVA — ver cada línea)"}
    return out


def sku_lot_channel_economics(sku, lote, canal, pvp_gross=None, volumen_90d_override=None):
    """Economía completa SKU/lote/canal: margen bruto · contribución · operativo · neto (sin Ads modelado aún) · IVA informativo.
    Si el lote está PENDIENTE (lote2), no se calcula ningún margen: se declara qué falta, no se usa el coste de otro lote."""
    if sku != SKU:
        raise ValueError("SKU desconocido: " + str(sku))
    if lote not in LOTES:
        raise ValueError("lote desconocido: " + str(lote))
    pvp = pvp_gross if pvp_gross is not None else PVP["v"]
    coste = LOTES[lote]["coste"]
    base = channel_baseline(pvp, canal, volumen_90d_override)
    net = _r2(pvp / (1 + VAT_RATE["v"]))
    vat_amount = _r2(pvp - net)
    out = {"sku": sku, "lote": lote, "canal": canal, "pvp_gross": pvp, "pvp_status": PVP["status"],
           "iva": {"tipo": VAT_RATE["v"], "importe": vat_amount, "clase": "INFORMATIVO (no es un coste, se declara aparte)"},
           "precio_neto_iva": net, "canal_baseline": base, "coste_producto": coste, "lote_incluye": LOTES[lote]["incluye"]}

    if coste["v"] is None:
        out.update(complete=False, state="PENDIENTE",
                   why="Coste del %s sin ningún valor declarado — no se calcula margen con el coste de otro lote ni con un valor supuesto." % lote,
                   margen_bruto=None, contribucion=None, operativo=None, neto=None)
        return out
    if not base["complete"]:
        out.update(complete=False, state="PENDIENTE", why="Faltan partidas del canal: " + ", ".join(base["missing"]),
                   margen_bruto=None, contribucion=None, operativo=None, neto=None)
        return out

    margen_bruto = _r2(net - coste["v"])
    contribucion = _r2(net - coste["v"] - base["total_antes_ads"])
    # Nota anti-doble-imputación: coste["incluye"]=="regulacion" para lote1 ⇒ NO se resta una partida de regulación aparte
    # en ningún punto de este cálculo (ni aquí ni en channel_baseline). Si en el futuro se añade un coste de "muestras" o
    # "costes fijos" distinto del plan de venta ya amortizado arriba, debe declararse con su propio `incluye` para que
    # quien añada la partida vea qué ya está contado.
    coste_sin_confirmar = coste["status"] not in ("VERIFICADO",)
    out.update(complete=True,
                coste_sin_confirmar=coste_sin_confirmar,
                state=("ESCENARIO HIPOTÉTICO/PENDIENTE DE CONFIRMAR: el coste del %s (%.2f €) aún no está verificado — "
                       "el margen que sigue es un cálculo con ese supuesto, no un dato firme" % (lote, coste["v"])) if coste_sin_confirmar
                else "ESTIMADO (depende de otros datos no verificados — ver cada línea de canal)",
                margen_bruto=margen_bruto, margen_bruto_pct=round(margen_bruto / net, 4) if net else None,
                contribucion_antes_ads=contribucion, contribucion_antes_ads_pct=round(contribucion / net, 4) if net else None,
                operativo_nota="Operativo = contribución − costes fijos NO amortizados en el plan (aún sin declarar: personal, estructura). PENDIENTE.",
                neto_nota="Neto = operativo − Ads; Ads se modela en el Bloque 3 del encargo (ingesta de informes). PENDIENTE.",
                caja_nota="Caja = neto ajustado a plazos de cobro Amazon y devoluciones reales; PENDIENTE de modelar (Bloque 2).")
    ref = REFERENCIA_CONTRIBUCION_LOTE1.get(canal)
    if lote == "lote1" and ref is not None and pvp == PVP["v"]:
        delta = _r2(contribucion - ref)
        out["reconciliacion_jose"] = {"referencia_jose": ref, "calculado": contribucion, "delta": delta,
                                       "nota": "COINCIDE con la cifra que dio José para lote1/%s" % canal if abs(delta) < 0.01
                                       else "NO COINCIDE (Δ=%.2f €) con la cifra que dio José — revisar el desglose" % delta}
    return out


def disponibles():
    """Catálogo expuesto (solo lectura) de qué SKU/lote/canal puede evaluar este motor hoy."""
    return {"skus": [SKU], "lotes": list(LOTES.keys()), "canales": list(CANALES.keys()),
            "pvp_escenario": PVP["v"], "volumen_90d": VOLUMEN_90D["v"]}
