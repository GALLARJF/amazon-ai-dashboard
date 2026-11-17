"""V1.0 · V1-05 — Motor financiero determinista: escenarios, sensibilidad y punto de equilibrio. Los supuestos de esta prueba son SINTÉTICOS (para verificar la aritmética)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import eu as E, finanzas100 as F
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
def f(v, st="DOCUMENTADO"): return E.fld(v, st, "SINTETICO prueba", "2026-01-01")
class Svc:
    pvp_default = 30.0
    def __init__(self, completo=True, st="DOCUMENTADO"): self.c, self.st = completo, st
    def assumptions(self):
        a = E.default_assumptions()
        for k in a:
            a[k].update(vat=f(0.21, self.st), cogs=f(3.0, self.st) if self.c else E.fld(), inbound=f(0.5, self.st), prep=f(0.2, self.st), fulfillment=f(3.0, self.st), storage=f(0.3, self.st), returns=f(0.5, self.st),
                        referral=E.fld({"low": 0.15, "high": 0.15, "threshold": 1e9, "min": 0.3}, self.st, "SINTETICO prueba", "2026-01-01"))
        return a
s = Svc(); u = F.X.unit(s, "ES", 24.20, "FBA", 0.10)["result"]
net = 24.20 / 1.21; contrib = net - (3.0 + 0.5 + 0.2 + 3.0 + 0.3 + 0.5) - 0.15 * 24.20
check("aritmética a mano: neto 20,00 y contribución %.4f coinciden con el motor" % contrib, abs(net - 20.0) < 1e-9 and abs(u["contribution_before_ads"] - contrib) < 0.011)
check("tras publicidad: contribución − ACoS×neto", abs(u["contribution_after_ads"] - (u["contribution_before_ads"] - 0.10 * 20.0)) < 0.011)
sn = F.sensibilidad(s, "ES", [20, 24.20, 30], [0.05, 0.10, 0.30])
check("sensibilidad 3×3 con clase heredada (DERIVADO o más débil, nunca OBSERVADO)", len(sn["celdas"]) == 3 and len(sn["celdas"][0]) == 3 and sn["clase"] in ("DERIVADO", "IMPORTADO", "ESTIMADO", "HIPOTESIS"))
m = [[c["margen_tras_ads"] for c in fila] for fila in sn["celdas"]]
check("monótona: más ACoS → menos margen; más PVP → más margen", all(m[i][0] > m[i][1] > m[i][2] for i in range(3)) and all(m[0][j] < m[1][j] < m[2][j] for j in range(3)))
check("la rejilla declara que PVP y ACoS son supuestos", "supuestos" in sn["hipotesis"])
es = F.escenarios(s, "ES", 24.20, 0.10)
check("escenarios ordenados: PESIMISTA < BASE < OPTIMISTA en contribución", es["PESIMISTA"]["contribucion_tras_ads"] < es["BASE"]["contribucion_tras_ads"] < es["OPTIMISTA"]["contribucion_tras_ads"])
check("determinista: dos ejecuciones idénticas", F.escenarios(s, "ES", 24.20, 0.10) == es and F.sensibilidad(s, "ES", [20, 30], [0.1]) == F.sensibilidad(s, "ES", [20, 30], [0.1]))
be = F.equilibrio_unidades(es["BASE"]["contribucion_tras_ads"], 1000)
check("punto de equilibrio = ceil(fijos/contribución) y es hipótesis", be["unidades"] == __import__("math").ceil(1000 / es["BASE"]["contribucion_tras_ads"]) and be["clase"] == "HIPOTESIS")
check("sin costes fijos → NO CALCULABLE (no se inventan)", F.equilibrio_unidades(5.0, None)["estado"] == "NO CALCULABLE")
check("contribución ≤ 0 → NO ALCANZABLE", F.equilibrio_unidades(-1.0, 1000)["estado"] == "NO ALCANZABLE" and F.equilibrio_unidades(0, 1000)["estado"] == "NO ALCANZABLE")
nc = F.sensibilidad(Svc(completo=False), "ES", [24.2], [0.1])
check("falta el coste de producto → NO CALCULABLE y dice qué falta", nc["estado"] == "NO CALCULABLE" and nc["faltan"])
check("supuestos blandos (HIPOTESIS) → resultado clase HIPOTESIS", F.sensibilidad(Svc(st="HIPOTESIS"), "ES", [24.2], [0.1])["clase"] == "HIPOTESIS")
for bad in ([[], [0.1]], [[24.2], []], [[True], [0.1]], [[24.2], [1.5]], [[-5], [0.1]], [[24.2] * 30, [0.1]]):
    try: F.sensibilidad(s, "ES", *bad); ok = False
    except ValueError: ok = True
    check("entrada inválida rechazada: %s" % str(bad)[:30], ok)
try: F.equilibrio_unidades(5, -1); ok = False
except ValueError: ok = True
check("coste fijo negativo rechazado", ok)
check("moneda local (SE/otros) → NO EVALUABLE sin inventar tipo de cambio", F.X.unit(s, "SE", 24.2)["complete"] is False)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
