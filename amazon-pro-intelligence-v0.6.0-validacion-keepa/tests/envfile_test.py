"""V0.3.3 — archivo local seguro para la clave: parseo (Windows/Notepad), no pisa el entorno, nunca imprime valores, ENABLE=0 => cero llamadas, scripts .bat, nada secreto en el proyecto."""
import glob, http.client, json, os, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import envfile as E, ai as AI
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
KEY = "sk-proj-CENTINELA-ENVFILE-77aa11bb22cc33dd-NO-REAL"
# parseo
txt = "﻿# comentario\r\nOPENAI_API_KEY = \"%s\"  \r\nAMAZON_PRO_AI_ENABLE=0 # nota\r\nPATH=/evil\r\nAMAZON_PRO_AI_PROVIDER=openai\r\nAMAZON_PRO_AI_MODEL=\r\nsin_igual\r\n" % KEY
p = E.parse(txt)
check("BOM de Notepad, CRLF, comillas, espacios y comentarios en línea", p == {"OPENAI_API_KEY": KEY, "AMAZON_PRO_AI_ENABLE": "0", "AMAZON_PRO_AI_PROVIDER": "openai"})
check("nombres no permitidos (PATH) y valores vacíos se ignoran", "PATH" not in p and "AMAZON_PRO_AI_MODEL" not in p)
check("el marcador PEGA_AQUI_TU_CLAVE cuenta como «sin clave»", E.parse("OPENAI_API_KEY=PEGA_AQUI_TU_CLAVE") == {})
env = {"AMAZON_PRO_AI_ENABLE": "1"}; d = tempfile.mkdtemp(); f = os.path.join(d, "ai.env"); open(f, "w", encoding="utf-8").write(txt)
info = E.load(f, env)
check("no pisa variables ya definidas en el entorno (gana el entorno)", env["AMAZON_PRO_AI_ENABLE"] == "1" and "AMAZON_PRO_AI_ENABLE" in info["names_already_set"] and env["OPENAI_API_KEY"] == KEY)
check("load() devuelve SOLO nombres, nunca valores", KEY not in json.dumps(info) and info["found"])
check("archivo inexistente → found=False sin error", E.load(os.path.join(d, "no.env"), {})["found"] is False)
check("ruta por defecto: carpeta del usuario, fuera del proyecto", E.default_path().endswith(os.path.join("AmazonPro", "ai.env")) and not E.default_path().startswith(ROOT))
check("forma de la clave: reconocible / con espacio / con comillas / corta", E.key_looks_valid(KEY) and not E.key_looks_valid(KEY + " x") and not E.key_looks_valid('"' + KEY) and not E.key_looks_valid("sk-123"))
st = AI.public_status(AI.config({"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": "sk-corta"}))
check("estado público: avisa de formato dudoso sin mostrar la clave", st["key_format_ok"] is False and "sk-corta" not in json.dumps(st))
# plantilla y scripts
tpl = open(os.path.join(ROOT, "config", "ai.env.plantilla"), encoding="utf-8").read()
check("plantilla: ENABLE=0, presupuesto mensual y tope por ejecución ya fijados, sin clave real", "AMAZON_PRO_AI_ENABLE=0" in tpl and "MONTHLY_BUDGET=2" in tpl and "MAX_COST=0.02" in tpl and E.parse(tpl).get("OPENAI_API_KEY") is None)
for b in ("CONFIGURAR_CLAVE.bat", "VERIFICAR_CONFIGURACION.bat", "INICIAR.bat"):
    raw = open(os.path.join(ROOT, b), "rb").read()
    check(f"{b}: ASCII puro y finales de línea de Windows (CRLF)", all(c < 128 for c in raw) and raw.count(b"\r\n") == raw.count(b"\n"))
cb = open(os.path.join(ROOT, "CONFIGURAR_CLAVE.bat")).read()
check("CONFIGURAR_CLAVE.bat crea el archivo en %USERPROFILE%\\AmazonPro fuera del proyecto y no pisa uno existente", r"%USERPROFILE%\AmazonPro" in cb and "if not exist \"%ARCHIVO%\" copy" in cb)
gi = open(os.path.join(ROOT, ".gitignore")).read()
check(".gitignore bloquea *.env, ai.env, data/ y bases de datos", all(x in gi for x in ("*.env", "ai.env", "data/", "*.db")))
check("ningún archivo del proyecto contiene una clave con forma sk-… (salvo centinelas de prueba)", not [p_ for p_ in glob.glob(ROOT + "/**/*", recursive=True) if os.path.isfile(p_) and not p_.endswith((".png", ".zip", ".db")) and "tests" not in p_ and __import__("re").search(r"sk-[A-Za-z0-9_-]{24,}", open(p_, "r", errors="ignore").read())])
# servidor real con archivo de configuración, ENABLE=0 → cero llamadas
HITS = []
class F(BaseHTTPRequestHandler):
    def do_POST(self): HITS.append(1); self.send_response(500); self.end_headers()
    def log_message(self, *a): pass
fs = ThreadingHTTPServer(("127.0.0.1", 0), F); threading.Thread(target=fs.serve_forever, daemon=True).start()
home = tempfile.mkdtemp(); os.makedirs(os.path.join(home, "AmazonPro"))
open(os.path.join(home, "AmazonPro", "ai.env"), "w", encoding="utf-8").write(f"﻿OPENAI_API_KEY={KEY}\r\nAMAZON_PRO_AI_ENABLE=0\r\nAMAZON_PRO_AI_PROVIDER=openai\r\nAMAZON_PRO_AI_MONTHLY_BUDGET=2\r\nAMAZON_PRO_AI_BASE_URL=http://127.0.0.1:{fs.server_address[1]}\r\nAMAZON_PRO_AI_ALLOW_LOOPBACK=1\r\n")
free = ThreadingHTTPServer(("127.0.0.1", 0), F); PORT = free.server_address[1]; free.server_close()
penv = {k: v for k, v in os.environ.items() if not k.startswith(("AMAZON_PRO", "OPENAI"))}
penv.update(HOME=home, USERPROFILE=home, AMAZON_PRO_DB=os.path.join(home, "t.db"), AMAZON_PRO_ADMIN_PASSWORD="admin-password-123", PYTHONDONTWRITEBYTECODE="1")
proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "server.py"), str(PORT)], env=penv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
for _ in range(60):
    try: http.client.HTTPConnection("127.0.0.1", PORT, timeout=1).request("GET", "/api/status"); break
    except OSError: time.sleep(0.2)
def req(m, path, body=None, ck=None, csrf=None):
    h = {"Host": f"127.0.0.1:{PORT}"}; 
    if ck: h["Cookie"] = "apisid=" + ck
    if csrf: h["X-CSRF-Token"] = csrf
    if body is not None: h["Content-Type"] = "application/json"
    c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=30); c.request(m, path, json.dumps(body) if body is not None else None, h); r = c.getresponse(); t = r.read().decode(); return r, t
r, t = req("POST", "/api/login", {"username": "admin", "password": "admin-password-123"}); ck = r.getheader("Set-Cookie").split("apisid=")[1].split(";")[0]; cs = json.loads(t)["csrf"]
r, t = req("GET", "/api/ai/status", ck=ck); stt = json.loads(t)
check("servidor lee la clave del archivo del usuario (key_present) pero con ENABLE=0 → DESHABILITADA", stt["key_present"] and not stt["can_call"] and "DESHABILITADA" in stt["status"])
r, t = req("GET", "/api/records?account=sintetico-primera-llamada&kind=dossier", ck=ck); did = json.loads(t)["records"][0]["id"]
r, t = req("POST", "/api/director/ask", {"account": "sintetico-primera-llamada", "dossier": did, "question": "resumen"}, ck, cs)
check("Director con clave cargada y ENABLE=0: respuesta determinista y CERO peticiones al proveedor", r.status == 200 and json.loads(t)["ai"]["mode"] == "SIN_IA" and not HITS)
time.sleep(0.3); proc.terminate(); out = proc.communicate(timeout=10)[0]
check("la salida del servidor muestra el archivo ENCONTRADO y los NOMBRES cargados, nunca la clave", "ENCONTRADO" in out and "OPENAI_API_KEY" in out and KEY not in out)
check("la clave del archivo no aparece en la BD ni en respuestas", KEY.encode() not in b"".join(open(x, "rb").read() for x in glob.glob(os.path.join(home, "t.db*"))) and KEY not in t)
pf = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "preflight_primera_llamada.py")], env=penv, capture_output=True, text=True, timeout=60, cwd=ROOT)
check("VERIFICAR (preflight) con la clave del archivo: dice DESHABILITADA, no imprime la clave, no hace red", pf.returncode == 0 and "DESHABILITADA" in pf.stdout and KEY not in pf.stdout + pf.stderr and "reconocible" in pf.stdout and not HITS)
f_ = sum(1 for _, c in R if not c); print(f"{len(R) - f_}/{len(R)} OK"); sys.exit(1 if f_ else 0)
