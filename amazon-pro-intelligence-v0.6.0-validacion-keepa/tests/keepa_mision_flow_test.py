"""Flujo PRODUCTOS → ACTIVCORE → DIRECTOR IA → PREPARAR LANZAMIENTO con Keepa SIMULADO y tope de misión 10 tokens. Ninguna llamada de red."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.environ["AMAZON_PRO_NO_WORKER"] = "1"
import server as S
from backend import ai as AI, api6, home as H, econ6 as X
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
calls = []
def mkprod(i, price, title):
    csv = [None] * 19; csv[1] = [7000000 + i, price]; csv[3] = [7000000, 100 + i]
    return {"asin": "B0MOCK%04d" % i, "title": title, "brand": "MARCA%d" % i, "csv": csv}
PRODS = [mkprod(1, 3990, "Sérum capilar leave-on 100 ml"), mkprod(2, 1500, "Champú 400 ml"), mkprod(3, 2500, "Sérum cuero cabelludo 50 ml"), mkprod(4, None, "Producto sin precio")]
def get(url, h, t):
    calls.append(url)
    if "/token" in url: return 200, json.dumps({"tokensLeft": 60, "refillRate": 1}).encode(), ""
    if "/search" in url: return 200, json.dumps({"tokensLeft": 50, "tokensConsumed": 10, "products": PRODS}).encode(), ""
    return 500, b"{}", ""  # /product NO debe llamarse
ENV = {"KEEPA_API_KEY": "Z" * 64, "AMAZON_PRO_KEEPA_ENABLE": "1", "AMAZON_PRO_KEEPA_MISSION_CAP": "10", "AMAZON_PRO_KEEPA_MISSION_COUNTRIES": "ES", "AMAZON_PRO_KEEPA_MIN_GAP_S": "0"}
db = os.path.join(tempfile.mkdtemp(), "f.db")
srv = S.make_server(0, admin_token="t", db_path=db, cfg_fn=lambda: AI.config({}), admin_password="admin-password-123", keepa_env_fn=lambda: ENV, keepa_get=get); A = S.APP; ops = A["ops"]; AC, MG = "PRD-ACTIVCORE-V2", "PRD-PHIVITAL-MAGNESIO"
r = api6.order_launch(A, AC, "director")
check("orden de lanzamiento: sin aprobación NO se llama a Keepa", not [c for c in calls if "/search" in c or "/product" in c])
d = [x for x in ops.decisions(product=AC) if x["status"] == "PENDIENTE" and x["kind"] == "llamada_keepa_nueva"]
check("la consulta Keepa queda en la bandeja para aprobación", len(d) == 1)
ops.decide(d[0]["id"], True, "jose", "Autorización lectura Keepa misión 10 tokens"); done = ops.run_all(limit=10, backoff_s=0)
t = [x for x in done if x["id"] == [y for y in r["tasks"] if y["kind"] == "discovery.run"][0]["id"]][0]
det = t["result"]["detalle"]
check("discovery.run tras aprobar: 10 tokens, solo ES, PARCIAL honesto (el candidato sin precio queda pendiente por falta de presupuesto)", t["result"]["estado"] == "PARCIAL" and det["pendiente"] == 1 and det["tokens_gastados"] == 10 and [p["country"] for p in det["paises"]] == ["ES"])
check("se hizo UNA llamada /search y NINGUNA /product (tope respetado)", len([c for c in calls if "/search" in c]) == 1 and not [c for c in calls if "/product" in c])
check("ninguna llamada a DE/FR/IT (solo dominio 9 = ES)", all("domain=9" in c for c in calls if "/search" in c))
ms = A["keepa"].mission_status(); check("contador de misión: 10 confirmados, 0 restantes", ms["confirmed_spent"] == 10 and ms["remaining_worst_case"] == 0)
dos = A["launch"].build(AC, "FBA"); comp = [s for s in dos["sections"] if s["id"] == "competidores"][0]["rows"]
check("expediente: competidores reales del /search incorporados con ASIN, precio y comparabilidad", len(comp) >= 3 and all(c["asin"].startswith("B0MOCK") for c in comp) and all(c["comparabilidad"] for c in comp))
check("el candidato sin precio NO se registra como competidor (queda pendiente; no se inventa)", not [c for c in comp if c["asin"] == "B0MOCK0004"] and all(c["price"] is not None for c in comp))
check("expediente sigue NO DECIDIBLE (faltan costes y cumplimiento): recomendación proporcional a la evidencia", dos["recommendation"] == "NO DECIDIBLE TODAVÍA" if isinstance(dos["recommendation"], str) else dos["recommendation"].get("verdict") == "NO DECIDIBLE TODAVÍA")
# segunda orden: no duplica gasto ni tareas activas
r2 = api6.order_launch(A, AC, "director"); ops.run_all(limit=10, backoff_s=0)
check("repetir la orden NO vuelve a llamar a Keepa (no duplicación)", len([c for c in calls if "/search" in c]) == 1)
# economía
e = X.unit(S.svc_for(AC), "ES", 49.9)
check("economía ACTIVCORE: NO CALCULABLE sin tarifas/logística (no se inventan)", e["state"] == "NO CALCULABLE" and e["missing"])
check("ACTIVCORE conserva solo su coste documentado 10,03", S.svc_for(AC).assumptions()["ES"]["cogs"]["v"] == 10.03)
check("PHIVITAL no hereda costes de ACTIVCORE", S.svc_for(MG).assumptions()["ES"]["cogs"]["v"] is None)
check("precios de competidores no se usan como ventas: el expediente no contiene ventas de mercado", "unidades vendidas" not in json.dumps(dos, ensure_ascii=False).lower())
# DEMO vs REAL
hm = A["home"].build(AC); dm = H.demo()
check("DEMO separado de REAL: DEMO rotulado sintético; INICIO real no lo es", dm["mode"] == "DEMO" and "SINTÉTICOS" in dm["banner"] and hm.get("mode") != "DEMO")
blob = json.dumps([A["keepa"].ledger(50), A["keepa"].mission_ops(), A["keepa"].cached_records(), dos, hm], default=str, ensure_ascii=False)
check("la clave no aparece en ninguna salida", ENV["KEEPA_API_KEY"] not in blob)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
