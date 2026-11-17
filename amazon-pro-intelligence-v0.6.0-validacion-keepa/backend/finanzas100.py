"""V1.0 (V1-05) — Escenarios, sensibilidad y punto de equilibrio sobre econ6.unit (determinista, sin IA, sin red).
Todo número hereda la clase del eslabón más débil; lo que falta es NO CALCULABLE. Los costes fijos y volúmenes son HIPÓTESIS del usuario, nunca valores por defecto."""
import math
from . import econ6 as X

def _num(v, nm, lo=0.0, hi=1e9):
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi: raise ValueError(nm + " inválido")
    return float(v)

def sensibilidad(svc, country, pvps, acos_list, mode="FBA"):
    """Rejilla PVP × ACoS → margen de contribución tras publicidad por unidad. ACoS e importes son hipótesis del usuario."""
    if not pvps or not acos_list or len(pvps) > 25 or len(acos_list) > 25: raise ValueError("rejilla vacía o demasiado grande (máx. 25×25)")
    celdas = []; clase = None; faltan = None
    for p in pvps:
        fila = []
        for a in acos_list:
            r = X.unit(svc, country, _num(p, "pvp", 0.5, 5000), mode, _num(a, "acos", 0, 1))
            if not r.get("complete"):
                faltan = r.get("missing") or r.get("why"); fila.append({"pvp": p, "acos": a, "estado": "NO CALCULABLE"}); continue
            res = r["result"]; clase = X.weakest([clase, r["class"]]) if clase else r["class"]
            fila.append({"pvp": p, "acos": a, "contribucion_tras_ads": res["contribution_after_ads"], "margen_tras_ads": res["margin_after_ads"], "rentable": res["contribution_after_ads"] > 0})
        celdas.append(fila)
    if faltan and clase is None: return {"estado": "NO CALCULABLE", "faltan": faltan, "celdas": celdas, "clase": None}
    return {"estado": "CALCULADO · " + str(clase), "clase": clase, "celdas": celdas, "hipotesis": "ACoS y PVP de la rejilla son supuestos, no datos reales", "faltan": faltan}

def escenarios(svc, country, pvp, acos_base, mode="FBA", delta_pvp=0.10, delta_acos=0.05):
    """Tres escenarios deterministas: PESIMISTA (PVP−Δ, ACoS+Δ), BASE y OPTIMISTA (PVP+Δ, ACoS−Δ)."""
    pvp = _num(pvp, "pvp", 0.5, 5000); acos_base = _num(acos_base, "acos", 0, 1)
    defs = {"PESIMISTA": (pvp * (1 - delta_pvp), min(1.0, acos_base + delta_acos)), "BASE": (pvp, acos_base), "OPTIMISTA": (pvp * (1 + delta_pvp), max(0.0, acos_base - delta_acos))}
    out = {}
    for n, (p, a) in defs.items():
        r = X.unit(svc, country, round(p, 2), mode, round(a, 4))
        out[n] = {"pvp": round(p, 2), "acos": round(a, 4), "estado": r.get("state"), "clase": r.get("class")}
        if r.get("complete"): out[n].update(contribucion_tras_ads=r["result"]["contribution_after_ads"], margen_tras_ads=r["result"]["margin_after_ads"])
        else: out[n]["faltan"] = r.get("missing") or r.get("why")
    return out

def equilibrio_unidades(contribucion_unitaria, costes_fijos):
    """Unidades para cubrir costes fijos (hipótesis del usuario). Sin coste fijo → NO CALCULABLE; contribución ≤ 0 → NO ALCANZABLE."""
    if costes_fijos is None or contribucion_unitaria is None: return {"estado": "NO CALCULABLE", "why": "faltan costes fijos (hipótesis del usuario) o contribución unitaria; no se inventan"}
    f = _num(costes_fijos, "costes_fijos"); c = float(contribucion_unitaria)
    if c <= 0: return {"estado": "NO ALCANZABLE", "why": "contribución unitaria ≤ 0: no se cubren costes fijos con ningún volumen"}
    return {"estado": "CALCULADO · HIPOTESIS", "unidades": math.ceil(f / c), "formula": "ceil(costes fijos ÷ contribución unitaria tras publicidad)", "clase": "HIPOTESIS"}
