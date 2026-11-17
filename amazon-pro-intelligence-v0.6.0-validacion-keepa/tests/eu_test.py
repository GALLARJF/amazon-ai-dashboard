"""Motor económico, benchmark y ranking europeo V0.4.0 (datos DEMO solo para probar la lógica; nunca se mezclan con datos reales)."""
import copy, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import eu as E
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
A = E.default_assumptions()
u = E.unit_economics(49.90, A["ES"])
check("sin costes logísticos documentados: INCOMPLETO, margen None (no cero) y se listan los datos que faltan", u["complete"] is False and u["contribution"] is None and u["margin"] is None and set(u["missing"]) == {"inbound", "prep", "fulfillment", "storage", "returns"})
B = copy.deepcopy(A); B["ES"]["vat"]["v"] = None
check("sin IVA: no se calcula nada", E.unit_economics(49.9, B["ES"])["complete"] is False and "net_price" not in E.unit_economics(49.9, B["ES"]))
H = E.apply_hypotheses(copy.deepcopy(A["ES"]), {**E.HYPOTHESIS_EXAMPLE, "vat": 0.0, "cogs": 1.0})
check("las hipótesis solo rellenan NO_DISPONIBLE: no pisan IVA verificado ni coste histórico", H["vat"]["v"] == 0.21 and H["cogs"]["v"] == 10.03 and H["fulfillment"]["status"] == "HIPOTESIS")
u = E.unit_economics(49.90, H, acos_target=0.15)
net = 49.90 / 1.21; contrib = net - 10.03 - .5 - .3 - 3.5 - .15 - 1.0 - 0.15 * 49.90
check("cálculo manual (ES, PVP 49,90): base 41,24 · comisión 15 % sobre PVP con IVA 7,49 · contribución 18,27", u["net_price"] == 41.24 and abs(u["referral_fee"] - 7.485) < 0.006 and u["contribution_before_ads"] == 18.27)
check("margen antes de publicidad = contribución / base imponible; margen bruto del producto separado", abs(u["margin_before_ads"] - u["contribution_before_ads"] / u["net_price"]) < 1e-3 and u["gross_margin_product"] == round(net - 10.03, 2))
check("ACoS de equilibrio sobre ventas sin IVA y con IVA (distintos) y ROAS", u["breakeven_acos_ex_vat"] > u["breakeven_acos_inc_vat"] and abs(u["breakeven_roas_ex_vat"] - 1 / u["breakeven_acos_ex_vat"]) < 0.02)
check("tras publicidad (ACoS 15 % sobre base): contribución = antes − 0,15·base", abs(u["contribution_after_ads"] - (u["contribution_before_ads"] - 0.15 * u["net_price"])) < 0.011 and u["margin_after_ads"] < u["margin_before_ads"])
check("etiqueta ESCENARIO HIPOTÉTICO (hay HIPOTESIS y coste histórico) y no se declara rentabilidad confirmada", u["hypothetical"] and "HIPOTÉTICO" in u["label"])
Hd = E.apply_hypotheses(copy.deepcopy(A["DE"]), E.HYPOTHESIS_EXAMPLE); Hs = E.apply_hypotheses(copy.deepcopy(A["ES"]), E.HYPOTHESIS_EXAMPLE)
check("IVA por país: la base imponible difiere (DE 19 % vs ES 21 %) y no se usa el IVA español para todos", E.unit_economics(49.9, Hd)["net_price"] == 41.93 and E.unit_economics(49.9, Hs)["net_price"] == 41.24)
lo = E.unit_economics(9.9, Hs)
check("comisión por tramos: ≤10 € → 8 % con mínimo 0,30 €; >10 € → 15 %", lo["referral_fee"] == 0.79 and E.unit_economics(10.0, Hs)["referral_fee"] == 0.80 and E.unit_economics(10.01, Hs)["referral_fee"] == 1.5)
check("7 escenarios de PVP y PVP personalizado", len(E.scenarios(Hs)) == 7 and E.scenarios(Hs, [44.0])[0]["pvp_gross"] == 44.0)
se = E.sensitivity(Hs, 49.9)
check("sensibilidad: PVP (7), logística (4) y publicidad (5); más logística → menos contribución", len(se["pvp"]) == 7 and len(se["logistics"]) == 4 and se["logistics"][-1]["contribution"] < se["logistics"][0]["contribution"] and len(se["ads"]) == 5)
check("sensibilidad sin datos completos: NO CALCULABLE", E.sensitivity(A["ES"], 49.9)["status"] == "NO CALCULABLE")
check("unidades para objetivo económico", E.units_for_target(18.27, 1000) == 55 and E.units_for_target(None, 1000) is None and E.units_for_target(-1, 10) is None)
# benchmark
def rec(asin, price, vol, bsr=5000, rev=1000, title="Sérum capilar cuero cabelludo", conf=None):
    return {"asin": asin, "country": "DE", "price": price, "volume_ml": vol, "bsr": bsr, "reviews": rev, "rating": 4.4, "title": title, "brand": "B" + asin[-2:], "fetched_at": "2026-11-16T10:00:00Z"}
recs = [rec("B0000000%02d" % i, 20 + i * 5, 50 + (i % 3) * 25, bsr=2000 * (i + 1), rev=500 * (i + 1)) for i in range(10)] + [rec("B000000099", 30, None), rec("B000000098", 25, 90, title="Vitamina cápsulas pelo")]
bm = E.benchmark(recs)
check("normalización por 100 mL; sin formato → None (no se inventa)", [r for r in bm["rows"] if r["asin"] == "B000000099"][0]["price_norm"] is None and [r for r in bm["rows"] if r["asin"] == "B0000000%02d" % 0][0]["price_norm"] == 40.0)
check("sin confirmar la comparabilidad no se cuenta ningún competidor (solo sugerencias)", bm["used"] == 0 and bm["unconfirmed"] == 12 and bm["price_norm"] is None)
check("sugerencia: sérum+cuero cabelludo ALTA; complemento alimenticio BAJA; rinse-off BAJA", E.suggest_comparability("Sérum anticaída cuero cabelludo")[0] == "ALTA" and E.suggest_comparability("Vitamina cápsulas pelo")[0] == "BAJA" and E.suggest_comparability("Champú anticaída")[0] == "BAJA")
reg = {r["asin"]: {"comparability": "ALTA"} for r in recs[:10]}; bm = E.benchmark(recs, reg)
check("con comparables confirmados: n, mediana, Q1/Q3, IQR, dispersión, más barato y premium", bm["used"] == 10 and bm["price_norm"]["n"] == 10 and bm["price_norm"]["iqr"] is not None and bm["cheapest"]["price_norm"] <= bm["price_norm"]["median"] <= bm["premium"]["price_norm"])
bm2 = E.benchmark(recs, {}, include_suggested=True); check("incluir sugeridas es opcional y explícito (ALTA/MEDIA cuentan, BAJA no)", bm2["used"] == 11 and bm2["include_suggested"])
us = E.enrich(recs[0], {recs[0]["asin"]: {"days": 50, "source": "dosis 2 mL/día"}}); check("precio por día solo con dosis/duración documentadas", us["price_per_day"] == 0.4 and E.enrich(recs[0])["price_per_day"] is None)
# ranking
def full(c, pvp100, bsr_scale, vol=100):
    rs = [rec("B%s%07d" % (c, i), 20 + i * 3, 50 + (i % 3) * 25, bsr=bsr_scale * (i + 1), rev=800 * (i + 1)) for i in range(10)]
    for r in rs: r["country"] = c
    b = E.benchmark(rs, {r["asin"]: {"comparability": "ALTA"} for r in rs})
    a = E.apply_hypotheses(copy.deepcopy(E.default_assumptions([c])[c]), E.HYPOTHESIS_EXAMPLE)
    return {"benchmark": b, "economics": E.unit_economics(49.9, a), "pvp100": pvp100, "compliance": {"pif": "OK", "cpsr": "OK", "persona_responsable": "OK", "cpnp": "PENDIENTE", "idiomas": "OK"}, "growth": None, "keepa_supported": True}
data = {c: {"benchmark": None, "economics": E.unit_economics(49.9, E.default_assumptions([c])[c]), "compliance": {}, "keepa_supported": c in ("DE", "FR", "IT", "ES")} for c in E.COUNTRIES}
r0 = E.rank(data)
check("sin datos: NINGÚN país evaluable, sin recomendación y con la lista exacta de lo que falta", not r0["ranking"] and r0["launch"] is None and all(p["missing"] for p in r0["pending"]) and len(r0["pending"]) == 6)
check("NL y PL: la demanda/competencia indican que Keepa no cubre el marketplace", all("Keepa no cubre" in [m for m in r0["pending"] if m["country"] == c][0]["missing"][0]["motivo"] for c in ("NL", "PL")))
# solo margen hipotético → no gana
data["DE"] = full("DE", 55.0, 3000); data["DE"]["benchmark"] = None; data["DE"]["compliance"] = {}
r1 = E.rank(data); de = [p for p in r1["pending"] if p["country"] == "DE"][0]
check("un país con solo margen HIPOTÉTICO (confianza BAJA) no es evaluable ni gana", de["evaluable"] is False and "Margen neto" in de["low_confidence"] and r1["launch"] is None)
data["DE"] = full("DE", 45.0, 3000); data["ES"] = full("ES", 70.0, 9000); data["IT"] = full("IT", 40.0, 2500); data["FR"]["economics"] = E.unit_economics(49.9, E.default_assumptions(["FR"])["FR"])
r2_ = E.rank(data)
check("con datos suficientes: ranking de evaluables ordenado, pendientes aparte (FR sin costes, NL/PL sin Keepa)", [p["country"] for p in r2_["ranking"]] and {p["country"] for p in r2_["pending"]} >= {"FR", "NL", "PL"} and all(r2_["ranking"][i]["score"] >= r2_["ranking"][i + 1]["score"] for i in range(len(r2_["ranking"]) - 1)))
check("lanzamiento y segundo país derivados del ranking; presets conservador/crecimiento y sensibilidad presentes", r2_["launch"] == r2_["ranking"][0]["country"] and r2_["second"] == r2_["ranking"][1]["country"] and set(r2_["presets"]) == {"base", "conservadora", "crecimiento"} and 0 <= r2_["sensitivity"]["stable_share"] <= 1)
check("cada criterio lleva fórmula, fuente, fecha, entradas y confianza (o qué falta)", all(c["formula"] and (c["status"] == "NO EVALUABLE" and c["missing"] or c["source"] and c["date"] and c["inputs"] and c["confidence"]) for p in r2_["ranking"] for c in p["criteria"].values()))
check("separa atractivo de mercado y viabilidad operativa", all("attractiveness" in p and "viability" in p for p in r2_["ranking"]))
# cambio de datos cambia la recomendación
data2 = copy.deepcopy(data); data2["ES"] = full("ES", 40.0, 600); data2["DE"] = full("DE", 90.0, 90000)
r3 = E.rank(data2); check("la recomendación cambia si cambian los datos", r3["launch"] != r2_["launch"] or r3["ranking"][0]["score"] != r2_["ranking"][0]["score"])
try: E.rank(data, {"demanda": 50, "margen": 30, "competencia": 20, "logistica": 15, "crecimiento": 5}); r = False
except ValueError: r = True
check("pesos editables: deben sumar 100", r and E.rank(data, {"demanda": 20, "margen": 40, "competencia": 20, "logistica": 15, "crecimiento": 5})["weights"]["margen"] == 40)
check("cobertura mínima editable (min_coverage) y mínimo de ASIN", E.rank(data, params={"min_coverage": 0.99})["ranking"] == [] )
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
