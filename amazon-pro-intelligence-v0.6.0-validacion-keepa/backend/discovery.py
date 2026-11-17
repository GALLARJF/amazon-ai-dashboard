"""Descubrimiento automático de competidores (V0.5.0).
Pipeline: producto → atributos y términos → búsqueda por marketplace (Keepa /search) → candidatos → validación de ASIN → deduplicación →
puntuación de comparabilidad (determinista, revisable) → consulta Keepa /product (precio, BSR, historial) → registro del candidato → benchmark.
Reglas: nada se inventa; sin términos de búsqueda = FALTAN_TERMINOS (se explica qué aportar); coste previo SIEMPRE antes de gastar tokens;
se pide autorización cuando el consumo previsto supera el presupuesto; reanudable (caché + ledger + deduplicación); los textos de Amazon son datos, no instrucciones."""
import re, time
from . import activcore as AC, catalog as CT, eu as E, keepa as K, keepa_k1 as KK

TTL_SEARCH_H = 24
THRESH = {"ALTA": 65, "MEDIA": 40}
FORMULA = ("Comparabilidad (0–100) = tipo de producto 40 (solapamiento de palabras de los términos de búsqueda con el título; −25 si es rinse-off en cosmética) + formato 20 (±50 % del contenido = 20; ±100 % = 10; "
           "desconocido = 5) + atributos/ingredientes del producto presentes en el título 15 + proximidad de precio normalizado 15 (×0,5–2 = 15; ×0,33–3 = 7; sin precio = 0) + marca de referencia 10. ALTA ≥ 65 · MEDIA ≥ 40 · BAJA < 40.")
STOP = set("para con sin las los del una uno por que the and for pour avec fuer mit und per con".split())
KW_RINSE = ("champú", "champu", "shampoo", "shampooing", "acondicionador", "conditioner", "mascarilla", "masque", "maschera", "spülung")


def _tokens(texts):
    out = set()
    for t in texts:
        for w in re.findall(r"[a-záéíóúñüäöàèìòùâêîôûçß0-9]{4,}", (t or "").lower()):
            if w not in STOP:
                out.add(w)
    return out


def score(product, country, cand, terms, price_norm=None, ref_norm=None):
    """Devuelve (puntuación, comparabilidad, razones, completa). cand = {title, brand, volume_ml, units}. Determinista."""
    title = (cand.get("title") or "").lower(); brand = (cand.get("brand") or "").lower(); why = []; sc = 0.0
    tt = _tokens(terms); hit = tt & _tokens([title])
    if tt:
        pts = 40 * min(1.0, len(hit) / max(2.0, len(tt) * 0.5)); sc += pts; why.append("tipo %.0f/40 (%d palabras clave en el título)" % (pts, len(hit)))
    else:
        why.append("tipo 0/40 (sin términos)")
    if product["category"] == "COSMETICA" and any(k in title for k in KW_RINSE) and "serum" not in title and "sérum" not in title:
        sc -= 25; why.append("−25 rinse-off")
    norm_ml = product["format"]["unit"] == "ml"; base = product["format"]["content"]; cv = cand.get("volume_ml") if norm_ml else cand.get("units")
    if base and cv:
        r = cv / base
        pts = 20 if 0.5 <= r <= 1.5 else 10 if 0.0 < r <= 2.0 else 0; sc += pts; why.append("formato %d/20 (%s vs %s)" % (pts, cv, base))
    else:
        sc += 5; why.append("formato 5/20 (desconocido)")
    attrs = [a.lower() for a in product.get("attributes") or []]
    if attrs:
        n = sum(1 for a in attrs if a in title); pts = 15 * n / len(attrs); sc += pts; why.append("atributos %.0f/15 (%d de %d)" % (pts, n, len(attrs)))
    refs = [r.lower() for r in product.get("reference_competitors") or []]
    rb = _tokens(refs)
    if rb and (brand and any(w in brand for w in rb) or any(w in title for w in rb if len(w) > 5)):
        sc += 10; why.append("marca de referencia +10")
    complete = price_norm is not None and ref_norm
    if complete:
        r = price_norm / ref_norm
        pts = 15 if 0.5 <= r <= 2 else 7 if 0.33 <= r <= 3 else 0; sc += pts; why.append("precio %d/15 (×%.2f)" % (pts, r))
    else:
        why.append("precio 0/15 (sin dato o sin PVP de referencia)")
    sc = round(max(0.0, min(100.0, sc)), 1)
    return sc, ("ALTA" if sc >= THRESH["ALTA"] else "MEDIA" if sc >= THRESH["MEDIA"] else "BAJA"), why, bool(complete)


class Discovery:
    def __init__(self, store, keepa, catalog, svc_for):
        self.store, self.kp, self.cat, self.svc_for = store, keepa, catalog, svc_for

    # ---------------------------------------------------------------- almacenamiento ----------------------------------------------------------
    def _f(self, pid, key):
        return AC._find(self.store, "dataset", "disc:%s:%s" % (pid, key), CT.ACCOUNT_ID)

    def _u(self, pid, key, data, actor="descubrimiento"):
        return AC._upsert(self.store, "dataset", "disc:%s:%s" % (pid, key), data, actor, CT.ACCOUNT_ID)

    def last_run(self, pid):
        r = self._f(pid, "last"); return r["data"] if r else None

    # ---------------------------------------------------------------- plan (cero gasto) --------------------------------------------------------
    def plan(self, pid, countries=None, depth="normal", max_candidates=20):
        p = self.cat.get(pid)
        if not p:
            raise ValueError("producto inexistente")
        cfg = self.kp.cfg_fn(); depth = depth if depth in ("ligera", "normal", "profunda") else "normal"; nq = {"ligera": 1, "normal": 2, "profunda": 3}[depth]
        max_candidates = max(3, min(int(max_candidates or 20), 30)); wanted = [c.upper() for c in (countries or p.get("target_markets") or []) if c.upper() in E.COUNTRIES + ["UK"]] or ["DE", "FR", "IT", "ES"]
        rows, est, missing = [], 0, []
        for c in wanted:
            if c not in K.DOMAINS:
                rows.append({"country": c, "status": "SIN_COBERTURA_KEEPA", "explanation": "Keepa no cubre este marketplace: NO EVALUABLE salvo datos por otra vía (adaptador alternativo: ver documentación).", "tokens": 0}); continue
            terms, origin = self.cat.search_terms(p, c)
            if not terms:
                rows.append({"country": c, "status": "FALTAN_TERMINOS", "explanation": "No hay términos de búsqueda en este idioma ni biblioteca para la subcategoría: añade 1–3 términos en la ficha (no se inventan).", "tokens": 0}); missing.append(c); continue
            terms = terms[:nq]; todo_q = []; cached_q = 0
            for t in terms:
                s = self._f(pid, "search:%s:%s" % (c, re.sub(r"\W+", "-", t.lower())))
                if s and (time.time() - s["data"]["ts"]) < TTL_SEARCH_H * 3600:
                    cached_q += 1
                else:
                    todo_q.append(t)
            n_fetch = max_candidates  # cota superior: se descuenta lo que ya esté en caché al ejecutar
            tok = len(todo_q) * cfg["search_cost"] + n_fetch * cfg["cost_per_asin"]
            rows.append({"country": c, "status": "LISTO", "terms": terms, "terms_origin": origin, "queries_to_run": len(todo_q), "queries_cached": cached_q, "max_fetch": n_fetch, "tokens": tok}); est += tok
        tk = self.kp.tokens; left, rate = tk.get("left"), tk.get("rate")
        eta = round(max(0.0, est - left) / rate, 1) if left is not None and rate else None
        return {"product": pid, "name": p["name"], "depth": depth, "max_candidates": max_candidates, "countries": rows, "estimated_tokens_max": est, "batch_budget": cfg["batch_budget"], "hard_cap": cfg["hard_cap"],
                "needs_approval": est > cfg["batch_budget"] or cfg["require_approval"], "exceeds_hard_cap": est > cfg["hard_cap"], "per_country_tokens": {r["country"]: r["tokens"] for r in rows if r.get("status") == "LISTO"}, "tokens_left_known": left, "refill_per_min": rate, "eta_minutes_if_short": eta if eta else None, "keepa_enabled": K.public_status(cfg)["can_call"],
                "assumptions": "Coste por búsqueda %d y por ASIN %d tokens (SUPUESTOS hasta verificar con tokensConsumed en la primera consulta real). Estimación máxima: la caché y las ASIN ya consultadas reducen el gasto." % (cfg["search_cost"], cfg["cost_per_asin"]),
                "formula": FORMULA, "missing_terms": missing}

    # ---------------------------------------------------------------- ejecución -----------------------------------------------------------------
    def run(self, pid, actor, countries=None, depth="normal", max_candidates=20, approved_tokens=None):
        pl = self.plan(pid, countries, depth, max_candidates); p = self.cat.get(pid); cfg = self.kp.cfg_fn(); svc = self.svc_for(pid)
        if not pl["keepa_enabled"]:
            code = "KEEPA_SIN_CLAVE" if not K.public_status(cfg).get("key_present") else ("KEEPA_SOLO_SALDO" if cfg["mode"] == "balance" else "KEEPA_DESACTIVADO")
            return {"ok": False, "status": code, "plan": pl, "explanation": K.explain(code)}
        ready = [r for r in pl["countries"] if r["status"] == "LISTO"]
        if not ready:
            return {"ok": False, "status": "SIN_NADA_QUE_EJECUTAR", "plan": pl, "explanation": "Ningún país tiene términos de búsqueda y cobertura Keepa. Revisa «FALTAN_TERMINOS»/«SIN_COBERTURA»."}
        if isinstance(approved_tokens, int) and not isinstance(approved_tokens, bool) and approved_tokens > cfg["hard_cap"]:
            return {"ok": False, "status": "APROBACION_SUPERA_TOPE", "plan": pl, "explanation": K.explain("KEEPA_APROBACION_SUPERA_TOPE") + " (aprobado %d > tope %d; el plan completo prevé como máximo %d: ejecútalo país a país)." % (approved_tokens, cfg["hard_cap"], pl["estimated_tokens_max"])}
        if pl["needs_approval"] and not (isinstance(approved_tokens, int) and not isinstance(approved_tokens, bool) and approved_tokens >= 1):
            return {"ok": False, "status": "REQUIERE_AUTORIZACION", "plan": pl, "explanation": "Consumo máximo previsto %d tokens > presupuesto del lote %d. Autoriza un máximo de tokens para esta ejecución (puede quedar parcial y reanudarse)." % (pl["estimated_tokens_max"], cfg["batch_budget"])}
        valid = isinstance(approved_tokens, int) and not isinstance(approved_tokens, bool) and approved_tokens >= 1
        allowed = approved_tokens if valid else max(cfg["batch_budget"], pl["estimated_tokens_max"])  # un máximo explícito SIEMPRE manda (también como tope)
        if valid:
            with self.kp.grant(approved_tokens):   # el tope aprobado se aplica también a nivel de llamada (K1)
                return self._run_inner(pid, actor, pl, p, cfg, svc, allowed, approved_tokens, ready)
        return self._run_inner(pid, actor, pl, p, cfg, svc, allowed, approved_tokens, ready)

    def _run_inner(self, pid, actor, pl, p, cfg, svc, allowed, approved_tokens, ready):
        spent, report, pending, errors, t0 = 0, [], [], [], time.time()
        ref_norm = svc.pvp_default / svc.content * 100 if svc.pvp_default and svc.content else None
        own = {(c, a) for c, a in (p.get("own_asins") or {}).items()}
        for r in ready:
            c = r["country"]; cr = {"country": c, "queries": [], "candidates_found": 0, "fetched": 0, "registered": 0, "status": "OK", "tokens": 0}; found = {}; srec = {}
            for t in r["terms"]:
                key = "search:%s:%s" % (c, re.sub(r"\W+", "-", t.lower())); cached = self._f(pid, key)
                if cached and (time.time() - cached["data"]["ts"]) < TTL_SEARCH_H * 3600:
                    cands = cached["data"]["candidates"]; srec.update(cached["data"].get("records") or {}); cr["queries"].append({"term": t, "from_cache": True, "n": len(cands)})
                else:
                    if spent + cfg["search_cost"] > allowed:
                        cr["status"] = "PARCIAL_PRESUPUESTO"; pending.append({"country": c, "step": "search", "term": t, "reason": "PRESUPUESTO_AUTORIZADO"}); continue
                    try:
                        s = self.kp.search(c, t, approved_tokens=min(max(cfg["search_cost"], cfg["batch_budget"]), cfg["hard_cap"]) if cfg["search_cost"] > cfg["batch_budget"] else None)
                    except K.KeepaError as e:
                        cr["status"] = "PARCIAL_" + e.code; errors.append({"country": c, "code": e.code, "explanation": K.explain(e.code)}); pending.append({"country": c, "step": "search", "term": t, "reason": e.code}); continue
                    if s.get("needs_approval"):
                        cr["status"] = "PARCIAL_PRESUPUESTO"; pending.append({"country": c, "step": "search", "term": t, "reason": "PRESUPUESTO_DEL_LOTE"}); continue
                    spent += s.get("tokens_consumed") if isinstance(s.get("tokens_consumed"), int) else cfg["search_cost"]; cr["tokens"] += s.get("tokens_consumed") or 0
                    cands = s["candidates"]; srec.update({r["asin"]: r for r in s.get("records", [])}); self._u(pid, key, {"ts": time.time(), "country": c, "term": t, "candidates": cands, "records": {r["asin"]: r for r in s.get("records", [])}, "tokens_left": s.get("tokens_left")}, actor); cr["queries"].append({"term": t, "from_cache": False, "n": len(cands)})
                for x in cands:  # validación + deduplicación + exclusión de ASIN propios
                    a = str(x.get("asin") or "").upper()
                    if K.ASIN_RE.match(a) and (c, a) not in own and a not in found:
                        found[a] = x
            cr["candidates_found"] = len(found)
            terms_all = r["terms"]; pre = []
            for a, x in found.items():
                title = x.get("title") or ""; sc, comp, why, _ = score(p, c, {"title": title, "brand": x.get("brand"), "volume_ml": K.parse_volume_ml(title), "units": K.parse_units(title)}, terms_all)
                pre.append((sc, a, x))
            pre.sort(key=lambda z: (-z[0], z[1])); pick = [a for _, a, _ in pre[:pl["max_candidates"]]]
            if pick:
                items = [(c, a) for a in pick if a not in srec or srec[a].get("price") is None]; fp = self.kp.plan(items); fetch_set = [(i["country"], i["asin"]) for i in fp["to_fetch"]]
                if spent + fp["estimated_tokens"] > allowed:  # solo lo que quepa en lo autorizado; el resto queda pendiente (reanudable)
                    fit = max(0, (allowed - spent) // max(1, fp["per_asin"])); drop = set(fetch_set[fit:]); fetch_set = fetch_set[:fit]
                    items = [it for it in items if it not in drop]; cr["status"] = "PARCIAL_PRESUPUESTO"
                    pending += [{"country": cc, "step": "fetch", "asin": aa, "reason": "PRESUPUESTO_AUTORIZADO"} for cc, aa in sorted(drop)]
                est_now = fp["per_asin"] * len(fetch_set)
                try:
                    out = self.kp.fetch(items, approved_tokens=min(est_now, cfg["hard_cap"]) if est_now > cfg["batch_budget"] else None) if items else {"products": [], "pending": [], "errors": [], "tokens_consumed": 0}
                except K.KeepaError as e:
                    errors.append({"country": c, "code": e.code, "explanation": K.explain(e.code)}); out = {"products": [], "pending": [], "errors": [], "tokens_consumed": 0}
                if out.get("needs_approval"):
                    pending += [{"country": c, "step": "fetch", "asin": a, "reason": "TOPE_ABSOLUTO_POR_LOTE (hard_cap %d): ejecuta por países o sube AMAZON_PRO_KEEPA_HARD_CAP" % cfg["hard_cap"]} for _, a in items]; cr["status"] = "PARCIAL_PRESUPUESTO"; out = {"products": [], "pending": [], "errors": [], "tokens_consumed": 0}
                spent += out.get("tokens_consumed") or 0; cr["tokens"] += out.get("tokens_consumed") or 0; errors += out.get("errors", [])
                pending += [{"country": x["country"], "step": "fetch", "asin": x["asin"], "reason": x["reason"], "eta_minutes": x.get("eta_minutes")} for x in out.get("pending", [])]
                if out.get("pending"):
                    cr["status"] = "PARCIAL_" + out["pending"][0]["reason"]
                got = {r["asin"] for r in out.get("products", [])}
                for rec in list(out.get("products", [])) + [srec[a] for a in pick if a in srec and a not in got and srec[a].get("price") is not None]:
                    norm = rec.get("price") / (rec.get("volume_ml") if p["format"]["unit"] == "ml" else rec.get("units")) * 100 if rec.get("price") and (rec.get("volume_ml") if p["format"]["unit"] == "ml" else rec.get("units")) else None
                    sc, comp, why, complete = score(p, c, rec, terms_all, norm, ref_norm)
                    comp, kwhy = KK.degradar(comp, rec, p, c); why = why + ["K1: " + "; ".join(kwhy)]   # reglas K1: solo pueden bajar la comparabilidad
                    svc.register_candidate(c, rec["asin"], comp, sc, "; ".join(why), "Descubrimiento automático (Keepa %s), %s" % ("/search" if rec.get("source", "").find("/search") >= 0 else "/search + /product", time.strftime("%Y-%m-%d"))); cr["registered"] += 1
                cr["fetched"] = len(out.get("products", [])); cr["from_search"] = sum(1 for a in pick if a in srec and a not in got and srec[a].get("price") is not None)
            report.append(cr)
        res = {"ok": True, "status": "COMPLETO" if not pending and not errors else "PARCIAL", "ts": time.time(), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tokens_spent": spent, "approved_tokens": approved_tokens, "countries": report,
               "pending": pending[:100], "errors": errors[:20], "plan": pl, "duration_s": round(time.time() - t0, 2), "actor": actor}
        self._u(pid, "last", res, actor); self.store.audit(CT.ACCOUNT_ID, actor, "discovery.run", {"product": pid, "status": res["status"], "tokens": spent, "pending": len(pending)})
        return res

    def manual(self, pid, country, asins, actor, approved_tokens=None):
        """Entrada manual de ASIN: OPCIÓN AVANZADA. Se registran como MANUAL (sin puntuar: no cuentan hasta confirmar su comparabilidad)."""
        c = str(country).upper(); svc = self.svc_for(pid); n, bad = 0, []
        if c not in K.DOMAINS:
            raise ValueError("país sin cobertura Keepa")
        for a in asins[:100]:
            a = str(a).upper().strip()
            if not K.ASIN_RE.match(a):
                bad.append(a); continue
            if not svc._f("dataset", "reg:%s:%s" % (c, a)):
                svc._u("dataset", "reg:%s:%s" % (c, a), {"country": c, "asin": a, "comparability": None, "status": "MANUAL", "score": None, "reason": "alta manual (opción avanzada)", "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, actor); n += 1
        res = {"registered": n, "invalid": bad, "fetch": None}
        items = [(c, str(a).upper()) for a in asins[:100] if K.ASIN_RE.match(str(a).upper().strip())]
        if items and K.public_status(self.kp.cfg_fn())["can_call"]:
            o = self.kp.fetch(items, approved_tokens=approved_tokens); res["fetch"] = {"fetched": len(o["products"]), "pending": len(o["pending"]), "needs_approval": bool(o.get("needs_approval")), "plan": o.get("plan")}
        return res
