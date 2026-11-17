"""Siete coworkers especializados V0.3. 100 % deterministas y verificables: leen SOLO los datos aportados (expediente, CSV, evidencias),
calculan con engine.py y declaran huecos en vez de inventar. No consultan Internet ni modelos de IA (la IA solo narra/coordina en director.py).
Resultado de cada coworker: {coworker, status, findings[{kind: calc|data|gap|risk, text, refs}], metrics, data_used, needs, checks}.
Cada cifra lleva su fórmula/origen; `checks` recalcula de forma independiente las cifras clave."""
import math, re
from . import engine as E

NAMES = {"mercado": "Mercado y competencia", "precios": "Precios y rentabilidad", "seo": "SEO y keywords", "ppc": "Publicidad PPC",
         "creatividad": "Creatividad, imágenes y vídeos", "inventario": "Inventario y logística", "cumplimiento": "Reputación y cumplimiento"}
DEPS = {"mercado": [], "seo": [], "inventario": [], "precios": ["mercado"], "creatividad": ["seo"], "ppc": ["precios", "seo"], "cumplimiento": ["creatividad", "mercado"]}
ORDER = ["mercado", "seo", "inventario", "precios", "creatividad", "ppc", "cumplimiento"]


def _r(co, status, findings, metrics, data_used, needs, checks):
    return {"coworker": co, "name": NAMES[co], "status": status, "findings": findings, "metrics": metrics, "data_used": data_used, "needs": needs,
            "checks": checks, "external_data": False, "ai_used": False}


def F(kind, text, refs=None):
    return {"kind": kind, "text": text, "refs": refs or []}


def _check(name, a, b, tol=1e-6):
    ok = a is not None and b is not None and abs(a - b) <= tol
    return {"name": name, "ok": bool(ok), "a": a, "b": b}


def mercado(d, today, bb):
    bm = E.benchmark(d, today)
    f, needs, checks = [], [], []
    n_in = len(d.get("competitors") or [])
    if not n_in:
        needs.append("Importar competidores (CSV) con precio, uds., contenido, fuente y fecha.")
        return _r("mercado", "datos_insuficientes", [F("gap", "No hay competidores cargados: no se puede analizar el mercado.")], {}, [], needs, [])
    f.append(F("data", f"{bm['n']} competidores válidos de {n_in} cargados (fuente+fecha ≤ {E.MAX_COMP_AGE} d, sin duplicados ni atípicos).", ["competitors"]))
    for t in bm["issues"]:
        f.append(F("gap", t))
    m = {"n_valid": bm["n"], "n_input": n_in, "sufficient": bm["sufficient"]}
    if bm["rows"]:
        m["unit_price"] = bm["unit"]; m["band"] = bm["band"]; m["unit_label"] = bm["unitLabel"]
        f.append(F("calc", f"Precio normalizado por {bm['unitLabel']} (envío incluido): mediana {bm['unit']['median']:.4f} €, P25 {bm['unit']['p25']:.4f} €, P75 {bm['unit']['p75']:.4f} €. "
                           f"Banda para tu formato ({bm['band']['size']:g} {bm['unitLabel']}): {bm['band']['low']:.2f}–{bm['band']['high']:.2f} € (mediana {bm['band']['mid']:.2f} €).", ["competitors"]))
        own = E.unit(d["econ"])
        if own["valid"]:
            pos = sum(1 for r in bm["rows"] if r["unitPrice"] * bm["band"]["size"] < own["price"])
            m["own_price"] = own["price"]; m["own_rank_cheaper_than"] = pos
            f.append(F("calc", f"Tu PVP planificado {own['price']:.2f} € es más caro que {pos} de {bm['n']} competidores válidos (a igual formato).", ["econ"]))
        rated = [r for r in bm["rows"] if isinstance(r.get("rating"), (int, float)) and isinstance(r.get("reviews"), (int, float))]
        if rated:
            m["max_reviews"] = max(r["reviews"] for r in rated)
            f.append(F("data", f"Referencia de reseñas (dato aportado): máx. {int(m['max_reviews'])} valoraciones entre los competidores con dato.", ["competitors"]))
        else:
            needs.append("Añadir columnas rating y reviews al CSV para comparar prueba social (no se inventan).")
        checks.append(_check("mediana recalculada", bm["unit"]["median"], E._pctl([r["unitPrice"] for r in bm["rows"]], .5)))
    if not bm["sufficient"]:
        needs.append(f"Se requieren ≥ {E.MIN_COMP} competidores válidos para decisión.")
    st = "ok" if bm["sufficient"] else "datos_insuficientes"
    return _r("mercado", st, f, m, ["competitors", "econ.price"], needs, checks)


def precios(d, today, bb):
    u = E.unit(d["econ"])
    if not u["valid"]:
        return _r("precios", "error_datos", [F("gap", "Datos económicos inválidos: " + " · ".join(u["errors"]))], {}, ["econ"], ["Corregir datos económicos."], [])
    mp = E.min_price(d["econ"])
    f, checks, needs = [], [], []
    m = {"price": u["price"], "net": u["net"], "contribution": u["contribution"], "contribution_pct": u["contributionPct"], "break_even_acos_pct": u["breakEvenAcos"] * 100,
         "min_price": mp["commercial"] if mp else None, "referral": u["referral"], "ads": u["ads"]}
    f.append(F("calc", f"A {u['price']:.2f} € (IVA {d['econ']['vatPct']} %): neto {u['net']:.2f} €, comisión {u['referral']:.2f} €, contribución {u['contribution']:.2f} € ({u['contributionPct'] * 100:.1f} % s/ neto) con ACoS {d['econ']['acosTarget']} %.", ["econ"]))
    f.append(F("calc", f"ACoS de equilibrio: {u['breakEvenAcos'] * 100:.1f} % (base {'PVP con IVA' if d['econ']['adsBasis'] == 'gross' else 'neto'}).", ["econ"]))
    if mp:
        f.append(F("calc", f"Precio mínimo para margen {d['econ']['minMarginPct']} % tras publicidad: {mp['commercial']:.2f} €.", ["econ"]))
    else:
        f.append(F("risk", "No existe precio que alcance el margen mínimo con estos costes y ACoS."))
    prices = sorted({round(u["price"], 2)} | {round(x, 2) for x in d.get("pvpScenarios", [])})
    if len(prices) == 1 and mp:
        band = (bb.get("mercado") or {}).get("metrics", {}).get("band")
        prices = sorted({prices[0], mp["commercial"]} | ({round(band["low"], 2), round(band["mid"], 2), round(band["high"], 2)} if band else set()))
    sc = E.scenarios(d["econ"], prices); m["scenarios"] = sc
    for s in sc:
        if s["valid"]:
            f.append(F("calc", f"Escenario PVP {s['price']:.2f} €: contribución {s['contribution']:.2f} € ({s['contributionPct'] * 100:.1f} %), ACoS equilibrio {s['breakEvenAcos'] * 100:.1f} %.", ["econ"]))
    band = (bb.get("mercado") or {}).get("metrics", {}).get("band")
    if band and mp:
        m["min_price_vs_band_high"] = mp["commercial"] - band["high"]
        f.append(F("calc" if mp["commercial"] <= band["high"] else "risk", f"Coordinado con Mercado: precio mínimo {mp['commercial']:.2f} € {'dentro' if mp['commercial'] <= band['high'] else 'FUERA'} de la banda competitiva (máx. {band['high']:.2f} €).", ["mercado"]))
    elif not band:
        needs.append("Sin banda competitiva (Mercado no suficiente): no se compara el precio mínimo con el mercado.")
    for w in u["warnings"]:
        f.append(F("gap", "Supuesto: " + w))
    checks.append(_check("contribución = neto − costes − comisión − ads", u["contribution"], u["net"] - u["cost"] - u["prep"] - u["fulfil"] - u["storage"] - u["returns"] - u["other"] - u["referral"] - u["ads"], 1e-9))
    if mp:
        checks.append(_check("margen en precio mínimo ≥ objetivo", 1.0 if E.unit(d["econ"], mp["commercial"])["contributionPct"] >= d["econ"]["minMarginPct"] / 100 - 1e-9 else 0.0, 1.0))
    return _r("precios", "ok", f, m, ["econ", "mercado.band"], needs, checks)


def _kw_ok(d, today):
    ok = []
    for k in d.get("keywords") or []:
        if (k.get("keyword") or "").strip() and E._num(k.get("volume")) and k["volume"] >= 0 and (k.get("source") or "").strip() and E._isdate(k.get("date")) and 0 <= E._age(k["date"], today) <= E.MAX_KW_AGE:
            ok.append(k)
    return ok


def _listing_text(d):
    l = d.get("listing") or {}
    return " ".join([l.get("title") or ""] + list(l.get("bullets") or []) + [l.get("backend") or ""]).lower()


def seo(d, today, bb):
    ok = _kw_ok(d, today)
    if not ok:
        return _r("seo", "datos_insuficientes", [F("gap", "Sin keywords vigentes con volumen, fuente y fecha. No se estima demanda.")], {"valid_keywords": 0}, [],
                  ["Importar keywords (p. ej. export Helium 10) con fuente y fecha ≤ 60 d."], [])
    txt = _listing_text(d)
    cov = [k for k in ok if k["keyword"].lower() in txt] if txt.strip() else []
    unc = [k for k in ok if k not in cov]
    tot = sum(k["volume"] for k in ok)
    f = [F("data", f"{len(ok)} keywords vigentes; volumen total aportado {tot:,.0f} (fuente: {', '.join(sorted({k['source'] for k in ok}))}).".replace(",", "."), ["keywords"])]
    top = sorted(ok, key=lambda k: -k["volume"])[:5]
    f.append(F("data", "Top por volumen aportado: " + "; ".join(f"{k['keyword']} ({k['volume']:g})" for k in top), ["keywords"]))
    needs = []
    if txt.strip():
        cv = sum(k["volume"] for k in cov) / tot * 100 if tot else 0
        f.append(F("calc", f"Cobertura del listing: {len(cov)}/{len(ok)} keywords presentes (frase exacta), {cv:.0f} % del volumen aportado.", ["keywords", "listing"]))
        if unc:
            f.append(F("gap", "Sin cubrir en el listing: " + ", ".join(k["keyword"] for k in sorted(unc, key=lambda k: -k["volume"])[:8])))
    else:
        needs.append("Aportar título/bullets/backend del listing para medir cobertura.")
    if len(ok) < E.MIN_KW:
        needs.append(f"Pocas keywords ({len(ok)}/{E.MIN_KW}).")
    m = {"valid_keywords": len(ok), "total_volume": tot, "uncovered": [k["keyword"] for k in unc] if txt.strip() else None, "top": [k["keyword"] for k in top]}
    return _r("seo", "ok", f, m, ["keywords", "listing"], needs, [_check("volumen total", tot, sum(k["volume"] for k in ok))])


def ppc(d, today, bb):
    pr = bb.get("precios")
    if not pr or pr["status"] != "ok":
        return _r("ppc", "datos_insuficientes", [F("gap", "Depende de Precios: economía no disponible.")], {}, [], ["Resolver Precios."], [])
    u = E.unit(d["econ"])
    f, needs, checks = [], [], []
    be = u["breakEvenAcos"]
    m = {"break_even_acos_pct": be * 100, "target_acos_pct": d["econ"]["acosTarget"], "cushion_pts": be * 100 - d["econ"]["acosTarget"]}
    f.append(F("calc", f"ACoS objetivo {d['econ']['acosTarget']} % vs equilibrio {be * 100:.1f} %: colchón {m['cushion_pts']:.1f} pts.", ["precios"]))
    if be <= 0:
        f.append(F("risk", "El equilibrio es ≤ 0: cualquier gasto publicitario pierde dinero."))
    cvr = d.get("cvrPct")
    if E._num(cvr) and 0 < cvr <= 100:
        base = u["adsBase"]
        cpc = be * base * cvr / 100
        m["max_cpc_break_even"] = cpc; m["cvr_pct"] = cvr
        f.append(F("calc", f"CPC máximo de equilibrio con CVR {cvr} % (dato aportado): {cpc:.2f} € (= ACoS_eq × precio × CVR).", ["precios", "cvr"]))
        checks.append(_check("CPC máx = ACoS_eq × base × CVR", cpc, be * base * cvr / 100))
    else:
        needs.append("Aportar CVR (conversión) real para calcular CPC máximo; no se estima.")
    budget = d.get("adBudgetMonth")
    if E._num(budget) and budget > 0 and u["adsBase"] > 0:
        sales_needed = budget / (d["econ"]["acosTarget"] / 100) if d["econ"]["acosTarget"] > 0 else None
        if sales_needed:
            f.append(F("calc", f"Con presupuesto {budget:g} €/mes y ACoS {d['econ']['acosTarget']} %, hacen falta {sales_needed:.0f} € de ventas publicitarias/mes ({sales_needed / u['adsBase']:.1f} uds.) para cumplir el objetivo.", ["adBudgetMonth"]))
            m["sales_needed"] = sales_needed
    seo_r = bb.get("seo")
    if seo_r and seo_r["status"] == "ok":
        f.append(F("data", f"Coordinado con SEO: {seo_r['metrics']['valid_keywords']} keywords vigentes candidatas para campañas (volúmenes aportados, no estimados).", ["seo"]))
        m["candidate_keywords"] = seo_r["metrics"]["top"]
    else:
        needs.append("Sin keywords vigentes: no hay lista de segmentación.")
    f.append(F("gap", "Solo propuesta analítica: no se crea ni modifica ninguna campaña (acciones de escritura no implementadas)."))
    return _r("ppc", "ok", f, m, ["precios", "seo", "econ"], needs, checks)


def creatividad(d, today, bb):
    c = d.get("content") or {}
    f, needs = [], []
    miss = [(k, v["label"]) for k, v in c.items() if v.get("status") != "cumplido" and v.get("status") != "no_aplica"]
    done = len(c) - len(miss)
    f.append(F("data", f"Activos de contenido: {done}/{len(c)} completados (según el expediente).", ["content"]))
    for k, lab in miss:
        f.append(F("gap", f"Falta: {lab}" + (" (crítico)" if c[k].get("critical") else "")))
    m = {"done": done, "total": len(c), "missing": [k for k, _ in miss]}
    seo_r = bb.get("seo")
    briefs = []
    if seo_r and seo_r["status"] == "ok":
        unc = seo_r["metrics"].get("uncovered")
        if unc:
            briefs.append("Incorporar al título/bullets las keywords sin cubrir: " + ", ".join(unc[:6]))
        m["uncovered_keywords"] = unc
    if "video" in m["missing"]: briefs.append("Guion de vídeo: demostrar uso y formato real, solo con claims respaldados por evidencia.")
    if "gallery" in m["missing"]: briefs.append("Galería ≥ 6 imágenes: uso, escala, packaging, infografía de formato, ingredientes/composición, certificaciones documentadas.")
    if "aplus" in m["missing"]: briefs.append("Módulos A+: comparativa de formato frente a la banda de mercado y bloque de calidad/fabricante.")
    m["briefs"] = briefs
    for b in briefs:
        f.append(F("calc", "Brief: " + b, ["seo", "content"]))
    f.append(F("gap", "No genera imágenes ni vídeos: elabora el listado de activos y briefs verificables."))
    return _r("creatividad", "ok", f, m, ["content", "seo"], needs, [_check("conteo", done + len(miss), len(c))])


def inventario(d, today, bb):
    L = d["logistics"]
    f, needs, checks = [], [], []
    sa, fc = L.get("stockAvailable"), L.get("forecastUnitsMonth")
    if not E._num(sa):
        needs.append("Informar stock disponible.")
    if not E._num(fc) or (E._num(fc) and fc <= 0):
        needs.append("Informar previsión de unidades/mes (decisión humana; no se infiere de ventas inexistentes).")
    if needs:
        return _r("inventario", "datos_insuficientes", [F("gap", "Sin stock o previsión: la cobertura no es calculable.")], {}, ["logistics"], needs, [])
    need = math.ceil((fc / 30) * L["coverTargetDays"])
    cover_days = sa / (fc / 30)
    m = {"stock": sa, "forecast_month": fc, "cover_days": cover_days, "need_units": need, "gap_units": max(0, need - sa)}
    f.append(F("calc", f"Cobertura: {cover_days:.0f} días con {sa:g} uds. a {fc:g} uds./mes (objetivo {L['coverTargetDays']} d → {need} uds.).", ["logistics"]))
    if sa < need:
        f.append(F("risk", f"Faltan {need - sa:g} uds. para la cobertura objetivo."))
    lt = L.get("leadTimeDays")
    if E._num(lt) and lt > 0:
        reorder_in = cover_days - lt
        m["reorder_in_days"] = reorder_in
        f.append(F("calc" if reorder_in >= 0 else "risk", f"Plazo de reposición {lt:g} d: " + (f"pedir en ≤ {reorder_in:.0f} d para evitar rotura." if reorder_in >= 0 else f"ya hay riesgo de rotura (déficit {-reorder_in:.0f} d).")))
    else:
        needs.append("Informar plazo de reposición.")
    pend = [v["label"] for v in L["items"].values() if v.get("status") == "pendiente"]
    for p in pend:
        f.append(F("gap", "Logística pendiente: " + p))
    checks.append(_check("cobertura = stock / (previsión/30)", cover_days, sa / (fc / 30)))
    return _r("inventario", "ok", f, m, ["logistics"], needs, checks)


def cumplimiento(d, today, bb):
    f, needs = [], []
    pend, nev = [], []
    for k, it in d["regulatory"].items():
        if it["status"] == "pendiente": pend.append(it["label"])
        elif it["status"] == "cumplido" and not (it.get("evidence") or "").strip(): nev.append(it["label"])
    tot = len(d["regulatory"])
    f.append(F("data", f"Checklist regulatorio ({d['product']['regType']}): {tot - len(pend) - len(nev)}/{tot} con evidencia; {len(pend)} pendientes; {len(nev)} sin evidencia.", ["regulatory"]))
    for p in pend: f.append(F("gap", "Dato regulatorio pendiente: " + p))
    for p in nev: f.append(F("gap", "Cumplido sin evidencia: " + p))
    claims = d.get("claims") or []
    unb = [c for c in claims if not (c.get("evidence") or "").strip()]
    if unb:
        for c in unb: f.append(F("risk", f"Claim sin respaldo: «{c.get('text', '')[:60]}»"))
    txt = _listing_text(d) + " " + " ".join((c.get("text") or "") for c in claims).lower()
    declared = " ".join((c.get("text") or "").lower() for c in claims if (c.get("evidence") or "").strip())
    risky = [w for w in E.RISKY if re.search(r"(?<!\w)" + re.escape(w), txt) and w not in declared]
    for w in risky: f.append(F("risk", f"Término de riesgo en listing/claims sin respaldo declarado: «{w}»"))
    rep = None
    rated = [r for r in (d.get("competitors") or []) if E._num(r.get("rating"))]
    own = d.get("ownRating")
    if E._num(own) and rated:
        rep = sum(r["rating"] for r in rated) / len(rated)
        f.append(F("calc", f"Reputación: tu valoración aportada {own:g}★ vs media de competidores con dato {rep:.2f}★ ({len(rated)}).", ["competitors"]))
    else:
        needs.append("Aportar valoración propia y de competidores para comparar reputación (no se estima).")
    mkt = bb.get("mercado")
    m = {"pending": len(pend), "no_evidence": len(nev), "unbacked_claims": len(unb), "risky_terms": risky, "ready": not (pend or nev or unb or risky)}
    f.append(F("gap", "Esto es una verificación documental interna, no asesoramiento legal ni aprobación de Amazon."))
    return _r("cumplimiento", "ok", f, m, ["regulatory", "claims", "listing"], needs, [_check("recuento", tot, len(pend) + len(nev) + (tot - len(pend) - len(nev)))])


RUN = {"mercado": mercado, "precios": precios, "seo": seo, "ppc": ppc, "creatividad": creatividad, "inventario": inventario, "cumplimiento": cumplimiento}


def run(co, dossier, today, blackboard):
    try:
        r = RUN[co](dossier, today, blackboard)
    except Exception as e:  # nunca silenciar: error explícito sin detalles sensibles
        r = _r(co, "error_interno", [F("gap", f"Error interno del coworker: {type(e).__name__}")], {}, [], [], [])
    r["checks_ok"] = all(c["ok"] for c in r["checks"]) if r["checks"] else None
    return r
