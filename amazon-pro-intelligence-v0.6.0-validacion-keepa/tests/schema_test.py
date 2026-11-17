"""Valida el paquete de ejemplo contra el esquema JSON formal (requiere jsonschema; si no está, el test falla en vez de saltarse)."""
import json, os, sys, jsonschema
R = os.path.join(os.path.dirname(__file__), "..")
sch = json.load(open(os.path.join(R, "schemas", "amazon-channel.schema.json"))); pkg = json.load(open(os.path.join(R, "tests", "paquete_ejemplo_DEMO.json")))
jsonschema.validate(pkg, sch); print("OK   paquete de ejemplo cumple el esquema")
assert pkg["ingest_allowed"] is False; print("OK   paquete DEMO con ingest_allowed=false")
for mut, name in [(lambda p: p["alerts"][0].__setitem__("severity", "x"), "severidad inválida"), (lambda p: p["channel_snapshots"][0].__setitem__("id", "mal"), "id inválido"), (lambda p: p.pop("ingest_allowed"), "falta ingest_allowed")]:
    b = json.loads(json.dumps(pkg)); mut(b)
    try: jsonschema.validate(b, sch); print("FAIL", name); sys.exit(1)
    except jsonschema.ValidationError: print("OK   esquema rechaza:", name)
