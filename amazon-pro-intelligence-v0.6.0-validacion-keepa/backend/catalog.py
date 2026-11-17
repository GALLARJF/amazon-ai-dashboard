"""Catálogo central de productos (V0.5.0): categorías ampliables, fichas versionadas, archivado y auditoría.
Regla de oro: NUNCA se inventa un dato. Cada valor numérico lleva estado + fuente + fecha; lo que falta es NO_DISPONIBLE.
Se guarda en la cuenta «catalogo-aht» (registros product/dataset). ACTIVCORE conserva sus datos heredados en «activcore-eu» (compatibilidad V0.4.0)."""
import copy, re, time
from . import activcore as AC, eu as E, keepa as K

ACCOUNT_ID = "catalogo-aht"
ACCOUNT_NAME = "Catálogo AHT · productos y mercados"
LEGAL = "Advanced Hybrid Technologies S.L."
STATUSES = ("VERIFICADO", "DOCUMENTADO", "A_CONFIRMAR", "HISTORICO_A_REVALIDAR", "PROPUESTO", "HIPOTESIS", "NO_DISPONIBLE")
STRONG = ("VERIFICADO", "DOCUMENTADO")
LANGS = ("ES", "DE", "FR", "IT")
REG_STATES = ("PENDIENTE", "EN_REVISION", "DOCUMENTADO_PARCIAL", "CONFORME_DOCUMENTADO", "NO_APLICA")
COMMERCIAL_STATES = ("IDEA", "DESARROLLO", "PRELANZAMIENTO", "LANZADO", "PAUSADO", "RETIRADO")
ID_RE = re.compile(r"^PRD-[A-Z0-9]+(?:-[A-Z0-9]+)*$")

# Categorías iniciales (ampliables desde la interfaz). «normalization» fija la unidad de comparación de precios.
CATEGORIES_SEED = {
    "COSMETICA": {"name": "Cosmética", "normalization": "ml", "checklist": "COSMETICA", "subcategories": ["Cuidado capilar · sérum/cuero cabelludo", "Cuidado de pies", "Otros"]},
    "SUPLEMENTOS": {"name": "Suplementos", "normalization": "unit", "checklist": "SUPLEMENTOS", "subcategories": ["Minerales · magnesio", "Ácidos grasos · omega-3", "Probióticos", "Otros"]},
}
# Biblioteca LINGÜÍSTICA de términos de búsqueda por subcategoría (traducciones de la consulta, NO datos de mercado). Editable por producto.
TERMS_LIBRARY = {
    "serum_capilar": {"ES": ["sérum capilar cuero cabelludo", "tratamiento anticaída cuero cabelludo"], "DE": ["Haarserum Kopfhaut", "Kopfhaut Serum Haarausfall"], "FR": ["sérum cuir chevelu", "sérum anti-chute cheveux"], "IT": ["siero capelli cuoio capelluto", "siero anticaduta capelli"]},
    "magnesio": {"ES": ["magnesio cápsulas"], "DE": ["Magnesium Kapseln"], "FR": ["magnésium gélules"], "IT": ["magnesio capsule"]},
    "omega3": {"ES": ["omega 3 cápsulas"], "DE": ["Omega 3 Kapseln"], "FR": ["oméga 3 capsules"], "IT": ["omega 3 capsule"]},
}
SUBCAT_KEY = [("serum_capilar", ("sérum", "serum", "cuero cabelludo", "capilar")), ("magnesio", ("magnesio", "magnesium")), ("omega3", ("omega",))]


def fld(v=None, status="NO_DISPONIBLE", source="", date=None):
    return {"v": v, "status": status if v is not None else "NO_DISPONIBLE", "source": source, "date": date}


def _today():
    return time.strftime("%Y-%m-%d")


def _clean_field(x, what, numeric=True, hi=1e7):
    """Valida un campo {v,status,source,date}. Un dato VERIFICADO/DOCUMENTADO exige fuente y fecha."""
    if x is None:
        return fld()
    if not isinstance(x, dict):
        raise ValueError("%s: formato inválido" % what)
    v = x.get("v"); st = x.get("status") or ("NO_DISPONIBLE" if v is None else "A_CONFIRMAR")
    if st not in STATUSES:
        raise ValueError("%s: estado inválido" % what)
    if v is None or v == "":
        return fld()
    if numeric and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= hi):
        raise ValueError("%s: valor numérico inválido" % what)
    src = str(x.get("source") or "")[:240]; date = x.get("date") or None
    if date is not None and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date)):
        raise ValueError("%s: fecha AAAA-MM-DD" % what)
    if st in STRONG and (len(src.strip()) < 8 or not date):
        raise ValueError("%s: un dato %s exige fuente (≥ 8 caracteres) y fecha" % (what, st))
    return {"v": v, "status": st, "source": src, "date": date}


def subcat_key(name, subcategory):
    t = ((name or "") + " " + (subcategory or "")).lower()
    for k, kws in SUBCAT_KEY:
        if any(w in t for w in kws):
            return k
    return None


def _slug(s):
    return re.sub(r"[^A-Z0-9]+", "-", (s or "").upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N")).strip("-")[:40]


def seed_products():
    """Productos iniciales: SOLO datos documentados. Lo demás NO_DISPONIBLE."""
    ap = AC.PRODUCT["fields"]; t = "2026-11-16"
    activ = {"id": "PRD-ACTIVCORE-V2", "name": "ACTIVCORE V2", "brand": "ACTIVCORE by AHT", "category": "COSMETICA", "subcategory": "Cuidado capilar · sérum/cuero cabelludo", "version": 1, "version_label": "V2",
             "format": {"content": 100, "unit": "ml", "description": "Sérum leave-on 100 mL", "status": "DOCUMENTADO", "source": ap["format_ml"]["source"]},
             "pvp": {"REF": fld(49.90, "PROPUESTO", "Precio propuesto por el usuario (no aprobado)", "2026-11-09")},
             "costs": {"cogs": fld(10.03, "HISTORICO_A_REVALIDAR", ap["cogs_eur_ex_vat"]["source"], "2026-11-09")},
             "stock": fld(550, "HISTORICO_A_REVALIDAR", ap["stock_units"]["source"], "2026-11-09"), "images": [], "documents": [{"name": "Infografías de empaque y científica (aportadas por el usuario)", "ref": "adjuntos del encargo V0.4.0 (no almacenados)", "date": "2026-11-09", "type": "referencia no verificada"}],
             "regulatory": {"state": "PENDIENTE", "note": "PIF, CPSR, persona responsable UE, CPNP y claims: sin documentación aportada", "date": "2026-11-09"}, "marketplaces": [], "target_markets": ["DE", "FR", "IT", "ES"],
             "dossiers": [{"account": AC.ACCOUNT_ID, "label": "Expediente ACTIVCORE (V0.4.0)"}], "own_asins": {}, "attributes": ["cafeína", "luteolina", "urea", "mentol"], "search_terms": {},
             "reference_competitors": ["Kérastase Genesis", "Nioxin Night Density Rescue", "Redken Aminexil Advanced", "The Ordinary Multi-Peptide", "Bio-Pilixin"], "notes": "Competidores de referencia aportados por el usuario: se usan solo como pistas de búsqueda, no como evidencia de ventas."}
    mg = {"id": "PRD-PHIVITAL-MAGNESIO", "name": "PHIVITAL Magnesio", "brand": "PHIVITAL", "category": "SUPLEMENTOS", "subcategory": "Minerales · magnesio", "version": 1, "version_label": "120 cápsulas",
          "format": {"content": 120, "unit": "unidades", "description": "120 cápsulas", "status": "DOCUMENTADO", "source": "Ficha de Amazon.es indicada por el usuario (2026-10-08)"},
          "pvp": {"ES": fld(17.99, "DOCUMENTADO", "PVP observado en Amazon.es el 2026-10-08 (dato indicado por el usuario)", "2026-10-08"), "REF": fld(17.99, "DOCUMENTADO", "PVP observado en Amazon.es el 2026-10-08 (dato indicado por el usuario)", "2026-10-08")},
          "costs": {}, "stock": fld(), "images": [], "documents": [], "regulatory": {"state": "PENDIENTE", "note": "Sin documentación regulatoria cargada", "date": None}, "marketplaces": ["ES"], "target_markets": ["DE", "FR", "IT", "ES"],
          "dossiers": [{"account": "phivital-pendiente", "label": "Piloto PHIVITAL Magnesio (V0.3)"}], "own_asins": {"ES": "B0F6KQP2WH"}, "attributes": [], "search_terms": {}, "reference_competitors": [],
          "notes": "Lote planificado 600 uds (decisión 2026-10-07): es plan de producción, NO stock verificado. IVA y comisión del suplemento: a confirmar."}
    om = {"id": "PRD-PHIVITAL-OMEGA3", "name": "PHIVITAL Omega-3", "brand": "PHIVITAL", "category": "SUPLEMENTOS", "subcategory": "Ácidos grasos · omega-3", "version": 1, "version_label": "",
          "format": {"content": None, "unit": "unidades", "description": "", "status": "NO_DISPONIBLE", "source": ""}, "pvp": {}, "costs": {}, "stock": fld(), "images": [], "documents": [], "regulatory": {"state": "PENDIENTE", "note": "Ficha mínima: sin datos documentados cargados", "date": None},
          "marketplaces": [], "target_markets": ["DE", "FR", "IT", "ES"], "dossiers": [], "own_asins": {}, "attributes": [], "search_terms": {}, "reference_competitors": [], "notes": "Faltan formato, PVP, costes y stock documentados (aportar desde la ficha en la interfaz)."}
    return [activ, mg, om]


class Catalog:
    def __init__(self, store):
        self.store = store

    # ------------------------------------------------------------ arranque idempotente -----------------------------------------------------
    def ensure(self):
        with self.store.lock:
            ex = self.store.db.execute("SELECT 1 FROM accounts WHERE id=?", (ACCOUNT_ID,)).fetchone()
        if not ex:
            self.store.create_account(ACCOUNT_ID, ACCOUNT_NAME, LEGAL, None, [], actor="system")
        for cid, c in CATEGORIES_SEED.items():
            if not AC._find(self.store, "dataset", "cat:" + cid, ACCOUNT_ID):
                AC._upsert(self.store, "dataset", "cat:" + cid, {"id": cid, **c, "active": True}, "system", ACCOUNT_ID)
        for p in seed_products():
            if not AC._find(self.store, "product", p["id"], ACCOUNT_ID):
                p = self._stamp(p, "system"); p["changelog"] = [{"version": 1, "at": p["updated_at"], "by": "system", "note": "alta inicial con datos documentados"}]
                AC._upsert(self.store, "product", p["id"], p, "system", ACCOUNT_ID)

    @staticmethod
    def _stamp(p, actor):
        p["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); p["updated_by"] = actor; p.setdefault("archived", False); return p

    # ------------------------------------------------------------ categorías ----------------------------------------------------------------
    def categories(self):
        with self.store.lock:
            rows = self.store.db.execute("SELECT id FROM records WHERE account_id=? AND kind='dataset' AND key LIKE 'cat:%' ORDER BY key", (ACCOUNT_ID,)).fetchall()
        return [self.store.get(ACCOUNT_ID, r["id"])["data"] for r in rows]

    def set_category(self, cid, name, normalization, subcategories, checklist, actor):
        cid = _slug(cid or name)
        if not cid or len(cid) > 30:
            raise ValueError("identificador de categoría inválido")
        if normalization not in ("ml", "unit") or checklist not in ("COSMETICA", "SUPLEMENTOS", "GENERICA"):
            raise ValueError("normalización (ml|unit) o checklist (COSMETICA|SUPLEMENTOS|GENERICA) inválidos")
        name = str(name or "").strip()[:60]
        if len(name) < 2:
            raise ValueError("nombre de categoría requerido")
        subs = [str(x).strip()[:80] for x in (subcategories or []) if str(x).strip()][:30]
        d = {"id": cid, "name": name, "normalization": normalization, "checklist": checklist, "subcategories": subs, "active": True}
        AC._upsert(self.store, "dataset", "cat:" + cid, d, actor, ACCOUNT_ID); return d

    def _cat(self, cid):
        r = AC._find(self.store, "dataset", "cat:" + str(cid), ACCOUNT_ID)
        if not r:
            raise ValueError("categoría desconocida: créala primero")
        return r["data"]

    # ------------------------------------------------------------ productos -----------------------------------------------------------------
    def list(self, include_archived=False, category=None):
        with self.store.lock:
            rows = self.store.db.execute("SELECT id FROM records WHERE account_id=? AND kind='product' ORDER BY key", (ACCOUNT_ID,)).fetchall()
        out = []
        for r in rows:
            d = self.store.get(ACCOUNT_ID, r["id"])["data"]
            if (include_archived or not d.get("archived")) and (not category or d["category"] == category):
                out.append(d)
        return out

    def get(self, pid):
        r = AC._find(self.store, "product", str(pid), ACCOUNT_ID)
        return r["data"] if r else None

    def versions(self, pid):
        with self.store.lock:
            rows = self.store.db.execute("SELECT id FROM records WHERE account_id=? AND kind='dataset' AND key LIKE ? ORDER BY key", (ACCOUNT_ID, "ver:" + pid + ":%")).fetchall()
        return [self.store.get(ACCOUNT_ID, r["id"])["data"] for r in rows]

    def _clean(self, b, cur=None):
        """Valida una ficha completa. Los campos no enviados conservan el valor actual (edición parcial)."""
        c = copy.deepcopy(cur) if cur else {}
        def sv(k, mx=120, req=False):
            if k in b:
                v = str(b[k] or "").strip()[:mx]
                if req and not v:
                    raise ValueError("%s es obligatorio" % k)
                c[k] = v
            elif req and not c.get(k):
                raise ValueError("%s es obligatorio" % k)
        sv("name", 80, True); sv("brand", 60, True); sv("subcategory", 80); sv("version_label", 40); sv("notes", 600)
        if "category" in b or not c.get("category"):
            cat = self._cat(b.get("category")); c["category"] = cat["id"]
        cat = self._cat(c["category"])
        if "format" in b:
            f = b["format"] or {}; content = f.get("content")
            if content is not None and (isinstance(content, bool) or not isinstance(content, (int, float)) or not 0 < content <= 100000):
                raise ValueError("formato: contenido inválido")
            unit = f.get("unit") or ("ml" if cat["normalization"] == "ml" else "unidades")
            if unit not in ("ml", "g", "unidades"):
                raise ValueError("formato: unidad ml|g|unidades")
            st = f.get("status") or ("NO_DISPONIBLE" if content is None else "A_CONFIRMAR")
            if st not in STATUSES:
                raise ValueError("formato: estado inválido")
            if content is not None and st in STRONG and len(str(f.get("source") or "").strip()) < 8:
                raise ValueError("formato: dato %s exige fuente" % st)
            c["format"] = {"content": content, "unit": unit, "description": str(f.get("description") or "")[:120], "status": st if content is not None else "NO_DISPONIBLE", "source": str(f.get("source") or "")[:240]}
        if "pvp" in b:
            c["pvp"] = {}
            for k, x in (b["pvp"] or {}).items():
                if k != "REF" and k not in E.VAT:
                    raise ValueError("PVP: país desconocido")
                fx = _clean_field(x, "PVP " + k, hi=10000)
                if fx["v"] is not None:
                    c["pvp"][k] = fx
        if "costs" in b:
            c["costs"] = {}
            for k, x in (b["costs"] or {}).items():
                if not re.match(r"^[a-z_]{2,30}$", str(k)):
                    raise ValueError("coste: nombre inválido (minúsculas y _)")
                fx = _clean_field(x, "coste " + k, hi=100000)
                if fx["v"] is not None:
                    c["costs"][k] = fx
        if "stock" in b:
            c["stock"] = _clean_field(b["stock"], "stock", hi=1e9)
        for k, req in (("images", ("ref",)), ("documents", ("name",)), ("dossiers", ("account",))):
            if k in b:
                if not isinstance(b[k], list) or len(b[k]) > 40 or any(not isinstance(i, dict) or any(not str(i.get(r) or "").strip() for r in req) for i in b[k]):
                    raise ValueError("%s: lista de objetos con %s" % (k, "/".join(req)))
                c[k] = [{kk: str(vv)[:240] for kk, vv in i.items()} for i in b[k]]
        if "regulatory" in b:
            r = b["regulatory"] or {}
            if r.get("state") not in REG_STATES:
                raise ValueError("estado regulatorio inválido")
            c["regulatory"] = {"state": r["state"], "note": str(r.get("note") or "")[:300], "date": r.get("date") or _today()}
        for k in ("marketplaces", "target_markets"):
            if k in b:
                v = [str(x).upper() for x in (b[k] or [])]
                if any(x not in E.VAT for x in v):
                    raise ValueError("%s: país desconocido" % k)
                c[k] = v
        if "own_asins" in b:
            c["own_asins"] = {}
            for k, a in (b["own_asins"] or {}).items():
                if k not in E.VAT or not K.ASIN_RE.match(str(a).upper()):
                    raise ValueError("own_asins: país/ASIN inválido")
                c["own_asins"][k] = str(a).upper()
        for k in ("attributes", "reference_competitors"):
            if k in b:
                c[k] = [str(x).strip()[:80] for x in (b[k] or []) if str(x).strip()][:40]
        if "search_terms" in b:
            c["search_terms"] = {}
            for k, v in (b["search_terms"] or {}).items():
                if k not in LANGS:
                    raise ValueError("términos de búsqueda: idioma ES|DE|FR|IT")
                c["search_terms"][k] = [str(x).strip()[:80] for x in (v or []) if str(x).strip()][:6]
        # ---- V0.6 (F3): SKU, composición, claims, estado comercial, conexiones Amazon, imágenes/dossiers ya existentes ----
        if "sku" in b:
            c["sku"] = re.sub(r"[^A-Za-z0-9._\-]", "", str(b["sku"] or ""))[:40]
        if "commercial_state" in b:
            if b["commercial_state"] not in COMMERCIAL_STATES:
                raise ValueError("estado comercial: " + "|".join(COMMERCIAL_STATES))
            c["commercial_state"] = b["commercial_state"]
        if "composition" in b:
            if not isinstance(b["composition"], list) or len(b["composition"]) > 60:
                raise ValueError("composición: lista de ingredientes (≤60)")
            c["composition"] = []
            for i in b["composition"]:
                i = i if isinstance(i, dict) else {"name": i}
                nm = str(i.get("name") or "").strip()[:80]
                if nm:
                    st = i.get("status") if i.get("status") in STATUSES else "A_CONFIRMAR"
                    c["composition"].append({"name": nm, "amount": str(i.get("amount") or "")[:30], "status": st, "source": str(i.get("source") or "")[:200]})
        if "claims" in b:
            if not isinstance(b["claims"], list) or len(b["claims"]) > 40:
                raise ValueError("claims: lista (≤40)")
            c["claims"] = []
            for i in b["claims"]:
                t = str((i or {}).get("text") or "").strip()[:200]
                if t:
                    ev = str((i or {}).get("evidence") or "").strip()[:240]
                    c["claims"].append({"text": t, "state": "RESPALDADO" if len(ev) >= 8 else "SIN_RESPALDO", "evidence": ev})
        if "amazon_connections" in b:
            c["amazon_connections"] = {}
            for k, v in (b["amazon_connections"] or {}).items():
                if k not in E.VAT:
                    raise ValueError("conexión Amazon: país desconocido")
                v = v or {}
                a = str(v.get("asin") or "").upper()
                if a and not K.ASIN_RE.match(a):
                    raise ValueError("conexión Amazon: ASIN inválido")
                c["amazon_connections"][k] = {"asin": a, "sku": str(v.get("sku") or "")[:40], "state": "SIN_VINCULAR" if not a else "ASIN_DECLARADO_NO_VERIFICADO"}
        c.setdefault("sku", ""); c.setdefault("composition", []); c.setdefault("claims", []); c.setdefault("commercial_state", "PRELANZAMIENTO"); c.setdefault("amazon_connections", {})
        c.setdefault("format", {"content": None, "unit": "ml" if cat["normalization"] == "ml" else "unidades", "description": "", "status": "NO_DISPONIBLE", "source": ""})
        for k, dv in (("pvp", {}), ("costs", {}), ("stock", fld()), ("images", []), ("documents", []), ("dossiers", []), ("marketplaces", []), ("target_markets", ["DE", "FR", "IT", "ES"]), ("own_asins", {}), ("attributes", []), ("reference_competitors", []), ("search_terms", {}), ("notes", ""),
                      ("regulatory", {"state": "PENDIENTE", "note": "", "date": None}), ("subcategory", ""), ("version_label", "")):
            c.setdefault(k, dv)
        return c

    def create(self, b, actor):
        c = self._clean(b); base = "PRD-" + (_slug(c["name"]) or "PRODUCTO"); pid = (b.get("id") or base).upper()
        if not ID_RE.match(pid):
            raise ValueError("ID inválido (PRD-LETRAS-NUMEROS)")
        n, cand = 1, pid
        while self.get(cand):
            if b.get("id"):
                raise ValueError("ya existe un producto con ese ID")
            n += 1; cand = "%s-%d" % (pid, n)
        c["id"] = cand; c["version"] = 1; c["archived"] = False; self._stamp(c, actor)
        c["changelog"] = [{"version": 1, "at": c["updated_at"], "by": actor, "note": "alta"}]
        AC._upsert(self.store, "product", cand, c, actor, ACCOUNT_ID); return c

    def update(self, pid, b, actor, note=""):
        cur = self.get(pid)
        if not cur:
            raise ValueError("producto inexistente")
        if cur.get("archived"):
            raise ValueError("producto archivado: restáuralo antes de editarlo")
        new = self._clean(b, cur); new["id"] = pid; new["archived"] = False
        snap = copy.deepcopy(cur); AC._upsert(self.store, "dataset", "ver:%s:%04d" % (pid, cur["version"]), snap, actor, ACCOUNT_ID)  # snapshot inmutable de la versión anterior
        new["version"] = cur["version"] + 1; self._stamp(new, actor)
        new["changelog"] = (cur.get("changelog") or [])[-49:] + [{"version": new["version"], "at": new["updated_at"], "by": actor, "note": str(note or "edición")[:120]}]
        AC._upsert(self.store, "product", pid, new, actor, ACCOUNT_ID); return new

    def archive(self, pid, archived, actor):
        cur = self.get(pid)
        if not cur:
            raise ValueError("producto inexistente")
        cur["archived"] = bool(archived); self._stamp(cur, actor)
        cur["changelog"] = (cur.get("changelog") or [])[-49:] + [{"version": cur["version"], "at": cur["updated_at"], "by": actor, "note": "archivado" if archived else "restaurado"}]
        AC._upsert(self.store, "product", pid, cur, actor, ACCOUNT_ID); return cur

    # ------------------------------------------------------------ contexto de análisis europeo -----------------------------------------------
    def completeness(self, p):
        """Qué falta en la ficha (para mostrar «NO DISPONIBLE» sin inventar)."""
        miss = []
        if p["format"]["content"] is None:
            miss.append("formato/contenido")
        if "REF" not in p["pvp"] and not p["pvp"]:
            miss.append("PVP de referencia")
        if not p["costs"]:
            miss.append("costes con fuente y fecha")
        if p["stock"]["v"] is None:
            miss.append("stock verificado")
        if not p["images"]:
            miss.append("imágenes")
        if not p["documents"]:
            miss.append("documentos")
        if p["regulatory"]["state"] == "PENDIENTE":
            miss.append("documentación regulatoria")
        if not p.get("composition"):
            miss.append("composición")
        if not p.get("sku") and not any(v.get("asin") for v in (p.get("amazon_connections") or {}).values()) and not p.get("own_asins"):
            miss.append("SKU/ASIN")
        return miss

    def ctx(self, pid):
        p = self.get(pid)
        if not p:
            return None
        cat = self._cat(p["category"]); legacy = pid == "PRD-ACTIVCORE-V2"
        ref = (p["pvp"].get("REF") or next(iter(p["pvp"].values()), None) or {}).get("v")
        c = p["format"]["content"]
        cost = p["costs"].get("cogs")
        out = {"account": AC.ACCOUNT_ID if legacy else ACCOUNT_ID, "prefix": "" if legacy else pid + ":", "product": AC.PRODUCT if legacy else p, "card": p, "product_id": pid, "content": c, "norm": cat["normalization"], "pvp_ref": ref,
               "category": cat["checklist"], "pvps": None if legacy else self.pvp_scenarios(ref),
               "cost_text": "Coste unitario: %s" % ("%.2f € (%s, %s)" % (cost["v"], cost["status"], cost["date"] or "sin fecha") if cost else "NO DISPONIBLE"),
               "stock_text": "Stock: %s" % ("%s uds (%s)" % (p["stock"]["v"], p["stock"]["status"]) if p["stock"]["v"] is not None else "NO DISPONIBLE (sin stock verificado)")}
        if legacy:
            out["claims"] = AC.CLAIMS
        else:
            out["claims"] = []; out["reg_findings"] = ["Sin documentación regulatoria cargada para este producto" if p["regulatory"]["state"] == "PENDIENTE" else "Estado regulatorio: " + p["regulatory"]["state"]]
        return out

    @staticmethod
    def pvp_scenarios(ref):
        """Escenarios de PVP alrededor del PVP de referencia (HIPÓTESIS de trabajo: ×0,7…×1,3, redondeo a .x0). Sin PVP de referencia → sin escenarios."""
        if not ref:
            return []
        return sorted({round(ref * m, 1) for m in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3)})

    def search_terms(self, p, country):
        """(términos, origen). Origen: «producto» (editados), «biblioteca» (traducción genérica de subcategoría) o None si faltan."""
        lang = {"DE": "DE", "FR": "FR", "IT": "IT", "ES": "ES", "UK": None}.get(country)
        if not lang:
            return [], None
        own = (p.get("search_terms") or {}).get(lang)
        if own:
            return own[:6], "producto"
        k = subcat_key(p["name"], p.get("subcategory"))
        if k and TERMS_LIBRARY[k].get(lang):
            return TERMS_LIBRARY[k][lang][:6], "biblioteca (traducción genérica de la subcategoría)"
        return [], None
