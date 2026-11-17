"""V0.3.2 — IDs, tarifas y niveles de razonamiento configurados == instantánea de la documentación oficial (docs/oficial_snapshot_2026-11-16.json)."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
snap = json.load(open(os.path.join(ROOT, "docs", "oficial_snapshot_2026-11-16.json")))
check("misma fecha de verificación en código e instantánea", AI.PRICE_VERIFIED_ON == snap["verificado"])
check("mismos IDs de modelo (tabla de precios)", set(AI.PRICES) == set(snap["modelos"]) and set(AI.MODEL_EFFORTS) == set(snap["modelos"]))
for m, v in snap["modelos"].items():
    check(f"{m}: entrada/caché/salida iguales a la documentación", AI.PRICES[m] == (v["in"], v["cached"], v["out"]))
    check(f"{m}: niveles de razonamiento iguales a la documentación", list(AI.MODEL_EFFORTS[m]) == v["razonamiento"])
check("perfiles apuntan a IDs documentados", all(m in snap["modelos"] for m in AI.PROFILES.values()))
check("esfuerzo por defecto 'low' válido en los 4 modelos", all("low" in v for v in AI.MODEL_EFFORTS.values()))
e = {"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": "k", "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "1", "AMAZON_PRO_AI_PROFILE": "razonamiento", "AMAZON_PRO_AI_REASONING": "none"}
try: AI.complete(AI.config(e), "s", "u"); check("none en gpt-6.1-sol se rechaza", False)
except AI.AIError as ex: check("«none» en gpt-6.1-sol (no documentado) → REASONING_NO_SOPORTADO antes de llamar", ex.code == "REASONING_NO_SOPORTADO")
check("antigüedad de tarifas calculada (aviso si >45 días)", AI.prices_age_days("2026-11-16") == 0 and AI.prices_age_days("2027-01-15") == 60)
check("estado público informa fecha de verificación", AI.public_status(AI.config({"AMAZON_PRO_AI_PROVIDER": "openai"}))["prices_verified_on"] == "2026-11-16")
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
