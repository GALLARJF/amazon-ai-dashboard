"""V0.6 (F4) — Expediente comercial de lanzamiento: se construye SOLO con datos del catálogo, descubrimiento Keepa en caché, economía trazable y cumplimiento.
Nada se inventa: lo ausente se muestra como NO DETERMINABLE / SIN DATOS / PENDIENTE DE CONEXIÓN. Los borradores son BORRADOR (nunca se publican).
Cumplimiento: comprobaciones PRELIMINARES (no sustituyen al responsable regulatorio)."""
import html, re, time
from . import eu as E, econ6 as X, keepa as K

GEN = "BORRADOR · no publicado · requiere revisión humana"
KEEPA_COUNTRIES = set(K.DOMAINS)  # países con conector Keepa (DE, FR, IT, ES, UK según la configuración)

# ---------------------------------------------------------------------------------------------------------------- claims
_BLOCK_COMMON = [r"\bcura(r|n|s)?\b", r"\bheal(s|ing)?\b", r"\bheilt\b", r"\bgu[eé]rit\b", r"\bguarisce\b", r"enfermedad", r"\bdisease\b", r"krankheit", r"maladie", r"malattia",
                 r"tratamiento m[eé]dico", r"medical treatment", r"\bdiagn[oó]stic", r"\bpreviene\b", r"\bprevents?\b"]
_BLOCK_COSM = [r"detiene la ca[ií]da", r"stops? hair loss", r"stoppt haarausfall", r"arr[eê]te la chute", r"ferma la caduta", r"regenera( el)? (cabello|pelo|fol[ií]culo)", r"hair regrow", r"hace crecer",
               r"crecimiento (del|de) (cabello|pelo)", r"hair growth", r"haarwachstum", r"repousse", r"estimula(r|ndo)? (el )?fol[ií]culo", r"mitocondri", r"energ[ií]a celular", r"\bADN\b|\bDNA\b",
               r"alopecia", r"hormon", r"\bDHT\b"]
_BLOCK_SUPP = [r"\bdiabetes\b", r"c[aá]ncer|cancer", r"depresi[oó]n|depression", r"ansiedad|anxiety|angst", r"insomnio|insomnia", r"hipertensi[oó]n|hypertension", r"sustituye (a )?(la )?medicaci[oó]n", r"reemplaza.{0,20}medic",
               r"sin efectos secundarios|no side effects", r"\bterap[eé]utic"]
_REVIEW_COMMON = [r"cl[ií]nicamente (probado|demostrado)", r"clinically (proven|tested)", r"klinisch (getestet|bewiesen)", r"cliniquement (prouv|test)", r"dermatol[oó]gicamente (testado|probado)", r"dermatologically tested",
                  r"100 ?% natural", r"sin qu[ií]micos|chemical[- ]free", r"hipoalerg[eé]nic", r"hypoallergenic", r"\bgarantizad", r"guaranteed", r"\bn\.?[ºo°]? ?1\b|number one|\bmejor del mercado|best (on|in) the market",
                  r"resultados? (en|garantizad)", r"antiedad|anti-?aging", r"anticada|anti-?hair ?loss|anticaída", r"\bgratis\b|\bfree shipping\b", r"\boferta\b|\bdescuento\b|% ?off"]
_REVIEW_SUPP = [r"contribuye a|contributes to", r"apoya (el|la|los|las)|supports?\b", r"mejora (el|la|los|las)|improves?", r"aumenta (el|la)|boosts?", r"\bdetox", r"energ[ií]a|energy", r"sue[ñn]o|sleep", r"estr[eé]s|stress"]


def claims_lint(text, category="COSMETICA"):
    """Revisión PRELIMINAR de afirmaciones. BLOQUEA = efecto médico/terapéutico/farmacológico (no se puede usar). REVISAR = exige prueba o redacción autorizada."""
    t = str(text or ""); f = []
    block = _BLOCK_COMMON + (_BLOCK_COSM if category == "COSMETICA" else _BLOCK_SUPP if category == "SUPLEMENTOS" else _BLOCK_COSM + _BLOCK_SUPP)
    review = _REVIEW_COMMON + (_REVIEW_SUPP if category != "COSMETICA" else [])
    for lvl, pats, why in (("BLOQUEA", block, "afirmación médica/terapéutica o de mecanismo: riesgo regulatorio (cosmética: Reg. CE 1223/2009 y 655/2013; complementos: Reg. CE 1924/2006)"),
                           ("REVISAR", review, "afirmación que exige prueba documentada o una redacción autorizada")):
        for p in pats:
            for m in re.finditer(p, t, re.I):
                f.append({"term": m.group(0), "level": lvl, "why": why})
    seen, out = set(), []
    for x in f:
        k = (x["term"].lower(), x["level"])
        if k not in seen:
            seen.add(k); out.append(x)
    return {"ok": not any(x["level"] == "BLOQUEA" for x in out), "findings": out, "blocks": sum(1 for x in out if x["level"] == "BLOQUEA"), "reviews": sum(1 for x in out if x["level"] == "REVISAR"),
            "note": "Revisión preliminar por patrones: NO sustituye a un responsable regulatorio. La ausencia de hallazgos no prueba que el texto sea conforme."}


def lint_validator(category):
    def v(text, facts=""):
        r = claims_lint(text, category)
        return {"ok": r["ok"], "why": "claims bloqueados: " + ", ".join(x["term"] for x in r["findings"] if x["level"] == "BLOQUEA"), "kind": "model"}
    return v


# ---------------------------------------------------------------------------------------------------------------- expediente
def _sec(i, title, state, **kw):
    return {"id": i, "title": title, "state": state, **kw}


class Launch:
    def __init__(self, catalog, svc_for, disc, ops=None):
        self.cat, self.svc_for, self.disc, self.ops = catalog, svc_for, disc, ops

    # ---- borradores deterministas (sin IA): solo reordenan datos documentados -----------------------------------------------------------------
    @staticmethod
    def listing_draft(p):
        fmt = p.get("format") or {}
        size = ("%s %s" % (fmt.get("content"), fmt.get("unit"))) if fmt.get("content") else None
        name = p["name"]; brand = p["brand"]
        title = " ".join(x for x in (brand if brand.lower() not in name.lower() else "", name, size or "[FORMATO PENDIENTE]", "[DESCRIPTOR PENDIENTE DE VALIDAR]") if x)
        comp = [c["name"] for c in (p.get("composition") or [])] or list(p.get("attributes") or [])
        comp_state = "composición documentada en la ficha" if p.get("composition") else "ingredientes citados por el usuario en infografías: SIN VERIFICAR contra el INCI"
        bullets = [
            "FORMATO: %s." % (fmt.get("description") or size or "[PENDIENTE: formato]"),
            "INGREDIENTES DECLARADOS: %s (%s)." % (", ".join(comp) if comp else "[PENDIENTE]", comp_state),
            "MODO DE USO: [PENDIENTE: instrucciones del fabricante/expediente de seguridad].",
            "PRECAUCIONES Y DATOS LEGALES: [PENDIENTE: persona responsable UE, lote/PAO, precauciones].",
            "MARCA: %s · %s." % (brand, p.get("subcategory") or "[PENDIENTE: subcategoría]"),
        ]
        ok_claims = [c["text"] for c in (p.get("claims") or []) if c.get("state") == "RESPALDADO"]
        bad = [c["text"] for c in (p.get("claims") or []) if c.get("state") != "RESPALDADO"]
        text = title + "\n" + "\n".join(bullets)
        lint = claims_lint(text, "COSMETICA" if p["category"] == "COSMETICA" else "SUPLEMENTOS")
        return {"label": GEN, "listing_title": title, "bullets": bullets, "description": "[DESCRIPCIÓN PENDIENTE: se redacta solo con propiedades documentadas y claims respaldados]",
                "claims_usables": ok_claims, "claims_sin_respaldo_excluidos": bad, "lint": lint,
                "a_plus": ["Módulo 1 · Marca y formato (solo datos documentados)", "Módulo 2 · Ingredientes declarados (tras validar INCI)", "Módulo 3 · Modo de uso y precauciones (tras validar etiquetado)", "Módulo 4 · Comparativa SOLO con datos verificados"],
                "faq": ["¿Cuál es el contenido? → %s" % (size or "[PENDIENTE]"), "¿Cómo se usa? → [PENDIENTE]", "¿Qué ingredientes contiene? → ver INCI [PENDIENTE]", "¿Quién es el responsable en la UE? → [PENDIENTE]"],
                "images_plan": ["1. Principal: producto sobre blanco (foto real aportada por AHT)", "2. Formato y contenido", "3. Ingredientes declarados (tras validar INCI)", "4. Modo de uso (tras validar)", "5. Etiquetado/precauciones", "6. Marca AHT"],
                "visual_proposals": "Propuestas visuales: solo con fotos/arte reales del producto; sin imágenes generadas que muestren resultados.",
                "video_script": ["0–5 s · Producto y marca", "5–15 s · Formato e ingredientes declarados (rótulos)", "15–25 s · Cómo se aplica [PENDIENTE de validar]", "25–30 s · Marca y datos legales"],
                "keywords_note": "Términos de búsqueda = traducciones del producto (biblioteca lingüística), SIN volumen de búsqueda verificado."}

    @staticmethod
    def ppc_plan(p, econ_rows):
        be = [r["breakeven_acos"]["sin_iva"] for r in econ_rows if r.get("complete") and r.get("breakeven_acos")]
        cap = min(be) if be else None
        return {"label": GEN, "campaigns": [{"tipo": "Automática de descubrimiento", "objetivo": "descubrir términos reales (con datos propios)", "presupuesto": "NO DIMENSIONADO"},
                                           {"tipo": "Exacta de marca", "objetivo": "proteger la marca", "presupuesto": "NO DIMENSIONADO"},
                                           {"tipo": "Manual por categoría (tras 2–4 semanas de datos)", "objetivo": "escalar términos con conversión", "presupuesto": "NO DIMENSIONADO"}],
                "acos_cap": {"valor": cap, "clase": "DERIVADO de economía con datos %s" % ("completos" if cap is not None else "INCOMPLETOS")} if cap is not None else {"valor": None, "estado": "NO DETERMINABLE", "why": "sin economía completa no hay ACoS de equilibrio"},
                "rule": "Ninguna campaña se activa ni se gasta sin aprobación (N3). Presupuestos: los fija una persona."}

    @staticmethod
    def calendar(gates):
        ph = [("T-60 a T-30", "Documentación regulatoria y etiquetado", "regulatorio"), ("T-30 a T-15", "Fotografía, listing y A+ (tras validar claims)", "claims"), ("T-15 a T-7", "Envío a Amazon / stock verificado", "stock"),
              ("T-7 a T0", "Alta del ASIN, revisión final y aprobación de lanzamiento", "aprobacion"), ("T0 a T+14", "Lanzamiento: PPC inicial aprobado, vigilancia diaria", "ppc"), ("T+14 a T+30", "Primera lectura de resultados y ajuste (con ventas propias)", "datos")]
        return {"label": GEN, "phases": [{"ventana": a, "hito": b, "puerta": c, "estado_puerta": gates.get(c, "PENDIENTE")} for a, b, c in ph], "note": "Fechas relativas a T0 (fecha de lanzamiento aún NO fijada: decisión humana)."}

    # ---- compliance -----------------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def compliance_view(svc, p, countries):
        comp = svc.compliance(); items = svc.items; rows = []; open_n = 0; ok_n = 0
        for c in countries:
            cc = comp.get(c) or {}
            for i, text, ref in items:
                st = (cc.get(i) or {}).get("state", "PENDIENTE")
                if st == "OK":
                    ok_n += 1
                elif st != "NO_APLICA":
                    open_n += 1
            rows.append({"country": c, "ok": sum(1 for i, _, _ in items if (cc.get(i) or {}).get("state") == "OK"), "total": sum(1 for i, _, _ in items if (cc.get(i) or {}).get("state") != "NO_APLICA")})
        flow = "COSMÉTICOS UE (Reg. CE 1223/2009: PIF, CPSR, persona responsable, CPNP, INCI, etiquetado) + política de la categoría en Amazon" if p["category"] == "COSMETICA" else \
            "COMPLEMENTOS ALIMENTICIOS (flujo distinto: Directiva 2002/46/CE, Reg. CE 1924/2006 sobre declaraciones, notificación nacional de comercialización, etiquetado) + política de Amazon para complementos" if p["category"] == "SUPLEMENTOS" else "GENÉRICO (categoría sin flujo específico)"
        return {"flow": flow, "by_country": rows, "open": open_n, "ok": ok_n, "verdict": "PUBLICACIÓN BLOQUEADA: requisitos sin evidencia" if open_n else "Sin requisitos abiertos registrados (verificar con responsable regulatorio)",
                "limit": "Comprobaciones PRELIMINARES basadas en la lista de requisitos y las evidencias registradas; no constituyen dictamen legal."}

    # ---- construcción -----------------------------------------------------------------------------------------------------------------------------
    def build(self, pid, mode="FBA", acos_target=None, ads_share=None, hypotheses=False):
        p = self.cat.get(pid)
        if not p:
            raise ValueError("producto inexistente")
        svc = self.svc_for(pid); today = time.strftime("%Y-%m-%d")
        tm = [c for c in (p.get("target_markets") or []) if c in E.VAT] or ["DE", "FR", "IT", "ES"]
        markets = [c for c in dict.fromkeys(tm + ["NL", "PL"]) if c in E.VAT]
        miss = self.cat.completeness(p)
        # --- 1 ficha
        sec = [_sec("ficha", "1 · Ficha del producto", "PARCIAL" if miss else "COMPLETO", missing=miss,
                    data={"id": p["id"], "name": p["name"], "brand": p["brand"], "category": p["category"], "subcategory": p.get("subcategory"), "format": p["format"], "sku": p.get("sku") or "NO DISPONIBLE",
                          "composition": p.get("composition") or "NO DISPONIBLE", "commercial_state": p.get("commercial_state", "PRELANZAMIENTO"), "pvp": p["pvp"], "costs": p["costs"] or "NO DISPONIBLE",
                          "stock": p["stock"], "regulatory": p["regulatory"], "notes": p.get("notes")},
                    note="Los datos «HISTORICO_A_REVALIDAR» NO se presentan como actuales. No se asume que el producto esté publicado en Amazon."
                    ),]
        # --- 2 investigación europea por país
        cd = svc.country_data(); last = self.disc.last_run(pid) if self.disc else None; research = []
        for c in markets:
            sup = c in KEEPA_COUNTRIES; bm = (cd.get(c) or {}).get("benchmark")
            if not sup:
                research.append({"country": c, "name": E.NAMES.get(c, c), "state": "PENDIENTE DE CONEXIÓN", "why": "El conector Keepa actual no cubre este mercado: requiere fuente autorizada o importación manual de datos de AHT", "competitors": 0})
            elif not bm:
                research.append({"country": c, "name": E.NAMES.get(c, c), "state": "SIN DATOS", "why": "Sin consulta Keepa realizada/aprobada para este producto", "competitors": 0})
            else:
                research.append({"country": c, "name": E.NAMES.get(c, c), "state": "CON DATOS PARCIALES", "competitors": bm["total"], "usables": bm["used"], "automatic": bm.get("automatic", 0), "unconfirmed": bm.get("unconfirmed", 0),
                                 "price_norm": bm.get("price_norm"), "norm_unit": bm.get("norm_unit"), "why": "Cobertura = ASIN encontrados por las consultas realizadas; NO se afirma cobertura completa del marketplace"})
        sec.append(_sec("europa", "2 · Investigación europea progresiva", "PARCIAL" if any(r["competitors"] for r in research) else "SIN DATOS", countries=research,
                        uk={"state": "SEPARADO", "why": "Reino Unido se analiza aparte (régimen regulatorio y fiscal distinto: UKCA/persona responsable británica, IVA 20 %, GBP). No se mezcla con la UE."},
                        last_discovery=last and {k: last.get(k) for k in ("at", "state", "countries", "tokens_used") if k in last}, note="Orden de investigación: país por país según autorización de presupuesto; nunca se asume España por defecto."))
        # --- 3 competidores
        comps = []
        for c in markets:
            bm = (cd.get(c) or {}).get("benchmark")
            for r in (bm or {}).get("rows", [])[:25]:
                cmp_ = r.get("comparability") if r.get("comparability_status") in ("CONFIRMADA", "AUTOMATICA") else None
                comps.append({"country": c, "asin": r.get("asin"), "brand": r.get("brand"), "title": (r.get("title") or "")[:90], "price": r.get("price"), "price_norm": r.get("price_norm"), "norm_unit": r.get("norm_unit"),
                              "tipo": "DIRECTO" if cmp_ in ("ALTA", "MEDIA") else ("INDIRECTO" if cmp_ == "BAJA" else "SIN CLASIFICAR"), "comparabilidad": r.get("comparability") or r.get("comparability_suggested"), "estado_comparabilidad": r.get("comparability_status"), "bsr": r.get("bsr")})
        sec.append(_sec("competidores", "3 · Competidores", "PARCIAL" if comps else "SIN DATOS", rows=comps, note="Deduplicados por (país, ASIN). Comparabilidad AUTOMÁTICA = heurística revisable; solo la CONFIRMADA es firme."))
        # --- 4 ranking países
        rk = svc.ranking()
        sec.append(_sec("paises", "4 · Comparación entre países", "PARCIAL" if rk.get("ranking") else "NO DETERMINABLE", ranking=rk.get("ranking"), pending=[{"country": x["country"], "name": x["name"], "why": [c["reason"] for c in x["criteria"].values() if c.get("status") == "NO EVALUABLE"][:3]} for x in rk.get("pending", [])],
                        note="Un país sin datos suficientes queda NO EVALUABLE; no se rellena con valores medios ni se inventa demanda ni cuota de mercado."))
        # --- 5 economía
        pvp = svc.pvp_default if svc.pvp_default else None
        econ = X.table(svc, pvp, mode, acos_target, ads_share, [c for c in markets if c not in E.CURRENCY])
        scen = "NO CALCULABLE" if not any(e.get("complete") for e in econ) else ("CALCULADO · " + (X.weakest([e.get("class") for e in econ if e.get("complete")]) or ""))
        sec.append(_sec("economia", "5 · Rentabilidad por país", scen, mode=mode, pvp_ref=pvp, rows=[{"country": e["country"], "state": e.get("state"), "missing": e.get("missing"), "class": e.get("class"), "contribution": (e.get("result") or {}).get("contribution_before_ads"),
                                                                                                      "margin": (e.get("result") or {}).get("margin_before_ads"), "breakeven_acos": (e.get("breakeven_acos") or {}).get("sin_iva"), "tacos": (e.get("tacos") or {}).get("valor")} for e in econ],
                        note="Contribución antes de publicidad. Faltan costes logísticos documentados → NO CALCULABLE (no se rellenan por defecto)."))
        # --- 6 recomendación fundamentada
        reasons, gates = [], {"regulatorio": "PENDIENTE", "claims": "PENDIENTE", "stock": "PENDIENTE", "aprobacion": "PENDIENTE", "ppc": "PENDIENTE", "datos": "PENDIENTE"}
        comp_view = self.compliance_view(svc, p, [c for c in markets if c in svc.compliance()])
        if comp_view["open"]:
            reasons.append("Cumplimiento: %d requisitos sin evidencia (bloquea la publicación)." % comp_view["open"])
        else:
            gates["regulatorio"] = "OK"
        if p["stock"]["v"] is None or p["stock"]["status"] not in ("VERIFICADO", "DOCUMENTADO"):
            reasons.append("Stock sin verificar actual: no se planifica el envío.")
        else:
            gates["stock"] = "OK"
        if not any(e.get("complete") for e in econ):
            reasons.append("Economía NO CALCULABLE: faltan costes logísticos/comisión documentados.")
        if not rk.get("ranking"):
            reasons.append("Sin ranking de países: faltan comparables confirmados con datos de mercado.")
        rec = {"verdict": "NO DECIDIBLE TODAVÍA", "reasons": reasons, "next_steps": ["Aportar costes logísticos reales y evidencias regulatorias", "Autorizar y ejecutar el descubrimiento Keepa por país", "Confirmar comparabilidad de competidores"]} if reasons else \
              {"verdict": "EVALUAR POR PAÍSES", "reasons": ["Datos mínimos presentes: revisar ranking y rentabilidad país por país"], "next_steps": ["Decidir país piloto con el ranking y la economía"]}
        rec["rule"] = "Recomendación basada solo en el estado de los datos; no inventa demanda, ventas ni cuota de mercado."
        sec.append(_sec("recomendacion", "6 · Recomendación fundamentada", rec["verdict"], **rec))
        # --- 7 listing + creatividad
        ld = self.listing_draft(p)
        sec.append(_sec("listing", "7 · Borradores de listing y creatividad", GEN, **ld))
        # --- 8 cumplimiento
        sec.append(_sec("cumplimiento", "8 · Cumplimiento preliminar", "PENDIENTE" if comp_view["open"] else "REVISAR", **comp_view))
        # --- 9 PPC + calendario
        sec.append(_sec("ppc", "9 · PPC inicial", GEN, **self.ppc_plan(p, econ)))
        gates["claims"] = "OK" if ld["lint"]["ok"] and p.get("claims") and not ld["claims_sin_respaldo_excluidos"] else "PENDIENTE"
        sec.append(_sec("calendario", "10 · Calendario de lanzamiento", GEN, **self.calendar(gates)))
        sec.append(_sec("limites", "11 · Límites y honestidad de datos", "INFO", items=[
            "Ninguna llamada real a Keepa/OpenAI/Amazon forma parte de este expediente salvo que conste en «Conexiones» con fecha.",
            "Datos históricos y de usuario sin revalidar se etiquetan como tales; no son estado actual.",
            "Los borradores NO están publicados ni aprobados. Publicar, activar anuncios o fijar precios exige aprobación (N3)."]))
        return {"product_id": pid, "name": p["name"], "generated_at": today, "mode": "ESTADO REAL DE LOS DATOS (lo ausente se marca; nada simulado)", "sections": sec, "recommendation": rec["verdict"]}


# ---------------------------------------------------------------------------------------------------------------- exportación
def _fmt(v):
    if isinstance(v, dict):
        if "v" in v and "status" in v:
            return "NO DISPONIBLE" if v["v"] is None else "%s (%s · %s · %s)" % (v["v"], v["status"], v.get("source") or "s/f", v.get("date") or "s/f")
        return "; ".join("%s: %s" % (k, _fmt(x)) for k, x in v.items())
    if isinstance(v, list):
        return ", ".join(_fmt(x) for x in v) or "—"
    return "—" if v is None else str(v)


def to_markdown(d):
    L = ["# Expediente comercial de lanzamiento · %s" % d["name"], "", "_Generado %s · %s_" % (d["generated_at"], d["mode"]), "", "**Recomendación:** %s" % d["recommendation"], ""]
    for s in d["sections"]:
        L += ["## %s" % s["title"], "**Estado:** %s" % s["state"], ""]
        for k, v in s.items():
            if k in ("id", "title", "state"):
                continue
            if isinstance(v, list) and v and isinstance(v[0], dict):
                L.append("**%s:**" % k)
                for r in v:
                    L.append("- " + "; ".join("%s=%s" % (a, _fmt(b)) for a, b in r.items() if b not in (None, [], {})))
            elif isinstance(v, list):
                L.append("**%s:**" % k); L += ["- " + _fmt(x) for x in v]
            elif isinstance(v, dict):
                L.append("**%s:** %s" % (k, _fmt(v)))
            elif v not in (None, ""):
                L.append("**%s:** %s" % (k, v))
        L.append("")
    return "\n".join(L)


def to_html(d):
    body = html.escape(to_markdown(d))
    body = re.sub(r"^## (.*)$", r"<h2>\1</h2>", body, flags=re.M); body = re.sub(r"^# (.*)$", r"<h1>\1</h1>", body, flags=re.M)
    body = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", body); body = re.sub(r"^- (.*)$", r"<li>\1</li>", body, flags=re.M)
    body = body.replace("\n", "<br>\n")
    return "<!doctype html><meta charset=utf-8><title>Expediente de lanzamiento</title><style>body{font:14px/1.5 system-ui;background:#06121a;color:#dff;max-width:980px;margin:24px auto;padding:0 16px}h1,h2{color:#18e6ff}li{margin-left:18px}</style>" + body
