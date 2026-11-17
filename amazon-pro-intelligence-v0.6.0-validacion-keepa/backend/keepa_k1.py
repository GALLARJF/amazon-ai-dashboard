"""K1 — Calidad del benchmarking Keepa e importación SIN RED de la evidencia real ya obtenida.
Reglas de comparabilidad deterministas (categoría, función, formato, volumen, precio normalizado, marketplace y calidad de evidencia). Solo BAJAN la comparabilidad de la puntuación
automática (nunca la suben). El BSR NO se convierte en ventas estimadas: no hay metodología validada (ver REGLAS)."""
import json, os, re, time
from . import keepa as K, keepa_real as KR

SUPP = ("complemento", "suplemento", "cápsulas", "capsulas", "comprimidos", "gominolas", "vitamina", "supplement", "minoxidil", "finasterida", "biotina", "kapseln", "gélules", "gelules", "capsule", "integratore", "nahrungsergänzung")
RINSE = ("champú", "champu", "shampoo", "shampooing", "acondicionador", "conditioner", "mascarilla", "masque", "maschera", "spülung", "spulung", "après-shampooing", "balsamo", "shampoing")
LEAVE_ON = ("sérum", "serum", "serúm", "haarserum", "siero", "lotion", "lozione", "tonic", "ampolla", "ampollas", "loción", "locion", "tónico", "tonico", "spray", "elixir", "tratamiento", "treatment", "aceite", "potenciador", "shot", "booster")
SCALP_HAIR = ("kopfhaut", "cuir chevelu", "cheveux", "capelli", "cuoio capelluto", "cuero cabelludo", "capilar", "cabello", "pelo", "scalp", "hair", "raíz", "raiz", "haar", "cheveux")
FUNC_OK = ("haarausfall", "anticaduta", "caduta", "croissance", "wachstum", "crescita", "koffein", "caféine", "caffeine", "caffeina", "cafeína", "anticaída", "anticaida", "anti-chute", "anti chute", "caída", "caida", "chute", "crecimiento", "growth", "grow", "densidad", "hair loss", "fortalec", "raíz viva", "potenciador de raíz", "volumen", "abundant")
FUNC_OTHER = ("calmante", "calming", "picor", "hidratante", "moisturiz", "anticaspa", "caspa", "purific", "clarific", "exfoliante", "nutritiv", "reparador", "color")
REGLAS = [
    "Categoría: se excluyen complementos alimenticios y tratamientos farmacológicos (minoxidil, finasterida…); champús, acondicionadores y mascarillas (rinse-off) son BAJA.",
    "Función: ALTA/MEDIA exige función anticaída/crecimiento/densidad en el título; si solo declara otra función (calmante, hidratante, anticaspa, nutritivo…) es BAJA.",
    "Formato/aplicación: debe ser tratamiento sin aclarado para cuero cabelludo/cabello (sérum, ampolla, loción, tónico, spray).",
    "Volumen: ALTA exige volumen conocido entre ×0,5 y ×2 del contenido propio; volumen desconocido limita a MEDIA; fuera de rango = BAJA.",
    "Precio normalizado: se compara por 100 mL; un precio fuera de ×0,33–×3 respecto al PVP de referencia limita a MEDIA (posible pack/otro segmento). Sin precio: máximo MEDIA.",
    "Marketplace: solo dominios cubiertos por Keepa (DE, FR, IT, ES, UK); el resto es NO EVALUABLE por esta vía.",
    "Calidad de evidencia: precio con más de 30 días de antigüedad o sin historial limita a MEDIA y se marca; ningún dato se promociona a «confirmado» sin decisión humana.",
    "BSR: es un ranking de categoría, NO ventas. No se convierte en unidades/mes sin una metodología documentada y validada con datos propios (pendiente).",
]
ORDER = {"BAJA": 0, "MEDIA": 1, "ALTA": 2}


def clasificar(title, country, volume_ml=None, price=None, price_age_days=None, ref_ml=None, ref_pvp=None):
    t = (title or "").lower(); razones = []; tope = "ALTA"
    if country not in K.DOMAINS: return "BAJA", ["marketplace sin cobertura Keepa: NO EVALUABLE por esta vía"]
    if any(k in t for k in SUPP): return "BAJA", ["excluido: complemento alimenticio o tratamiento farmacológico"]
    if any(k in t for k in RINSE) and not any(k in t for k in ("sérum", "serum", "ampolla")): return "BAJA", ["excluido: producto con aclarado (champú/acondicionador/mascarilla)"]
    if not any(k in t for k in SCALP_HAIR) and not any(k in t for k in ("anticaída", "anticaida", "anti-chute", "hair loss", "chute", "growth", "grow", "haarausfall", "anticaduta")): return "BAJA", ["sin señal de cuidado capilar/cuero cabelludo"]
    if not any(k in t for k in LEAVE_ON): return "BAJA", ["formato/aplicación no comparable (no es tratamiento sin aclarado)"]
    if not any(k in t for k in FUNC_OK):
        return "BAJA", ["función distinta: " + (", ".join(k for k in FUNC_OTHER if k in t)[:60] or "no declara función anticaída/crecimiento")]
    razones.append("categoría y función comparables (tratamiento sin aclarado anticaída/crecimiento)")
    if volume_ml and ref_ml:
        r = volume_ml / ref_ml
        if not 0.5 <= r <= 2: return "BAJA", ["volumen fuera de rango (×%.2f del propio)" % r]
        razones.append("volumen en rango (×%.2f)" % r)
    else:
        tope = "MEDIA"; razones.append("volumen desconocido → máximo MEDIA")
    if price is None: tope = "MEDIA"; razones.append("sin precio observado → máximo MEDIA")
    elif volume_ml and ref_ml and ref_pvp:
        rn = (price / volume_ml) / (ref_pvp / ref_ml)
        if not 0.33 <= rn <= 3: tope = "MEDIA"; razones.append("precio/100 mL ×%.2f del propio: otro segmento → máximo MEDIA" % rn)
    if price_age_days is not None and price_age_days > 30: tope = "MEDIA"; razones.append("precio con %d días → evidencia antigua, máximo MEDIA" % price_age_days)
    return tope, razones


def _pvp(product, country="ES"):
    d = ((product or {}).get("pvp") or {}); x = d.get(country) or d.get("REF") or {}
    v = x.get("v") if isinstance(x, dict) else None
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def degradar(comp, rec, product, country):
    """Combina la comparabilidad automática de V0.5 con las reglas K1: solo puede BAJAR."""
    fm = (product or {}).get("format") or {}; ref_ml = fm.get("content") if fm.get("unit") == "ml" else None
    k, why = clasificar(rec.get("title"), country, rec.get("volume_ml"), rec.get("price"), None, ref_ml, _pvp(product, country))
    return (k if ORDER[k] < ORDER[comp] else comp), why


def importar_evidencia(kp, pid, product=None, register=None):
    """Importa SIN RED ni gasto los competidores reales ya obtenidos (Keepa /search ES) a la caché de ESTA base (la de Render empieza vacía). Marca la procedencia y NO confirma nada."""
    fname = KR.PRODUCT_EVIDENCE.get(pid)
    if not fname: return {"ok": False, "importados": 0, "motivo": "no hay evidencia real de Keepa para este producto"}
    path = os.path.join(KR.EVID, fname)
    try: rows = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError): return {"ok": False, "importados": 0, "motivo": "evidencia ilegible"}
    fm = (product or {}).get("format") or {}; ref_ml = fm.get("content") if fm.get("unit") == "ml" else None; n = 0; niveles = {"ALTA": 0, "MEDIA": 0, "BAJA": 0}
    for r in rows:
        a = str(r.get("asin") or "").upper()
        if not K.ASIN_RE.match(a): continue
        title, susp = K.sanitize_text(r.get("producto")); brand, s2 = K.sanitize_text(r.get("marca"), 60)
        vol = r.get("formato_ml") if isinstance(r.get("formato_ml"), (int, float)) else None; price = r.get("precio_observado_eur") if isinstance(r.get("precio_observado_eur"), (int, float)) else None
        age = None
        try: age = int((time.time() - time.mktime(time.strptime(str(r.get("precio_fecha_ultimo_punto"))[:10], "%Y-%m-%d"))) / 86400)
        except (ValueError, TypeError): pass
        rec = {"country": "ES", "marketplace": "amazon.es", "domain": K.DOMAINS["ES"], "asin": a, "brand": brand, "title": title, "injection_suspect": susp or s2, "url": "https://www.amazon.es/dp/" + a, "currency": "EUR", "volume_ml": vol, "units": None,
               "bsr_category": None, "bsr_date": str(r.get("bsr_fecha") or "")[:10] or None, "volume_source": "evidencia importada" if vol else None, "price": price, "price_source": "nuevo (último punto de la serie)" if price is not None else None, "price_as_of": r.get("precio_fecha_ultimo_punto"),
               "price_list": None, "bsr": r.get("bsr") if isinstance(r.get("bsr"), int) and not isinstance(r.get("bsr"), bool) else None, "rating": r.get("rating") if isinstance(r.get("rating"), (int, float)) and not isinstance(r.get("rating"), bool) else None, "reviews": None, "offers_new": None, "available": None, "price_history": [], "bsr_history": [], "history_points": {"price": 0, "bsr": 0},
               "fetched_at": str(r.get("fecha_consulta") or "")[:20], "source": "IMPORTADO · Keepa API /search ES (evidencia real 2026-11-17, sin red en esta importación)", "evidence_quality": "MEDIA" if price is not None else "BAJA", "seller": None}
        kp._cache_put(K.DOMAINS["ES"], a, "search", rec)
        nivel, why = clasificar(title, "ES", vol, price, age, ref_ml, _pvp(product)); niveles[nivel] += 1
        if register: register("ES", a, nivel, 0, "K1: " + "; ".join(why), "Evidencia real importada (Keepa /search ES, 2026-11-17)")
        n += 1
    return {"ok": True, "importados": n, "niveles_k1": niveles, "red": 0, "tokens": 0, "nota": "Candidatos importados con comparabilidad AUTOMÁTICA K1 (revisable). Nada queda CONFIRMADO sin decisión humana.", "reglas": REGLAS}
