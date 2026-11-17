"""V0.7.0 (V7-01) — Datos REALES de Keepa ya obtenidos, integrados sin red y sin gasto.
Lee docs_v06/evidencia_keepa_real/ (la única llamada real autorizada: /search ES, 10 tokens, 2026-11-17). Cada dato lleva fuente, fecha y estado;
lo que Keepa /search no entrega (rating, vendedor) es NO DISPONIBLE, nunca 0. Los títulos externos son DATOS NO FIABLES (sanitizados)."""
import json, os, re, time
from .director import sanitize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "docs_v06", "evidencia_keepa_real")
PRODUCT_EVIDENCE = {"PRD-ACTIVCORE-V2": "competidores_ES.json"}  # producto -> fichero de evidencia real (ES)
STALE_DAYS = 30
LIMITS = ["Solo dominio ES (amazon.es): DE/FR/IT/UK sin verificar.", "Keepa /search no entrega rating ni vendedor: NO DISPONIBLE.",
          "La comparabilidad es AUTOMÁTICA y NO CONFIRMADA por una persona: no usar medianas como decisión.",
          "El precio es el último punto de la serie Keepa y puede ser antiguo (ver price_age_days): no es el precio de hoy.", "Sin datos de ventas: Keepa /search no estima ventas."]
PID = re.compile(r"^[A-Za-z0-9._\-]{3,60}$")


def _day(s):
    try: return time.mktime(time.strptime(str(s)[:10], "%Y-%m-%d")) / 86400
    except (ValueError, TypeError): return None


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _empty(state, why, pid=None):
    return {"product": pid, "state": state, "why": why, "source": None, "domain": None, "consulted_at": None, "competitors": [], "own": None,
            "summary": {"n": 0, "n_priced": 0, "n_fresh": 0, "n_stale": 0}, "limits": LIMITS, "network_calls": 0, "tokens_spent_now": 0}


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def load(product_id, evid_dir=None, own_per_100ml=None):
    """Devuelve los competidores reales de un producto. NUNCA lanza excepción ni usa la red."""
    if not isinstance(product_id, str) or not PID.match(product_id): return _empty("SIN DATOS", "Identificador de producto no válido")
    fname = PRODUCT_EVIDENCE.get(product_id)
    if not fname: return _empty("SIN DATOS", "No hay evidencia real de Keepa para este producto (solo ACTIVCORE se consultó). Requiere una nueva consulta autorizada.", product_id)
    path = os.path.join(evid_dir or EVID, fname)
    if not os.path.isfile(path): return _empty("SIN DATOS", "Faltan las evidencias de la validación real (docs_v06/evidencia_keepa_real).", product_id)
    try:
        rows = json.load(open(path, encoding="utf-8"))
        if not isinstance(rows, list): raise ValueError("estructura inesperada")
    except (ValueError, OSError) as e:
        return _empty("ERROR DE DATOS", "Evidencia ilegible o corrupta (%s). No se muestran datos parciales." % type(e).__name__, product_id)
    comp = []
    for r in rows:
        if not isinstance(r, dict) or not isinstance(r.get("asin"), str): continue
        consulted = _day(r.get("fecha_consulta")); pday = _day(r.get("precio_fecha_ultimo_punto")); price = _num(r.get("precio_observado_eur"))
        age = int(consulted - pday) if consulted is not None and pday is not None and price is not None else None
        fmt = _num(r.get("formato_ml")); p100 = round(price / fmt * 100, 2) if price is not None and fmt else None
        comp.append({"asin": r["asin"][:10], "brand": sanitize(r.get("marca", ""), 80), "title": sanitize(r.get("producto", ""), 400), "untrusted": True, "price_eur": price, "price_as_of": r.get("precio_fecha_ultimo_punto"),
                     "price_age_days": age, "price_stale": age is not None and age > STALE_DAYS, "format_ml": fmt, "format_source": sanitize(r.get("formato_fuente", ""), 60), "price_per_100ml": p100, "bsr": _num(r.get("bsr")), "bsr_as_of": r.get("bsr_fecha"),
                     "type": r.get("tipo"), "comparability_auto": r.get("comparabilidad"), "comparability_confirmed": "NO CONFIRMADA", "rating": None, "source": "Keepa /search (real) · " + sanitize(r.get("fuente", ""), 80),
                     "consulted_at": r.get("fecha_consulta"), "confidence": sanitize(r.get("confianza_dato", ""), 120)})
    if not comp: return _empty("SIN DATOS", "La evidencia no contiene competidores válidos.", product_id)
    priced = [c for c in comp if c["price_eur"] is not None]; fresh = [c for c in priced if not c["price_stale"]]; per = [c["price_per_100ml"] for c in comp if c["price_per_100ml"] is not None]
    prices = [c["price_eur"] for c in priced]; med = _median(prices); med100 = _median(per)
    own_p = own_per_100ml if own_per_100ml is not None else 49.9  # PVP propuesto 49,90 € / 100 mL (catálogo; no aprobado)
    vs = None if med100 is None else ("EN LINEA" if abs(own_p - med100) / med100 < 0.05 else ("POR ENCIMA" if own_p > med100 else "POR DEBAJO"))
    return {"product": product_id, "state": "REAL", "why": None, "source": "Keepa /search (real) · amazon.es (dominio ES=9)", "domain": "ES", "consulted_at": comp[0]["consulted_at"], "competitors": comp,
            "summary": {"n": len(comp), "n_priced": len(priced), "n_fresh": len(fresh), "n_stale": len(priced) - len(fresh), "price_min": min(prices) if prices else None, "price_max": max(prices) if prices else None, "price_median": med,
                        "price_median_fresh": _median([c["price_eur"] for c in fresh]), "n_per_100ml": len(per), "per_100ml_median": med100, "n_alta": sum(c["comparability_auto"] == "ALTA" for c in comp)},
            "own": {"per_100ml": own_p, "pvp_state": "PROPUESTO (no aprobado)", "vs_median_per100ml": vs}, "limits": LIMITS, "network_calls": 0, "tokens_spent_now": 0}
