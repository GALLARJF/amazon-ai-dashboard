"""Motor determinista Amazon Pro V0.3 — port fiel de js/economics.js y js/dossier.js (V0.2).
Sin IA, sin red, sin azar. La paridad con JS se verifica en tests/parity_test.py."""
import copy, datetime, math

INF = float("inf")
EPS = 1e-9

FEE_SCHEDULES = {
    "generico_15": {"label": "Genérica 15 % (orientativa)", "mode": "flat", "tiers": [(INF, 15)], "minFee": 0.3, "verified": False},
    "belleza_8_15": {"label": "Belleza / cuidado personal: 8 % hasta 10 €, 15 % por encima (orientativa)", "mode": "threshold", "tiers": [(10, 8), (INF, 15)], "minFee": 0.3, "verified": False},
    "tramos_marginales": {"label": "Tramos marginales de ejemplo", "mode": "marginal", "tiers": [(100, 15), (INF, 8)], "minFee": 0.3, "verified": False},
    "personalizado": {"label": "Personalizada", "mode": "flat", "tiers": [(INF, 15)], "minFee": 0, "verified": False, "custom": True},
}
DEFAULTS = dict(price=24.9, vatPct=21, feeSchedule="belleza_8_15", customReferralPct=15, customMinFee=0, cost=5.2, prep=0, fulfilMode="FBA",
                fbaFee=4.1, fbmShipping=0, fbmPackaging=0, fbmHandling=0, storageMonthly=0.15, storageMonths=2, returnsPct=4,
                returnProcessing=1.5, unsellablePct=30, otherCosts=0, acosTarget=25, adsBasis="gross", minMarginPct=15)
NUM_RULES = [("price", "PVP con IVA", 0.01, 100000), ("vatPct", "IVA %", 0, 30), ("cost", "Coste de producto", 0, 100000), ("prep", "Preparación/etiquetado", 0, 100000),
             ("fbaFee", "Tarifa FBA", 0, 1000), ("fbmShipping", "Envío FBM", 0, 1000), ("fbmPackaging", "Embalaje FBM", 0, 1000), ("fbmHandling", "Manipulación FBM", 0, 1000),
             ("storageMonthly", "Almacenaje €/ud/mes", 0, 1000), ("storageMonths", "Meses de almacenaje", 0, 60), ("returnsPct", "Devoluciones %", 0, 100),
             ("returnProcessing", "Coste por devolución", 0, 1000), ("unsellablePct", "% devoluciones no vendibles", 0, 100), ("otherCosts", "Otros costes", 0, 100000),
             ("acosTarget", "ACoS objetivo %", 0, 99), ("minMarginPct", "Margen mínimo %", 0, 95)]


def _isnum(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def schedule(i):
    base = FEE_SCHEDULES.get(i.get("feeSchedule") or "generico_15")
    if not base:
        return None
    if base.get("custom"):
        try:
            pct = float(i.get("customReferralPct"))
            mf = float(i.get("customMinFee") or 0)
        except (TypeError, ValueError):
            pct, mf = float("nan"), float("nan")
        return {**base, "tiers": [(INF, pct)], "minFee": mf}
    return base


def referral_fee(price, sch):
    fee = 0.0
    if sch["mode"] == "marginal":
        lo = 0
        for up, pct in sch["tiers"]:
            hi = min(price, up)
            if hi > lo:
                fee += (hi - lo) * pct / 100
            lo = up
            if price <= up:
                break
    else:
        pct = next((p for up, p in sch["tiers"] if price <= up), sch["tiers"][-1][1])
        fee = price * pct / 100
    return max(fee, sch.get("minFee") or 0)


def validate(i):
    errors = []
    for k, label, lo, hi in NUM_RULES:
        v = i.get(k)
        if not _isnum(v):
            errors.append(f"{label}: valor no numérico")
        elif v < lo or v > hi:
            errors.append(f"{label}: fuera de rango ({lo}–{hi})")
    sch = schedule(i)
    if not sch:
        errors.append("Esquema de comisión desconocido")
    elif sch.get("custom"):
        p = sch["tiers"][0][1]
        if not math.isfinite(p) or p < 0 or p >= 100:
            errors.append("Comisión personalizada: fuera de rango (0–<100)")
        if not math.isfinite(sch["minFee"]) or sch["minFee"] < 0:
            errors.append("Comisión mínima inválida")
    if i.get("fulfilMode") not in ("FBA", "FBM"):
        errors.append("Modo logístico debe ser FBA o FBM")
    if i.get("adsBasis") not in ("gross", "net"):
        errors.append("Base de ACoS debe ser gross o net")
    return errors


def _fulfil(i):
    return i["fbaFee"] if i["fulfilMode"] == "FBA" else i["fbmShipping"] + i["fbmPackaging"] + i["fbmHandling"]


def unit(raw, price_override=None):
    i = {**DEFAULTS, **(raw or {})}
    if price_override is not None:
        i["price"] = price_override
    errors = validate(i)
    if errors:
        return {"valid": False, "errors": errors, "warnings": []}
    sch = schedule(i)
    g = 1 / (1 + i["vatPct"] / 100)
    p = i["price"]
    net = p * g
    referral = referral_fee(p, sch)
    fulfil = _fulfil(i)
    storage = i["storageMonthly"] * i["storageMonths"] if i["fulfilMode"] == "FBA" else 0
    returns = (i["returnsPct"] / 100) * (i["returnProcessing"] + (i["unsellablePct"] / 100) * i["cost"])
    fixed = i["cost"] + i["prep"] + fulfil + storage + returns + i["otherCosts"]
    before_ads = net - fixed - referral
    ads_base = p if i["adsBasis"] == "gross" else net
    ads = (i["acosTarget"] / 100) * ads_base
    contribution = before_ads - ads
    w = []
    if not sch["verified"]:
        w.append("Comisión basada en tarifa orientativa NO verificada: confirmar en las tarifas vigentes de Amazon para la categoría.")
    if i["vatPct"] == 0:
        w.append("IVA 0 %: confirmar que el PVP no incluye IVA (régimen/destino).")
    if i["adsBasis"] == "gross":
        w.append("ACoS sobre PVP con IVA: verificar que los informes de Amazon Ads reportan ventas con IVA.")
    if i["fulfilMode"] == "FBA" and i["storageMonthly"] * i["storageMonths"] == 0:
        w.append("Almacenaje FBA = 0: el margen puede estar sobrestimado.")
    if i["returnsPct"] == 0:
        w.append("Devoluciones 0 %: poco realista; el margen puede estar sobrestimado.")
    if i["cost"] > net:
        w.append("El coste de producto supera el ingreso neto: pérdida garantizada.")
    return {"valid": True, "errors": [], "warnings": w, "input": i, "price": p, "net": net, "referral": referral, "fulfil": fulfil, "storage": storage,
            "returns": returns, "prep": i["prep"], "cost": i["cost"], "other": i["otherCosts"], "ads": ads, "adsBase": ads_base, "beforeAds": before_ads,
            "contribution": contribution, "contributionPct": contribution / net if net > 0 else 0,
            "breakEvenAcos": before_ads / ads_base if ads_base > 0 else 0}


def min_price(raw, margin_pct=None):
    i = {**DEFAULTS, **(raw or {})}
    m = (i["minMarginPct"] if margin_pct is None else margin_pct) / 100
    if validate({**i, "price": 1}):
        return None
    sch = schedule(i)
    g = 1 / (1 + i["vatPct"] / 100)
    acos = i["acosTarget"] / 100
    c = 1 if i["adsBasis"] == "gross" else g
    storage = i["storageMonthly"] * i["storageMonths"] if i["fulfilMode"] == "FBA" else 0
    K = i["cost"] + i["prep"] + _fulfil(i) + storage + (i["returnsPct"] / 100) * (i["returnProcessing"] + (i["unsellablePct"] / 100) * i["cost"]) + i["otherCosts"]
    regimes = []
    if sch["mode"] == "marginal":
        lo = 0
        acc = 0.0
        for up, pct in sch["tiers"]:
            regimes.append((acc - lo * pct / 100, pct / 100, lo, up))
            acc += (min(up, 1e9) - lo) * pct / 100
            lo = up
    else:
        lo = 0
        for up, pct in sch["tiers"]:
            regimes.append((0.0, pct / 100, lo, up))
            lo = up
    if sch["minFee"] > 0:
        regimes.append((sch["minFee"], 0.0, 0, INF))
    best = None
    for A, B, lo, hi in regimes:
        den = g * (1 - m) - B - acos * c
        if den <= EPS:
            continue
        p = (K + A) / den
        if not (p > lo - EPS and p <= hi + EPS) or p < 0.01:
            continue
        u = unit(i, p)
        if u["valid"] and u["contributionPct"] >= m - 1e-7 and (best is None or p < best):
            best = p
    if best is None:
        return None
    commercial = math.ceil(best * 100 - 1e-9) / 100
    for _ in range(500):
        u = unit(i, commercial)
        if u["valid"] and u["contributionPct"] >= m - 1e-9:
            return {"exact": best, "commercial": commercial}
        commercial = round((commercial + 0.01) * 100) / 100
    return {"exact": best, "commercial": None}


def scenarios(raw, prices):
    """Comparación de escenarios de PVP: economía determinista por precio."""
    out = []
    for p in prices:
        u = unit(raw, p)
        if not u["valid"]:
            out.append({"price": p, "valid": False, "errors": u["errors"]})
        else:
            out.append({"price": p, "valid": True, "net": u["net"], "referral": u["referral"], "contribution": u["contribution"],
                        "contributionPct": u["contributionPct"], "breakEvenAcos": u["breakEvenAcos"], "ads": u["ads"]})
    return out


# ------------------------------- Dossier ---------------------------------------------------------
MAX_COMP_AGE, MAX_KW_AGE, MIN_COMP, MIN_KW = 30, 60, 3, 5
REG = {
    "cosmetico": [("rp", "Persona responsable en la UE designada (Reg. CE 1223/2009)", True), ("cpnp", "Notificación en el portal CPNP", True),
                  ("cpsr", "Informe de seguridad del producto cosmético (CPSR) firmado por evaluador cualificado", True), ("etiq", "Etiquetado conforme (INCI, lote, PAO, responsable, contenido)", True),
                  ("pif", "Expediente de información del producto (PIF) disponible", True), ("amz", "Cumplimiento de políticas/restricciones de Amazon para la categoría", True)],
    "suplemento": [("notif", "Notificación de puesta en el mercado de complementos alimenticios (AESAN/autoridad competente)", True), ("etiq", "Etiquetado conforme (RD 1487/2009 y Reg. UE 1169/2011)", True),
                   ("claims", "Solo declaraciones de salud autorizadas (Reg. CE 1924/2006)", True), ("nf", "Ingredientes revisados frente a nuevos alimentos (Reg. UE 2015/2283)", True),
                   ("spec", "Especificaciones y análisis de lote del producto", True), ("amz", "Cumplimiento de políticas/restricciones de Amazon para la categoría", True)],
    "otro": [("gpsr", "Persona responsable y etiquetado conforme (GPSR, Reg. UE 2023/988)", True), ("ce", "Marcado CE / declaración de conformidad si aplica", False),
             ("reach", "REACH / RoHS / otras restricciones de sustancias si aplica", False), ("amz", "Cumplimiento de políticas/restricciones de Amazon para la categoría", True)],
}
CONTENT = [("img_main", "Imagen principal conforme (fondo blanco, resolución mínima de Amazon)", True), ("title", "Título redactado", True), ("bullets", "Bullets redactados (5)", True),
           ("gallery", "Galería: ≥ 6 imágenes (uso, escala, packaging, infografías)", False), ("aplus", "Contenido A+ preparado", False), ("video", "Vídeo de producto", False),
           ("backend", "Términos de búsqueda (backend) definidos", False)]
LOGI = {"FBA": [("dims", "Dimensiones y peso verificados (determinan la tarifa FBA)", True), ("fnsku", "Etiquetado FNSKU / preparación FBA planificado", True), ("inbound", "Envío de entrada a FBA planificado", True)],
        "FBM": [("dims", "Dimensiones y peso verificados (determinan el envío)", True), ("carrier", "Transportista y plazo de entrega definidos", True), ("returns", "Gestión de devoluciones definida", True)]}
RISKY = ["cura", "curar", "trata", "tratamiento", "previene", "elimina", "clínicamente probado", "dermatológicamente", "sana", "regenera", "antiinflamatorio", "adelgaz", "detox", "milagro", "100% natural", "sin efectos secundarios", "aprobado por"]


def _items(lst):
    return {i: {"label": l, "critical": c, "status": "pendiente", "evidence": "", "date": ""} for i, l, c in lst}


def create_empty(reg_type="cosmetico", mode="FBA"):
    return {"product": {"name": "", "regType": reg_type, "ownPackUnits": 1, "ownContent": 100, "contentUnit": "ml"}, "econ": dict(DEFAULTS),
            "competitors": [], "keywords": [], "claims": [], "regulatory": _items(REG[reg_type]), "content": _items(CONTENT),
            "logistics": {"mode": mode, "stockAvailable": None, "leadTimeDays": None, "forecastUnitsMonth": None, "coverTargetDays": 45, "items": _items(LOGI[mode])}}


def _isdate(s):
    try:
        return isinstance(s, str) and len(s) == 10 and bool(datetime.date.fromisoformat(s))
    except ValueError:
        return False


def _age(d, today):
    return round((datetime.date.fromisoformat(today) - datetime.date.fromisoformat(d)).days)


def _pctl(a, p):
    s = sorted(a)
    i = (len(s) - 1) * p
    lo, hi = math.floor(i), math.ceil(i)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def _num(x):
    return _isnum(x)


def benchmark(d, today):
    own = d["product"]
    rows, issues, seen, per_row = [], [], set(), {}
    for idx, c in enumerate(d.get("competitors") or []):
        name = (c.get("name") or f"#{idx + 1}").strip()
        key = (c.get("asin") or c.get("name") or "").strip().lower()
        bad = []
        if not _num(c.get("priceGross")) or c["priceGross"] <= 0: bad.append("precio")
        if not _num(c.get("packUnits")) or c["packUnits"] < 1: bad.append("uds. por pack")
        if not _num(c.get("contentValue")) or c["contentValue"] <= 0: bad.append("contenido")
        sh = c.get("shipping")
        if sh is not None and (not _num(sh) or sh < 0): bad.append("envío")
        if not (c.get("source") or "").strip(): bad.append("fuente")
        if not _isdate(c.get("date")): bad.append("fecha")
        if bad:
            per_row[idx] = {"ok": False, "reason": "falta/inválido: " + ", ".join(bad)}
            issues.append(f"{name}: dato inválido o ausente ({', '.join(bad)}) → excluido"); continue
        a = _age(c["date"], today)
        if a < 0:
            per_row[idx] = {"ok": False, "reason": "fecha futura"}; issues.append(f"{name}: fecha futura → excluido"); continue
        if a > MAX_COMP_AGE:
            per_row[idx] = {"ok": False, "reason": f"caducado ({a} d)"}; issues.append(f"{name}: dato de hace {a} días (> {MAX_COMP_AGE}) → excluido"); continue
        if key and key in seen:
            per_row[idx] = {"ok": False, "reason": "duplicado"}; issues.append(f"{name}: duplicado → excluido"); continue
        if key: seen.add(key)
        up = (c["priceGross"] + (sh or 0)) / (c["packUnits"] * c["contentValue"])
        per_row[idx] = {"ok": True, "unitPrice": up}
        rows.append({**c, "name": name, "_idx": idx, "unitPrice": up})
    valid = rows
    if len(rows) >= 4:
        med = _pctl([r["unitPrice"] for r in rows], 0.5)
        valid = []
        for r in rows:
            if r["unitPrice"] <= 3 * med and r["unitPrice"] >= med / 3:
                valid.append(r)
            else:
                per_row[r["_idx"]] = {"ok": False, "reason": "atípico", "unitPrice": r["unitPrice"]}
                issues.append(f"{r['name']}: precio unitario atípico → excluido")
    out = {"rows": valid, "perRow": per_row, "issues": issues, "n": len(valid), "sufficient": len(valid) >= MIN_COMP, "unitLabel": own.get("contentUnit") or "ud"}
    if valid:
        u = [r["unitPrice"] for r in valid]
        size = (own.get("ownPackUnits") or 1) * (own.get("ownContent") or 1)
        out["unit"] = {"min": min(u), "p25": _pctl(u, .25), "median": _pctl(u, .5), "p75": _pctl(u, .75), "max": max(u)}
        out["band"] = {"low": out["unit"]["p25"] * size, "mid": out["unit"]["median"] * size, "high": out["unit"]["p75"] * size, "size": size}
    return out


def _eval_checklist(items, section, F, prefix):
    for id_, it in items.items():
        sev = "block" if it.get("critical") else "warn"
        st = it.get("status")
        ev = (it.get("evidence") or "").strip()
        fid = f"{section}.{id_}"
        if st == "pendiente":
            F.append({"id": fid, "section": section, "severity": sev, "title": f"{prefix}: {it['label']}", "why": "Pendiente.", "fix": "Completa el punto o márcalo «No aplica» con justificación."})
        elif st == "cumplido" and not ev:
            F.append({"id": fid, "section": section, "severity": sev, "title": f"{prefix}: {it['label']}", "why": "Marcado como cumplido sin evidencia (referencia, documento o enlace).", "fix": "Indica la referencia de la evidencia."})
        elif st == "no_aplica" and not ev:
            F.append({"id": fid, "section": section, "severity": "warn", "title": f"{prefix}: {it['label']}", "why": "«No aplica» sin justificación.", "fix": "Justifica por qué no aplica."})


def evaluate(d, today=None):
    F, S = [], {}
    today = today or datetime.date.today().isoformat()
    add = F.append
    bm = benchmark(d, today); S["benchmark"] = bm
    for t in bm["issues"]:
        add({"id": "bench.issue", "section": "benchmark", "severity": "warn", "title": "Benchmark", "why": t, "fix": "Corrige o actualiza el dato del competidor."})
    if not bm["sufficient"]:
        add({"id": "bench.insufficient", "section": "benchmark", "severity": "block", "title": f"Benchmark insuficiente ({bm['n']}/{MIN_COMP})", "why": f"Se necesitan ≥ {MIN_COMP} competidores válidos, distintos, con fuente y fecha ≤ {MAX_COMP_AGE} días.", "fix": "Añade competidores comparables con su fuente y fecha de captura."})
    okk, stale = [], []
    for k in d.get("keywords") or []:
        if not (k.get("keyword") or "").strip() or not _num(k.get("volume")) or k["volume"] < 0 or not (k.get("source") or "").strip() or not _isdate(k.get("date")) or _age(k["date"], today) < 0:
            continue
        (stale if _age(k["date"], today) > MAX_KW_AGE else okk).append(k)
    S["demand"] = {"valid": len(okk), "stale": len(stale), "totalVolume": sum(k["volume"] for k in okk)}
    if not okk:
        add({"id": "demand.none", "section": "demand", "severity": "block", "title": "Sin datos de demanda vigentes", "why": f"No hay keywords válidas con volumen, fuente y fecha ≤ {MAX_KW_AGE} días" + (f" ({len(stale)} caducadas)." if stale else "."), "fix": "Añade keywords con su volumen, fuente (p. ej. exportación Helium 10) y fecha."})
    elif len(okk) < MIN_KW:
        add({"id": "demand.few", "section": "demand", "severity": "warn", "title": f"Pocas keywords ({len(okk)}/{MIN_KW})", "why": "La estimación de demanda es frágil.", "fix": f"Añade hasta {MIN_KW} o más keywords."})
    if okk and stale:
        add({"id": "demand.stale", "section": "demand", "severity": "warn", "title": f"{len(stale)} keywords caducadas", "why": f"Fecha anterior a {MAX_KW_AGE} días.", "fix": "Refresca los datos."})
    u = unit(d["econ"]); S["unit"] = u
    if not u["valid"]:
        add({"id": "econ.invalid", "section": "price", "severity": "block", "title": "Datos económicos inválidos", "why": " · ".join(u["errors"]), "fix": "Corrige los campos señalados."})
    else:
        mp = min_price(d["econ"]); S["minPrice"] = mp; S["band"] = bm.get("band")
        band = S["band"]
        if u["contribution"] <= 0:
            add({"id": "econ.loss", "section": "price", "severity": "nogo", "title": "Pierdes dinero por unidad", "why": f"Contribución tras publicidad: {u['contribution']:.2f} € por unidad al precio planificado.", "fix": "Reduce costes o sube el precio."})
        if not mp:
            add({"id": "econ.unreachable", "section": "price", "severity": "nogo", "title": "Margen mínimo inalcanzable", "why": f"Con estos costes y un ACoS objetivo del {d['econ']['acosTarget']} % no existe precio que alcance {d['econ']['minMarginPct']} % de margen.", "fix": "Reduce costes/ACoS objetivo o acepta un margen menor de forma explícita."})
        else:
            if band and mp["commercial"] > band["high"] + 0.005:
                add({"id": "price.out_of_band", "section": "price", "severity": "nogo", "title": "Precio mínimo rentable fuera de la banda competitiva", "why": f"Precio mínimo {mp['commercial']:.2f} € > extremo alto de la banda ({band['high']:.2f} €, P75 normalizado a tu formato).", "fix": "No es competitivo con estos costes: rediseña coste/formato o diferénciate."})
            elif u["price"] < mp["commercial"] - 1e-9:
                add({"id": "price.below_min", "section": "price", "severity": "block", "title": "Precio planificado por debajo del mínimo rentable", "why": f"Planificado {u['price']:.2f} € < mínimo {mp['commercial']:.2f} € (margen objetivo {d['econ']['minMarginPct']} %).", "fix": f"Sube el precio a ≥ {mp['commercial']:.2f} € o reduce costes."})
        if band:
            if u["price"] > band["high"] + 0.005:
                add({"id": "price.above", "section": "price", "severity": "warn", "title": "Precio por encima de la banda competitiva", "why": f"{u['price']:.2f} € > {band['high']:.2f} €.", "fix": "Justifica el posicionamiento premium."})
            elif u["price"] < band["low"] - 0.005:
                add({"id": "price.below", "section": "price", "severity": "warn", "title": "Precio por debajo de la banda competitiva", "why": f"{u['price']:.2f} € < {band['low']:.2f} €: posible margen sacrificado.", "fix": "Valora subir hasta la banda."})
        if u["breakEvenAcos"] * 100 < d["econ"]["acosTarget"] + 5:
            add({"id": "econ.be", "section": "price", "severity": "warn", "title": "ACoS de equilibrio justo", "why": f"Equilibrio {u['breakEvenAcos'] * 100:.1f} % vs objetivo {d['econ']['acosTarget']} %: poco colchón de lanzamiento.", "fix": "Reserva más margen para publicidad."})
        for w in u["warnings"]:
            add({"id": "econ.assumption", "section": "price", "severity": "warn", "title": "Supuesto económico", "why": w, "fix": "Verifícalo antes de operar."})
    _eval_checklist(d["regulatory"], "regulatory", F, "Regulatorio")
    claims = d.get("claims") or []
    for i, c in enumerate(claims):
        if not (c.get("evidence") or "").strip():
            add({"id": f"claims.{i}", "section": "regulatory", "severity": "block", "title": f"Claim sin respaldo: «{(c.get('text') or '')[:60]}»", "why": "Todo claim del listing necesita evidencia documental.", "fix": "Adjunta el estudio/ensayo/autorización o elimina el claim."})
    declared = " ".join((c.get("text") or "").lower() for c in claims)
    cont = d.get("content") or {}
    listing = ((cont.get("title") or {}).get("evidence") or "") + " " + ((cont.get("bullets") or {}).get("evidence") or "")
    for w in RISKY:
        if w in listing.lower() and w not in declared:
            add({"id": f"claims.risky.{w}", "section": "regulatory", "severity": "warn", "title": f"Posible claim de riesgo en el listing: «{w}»", "why": "Términos de este tipo suelen requerir respaldo o están restringidos.", "fix": "Añádelo a la lista de claims con evidencia o reescribe el texto."})
    S["regulatory"] = {"critical": sum(1 for x in d["regulatory"].values() if x.get("critical"))}
    _eval_checklist(d["content"], "content", F, "Contenido")
    L = d["logistics"]
    _eval_checklist(L["items"], "logistics", F, "Logística")
    sa, fc = L.get("stockAvailable"), L.get("forecastUnitsMonth")
    if not _num(sa) or sa < 0:
        add({"id": "log.stock", "section": "logistics", "severity": "block", "title": "Stock disponible no informado", "why": "No se puede comprobar la cobertura de lanzamiento.", "fix": "Indica unidades disponibles (incl. entradas confirmadas)."})
    elif not _num(fc) or fc <= 0:
        add({"id": "log.forecast", "section": "logistics", "severity": "block", "title": "Previsión de ventas no informada", "why": "Sin previsión no hay cobertura calculable.", "fix": "Indica unidades/mes previstas."})
    else:
        need = math.ceil((fc / 30) * L["coverTargetDays"]); S["stockNeed"] = need
        if sa < need:
            add({"id": "log.short", "section": "logistics", "severity": "block", "title": "Stock insuficiente para el lanzamiento", "why": f"Necesitas {need} uds para {L['coverTargetDays']} días ({fc}/mes) y hay {sa}: faltan {need - sa}.", "fix": "Aumenta el stock o retrasa el lanzamiento."})
        lt = L.get("leadTimeDays")
        if not _num(lt) or lt <= 0:
            add({"id": "log.lead", "section": "logistics", "severity": "warn", "title": "Plazo de reposición no informado", "why": "No se puede comprobar riesgo de rotura.", "fix": "Indica el plazo de reposición en días."})
        elif lt > L["coverTargetDays"]:
            add({"id": "log.leadlong", "section": "logistics", "severity": "warn", "title": "Reposición más lenta que la cobertura", "why": f"Plazo {lt} d > cobertura {L['coverTargetDays']} d: rotura probable.", "fix": "Aumenta la cobertura inicial."})
    rank = {"nogo": 0, "block": 1, "warn": 2}
    F.sort(key=lambda f: rank[f["severity"]])
    n = lambda s: sum(1 for f in F if f["severity"] == s)
    decision = "NO-GO" if n("nogo") else "REVISAR" if n("block") else "GO"
    ss = {}
    for s in ("benchmark", "demand", "price", "regulatory", "content", "logistics"):
        fs = [f for f in F if f["section"] == s]
        ss[s] = "nogo" if any(f["severity"] == "nogo" for f in fs) else "block" if any(f["severity"] == "block" for f in fs) else "warn" if fs else "ok"
    summary = ("Sin bloqueos. GO no publica nada: la publicación sigue requiriendo aprobación explícita." if decision == "GO"
               else f"{n('block')} bloqueo(s) por resolver antes de lanzar." if decision == "REVISAR" else f"{n('nogo')} causa(s) de inviabilidad económica/competitiva.")
    return {"decision": decision, "findings": F, "counts": {"nogo": n("nogo"), "block": n("block"), "warn": n("warn")}, "sections": S, "sectionStatus": ss, "today": today, "summary": summary}
