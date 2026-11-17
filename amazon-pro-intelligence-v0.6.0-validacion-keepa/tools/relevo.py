#!/usr/bin/env python3
"""Relevo de sesiones (gasto cero): recupera el estado del coordinador desde GitHub, ejecuta UN ciclo y publica el estado.

Las sesiones programadas arrancan aisladas (sin ficheros). El código viene de la rama de código y el ESTADO de una rama propia
(por defecto aht-autonomia-estado). Sin claves: usa el git ya configurado en la sesión. Nunca invoca Keepa ni APIs de pago.
Uso:  python3 tools/relevo.py [--sin-push]          recupera estado, ejecuta UN ciclo del coordinador y publica el estado
      python3 tools/relevo.py --recuperar         (sesión de desarrollo) solo recupera el estado
      python3 tools/relevo.py --publicar [-m txt]  (sesión de desarrollo) publica el estado tras desarrollar
      python3 tools/relevo.py --adquirir --id X [--ttl s]   bloqueo de concurrencia (código 3 = ocupado)
      python3 tools/relevo.py --publicar --id X --liberar    publica estado y libera SOLO si el bloqueo es tuyo
      python3 tools/relevo.py --commit -m txt [--rama R]     commit controlado (rama permitida, sin secretos, sin force)
Variables: AHT_REMOTE (URL), AHT_RAMA_ESTADO
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


def publicar(msg, sid=None, liberar=False):
    """Publica AUTONOMIA/ en la rama de estado (clon limpio + superposición; un reintento si otra sesión se adelantó)."""
    for intento in (1, 2):
        w = os.path.join(tempfile.mkdtemp(prefix="pub_"), "e")
        if sh(["git", "ls-remote", "--heads", REMOTE, RAMA], ok=True).stdout.strip(): sh(["git", "clone", "-q", "--branch", RAMA, "--single-branch", REMOTE, w])
        else: sh(["git", "init", "-q", "-b", RAMA, w]); sh(["git", "remote", "add", "origin", REMOTE], cwd=w)
        os.makedirs(os.path.join(w, "AUTONOMIA"), exist_ok=True)
        for f in FICHEROS:
            if os.path.exists(os.path.join(AUT, f)): shutil.copy(os.path.join(AUT, f), os.path.join(w, "AUTONOMIA", f))
        lib = None
        if liberar:
            lp = os.path.join(w, "AUTONOMIA", LOCK); d = json.load(open(lp)) if os.path.exists(lp) else None
            if d and d.get("id") == sid: os.remove(lp); lib = True
            else: lib = False  # solo el dueño libera
        sh(["git", "add", "-f", "-A"], cwd=w); sh(GIT + ["commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"], cwd=w, ok=True)
        p = sh(["git", "push", "-q", "origin", RAMA], cwd=w, ok=True)
        if p.returncode == 0: return {"push_ok": True, "commit_estado": sh(["git", "rev-parse", "--short", "HEAD"], cwd=w).stdout.strip(), "intento": intento, "liberado": lib}
    return {"push_ok": False, "push_error": p.stderr[-300:], "liberado": None}


LOCK = "sesion.lock"


def adquirir(sid, ttl):
    """Bloqueo de concurrencia: un fichero en la rama de estado. El push es compare-and-swap: si otra sesión se adelantó, git lo rechaza y NO se adquiere.
    Un bloqueo caducado (sesión caída) se recupera y queda registrado."""
    w = os.path.join(tempfile.mkdtemp(prefix="lock_"), "e")
    if sh(["git", "ls-remote", "--heads", REMOTE, RAMA], ok=True).stdout.strip(): sh(["git", "clone", "-q", "--branch", RAMA, "--single-branch", REMOTE, w])
    else: sh(["git", "init", "-q", "-b", RAMA, w]); sh(["git", "remote", "add", "origin", REMOTE], cwd=w)
    os.makedirs(os.path.join(w, "AUTONOMIA"), exist_ok=True); lp = os.path.join(w, "AUTONOMIA", LOCK); prev = None
    if os.path.exists(lp):
        d = json.load(open(lp)); edad = time.time() - d["t"]
        if edad < d["ttl"]: return {"adquirido": False, "motivo": "OCUPADO", "por": d["id"], "edad_s": int(edad), "ttl_s": d["ttl"]}
        prev = d["id"]
    json.dump({"id": sid, "t": time.time(), "ttl": ttl, "recuperado_de": prev}, open(lp, "w"))
    sh(["git", "add", "-f", "-A"], cwd=w); sh(GIT + ["commit", "-q", "-m", "Bloqueo de sesion %s%s" % (sid, " (recupera caducado de %s)" % prev if prev else "")], cwd=w, ok=True)
    p = sh(["git", "push", "-q", "origin", RAMA], cwd=w, ok=True)
    if p.returncode: return {"adquirido": False, "motivo": "OCUPADO", "por": "otra sesión (carrera perdida)", "detalle": p.stderr[-120:]}
    return {"adquirido": True, "id": sid, "ttl_s": ttl, "recuperado_de": prev}


SECRETO = __import__("re").compile(r"(KEEPA_API_KEY|OPENAI_API_KEY|api[_-]?key|secret|token)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{24,})['\"]?", __import__("re").I)
OKFALSO = __import__("re").compile(r"CENTINELA|FALS[OA]|FAKE|EJEMPLO|MOCK|DEMO|DUMMY|PLACEHOLDER", __import__("re").I)


def commit_seguro(msg, rama):
    """Commit controlado: solo en la rama permitida, nunca con secretos en el árbol, push SIN force (si falla, no se fuerza)."""
    actual = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT).stdout.strip()
    if actual != rama: return {"error": "rama no permitida: estás en %r y solo se commitea en %r" % (actual, rama)}, 2
    hall = []
    for r, ds, fs in os.walk(ROOT):
        ds[:] = [d for d in ds if d not in {".git", "__pycache__", "node_modules", "CAPTURAS_UI", "data", "AUTONOMIA"}]
        for f in fs:
            if f.endswith((".png", ".zip", ".db", ".pyc")): continue
            try: t = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
            except OSError: continue
            for m in SECRETO.finditer(t):
                if not OKFALSO.search(t[max(0, m.start() - 80):m.end() + 80]) and "PEGA_AQUI" not in m.group(0): hall.append(os.path.relpath(os.path.join(r, f), ROOT))
    if hall: return {"error": "posible secreto en el árbol: %s. No se commitea." % ", ".join(sorted(set(hall))[:5])}, 2
    sh(["git", "add", "-A"], cwd=ROOT)
    c = sh(GIT + ["commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"], cwd=ROOT, ok=True)
    if c.returncode and "nothing to commit" not in (c.stdout + c.stderr): return {"error": "commit fallido: " + (c.stderr or c.stdout)[-200:]}, 2
    p = sh(["git", "push", "-q", "origin", rama], cwd=ROOT, ok=True)
    return {"push_ok": p.returncode == 0, "commit": sh(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT).stdout.strip(), "push_error": None if p.returncode == 0 else p.stderr[-300:]}, (0 if p.returncode == 0 else 2)


def recuperar():
    w = os.path.join(tempfile.mkdtemp(prefix="rec_"), "e"); os.makedirs(AUT, exist_ok=True)
    if not sh(["git", "ls-remote", "--heads", REMOTE, RAMA], ok=True).stdout.strip(): return {"estado_recuperado": False}
    sh(["git", "clone", "-q", "--branch", RAMA, "--single-branch", REMOTE, w])
    for f in FICHEROS:
        if os.path.exists(os.path.join(w, "AUTONOMIA", f)): shutil.copy(os.path.join(w, "AUTONOMIA", f), os.path.join(AUT, f))
    v = json.loads(coord("verificar").stdout or "{}")
    return {"estado_recuperado": True, "commit_estado": sh(["git", "rev-parse", "--short", "HEAD"], cwd=w).stdout.strip(), "registro_integro": v.get("ok"), "lineas_registro": v.get("lineas")}


def main():
    if "--recuperar" in sys.argv: print(json.dumps(recuperar(), ensure_ascii=False, indent=1)); return 0
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    if "--adquirir" in sys.argv:
        r = adquirir(arg("--id", "sesion-%d" % os.getpid()), int(arg("--ttl", "5400"))); print(json.dumps(r, ensure_ascii=False, indent=1)); return 0 if r["adquirido"] else 3
    if "--commit" in sys.argv:
        r, rc = commit_seguro(arg("-m", "cambio"), arg("--rama", "aht-v100-desarrollo")); print(json.dumps(r, ensure_ascii=False, indent=1)); return rc
    if "--publicar" in sys.argv:
        r = publicar(arg("-m", "Estado tras sesion de desarrollo"), arg("--id"), "--liberar" in sys.argv); print(json.dumps(r, ensure_ascii=False, indent=1)); return 0 if r["push_ok"] else 2
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
