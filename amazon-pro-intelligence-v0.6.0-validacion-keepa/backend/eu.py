"""Inteligencia de mercado europea de ACTIVCORE (V0.4.0): IVA por país, normalización de precios, benchmarking, motor económico y ranking multicriterio.
TODO es determinista y reproducible. Reglas de honestidad:
  * Cada variable lleva estado: VERIFICADO (fuente oficial leída), DOCUMENTADO (dato interno), HISTORICO_A_REVALIDAR, HIPOTESIS (supuesto editable) o NO_DISPONIBLE.
  * Un coste obligatorio ausente NO se convierte en cero: el resultado queda INCOMPLETO (margen None) salvo que el usuario aporte un valor (que se etiqueta HIPOTESIS).
  * Un país solo entra en el ranking si los criterios con datos NO hipotéticos suman al menos `min_coverage` del peso total. Si no, NO EVALUABLE.
  * Ranking = señal de oportunidad, no verdad: se muestra sensibilidad a los pesos y se separa ATRACTIVO de VIABILIDAD OPERATIVA."""
import math, statistics

COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "PL"]  # núcleo; SE/BE/IE solo con justificación
EXTRA = ["SE", "BE", "IE"]
NAMES = {"DE": "Alemania", "FR": "Francia", "IT": "Italia", "ES": "España", "NL": "Países Bajos", "PL": "Polonia", "SE": "Suecia", "BE": "Bélgica", "IE": "Irlanda"}
MARKET = {"DE": "amazon.de", "FR": "amazon.fr", "IT": "amazon.it", "ES": "amazon.es", "NL": "amazon.nl", "PL": "amazon.pl", "SE": "amazon.se", "BE": "amazon.com.be", "IE": "amazon.ie"}
CURRENCY = {"PL": "PLN", "SE": "SEK"}  # el resto EUR; importes en PLN/SEK exigen tipo de cambio documentado (no implementado → NO EVALUABLE en economía)
TODAY_REF = "2026-11-16"
VAT = {"DE": 19, "FR": 20, "IT": 22, "ES": 21, "NL": 21, "PL": 23, "SE": 25, "BE": 21, "IE": 23}
VAT_SRC = "Tipos generales 2026 (taxfoundation.org / vatupdate.com / Comisión Europea vía taxually.com). Los cosméticos tributan al tipo general; confirmar con asesor fiscal."
PVP_SCENARIOS = [29.90, 34.90, 39.90, 44.90, 49.90, 54.90, 59.90]
FIELDS = ["vat", "cogs", "inbound", "prep", "fulfillment", "storage", "returns", "promo", "other", "referral"]
REQUIRED = ["vat", "cogs", "inbound", "prep", "fulfillment", "storage", "returns", "referral"]
STATUS_OK = {"VERIFICADO", "DOCUMENTADO"}
STATUSES = {"VERIFICADO", "DOCUMENTADO", "A_CONFIRMAR", "HISTORICO_A_REVALIDAR", "HIPOTESIS", "NO_DISPONIBLE"}
SOFT = {"HIPOTESIS", "HISTORICO_A_REVALIDAR", "A_CONFIRMAR"}
LABEL = {"vat": "IVA", "cogs": "Coste del producto (sin IVA)", "inbound": "Transporte hasta Amazon", "prep": "Preparación", "fulfillment": "Tarifa FBA/FBM",
         "storage": "Almacenamiento", "returns": "Devoluciones", "promo": "Costes promocionales", "other": "Otros costes documentados", "referral": "Comisión Amazon"}
REFERRAL_SRC = "sell.amazon.de/preisgestaltung y sell.amazon.fr/tarifs (leídos 2026-11-16): Belleza, salud y cuidado personal 8 % ≤ 10 € · 15 % > 10 € · mínimo 0,30 €; sobre el precio total de venta (IVA incluido)"


def fld(v=None, status="NO_DISPONIBLE", source="", date=TODAY_REF):
    return {"v": v, "status": status, "source": source, "date": date}


def default_assumptions(countries=None):
    """Supuestos de partida por país. Solo IVA y comisión están VERIFICADOS; el coste histórico exige revalidación; el resto queda NO_DISPONIBLE (no se inventa)."""
    out = {}
    for c in (countries or COUNTRIES + EXTRA):
        out[c] = {"vat": fld(VAT[c] / 100.0, "VERIFICADO", VAT_SRC),
                  "cogs": fld(10.03, "HISTORICO_A_REVALIDAR", "Coste unitario histórico documentado sin IVA (10,03 €). NO es coste puesto en Amazon; reconfirmar."),
                  "referral": fld({"low": 0.08, "high": 0.15, "threshold": 10.0, "min": 0.30}, "VERIFICADO" if c in ("DE", "FR") else "A_CONFIRMAR", REFERRAL_SRC + ("" if c in ("DE", "FR") else " · para este país se asume la misma tabla (armonizada en la UE); confirmar en su página de tarifas")),
                  **{k: fld() for k in ("inbound", "prep", "fulfillment", "storage", "returns")}, "promo": fld(), "other": fld(),
                  "ads_acos": fld()}
    return out


HYPOTHESIS_EXAMPLE = {"inbound": 0.50, "prep": 0.30, "fulfillment": 3.50, "storage": 0.15, "returns": 1.00, "promo": 0.0, "other": 0.0}  # SOLO ilustrativo; se etiqueta HIPOTESIS


def apply_hypotheses(assump, values, source="Hipótesis editable del usuario (NO verificada)"):
    """Rellena campos NO_DISPONIBLE con valores del usuario marcándolos HIPOTESIS. No pisa datos verificados/documentados."""
    for k, v in values.items():
        if k in assump and assump[k]["status"] == "NO_DISPONIBLE" and isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
            assump[k] = fld(float(v), "HIPOTESIS", source)
    return assump


def _referral(pvp, f):
    r = f["v"]; pct = r["low"] if pvp <= r["threshold"] else r["high"]
    return max(r["min"], pct * pvp)


def r2(x):
    return None if x is None else round(x, 2)


def unit_economics(pvp, a, acos_target=None):
    """Economía por unidad para un PVP con IVA. `a` = supuestos de un país. Devuelve campos + estado de cada variable + qué falta.
    Distingue: margen bruto del producto · contribución tras Amazon (antes de publicidad) · tras publicidad · resultado del canal (sin costes fijos)."""
    missing = [k for k in REQUIRED if a[k]["v"] is None]
    used = {k: {"v": a[k]["v"] if k != "referral" else None, "status": a[k]["status"], "source": a[k]["source"]} for k in FIELDS}
    flags = sorted({a[k]["status"] for k in REQUIRED if a[k]["v"] is not None})
    res = {"pvp_gross": pvp, "inputs": used, "missing": missing, "status_mix": flags}
    if "vat" in missing or "referral" in missing:
        res.update(complete=False, label="INCOMPLETO: sin IVA/comisión verificados no se calcula nada"); return res
    vat = a["vat"]["v"]; net = pvp / (1 + vat); vat_amt = pvp - net
    res.update(vat_rate=vat, net_price=r2(net), vat_amount=r2(vat_amt))
    if a["cogs"]["v"] is not None:
        res["gross_margin_product"] = r2(net - a["cogs"]["v"]); res["gross_margin_product_pct"] = round((net - a["cogs"]["v"]) / net, 4)
    ref = _referral(pvp, a["referral"]); res["referral_fee"] = r2(ref)
    if missing:
        res.update(complete=False, label="INCOMPLETO: faltan " + ", ".join(LABEL[k] for k in missing) + " → no se declara margen de contribución", contribution=None, margin=None, breakeven_acos=None)
        return res
    opt_missing = [k for k in ("promo", "other") if a[k]["v"] is None]
    costs = {k: a[k]["v"] for k in ("cogs", "inbound", "prep", "fulfillment", "storage", "returns")}
    promo = a["promo"]["v"] or 0.0; other = a["other"]["v"] or 0.0
    contrib = net - sum(costs.values()) - ref - promo - other
    res.update(complete=True, contribution_before_ads=r2(contrib), margin_before_ads=round(contrib / net, 4), amazon_costs=r2(ref + costs["fulfillment"] + costs["storage"]),
               not_included=[LABEL[k] + " (no informado, no incluido)" for k in opt_missing],
               breakeven_acos_ex_vat=round(contrib / net, 4) if contrib > 0 else 0.0, breakeven_acos_inc_vat=round(contrib / pvp, 4) if contrib > 0 else 0.0,
               breakeven_roas_ex_vat=round(net / contrib, 2) if contrib > 0 else None,
               hypothetical=bool(SOFT & set(flags)),
               label=("ESCENARIO HIPOTÉTICO (contiene datos no verificados: " + ", ".join(f for f in flags if f in SOFT) + ")") if SOFT & set(flags) else "Calculado con datos verificados/documentados",
               acos_base_note="El ACoS de equilibrio se da sobre ventas SIN IVA y CON IVA: verificar en los informes de Amazon Ads qué base usan.")
    if acos_target is not None:
        ads = acos_target * net; after = contrib - ads
        res.update(acos_target=acos_target, ads_cost=r2(ads), contribution_after_ads=r2(after), margin_after_ads=round(after / net, 4))
    return res


def scenarios(a, pvps=None, acos_target=None):
    return [unit_economics(p, a, acos_target) for p in (pvps or PVP_SCENARIOS)]


def units_for_target(contribution_per_unit, target):
    if contribution_per_unit is None or contribution_per_unit <= 0 or target is None or target < 0:
        return None
    return math.ceil(target / contribution_per_unit)


def sensitivity(a, pvp, acos_target=None):
    """Sensibilidad ante PVP, costes logísticos (±20 %/±50 %) y publicidad. Solo si el escenario base es completo."""
    base = unit_economics(pvp, a, acos_target)
    if not base.get("complete"):
        return {"status": "NO CALCULABLE", "missing": base["missing"]}
    out = {"base": base, "pvp": [{"pvp": p, "contribution": e.get("contribution_before_ads"), "margin": e.get("margin_before_ads")} for p in PVP_SCENARIOS for e in [unit_economics(p, a)]], "logistics": [], "ads": []}
    for pct in (-0.5, -0.2, 0.2, 0.5):
        b = {k: dict(v) for k, v in a.items()}
        for k in ("inbound", "prep", "fulfillment", "storage"):
            b[k]["v"] = a[k]["v"] * (1 + pct)
        e = unit_economics(pvp, b); out["logistics"].append({"delta": pct, "contribution": e["contribution_before_ads"], "margin": e["margin_before_ads"]})
    be = base["breakeven_acos_ex_vat"]
    for ac in (0.0, 0.10, 0.20, 0.30, be):
        e = unit_economics(pvp, a, ac); out["ads"].append({"acos": round(ac, 4), "contribution_after_ads": e["contribution_after_ads"], "margin_after_ads": e["margin_after_ads"]})
    return out


# ------------------------------------------------------------------------------ benchmark ------------------------------------------------
KW_SERUM = ("sérum", "serum", "suero", "sérum".upper())
KW_SCALP = ("cuero cabelludo", "scalp", "kopfhaut", "cuir chevelu", "cuoio capelluto", "capilar", "cheveux", "haar", "capelli", "pelo")
KW_RINSE = ("champú", "champu", "shampoo", "shampooing", "acondicionador", "conditioner", "mascarilla", "mask", "masque", "maschera")
KW_SUPP = ("cápsulas", "capsulas", "kapseln", "gélules", "capsule", "comprimidos", "tabletas", "supplement", "complemento", "vitamin")


def suggest_comparability(title):
    """SUGERENCIA por palabras del título (inferencia: requiere confirmación humana). ALTA/MEDIA/BAJA."""
    t = (title or "").lower()
    if any(k in t for k in KW_SUPP):
        return "BAJA", "complemento alimenticio"
    if any(k in t for k in KW_RINSE) and not any(k in t for k in KW_SERUM):
        return "BAJA", "rinse-off/champú/mascarilla"
    if any(k in t for k in KW_SERUM) and any(k in t for k in KW_SCALP):
        return "ALTA", "sérum capilar/cuero cabelludo"
    if any(k in t for k in KW_SERUM) or any(k in t for k in KW_SCALP):
        return "MEDIA", "tratamiento capilar tópico próximo"
    return "BAJA", "sin señales de categoría"


def quantiles(xs):
    xs = sorted(xs); n = len(xs)
    if n == 0:
        return None
    med = statistics.median(xs)
    if n < 4:
        return {"n": n, "median": r2(med), "q1": None, "q3": None, "iqr": None, "min": r2(xs[0]), "max": r2(xs[-1]), "dispersion": None}
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return {"n": n, "median": r2(med), "q1": r2(q[0]), "q3": r2(q[2]), "iqr": r2(q[2] - q[0]), "min": r2(xs[0]), "max": r2(xs[-1]), "dispersion": round((q[2] - q[0]) / med, 3) if med else None}


USABLE_ST = ("CONFIRMADA", "AUTOMATICA")  # AUTOMATICA = puntuación determinista del descubrimiento (revisable); CONFIRMADA = decisión humana


def enrich(rec, usage=None, norm="ml"):
    """Normaliza: precio por 100 mL (si hay formato), precio por día (si hay dosis y duración documentadas). Nada de esto se inventa."""
    p = rec.get("price"); u = (usage or {}).get(rec.get("asin")) or {}
    o = dict(rec)
    base = rec.get("volume_ml") if norm == "ml" else rec.get("units")
    o["price_norm"] = r2(p / base * 100) if p is not None and base else None; o["norm_unit"] = "100 mL" if norm == "ml" else "100 unidades"
    days = u.get("days"); o["usage_days"] = days; o["usage_source"] = u.get("source")
    o["price_per_day"] = r2(p / days) if p is not None and days else None
    return o


def benchmark(records, registry=None, usage=None, include_suggested=False, norm="ml"):
    """records: registros normalizados de Keepa (de un país). registry: {asin: {comparability, status}} confirmado por el usuario.
    Por defecto solo cuentan comparables CONFIRMADOS ALTA/MEDIA. Devuelve filas + estadísticos + hallazgos."""
    registry = registry or {}; rows = []
    for r in records:
        e = enrich(r, usage, norm); reg = registry.get(r["asin"]); sug, why = suggest_comparability(r.get("title"))
        e["comparability"] = reg["comparability"] if reg else None; e["comparability_status"] = (reg.get("status") or "CONFIRMADA") if reg else "SUGERIDA"; e["comparability_suggested"] = (reg.get("suggested") or sug) if reg else sug; e["comparability_reason"] = (reg.get("reason") or why) if reg else why; e["comparability_score"] = reg.get("score") if reg else None
        rows.append(e)
    def counts(e):
        c = e["comparability"] if e["comparability_status"] in USABLE_ST else (e["comparability_suggested"] if include_suggested else None)
        return c in ("ALTA", "MEDIA")
    use = [e for e in rows if counts(e)]
    p100 = [e["price_norm"] for e in use if e["price_norm"] is not None]; pk = [e["price"] for e in use if e["price"] is not None]
    cheapest = min((e for e in use if e["price_norm"] is not None), key=lambda e: e["price_norm"], default=None)
    premium = max((e for e in use if e["price_norm"] is not None), key=lambda e: e["price_norm"], default=None)
    return {"rows": rows, "used": len(use), "total": len(rows), "price_norm": quantiles(p100), "price_pack": quantiles(pk),
            "bsr": quantiles([e["bsr"] for e in use if e.get("bsr")]), "reviews": quantiles([e["reviews"] for e in use if e.get("reviews") is not None]),
            "rating": quantiles([e["rating"] for e in use if e.get("rating") is not None]),
            "cheapest": {k: cheapest[k] for k in ("asin", "brand", "price_norm")} if cheapest else None, "premium": {k: premium[k] for k in ("asin", "brand", "price_norm")} if premium else None,
            "unconfirmed": sum(1 for e in rows if e["comparability_status"] != "CONFIRMADA"), "automatic": sum(1 for e in rows if e["comparability_status"] == "AUTOMATICA"), "norm_unit": "100 mL" if norm == "ml" else "100 unidades", "include_suggested": include_suggested}


def percentile_position(x, xs):
    """Fracción de competidores con precio/100 mL inferior a x (0 = el más barato, 1 = el más caro)."""
    return None if not xs else sum(1 for y in xs if y < x) / len(xs)


# --------------------------------------------------------------------------------- ranking ---------------------------------------------------
CRITERIA = ["demanda", "margen", "competencia", "logistica", "crecimiento"]
WEIGHTS = {"demanda": 30, "margen": 30, "competencia": 20, "logistica": 15, "crecimiento": 5}
CRIT_NAME = {"demanda": "Demanda y oportunidad", "margen": "Margen neto", "competencia": "Competencia y precios", "logistica": "Logística, fiscalidad y cumplimiento", "crecimiento": "Crecimiento potencial"}
PRESETS = {"base": dict(WEIGHTS), "conservadora": {"demanda": 10, "margen": 40, "competencia": 20, "logistica": 30, "crecimiento": 0}, "crecimiento": {"demanda": 40, "margen": 20, "competencia": 15, "logistica": 10, "crecimiento": 15}}
ATTRACT = ("demanda", "competencia", "crecimiento"); VIABLE = ("margen", "logistica")
CONF_RANK = {"ALTA": 3, "MEDIA": 2, "BAJA": 1, "NULA": 0}
FORMULAS = {
    "demanda": "100·(1 − min(1, log10(BSR mediano)/log10(100000))) sobre comparables confirmados ALTA/MEDIA; exige ≥ min_asins con BSR. BSR = señal indirecta (no son ventas) y no es comparable entre países → confianza máx. MEDIA.",
    "margen": "100·min(1, margen de contribución antes de publicidad / 40 %) al PVP de referencia; confianza ALTA solo si todas las variables son VERIFICADO/DOCUMENTADO; MEDIA si hay coste histórico a revalidar; BAJA si hay hipótesis.",
    "competencia": "50 % posición de precio (100·(1 − fracción de comparables más baratos por 100 mL)) + 50 % barrera de reseñas (100·(1 − min(1, mediana de reseñas/10000))). Exige ≥ min_asins con precio/100 mL.",
    "logistica": "100·(requisitos documentados y cumplidos / requisitos aplicables) del país (PIF, CPSR, persona responsable UE, CPNP, idiomas de etiquetado, representante fiscal, EPR). NO EVALUABLE si menos de la mitad de los requisitos están revisados (OK/NO_CUMPLE); PENDIENTE = desconocido, no suma.",
    "crecimiento": "Pendiente de ≥ 90 días de historial BSR/precio en ≥ min_asins: pendiente de tendencia del BSR mediano. NO EVALUABLE sin ese historial.",
}


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def score_country(c, data, params):
    """data = {"benchmark": benchmark(), "economics": unit_economics() en el PVP de referencia, "compliance": {...}, "pvp_ref": float, "growth": float|None, "keepa_supported": bool}. Devuelve criterios con puntuación o NO EVALUABLE."""
    mn = params["min_asins"]; crit = {}
    b = data.get("benchmark"); supported = data.get("keepa_supported", True)
    def ne(k, why, need):
        crit[k] = {"status": "NO EVALUABLE", "score": None, "confidence": "NULA", "missing": need, "reason": why, "formula": FORMULAS[k]}
    # demanda
    n_bsr = len(([e for e in b["rows"] if e.get("bsr")])) if b else 0
    if not supported:
        ne("demanda", "Keepa no cubre este marketplace", ["datos de mercado por otra vía (p. ej. importación CSV de Helium 10/Seller Central)"])
    elif not b or not b["bsr"] or b["bsr"]["n"] < mn:
        ne("demanda", "comparables confirmados con BSR insuficientes (%d < %d)" % ((b or {}).get("bsr", {}) and b["bsr"]["n"] or 0, mn), ["≥ %d ASIN comparables confirmados con BSR (consulta Keepa + confirmar comparabilidad)" % mn])
    else:
        med = b["bsr"]["median"]; sc = 100 * (1 - _clamp(math.log10(max(med, 1)) / math.log10(100000)))
        crit["demanda"] = {"status": "EVALUADO", "score": round(sc, 1), "confidence": "MEDIA", "inputs": {"bsr_mediano": med, "n": b["bsr"]["n"]}, "formula": FORMULAS["demanda"], "source": "Keepa API", "date": max((e["fetched_at"] for e in b["rows"]), default=None)}
    # margen
    ec = data.get("economics")
    if c in ("PL", "SE"):
        ne("margen", "moneda local (%s): falta tipo de cambio documentado" % CURRENCY[c], ["tipo de cambio y precios locales documentados"])
    elif not ec or not ec.get("complete"):
        ne("margen", "costes obligatorios sin dato: " + ", ".join(LABEL[k] for k in (ec or {}).get("missing", REQUIRED)), ["valor documentado de: " + ", ".join(LABEL[k] for k in (ec or {}).get("missing", REQUIRED))])
    else:
        conf = "BAJA" if "HIPOTESIS" in ec["status_mix"] else "MEDIA" if {"HISTORICO_A_REVALIDAR", "A_CONFIRMAR"} & set(ec["status_mix"]) else "ALTA"
        crit["margen"] = {"status": "EVALUADO", "score": round(100 * min(1.0, max(0.0, ec["margin_before_ads"]) / 0.40), 1), "confidence": conf, "inputs": {"pvp": ec["pvp_gross"], "margen_contribucion": ec["margin_before_ads"], "contribucion": ec["contribution_before_ads"]}, "formula": FORMULAS["margen"], "source": "Motor económico (supuestos con estado)", "date": TODAY_REF}
    # competencia
    p100 = [e["price_norm"] for e in (b["rows"] if b else []) if e["price_norm"] is not None and (e["comparability_status"] in USABLE_ST and e["comparability"] in ("ALTA", "MEDIA") or (b["include_suggested"] and e["comparability_suggested"] in ("ALTA", "MEDIA") and e["comparability_status"] not in USABLE_ST))]
    pvp100 = data.get("pvp100")
    if not supported:
        ne("competencia", "Keepa no cubre este marketplace", ["precios de competidores por otra vía"])
    elif len(p100) < mn or pvp100 is None:
        ne("competencia", "comparables con precio/100 mL insuficientes (%d < %d)" % (len(p100), mn), ["≥ %d comparables confirmados con precio y formato en mL" % mn])
    else:
        q = percentile_position(pvp100, p100); rev = (b["reviews"] or {}).get("median")
        if rev is None:
            ne("competencia", "sin reseñas disponibles", ["reseñas de comparables"])
        else:
            sc = 0.5 * 100 * (1 - q) + 0.5 * 100 * (1 - _clamp(rev / 10000))
            crit["competencia"] = {"status": "EVALUADO", "score": round(sc, 1), "confidence": "MEDIA", "inputs": {"pvp_por_100ml": pvp100, "fraccion_comparables_mas_baratos": round(q, 3), "resenas_mediana": rev, "n": len(p100)}, "formula": FORMULAS["competencia"], "source": "Keepa API", "date": max((e["fetched_at"] for e in b["rows"]), default=None)}
    # logística / cumplimiento
    comp = data.get("compliance") or {}
    app = [k for k, v in comp.items() if v in ("OK", "PENDIENTE", "NO_CUMPLE")]; rev = [k for k in app if comp[k] in ("OK", "NO_CUMPLE")]
    if not app or len(rev) / len(app) < 0.5:
        ne("logistica", "requisitos del país sin revisar (%d de %d revisados; se exige ≥ 50 %%)" % (len(rev), len(app)), ["revisar con documentación los requisitos de cumplimiento/logística del país (ver ACTIVCORE_RIESGOS_REGULATORIOS)"])
    else:
        ok = sum(1 for k in app if comp[k] == "OK")
        crit["logistica"] = {"status": "EVALUADO", "score": round(100 * ok / len(app), 1), "confidence": "MEDIA", "inputs": {"cumplidos": ok, "revisados": len(rev), "aplicables": len(app)}, "formula": FORMULAS["logistica"], "source": "Checklist del expediente", "date": TODAY_REF}
    # crecimiento
    g = data.get("growth")
    if g is None:
        ne("crecimiento", "sin ≥ 90 días de historial en comparables", ["historial BSR/precio ≥ 90 días de ≥ %d comparables" % mn])
    else:
        crit["crecimiento"] = {"status": "EVALUADO", "score": round(100 * _clamp(0.5 + g), 1), "confidence": "BAJA", "inputs": {"tendencia_bsr": g}, "formula": FORMULAS["crecimiento"], "source": "Keepa API (historial)", "date": TODAY_REF}
    return crit


def aggregate(crit, weights, subset=None):
    ks = [k for k in (subset or CRITERIA) if crit[k]["status"] == "EVALUADO"]
    w = sum(weights[k] for k in ks)
    return None if not w else round(sum(weights[k] * crit[k]["score"] for k in ks) / w, 1)


def rank(country_data, weights=None, params=None):
    """country_data = {país: data(ver score_country)}. Devuelve ranking de evaluables, pendientes, recomendación y sensibilidad."""
    P = {"min_asins": 8, "min_coverage": 0.60, "min_conf": "MEDIA", **(params or {})}; W = dict(weights or WEIGHTS)
    if abs(sum(W.values()) - 100) > 1e-6 or any(v < 0 for v in W.values()):
        raise ValueError("los pesos deben sumar 100 y no ser negativos")
    per = {}
    for c, d in country_data.items():
        crit = score_country(c, d, P)
        tw = sum(W.values()); cov = sum(W[k] for k in CRITERIA if crit[k]["status"] == "EVALUADO" and CONF_RANK[crit[k]["confidence"]] >= CONF_RANK[P["min_conf"]]) / tw
        miss = [{"criterio": CRIT_NAME[k], "falta": crit[k]["missing"], "motivo": crit[k]["reason"]} for k in CRITERIA if crit[k]["status"] != "EVALUADO"]
        low = [CRIT_NAME[k] for k in CRITERIA if crit[k]["status"] == "EVALUADO" and CONF_RANK[crit[k]["confidence"]] < CONF_RANK[P["min_conf"]]]
        per[c] = {"country": c, "name": NAMES.get(c, c), "criteria": crit, "coverage": round(cov, 3), "evaluable": cov >= P["min_coverage"], "missing": miss, "low_confidence": low,
                  "score": aggregate(crit, W) if cov >= P["min_coverage"] else None, "attractiveness": aggregate(crit, W, ATTRACT), "viability": aggregate(crit, W, VIABLE)}
    ev = sorted([p for p in per.values() if p["evaluable"]], key=lambda p: (-p["score"], p["country"]))
    for i, p in enumerate(ev):
        p["rank"] = i + 1
    pend = [p for p in per.values() if not p["evaluable"]]
    out = {"weights": W, "params": P, "ranking": ev, "pending": pend, "launch": ev[0]["country"] if ev else None, "second": ev[1]["country"] if len(ev) > 1 else None,
           "note": "Sin países evaluables: no hay recomendación. Falta lo indicado en cada país." if not ev else "Recomendación condicionada a los datos: cambia si cambian los datos o los pesos."}
    if ev:
        diffs = {}
        for pname, pw in PRESETS.items():
            sc = sorted([(aggregate(per[p["country"]]["criteria"], pw), p["country"]) for p in ev], key=lambda t: (-(t[0] or 0), t[1]))
            diffs[pname] = {"top": sc[0][1], "order": [c for _, c in sc]}
        out["presets"] = diffs
        stable = total = 0
        for k in CRITERIA:
            for dlt in (-10, 10):
                w2 = dict(W); w2[k] = max(0, W[k] + dlt); rest = sum(v for kk, v in W.items() if kk != k); tgt = 100 - w2[k]
                for kk in W:
                    if kk != k:
                        w2[kk] = W[kk] * tgt / rest if rest else 0
                top = sorted([(aggregate(per[p["country"]]["criteria"], w2), p["country"]) for p in ev], key=lambda t: (-(t[0] or 0), t[1]))[0][1]
                total += 1; stable += top == ev[0]["country"]
        out["sensitivity"] = {"stable_share": round(stable / total, 2), "scenarios": total, "note": "Fracción de perturbaciones de ±10 puntos en cada peso en las que el primer país no cambia."}
    return out
