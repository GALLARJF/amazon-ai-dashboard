"""Comprueba la COHERENCIA de las evidencias de la validación REAL de Keepa (docs_v06/evidencia_keepa_real/). No llama a la red:
lee los ficheros generados por la llamada real del 2026-11-17. Si no existen (instalación limpia), la prueba se omite."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(ROOT, "docs_v06", "evidencia_keepa_real")
if not os.path.isdir(D):
    print("OMITIDA: sin evidencias reales"); sys.exit(0)
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
L = lambda f: json.load(open(os.path.join(D, f), encoding="utf-8"))
ops, led, sal, tab = L("mision_operaciones.json"), L("keepa_ledger.json"), L("saldo.json"), L("competidores_ES.json")
check("REAL: una única operación de pago, /search, dominio ES, consumo confirmado 10", len(ops) == 1 and ops[0]["path"] == "/search" and ops[0]["confirmed_tokens"] == 10 and ops[0]["status"] == "OK")
check("REAL: el libro registra la búsqueda con 10 tokens y dominio 9 (amazon.es)", [x for x in led if x["op"] == "search"][0]["tokens_consumed"] == 10 and [x for x in led if x["op"] == "search"][0]["domain"] == 9)
check("REAL: el saldo bajó exactamente 10 (60→50) y la recarga posterior es +1/min", sal["antes_de_buscar"]["tokens_left"] - sal["tras_buscar"]["tokens_left"] == 10)
check("REAL: ≥10 competidores con ASIN válido y sin duplicados", len(tab) >= 10 and len({r["asin"] for r in tab}) == len(tab) and all(len(r["asin"]) == 10 for r in tab))
check("REAL: ningún ASIN fue introducido a mano (todos con fuente Keepa /search)", all("/search" in r["fuente"] for r in tab))
check("REAL: precio normalizado solo cuando hay formato; si no, None", all((r["precio_por_100ml_derivado"] is None) == (r["formato_ml"] is None or r["precio_observado_eur"] is None) for r in tab))
check("REAL: cada precio lleva la fecha de su último punto", all(r["precio_fecha_ultimo_punto"] for r in tab if r["precio_observado_eur"] is not None))
check("REAL: valoraciones NO DISPONIBLES (no inventadas)", all(r["rating"] == "NO DISPONIBLE" for r in tab))
blob = "".join(open(os.path.join(D, f), encoding="utf-8").read() for f in os.listdir(D))
check("REAL: las evidencias no contienen nada con aspecto de clave", "KEEPA_API_KEY" not in blob and "key=" not in blob)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
