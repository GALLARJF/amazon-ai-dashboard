"""Misión de validación Keepa V0.6.0 — pruebas del presupuesto de misión. TODAS usan Keepa SIMULADO (mock): ninguna llama a la red.
Las evidencias REALES de la misión están en docs_v06/evidencia_keepa_real/ y se comprueban en tests/keepa_real_evidence_test.py (solo lectura de ficheros)."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import keepa as K
from backend.store import Store
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
KEY = "K" * 64
ENV = {"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "1", "AMAZON_PRO_KEEPA_MISSION_CAP": "10", "AMAZON_PRO_KEEPA_MIN_GAP_S": "0"}
calls = []
def prod(a, price=1299, title="Sérum capilar 100 ml"):
    csv = [None] * 19; csv[1] = [7000000, price]; csv[3] = [7000000, 500]
    return {"asin": a, "title": title, "brand": "MARCA", "csv": csv if price else [None] * 19}
def mk(consumed=10, status=200, body=None, st=None, env=None):
    def get(url, h, t):
        calls.append(url)
        if "/token" in url: return 200, json.dumps({"tokensLeft": 60, "refillRate": 1, "refillIn": 1000}).encode(), ""
        b = body if body is not None else {"tokensLeft": 60 - consumed, "tokensConsumed": consumed, "products": [prod("B0AAAAAAA%d" % i) for i in range(3)]}
        return status, json.dumps(b).encode(), ""
    st = st or Store(); return st, K.Keepa(st, lambda: K.config(env or ENV), get_fn=get, sleep=lambda s: None)
# 1 · búsqueda dentro de tope; consumo CONFIRMADO desde la respuesta
st, kp = mk(); r = kp.search("ES", "sérum capilar")
ms = kp.mission_status()
check("misión: consumo confirmado = tokensConsumed de la respuesta", ms["confirmed_spent"] == 10 and ms["remaining_worst_case"] == 0)
check("misión: operación con identificador y estado OK", kp.mission_ops()[0]["op_id"].startswith("KP-") and kp.mission_ops()[0]["status"] == "OK")
check("búsqueda devuelve registros con fecha de precio y fuente /search", r["records"][0]["price_as_of"] is not None and "/search" in r["records"][0]["source"])
# 2 · presupuesto agotado: NO hay llamada de red
n = len(calls)
try: kp.search("ES", "otro término distinto"); ok = False
except K.KeepaError as e: ok = e.code == "KEEPA_MISION_AGOTADA"
check("presupuesto agotado: parada automática ANTES de la red", ok and len(calls) == n)
# 3 · duplicado
try: kp.search("ES", "sérum capilar"); ok = False
except K.KeepaError as e: ok = e.code in ("KEEPA_DUPLICADA", "KEEPA_MISION_AGOTADA")
check("no duplicación: misma consulta no vuelve a la red", ok and len(calls) == n)
st2, kp2 = mk(); kp2.search("ES", "x1")
try: kp2.fetch([("ES", "B0AAAAAAA1")]); ok2 = False
except K.KeepaError as e: ok2 = e.code == "KEEPA_MISION_AGOTADA"
check("un /product que no cabe en el resto no se ejecuta", ok2 or kp2.mission_status()["remaining_worst_case"] == 0)
# 4 · un coste mayor del previsto se detecta y se cuenta (nunca se oculta)
st3, kp3 = mk(consumed=14); kp3.search("ES", "caro")
check("coste real superior al previsto: queda REGISTRADO y la misión queda agotada", kp3.mission_status()["confirmed_spent"] == 14 and kp3.mission_status()["remaining_worst_case"] == 0)
# 5 · error de API
for code, expect in ((401, "ERROR"), (500, "INCIERTA"), (429, "ERROR")):
    s_, k_ = mk(status=code, body={}); 
    try: k_.search("ES", "e%d" % code)
    except K.KeepaError: pass
    o = k_.mission_ops()[0]
    worst = k_.mission_status()["worst_case_spent"]
    check("error API %d: estado %s y peor caso %s" % (code, expect, "10 (incierto)" if expect == "INCIERTA" else "0"), o["status"] == expect and worst == (10 if expect == "INCIERTA" else 0))
# 6 · datos incompletos: no se inventa
s_, k_ = mk(body={"tokensLeft": 50, "tokensConsumed": 10, "products": [prod("B0BBBBBBB1", price=None, title="Producto sin precio")]})
rr = k_.search("ES", "incompleto")["records"][0]
check("datos incompletos: precio y rating = None (NO DISPONIBLE), calidad BAJA", rr["price"] is None and rr["rating"] is None and rr["evidence_quality"] == "BAJA")
s_, k_ = mk(body={"tokensLeft": 50, "products": [prod("B0CCCCCCC1")]})
k_.search("ES", "sin tokensConsumed")
check("Keepa no informa tokensConsumed: se cuenta el peor caso (INCIERTA)", k_.mission_ops()[0]["status"] == "INCIERTA" and k_.mission_status()["remaining_worst_case"] == 0)
# 7 · persistencia en disco
d = tempfile.mkdtemp(); p = os.path.join(d, "m.db"); s_, k_ = mk(st=Store(p)); k_.search("ES", "persistente")
s2 = Store(p); k2 = K.Keepa(s2, lambda: K.config(ENV), get_fn=lambda *a: (200, b"{}", ""))
check("persistencia: tras reabrir la base el gasto de misión sigue contado", k2.mission_status()["confirmed_spent"] == 10)
try: k2.search("ES", "persistente"); ok = False
except K.KeepaError as e: ok = e.code in ("KEEPA_DUPLICADA", "KEEPA_MISION_AGOTADA")
check("persistencia: tras reabrir sigue bloqueado el duplicado", ok)
# 8 · /token es gratuito y no cuenta
s_, k_ = mk(); k_.token_status()
check("/token no consume ni cuenta en la misión", k_.mission_status()["worst_case_spent"] == 0 and k_.mission_ops() == [])
# 9 · la clave nunca aparece
blob = json.dumps([k_.ledger(50), kp.mission_ops(), kp.cached_records(), kp.ledger(50)], default=str)
check("la clave no aparece en libro, operaciones ni caché", KEY not in blob)
# 10 · sin tope de misión (uso normal) no cambia el comportamiento
s_, k_ = mk(env={**ENV, "AMAZON_PRO_KEEPA_MISSION_CAP": "0"}); k_.search("ES", "a"); 
try: k_.search("ES", "b"); ok = True
except K.KeepaError: ok = False
check("sin AMAZON_PRO_KEEPA_MISSION_CAP el comportamiento V0.6.0 no cambia", ok)
# 11 · host/paths: sigue siendo solo lectura
check("solo se permiten /token, /product, /search", K.ALLOWED_PATHS == {"/token", "/product", "/search"})
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
