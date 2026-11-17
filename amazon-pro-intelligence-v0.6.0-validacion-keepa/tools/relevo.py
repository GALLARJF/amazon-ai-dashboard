#!/usr/bin/env python3
"""Relevo de sesiones (gasto cero): recupera el estado del coordinador desde GitHub, ejecuta UN ciclo y publica el estado.

Las sesiones programadas arrancan aisladas (sin ficheros). El código viene de la rama de código y el ESTADO de una rama propia
(por defecto aht-autonomia-estado). Sin claves: usa el git ya configurado en la sesión. Nunca invoca Keepa ni APIs de pago.
Uso:  python3 tools/relevo.py [--sin-push]      Variables: AHT_REMOTE (URL), AHT_RAMA_ESTADO
"""
import os, subprocess, sys, json, shutil, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUT = os.path.join(ROOT, "AUTONOMIA")
REMOTE = os.environ.get("AHT_REMOTE", "https://github.com/GALLARJF/amazon-ai-dashboard")
RAMA = os.environ.get("AHT_RAMA_ESTADO", "aht-autonomia-estado")
FICHEROS = ("estado.json", "registro.jsonl", "limites.json")
GIT = ["git", "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com"]


def sh(args, cwd=None, ok=False):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=300)
    if p.returncode and not ok: raise RuntimeError("%s -> %s" % (" ".join(args[:3]), (p.stderr or p.stdout)[-300:]))
    return p


def coord(*a):
    env = dict(os.environ); env["AMAZON_PRO_KEEPA_ENABLE"] = "0"
    for k in [k for k in env if "KEEPA_KEY" in k or "API_KEY" in k]: env.pop(k)
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "coordinador.py")] + list(a), capture_output=True, text=True, env=env, cwd=ROOT, timeout=3000)


def main():
    push = "--sin-push" not in sys.argv; r = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "remoto": REMOTE, "rama_estado": RAMA}
    tmp = tempfile.mkdtemp(prefix="relevo_"); w = os.path.join(tmp, "estado")
    existe = sh(["git", "ls-remote", "--heads", REMOTE, RAMA], ok=True).stdout.strip()
    os.makedirs(AUT, exist_ok=True)
    if existe:
        sh(["git", "clone", "-q", "--branch", RAMA, "--single-branch", REMOTE, w])
        for f in FICHEROS:
            if os.path.exists(os.path.join(w, "AUTONOMIA", f)): shutil.copy(os.path.join(w, "AUTONOMIA", f), os.path.join(AUT, f))
        r["estado_recuperado"] = True; r["commit_estado_previo"] = sh(["git", "rev-parse", "--short", "HEAD"], cwd=w).stdout.strip()
    else:
        r["estado_recuperado"] = False  # primera sesión: el coordinador inicializa
        sh(["git", "init", "-q", "-b", RAMA, w]); sh(["git", "remote", "add", "origin", REMOTE], cwd=w)
    v = json.loads(coord("verificar").stdout or "{}"); r["registro_integro_al_llegar"] = v.get("ok"); r["lineas_registro_al_llegar"] = v.get("lineas")
    e0 = json.load(open(os.path.join(AUT, "estado.json"))) if os.path.exists(os.path.join(AUT, "estado.json")) else {"ciclos": []}
    r["ciclos_previos"] = len(e0.get("ciclos", []))
    c = coord("ciclo"); r["ciclo_stdout"] = c.stdout[-900:]; r["ciclo_rc"] = c.returncode
    e1 = json.load(open(os.path.join(AUT, "estado.json"))); v2 = json.loads(coord("verificar").stdout or "{}")
    r.update(ciclos_ahora=len(e1.get("ciclos", [])), ultimo_objetivo=(e1["ciclos"][-1]["objetivo"] if e1.get("ciclos") else None), registro_integro_al_salir=v2.get("ok"), lineas_registro_al_salir=v2.get("lineas"),
             pendientes=[o["id"] for o in e1["objetivos"] if o["estado"] == "PENDIENTE"])
    os.makedirs(os.path.join(w, "AUTONOMIA"), exist_ok=True)
    for f in FICHEROS:
        if os.path.exists(os.path.join(AUT, f)): shutil.copy(os.path.join(AUT, f), os.path.join(w, "AUTONOMIA", f))
    open(os.path.join(w, "LEEME.md"), "w").write("Estado del coordinador AHT (sin claves). Lo escribe tools/relevo.py. Una linea de registro por evento.\n")
    sh(["git", "add", "-f", "-A"], cwd=w)
    msg = "Relevo: ciclo %d objetivo=%s\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" % (r["ciclos_ahora"], r["ultimo_objetivo"])
    sh(GIT + ["commit", "-q", "-m", msg], cwd=w, ok=True)
    r["commit_estado"] = sh(["git", "rev-parse", "--short", "HEAD"], cwd=w).stdout.strip()
    if push:
        p = sh(["git", "push", "-q", "origin", RAMA], cwd=w, ok=True); r["push_ok"] = p.returncode == 0; r["push_error"] = None if p.returncode == 0 else p.stderr[-300:]
    else: r["push_ok"] = None
    print(json.dumps(r, ensure_ascii=False, indent=1)); return 0 if r.get("push_ok") is not False else 2


if __name__ == "__main__": sys.exit(main())
