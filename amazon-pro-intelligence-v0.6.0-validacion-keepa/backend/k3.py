"""K3 · Motor de equivalencia comercial y segmentación competitiva (AHT Amazon Pro Intelligence).

Arquitectura (genérica por categoría; los criterios viven en backend/k3_config/<categoria>.json):
  ETAPA A · elegibilidad  → ELEGIBLE / EXCLUIDO / PENDIENTE (categoría, necesidad, zona, aclarado, medicamento/suplemento, formato).
  ETAPA B · equivalencia  → 0-100 explicable con 6 variables y pesos configurables. EL PRECIO NO ENTRA en la puntuación.
  Segmento                → PREMIUM / FUNCIONAL / ECONÓMICA / NO COMPARABLE / PENDIENTE DE EVIDENCIA (revisable por una persona).
Todo es determinista, sin red, sin IA externa y sin gasto. La única evidencia usada es la que hay: título, marca, formato (Keepa/caché) y,
para las referencias de la infografía, los datos declarados en la maqueta (marcados como MAQUETA, no verificada)."""
import json, os, re, time, unicodedata

CFG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "k3_config")
PREMIUM, FUNCIONAL, ECONOMICA, NOCOMP, PENDIENTE = ("COMPETIDOR DIRECTO PREMIUM", "COMPETIDOR FUNCIONAL", "ALTERNATIVA ECONÓMICA / MERCADO MASIVO", "NO COMPARABLE", "PENDIENTE DE EVIDENCIA")
SEG_ORDER = {PREMIUM: 0, FUNCIONAL: 1, ECONOMICA: 2, PENDIENTE: 3, NOCOMP: 4}
SEG_CODE = {PREMIUM: "premium", FUNCIONAL: "funcional", ECONOMICA: "economica", NOCOMP: "no_comparable", PENDIENTE: "pendiente"}
CODE_SEG = {v: k for k, v in SEG_CODE.items()}
COMPONENTES = ("necesidad", "tipo_aplicacion", "posicionamiento", "activos", "canal", "formato")
COMP_NAME = {"necesidad": "Necesidad y función principal", "tipo_aplicacion": "Tipo de producto y aplicación", "posicionamiento": "Posicionamiento y público objetivo",
             "activos": "Ingredientes activos y propuesta funcional", "canal": "Canal comercial y categoría de mercado", "formato": "Formato, volumen y pauta de uso"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def load_config(categoria="capilar_cuero_cabelludo"):
    if not re.fullmatch(r"[a-z0-9_]+", categoria or ""):
        raise ValueError("categoría inválida")
    p = os.path.join(CFG_DIR, categoria + ".json")
    if not os.path.isfile(p):
        raise ValueError("sin perfil K3 para la categoría «%s»" % categoria)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_infografia():
    with open(os.path.join(CFG_DIR, "referencias_infografia_activcore.json"), encoding="utf-8") as f:
        return json.load(f)


def freshness(as_of, now=None, actual=7, reciente=30):
    """ACTUAL ≤7 d · RECIENTE ≤30 d · HISTÓRICO >30 d · FECHA DESCONOCIDA. Un precio histórico NO es un precio actual."""
    try:
        t = time.mktime(time.strptime(str(as_of)[:10], "%Y-%m-%d")); d = max(int(((now or time.time()) - t) / 86400), 0)
    except (ValueError, TypeError, OverflowError):
        return None, "FECHA DESCONOCIDA"
    return d, ("ACTUAL" if d <= actual else "RECIENTE" if d <= reciente else "HISTÓRICO")


class Segmenter:
    def __init__(self, cfg=None, pesos=None, umbrales=None):
        self.cfg = cfg or load_config()
        self.w = dict(self.cfg["pesos"]); self.w.update(pesos or {})
        self.t = dict(self.cfg["umbrales"]); self.t.update(umbrales or {})
        lx = self.cfg["lexico"]
        def rx(lst): return re.compile(r"(?<![a-z0-9])(?:" + "|".join(lst) + r")", re.I) if lst else re.compile(r"(?!x)x")
        self.rx = {k: rx(v) for k, v in lx.items() if isinstance(v, list)}
        self.need_rx = {k: rx(v) for k, v in lx["necesidades"].items()}
        self.act_rx = {k: (rx(v["patrones"]), v["valor"]) for k, v in lx["activos"].items()}
        self.brands = []
        for tier, b in self.cfg["marcas"].items():
            for n in b["nombres"]:
                self.brands.append((norm(n), tier, b["valor"], b["canal"]))
        self.brands.sort(key=lambda x: -len(x[0]))
        self.ref = self.cfg["referencia"]

    # ------------------------------------------------------------------ extracción de características ------------------------------------------
    @staticmethod
    def volume(rec):
        v = rec.get("volume_ml") if rec.get("volume_ml") is not None else rec.get("volumen_ml")
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
            return float(v), "dato"
        m = re.search(r"(\d+(?:[.,]\d+)?)\s?ml\b", norm(rec.get("title") or rec.get("producto")))
        if m:
            x = float(m.group(1).replace(",", "."))
            if 5 <= x <= 2000: return x, "título"
        return None, None

    def brand_tier(self, brand, title):
        b = norm(brand); t = norm(title)
        for n, tier, val, canal in self.brands:
            if b and (b == n or re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", b)) or (not b and re.match(re.escape(n) + r"\b", t)):
                return tier, val, canal, "marca documentada en la configuración"
        if re.search(r"\bprofesional|\bprofessional|\bsalon\b|\bpeluquer", t):
            return "profesional_media", 0.7, 0.7, "el título declara posicionamiento profesional (sin marca clasificada)"
        nc = self.cfg["marca_no_clasificada"]
        return None, nc["valor"], nc["canal"], "marca sin clasificar (sin posicionamiento documentado): puntuación prudente"

    def features(self, rec):
        title = rec.get("title") or rec.get("producto") or ""; t = norm(title); brand = rec.get("brand") or rec.get("marca") or ""; ov = rec.get("overlay") or {}
        f = {"t": t, "title": title, "brand": brand, "overlay": bool(ov)}
        f["medicamento"] = [m.group(0) for m in self.rx["medicamento"].finditer(t)]
        f["suplemento"] = [m.group(0) for m in self.rx["suplemento"].finditer(t)]
        f["leave_on_exp"] = bool(self.rx["leave_on_explicito"].search(t)) or ov.get("leave_on") is True
        t_clean = self.rx["leave_on_explicito"].sub(" ", t)
        f["rinse"] = [m.group(0) for m in self.rx["rinse_off"].finditer(t_clean)]
        f["prelavado"] = bool(self.rx["pre_lavado"].search(t))
        f["tipo"] = ov.get("tipo") or ("serum" if self.rx["tipo_serum"].search(t) else "locion" if self.rx["tipo_locion"].search(t) else "aceite" if self.rx["tipo_aceite"].search(t) else None)
        f["tipo_fuente"] = "maqueta" if ov.get("tipo") else ("título" if f["tipo"] else None)
        f["hair"] = bool(self.rx["categoria_capilar"].search(t)) or bool(ov)
        needs = [k for k, r in self.need_rx.items() if r.search(t)]
        if ov.get("necesidad"): needs.insert(0, ov["necesidad"])
        vn = self.cfg["lexico"]["valor_necesidad"]; needs = sorted(set(needs), key=lambda k: -vn.get(k, 0))
        f["necesidades"] = needs; f["necesidad"] = needs[0] if needs else None; f["necesidad_fuente"] = "maqueta" if ov.get("necesidad") else ("título" if needs else None)
        if ov.get("zona") == "cuero_cabelludo" or self.rx["zona_cuero"].search(t): f["zona"], f["zona_fuente"] = "cuero_cabelludo", ("maqueta" if ov.get("zona") else "título")
        elif self.rx["zona_longitud"].search(t): f["zona"], f["zona_fuente"] = "longitud", "título"
        elif self.rx["pista_cuero"].search(t) and f["tipo"]: f["zona"], f["zona_fuente"] = "cuero_inferido", "inferida (cepillo/masaje)"
        elif f["hair"]: f["zona"], f["zona_fuente"] = "pelo_sin_especificar", "título (solo «pelo/cabello»)"
        else: f["zona"], f["zona_fuente"] = None, None
        acts = {}
        for k, (r, v) in self.act_rx.items():
            for m in r.finditer(t): acts[norm(m.group(0))] = (k, v)
        for a in ov.get("activos_doc") or []:
            for k, (r, v) in self.act_rx.items():
                if r.search(norm(a)): acts[norm(a)] = (k, v)
        f["activos"] = acts; f["activos_fuente"] = "maqueta" if ov.get("activos_doc") else ("título" if acts else None)
        f["vol"], f["vol_fuente"] = self.volume(rec)
        f["tier"], f["tier_val"], f["canal_val"], f["tier_nota"] = self.brand_tier(brand, title)
        f["posicionamiento_maqueta"] = ov.get("posicionamiento_maqueta")
        return f

    # ------------------------------------------------------------------ ETAPA A · elegibilidad ---------------------------------------------------
    def eligibility(self, f):
        if f["medicamento"]: return "EXCLUIDO", ["producto con uso médico/farmacológico (%s): no es cosmético comparable" % ", ".join(sorted(set(f["medicamento"]))[:3])]
        if f["suplemento"]: return "EXCLUIDO", ["complemento alimenticio o suplemento oral (%s): otra categoría" % ", ".join(sorted(set(f["suplemento"]))[:3])]
        if not f["hair"]:
            if f["necesidades"] and f["tipo"]: return "PENDIENTE", ["el título no menciona pelo ni cuero cabelludo (solo «%s»): categoría no confirmada" % f["necesidades"][0].replace("_", " ")]
            if f["tier"] in self.cfg["premium_marca_tiers"] + ["profesional_media"]: return "PENDIENTE", ["el título no menciona pelo ni cuero cabelludo: categoría capilar no confirmada (marca de cuidado capilar/dermocosmética)"]
            return "EXCLUIDO", ["sin señal de cuidado capilar / cuero cabelludo: otra categoría"]
        serum_like = f["tipo"] in ("serum", "locion")
        if f["rinse"] and not f["leave_on_exp"]:
            if serum_like and not re.search(r"champu|shampoo|acondicionador|conditioner|mascarilla|masque", " ".join(f["rinse"])):
                return "PENDIENTE", ["el título mezcla un formato de aclarado (%s) con un sérum: no se puede confirmar que sea sin aclarado" % ", ".join(sorted(set(f["rinse"]))[:2])]
            return "EXCLUIDO", ["producto con aclarado (%s): no es un tratamiento leave-on como ACTIVCORE" % ", ".join(sorted(set(f["rinse"]))[:2])]
        if f["prelavado"]: return "PENDIENTE", ["aplicación previa al lavado («prelavado»): no está confirmado que sea sin aclarado"]
        return "ELEGIBLE", ["categoría capilar; sin aclarado no excluyente; no es medicamento ni suplemento"]

    # ------------------------------------------------------------------ ETAPA B · puntuación -----------------------------------------------------
    def components(self, f):
        C = {}; vn = self.cfg["lexico"]["valor_necesidad"]
        # 1. necesidad
        if f["necesidad"]:
            C["necesidad"] = (vn[f["necesidad"]], "necesidad detectada: %s (%s) frente a «%s» de ACTIVCORE" % (f["necesidad"].replace("_", " "), f["necesidad_fuente"], self.ref["necesidad_principal"].replace("_", " ")), f["necesidad_fuente"])
        else:
            C["necesidad"] = (None, "no se identifica la necesidad principal en la evidencia disponible", None)
        # 2. tipo y aplicación
        if f["tipo"]:
            base = {"serum": 1.0, "locion": 0.9, "aceite": 0.4}[f["tipo"]]
            zk = {"cuero_cabelludo": 1.0, "cuero_inferido": 0.85, "pelo_sin_especificar": 0.7, "longitud": 0.2}.get(f["zona"], 0.5)
            C["tipo_aplicacion"] = (round(base * zk, 3), "tipo «%s» (%s) · zona %s (%s)%s" % (f["tipo"], f["tipo_fuente"], (f["zona"] or "n/d").replace("_", " "), f["zona_fuente"], " · aceite genérico: señal de tipo baja, nunca equivalente directo" if f["tipo"] == "aceite" else ""), f["tipo_fuente"])
        else:
            C["tipo_aplicacion"] = (None, "no se identifica el tipo de producto (sérum, loción, aceite…)", None)
        # 3. posicionamiento y público (SIN PRECIO)
        spec = 0.0
        if f["tipo"] in ("serum", "locion") and f["necesidad"] in ("caida_densidad", "hidratacion_cuero", "confort_cuero"): spec = 0.5 + (0.5 if f["zona"] in ("cuero_cabelludo",) else 0.25 if f["zona"] in ("cuero_inferido", "pelo_sin_especificar") else 0)
        elif f["tipo"] == "aceite": spec = 0.0
        else: spec = 0.3
        if f["posicionamiento_maqueta"] and re.search(r"premium|profesional|avanzad", norm(f["posicionamiento_maqueta"])): spec = max(spec, 0.8)
        pv = round(0.7 * f["tier_val"] + 0.3 * spec, 3)
        C["posicionamiento"] = (pv, "%s · especialización %.2f (sin usar el precio)" % (f["tier_nota"], spec), "marca" if f["tier"] else "supuesto prudente")
        # 4. activos
        if f["activos"]:
            vals = sorted((v for k, v in f["activos"].values()), reverse=True); fam = {k for k, v in f["activos"].values()}
            C["activos"] = (min(1.0, vals[0] + (0.1 if len(fam) > 1 else 0)), "activos: %s (%s)" % (", ".join(sorted(f["activos"])[:5]), f["activos_fuente"]), f["activos_fuente"])
        else:
            C["activos"] = (None, "activos no documentados en la evidencia disponible (los títulos de Amazon rara vez los incluyen)", None)
        # 5. canal
        C["canal"] = (f["canal_val"], "canal/categoría según la marca: %s" % ("documentada" if f["tier"] else "sin clasificar (valor prudente)"), "marca" if f["tier"] else "supuesto prudente")
        # 6. formato
        if f["vol"]:
            r = f["vol"] / float(self.ref["formato_ml"]); v = 1.0 if 0.5 <= r <= 2 else 0.5 if 0.25 <= r <= 4 else 0.2
            C["formato"] = (v, "%g mL (%s) = ×%.2f de los %g mL de ACTIVCORE" % (f["vol"], f["vol_fuente"], r, self.ref["formato_ml"]), f["vol_fuente"])
        else:
            C["formato"] = (None, "volumen no documentado", None)
        return C

    def score(self, C):
        tot = sum(self.w[k] for k in COMPONENTES) or 1.0; known = sum(self.w[k] for k in COMPONENTES if C[k][0] is not None)
        pts = {k: (round(self.w[k] * C[k][0], 2) if C[k][0] is not None else None) for k in COMPONENTES}
        return round(100 * sum(p for p in pts.values() if p is not None) / tot, 1), round(known / tot, 3), pts

    def classify(self, rec, now=None):
        f = self.features(rec); estado, razones = self.eligibility(f); C = self.components(f); sc, cov, pts = self.score(C)
        faltan = [COMP_NAME[k] for k in COMPONENTES if C[k][0] is None]
        ess_missing = [COMP_NAME[k] for k in self.cfg["esenciales"] if C[k][0] is None]
        gate = self._premium_gate(f, sc)
        if estado == "EXCLUIDO": seg, why = NOCOMP, razones[0]
        elif estado == "PENDIENTE": seg, why = PENDIENTE, razones[0]
        elif ess_missing: seg, why = PENDIENTE, "faltan datos esenciales: %s" % ", ".join(ess_missing)
        elif cov < self.t["cobertura_min"]: seg, why = PENDIENTE, "cobertura de evidencia %d %% < mínimo %d %%" % (cov * 100, self.t["cobertura_min"] * 100)
        elif sc < self.t["economica"]: seg, why = NOCOMP, "equivalencia %.1f < %g: no compite por cliente, necesidad y función" % (sc, self.t["economica"])
        elif f["tier"] == "masivo": seg, why = ECONOMICA, "marca de mercado masivo documentada; equivalencia %.1f: presión de precio y contexto, no referencia de posicionamiento" % sc
        elif sc >= self.t["premium"] and gate["ok"]: seg, why = PREMIUM, "equivalencia %.1f ≥ %g y cumple todas las condiciones premium (marca especializada/profesional, sérum, misma necesidad)" % (sc, self.t["premium"])
        elif sc >= self.t["funcional"]: seg, why = FUNCIONAL, "equivalencia %.1f: finalidad similar%s" % (sc, "" if sc < self.t["premium"] else "; no es premium porque " + "; ".join(gate["falla"]))
        else: seg, why = ECONOMICA, "equivalencia %.1f (<%g): alternativa de menor equivalencia funcional" % (sc, self.t["funcional"])
        if seg in (FUNCIONAL, ECONOMICA) and f["tier"] is None and not f["overlay"]: why += " (marca sin clasificar: nunca puede ser premium)"
        vol, vsrc = f["vol"], f["vol_fuente"]
        out = {"segmento": seg, "codigo": SEG_CODE[seg], "equivalencia": sc, "cobertura": cov, "explicacion": why, "elegibilidad": {"estado": estado, "razones": razones},
               "componentes": {k: {"nombre": COMP_NAME[k], "peso": self.w[k], "valor": C[k][0], "puntos": pts[k], "razon": C[k][1], "evidencia": C[k][2]} for k in COMPONENTES},
               "faltan": faltan, "premium": gate, "necesidades": f["necesidades"], "tipo": f["tipo"], "zona": f["zona"], "leave_on": (True if f["leave_on_exp"] else False if f["rinse"] else None),
               "activos": sorted(f["activos"]), "volumen_ml": vol, "volumen_fuente": vsrc, "marca_tier": f["tier"] or "NO CLASIFICADA", "evidencia": (("MAQUETA (no verificada)" if not rec.get("asin") else "KEEPA (título/marca/formato) + MAQUETA (necesidad/activos, no verificada)") if f["overlay"] else "TÍTULO/MARCA/FORMATO (Keepa en caché)")}
        return out

    def _premium_gate(self, f, sc):
        falla = []
        if f["tier"] not in self.cfg["premium_marca_tiers"]: falla.append("la marca no está documentada como premium/profesional/dermocosmética")
        if f["tipo"] not in ("serum", "locion"): falla.append("no es un sérum/loción leave-on")
        if f["zona"] in ("longitud", None): falla.append("la zona de aplicación no es el cuero cabelludo ni es genérica")
        if f["necesidad"] != self.ref["necesidad_principal"]: falla.append("la necesidad principal no coincide (%s)" % (f["necesidad"] or "no identificada").replace("_", " "))
        if sc < self.t["premium"]: falla.append("equivalencia %.1f < %g" % (sc, self.t["premium"]))
        return {"ok": not falla, "falla": falla}


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# candidatos, revisión manual, benchmark por segmentos
# ---------------------------------------------------------------------------------------------------------------------------------------------------
def _canon_key(rec):
    t = norm(rec.get("title") or rec.get("producto")); t = re.sub(r"\d+(?:[.,]\d+)?\s?ml|\b\d+\b", " ", t)
    toks = sorted(set(w for w in re.findall(r"[a-z]{3,}", t) if w not in ("para", "pelo", "cabello", "capilar", "serum", "cuero", "cabelludo", "con", "del", "los", "las")))
    return norm(rec.get("brand") or rec.get("marca")) + "|" + " ".join(toks[:6])


def build_candidates(keepa_records, infografia=None):
    """Une registros Keepa (caché) con las 5 referencias de la maqueta. Evita duplicados: mismo ASIN o misma marca+línea. Devuelve (candidatos, duplicados_descartados)."""
    infografia = infografia or load_infografia(); out = {}; dups = []; seen = {}
    for r in keepa_records:
        a = str(r.get("asin") or "").upper(); k = _canon_key(r)
        if a in out or (k in seen and k.split("|")[1]):
            dups.append({"asin": a, "duplicado_de": a if a in out else seen[k], "motivo": "mismo ASIN" if a in out else "misma marca y línea (variante)"}); continue
        out[a] = dict(r, asin=a, evidence_kind="KEEPA"); seen[k] = a
    for ref in infografia["referencias"]:
        ov = {"necesidad": ref["necesidad"], "tipo": ref["tipo"], "zona": ref["zona"], "leave_on": ref["leave_on"], "activos_doc": ref["activos_doc"], "posicionamiento_maqueta": ref["posicionamiento_maqueta"]}
        a = ref.get("asin_hint")
        if a and a in out:
            out[a]["overlay"] = ov; out[a]["infografia"] = ref; out[a]["evidence_kind"] = "KEEPA+MAQUETA"; continue
        key = "INF:" + ref["slug"]
        out[key] = {"asin": None, "id": key, "brand": ref["marca"], "title": "%s %s %s" % (ref["marca"], ref["producto"], ("%g ml" % ref["volumen_ml"]) if ref["volumen_ml"] else ""), "volume_ml": ref["volumen_ml"], "price": None, "price_as_of": None,
                    "overlay": ov, "infografia": ref, "evidence_kind": "MAQUETA", "country": "ES"}
    return list(out.values()), dups


def classify_all(seg, recs, reviews=None, now=None):
    reviews = reviews or {}; rows = []
    for r in recs:
        c = seg.classify(r, now)
        key = r.get("asin") or r.get("id"); rv = reviews.get(key)
        age, pcls = freshness(r.get("price_as_of"), now, seg.t["frescura_actual_dias"], seg.t["frescura_reciente_dias"]) if r.get("price") is not None else (None, "SIN PRECIO")
        ml = c["volumen_ml"]; p = r.get("price"); inf = r.get("infografia") or {}
        fin = c["segmento"]; fin_src = "automática"
        if rv and rv.get("estado") == "CONFIRMADO": fin, fin_src = CODE_SEG[rv["segmento"]], "confirmada por %s" % rv.get("actor")
        elif rv and rv.get("estado") == "RECHAZADO": fin, fin_src = NOCOMP, "rechazada por %s" % rv.get("actor")
        cost_day = None
        if p is not None and inf.get("duracion_dias") and pcls in ("ACTUAL", "RECIENTE"): cost_day = round(p / inf["duracion_dias"], 2)
        rows.append({"key": key, "asin": r.get("asin"), "country": r.get("country") or "ES", "brand": r.get("brand") or r.get("marca"), "title": r.get("title"), "url": r.get("url") or ("https://www.amazon.es/dp/%s" % r["asin"] if r.get("asin") else None),
                     "image": None, "image_nota": "sin imagen: la caché Keepa no incluye imágenes autorizadas",
                     "price": p, "price_as_of": r.get("price_as_of"), "price_age_days": age, "price_class": pcls, "price_100ml": round(p / ml * 100, 2) if p is not None and ml else None,
                     "cost_day": cost_day, "cost_day_nota": None if cost_day is not None else "NO DISPONIBLE: pauta/duración no documentada o precio no vigente",
                     "bsr": r.get("bsr"), "bsr_nota": "BSR = ranking de categoría, NO ventas", "evidence_kind": r.get("evidence_kind"), "automatic": c, "review": rv,
                     "segmento": fin, "codigo": SEG_CODE[fin], "segmento_origen": fin_src, "equivalencia": c["equivalencia"], "infografia": ({k: inf.get(k) for k in ("pvp_maqueta_eur", "posicionamiento_maqueta", "dosis", "duracion_dias", "concentracion", "nota")} if inf else None)})
    rows.sort(key=lambda x: (SEG_ORDER[x["segmento"]], -x["equivalencia"], x["asin"] or x["key"]))
    return rows


def median(xs):
    xs = sorted(xs); n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def panels(rows, own_pvp=None, own_ml=None, muestra_min=3, own_cost_day=None):
    """Tres paneles SEPARADOS (nunca se mezclan medianas de segmentos). Estadísticos solo con precios vigentes (≤30 d) y muestra mínima."""
    out = {}
    for code, title in (("premium", "A · Competencia directa premium"), ("funcional", "B · Competencia funcional"), ("economica", "C · Mercado económico / masivo")):
        rs = [r for r in rows if r["codigo"] == code]; vig = [r for r in rs if r["price_class"] in ("ACTUAL", "RECIENTE") and r["price_100ml"] is not None]; xs = [r["price_100ml"] for r in vig]
        p = {"titulo": title, "n": len(rs), "n_precio_vigente": len(vig), "n_historico_o_sin_fecha": sum(1 for r in rs if r["price_class"] in ("HISTÓRICO", "FECHA DESCONOCIDA")), "n_sin_precio": sum(1 for r in rs if r["price_class"] == "SIN PRECIO"), "estadisticos": None}
        if len(xs) >= muestra_min:
            p["estadisticos"] = {"mediana_100ml": round(median(xs), 2), "min_100ml": round(min(xs), 2), "max_100ml": round(max(xs), 2), "n": len(xs)}
        else:
            p["estadisticos_nota"] = "MUESTRA INSUFICIENTE (n=%d de precios vigentes; mínimo %d): no se calculan medianas ni rangos." % (len(xs), muestra_min)
        if own_pvp and own_ml:
            mine = own_pvp / own_ml * 100; p["propio_100ml"] = round(mine, 2)
            p["posicion"] = ({"mas_baratos": sum(1 for x in xs if x < mine), "mas_caros": sum(1 for x in xs if x > mine), "n": len(xs)} if len(xs) >= muestra_min else None)
            p["comparadores_individuales"] = [{"marca": r["brand"], "asin": r["asin"], "precio_100ml": r["price_100ml"], "clase": r["price_class"], "vs_propio_pct": round((r["price_100ml"] / mine - 1) * 100)} for r in vig] if 0 < len(xs) < muestra_min else None
        out[code] = p
    return out


def plan_consultas(cfg, countries=("ES", "DE", "FR", "IT"), max_por_pais=8):
    """Plan de descubrimiento multilingüe (SIN llamadas): necesidad + tipo + aplicación + activos + posicionamiento + «productos similares».
    La ejecución contra Keepa de pago requiere autorización explícita y estimación previa de tokens (módulo de descubrimiento K1)."""
    T = {"ES": {"nec": "sérum anticaída cuero cabelludo", "tipo": "sérum capilar sin aclarado", "app": "tratamiento densidad capilar leave-in", "pos": "sérum anticaída profesional", "act": "cafeína sérum cuero cabelludo"},
         "DE": {"nec": "Haarausfall Serum Kopfhaut", "tipo": "Kopfhaut Serum ohne Ausspülen", "app": "Haardichte Treatment Leave-in", "pos": "Haarserum gegen Haarausfall Profi", "act": "Koffein Serum Kopfhaut"},
         "FR": {"nec": "sérum anti-chute cuir chevelu", "tipo": "sérum capillaire sans rinçage", "app": "soin densité cheveux sans rinçage", "pos": "sérum anti-chute professionnel", "act": "caféine sérum cuir chevelu"},
         "IT": {"nec": "siero anticaduta cuoio capelluto", "tipo": "siero capelli senza risciacquo", "app": "trattamento densità capelli leave-in", "pos": "siero anticaduta professionale", "act": "caffeina siero cuoio capelluto"},
         "EN": {"nec": "hair loss scalp serum", "tipo": "leave-in scalp serum", "app": "hair density treatment serum", "pos": "professional anti hair loss serum", "act": "caffeine scalp serum"}}
    sim = ["Kérastase Genesis sérum", "Nioxin Night Density Rescue", "Redken Aminexil", "The Ordinary Multi-Peptide Serum for Hair Density", "Bio-Pilixin sérum"]
    plan = []
    for c in countries:
        lang = T.get(c, T["EN"]); qs = [{"eje": k, "consulta": v} for k, v in lang.items()] + [{"eje": "producto_similar", "consulta": s} for s in sim]
        plan.append({"pais": c, "consultas": qs[:max_por_pais]})
    n = sum(len(p["consultas"]) for p in plan)
    return {"consultas_total": n, "paises": plan, "ejecucion": "NO ejecutada: Keepa de pago desactivado. Requiere autorización explícita y estimación previa de tokens (descubrimiento K1: plan → autorización → ejecución).", "expansion": ["identificar candidatos", "clasificar (K3)", "descartar falsos positivos (NO COMPARABLE)", "usar los confirmados como nuevas semillas de búsqueda", "deduplicar por ASIN y por marca+línea"]}


def explain(row):
    a = row["automatic"]; L = ["%s · %s → %s (%s)" % (row.get("brand") or "marca n/d", (row.get("title") or "")[:80], row["segmento"], row["segmento_origen"])]
    L.append("Elegibilidad (etapa A): %s — %s." % (a["elegibilidad"]["estado"], "; ".join(a["elegibilidad"]["razones"])))
    L.append("Equivalencia (etapa B): %.1f/100 con cobertura de evidencia %d %%." % (a["equivalencia"], a["cobertura"] * 100))
    for k in COMPONENTES:
        c = a["componentes"][k]; L.append("  · %s (%d %%): %s — %s" % (c["nombre"], c["peso"], ("%.1f/%d" % (c["puntos"], c["peso"])) if c["puntos"] is not None else "SIN DATOS", c["razon"]))
    L.append("Decisión: " + a["explicacion"] + ".")
    if a["premium"]["falla"] and a["segmento"] != NOCOMP: L.append("No es premium porque: " + "; ".join(a["premium"]["falla"]) + ".")
    L.append("El precio NO interviene en la equivalencia ni en el segmento.")
    return L
