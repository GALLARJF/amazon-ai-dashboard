"""Relevo entre sesiones: bloqueo de concurrencia (compare-and-swap en git), recuperación de bloqueos caducados, liberación solo por el dueño,
commit controlado (rama permitida, sin secretos, sin force). Remoto simulado: repositorio bare local."""
import json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); bare = os.path.join(tmp, "remote.git"); subprocess.run(["git", "init", "-q", "--bare", bare], check=True)
def proj(name):
    d = os.path.join(tmp, name); shutil.copytree(ROOT, d, ignore=shutil.ignore_patterns("AUTONOMIA", "__pycache__", "data", "CAPTURAS_UI", ".git")); return d
def run(d, *a, env=None):
    e = dict(os.environ); e.update(AHT_REMOTE=bare, AHT_PROYECTO=d, **(env or {}))
    p = subprocess.run([sys.executable, os.path.join(d, "tools", "relevo.py")] + list(a), cwd=d, capture_output=True, text=True, env=e); 
    try: return p.returncode, json.loads(p.stdout)
    except ValueError: return p.returncode, {"raw": p.stdout[-300:], "err": p.stderr[-300:]}
A, B = proj("a"), proj("b")
rc, r = run(A, "--adquirir", "--id", "sesionA"); check("A adquiere el bloqueo (rama de estado inexistente: se crea)", rc == 0 and r["adquirido"] and r["id"] == "sesionA")
rc, r = run(B, "--adquirir", "--id", "sesionB"); check("B NO adquiere mientras A lo tiene (OCUPADO, código 3)", rc == 3 and not r["adquirido"] and r["motivo"] == "OCUPADO" and r["por"] == "sesionA")
rc, r = run(B, "--publicar", "--id", "sesionB", "--liberar", "-m", "intento ajeno"); check("B no puede liberar el bloqueo de A", r.get("liberado") is False)
rc, r = run(B, "--adquirir", "--id", "sesionB2"); check("sigue OCUPADO tras el intento ajeno", rc == 3)
rc, r = run(A, "--publicar", "--id", "sesionA", "--liberar", "-m", "fin A"); check("A publica el estado y libera", rc == 0 and r["push_ok"] and r["liberado"] is True)
rc, r = run(B, "--adquirir", "--id", "sesionB", "--ttl", "0"); check("tras liberar, B adquiere (con TTL 0 para la prueba de caducidad)", rc == 0 and r["adquirido"])
rc, r = run(A, "--adquirir", "--id", "sesionA2", "--ttl", "600"); check("bloqueo CADUCADO (sesión caída): A lo recupera y lo registra", rc == 0 and r["adquirido"] and r["recuperado_de"] == "sesionB")
rc, r = run(A, "--publicar", "--id", "sesionA2", "--liberar", "-m", "fin"); check("liberación limpia", r["liberado"] is True)
# carrera: dos adquisiciones casi simultáneas -> exactamente una gana
import threading; out = {}
def go(n, d): out[n] = run(d, "--adquirir", "--id", n)
ts = [threading.Thread(target=go, args=(n, d)) for n, d in (("rA", A), ("rB", B))]; [t.start() for t in ts]; [t.join() for t in ts]
check("carrera simultánea: exactamente UNA sesión adquiere (%s)" % {k: v[0] for k, v in out.items()}, sorted(v[0] for v in out.values()) == [0, 3])
# commit controlado
g = os.path.join(tmp, "g"); subprocess.run(["git", "clone", "-q", bare, g], check=True, capture_output=True) if False else None
w = os.path.join(tmp, "w"); os.makedirs(w); subprocess.run(["git", "init", "-q", "-b", "main", w], check=True); 
for f in ("tools",): shutil.copytree(os.path.join(ROOT, f), os.path.join(w, f))
os.makedirs(os.path.join(w, "AUTONOMIA")); subprocess.run(["git", "-C", w, "remote", "add", "origin", bare]); open(os.path.join(w, "a.txt"), "w").write("x"); subprocess.run(["git", "-C", w, "add", "-A"]); subprocess.run(["git", "-C", w, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base"], check=True)
rc, r = run(w, "--commit", "-m", "x", "--rama", "aht-v100-desarrollo"); check("commit controlado: rechaza si la rama actual no es la permitida (main)", rc != 0 and "rama" in json.dumps(r).lower())
subprocess.run(["git", "-C", w, "checkout", "-q", "-b", "aht-v100-desarrollo"]); open(os.path.join(w, "k.txt"), "w").write("KEEPA_API_" + "KEY=abcdefghijklmnopqrstuvwxyz0123456789ZZ")
rc, r = run(w, "--commit", "-m", "x", "--rama", "aht-v100-desarrollo"); check("commit controlado: rechaza si hay un secreto en el árbol", rc != 0 and "secreto" in json.dumps(r).lower() and subprocess.run(["git", "-C", w, "log", "--oneline"], capture_output=True, text=True).stdout.count("\n") == 1)
os.remove(os.path.join(w, "k.txt")); open(os.path.join(w, "b.txt"), "w").write("cambio"); rc, r = run(w, "--commit", "-m", "cambio valido", "--rama", "aht-v100-desarrollo"); check("commit controlado: limpio → commit + push sin force", rc == 0 and r["push_ok"] and len(r["commit"]) >= 7)
heads = subprocess.run(["git", "ls-remote", "--heads", bare], capture_output=True, text=True).stdout; msg = subprocess.run(["git", "-C", w, "log", "-1", "--format=%B"], capture_output=True, text=True).stdout; check("la rama remota existe y el commit lleva la atribución", "refs/heads/aht-v100-desarrollo" in heads and "Co-Authored-By" in msg)
src = open(os.path.join(ROOT, "tools", "relevo.py"), encoding="utf-8").read(); check("el código nunca usa --force", "--force" not in src.replace('"--force" not in', "") and "push\", \"-f" not in src)
shutil.rmtree(tmp, ignore_errors=True); print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
