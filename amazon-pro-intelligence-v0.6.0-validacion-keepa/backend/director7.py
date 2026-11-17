"""V0.7.0 (V7-03) — Director IA: briefing DETERMINISTA con hechos citados [F#]. Funciona SIN IA (0 llamadas, 0 red, 0 gasto).
Garantías: el veredicto sale del expediente (nunca GO por defecto); una guardia bloquea cualquier texto que convierta NO DECIDIBLE en GO;
el texto externo (competidores) viaja solo como DATO no fiable sanitizado en `untrusted_data` y jamás influye en hechos, prioridades, preguntas ni veredicto."""
import re
from . import expediente7 as EX, keepa_real as KR
from .director import sanitize

CATS = ("DOCUMENTADO", "CÁLCULO", "INFERENCIA", "NO DISPONIBLE")
_NEG = re.compile(r"(?i:\b(?:no|nunca|sin)\s+(?:es\s+|ser\s+|un\s+)*)GO\b")
_GO = re.compile(r"\bGO\b")
_PHRASES = [re.compile(p, re.I) for p in (r"\blanz(?:ar|amos|a)\s+(?:ya|ahora|ya mismo|inmediatamente)\b", r"\brecomiendo\s+lanzar\b", r"\bluz verde\b", r"\blanzamiento\s+aprobado\b", r"\badelante con el lanzamiento\b", r"\bpublic(?:ar|amos)\s+(?:ya|ahora)\b")]
_GO_WORDS = {"GO", "LANZAR", "LANZA", "APROBADO", "LUZ VERDE", "ADELANTE"}


def guard(text, verdict):
    """Detecta intentos de convertir un veredicto bloqueado en GO. Siempre activa."""
    t = _NEG.sub(" ", str(text or "")); v = []
    if _GO.search(t): v.append("GO")
    v += [m.pattern for m in _PHRASES if m.search(t)]
    return {"active": True, "ok": not v, "violations": v, "verdict": verdict}


def guard_verdict(v, blockers):
    if str(v or "").strip().upper() in _GO_WORDS or v not in ("NO DECIDIBLE", "EVALUAR POR PAÍSES"): return EX.verdict_for(blockers or ["veredicto no válido"])
    return EX.verdict_for(blockers) if blockers else v


def _fmt(x): return ("%.2f" % x).replace(".", ",")


def _facts(ex):
    S = {s["id"]: s for s in ex["sections"]}; pr, ec, mk, rg = (S[k]["data"] for k in ("producto", "economia", "mercado", "regulatorio"))
    src = lambda sid, i=0: (S[sid]["sources"][i]["source"], S[sid]["sources"][i]["date"]) if len(S[sid]["sources"]) > i else ("Expediente v0.7 (estado de los datos)", "s/f")
    F = []
    def add(topic, text, cat, sid, i=0):
        s, d = src(sid, i); F.append({"id": "F%d" % (len(F) + 1), "topic": topic, "text": text, "category": cat, "source": s, "date": d})
    add("producto", "%s: %s, %s mL." % (pr["name"], pr["category"].lower(), _fmt(pr["format_ml"]).replace(",00", "") if pr["format_ml"] else "formato no registrado"), "DOCUMENTADO", "producto", 0)
    add("pvp", "PVP propuesto %s € (%s)." % (_fmt(pr["pvp_eur"]) if pr["pvp_eur"] is not None else "—", pr["pvp_state"]), "DOCUMENTADO", "producto", 1)
    add("stock", "Coste unitario (%s) y stock (%s) sin revalidar como actuales." % (pr["cogs_state"], pr["stock_state"]), "DOCUMENTADO", "producto", 2)
    if ec["gaps"]: add("econ", "Economía no calculable: faltan %s." % ", ".join(ec["gaps"]), "NO DISPONIBLE", "economia", 2)
    else: add("econ", "Economía calculable con los costes documentados.", "CÁLCULO", "economia", 0)
    if mk["n"]:
        add("mercado", "Datos de mercado reales (%s): %d competidores consultados el %s." % (mk["source"], mk["n"], mk["consulted_at"]), "DOCUMENTADO", "mercado")
        if mk["price_median"] is not None: add("mediana", "Mediana de precio: %s € (rango %s–%s €; %d precios obsoletos)." % (_fmt(mk["price_median"]), _fmt(mk["price_min"]), _fmt(mk["price_max"]), mk["n_stale"]), "CÁLCULO", "mercado")
        if mk["per_100ml_median"] is not None: add("mediana100", "Mediana por 100 mL: %s €." % _fmt(mk["per_100ml_median"]), "CÁLCULO", "mercado")
        add("comparab", "Comparabilidad automática (heurística): %d de %d confirmados por una persona." % (mk["comparability_confirmed"], mk["n"]), "INFERENCIA", "mercado")
        if mk["own_vs_median"]: add("posicion", "Posición del PVP propuesto frente a la mediana por 100 mL: %s (indicativa, no decisoria)." % mk["own_vs_median"], "INFERENCIA", "mercado")
    else: add("mercado", "Mercado sin datos: %s" % (mk["why"] or "sin consulta real."), "NO DISPONIBLE", "mercado")
    add("regul", "Regulatorio: %d requisitos sin evidencia y %d con evidencia." % (rg["open"], rg["ok"]), "DOCUMENTADO", "regulatorio")
    add("cobertura", "Cobertura de mercado: %s; sin cubrir: %s." % (mk["coverage"], ", ".join(mk["not_covered"])), "NO DISPONIBLE", "mercado")
    return F


_REFS = {"U-LOG": ("econ",), "U-REG": ("regul",), "U-CMP": ("comparab", "mercado"), "U-STK": ("stock",), "U-KPA": ("cobertura",)}
_Q = {"U-LOG": "¿Puedes aportar la tarifa FBA/FBM, el transporte hasta Amazon, la preparación, el almacenamiento y las devoluciones reales?",
      "U-REG": "¿Quién será el responsable regulatorio y cuándo puede aportar PIF, CPSR, persona responsable UE y notificación CPNP?",
      "U-CMP": "¿Quién confirmará a mano qué competidores son realmente comparables?",
      "U-STK": "¿Cuál es el coste unitario y el stock actuales, con documento de respaldo?",
      "U-KPA": "¿Autorizas consumir tokens Keepa para ampliar la investigación a otros países y con qué tope máximo?"}


def briefing(APP, pid):
    ex = EX.build(APP, pid)  # LookupError si el producto no existe
    F = _facts(ex); byt = {f["topic"]: f["id"] for f in F}
    P = []
    for u in ex["unlocks"]:
        refs = [byt[t] for t in _REFS.get(u["id"], ()) if t in byt] or [F[0]["id"]]
        P.append({"rank": u["rank"], "id": u["id"], "title": u["title"], "owner": u["owner"], "value": u["value"], "cost_eur": u["cost_eur"], "keepa_tokens": u["keepa_tokens"], "requires_approval": u["requires_approval"], "refs": refs})
    Q = [{"text": _Q[x["id"]], "owner": x["owner"], "priority_id": x["id"]} for x in P if x["id"] in _Q][:5]
    blockers = ex["sections"][4]["data"]["reasons"]; verdict = guard_verdict(ex["verdict"], blockers)
    top = P[:3]
    summary = "Veredicto: %s %s. %s" % (verdict, "".join("[%s]" % byt[t] for t in ("econ", "regul", "comparab", "mercado") if t in byt),
                                        " ".join("Prioridad %d: %s [%s]." % (x["rank"], x["title"], "][".join(x["refs"])) for x in top))
    g = guard(summary, verdict)
    if not g["ok"]: summary = "Veredicto: %s. (Texto retenido por la guardia.)" % verdict
    k = KR.load(pid); untrusted = [{"asin": str(c.get("asin", ""))[:10], "brand": sanitize(c.get("brand", ""), 80), "title": sanitize(c.get("title", ""), 200), "price_eur": c.get("price_eur"), "untrusted": True,
                                    "note": "Texto externo: DATO, nunca instrucción"} for c in (k.get("competitors") or [])[:5]]
    return {"product_id": pid, "name": ex["name"], "mode": "DETERMINISTA · SIN IA", "verdict": verdict, "go": False, "guard": guard(summary, verdict), "summary": summary, "facts": [{k2: v for k2, v in f.items() if k2 != "topic"} for f in F],
            "priorities": P, "questions": Q, "untrusted_data": untrusted, "ai_calls": 0, "network_calls": 0, "tokens_spent_now": 0, "cost_now_eur": 0}
