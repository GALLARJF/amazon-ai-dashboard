"""V0.5.0 — lógica del lanzador (puerto, instancia única, errores, salida segura). Windows real NO verificable aquí."""
import os, socket, subprocess, sys, threading, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "tools"))
import lanzador as L
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
p = free_port(); a = L.elegir(p)
check("puerto libre → arrancar", a[0] == "arrancar" and a[1] == p)
busy = socket.socket(); busy.bind(("127.0.0.1", p)); busy.listen(1)
a = L.elegir(p)
check("puerto ocupado por otro programa → usa el siguiente y lo explica", a[0] == "arrancar" and a[1] != p and "ocupado" in a[2])
busy.close()
check("archivos de Windows presentes (icono, .ps1, .bat)", all(os.path.exists(os.path.join(ROOT, f)) for f in ["assets/aht_amazon_pro.ico", "tools/crear_acceso_directo.ps1", "CREAR_ACCESO_DIRECTO.bat", "INICIAR.bat"]))
ps = open(os.path.join(ROOT, "tools/crear_acceso_directo.ps1")).read()
check("el acceso directo se llama AHT Amazon Pro Intelligence y usa el icono propio", "AHT Amazon Pro Intelligence.lnk" in ps and "aht_amazon_pro.ico" in ps)
env = dict(os.environ, AMAZON_PRO_PORT=str(p))
proc = subprocess.Popen([sys.executable, "-c", "import sys;sys.path.insert(0,'tools');import lanzador as L;sys.exit(L.main(abrir_navegador=False))"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
t0 = time.time()
while time.time() - t0 < 20 and not L.es_nuestra(p): time.sleep(0.3)
check("el lanzador arranca el servidor y responde en 127.0.0.1", L.es_nuestra(p))
a = L.elegir(p)
check("segunda ejecución detecta la instancia y NO duplica", a[0] == "abrir" and a[1] == p)
proc.terminate()
try: proc.wait(timeout=10)
except subprocess.TimeoutExpired: proc.kill()
time.sleep(0.5)
check("salida limpia: el puerto queda libre", L.puerto_libre(p))
out = (proc.stdout.read() or b"").decode(errors="replace")
check("no se imprime ninguna clave", "sk-" not in out and "KEEPA_API_KEY" not in out)

# --- V0.6.1: regresión del bloqueo intermitente (SIGTERM temprano dejaba el servidor huérfano reteniendo la tubería) ---
import signal as _sg
def _early_term(delay):
    q = free_port(); e2 = dict(os.environ, AMAZON_PRO_PORT=str(q))
    pr = subprocess.Popen([sys.executable, "-c", "import sys;sys.path.insert(0,'tools');import lanzador as L;sys.exit(L.main(abrir_navegador=False))"], cwd=ROOT, env=e2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(delay); pr.send_signal(_sg.SIGTERM)
    try: pr.wait(timeout=15)
    except subprocess.TimeoutExpired: pr.kill()
    time.sleep(1.5); alive = not L.puerto_libre(q)
    if alive:  # limpieza de un posible huérfano (lo que ocurría antes de la corrección)
        import urllib.request
        os.system("pkill -f 'server.py %d'" % q)
    return alive
if hasattr(_sg, "SIGTERM") and os.name != "nt":
    orph = [_early_term(d) for d in (0.05, 0.3, 0.6, 1.0)]
    check("SIGTERM temprano (4 instantes de arranque): nunca queda un servidor huérfano", not any(orph))
else:
    print("OMITIDA en Windows (señales POSIX): la corrección de orden de señal NO está verificada en Windows")
bad = [n for n, c in R if not c]; print(f"{len(R)-len(bad)}/{len(R)} OK"); sys.exit(1 if bad else 0)
