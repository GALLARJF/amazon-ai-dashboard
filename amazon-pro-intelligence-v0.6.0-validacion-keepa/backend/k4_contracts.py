"""K4 · contratos comunes de datos y evidencia. Una cifra SIEMPRE lleva valor, unidad, moneda, denominador, periodo, fuente, fecha, metodología, confianza, estado y entorno.
Ausencia de dato = SIN_DATO (valor None), NUNCA 0. Los datos sintéticos llevan entorno SINTETICO_DEMO y no se mezclan con producción."""
import datetime, re

ESTADOS = ("OBSERVADO", "DERIVADO", "ESTIMADO", "HIPOTESIS", "SIN_DATO")
CONFIANZAS = ("ALTA", "MEDIA", "BAJA", "MUY_BAJA")
ENTORNOS = ("PRODUCCION", "SINTETICO_DEMO")
ORIGENES = ("KEEPA", "SPAPI", "ADS", "EXPORT_SELLER_CENTRAL", "EXPORT_ADS", "MANUAL_AHT", "CATALOGO_OFICIAL", "MAQUETA", "IA_HIPOTESIS", "SINTETICO", "K3")
CLASES_AFIRMACION = ("HECHO", "CAUSA_POSIBLE", "HIPOTESIS", "ACCION_PROPUESTA", "ACCION_EJECUTADA", "RESULTADO_COMPROBADO")
TIPOS_DICTAMEN = {1: "SUBIR PRECIO", 2: "MANTENER PRECIO", 3: "BAJAR PRECIO O ENSAYAR UNA PROMOCIÓN", 4: "NO MODIFICAR PRECIO Y CORREGIR OTRA CAUSA", 5: "EVIDENCIA INSUFICIENTE"}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")


def iso_date(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def medida(valor, unidad, fuente=None, fecha_dato=None, *, moneda=None, denominador=None, periodo=None, metodologia=None, confianza="BAJA", estado=None, entorno="PRODUCCION", fuente_ref=None):
    """Construye una Medida. Sin valor ⇒ SIN_DATO. Con valor exige fuente y fecha; si no, lanza ValueError (no se admiten cifras huérfanas)."""
    if valor is None:
        return {"valor": None, "unidad": unidad, "moneda": moneda, "denominador": denominador, "periodo": periodo, "fuente": fuente, "fuente_ref": fuente_ref, "fecha_dato": fecha_dato,
                "metodologia": metodologia, "confianza": "MUY_BAJA", "estado": "SIN_DATO", "entorno": entorno}
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError("el valor de una medida debe ser numérico")
    if not fuente or not iso_date(fecha_dato):
        raise ValueError("toda cifra exige fuente y fecha")
    if confianza not in CONFIANZAS or entorno not in ENTORNOS:
        raise ValueError("confianza o entorno inválidos")
    est = estado or "OBSERVADO"
    if est not in ESTADOS or est == "SIN_DATO":
        raise ValueError("estado inválido")
    return {"valor": valor, "unidad": unidad, "moneda": moneda, "denominador": denominador, "periodo": periodo, "fuente": fuente, "fuente_ref": fuente_ref, "fecha_dato": str(fecha_dato)[:10],
            "metodologia": metodologia, "confianza": confianza, "estado": est, "entorno": entorno}


def validar_medida(m):
    e = []
    if not isinstance(m, dict): return ["no es un objeto"]
    for k in ("valor", "unidad", "fuente", "fecha_dato", "confianza", "estado", "entorno"):
        if k not in m: e.append("falta " + k)
    if e: return e
    if m["estado"] == "SIN_DATO":
        if m["valor"] is not None: e.append("SIN_DATO con valor")
        return e
    if m["valor"] is None or isinstance(m["valor"], bool) or not isinstance(m["valor"], (int, float)): e.append("valor no numérico")
    if not m["fuente"]: e.append("sin fuente")
    if not iso_date(m["fecha_dato"]): e.append("fecha inválida")
    if m["confianza"] not in CONFIANZAS: e.append("confianza inválida")
    if m["estado"] not in ESTADOS: e.append("estado inválido")
    if m["entorno"] not in ENTORNOS: e.append("entorno inválido")
    if m["unidad"] in ("EUR", "€") and not m.get("moneda"): e.append("importe sin moneda")
    return e


def afirmacion(clase, texto, evidencia=None):
    if clase not in CLASES_AFIRMACION: raise ValueError("clase de afirmación inválida")
    return {"clase": clase, "texto": str(texto)[:600], "evidencia": evidencia or []}


def validar_dictamen(d):
    """Un dictamen es válido si es trazable: tipo 1-5, fuentes, confianza, riesgos, próxima acción, criterio de revisión y afirmaciones clasificadas."""
    e = []
    if d.get("tipo") not in TIPOS_DICTAMEN: e.append("tipo inválido")
    for k in ("precio_actual", "justificacion", "fuentes", "confianza", "margen_estimado", "escenarios", "riesgos", "proxima_accion", "criterio_revision", "trazabilidad", "entorno"):
        if k not in d: e.append("falta " + k)
    if d.get("confianza") not in CONFIANZAS: e.append("confianza inválida")
    for a in d.get("justificacion", []):
        if a.get("clase") not in CLASES_AFIRMACION: e.append("afirmación sin clase")
    if d.get("tipo") in (1, 2, 3) and d.get("confianza") == "MUY_BAJA": e.append("dictamen 1-3 con confianza MUY_BAJA no permitido")
    if d.get("tipo") in (1, 3) and not d.get("intervalo_recomendado"): e.append("subir/bajar exige intervalo")
    if d.get("intervalo_recomendado") and d.get("base_solo_mediana"): e.append("el intervalo no puede basarse solo en una mediana")
    return e
