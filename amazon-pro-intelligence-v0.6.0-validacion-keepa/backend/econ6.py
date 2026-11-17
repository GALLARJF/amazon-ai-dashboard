"""V0.6 (F7) — Motor económico verificable con TRAZABILIDAD. Capa sobre eu.unit_economics (determinista, sin IA).
Clases de dato: OBSERVADO · IMPORTADO · DERIVADO · ESTIMADO · HIPOTESIS · SINTETICO (de más a menos fiable). El resultado hereda la clase del eslabón más débil.
Nunca rellena con valores por defecto: lo que falta es NO CALCULABLE y se dice qué falta."""
import math
from . import eu as E

CLASS_ORDER = ["OBSERVADO", "IMPORTADO", "DERIVADO", "ESTIMADO", "HIPOTESIS", "SINTETICO"]
STATUS_TO_CLASS = {"VERIFICADO": "OBSERVADO", "DOCUMENTADO": "IMPORTADO", "HISTORICO_A_REVALIDAR": "ESTIMADO", "A_CONFIRMAR": "ESTIMADO", "PROPUESTO": "HIPOTESIS", "HIPOTESIS": "HIPOTESIS", "SINTETICO": "SINTETICO"}
CLASS_HELP = {"OBSERVADO": "dato verificado en fuente oficial/real", "IMPORTADO": "dato documentado aportado con fuente y fecha", "DERIVADO": "calculado a partir de datos anteriores",
              "ESTIMADO": "dato sin revalidar o pendiente de confirmar", "HIPOTESIS": "supuesto editable, no verificado", "SINTETICO": "dato de demostración (no real)"}
LABEL = E.LABEL


def weakest(classes):
    cs = [c for c in classes if c in CLASS_ORDER]
    return max(cs, key=CLASS_ORDER.index) if cs else None


def input_class(f):
    return STATUS_TO_CLASS.get(f.get("status"))


def unit(svc, country, pvp, mode="FBA", acos_target=None, ads_share_of_sales=None):
    """Economía por unidad para un país y PVP. acos_target y ads_share_of_sales son HIPÓTESIS del usuario (fracciones 0–1)."""
    country = str(country).upper()
    if country not in E.VAT:
        raise ValueError("país desconocido")
    if mode not in ("FBA", "FBM"):
        raise ValueError("modo logístico FBA|FBM")
    if country in E.CURRENCY:
        return {"country": country, "complete": False, "label": "NO EVALUABLE: moneda local (%s) — hace falta tipo de cambio y precios locales documentados" % E.CURRENCY[country], "missing": ["tipo de cambio"]}
    if not isinstance(pvp, (int, float)) or isinstance(pvp, bool) or not 0.5 <= pvp <= 5000:
        raise ValueError("PVP con IVA inválido")
    for nm, v in (("acos_target", acos_target), ("ads_share_of_sales", ads_share_of_sales)):
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1):
            raise ValueError(nm + ": fracción 0–1")
    a = svc.assumptions()[country]
    r = E.unit_economics(pvp, a, acos_target)
    used = r.get("inputs", {})
    trace = {k: {"clase": input_class(a[k]), "estado": a[k]["status"], "fuente": a[k]["source"], "fecha": a[k]["date"], "valor": a[k]["v"] if k != "referral" else "tabla por tramos"} for k in E.FIELDS if k in a}
    classes = [t["clase"] for k, t in trace.items() if k in E.REQUIRED and t["clase"]]
    out = {"country": country, "mode": mode, "pvp_gross": pvp, "result": r, "trace": trace, "complete": bool(r.get("complete"))}
    if not r.get("complete"):
        out["state"] = "NO CALCULABLE"; out["missing"] = [LABEL[k] for k in r.get("missing", [])]
        out["why"] = r.get("label"); out["class"] = None
        return out
    out["class"] = weakest(classes + ["DERIVADO"])
    out["class_help"] = CLASS_HELP[out["class"]]
    out["state"] = "CALCULADO · " + out["class"]
    be = r["breakeven_acos_ex_vat"]
    out["breakeven_acos"] = {"sin_iva": be, "con_iva": r["breakeven_acos_inc_vat"], "clase": "DERIVADO"}
    if acos_target is not None and ads_share_of_sales is not None:
        out["tacos"] = {"valor": round(acos_target * ads_share_of_sales, 4), "clase": "HIPOTESIS", "formula": "TACoS = ACoS objetivo × (ventas por publicidad ÷ ventas totales); ambos son hipótesis"}
    else:
        out["tacos"] = {"valor": None, "estado": "NO DETERMINABLE", "why": "TACoS exige ACoS y la proporción de ventas atribuidas a publicidad (aún sin datos reales)"}
    out["logistica"] = mode
    if mode == "FBM":
        out["warning"] = "Modo FBM: el motor usa el campo «fulfillment» como coste de envío+embalaje FBM; confirmar importes."
    return out


def table(svc, pvp=None, mode="FBA", acos_target=None, ads_share=None, countries=None):
    rows = []
    for c in countries or E.COUNTRIES:
        p = pvp if pvp is not None else (svc.pvp_default or None)
        if p is None:
            rows.append({"country": c, "state": "NO CALCULABLE", "why": "el producto no tiene PVP de referencia", "complete": False}); continue
        rows.append(unit(svc, c, p, mode, acos_target, ads_share))
    return rows


def inventory(units_per_month, lead_time_days, safety_days, stock=None, moq=None):
    """Necesidades de inventario a partir de HIPÓTESIS de ventas. Sin velocidad de ventas → NO DETERMINABLE (no se inventa demanda)."""
    if units_per_month is None or lead_time_days is None:
        return {"state": "NO DETERMINABLE", "why": "faltan ventas esperadas (uds/mes) y plazo de reposición; no se inventa demanda", "class": None}
    for nm, v in (("units_per_month", units_per_month), ("lead_time_days", lead_time_days), ("safety_days", safety_days or 0)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 or v > 1e6:
            raise ValueError(nm + " inválido")
    daily = units_per_month / 30.0; rop = math.ceil(daily * (lead_time_days + (safety_days or 0)))
    out = {"state": "CALCULADO · HIPOTESIS", "class": "HIPOTESIS", "daily_units": round(daily, 3), "reorder_point_units": rop, "cover_days": None, "order_units": None,
           "formula": "punto de pedido = ventas/día × (plazo + días de seguridad)"}
    if stock is not None:
        out["cover_days"] = round(stock / daily, 1) if daily > 0 else None
        out["order_units"] = max(0, math.ceil(daily * (lead_time_days + (safety_days or 0) + 30)) - int(stock))
        out["order_note"] = "pedido sugerido = cobertura de plazo+seguridad+30 días − stock actual (stock debe estar verificado)"
    if moq:
        out["order_units"] = max(out["order_units"] or 0, int(moq))
    return out
