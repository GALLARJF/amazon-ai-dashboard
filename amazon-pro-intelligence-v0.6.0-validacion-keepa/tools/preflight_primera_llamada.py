"""PREFLIGHT de la primera llamada real — NO hace ninguna petición de red ni gasta nada.
Muestra: estado de configuración (sin valores de clave), guardias, peor caso de coste, y el TEXTO EXACTO que saldría hacia OpenAI para el expediente sintético.
Uso: set -a; source ~/.amazon_pro_ai.env; set +a; python3 tools/preflight_primera_llamada.py"""
import datetime, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import ai as AI, director as D, synthetic as SY, envfile as ENVF
from backend.store import Store
AI._post = lambda *a, **k: (_ for _ in ()).throw(SystemExit("preflight: PROHIBIDO hacer red"))  # seguro por construcción
_ef = ENVF.load(); cfg = AI.config(); st = AI.public_status(cfg)
print("Archivo de configuración:", _ef["path"], "→", "ENCONTRADO" if _ef["found"] else "NO EXISTE (ejecuta CONFIGURAR_CLAVE.bat)")
s = Store(); did = SY.ensure(s); today = datetime.date.today().isoformat()
r = D.Director(s, lambda: cfg).analyze(SY.ACCOUNT_ID, did, "preflight", "resumen general", today=today, dry_run=True)
print("== PREFLIGHT PRIMERA LLAMADA REAL (sin red, sin gasto) ==")
print("Proveedor:", st["provider"], "| modelo:", st["model"], "| perfil:", st["profile"] or "economico (por defecto)", "| razonamiento:", cfg["reasoning_effort"])
print("Estado:", st["status"])
print("Clave presente:", "SÍ" if st["key_present"] else "NO", "· formato:", {True: "reconocible", False: "NO reconocible (¿espacios o comillas? debe empezar por sk-)", None: "—"}[st["key_format_ok"]], "(el valor nunca se muestra) | ENABLE:", "1" if st["enabled"] else "0")
print("Tarifas:", st["price_source"], "| verificadas el", st["prices_verified_on"], "| ¡CADUCADAS!" if st["prices_stale"] else "| vigentes")
print("Presupuestos: salida máx", cfg["max_output_tokens"], "| entrada máx", cfg["max_input_tokens"], "| por ejecución", cfg["max_cost_per_run"], "USD | mensual", cfg["monthly_budget"], "USD | simultáneas", cfg["max_concurrent"], "| timeout", cfg["timeout"], "s")
print("Expediente:", SY.NAME, "| elegible para la primera llamada:", SY.eligible(SY.ACCOUNT_ID, s.get(SY.ACCOUNT_ID, did)))
print("Decisión determinista:", r["decision"], "| coworkers:", ", ".join(r["plan"]))
print("Tokens de entrada estimados:", r["tokens_in_est"], "| coste PEOR CASO de esta llamada:", None if r["worst_case_cost"] is None else round(r["worst_case_cost"], 6), "USD")
print("Guardia:", r["guard"] or "ninguna (el sintético puede salir)")
ok = st["can_call"] and not r["guard"]
print("\n>>> LISTO PARA LLAMAR" if ok else "\n>>> NO se llamará todavía:", "" if ok else st["status"])
print("\n--- TEXTO EXACTO que se enviaría (instructions) ---\n" + r["system"] + "\n--- TEXTO EXACTO que se enviaría (input) ---\n" + r["user"])
