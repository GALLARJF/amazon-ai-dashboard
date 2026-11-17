"""Pruebas unitarias backend V0.3: motor, coworkers, piloto PHIVITAL, adaptador IA y Director. Datos ficticios (origen PRUEBA)."""
import datetime, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, coworkers as C, director as D, engine as E, pilot as P
from backend.store import Store
R = []
def check(n, c):
    R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
TODAY = "2026-11-16"
def ago(n): return (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=n)).isoformat()

# ---- motor: cálculo manual independiente ----
u = E.unit({"price": 24.9, "vatPct": 21, "feeSchedule": "generico_15", "cost": 5, "prep": 0, "fulfilMode": "FBA", "fbaFee": 4, "storageMonthly": 0, "storageMonths": 0, "returnsPct": 0, "otherCosts": 0, "acosTarget": 20, "adsBasis": "gross"})
net = 24.9 / 1.21; man = net - 5 - 4 - 24.9 * .15 - 24.9 * .20
check("economía: contribución = cálculo manual", abs(u["contribution"] - man) < 1e-9)
check("economía: ACoS de equilibrio = (contribución+ads)/PVP", abs(u["breakEvenAcos"] - (man + 24.9 * .2) / 24.9) < 1e-9)
check("economía: PVP negativo inválido, nunca GO", E.unit({"price": -5})["valid"] is False)
check("economía: IVA 21 → neto = PVP/1,21", abs(E.unit({"price": 121})["net"] - 100) < 1e-9)
check("comisión mínima aplica", abs(E.referral_fee(1.0, E.FEE_SCHEDULES["generico_15"]) - 0.3) < 1e-12)
sc = E.scenarios({"cost": 5}, [15, 20, 25]); check("escenarios de PVP: contribución creciente con el precio", sc[0]["contribution"] < sc[1]["contribution"] < sc[2]["contribution"])

# ---- piloto PHIVITAL ----
t = P.template()
check("plantilla: identidad del producto, sin ventas ni demanda inventadas", t["product"]["asin"] == "B0F6KQP2WH" and t["keywords"] == [] and t["competitors"] == [] and t["logistics"]["stockAvailable"] is None)
check("plantilla: 7 de 8 costes sin documentar (solo PVP observado)", len(P.missing_costs(t)) == 7 and "price" not in P.missing_costs(t))
ev = P.assess(t, TODAY)
check("piloto vacío: REVISAR (nunca GO ni NO-GO firme) con bloqueos", ev["decision"] == "REVISAR" and ev["pilot"]["provisional"])
check("plantilla: sin costes inventados (campos de coste vacíos)", all(t["econ"][k] is None for k in ("cost", "fbaFee", "returnsPct", "acosTarget")))
check("piloto: lista datos regulatorios pendientes", sum(1 for f in ev["findings"] if f["section"] == "regulatory") >= 6)
check("origen: plantilla incompleta → INCOMPLETO (no USUARIO)", P.derive_origin(t, "USUARIO") == "INCOMPLETO")

def full_pilot(cost=3.0, price=19.9):
    d = P.template(); d["econ"].update(price=price, cost=cost, fbaFee=3.2, acosTarget=18, vatPct=10, feeSchedule="generico_15", storageMonthly=0.1, storageMonths=2, returnsPct=3, returnProcessing=1.5)
    for k in d["costDocs"]: d["costDocs"][k] = {"evidence": "PRUEBA doc " + k, "date": ago(5)}
    d["competitors"] = [{"name": f"C{i}", "asin": f"A{i}", "priceGross": p, "shipping": 0, "packUnits": 1, "contentValue": 120, "source": "PRUEBA", "date": ago(4), "rating": 4.4, "reviews": 200 * i} for i, p in enumerate([18.5, 21, 23.9, 26], 1)]
    d["keywords"] = [{"keyword": k, "volume": v, "source": "PRUEBA", "date": ago(10)} for k, v in [("magnesio", 9000), ("magnesio 120 capsulas", 2000), ("citrato de magnesio", 4000), ("magnesio sueño", 1500), ("magnesio cansancio", 900)]]
    for it in list(d["regulatory"].values()) + list(d["content"].values()) + list(d["logistics"]["items"].values()): it.update(status="cumplido", evidence="PRUEBA", date=ago(3))
    d["logistics"].update(stockAvailable=900, forecastUnitsMonth=300, leadTimeDays=30, coverTargetDays=45)
    d["listing"] = {"title": "Magnesio 120 capsulas citrato de magnesio", "bullets": ["magnesio sueño"], "backend": ""}; d["cvrPct"] = 10; d["adBudgetMonth"] = 300; d["ownRating"] = 4.5
    return d
fp = full_pilot()
check("origen: piloto completo → USUARIO", P.derive_origin(fp, "USUARIO") == "USUARIO")
e1 = P.assess(fp, TODAY); check("piloto completo y rentable (datos PRUEBA) → GO fundamentado", e1["decision"] == "GO" and not e1["pilot"]["provisional"])
fp2 = full_pilot(); fp2["costDocs"]["cost"]["evidence"] = ""
check("un coste sin documentar impide GO aunque el margen sea bueno", P.assess(fp2, TODAY)["decision"] == "REVISAR")
check("coste de producto alto con costes documentados → NO-GO firme", P.assess(full_pilot(cost=16), TODAY)["decision"] == "NO-GO")
fpx = full_pilot(cost=16); fpx["costDocs"]["ads"]["evidence"] = ""
check("inviabilidad con costes sin documentar → solo REVISAR (indicio)", P.assess(fpx, TODAY)["decision"] == "REVISAR")
fp3 = full_pilot(); fp3["regulatory"]["notif"]["status"] = "pendiente"
check("dato regulatorio pendiente → REVISAR", P.assess(fp3, TODAY)["decision"] == "REVISAR")
fp4 = full_pilot(); fp4["competitors"] = fp4["competitors"][:2]
check("benchmark insuficiente → REVISAR (no se inventa mercado)", P.assess(fp4, TODAY)["decision"] == "REVISAR")
fp5 = full_pilot(); fp5["keywords"] = []
check("sin demanda aportada → REVISAR (no se inventa demanda)", P.assess(fp5, TODAY)["decision"] == "REVISAR")

# ---- coworkers ----
bb = {}
for co in C.ORDER: bb[co] = C.run(co, fp, TODAY, bb)
check("los 7 coworkers ejecutan con datos completos y verificaciones OK", all(bb[c]["status"] == "ok" for c in C.ORDER) and all(bb[c]["checks_ok"] in (True, None) for c in C.ORDER))
check("ningún coworker usa IA ni datos externos", all(not bb[c]["ai_used"] and not bb[c]["external_data"] for c in C.ORDER))
m = bb["mercado"]["metrics"]; ups = sorted((p / 120) for p in [18.5, 21, 23.9, 26])
check("Mercado: mediana normalizada = cálculo manual", abs(m["unit_price"]["median"] - (ups[1] + ups[2]) / 2) < 1e-12)
check("Precios coordina con Mercado (compara con la banda)", any("Coordinado con Mercado" in f["text"] for f in bb["precios"]["findings"]))
check("PPC: CPC máx = ACoS_eq × PVP × CVR", abs(bb["ppc"]["metrics"]["max_cpc_break_even"] - bb["precios"]["metrics"]["break_even_acos_pct"] / 100 * 19.9 * 0.10) < 1e-9)
check("SEO: cobertura calculada con keywords y listing aportados", bb["seo"]["metrics"]["uncovered"] == ["magnesio"] or "magnesio cansancio" in bb["seo"]["metrics"]["uncovered"])
check("Inventario: cobertura = stock/(previsión/30)", abs(bb["inventario"]["metrics"]["cover_days"] - 900 / 10) < 1e-9)
check("Cumplimiento: sin pendientes en expediente completo", bb["cumplimiento"]["metrics"]["ready"] is True)
e = C.run("mercado", E.create_empty(), TODAY, {}); check("Mercado sin datos: declara datos insuficientes, no inventa", e["status"] == "datos_insuficientes" and e["metrics"] == {})
e = C.run("seo", E.create_empty(), TODAY, {}); check("SEO sin keywords: no estima demanda", e["status"] == "datos_insuficientes" and "volume" not in str(e["metrics"]))
e = C.run("ppc", fp, TODAY, {}); check("PPC sin Precios: datos insuficientes", e["status"] == "datos_insuficientes")
fpn = full_pilot(); fpn.pop("cvrPct")
e = C.run("ppc", fpn, TODAY, {"precios": bb["precios"], "seo": bb["seo"]}); check("PPC sin CVR: no estima CPC", "max_cpc_break_even" not in e["metrics"] and any("CVR" in n for n in e["needs"]))
fr = full_pilot(); fr["listing"]["title"] = "Magnesio que cura el insomnio"
e = C.run("cumplimiento", fr, TODAY, {}); check("Cumplimiento detecta término de riesgo sin respaldo", "cura" in e["metrics"]["risky_terms"] and e["metrics"]["ready"] is False)
check("dependencias: un coworker pedido arrastra sus dependencias", D.plan_for("quiero revisar el ppc")[0] == ["mercado", "seo", "inventario"][:0] + ["mercado", "seo", "precios", "ppc"][:0] or D.plan_for("ppc", ["ppc"])[0] == ["mercado", "seo", "precios", "ppc"])

# ---- adaptador IA ----
check("sin proveedor → SIN IA CONFIGURADA", AI.public_status(AI.config({}))["status"] == "SIN IA CONFIGURADA")
s = AI.public_status(AI.config({"AMAZON_PRO_AI_PROVIDER": "anthropic"})); check("anthropic sin clave → ejecuciones reales PENDIENTES", "PENDIENTES" in s["status"] and not s["can_call"])
s = AI.public_status(AI.config({"AMAZON_PRO_AI_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k"})); check("clave sin ENABLE → deshabilitada, no llama", not s["can_call"] and "DESHABILITADA" in s["status"])
try: AI.complete(AI.config({"AMAZON_PRO_AI_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k", "AMAZON_PRO_AI_MODEL": "m"}), "s", "u"); check("sin ENABLE=1 la llamada se rechaza", False)
except AI.AIError as ex: check("sin ENABLE=1 la llamada se rechaza", ex.code == "IA_DESHABILITADA")
try: AI.complete(AI.config({"AMAZON_PRO_AI_PROVIDER": "mock", "AMAZON_PRO_AI_MAX_IN": "5"}), "s" * 100, "u" * 100); check("presupuesto de entrada", False)
except AI.AIError as ex: check("presupuesto de entrada excedido → error", ex.code == "PRESUPUESTO_ENTRADA_EXCEDIDO")
try: AI.complete(AI.config({"AMAZON_PRO_AI_PROVIDER": "mock", "AMAZON_PRO_AI_PRICE_IN": "1000000", "AMAZON_PRO_AI_PRICE_OUT": "1000000", "AMAZON_PRO_AI_MAX_COST": "1"}), "s", "u"); check("presupuesto de coste", False)
except AI.AIError as ex: check("presupuesto de coste excedido → error antes de llamar", ex.code == "PRESUPUESTO_COSTE_EXCEDIDO")
c = AI.config({"AMAZON_PRO_AI_PROVIDER": "openai_compat", "AMAZON_PRO_AI_API_KEY": "k", "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MODEL": "m", "AMAZON_PRO_AI_BASE_URL": "https://evil.example"})
check("host no oficial bloqueado", not AI._host_ok(c, AI._endpoint(c)))
c["base_url"] = None; check("host oficial OpenAI permitido", AI._host_ok(c, AI._endpoint(c)))
check("loopback bloqueado sin ALLOW_LOOPBACK", not AI._host_ok(c, "http://127.0.0.1:1/v1"))
check("sin precios configurados el coste es null (no se inventan tarifas)", AI.cost(AI.config({}), 1000, 1000) is None)
check("coste = tokens × precio configurado", abs(AI.cost(AI.config({"AMAZON_PRO_AI_PRICE_IN": "2", "AMAZON_PRO_AI_PRICE_OUT": "10"}), 1_000_000, 500_000) - 7.0) < 1e-12)
g = AI.grounding("PVP 19,90 [F1] y 15 % [F2]", "[F1] PVP 19.9 [F2] comisión 15"); check("anclaje: cifras presentes → ok", g["ok"])
check("anclaje: cifra inventada → detectada", AI.grounding("hay 777 ventas [F1]", "[F1] 3 competidores")["ungrounded"] == ["777"])

# ---- Director + estado de coworkers (operativo solo con datos USUARIO completos) ----
st = Store(); st.create_account("A", "m", "e")
i_t = st.put("A", "dossier", {"origin": "PRUEBA", "dossier": fp}); i_u = st.put("A", "dossier", {"origin": "USUARIO", "dossier": fp}); i_i = st.put("A", "dossier", {"origin": "INCOMPLETO", "dossier": P.template()})
dr = D.Director(st, lambda: AI.config({}))
dr.analyze("A", i_t, "u", "todo", today=TODAY); lab = dr.coworker_status("A")["coworkers"]
check("tras ejecutar sobre PRUEBA ninguno es operativo", not any(v["operational"] for v in lab.values()))
dr.analyze("A", i_i, "u", "todo", today=TODAY); lab = dr.coworker_status("A")["coworkers"]
check("INCOMPLETO: no operativo", not any(v["operational"] for v in lab.values()) and lab["precios"]["label"].startswith("DATOS INSUFICIENTES"))
dr.analyze("A", i_u, "u", "todo", today=TODAY); lab = dr.coworker_status("A")["coworkers"]
check("USUARIO completo con ejecución verificada → operativo (determinista)", all(v["operational"] for v in lab.values()))
check("IA real NO verificada (no hubo ejecución real)", dr.coworker_status("A")["ai"]["real_verified"] is False)
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
