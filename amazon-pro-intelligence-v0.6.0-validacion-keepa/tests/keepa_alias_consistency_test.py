"""Consistencia del alias KEEPA_KEY frente a KEEPA_API_KEY (status, configuración y guardia de staging). SOLO CARACTERIZA el comportamiento actual: no habilita
el alias ni cambia el servidor. Cada caso corre en un subproceso con entorno MÍNIMO (sin variables heredadas) y secretos FALSOS; sin red.
HALLAZGO documentado en docs/p0_hoy/REGRESION_Y_AUDITORIA_POST_4_2_1.md §2 (propuesta, no aplicada)."""
import json, os, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SECRET = "FAKESECRET_alias_7c1e"
R = []
def check(n, c, extra=""): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n + ((" → " + extra) if (extra and not c) else ""))
CHILD = r'''
import json, os, sys
sys.path.insert(0, %r)
import server
from backend import keepa
st = [c for c in server.status()["connectors"] if c["id"] == "keepa"][0]
cfg = keepa.config(os.environ)
print(json.dumps({"guard": server.staging_guard(), "missing": st["missing"], "testable": st["testable"], "status": st["status"], "enabled": st["enabled"],
                  "cfg_has_key": bool(cfg["key"]), "cfg_key_is_api": cfg["key"] == os.environ.get("KEEPA_API_KEY", "").strip() and bool(cfg["key"]),
                  "cfg_mode": cfg["mode"], "cfg_enabled": cfg["enabled"], "status_json_leaks": %r in json.dumps(server.status())}))
''' % (ROOT, SECRET)
def run(extra, staging=False):
    env = {"PATH": os.environ.get("PATH", ""), "HOME": "/nonexistent-home", "AMAZON_PRO_CONNECTORS": "keepa", **extra}
    if staging: env["AMAZON_PRO_STAGING"] = "1"
    p = subprocess.run([sys.executable, "-I", "-c", CHILD], env=env, capture_output=True, text=True, timeout=60, cwd=ROOT)
    out = p.stdout.strip().splitlines()
    return p.returncode, (json.loads(out[-1]) if out and out[-1].startswith("{") else None), p.stdout + p.stderr
# 1. solo alias legado: status NO lo reconoce (falta KEEPA_API_KEY), no es probable; la configuración SÍ lo lee (incoherencia caracterizada)
rc, d, raw = run({"KEEPA_KEY": SECRET})
check("[alias solo] status: falta KEEPA_API_KEY, conector no probable, «SIN CREDENCIALES»", rc == 0 and d and d["missing"] == ["KEEPA_API_KEY"] and d["testable"] is False and "SIN CREDENCIALES" in d["status"], raw[-200:])
check("[alias solo] configuración (backend.keepa) SÍ lee el alias → incoherencia status/configuración (hallazgo)", d and d["cfg_has_key"] is True)
check("[alias solo] modo Keepa sigue APAGADO por defecto (sin AMAZON_PRO_KEEPA_ENABLE no hay operaciones)", d and d["cfg_mode"] == "0" and d["cfg_enabled"] is False)
check("[alias solo] el secreto no aparece en el JSON de status ni en la salida", d and d["status_json_leaks"] is False and SECRET not in raw)
# 2. nombre canónico: reconocido por status y configuración
rc, d, raw = run({"KEEPA_API_KEY": SECRET})
check("[canónica] status: sin faltantes y conector probable", rc == 0 and d and d["missing"] == [] and d["testable"] is True)
check("[canónica] configuración lee la clave canónica", d and d["cfg_key_is_api"] is True)
check("[canónica] el secreto no se filtra", d and d["status_json_leaks"] is False and SECRET not in raw)
# 3. ambas: gana la canónica
rc, d, raw = run({"KEEPA_API_KEY": SECRET, "KEEPA_KEY": "FAKESECRET_otro"})
check("[ambas] gana KEEPA_API_KEY en la configuración", d and d["cfg_key_is_api"] is True)
# 4. guardia de staging
rc, d, raw = run({"KEEPA_API_KEY": SECRET}, staging=True)
check("[staging + canónica] NO arranca (la guardia la prohíbe) y solo nombra la variable, nunca el valor", rc != 0 and "KEEPA_API_KEY" in raw and SECRET not in raw, raw[-200:])
rc, d, raw = run({"KEEPA_KEY": SECRET}, staging=True)
check("[staging + alias] HALLAZGO: la guardia NO detecta KEEPA_KEY (arranca)", rc == 0 and d and d["guard"] == [])
check("[staging + alias] mitigado: la guardia fuerza Keepa APAGADO (mode 0, enabled False) → sin operaciones", d and d["cfg_mode"] == "0" and d["cfg_enabled"] is False)
check("[staging + alias] el secreto no se filtra", d and d["status_json_leaks"] is False and SECRET not in raw)
rc, d, raw = run({}, staging=True)
check("[staging limpio] arranca, guardia vacía y Keepa apagado", rc == 0 and d and d["guard"] == [] and d["cfg_mode"] == "0" and not d["cfg_has_key"])
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
