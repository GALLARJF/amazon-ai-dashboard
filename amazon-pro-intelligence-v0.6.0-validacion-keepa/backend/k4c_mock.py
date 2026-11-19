"""K4 · Consejero · F1/F2 — PROVEEDORES SIMULADOS y corpus SINTÉTICO. Todo lo de este módulo es DATOS DE PRUEBA («SINTÉTICO»): no son hechos del mundo.
Superar pruebas con estos proveedores valida el MOTOR (trazabilidad, verificador, reglas, sensibilidad a la evidencia), NO demuestra razonamiento autónomo real de un modelo."""
import re, unicodedata
from .k4c_providers import ProveedorBusqueda, ProveedorLectura, ProveedorLLM, Herramienta

ESCENARIOS = ("BASE", "NUEVA_EVIDENCIA_COMPARABLES", "REVISION_DEGRADADA", "SIN_DATOS", "COMPARABLES_NO_EQUIVALENTES")
def _d(url, titulo, texto, tf, cal, td, fecha, org, obj, tags, temas, categoria=None):
    return {"categoria": categoria, "url": "sintetico://" + url, "titulo": "[SINTÉTICO] " + titulo, "texto": "[SINTÉTICO] " + texto, "tipo_fuente": tf, "calidad": cal, "tipo_dato": td, "fecha_publicacion": fecha, "organismo": org, "objeto": obj, "tags": tags, "temas": temas}

def corpus(escenario="BASE"):
    if escenario not in ESCENARIOS: raise ValueError("escenario desconocido")
    cafe_txt = "Revisión sistemática ficticia de 6 ensayos con 412 participantes: la cafeína tópica mejora el recuento de cabello en alopecia androgenética con certeza GRADE moderada."
    cafe_tag = ("H0", 1, "la cafeína tópica mejora el recuento de cabello en alopecia androgenética con certeza GRADE moderada")
    if escenario == "REVISION_DEGRADADA":
        cafe_txt = "Corrección ficticia de la revisión sistemática de 6 ensayos con 412 participantes: tras excluir dos ensayos con sesgo, la certeza GRADE de la cafeína tópica es muy baja y el efecto no es concluyente."
        cafe_tag = ("H0", -1, "la certeza GRADE de la cafeína tópica es muy baja y el efecto no es concluyente")
    if escenario == "SIN_DATOS": return []
    docs = [
        _d("cafeina-revision", "Revisión sistemática de cafeína tópica", cafe_txt, "PRIMARIA", "ALTA" if escenario != "REVISION_DEGRADADA" else "ALTA", "ATEMPORAL", "2024-05-01", "Revista ficticia", "INGREDIENTE", [cafe_tag], "cafeina topica alopecia ensayo revision evidencia ingrediente"),
        _d("luteolina-raton", "Luteolina tópica en modelo murino", "Estudio ficticio en ratones: la luteolina tópica aumentó el crecimiento del pelo; no existen datos en humanos.", "PRIMARIA", "MEDIA", "ATEMPORAL", "2023-02-10", "Revista ficticia", "INGREDIENTE", [("H0", 0, "la luteolina tópica aumentó el crecimiento del pelo; no existen datos en humanos")], "luteolina topica raton murino evidencia ingrediente"),
        _d("comp-alfa", "Ficha Alfa serum capilar", "Competidor Alfa, serum capilar premium de 90 ml, precio observado 39,94 EUR el 2026-11-16.", "PRIMARIA", "ALTA", "ACTUAL", "2026-11-16", "Marketplace sintético", "PRODUCTO", [("H2", 1, "serum capilar premium de 90 ml, precio observado 39,94 EUR")], "competidor precio serum capilar premium alfa mercado", "COSMETICO_CAPILAR_PREMIUM"),
        _d("comp-beta", "Ficha Beta tratamiento capilar", "Competidor Beta, tratamiento capilar de 100 ml, precio 55,00 EUR en marzo de 2025.", "PRIMARIA", "ALTA", "HISTORICO", "2025-03-02", "Marketplace sintético", "PRODUCTO", [("H2", 0, "tratamiento capilar de 100 ml, precio 55,00 EUR en marzo de 2025")], "competidor precio tratamiento capilar beta mercado", "COSMETICO_CAPILAR_PREMIUM"),
        _d("minoxidil", "Precio máximo minoxidil", "Minoxidil 5 % solución de 60 ml, precio máximo oficial 12,49 EUR, medicamento de uso tópico para alopecia.", "PRIMARIA", "ALTA", "ACTUAL", "2026-10-20", "Organismo sintético", "MEDICAMENTO", [("H3", 1, "Minoxidil 5 % solución de 60 ml, precio máximo oficial 12,49 EUR")], "minoxidil precio medicamento alopecia sustituto", "MEDICAMENTO"),
        _d("norma-oficial", "Criterio oficial de clasificación", "La clasificación como cosmético o medicamento se decide caso por caso valorando la presentación completa, la composición y las alegaciones del producto.", "PRIMARIA", "ALTA", "ATEMPORAL", "2023-06-01", "Autoridad sintética", "NORMA", [("H4", 1, "se decide caso por caso valorando la presentación completa, la composición y las alegaciones")], "clasificacion cosmetico medicamento alegaciones regulatoria normativa"),
        _d("blog-norma", "Blog: alegaciones capilares", "Un blog sintético afirma que las alegaciones de crecimiento capilar suelen considerarse medicinales.", "SECUNDARIA", "BAJA", "ATEMPORAL", "2024-09-01", "Blog sintético", "NORMA", [("H4", 0, "alegaciones de crecimiento capilar suelen considerarse medicinales")], "alegaciones crecimiento capilar medicinales normativa blog"),
        _d("bsr-nota", "Nota sobre el BSR", "El BSR refleja una posición relativa en la categoría y no equivale a unidades vendidas.", "SECUNDARIA", "MEDIA", "ATEMPORAL", "2024-01-15", "Consultora sintética", "METODO", [("H5", 0, "no equivale a unidades vendidas")], "bsr ranking ventas demanda unidades metodo"),
    ]
    if escenario == "NUEVA_EVIDENCIA_COMPARABLES":
        docs += [_d("comp-gamma", "Ficha Gamma serum", "Competidor Gamma, serum capilar premium de 30 ml, precio observado 35,00 EUR el 2026-11-12.", "PRIMARIA", "ALTA", "ACTUAL", "2026-11-12", "Marketplace sintético", "PRODUCTO", [("H2", 1, "serum capilar premium de 30 ml, precio observado 35,00 EUR")], "competidor precio serum capilar premium gamma mercado", "COSMETICO_CAPILAR_PREMIUM"),
                 _d("comp-delta", "Ficha Delta ampolla", "Competidor Delta, ampollas capilares premium de 50 ml, precio observado 52,00 EUR el 2026-11-12.", "PRIMARIA", "ALTA", "ACTUAL", "2026-11-12", "Marketplace sintético", "PRODUCTO", [("H2", 1, "ampollas capilares premium de 50 ml, precio observado 52,00 EUR")], "competidor precio ampollas capilar premium delta mercado", "COSMETICO_CAPILAR_PREMIUM")]
    if escenario == "COMPARABLES_NO_EQUIVALENTES":
        docs += [_d("comp-epsilon", "Ficha Epsilon champú", "Competidor Epsilon, champú anticaída masivo de 400 ml, precio observado 5,99 EUR el 2026-11-12.", "PRIMARIA", "ALTA", "ACTUAL", "2026-11-12", "Marketplace sintético", "PRODUCTO", [("H2", 1, "champú anticaída masivo de 400 ml, precio observado 5,99 EUR")], "competidor precio tratamiento champu capilar masivo mercado", "COSMETICO_CAPILAR_MASIVO"),
                 _d("comp-zeta", "Ficha Zeta spray", "Competidor Zeta, spray capilar masivo de 250 ml, precio observado 7,50 EUR el 2026-11-12.", "PRIMARIA", "ALTA", "ACTUAL", "2026-11-12", "Marketplace sintético", "PRODUCTO", [("H2", 1, "spray capilar masivo de 250 ml, precio observado 7,50 EUR")], "competidor precio tratamiento spray capilar masivo mercado", "COSMETICO_CAPILAR_MASIVO")]
    return docs


def _plano(t): return unicodedata.normalize("NFKD", str(t).lower()).encode("ascii", "ignore").decode()


class BusquedaSimulada(ProveedorBusqueda):
    nombre = "busqueda_sintetica"; modo = "SIMULADO"
    def __init__(self, escenario="BASE"): self.docs = corpus(escenario)
    def estado(self): return {"estado": "OPERATIVA", "motivo": "corpus SINTÉTICO en memoria"}
    def buscar(self, consulta, max_resultados=5):
        q = set(re.findall(r"[a-z]{4,}", _plano(consulta))); res = []
        for d in self.docs:
            t = set(re.findall(r"[a-z]{4,}", _plano(d["temas"] + " " + d["titulo"]))); s = len(q & t)
            if s >= 2: res.append((s, d))
        res.sort(key=lambda x: (-x[0], x[1]["url"]))
        return [{"url": d["url"], "titulo": d["titulo"], "snippet": d["texto"][:140], "fecha": d["fecha_publicacion"]} for _, d in res[:max_resultados]]


class LecturaSimulada(ProveedorLectura):
    nombre = "lectura_sintetica"; modo = "SIMULADO"
    def __init__(self, escenario="BASE"): self.por_url = {d["url"]: d for d in corpus(escenario)}
    def estado(self): return {"estado": "OPERATIVA", "motivo": "corpus SINTÉTICO en memoria"}
    def leer(self, url):
        if not url.startswith("sintetico://"): raise PermissionError("la lectura simulada solo abre sintetico://")
        if url not in self.por_url: raise LookupError("documento inexistente")
        return dict(self.por_url[url])


class CalculadoraExperimento(Herramienta):
    """Diseño de experimento A/B por tráfico, línea base, efecto mínimo detectable, variabilidad y margen. No recomienda duraciones fijas."""
    nombre = "diseno_experimento"; modo = "LOCAL"
    def estado(self): return {"estado": "OPERATIVA", "motivo": "cálculo local sin red"}
    def ejecutar(self, trafico_diario=None, conv_base=None, mde_rel=0.15, alpha=0.05, potencia=0.8, margen_unitario=None, coste_visitante_eur=None, **_):
        faltan = [k for k, v in (("trafico_diario", trafico_diario), ("conv_base", conv_base)) if not v]
        if faltan: return {"disenable": False, "motivo": "faltan datos internos para dimensionar: " + ", ".join(faltan), "datos_necesarios": ["tráfico diario por variante", "conversión base", "variabilidad semanal", "margen unitario", "condiciones comerciales (promociones, stock, estacionalidad)"]}
        from statistics import NormalDist
        z = NormalDist().inv_cdf; za, zb = z(1 - alpha / 2), z(potencia); p1 = conv_base; p2 = conv_base * (1 + mde_rel); pm = (p1 + p2) / 2
        n = ((za * (2 * pm * (1 - pm)) ** .5 + zb * (p1 * (1 - p1) + p2 * (1 - p2)) ** .5) ** 2) / (p2 - p1) ** 2
        n = int(n) + 1; dias = -(-n * 2 // trafico_diario); dias_c = max(dias, 14)
        return {"disenable": True, "n_por_variante": n, "dias_estimados": dias_c, "nota": "al menos 2 semanas completas para cubrir ciclo semanal; potencia %.0f %%, alfa %.2f, efecto mínimo detectable %.0f %% relativo" % (potencia * 100, alpha, mde_rel * 100), "supuestos": ["tráfico dividido a partes iguales", "sin promociones simultáneas", "conversión estable"], "advertencia": "con poco tráfico el experimento puede ser inviable: valorar otra vía (precio de lista con monitorización, panel, experiencia en otro canal)" if dias_c > 90 else None}


class LLMSimulado(ProveedorLLM):
    """Redactor SIMULADO: aplica una mutación determinista controlada por `trampa` para probar el verificador. NO razona; no sustituye a un modelo real."""
    nombre = "llm_simulado"; modo = "SIMULADO"
    TRAMPAS = (None, "CITA_INEXISTENTE", "CITA_NO_RESPALDA", "HISTORICO_COMO_ACTUAL", "ERROR_DE_CALCULO", "SECUNDARIA_COMO_PRIMARIA", "COMPARACION_NO_EQUIVALENTE", "CONCLUSION_EXCEDE_EVIDENCIA", "AUSENCIA_COMO_AUSENCIA", "BSR_COMO_VENTAS", "CORRELACION_COMO_CAUSA", "INGREDIENTE_COMO_FORMULA", "PRECIO_SOLO_POR_RANGO", "COMPARABLE_NO_EQUIVALENTE_EN_BASE", "VOLUMEN_ERRONEO")
    def __init__(self, trampa=None):
        if trampa not in self.TRAMPAS: raise ValueError("trampa desconocida")
        self.trampa = trampa
    def estado(self): return {"estado": "OPERATIVA", "motivo": "redactor simulado determinista (no es un modelo)"}
    def completar(self, sistema, usuario, esquema=None):
        informe = (esquema or {}).get("informe"); t = self.trampa
        if not informe or not t: return {"json": informe, "texto": "sin mutación", "tokens_in": 0, "tokens_out": 0, "coste_eur": 0.0, "modo": "SIMULADO"}
        import copy; inf = copy.deepcopy(informe); afs = inf["afirmaciones"]
        def nuevo(tipo, texto, **kw): d = dict(id="AF-T", tipo=tipo, texto=texto, citas=[], relacion="FAVORABLE"); d.update(kw); afs.append(d); return afs[-1]
        hechos = [a for a in afs if a["tipo"] == "HECHO" and a.get("citas")]
        if t == "CITA_INEXISTENTE": hechos[0]["citas"] = ["X-inventada01"]
        elif t == "CITA_NO_RESPALDA": hechos[0]["texto"] = "El producto reduce un 40 % la caída del cabello en humanos."
        elif t == "HISTORICO_COMO_ACTUAL":
            h = next(a for a in hechos if a.get("categoria_dato") == "PRECIO" and a.get("fecha_dato", "") < "2026"); h["vigencia_afirmada"] = "ACTUAL"
        elif t == "ERROR_DE_CALCULO":
            c = next(a for a in afs if a.get("calculo")); c["calculo"]["resultado"] = c["calculo"]["resultado"] * 1.5
        elif t == "SECUNDARIA_COMO_PRIMARIA":
            h = next(a for a in hechos if a.get("categoria_dato") == "NORMATIVA" and a.get("nivel_fuente") == "SECUNDARIA"); h["nivel_fuente_afirmado"] = "PRIMARIA"
        elif t == "COMPARACION_NO_EQUIVALENTE":
            nuevo("INFERENCIA", "El minoxidil es un competidor equivalente directo del producto premium.", comparacion={"a": {"categoria": "COSMETICO_PREMIUM", "unidad_base": "100ML"}, "b": {"categoria": "MEDICAMENTO", "unidad_base": "100ML"}})
        elif t == "CONCLUSION_EXCEDE_EVIDENCIA": inf["conclusion"] = dict(inf["conclusion"], confianza="ALTA", decision="SUBIR", base=[a["id"] for a in afs if a["tipo"] in ("HIPOTESIS", "INFERENCIA")][:2] or inf["conclusion"]["base"])
        elif t == "AUSENCIA_COMO_AUSENCIA": nuevo("HECHO", "La luteolina no tiene efecto sobre el cabello humano.", relacion="AUSENCIA")
        elif t == "BSR_COMO_VENTAS": nuevo("INFERENCIA", "El BSR de la competencia implica ventas mensuales de unidades elevadas.")
        elif t == "CORRELACION_COMO_CAUSA": nuevo("INFERENCIA", "La subida del BSR se debe a la bajada de precio, causa del aumento de ventas.").update(relacion="CORRELACION")
        elif t == "INGREDIENTE_COMO_FORMULA": nuevo("HECHO", "La fórmula final de ACTIVCORE es eficaz y segura.", sujeto="FORMULA_FINAL").update(citas=[next(a["citas"][0] for a in hechos if a["citas"] and a.get("categoria_dato") == "INGREDIENTE")])
        elif t == "PRECIO_SOLO_POR_RANGO": inf["conclusion"] = dict(inf["conclusion"], decision="BAJAR", confianza="MEDIA", motivo="El precio está por encima del rango de competidores.", base=[a["id"] for a in afs if (a.get("dato_interno") and not a.get("respuesta_precio")) or (a.get("calculo") and a.get("vigencia_afirmada") == "ACTUAL" and a.get("categoria_comparable") == "COSMETICO_CAPILAR_PREMIUM")])
        elif t == "COMPARABLE_NO_EQUIVALENTE_EN_BASE":
            c0 = next(a for a in afs if a.get("calculo") and a.get("categoria_comparable")); c0["categoria_comparable"] = "COSMETICO_CAPILAR_MASIVO"; inf["conclusion"]["base"] = list(inf["conclusion"]["base"]) + [c0["id"]]
        elif t == "VOLUMEN_ERRONEO":
            p0 = next(a for a in afs if a.get("dato_interno") and a.get("calculo")); p0["calculo"]["inputs"]["volumen"]["valor"] = 50.0; p0["calculo"]["resultado"] = round(p0["calculo"]["inputs"]["precio"]["valor"] / 50.0 * 100, 2)
        return {"json": inf, "texto": "informe mutado (trampa=%s)" % t, "tokens_in": 0, "tokens_out": 0, "coste_eur": 0.0, "modo": "SIMULADO"}
