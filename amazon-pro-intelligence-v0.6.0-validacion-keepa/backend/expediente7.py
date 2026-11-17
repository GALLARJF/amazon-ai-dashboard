"""V0.7.0 (V7-02) — Expediente comercial ACTIVCORE v0.7. Solo lectura de lo ya registrado: sin red, sin gasto, sin claves.
Reglas: lo que falta se muestra como hueco (nunca se rellena); el veredicto NUNCA es GO (máximo «EVALUAR POR PAÍSES»); cada dato lleva fuente, fecha y clase;
los textos externos (títulos de competidores) no entran en el expediente: solo agregados."""
from . import keepa_real as KR
from .director import sanitize

NOT_COVERED = ["DE", "FR", "IT", "UK", "NL", "PL"]
LIMITS = ["Windows y conexiones externas (Keepa en vivo, Amazon, OpenAI) NO verificadas en este expediente: solo datos ya registrados.",
          "Veredicto de solo-estado-de-datos: no inventa demanda, ventas ni cuota de mercado.",
          "Ningún borrador está publicado ni aprobado; publicar, fijar precios o activar anuncios exige aprobación humana."]


def verdict_for(blockers):
    """Nunca devuelve GO: con bloqueos → NO DECIDIBLE; sin ellos, como máximo EVALUAR POR PAÍSES (decisión humana)."""
    return "NO DECIDIBLE" if blockers else "EVALUAR POR PAÍSES"


def _src(field, source, date, cls): return {"field": field, "source": str(source or "s/f")[:160], "date": str(date or "s/f")[:10] if date else "s/f", "class": cls}


def _aggregate_reqs(svc, countries):
    comp = svc.compliance(); out = []
    for i, text, ref in svc.items:
        sts = [((comp.get(c) or {}).get(i) or {}).get("state", "PENDIENTE") for c in countries]
        sts = [x for x in sts if x != "NO_APLICA"]
        st = "NO_CUMPLE" if "NO_CUMPLE" in sts else ("PENDIENTE" if (not sts or "PENDIENTE" in sts) else "OK")
        out.append({"id": i, "text": text, "reference": ref, "state": st, "countries_pending": sum(1 for x in sts if x == "PENDIENTE")})
    return out


def build(APP, pid):
    if not isinstance(pid, str) or not APP["catalog"].get(pid): raise LookupError("producto inexistente")
    la = APP["launch"]; p = APP["catalog"].get(pid); svc = la.svc_for(pid); full = la.build(pid); fs = {s["id"]: s for s in full["sections"]}
    # 1 producto
    fd = fs["ficha"]["data"]; pv = (fd["pvp"] or {}).get("REF") or {}; cg = (fd["costs"] or {}).get("cogs") if isinstance(fd["costs"], dict) else None; stock = fd["stock"] or {}; fmt = fd["format"] or {}
    prod = {"id": fd["id"], "name": fd["name"], "brand": fd["brand"], "category": fd["category"], "format_ml": fmt.get("content"), "pvp_eur": pv.get("v"),
            "pvp_state": ("%s (no aprobado)" % pv.get("status") if pv.get("status") == "PROPUESTO" else str(pv.get("status") or "NO DISPONIBLE")), "cogs_eur": (cg or {}).get("v"), "cogs_state": (cg or {}).get("status") or "NO DISPONIBLE",
            "stock_units": stock.get("v"), "stock_state": stock.get("status") or "NO DISPONIBLE", "commercial_state": fd["commercial_state"], "missing": list(fs["ficha"].get("missing") or [])}
    ps = [_src("formato", fmt.get("source"), fmt.get("date") or pv.get("date"), fmt.get("status") or "DOCUMENTADO"), _src("pvp", pv.get("source"), pv.get("date"), pv.get("status") or "NO DISPONIBLE"),
          _src("coste unitario", (cg or {}).get("source"), (cg or {}).get("date"), prod["cogs_state"]), _src("stock", stock.get("source"), stock.get("date"), prod["stock_state"])]
    stock_ok = stock.get("v") is not None and stock.get("status") in ("VERIFICADO", "DOCUMENTADO") and prod["cogs_state"] in ("VERIFICADO", "DOCUMENTADO")
    sec_prod = {"id": "producto", "title": "Producto", "state": "PARCIAL" if prod["missing"] or not stock_ok else "COMPLETO", "data": prod, "sources": ps}
    # 2 economía
    rows = [{"country": r["country"], "state": r["state"], "missing": r["missing"] or [], "contribution": r["contribution"], "margin": r["margin"], "breakeven_acos": r["breakeven_acos"]} for r in fs["economia"]["rows"]]
    gaps = list(dict.fromkeys(g for r in rows for g in r["missing"])); econ_ok = bool(rows) and all(r["state"] != "NO CALCULABLE" for r in rows)
    sec_econ = {"id": "economia", "title": "Economía", "state": "CALCULADO" if econ_ok else "NO CALCULABLE", "data": {"pvp_ref": fs["economia"]["pvp_ref"], "mode": fs["economia"]["mode"], "rows": rows, "gaps": gaps,
                "note": "Contribución antes de publicidad. Los costes logísticos ausentes NO se rellenan por defecto."}, "sources": [_src("PVP de referencia", pv.get("source"), pv.get("date"), pv.get("status") or "NO DISPONIBLE"), _src("coste unitario", (cg or {}).get("source"), (cg or {}).get("date"), prod["cogs_state"]),
                _src("costes logísticos y comisión", "Sin documentar en el sistema", (cg or {}).get("date") or pv.get("date"), "NO DISPONIBLE")]}
    # 3 mercado (Keepa real ya obtenido; sin red)
    k = KR.load(pid); s = k["summary"]; real = k["state"] == "REAL"
    conf = sum(1 for c in k["competitors"] if c.get("comparability_confirmed") not in (None, "NO CONFIRMADA"))
    mk = {"n": s["n"], "domain": k["domain"], "source": k["source"], "consulted_at": k["consulted_at"], "price_median": s.get("price_median"), "price_min": s.get("price_min"), "price_max": s.get("price_max"), "n_stale": s.get("n_stale", 0),
          "per_100ml_median": s.get("per_100ml_median"), "comparability_confirmed": conf, "own_vs_median": (k.get("own") or {}).get("vs_median_per100ml"), "limits": list(k["limits"]), "why": k["why"],
          "coverage": "ES (amazon.es)" if real else "NINGUNA", "not_covered": NOT_COVERED if real else ["ES"] + NOT_COVERED, "network_calls": k["network_calls"], "tokens_spent_now": k["tokens_spent_now"]}
    sec_mk = {"id": "mercado", "title": "Mercado", "state": "REAL (parcial: solo ES, comparabilidad sin confirmar)" if real else k["state"], "data": mk,
              "sources": [_src("competidores, precio y BSR", k["source"], k["consulted_at"], "REAL")] if real else []}
    # 4 regulatorio
    cv = fs["cumplimiento"]; reqs = _aggregate_reqs(svc, [c["country"] for c in cv["by_country"]])
    reg = {"flow": cv["flow"], "open": cv["open"], "ok": cv["ok"], "by_country": cv["by_country"], "requirements": reqs, "verdict": cv["verdict"], "limit": cv["limit"]}
    sec_reg = {"id": "regulatorio", "title": "Regulatorio", "state": "PUBLICACIÓN BLOQUEADA" if cv["open"] else "REVISAR CON RESPONSABLE REGULATORIO", "data": reg,
               "sources": [_src("checklist de requisitos", "Lista de requisitos del expediente (preliminar, sin dictamen legal)", (fd.get("regulatory") or {}).get("date") or pv.get("date"), "PRELIMINAR"),
                           _src("estado regulatorio del producto", ((p.get("regulatory") or {}).get("note")) or "Catálogo", (p.get("regulatory") or {}).get("date") or pv.get("date"), (p.get("regulatory") or {}).get("state") or "PENDIENTE")]}
    # 5 decisión
    reasons = []
    if not econ_ok: reasons.append("Economía NO CALCULABLE: faltan %s." % (", ".join(gaps) or "costes documentados"))
    if cv["open"]: reasons.append("Cumplimiento: %d requisitos sin evidencia bloquean la publicación." % cv["open"])
    if not real: reasons.append("Mercado SIN DATOS: no hay consulta real para este producto.")
    elif conf == 0: reasons.append("Comparabilidad NO CONFIRMADA en %d competidores: las medianas no son base de decisión." % s["n"])
    if not stock_ok: reasons.append("Stock y coste unitario históricos sin revalidar.")
    ver = verdict_for(reasons)
    sec_dec = {"id": "decision", "title": "Decisión", "state": ver, "data": {"verdict": ver, "go": False, "reasons": reasons, "rule": "Nunca GO por defecto: lanzar es una decisión humana con datos completos."},
               "sources": [_src("veredicto", "Derivado del estado de las secciones 1–4", pv.get("date"), "DERIVADO")]}
    # desbloqueos
    cand = []
    if not econ_ok: cand.append(("U-LOG", "Documentar costes logísticos reales (tarifa FBA/FBM, transporte, preparación, almacenamiento, devoluciones)", "Propietario de producto / logística (AHT)", 0.0, 0, ["economia", "decision"], False))
    if cv["open"]: cand.append(("U-REG", "Aportar evidencias regulatorias por país (PIF, CPSR, persona responsable, CPNP, etiquetado)", "Responsable regulatorio (AHT)", 0.0, 0, ["regulatorio", "decision"], True))
    if not real or conf == 0: cand.append(("U-CMP", "Confirmar a mano la comparabilidad de los competidores" if real else "Realizar una consulta real autorizada de competidores", "Analista de mercado (AHT)", 0.0, 0, ["mercado", "decision"], False))
    if not stock_ok: cand.append(("U-STK", "Revalidar stock actual y coste unitario del producto", "Propietario de producto (AHT)", 0.0, 0, ["producto", "economia"], False))
    try: tk = int((APP["disc"].plan(pid, None, "normal", 20) or {}).get("estimated_tokens_max") or 0)
    except Exception: tk = 0
    if real: cand.append(("U-KPA", "Ampliar la investigación Keepa a DE/FR/IT (consume tokens: requiere aprobación)", "Aprobador (AHT)", 0.0, max(tk, 1), ["mercado"], True))
    unlocks = [{"id": i, "title": t, "owner": o, "cost_eur": c, "cost_known": c == 0.0 and tkn == 0 and not ap, "keepa_tokens": tkn, "unblocks": ub, "value": len(ub), "requires_approval": ap or c > 0 or tkn > 0} for i, t, o, c, tkn, ub, ap in cand]
    unlocks.sort(key=lambda x: (-x["value"], x["cost_eur"], x["keepa_tokens"], x["id"]))
    for n, x in enumerate(unlocks, 1): x["rank"] = n
    for x in unlocks:
        x["cost_note"] = "Coste externo no estimado: lo determina el propietario" if x["id"] == "U-REG" else ("Consume tokens Keepa; 0 € directos" if x["keepa_tokens"] else "Trabajo interno; 0 € de desembolso")
    sections = [sec_prod, sec_econ, sec_mk, sec_reg, sec_dec]
    return {"product_id": pid, "name": p["name"], "sections": sections, "verdict": ver, "unlocks": unlocks, "limits": list(LIMITS), "network_calls": k["network_calls"], "tokens_spent_now": k["tokens_spent_now"], "cost_now_eur": 0}


def _v(x):
    if x is None or x == "": return "NO DISPONIBLE"
    return str(x)


def to_markdown(d):
    L = ["# Expediente comercial · %s" % d["name"], "", "**Veredicto:** %s (nunca GO por defecto; decisión humana)" % d["verdict"], "**Gasto de esta consulta:** %s € · %s tokens Keepa · %s llamadas de red" % (d["cost_now_eur"], d["tokens_spent_now"], d["network_calls"]), ""]
    for n, s in enumerate(d["sections"], 1):
        L += ["## %d · %s" % (n, s["title"]), "**Estado:** %s" % s["state"], ""]
        for k, v in s["data"].items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                L.append("**%s:**" % k); L += ["- " + "; ".join("%s=%s" % (a, _v(b) if not isinstance(b, list) else ", ".join(map(str, b)) or "—") for a, b in r.items()) for r in v]
            elif isinstance(v, list): L.append("**%s:** %s" % (k, "; ".join(map(str, v)) or "—"))
            else: L.append("**%s:** %s" % (k, _v(v)))
        if s["sources"]:
            L += ["", "**Fuentes:**"] + ["- %s — %s (%s) [%s]" % (x["field"], x["source"], x["date"], x["class"]) for x in s["sources"]]
        L.append("")
    L += ["## Desbloqueos priorizados", ""]
    for x in d["unlocks"]:
        L.append("%d. %s — propietario: %s · coste: %s € (%s) · tokens Keepa: %d · desbloquea: %s%s" % (x["rank"], x["title"], x["owner"], x["cost_eur"], x["cost_note"], x["keepa_tokens"], ", ".join(x["unblocks"]), " · REQUIERE APROBACIÓN" if x["requires_approval"] else ""))
    L += ["", "## Límites", ""] + ["- " + x for x in d["limits"]]
    return sanitize("\n".join(L), 200000) + "\n"
