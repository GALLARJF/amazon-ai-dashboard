"""ACTIVCORE V2 · expediente real (parcial), claims, checklist regulatorio, panel de coworkers y servicio de inteligencia europea (V0.4.0).
Vive en su propia cuenta («activcore-eu») usando registros product/plan/dataset: NO toca el motor de expedientes de V0.3 ni el piloto PHIVITAL ni el sintético.
Todo dato lleva su procedencia. Las infografías aportadas son REFERENCIA de producto/diseño, no fuente de ventas, rankings, claims ni precios."""
import copy, csv, io, json, math, statistics, time
from . import eu as E, keepa as K

ACCOUNT_ID = "activcore-eu"
ACCOUNT_NAME = "ACTIVCORE · Inteligencia europea"
LEGAL = "Advanced Hybrid Technologies S.L. (titular del Seller Central: POR CONFIRMAR)"
SRC_USER = "Indicado por el usuario en el encargo V0.4.0"
SRC_INFO = "Infografía aportada por el usuario (referencia de producto/diseño; NO verificado)"
INFO_HIST = "Dato histórico del usuario: reconfirmar antes de usar como actual"

PRODUCT = {
    "name": "ACTIVCORE V2", "brand": "ACTIVCORE by AHT", "company": "Advanced Hybrid Technologies S.L.", "category": "Cosmética capilar · sérum leave-on para el cuero cabelludo (sin aclarado)",
    "regulatory_class": "Cosmético (Reglamento (CE) 1223/2009). No es medicamento ni complemento alimenticio.", "technology": "CaffeineDES™ (marca comercial)",
    "fields": {
        "format_ml": {"v": 100, "status": "DOCUMENTADO", "source": SRC_USER + " · envase de las infografías"},
        "pvp_initial_eur": {"v": 49.90, "status": "PROPUESTO", "source": SRC_USER + " (precio propuesto, no aprobado)"},
        "pvp_intro_eur": {"v": None, "status": "NO_DISPONIBLE", "source": "No definido"},
        "cogs_eur_ex_vat": {"v": 10.03, "status": "HISTORICO_A_REVALIDAR", "source": SRC_USER + " · coste unitario histórico sin IVA; NO es coste puesto en Amazon"},
        "stock_units": {"v": 550, "status": "HISTORICO_A_REVALIDAR", "source": SRC_USER + " · existencias históricas; NO es stock disponible hoy"},
        "dose_ml_per_day": {"v": 2, "status": "PROPUESTO", "source": SRC_USER + " · depende del sistema de dispensación (cuentagotas) confirmado"},
        "duration_days": {"v": 50, "status": "TEORICO", "source": "100 mL ÷ 2 mL/día; teórico hasta confirmar dosis y dispensación"},
        "label_languages": {"v": ["ES", "DE", "FR", "IT", "EN"], "status": "BORRADOR_DE_DISEÑO", "source": SRC_INFO + " · modo de empleo y precauciones en 5 idiomas"},
        "eu_responsible_person": {"v": None, "status": "NO_DISPONIBLE", "source": "La maqueta indica «[Dirección a confirmar, según CPNP]»"},
        "pao": {"v": "12M", "status": "BORRADOR_DE_DISEÑO", "source": SRC_INFO},
    },
    "inci_draft": ["Propylene Glycol", "Betaine", "Lactic Acid", "Urea", "Caffeine", "Menthol", "Luteolin"],
    "inci_status": "BORRADOR de maqueta: el orden y los porcentajes deben contrastarse con la fórmula y el PIF vigentes (no modificar formulaciones sin autorización).",
    "formula_reference": {"basis_g": 10.05, "status": "REFERENCIA_INFOGRAFIA (fórmula «congelada» indicada por el usuario; no es el PIF)", "rows": [
        ["Propylene Glycol", 8.329, 82.90], ["Lactic Acid", 0.545, 5.42], ["Betaine", 0.591, 5.88], ["Urea", 0.366, 3.64], ["Caffeine", 0.098, 0.98], ["Luteolin", 0.021, 0.21], ["Menthol", 0.097, 0.97]],
        "note": "La tabla suma 10,05 g: es una base de referencia, NO la composición por envase ni un coste."},
    "discrepancies": [
        {"id": "D1", "text": "Coste unitario: 10,03 € (dato histórico del encargo) frente a 6,91 € (500 uds) y 6,40 € (1.000 uds) en la infografía de economía. No se usa ninguno como verdad: se parte de 10,03 € marcado A REVALIDAR.", "action": "Pedir presupuesto/factura vigente (coste puesto en almacén Amazon, sin IVA)."},
        {"id": "D2", "text": "La infografía concluye «ESPAÑA · primer país». El encargo exige no elegir España por defecto: esa conclusión NO se usa como evidencia ni en el ranking.", "action": "El ranking se construye solo con datos con fuente y fecha."},
        {"id": "D3", "text": "Las ventas estimadas, valoraciones y «países con el producto» de competidores en la infografía no tienen fuente verificable.", "action": "Sustituir por consultas Keepa con fecha; hasta entonces, referencia no verificada."},
        {"id": "D4", "text": "La infografía calcula «1,00 € por día» y «50 días» como si la dosis y el cuentagotas estuvieran confirmados.", "action": "Confirmar dosificación real del cuentagotas antes de usar precio/día."},
        {"id": "D5", "text": "Dirección de la persona responsable en la UE pendiente en las maquetas.", "action": "Designar persona responsable y notificar en CPNP antes de comercializar."},
        {"id": "D6", "text": "La maqueta indica «Sin claims de absorción o sensación hasta evaluar la muestra real» y lista claims de resultados («resultados visibles», «menos caída»…).", "action": "Aplicar el registro de claims: no publicar los pendientes."},
    ],
}

# Registro de claims (Reglamento (UE) 655/2013: conformidad legal, veracidad, respaldo probatorio, honestidad, imparcialidad, decisión informada)
CLAIMS = [
    ("Cuida el cuero cabelludo", "PENDIENTE_EVIDENCIA", "Función cosmética genérica atribuible a la fórmula; falta evidencia del producto final.", "Informe de evaluación de la fórmula / test de uso."),
    ("Ayuda a la energía celular / estimula la energía del folículo (mitocondria)", "REFORMULAR_O_ELIMINAR", "Atribuye un efecto fisiológico/mecanismo: riesgo de claim farmacológico y sin prueba sobre el producto terminado.", "Eliminar el mecanismo; si se mantiene, ensayo del producto final y revisión regulatoria."),
    ("Menos caída (aparente) / anticaída", "REFORMULAR_O_ELIMINAR", "Prevención de la caída del cabello se acerca a finalidad terapéutica; exige evidencia sólida y asesoría regulatoria.", "Estudio clínico/instrumental con protocolo; revisión por experto en claims."),
    ("Mayor fuerza capilar / cabello con más fuerza", "PENDIENTE_EVIDENCIA", "Resultado sobre el cabello sin ensayo del producto.", "Test instrumental o de consumidores con metodología."),
    ("Mejor circulación / microcirculación", "REFORMULAR_O_ELIMINAR", "Función fisiológica: riesgo de claim medicinal.", "Eliminar; solo sensación de confort si se evidencia."),
    ("Más energía folicular / estimulación folicular", "REFORMULAR_O_ELIMINAR", "Efecto fisiológico no sustentado.", "Eliminar o respaldar con ensayo y revisión regulatoria."),
    ("Menos inflamación (aparente) / reducción de inflamación", "REFORMULAR_O_ELIMINAR", "Término terapéutico (medicamento); no apto para cosmético.", "Eliminar."),
    ("Resultados visibles en semanas de uso continuado", "PENDIENTE_EVIDENCIA", "Promesa temporal sin datos del producto.", "Estudio de uso con duración y N documentados."),
    ("Antioxidante / protege del estrés oxidativo (luteolina)", "PENDIENTE_EVIDENCIA", "Propiedad del ingrediente; no demuestra efecto del producto terminado.", "Ensayo sobre producto final o formulación conservadora («contiene luteolina»)."),
    ("Hidratación y equilibrio / mejora de la función barrera (urea)", "PENDIENTE_EVIDENCIA", "Claim cosmético habitual pero requiere respaldo para este producto.", "Test de hidratación del cuero cabelludo (corneometría) o consumidores."),
    ("Sensación refrescante y de confort (mentol)", "PENDIENTE_EVIDENCIA", "Claim sensorial directamente atribuible al mentol; confirmar en muestra real.", "Test sensorial."),
    ("Sin aclarado · uso diario · leave-on", "CONFORME_DESCRIPTIVO", "Describe el modo de uso, no un efecto.", "Coherente con etiqueta y modo de empleo aprobados."),
    ("Sin agua / anhidro", "PENDIENTE_EVIDENCIA", "Afirmación de composición verificable.", "Análisis de contenido en agua del lote (Karl Fischer)."),
    ("Fórmula de origen responsable", "REFORMULAR_O_ELIMINAR", "Vaga/ambiental sin criterio verificable (riesgo de greenwashing).", "Eliminar o concretar con certificación/ACV."),
    ("Fabricado en España", "PENDIENTE_EVIDENCIA", "Verificable por documentación del fabricante.", "Ficha/certificado del fabricante y trazabilidad."),
    ("Textura fluida, no grasa, rápida absorción", "PENDIENTE_EVIDENCIA", "La propia maqueta exige evaluar la muestra real antes de afirmarlo.", "Test sensorial de la muestra real."),
    ("Excelente relación calidad-precio", "REFORMULAR_O_ELIMINAR", "Valoración subjetiva/comparativa no verificable.", "Eliminar de contenidos de venta."),
    ("«1,00 € por día de uso» / «50 días»", "PENDIENTE_EVIDENCIA", "Cálculo válido solo con dosis y dispensación confirmadas.", "Medir volumen del cuentagotas y dosis real."),
    ("Comparativas con Kérastase/Nioxin/Redken/The Ordinary/Bio-Pilixin", "REFORMULAR_O_ELIMINAR", "Publicidad comparativa: solo con datos objetivos y verificables; no para el listing.", "Uso interno únicamente; revisión legal si se publica."),
]
USABLE = []  # claims utilizables con respaldo suficiente: NINGUNO hoy (no hay evidencia aportada)

CHECK_ITEMS = [  # (id, texto, referencia, aplica_a)
    ("pif", "Expediente de información del producto (PIF) completo y accesible en la UE", "Reglamento (CE) 1223/2009, art. 11"),
    ("cpsr", "Informe de seguridad (CPSR) firmado por evaluador cualificado", "Reglamento (CE) 1223/2009, art. 10 y Anexo I"),
    ("persona_responsable", "Persona responsable en la UE designada y con dirección en el etiquetado", "Reglamento (CE) 1223/2009, art. 4 y 19"),
    ("cpnp", "Notificación en el CPNP antes de la comercialización", "Reglamento (CE) 1223/2009, art. 13"),
    ("inci", "Lista INCI en orden decreciente y conforme a la fórmula", "Reglamento (CE) 1223/2009, art. 19"),
    ("lote_pao", "Número de lote y durabilidad/PAO", "Reglamento (CE) 1223/2009, art. 19"),
    ("precauciones", "Precauciones de empleo (mentol, menores de 3 años, uso externo)", "Reglamento (CE) 1223/2009, art. 19 y 20"),
    ("idiomas", "Idiomas del etiquetado exigidos por el país de venta", "Reglamento (CE) 1223/2009, art. 19(5) y normativa nacional (A VERIFICAR por país)"),
    ("claims", "Claims revisados y respaldados", "Reglamento (UE) 655/2013"),
    ("amazon_politicas", "Requisitos de Amazon para cosméticos en el marketplace (documentación, categoría restringida)", "Políticas del marketplace (A VERIFICAR en Seller Central)"),
    ("epr_envases", "Responsabilidad ampliada del productor de envases del país (registro/símbolos)", "Normativa nacional (A VERIFICAR por país: p. ej. DE, FR, IT, ES)"),
    ("iva_registro", "Registro de IVA/representante fiscal y régimen OSS/FBA paneuropeo", "Normativa fiscal nacional (A VERIFICAR con asesor)"),
]
STATES = {"OK", "PENDIENTE", "NO_CUMPLE", "NO_APLICA"}


def default_compliance(countries=None, items=None):
    return {c: {i: {"state": "PENDIENTE", "evidence": "", "date": None} for i, _, _ in (items or CHECK_ITEMS)} for c in (countries or E.COUNTRIES + E.EXTRA)}


def ensure(store):
    """Crea (idempotente) la cuenta y el maestro de producto ACTIVCORE. No toca ninguna otra cuenta."""
    with store.lock:
        exists = store.db.execute("SELECT 1 FROM accounts WHERE id=?", (ACCOUNT_ID,)).fetchone()
    if not exists:
        store.create_account(ACCOUNT_ID, ACCOUNT_NAME, LEGAL, None, [], actor="system")
    if not _find(store, "product", "activcore_v2"):
        store.put(ACCOUNT_ID, "product", PRODUCT, key="activcore_v2")


def _find(store, kind, key, account=ACCOUNT_ID):
    with store.lock:
        r = store.db.execute("SELECT id FROM records WHERE account_id=? AND kind=? AND key=?", (account, kind, key)).fetchone()
    return store.get(account, r["id"]) if r else None


def _upsert(store, kind, key, data, actor="system", account=ACCOUNT_ID):
    r = _find(store, kind, key, account)
    return store.put(account, kind, data, id_=r["id"] if r else None, key=key, actor=actor)


SUPP_CHECK_ITEMS = [  # complementos alimenticios (referencias a VERIFICAR con asesor regulatorio)
    ("formula_dossier", "Fórmula, ficha técnica y especificaciones de materias primas documentadas", "Directiva 2002/46/CE (complementos alimenticios)"),
    ("ingredientes", "Ingredientes y formas químicas permitidos en cada país (nutrientes/sustancias)", "Directiva 2002/46/CE y normativa nacional (A VERIFICAR por país)"),
    ("dosis_max", "Dosis diaria dentro de los máximos nacionales y avisos obligatorios", "Normativa nacional de límites (A VERIFICAR por país)"),
    ("notificacion", "Notificación/registro de puesta en el mercado ante la autoridad del país", "p. ej. AESAN (ES), BVL (DE), DGCCRF (FR), Ministero della Salute (IT): A VERIFICAR"),
    ("etiquetado", "Etiquetado alimentario: ingredientes, alérgenos, valores diarios, lote, caducidad", "Reglamento (UE) 1169/2011"),
    ("claims_salud", "Declaraciones nutricionales y de propiedades saludables autorizadas (solo registro UE)", "Reglamento (CE) 1924/2006 y registro de declaraciones autorizadas"),
    ("idiomas", "Idiomas del etiquetado exigidos por el país de venta", "Reglamento (UE) 1169/2011, art. 15 y normativa nacional"),
    ("trazabilidad", "Trazabilidad, lote y fabricante autorizado (registro sanitario)", "Reglamento (CE) 178/2002 y 852/2004"),
    ("amazon_politicas", "Requisitos de Amazon para complementos en el marketplace (documentación, categoría restringida)", "Políticas del marketplace (A VERIFICAR en Seller Central)"),
    ("epr_envases", "Responsabilidad ampliada del productor de envases del país", "Normativa nacional (A VERIFICAR por país)"),
    ("iva_registro", "Tipo de IVA de complementos y registro/representante fiscal (OSS/FBA paneuropeo)", "Normativa fiscal nacional (A VERIFICAR con asesor)"),
]
CHECK_BY_CAT = {"COSMETICA": CHECK_ITEMS, "SUPLEMENTOS": SUPP_CHECK_ITEMS}


class EUService:
    def __init__(self, store, keepa, ctx=None):
        """ctx: contexto de producto del catálogo. Sin ctx = ACTIVCORE heredado (cuenta activcore-eu, claves sin prefijo)."""
        self.store, self.keepa = store, keepa
        c = ctx or {}
        self.account = c.get("account", ACCOUNT_ID); self.prefix = c.get("prefix", ""); self.legacy = not self.prefix
        self.product = c.get("product") or PRODUCT; self.card = c.get("card"); self.pid = c.get("product_id", "activcore_v2")
        self.content = c.get("content") or PRODUCT["fields"]["format_ml"]["v"]; self.norm = c.get("norm", "ml"); self.pvp_default = c.get("pvp_ref") if "pvp_ref" in c else 49.90; self.pvps = c.get("pvps")
        self.cost_text = c.get("cost_text") or "IVA y comisión verificados; coste 10,03 € histórico a revalidar"; self.stock_text = c.get("stock_text") or "550 uds históricas (no es stock actual)"
        self.reg_findings = c.get("reg_findings") or ["PIF/CPSR/persona responsable/CPNP sin documentación aportada", "Dirección de persona responsable pendiente en maquetas"]
        self.category = c.get("category", "COSMETICA"); self.claims = c["claims"] if "claims" in c else CLAIMS; self.items = CHECK_BY_CAT.get(self.category, CHECK_ITEMS)

    def _f(self, kind, key):
        return _find(self.store, kind, self.prefix + key, self.account)

    def _u(self, kind, key, data, actor="system"):
        return _upsert(self.store, kind, self.prefix + key, data, actor, self.account)

    # ------------------------------------------------------------------ almacenamiento editable -----------------------------------------
    def assumptions(self):
        r = self._f("plan", "assumptions")
        base = E.default_assumptions()
        if not self.legacy:  # V0.6: un producto NUNCA hereda los costes de ACTIVCORE; parte de los costes de SU ficha (o NO_DISPONIBLE)
            costs = (self.card or {}).get("costs") or {}
            for c in base:
                for k in ("cogs", "inbound", "prep", "fulfillment", "storage", "returns", "promo", "other"):
                    f = costs.get(k)
                    base[c][k] = E.fld(f["v"], f["status"], f.get("source") or "ficha del producto", f.get("date") or E.TODAY_REF) if f and f.get("v") is not None else E.fld()
                if self.category != "COSMETICA" and base[c]["referral"]["status"] == "VERIFICADO":
                    base[c]["referral"] = {**base[c]["referral"], "status": "A_CONFIRMAR", "source": base[c]["referral"]["source"] + " · tarifa de Belleza aplicada de forma orientativa a otra categoría: CONFIRMAR la categoría real del producto"}
        if r:
            for c, a in r["data"].items():
                if c in base:
                    base[c].update({k: v for k, v in a.items() if k in base[c]})
        return base

    def set_assumption(self, country, field, value, status, source, actor):
        c = str(country).upper()
        if c not in E.VAT or field not in E.FIELDS + ["ads_acos"]:
            raise ValueError("país o campo desconocido")
        if status not in E.STATUSES:
            raise ValueError("estado inválido")
        if field == "referral":
            raise ValueError("la comisión solo se modifica editando las tablas verificadas (no desde la interfaz)")
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or (field in ("vat", "ads_acos") and value > 1)):
            raise ValueError("valor inválido (importes ≥ 0; IVA y ACoS como fracción 0–1)")
        if status in ("VERIFICADO", "DOCUMENTADO") and not (isinstance(source, str) and len(source.strip()) >= 8):
            raise ValueError("un dato VERIFICADO/DOCUMENTADO exige indicar la fuente (≥ 8 caracteres)")
        a = self.assumptions(); a[c][field] = E.fld(None if value is None else float(value), status if value is not None else "NO_DISPONIBLE", str(source or "")[:200], time.strftime("%Y-%m-%d"))
        self._u("plan", "assumptions", a, actor); return a[c]

    def load_hypotheses(self, countries, values, actor):
        a = self.assumptions()
        for c in countries:
            if c in a:
                E.apply_hypotheses(a[c], values)
        self._u("plan", "assumptions", a, actor); return a

    def settings(self):
        r = self._f("plan", "settings")
        return {"weights": dict(E.WEIGHTS), "pvp_ref": self.pvp_default, "min_asins": 8, "min_coverage": 0.60, "include_suggested": False, "acos_target": None, **(r["data"] if r else {})}

    def set_settings(self, b, actor):
        s = self.settings()
        if "weights" in b:
            w = b["weights"]
            if not isinstance(w, dict) or set(w) != set(E.CRITERIA) or any(isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 for v in w.values()) or abs(sum(w.values()) - 100) > 1e-6:
                raise ValueError("los pesos deben ser los 5 criterios, no negativos y sumar 100")
            s["weights"] = {k: float(v) for k, v in w.items()}
        for k, lo, hi in (("pvp_ref", 1, 1000), ("min_asins", 1, 50), ("min_coverage", 0.1, 1.0), ("acos_target", 0, 1)):
            if k in b and b[k] is not None:
                if isinstance(b[k], bool) or not isinstance(b[k], (int, float)) or not lo <= b[k] <= hi:
                    raise ValueError("%s fuera de rango" % k)
                s[k] = b[k]
        if "include_suggested" in b:
            s["include_suggested"] = b["include_suggested"] is True
        self._u("plan", "settings", s, actor); return s

    def registry(self):
        out = {}
        with self.store.lock:
            rows = self.store.db.execute("SELECT id FROM records WHERE account_id=? AND kind='dataset' AND key LIKE ?", (self.account, self.prefix + "reg:%")).fetchall()
        for r in rows:
            d = self.store.get(self.account, r["id"])["data"]; out.setdefault(d["country"], {})[d["asin"]] = d
        return out

    def foreign_asins(self, country):
        """ASIN registrados por OTROS productos (la caché de Keepa es compartida y no debe contaminar a este producto)."""
        out = set()
        with self.store.lock:
            rows = self.store.db.execute("SELECT key FROM records WHERE kind='dataset' AND key LIKE ?", ("%reg:" + str(country).upper() + ":%",)).fetchall()
        for r in rows:
            k = r["key"]
            if not k.startswith(self.prefix + "reg:") or (self.legacy and not k.startswith("reg:")):
                out.add(k.rsplit(":", 1)[-1])
        return out

    def scoped_records(self, country):
        """Registros Keepa en caché que pertenecen a ESTE producto. Heredado: todo lo no registrado por otro producto. Resto: solo lo registrado (descubierto o manual)."""
        recs = self.keepa.cached_records(country) if country in K.DOMAINS else []
        reg = self.registry().get(country, {})
        if self.legacy:
            f = self.foreign_asins(country); return [r for r in recs if r["asin"] not in f or r["asin"] in reg]
        return [r for r in recs if r["asin"] in reg]

    def set_competitor(self, country, asin, comparability, actor, note=""):
        c = str(country).upper(); a = str(asin).upper()
        if comparability not in ("ALTA", "MEDIA", "BAJA") or c not in E.VAT or not K.ASIN_RE.match(a):
            raise ValueError("país/ASIN/comparabilidad inválidos")
        d = {"country": c, "asin": a, "comparability": comparability, "status": "CONFIRMADA", "confirmed_by": actor, "confirmed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "note": str(note)[:200]}
        old = self._f("dataset", "reg:%s:%s" % (c, a))
        if old:
            d["score"] = old["data"].get("score"); d["reason"] = old["data"].get("reason"); d["suggested"] = old["data"].get("suggested"); d["automatic_was"] = old["data"].get("comparability")
        self._u("dataset", "reg:%s:%s" % (c, a), d, actor); return d

    def register_candidate(self, country, asin, comparability, score, reason, source, actor="descubrimiento"):
        """Alta AUTOMÁTICA (puntuación determinista, revisable). No pisa una confirmación humana."""
        c = str(country).upper(); a = str(asin).upper(); old = self._f("dataset", "reg:%s:%s" % (c, a))
        if old and old["data"].get("status") == "CONFIRMADA":
            return old["data"]
        d = {"country": c, "asin": a, "comparability": comparability, "suggested": comparability, "status": "AUTOMATICA", "score": score, "reason": str(reason)[:200], "source": source, "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        self._u("dataset", "reg:%s:%s" % (c, a), d, actor); return d

    def compliance(self):
        r = self._f("dataset", "compliance"); base = default_compliance(None, self.items)
        if r:
            for c, items in r["data"].items():
                if c in base:
                    base[c].update(items)
        return base

    def set_compliance(self, country, item, state, evidence, actor):
        c = str(country).upper()
        if c not in E.VAT or item not in {i for i, _, _ in self.items} or state not in STATES:
            raise ValueError("país/requisito/estado inválido")
        if state == "OK" and not (isinstance(evidence, str) and len(evidence.strip()) >= 8):
            raise ValueError("marcar OK exige describir la evidencia (documento, fecha, referencia)")
        d = self.compliance(); d[c][item] = {"state": state, "evidence": str(evidence or "")[:300], "date": time.strftime("%Y-%m-%d")}
        self._u("dataset", "compliance", d, actor); return d[c][item]

    # ------------------------------------------------------------------ cálculo -------------------------------------------------------------
    def country_data(self):
        s = self.settings(); a = self.assumptions(); comp = self.compliance(); reg = self.registry(); data = {}
        for c in E.COUNTRIES:
            sup = c in K.DOMAINS
            recs = self.scoped_records(c) if sup else []
            bm = E.benchmark(recs, reg.get(c, {}), include_suggested=s["include_suggested"], norm=self.norm) if recs else None
            ec = None if (c in E.CURRENCY or not s["pvp_ref"]) else E.unit_economics(s["pvp_ref"], a[c], s["acos_target"])
            states = {i: v["state"] for i, v in comp[c].items() if v["state"] != "NO_APLICA"}
            data[c] = {"benchmark": bm, "economics": ec, "pvp100": (s["pvp_ref"] / self.content * 100) if s["pvp_ref"] and self.content else None, "compliance": states, "growth": self._growth(bm), "keepa_supported": sup}
        return data

    @staticmethod
    def _growth(bm, min_days=90):
        """Pendiente del BSR mediano (positiva = mejora de posición). Requiere ≥ 90 días de historial en ≥ min_asins comparables confirmados; si no, None."""
        if not bm:
            return None
        ch = []
        for e in bm["rows"]:
            if e["comparability_status"] in E.USABLE_ST and e["comparability"] in ("ALTA", "MEDIA") and len(e.get("bsr_history") or []) >= 3:
                h = e["bsr_history"]; t0 = time.mktime(time.strptime(h[0][0], "%Y-%m-%d")); t1 = time.mktime(time.strptime(h[-1][0], "%Y-%m-%d"))
                if (t1 - t0) / 86400 >= min_days and h[0][1] > 0:
                    ch.append((h[0][1] - h[-1][1]) / h[0][1])
        return round(max(-0.5, min(0.5, statistics.median(ch))), 3) if len(ch) >= 8 else None

    def ranking(self):
        s = self.settings()
        return E.rank(self.country_data(), s["weights"], {"min_asins": s["min_asins"], "min_coverage": s["min_coverage"]})

    def economics_table(self, pvps=None):
        s = self.settings(); a = self.assumptions(); out = {}; pvps = pvps or self.pvps
        for c in E.COUNTRIES + E.EXTRA:
            if pvps is not None and len(pvps) == 0:
                out[c] = [{"pvp_gross": None, "net_price": None, "referral_fee": None, "complete": False, "missing": ["PVP de referencia"], "label": "NO CALCULABLE: el producto no tiene PVP de referencia documentado/propuesto"}]; continue
            out[c] = E.scenarios(a[c], pvps, s["acos_target"]) if c not in E.CURRENCY else [{"pvp_gross": p, "complete": False, "missing": ["tipo de cambio y precios locales"], "label": "NO EVALUABLE: moneda local (%s)" % E.CURRENCY[c]} for p in (pvps or E.PVP_SCENARIOS)]
        return out

    # ------------------------------------------------------------------ exportaciones CSV (nunca inventan filas) -------------------------
    def csv_benchmark(self):
        recs = [r for c in K.DOMAINS for r in self.scoped_records(c)]
        return self.keepa.export_csv_records(recs) if recs else "country,marketplace,asin,brand,title,url,volume_ml,volume_source,price,currency,price_source,price_list,bsr,rating,reviews,offers_new,available,seller,history_points_price,fetched_at,source,evidence_quality,injection_suspect\n# ESTADO: PENDIENTE — sin consultas Keepa en caché. No hay registros reales todavía.\n"

    def csv_economics(self):
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(["country", "pvp_gross_eur", "vat_rate", "net_price", "cogs_eur", "referral_fee", "contribution_before_ads", "margin_before_ads", "breakeven_acos_ex_vat", "breakeven_acos_inc_vat", "complete", "status_mix", "missing", "label"])
        for c, rows in self.economics_table().items():
            for e in rows:
                f = lambda k: "NO DISPONIBLE" if e.get(k) is None else e.get(k)
                w.writerow([c, e["pvp_gross"], f("vat_rate"), f("net_price"), (e.get("inputs") or {}).get("cogs", {}).get("v", "NO DISPONIBLE") if e.get("inputs") else "NO DISPONIBLE", f("referral_fee"), f("contribution_before_ads"), f("margin_before_ads"), f("breakeven_acos_ex_vat"), f("breakeven_acos_inc_vat"), e.get("complete"), "|".join(e.get("status_mix", [])), "|".join(e.get("missing", [])), e.get("label", "")])
        return buf.getvalue()

    def csv_ranking(self):
        r = self.ranking(); buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(["country", "estado", "posicion", "puntuacion", "cobertura", "atractivo", "viabilidad"] + E.CRITERIA + ["falta"])
        for p in r["ranking"] + r["pending"]:
            w.writerow([p["country"], "EVALUABLE" if p["evaluable"] else "NO EVALUABLE", p.get("rank", ""), "" if p["score"] is None else p["score"], p["coverage"], "" if p["attractiveness"] is None else p["attractiveness"], "" if p["viability"] is None else p["viability"]]
                       + [p["criteria"][k]["score"] if p["criteria"][k]["status"] == "EVALUADO" else "NO EVALUABLE" for k in E.CRITERIA] + [" | ".join(m["criterio"] + ": " + "; ".join(m["falta"]) for m in p["missing"])])
        w.writerow([]); w.writerow(["# pesos", *[f"{k}={v}" for k, v in r["weights"].items()]]); w.writerow(["# recomendación", r["launch"] or "SIN RECOMENDACIÓN (faltan datos)"])
        return buf.getvalue()

    # ------------------------------------------------------------------ panel de coworkers (estados honestos) -------------------------------
    def coworker_panel(self):
        kst = K.public_status(self.keepa.cfg_fn()); led = self.keepa.ledger(200); ok_runs = [x for x in led if x["op"] == "product" and x["status"] in ("OK", "INCOMPLETA")]
        reg = self.registry(); n_reg = sum(len(v) for v in reg.values()); n_recs = sum(len(self.scoped_records(c)) for c in K.DOMAINS); a = self.assumptions(); comp = self.compliance()
        n_conf = sum(1 for v in reg.values() for d in v.values() if d.get("status") == "CONFIRMADA"); n_auto = n_reg - n_conf
        pr = self._f("product", "activcore_v2") if self.legacy else None; link = {"account": self.account, "record": pr["id"] if pr else None, "product": self.pid}
        ec = [E.unit_economics(self.settings()["pvp_ref"], a[c]) if self.settings()["pvp_ref"] else {"complete": False} for c in ("DE", "FR", "IT", "ES")]
        n_complete = sum(1 for e in ec if e.get("complete")); n_pend_claims = sum(1 for _, st, _, _ in self.claims if st != "CONFORME_DESCRIPTIVO")
        reviewed = sum(1 for c in comp.values() for v in c.values() if v["state"] in ("OK", "NO_CUMPLE")); total = sum(1 for c in comp.values() for v in c.values())
        def card(name, label, ts, src, used, finds, blocks, nxt, operational=False):
            return {"name": name, "state": label, "operational": operational, "last_run": ts, "source": src, "data_used": used, "findings": finds, "blockers": blocks, "next_action": nxt, "link": link}
        last = ok_runs[0]["ts"] if ok_runs else None
        return {
            "mercado": card("Mercado y competencia", "SIN EJECUCIÓN" if not ok_runs else "PARCIAL", last, "Keepa API (caché local)", "%d ASIN de este producto en caché · %d candidatos (%d confirmados, %d automáticos)" % (n_recs, n_reg, n_conf, n_auto),
                            ["Keepa cubre DE, FR, IT, ES (y UK, fuera del ranking UE); NL, PL, SE, BE e IE quedan NO EVALUABLES por esta vía."],
                            ([] if kst["can_call"] else ["Keepa desactivado o sin clave (keepa.env)"]) + ([] if n_reg else ["Sin candidatos: ejecutar «Analizar Europa» (descubrimiento automático)"]), "Ejecutar el descubrimiento automático y revisar comparables ALTA/MEDIA."),
            "precios": card("Precios y rentabilidad", "ESCENARIOS HIPOTÉTICOS" if n_complete else "INCOMPLETO", None, "Motor económico determinista", self.cost_text,
                            ["%d de 4 países núcleo con todos los costes obligatorios informados" % n_complete], ["Faltan FBA/FBM, transporte, preparación, almacenamiento y devoluciones documentados"] if n_complete < 4 else ["Costes del producto sin documentar o sin revalidar"], "Introducir costes documentados (calculadora de tarifas de Amazon + presupuesto logístico)."),
            "seo": card("SEO y keywords", "SIN DATOS", None, "—", "Ninguno", ["No se inventan volúmenes de búsqueda."], ["Sin Helium 10 / Brand Analytics autorizados"], "Importar CSV de Helium 10 o Brand Analytics (exportación) cuando se autorice."),
            "ppc": card("Publicidad PPC", "SIN DATOS", None, "Motor económico", "Solo ACoS de equilibrio (calculable con costes completos)", ["Sin CPC ni conversión reales: no se estima presupuesto PPC"], ["Sin datos de Amazon Ads"], "Calcular ACoS de equilibrio con costes completos; definir presupuesto de prueba con aprobación."),
            "creatividad": card("Creatividad, imágenes y vídeos", "PARCIAL", None, "Registro de claims", "%d claims revisados" % len(self.claims), ["%d claims pendientes de evidencia o a reformular/eliminar; 0 utilizables con respaldo" % n_pend_claims, "Revisar imágenes y claims antes de publicar"], ["Sin dossier de evidencia de claims"], "Priorizar evidencia de los claims pendientes antes de A+ Content."),
            "inventario": card("Inventario y logística", "DATO HISTÓRICO SIN CONFIRMAR", None, "Indicado por el usuario", self.stock_text, ["Sin plan FBA/FBM ni costes transfronterizos"], ["Stock actual sin verificar o sin dato", "Costes logísticos sin documentar"], "Confirmar stock físico, lote y coste logístico puesto en Amazon."),
            "cumplimiento": card("Reputación y cumplimiento", "PARCIAL" if reviewed else "SIN REVISAR", None, "Checklist del expediente", "%d de %d requisitos-país revisados" % (reviewed, total), self.reg_findings, ["Sin documentación regulatoria"], "Aportar la documentación regulatoria y marcar cada requisito con su evidencia."),
        }
