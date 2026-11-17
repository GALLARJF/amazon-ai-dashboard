"""Caso piloto PHIVITAL MAGNESIO (V0.3). No inventa nada: la plantilla solo trae identidad del producto y valores marcados como NO DOCUMENTADOS.
Reglas: (1) cada coste usado necesita evidencia+fecha (costDocs); (2) sin costes documentados la decisión nunca es GO;
(3) no hay demanda ni ventas por defecto: keywords/competidores/stock se aportan por el usuario."""
from . import engine as E

COST_KEYS = {
    "price": "PVP planificado (con IVA)", "vat": "IVA aplicable al producto", "cost": "Coste de producto puesto en almacén (fabricante)", "fulfil": "Logística FBA/FBM (tarifa o envío+embalaje)",
    "storage": "Almacenaje FBA (€/ud/mes y meses)", "returns": "Devoluciones (% y coste de gestión)", "referral": "Comisión de referencia de la categoría (tarifa vigente de Amazon)",
    "ads": "ACoS objetivo y su base (informe de Ads o decisión documentada)",
}


def template():
    d = E.create_empty("suplemento", "FBA")
    d["product"].update(name="PhiVital Magnesio (120 cápsulas)", asin="B0F6KQP2WH", ownPackUnits=1, ownContent=120, contentUnit="cápsulas")
    d["econ"].update(price=17.99, vatPct=10, feeSchedule="personalizado", customReferralPct=15, customMinFee=0.3)
    for k in ("cost", "fbaFee", "storageMonthly", "storageMonths", "returnsPct", "returnProcessing", "acosTarget"):
        d["econ"][k] = None  # sin valores por defecto: el usuario debe introducir costes documentados
    d["costDocs"] = {k: {"evidence": "", "date": ""} for k in COST_KEYS}
    d["costDocs"]["price"] = {"evidence": "PVP observado en Amazon.es el 2026-10-08 (dato indicado por el usuario); PVP planificado a confirmar", "date": "2026-10-08"}
    d["pvpScenarios"] = [15.99, 17.99, 19.99]
    d["notes"] = ("Plantilla: valores económicos distintos de PVP e identidad del producto son PROVISIONALES y NO documentados. "
                  "Los costes vacíos deben introducirse con su evidencia; IVA 10 % y comisión 15 %/0,30 € son supuestos a confirmar (tarifas vigentes de Amazon y tipo de IVA de complementos).")
    return d


def missing_costs(d):
    docs = d.get("costDocs") or {}
    return [k for k in COST_KEYS if not (docs.get(k, {}).get("evidence") or "").strip() or not E._isdate((docs.get(k) or {}).get("date"))]


def assess(d, today):
    ev = E.evaluate(d, today)
    if "costDocs" not in d:
        ev["pilot"] = None
        return ev
    miss = missing_costs(d)
    ev["pilot"] = {"costs_documented": not miss, "missing_costs": [COST_KEYS[k] for k in miss], "provisional": bool(miss)}
    for k in miss:
        ev["findings"].append({"id": f"costdoc.{k}", "section": "price", "severity": "block", "title": f"Coste sin documentar: {COST_KEYS[k]}", "why": "Cada coste usado en la decisión necesita evidencia (factura, presupuesto, tarifa vigente) y fecha.", "fix": "Indica la referencia de evidencia y la fecha."})
    rank = {"nogo": 0, "block": 1, "warn": 2}
    ev["findings"].sort(key=lambda f: rank[f["severity"]])
    ev["counts"] = {s: sum(1 for f in ev["findings"] if f["severity"] == s) for s in ("nogo", "block", "warn")}
    if ev["decision"] == "GO" and miss:
        ev["decision"] = "REVISAR"
    if ev["decision"] == "NO-GO" and miss:  # una inviabilidad calculada con costes sin documentar es solo un indicio
        ev["decision"] = "REVISAR"
        ev["summary"] = "REVISAR: hay indicios de inviabilidad, pero se calculan con costes aún no documentados (no se emite NO-GO firme)."
    elif ev["decision"] == "REVISAR":
        ev["summary"] = f"{ev['counts']['block']} bloqueo(s) por resolver antes de lanzar."
    return ev


def derive_origin(d, requested):
    """USUARIO solo si el piloto tiene todos los costes documentados; con plantilla incompleta → INCOMPLETO."""
    if requested in ("DEMO", "PRUEBA"):
        return requested
    if "costDocs" in d and missing_costs(d):
        return "INCOMPLETO"
    return "USUARIO"
