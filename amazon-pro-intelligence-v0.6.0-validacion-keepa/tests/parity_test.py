"""Paridad JS(V0.2) ↔ Python(V0.3): mismos resultados económicos y de decisión en N casos pseudoaleatorios con semilla fija."""
import json, os, random, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend import engine as E

TODAY = "2026-11-16"
rnd = random.Random(20261116)


def rand_econ():
    return {"price": round(rnd.uniform(3, 90), 2), "vatPct": rnd.choice([0, 4, 10, 21]), "feeSchedule": rnd.choice(["generico_15", "belleza_8_15", "tramos_marginales", "personalizado"]),
            "customReferralPct": rnd.choice([5, 8, 15, 20]), "customMinFee": rnd.choice([0, 0.3]), "cost": round(rnd.uniform(0, 30), 2), "prep": round(rnd.uniform(0, 1), 2),
            "fulfilMode": rnd.choice(["FBA", "FBM"]), "fbaFee": round(rnd.uniform(1, 8), 2), "fbmShipping": round(rnd.uniform(1, 6), 2), "fbmPackaging": 0.4, "fbmHandling": 0.3,
            "storageMonthly": rnd.choice([0, 0.15, 0.4]), "storageMonths": rnd.choice([0, 1, 3]), "returnsPct": rnd.choice([0, 3, 8]), "returnProcessing": 1.5, "unsellablePct": rnd.choice([0, 30, 100]),
            "otherCosts": rnd.choice([0, 0.5]), "acosTarget": rnd.choice([0, 10, 25, 40, 60]), "adsBasis": rnd.choice(["gross", "net"]), "minMarginPct": rnd.choice([0, 10, 15, 30])}


def rand_dossier():
    d = E.create_empty(rnd.choice(["cosmetico", "suplemento", "otro"]), rnd.choice(["FBA", "FBM"]))
    d["econ"] = {**E.DEFAULTS, **rand_econ()}
    for i in range(rnd.randint(0, 7)):
        ago = rnd.choice([1, 5, 20, 29, 31, 60])
        import datetime
        dt = (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=ago)).isoformat()
        d["competitors"].append({"name": f"C{i}", "asin": f"A{rnd.randint(0, 5)}", "priceGross": round(rnd.uniform(5, 60), 2), "shipping": rnd.choice([0, 3, None]), "packUnits": rnd.choice([1, 2]),
                                 "contentValue": rnd.choice([60, 100, 120]), "source": rnd.choice(["Keepa", "", "Manual"]), "date": dt})
    for i in range(rnd.randint(0, 8)):
        d["keywords"].append({"keyword": f"kw{i}", "volume": rnd.randint(0, 9000), "source": "H10", "date": f"2026-{rnd.choice(['09', '10', '11'])}-{rnd.choice(['01', '10'])}"})
    for sec in (d["regulatory"], d["content"], d["logistics"]["items"]):
        for it in sec.values():
            it["status"] = rnd.choice(["pendiente", "cumplido", "no_aplica"]); it["evidence"] = rnd.choice(["", "doc"])
    d["claims"] = [{"text": "claim", "evidence": rnd.choice(["", "estudio"])}] if rnd.random() < .4 else []
    d["logistics"].update({"stockAvailable": rnd.choice([None, 0, 200, 900]), "forecastUnitsMonth": rnd.choice([None, 0, 300]), "leadTimeDays": rnd.choice([None, 30, 70]), "coverTargetDays": 45})
    return d


econ_cases = [{"input": rand_econ(), "price": None} for _ in range(400)]
econ_cases += [{"input": {**rand_econ(), "price": p}, "price": p} for p in (-1, 0, 0.0, 10.0, 10.01, 100.0, 100.5)]
for c in econ_cases:
    c["input"] = {k: v for k, v in c["input"].items()}
dossiers = [rand_dossier() for _ in range(250)]
ref = json.loads(subprocess.run(["node", os.path.join(ROOT, "tests", "parity_node.js")], input=json.dumps({"econ": econ_cases, "dossier": dossiers, "today": TODAY}), capture_output=True, text=True, check=True).stdout)

bad = 0
def close(a, b): return (a is None and b is None) or (a is not None and b is not None and abs(a - b) < 1e-7)
for c, r in zip(econ_cases, ref["econ"]):
    u = E.unit(c["input"], c["price"]); mp = E.min_price(c["input"])
    ok = u["valid"] == r["valid"]
    if ok and u["valid"]:
        ok = close(u["contribution"], r["contribution"]) and close(u["net"], r["net"]) and close(u["referral"], r["referral"]) and close(u["breakEvenAcos"], r["be"])
    ok = ok and close(mp["commercial"] if mp else None, r["mp"])
    if not ok:
        bad += 1; print("DIFF econ", c["input"], u.get("contribution"), r)
for d, r in zip(dossiers, ref["dossier"]):
    res = E.evaluate(d, TODAY); ids = [f["id"] + "|" + f["severity"] for f in res["findings"]]
    if res["decision"] != r["decision"] or sorted(ids) != sorted(r["ids"]) or res["counts"] != r["counts"]:
        bad += 1; print("DIFF dossier", res["decision"], r["decision"], set(ids) ^ set(r["ids"]))
n = len(econ_cases) + len(dossiers)
print(f"paridad JS↔Python: {n - bad}/{n} casos idénticos")
sys.exit(1 if bad else 0)
