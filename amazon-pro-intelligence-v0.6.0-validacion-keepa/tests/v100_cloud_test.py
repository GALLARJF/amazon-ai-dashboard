"""V1.0 · Despliegue cloud — modo cloud del servidor (proceso real, Host/HTTPS del proxy simulados), usuarios sembrados por variables secretas, respaldo automático, y paquete de despliegue sin secretos.
NO prueba un despliegue real en un proveedor ni la construcción de la imagen Docker (no hay demonio Docker en esta sesión)."""
import http.client, json, os, re, socket, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
H = "demo.example.com"; ADMINPW = "ClaveAdminDePrueba-123"; SERGPW = "ClaveSergioDePrueba-456"
def libre():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
def arrancar(tmp, extra=None, port=None):
    port = port or libre(); env = {k: v for k, v in os.environ.items() if not k.startswith(("AMAZON_PRO", "KEEPA", "OPENAI"))}
    env.update(AMAZON_PRO_PUBLIC_HOST=H, AMAZON_PRO_DB=os.path.join(tmp, "s.db"), AMAZON_PRO_BACKUP_DIR=os.path.join(tmp, "bk"), AMAZON_PRO_ADMIN_PASSWORD=ADMINPW, AMAZON_PRO_SEED_USERS="sergio:approver,corto:analyst,jefe:admin",
               AMAZON_PRO_PASSWORD_SERGIO=SERGPW, AMAZON_PRO_PASSWORD_CORTO="corta", AMAZON_PRO_PASSWORD_JEFE="UnaClaveLargaDeJefe-1", AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0", PORT=str(port)); env.update(extra or {})
    p = subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(100):
        try:
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=2); c.request("GET", "/healthz"); c.getresponse().read(); return p, port
        except OSError: time.sleep(0.1)
    return p, port
def req(port, m, path, body=None, host=H, proto="https", cookie=None, csrf=None, origin=None):
    h = {"Host": host, "X-Forwarded-Proto": proto, "Content-Type": "application/json"}
    if cookie: h["Cookie"] = cookie
    if csrf: h["X-CSRF-Token"] = csrf
    if origin: h["Origin"] = origin
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=20); c.request(m, path, json.dumps(body) if body is not None else None, h); r = c.getresponse(); d = r.read().decode(); return r.status, d, dict(r.getheaders())
def login(port, u, pw):
    c, d, h = req(port, "POST", "/api/login", {"username": u, "password": pw}); return c, (json.loads(d) if c == 200 else {}), h
tmp = tempfile.mkdtemp(); p, port = arrancar(tmp)
c, d, h = req(port, "GET", "/healthz", host="cualquiera.interno"); check("/healthz responde 200 sin datos (comprobación de salud del proveedor)", c == 200 and json.loads(d) == {"ok": True})
check("Host distinto del público → 403 (anti DNS rebinding)", req(port, "GET", "/api/status", host="evil.example.org")[0] == 403)
check("sin HTTPS en el proxy (X-Forwarded-Proto=http) → 403", req(port, "GET", "/api/status", proto="http")[0] == 403)
check("Origin ajeno → 403", req(port, "POST", "/api/login", {"username": "admin", "password": ADMINPW}, origin="https://evil.example.org")[0] == 403)
check("sin sesión: API → 401 (nada público sin autenticación)", req(port, "GET", "/api/v07/expediente?product=PRD-ACTIVCORE-V2")[0] == 401 and req(port, "GET", "/api/v06/home")[0] == 401)
c, ses, h = login(port, "admin", ADMINPW); ck = h.get("Set-Cookie", "")
check("admin entra con la contraseña de la variable secreta", c == 200 and ses.get("role") == "admin")
check("cookie HttpOnly + Secure + SameSite=Strict y cabecera HSTS", all(x in ck for x in ("HttpOnly", "Secure", "SameSite=Strict")) and "max-age" in h.get("Strict-Transport-Security", ""))
check("contraseña incorrecta rechazada", login(port, "admin", "incorrecta-123456")[0] in (401, 403))
c, ss, h2 = login(port, "sergio", SERGPW); check("Sergio (sembrado por variable secreta) entra con rol approver", c == 200 and ss.get("role") == "approver")
check("usuario con contraseña corta NO se crea", login(port, "corto", "corta")[0] != 200)
check("nunca se crean administradores por la vía de siembra", login(port, "jefe", "UnaClaveLargaDeJefe-1")[0] != 200)
cs = h2["Set-Cookie"].split(";")[0]
c, d, _ = req(port, "GET", "/api/v07/expediente?product=PRD-ACTIVCORE-V2", cookie=cs); ex = json.loads(d) if c == 200 else {}
check("ACTIVCORE: expediente NO DECIDIBLE con 20 competidores reales de Keepa conservados", c == 200 and ex.get("verdict") == "NO DECIDIBLE")
c, d, _ = req(port, "GET", "/api/v07/keepa-real?product=PRD-ACTIVCORE-V2", cookie=cs); kr = json.loads(d); check("datos reales de Keepa presentes (0 tokens, 0 llamadas)", kr["state"] == "REAL" and len(kr["competitors"]) == 20 and kr["tokens_spent_now"] == 0)
c, d, _ = req(port, "GET", "/api/v06/connections", cookie=cs); cn = {r["name"]: r for r in json.loads(d)["rows"]}
check("conexiones: SP-API y Ads API PENDIENTE DE CONEXIÓN (no afirmadas); OpenAI sin verificar; Keepa sin consumo ahora", cn["Amazon SP-API"]["state"] == "PENDIENTE DE CONEXIÓN" and cn["Amazon Ads API"]["state"] == "PENDIENTE DE CONEXIÓN" and cn["OpenAI / IA"]["real_verified"] is False and cn["Keepa"]["real_calls_logged"] == 0)
c, d, _ = req(port, "GET", "/api/v06/ai/calls", cookie=cs); check("Sergio no accede a funciones de administrador (rol)", c in (401, 403))
c, d, _ = req(port, "POST", "/api/v06/order", {"product": "PRD-ACTIVCORE-V2", "run": True}, cookie=cs, csrf=ss["csrf"]); check("Sergio (approver) puede ordenar un lanzamiento con CSRF", c == 200)
time.sleep(1); bk = os.path.join(tmp, "bk"); fs = [f for f in os.listdir(bk)] if os.path.isdir(bk) else []
check("respaldo automático creado al arrancar, con hash", any(f.endswith(".db") for f in fs) and any(f.endswith(".sha256") for f in fs))
sys.path.insert(0, ROOT); from backend import respaldo100 as RB
check("el respaldo automático verifica íntegro", any(RB.verificar(os.path.join(bk, f))["ok"] for f in fs if f.endswith(".db")))
p.terminate(); out = p.communicate(timeout=10)[0]
check("los logs no contienen contraseñas ni cookies", ADMINPW not in out and SERGPW not in out and "apisid" not in out and "UnaClave" not in out)
check("los logs registran accesos (diagnóstico) y el usuario sembrado", "usuarios creados desde variables secretas: sergio" in out and "GET /healthz" in out)
p, port = arrancar(tmp); c, ses2, _ = login(port, "sergio", SERGPW)
c3, ss3, h3 = login(port, "sergio", SERGPW); cs3 = h3["Set-Cookie"].split(";")[0]; c4, d4, _ = req(port, "GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2", cookie=cs3)
check("tras reiniciar el proceso: usuarios y tareas persisten en el disco", c3 == 200 and c4 == 200 and len(json.loads(d4)["tasks"]) >= 1)
p.terminate(); p.communicate(timeout=10)
e = subprocess.run([sys.executable, "server.py"], cwd=ROOT, env={k: v for k, v in os.environ.items() if not k.startswith("AMAZON_PRO")} | {"AMAZON_PRO_PUBLIC_HOST": H, "AMAZON_PRO_DB": os.path.join(tmp, "x.db")}, capture_output=True, text=True, timeout=20)
check("modo cloud sin AMAZON_PRO_ADMIN_PASSWORD: no arranca y lo explica", e.returncode != 0 and "AMAZON_PRO_ADMIN_PASSWORD" in (e.stdout + e.stderr))
# paquete de despliegue
rd = lambda f: open(os.path.join(ROOT, f), encoding="utf-8").read()
y, dk, di = rd("render.yaml"), rd("Dockerfile"), rd(".dockerignore")
check("render.yaml: plan starter, disco persistente, healthcheck y rama", "plan: starter" in y and "mountPath: /data" in y and "healthCheckPath: /healthz" in y and "branch: aht-v100-desarrollo" in y)
rr = open(os.path.join(ROOT, "..", "render.yaml"), encoding="utf-8").read() if os.path.exists(os.path.join(ROOT, "..", "render.yaml")) else None
check("render.yaml de la raíz del repositorio = el del proyecto + rootDir (si existe la raíz del repo)", rr is None or rr.replace("    rootDir: amazon-pro-intelligence-v0.6.0-validacion-keepa   # la app vive en este subdirectorio del repositorio\n", "") == y)
check("render.yaml: secretos con sync:false y ningún valor de contraseña", all(re.search(k + r"\s*#?[^\n]*\n\s*sync: false", y) for k in ("AMAZON_PRO_ADMIN_PASSWORD", "AMAZON_PRO_PASSWORD_SERGIO")) and not re.search(r"(?i)PASSWORD[A-Z_]*\s*\n\s*value:", y))
check("render.yaml: IA y Keepa desactivadas por defecto", re.search(r'AMAZON_PRO_KEEPA_ENABLE\s*\n\s*value: "0"', y) and re.search(r'AMAZON_PRO_AI_ENABLE\s*\n\s*value: "0"', y))
check("Dockerfile: usuario no root, sin COPY de claves ni ENV de secretos", "USER app" in dk and not re.search(r"(?i)(KEY|PASSWORD|SECRET|TOKEN)\s*=", dk))
check(".dockerignore excluye datos, estado autónomo, .env y .git", all(x in di for x in ("data/", "AUTONOMIA/", "*.env", ".git/")))
check("sin cadenas con aspecto de clave en el paquete de despliegue", not re.search(r"[A-Za-z0-9]{32,}", y + dk + di))
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
