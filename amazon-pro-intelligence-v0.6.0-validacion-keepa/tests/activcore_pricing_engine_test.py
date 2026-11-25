"""Bloque 1 (encargo 25/11/2026, PR #5): motor económico ACTIVCORE por SKU/lote/canal. Sin red, sin gasto."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import activcore_pricing_engine as PE

R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
def raises(f, *a, **k):
    try:
        f(*a, **k); return False
    except (ValueError, LookupError):
        return True


# ---- catálogo expuesto (solo lectura)
disp = PE.disponibles()
check("expone SKU/lote/canal sin inventar nada fuera del encargo", disp["skus"] == ["ACTIVCORE_V2"] and set(disp["lotes"]) == {"lote1", "lote2"} and set(disp["canales"]) == {"FBA", "FBM"})

# ---- validación de entradas
check("SKU/lote/canal desconocidos se rechazan, nunca se calculan con supuestos", raises(PE.sku_lot_channel_economics, "OTRO_SKU", "lote1", "FBA") and raises(PE.sku_lot_channel_economics, "ACTIVCORE_V2", "lote9", "FBA") and raises(PE.channel_baseline, 49.9, "DHL"))

# ---- redondeo por partida (media al alza, no banker's rounding)
check("_r2 redondea por partida con media al alza", PE._r2(7.485) == 7.49 and PE._r2(0.125) == 0.13 and PE._r2(None) is None)

# ---- línea por línea del canal FBA
base_fba = PE.channel_baseline(49.90, "FBA")
check("comisión FBA = 15% del PVP BRUTO (49,90€), no del neto", base_fba["lineas"]["comision"]["v"] == PE._r2(0.15 * 49.90))
check("FBA condicionado a peso/dimensiones queda etiquetado CONDICIONADO, no VERIFICADO", base_fba["lineas"]["fba"]["status"] == "CONDICIONADO" and base_fba["lineas"]["fba"]["v"] == 3.81)
check("plan 39€/mes amortizado sobre 300 uds/90 días = 100 uds/mes ⇒ 0,39 €/ud", base_fba["lineas"]["plan_amortizado"]["v"] == PE._r2(39.0 / 100.0))
check("el canal FBA se completa con todas las líneas declaradas", base_fba["complete"] is True and isinstance(base_fba["total_antes_ads"], float))
base_fbm = PE.channel_baseline(49.90, "FBM")

# ---- lote1 (incluye regulación) vs lote2 (pendiente) — anti-doble-imputación
eco_l1 = PE.sku_lot_channel_economics("ACTIVCORE_V2", "lote1", "FBA")
check("lote1: coste 12,55€ incluye regulación; no se resta una partida de regulación aparte", eco_l1["lote_incluye"] == ["regulacion"] and "regulacion" not in eco_l1["canal_baseline"]["lineas"])
check("lote1 completo: margen bruto y contribución se calculan (coste y canal disponibles)", eco_l1["complete"] is True and eco_l1["margen_bruto"] is not None and eco_l1["contribucion_antes_ads"] is not None)
check("margen bruto = PVP neto de IVA − coste del lote (12,55€), sin tocar comisiones de canal", eco_l1["margen_bruto"] == PE._r2(eco_l1["precio_neto_iva"] - 12.55))
check("contribución = margen bruto − canal_baseline.total_antes_ads (no se duplica el coste de canal)", eco_l1["contribucion_antes_ads"] == PE._r2(eco_l1["precio_neto_iva"] - 12.55 - eco_l1["canal_baseline"]["total_antes_ads"]))

# ---- conciliación con las cifras de referencia de José ("base FBA 15,40 / FBM 14,81 antes de Ads") — RESUELTO:
# coinciden exactamente con la CONTRIBUCIÓN de lote1 (no con el total de canal solo), y la prueba fija ese resultado
# como regresión: si un cambio futuro del motor deja de reproducirlas, debe fallar aquí, no pasar desapercibido.
check("contribución de lote1/FBA reproduce exactamente la referencia de José (15,40€)", eco_l1["contribucion_antes_ads"] == 15.40 and eco_l1["reconciliacion_jose"]["nota"].startswith("COINCIDE"))
eco_l1_fbm = PE.sku_lot_channel_economics("ACTIVCORE_V2", "lote1", "FBM")
check("contribución de lote1/FBM reproduce exactamente la referencia de José (14,81€)", eco_l1_fbm["contribucion_antes_ads"] == 14.81 and eco_l1_fbm["reconciliacion_jose"]["nota"].startswith("COINCIDE"))

eco_l2 = PE.sku_lot_channel_economics("ACTIVCORE_V2", "lote2", "FBA")
check("lote2 (coste 8,99€ marcado PENDIENTE por José): SÍ calcula, pero queda marcado explícitamente sin confirmar", eco_l2["complete"] is True and eco_l2["coste_sin_confirmar"] is True and "PENDIENTE DE CONFIRMAR" in eco_l2["state"])
check("lote2 usa su propio coste (8,99€), nunca el de lote1 (12,55€) como sustituto silencioso", eco_l2["coste_producto"]["v"] == 8.99 and eco_l2["margen_bruto"] == PE._r2(eco_l2["precio_neto_iva"] - 8.99))
_coste_real = PE.LOTES["lote2"]["coste"]
PE.LOTES["lote2"]["coste"] = PE.fld(None, "PENDIENTE", "simulación de coste totalmente ausente")
eco_ausente = PE.sku_lot_channel_economics("ACTIVCORE_V2", "lote2", "FBA")
check("un coste con v=None (dato realmente ausente) SÍ bloquea el margen", eco_ausente["complete"] is False and eco_ausente["margen_bruto"] is None)
PE.LOTES["lote2"]["coste"] = _coste_real

# ---- IVA es informativo, nunca se trata como coste de margen
check("el IVA se declara aparte y como INFORMATIVO (no resta del margen/contribución)", eco_l1["iva"]["clase"].startswith("INFORMATIVO") and eco_l1["iva"]["importe"] == PE._r2(49.90 - eco_l1["precio_neto_iva"]))

# ---- ningún dato de este bloque se declara VERIFICADO salvo el IVA (honestidad: José dio cifras estimadas/provisionales)
no_verificado = all(f["status"] != "VERIFICADO" for f in [PE.PVP] + list(PE.LOTES["lote1"].values() if False else [PE.LOTES["lote1"]["coste"]]))
check("PVP y costes de lote se etiquetan ESTIMADO/PENDIENTE, nunca VERIFICADO sin evidencia oficial", PE.PVP["status"] != "VERIFICADO" and PE.LOTES["lote1"]["coste"]["status"] != "VERIFICADO" and PE.VAT_RATE["status"] == "VERIFICADO")

# ---- canal/volumen override no rompe nada y permite simular Bloque 2 (simulador) más adelante
base_fba_vol_distinto = PE.channel_baseline(49.90, "FBA", volumen_90d_override=900)
check("un volumen distinto cambia solo la amortización del plan, no las tarifas fijas", base_fba_vol_distinto["lineas"]["plan_amortizado"]["v"] == PE._r2(39.0 / 300.0) and base_fba_vol_distinto["lineas"]["fba"]["v"] == base_fba["lineas"]["fba"]["v"])

print("\n%d/%d" % (sum(R), len(R)))
sys.exit(0 if all(R) else 1)
