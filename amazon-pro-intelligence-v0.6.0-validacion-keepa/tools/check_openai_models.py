"""Comprueba, SIN generar tokens (GET /v1/models, sin coste de inferencia), qué IDs de modelo ve TU cuenta. No se ejecuta en pruebas ni automáticamente.
Uso:  OPENAI_API_KEY=... python3 tools/check_openai_models.py --yes     (la clave solo se lee del entorno; no se imprime)"""
import json, os, sys, urllib.request
if "--yes" not in sys.argv:
    sys.exit("Añade --yes para confirmar que quieres hacer UNA petición GET real a api.openai.com/v1/models.")
k = os.environ.get("OPENAI_API_KEY")
if not k:
    sys.exit("Falta OPENAI_API_KEY en el entorno.")
req = urllib.request.Request("https://api.openai.com/v1/models", headers={"Authorization": "Bearer " + k})
ids = {m["id"] for m in json.load(urllib.request.urlopen(req, timeout=30)).get("data", [])}
for m in ("gpt-6-luna", "gpt-6.1-terra", "gpt-6.1-sol", "gpt-6-astra"):
    print(("DISPONIBLE   " if m in ids else "NO DISPONIBLE ") + m)
