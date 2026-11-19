"""K4 · Consejero · F2 — VERIFICADOR de citas y cálculos. Un id de cita válido NO demuestra que la afirmación sea correcta: se comprueba que el extracto respalda el contenido (cifras y términos),
que el dato no sea histórico presentado como actual, que los cálculos se recalculen en código, que una fuente secundaria no se trate como primaria, que las comparaciones sean entre magnitudes equivalentes
y que la conclusión no exceda la calidad de la evidencia. Los controles léxicos son HEURÍSTICOS (detectan errores evidentes; no prueban veracidad): la revisión humana sigue siendo necesaria."""
import ast, datetime, operator, re, unicodedata
from .k4c_ledger import RANGO_CAL

BLOQ, AVISO = "BLOQUEANTE", "AVISO"
STOP = set("para como entre sobre desde hasta cuando donde estos estas esto esta este todos todas cada pero tambien segun puede pueden tiene tienen hacer sido ser son los las del una uno unos unas que con por sin mas muy".split())
SOBREAFIRMA = ("demostrad", "demuestr", "probad", "comprobad", "garantiz", "eficaz", "establecid")
CAUTELA = ("no existen datos", "no hay datos", "sin datos en humanos", "no concluyente", "raton", "ratones", "murino", "mice", "mouse", "in vitro", "preliminar", "preclinic", "podria", "podrian", "sugiere", "sugieren", "might", "may ", "animal", "modelo")
MAX_DIAS = {"PRECIO": 45, "MERCADO": 550, "NORMATIVA": 730, "GENERAL": 1100}
NEGACION_EFECTO = ("no tiene efecto", "no funciona", "ineficaz", "no sirve", "carece de efecto", "no produce efecto")
CAUSAL = ("causa", "provoca", "debido a", "gracias a", "origina", "explica por qué")
CONF_RANGO = {"ALTA": 3, "MEDIA": 2, "BAJA": 1, "MUY_BAJA": 0}


def _plano(t): return unicodedata.normalize("NFKD", str(t).lower()).encode("ascii", "ignore").decode()
def numeros(t):
    out = []
    for m in re.findall(r"\d+(?:[.,]\d+)?", str(t)):
        try: out.append(float(m.replace(",", ".")))
        except ValueError: pass
    return out
def _en(n, lst):
    d = len(str(n).split(".")[1]) if "." in str(n) and not str(n).endswith(".0") else 0
    return any(abs(n - e) < 1e-9 or abs(round(e, d) - n) < 1e-9 for e in lst)
def claves(t): return {w[:6] for w in re.findall(r"[a-z]{5,}", _plano(t)) if w not in STOP}


def soporta(texto_afirmacion, extracto):
    """Devuelve (ok, motivo). Heurística léxica/numérica."""
    nums = numeros(texto_afirmacion); en = numeros(extracto)
    falt = [n for n in nums if not _en(n, en)]
    if falt: return False, "cifras no presentes en el extracto: %s" % ", ".join(("%g" % n) for n in falt)
    kw = claves(texto_afirmacion); ek = claves(extracto)
    cov = (len(kw & ek) / len(kw)) if kw else 1.0
    if cov < 0.4: return False, "el extracto no trata el contenido de la afirmación (cobertura léxica %.0f %%)" % (cov * 100)
    pa, pe = _plano(texto_afirmacion), _plano(extracto)
    if any(s in pa for s in SOBREAFIRMA) and any(c in pe for c in CAUTELA): return False, "la afirmación sobreafirma: el extracto es cauteloso/preclínico (p. ej. animales, in vitro, preliminar)"
    return True, ""


def _calc(expr, vals):
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}
    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool): return n.value
        if isinstance(n, ast.Name) and n.id in vals: return vals[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in ops: return ops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in ops: return ops[type(n.op)](ev(n.operand))
        raise ValueError("expresión no permitida")
    return ev(ast.parse(expr, mode="eval"))


class Verificador:
    def __init__(self, libro): self.L = libro

    def verificar(self, informe, inv_id, hoy=None):
        hoy = datetime.date.fromisoformat(hoy) if hoy else datetime.date.today(); iss = []; self._inf = informe
        def add(sev, cod, af, msg): iss.append({"severidad": sev, "codigo": cod, "afirmacion": af, "detalle": msg})
        afs = {a["id"]: a for a in informe["afirmaciones"]}
        for a in afs.values():
            self._cita(a, add); self._vigencia(a, add, hoy); self._calculo(a, add); self._primaria(a, add); self._comparacion(a, add); self._alcance(a, add)
        self._conclusion(informe, afs, add)
        n_b = sum(1 for i in iss if i["severidad"] == BLOQ); n_a = len(iss) - n_b
        ver = "RECHAZADO" if n_b else ("ACEPTADO_CON_RESERVAS" if n_a else "ACEPTADO")
        malas = sorted({i["afirmacion"] for i in iss if i["severidad"] == BLOQ and i["afirmacion"] in afs})
        return {"veredicto": ver, "bloqueantes": n_b, "avisos": n_a, "problemas": iss, "afirmaciones_rechazadas": malas, "nota": "Verificación heurística: un id de cita válido no demuestra que la afirmación sea correcta; la revisión humana sigue siendo necesaria."}

    # --- controles
    def _cita(self, a, add):
        if a["tipo"] not in ("HECHO",) and not a.get("citas"): return
        citas = a.get("citas") or []
        if a["tipo"] == "HECHO" and not citas and not a.get("dato_interno"): add(BLOQ, "SIN_CITA", a["id"], "un HECHO exige al menos una cita o un dato interno observado"); return
        for c in citas:
            x = self.L.extracto(c)
            if not x or not self.L.fuente(x["fuente_id"]): add(BLOQ, "CITA_INEXISTENTE", a["id"], "la cita %s no existe en el libro de evidencias" % c); continue
            if a["tipo"] in ("HECHO", "INFERENCIA"):
                ok, mot = soporta(a["texto"] if not a.get("texto_verificable") else a["texto_verificable"], x["texto"])
                if not ok and a.get("relacion") != "CONTEXTO": add(BLOQ, "CITA_NO_RESPALDA", a["id"], "%s: %s" % (c, mot))
            f = self.L.fuente(x["fuente_id"])
            if a.get("sujeto") == "FORMULA_FINAL" and (f.get("objeto") or "INGREDIENTE") == "INGREDIENTE": add(BLOQ, "INGREDIENTE_COMO_FORMULA", a["id"], "evidencia sobre un ingrediente se usa para afirmar eficacia/seguridad de la fórmula final")

    def _vigencia(self, a, add, hoy):
        if not a.get("citas"): return
        cat = a.get("categoria_dato") or "GENERAL"
        for c in a["citas"]:
            x = self.L.extracto(c); f = self.L.fuente(x["fuente_id"]) if x else None
            if not f: continue
            if a.get("vigencia_afirmada") == "ACTUAL":
                if f["tipo_dato"] == "HISTORICO": add(BLOQ, "HISTORICO_COMO_ACTUAL", a["id"], "dato HISTÓRICO (%s) presentado como actual" % (f["fecha_publicacion"] or "s/f")); continue
                try: d = datetime.date.fromisoformat((f["fecha_publicacion"] or "")[:10]); edad = (hoy - d).days
                except ValueError: add(AVISO, "FECHA_DESCONOCIDA", a["id"], "no consta la fecha del dato presentado como actual"); continue
                if edad > MAX_DIAS.get(cat, MAX_DIAS["GENERAL"]): add(BLOQ, "HISTORICO_COMO_ACTUAL", a["id"], "dato de hace %d días presentado como actual (máx. %d para %s)" % (edad, MAX_DIAS.get(cat, 1100), cat))
            if f.get("vigente_hasta") and f["vigente_hasta"] < hoy.isoformat() and a.get("vigencia_afirmada") == "ACTUAL": add(BLOQ, "FUENTE_CADUCADA", a["id"], "la fuente caducó el %s" % f["vigente_hasta"])

    def _calculo(self, a, add):
        c = a.get("calculo")
        if not c: return
        vals = {}
        for k, v in (c.get("inputs") or {}).items():
            vals[k] = v["valor"]; o = v.get("origen") or {}
            if "extracto" in o:
                x = self.L.extracto(o["extracto"])
                if not x: add(BLOQ, "CITA_INEXISTENTE", a["id"], "input %s cita un extracto inexistente" % k)
                elif not _en(v["valor"], numeros(x["texto"])): add(BLOQ, "CALCULO_INPUT_NO_RESPALDADO", a["id"], "el valor %s de «%s» no figura en el extracto %s" % (v["valor"], k, o["extracto"]))
            elif o.get("maestro"):
                m = (self._inf.get("maestro") or {}); ref = {"precio": m.get("pvp"), "volumen": m.get("volumen_ml")}.get(k)
                if ref is None or abs(float(ref) - float(v["valor"])) > 0.005: add(BLOQ, "DATO_MAESTRO_INCOHERENTE", a["id"], "el valor %s de «%s» no coincide con la ficha maestra (%s)" % (v["valor"], k, ref))
            elif "interno" not in o and "supuesto" not in o: add(AVISO, "INPUT_SIN_ORIGEN", a["id"], "input %s sin origen declarado" % k)
        try: r = _calc(c["expr"], vals)
        except Exception as e: add(BLOQ, "CALCULO_INVALIDO", a["id"], "no se pudo recalcular: %s" % e); return
        decl = c.get("resultado")
        if decl is None or abs(r - decl) > max(0.01, abs(r) * 0.002): add(BLOQ, "ERROR_DE_CALCULO", a["id"], "declarado %s ≠ recalculado %.4g (%s)" % (decl, r, c["expr"]))

    def _primaria(self, a, add):
        for c in a.get("citas") or []:
            x = self.L.extracto(c); f = self.L.fuente(x["fuente_id"]) if x else None
            if not f: continue
            if a.get("nivel_fuente_afirmado") == "PRIMARIA" and f["tipo_fuente"] != "PRIMARIA": add(BLOQ, "SECUNDARIA_COMO_PRIMARIA", a["id"], "se presenta como fuente primaria/oficial algo que es %s (%s)" % (f["tipo_fuente"], f["url"]))
            if a.get("categoria_dato") == "NORMATIVA" and f["tipo_fuente"] != "PRIMARIA": add(AVISO, "NORMATIVA_SIN_FUENTE_OFICIAL", a["id"], "una afirmación normativa se apoya en una fuente no oficial; contrastar con el texto oficial")

    def _comparacion(self, a, add):
        c = a.get("comparacion")
        if not c: return
        A, B = c["a"], c["b"]
        if A.get("categoria") != B.get("categoria") and c.get("relacion_declarada") != "SUSTITUTO_INDIRECTO": add(BLOQ, "COMPARACION_NO_EQUIVALENTE", a["id"], "se comparan %s y %s como equivalentes; declarar la relación (p. ej. SUSTITUTO_INDIRECTO) y su alcance" % (A.get("categoria"), B.get("categoria")))
        if A.get("unidad_base") != B.get("unidad_base") and not c.get("conversion"): add(BLOQ, "COMPARACION_NO_EQUIVALENTE", a["id"], "bases distintas (%s vs %s) sin conversión declarada" % (A.get("unidad_base"), B.get("unidad_base")))
        if (A.get("moneda") != B.get("moneda") or A.get("pais") != B.get("pais")) and not c.get("conversion"): add(AVISO, "COMPARACION_MONEDA_PAIS", a["id"], "moneda o país distintos sin conversión")

    def _alcance(self, a, add):
        t = _plano(a["texto"])
        if a.get("relacion") == "AUSENCIA" or a.get("tipo_hallazgo") == "AUSENCIA_LOCALIZADA":
            if any(n in t for n in NEGACION_EFECTO): add(BLOQ, "AUSENCIA_COMO_EVIDENCIA_DE_AUSENCIA", a["id"], "no localizar evidencia no demuestra la ausencia de efecto; reformular como «no se localizó evidencia» con el alcance de la búsqueda")
        if "bsr" in t and re.search(r"\bventas?\b", t) and any(w in t for w in ("unidades", "al mes", "mensual", "diari", "implica", "equivale")) and not a.get("estimacion_declarada"): add(BLOQ, "BSR_COMO_VENTAS", a["id"], "no se pueden inferir ventas reales del BSR")
        if a.get("relacion") == "CORRELACION" and any(w in t for w in CAUSAL): add(BLOQ, "CORRELACION_COMO_CAUSA", a["id"], "se atribuye causalidad a una correlación")

    def _conclusion(self, informe, afs, add):
        c = informe.get("conclusion") or {}
        if not c: return
        base = [afs[i] for i in c.get("base", []) if i in afs]
        for i in c.get("base", []):
            if i not in afs: add(BLOQ, "CONCLUSION_BASE_INEXISTENTE", i, "la conclusión se apoya en una afirmación que no existe")
        cal = []
        for a in base:
            if a["tipo"] == "FALTANTE": continue   # ignorancia declarada: no es una base que sostenga la conclusión
            if a["tipo"] in ("HIPOTESIS", "INFERENCIA"): cal.append(0 if a["tipo"] != "INFERENCIA" else 1); continue
            q = [RANGO_CAL.get((self.L.fuente(self.L.extracto(cc)["fuente_id"]) or {}).get("calidad"), 0) for cc in a.get("citas") or [] if self.L.extracto(cc)]
            cal.append(max(q) if q else (3 if a.get("dato_interno") else 0))
        conf = CONF_RANGO.get(c.get("confianza"), 0)
        if c.get("decision") in ("NO_CONCLUIBLE", "BLOQUEADO"):
            if conf > 1: add(BLOQ, "CONCLUSION_EXCEDE_EVIDENCIA", "conclusion", "una conclusión NO_CONCLUIBLE no puede declarar confianza superior a BAJA")
            return
        if cal and conf > min(cal): add(BLOQ, "CONCLUSION_EXCEDE_EVIDENCIA", "conclusion", "confianza %s pero el eslabón más débil de la base es de calidad %d/3" % (c.get("confianza"), min(cal)))
        if c.get("decision") in ("SUBIR", "BAJAR", "MANTENER", "DISENAR_EXPERIMENTO") and not any(a.get("dato_interno") for a in base): add(BLOQ, "CONCLUSION_EXCEDE_EVIDENCIA", "conclusion", "una decisión de precio exige datos internos observados (ventas/margen) entre sus bases")
        if c.get("decision") in ("SUBIR", "BAJAR", "MANTENER") and not any(a.get("respuesta_precio") for a in base): add(BLOQ, "RECOMENDACION_SOLO_POR_RANGO", "conclusion", "SUBIR/BAJAR/MANTENER exige evidencia de la respuesta de la demanda al precio; la posición frente al rango de competidores no basta")
        cats = set((informe.get("ficha") or {}).get("categorias_comparables") or [])
        for a in base:
            if a.get("categoria_comparable") and cats and a["categoria_comparable"] not in cats: add(BLOQ, "COMPARACION_NO_EQUIVALENTE", a["id"], "la conclusión se apoya en un comparable de categoría no equivalente (%s)" % a["categoria_comparable"])
        if base and all(a["tipo"] in ("HIPOTESIS", "INFERENCIA") for a in base) and conf > 1: add(BLOQ, "CONCLUSION_EXCEDE_EVIDENCIA", "conclusion", "conclusión basada solo en hipótesis/inferencias con confianza superior a BAJA")
        if not base and c.get("decision") not in (None, "NO_CONCLUIBLE"): add(BLOQ, "CONCLUSION_SIN_BASE", "conclusion", "decisión sin afirmaciones de base")
