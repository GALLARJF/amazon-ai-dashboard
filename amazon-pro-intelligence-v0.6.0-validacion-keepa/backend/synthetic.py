"""Expediente SINTÉTICO único para la primera ejecución real de IA (V0.3.2).
100 % ficticio: ningún dato de PhiVital, de Amazon ni de ninguna persona. Vive en su propia cuenta, sin titular real ni marketplaces.
Mientras no exista una ejecución REAL verificada, el Director solo enviará a OpenAI ESTE expediente, y solo si no se ha modificado (huella SHA-256)."""
import datetime, hashlib, json
from . import pilot as P

ACCOUNT_ID = "sintetico-primera-llamada"
NAME = "SINTÉTICO · PRUEBA API"


def fixture(today=None):
    t = datetime.date.fromisoformat(today) if today else datetime.date.today(); ago = lambda n: (t - datetime.timedelta(days=n)).isoformat()
    d = P.template(); d["product"]["name"] = "Magnesio SINTÉTICO (ficticio)"
    d["econ"].update(price=19.9, cost=3.0, fbaFee=3.2, acosTarget=18, vatPct=10, feeSchedule="generico_15", storageMonthly=0.1, storageMonths=2, returnsPct=3, returnProcessing=1.5)
    for k in d["costDocs"]: d["costDocs"][k] = {"evidence": "SINTÉTICO ficticio " + k, "date": ago(5)}
    d["competitors"] = [{"name": f"Competidor {i}", "asin": f"SINT{i:04d}", "priceGross": p, "shipping": 0, "packUnits": 1, "contentValue": 120, "source": "SINTÉTICO", "date": ago(4), "rating": 4.4, "reviews": 200 * i} for i, p in enumerate([18.5, 21, 23.9, 26], 1)]
    d["keywords"] = [{"keyword": k, "volume": v, "source": "SINTÉTICO", "date": ago(10)} for k, v in [("magnesio", 9000), ("citrato de magnesio", 4000), ("magnesio sueño", 1500)]]
    for it in list(d["regulatory"].values()) + list(d["content"].values()) + list(d["logistics"]["items"].values()): it.update(status="cumplido", evidence="SINTÉTICO", date=ago(3))
    d["content"]["video"].update(status="pendiente", evidence="")  # un dato pendiente a propósito: la IA debe reflejar lo ausente, no inventarlo
    d["logistics"].update(stockAvailable=900, forecastUnitsMonth=300, leadTimeDays=30, coverTargetDays=45)
    d["listing"] = {"title": "Magnesio citrato de magnesio", "bullets": ["magnesio sueño"], "backend": ""}; d["cvrPct"] = 10; d["adBudgetMonth"] = 300
    return d


def digest(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def ensure(store, today=None):
    """Idempotente: crea la cuenta y el ÚNICO expediente sintético si no existen. Devuelve su id."""
    if not store.db.execute("SELECT 1 FROM accounts WHERE id=?", (ACCOUNT_ID,)).fetchone():
        store.create_account(ACCOUNT_ID, "Sintético · primera llamada real", "SINTÉTICO — sin titularidad real", None, [], actor="system")
    ex = store.list(ACCOUNT_ID, "dossier", limit=5)
    if ex:
        rec = ex[-1]
        if rec["data"].get("name") != NAME:  # renombra el expediente sintético de versiones anteriores (solo la etiqueta; el contenido y su huella no cambian)
            store.put(ACCOUNT_ID, "dossier", dict(rec["data"], name=NAME), id_=rec["id"], actor="system")
        return rec["id"]
    d = fixture(today)
    return store.put(ACCOUNT_ID, "dossier", {"origin": "PRUEBA", "synthetic": True, "name": NAME, "fixture_sha256": digest(d), "dossier": d}, actor="system")


def eligible(account_id, rec):
    """¿Puede este expediente salir hacia OpenAI antes de haber verificado la IA real? Solo el sintético, en su cuenta y sin alterar."""
    m = (rec or {}).get("data") or {}
    return bool(account_id == ACCOUNT_ID and m.get("synthetic") is True and m.get("origin") == "PRUEBA" and m.get("fixture_sha256") and digest(m.get("dossier")) == m["fixture_sha256"])
