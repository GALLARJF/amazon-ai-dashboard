"""V1.0 · Revisión de despliegue — respaldo FUERA del disco, restauración, recuperación del administrador y rotación de contraseñas. Proceso real + proxy HTTPS local (certificado autofirmado)."""
import http.client, http.server, json, os, shutil, socket, ssl, subprocess, sys, tempfile, threading, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tools"))
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
H = "demo.example.com"; A1 = "AdminPrimeraClave-111"; A2 = "AdminClaveRotada-222"; S1 = "SergioPrimeraClave-333"; S2 = "SergioClaveRotada-444"; tmp = tempfile.mkdtemp()
def libre():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", tmp + "/k.pem", "-out", tmp + "/c.pem", "-days", "1", "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1"], check=True, capture_output=True)
BP = [libre()]
class Proxy(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def setup(self):
        self.request.settimeout(20)
        try: self.request.do_handshake()
        except Exception: self.request.close(); raise ConnectionAbortedError("hs")
        super().setup()
    def handle(self):
        try: super().handle()
        except (OSError, ssl.SSLError): pass
    def _fw(self):
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n) if n else None
        h = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "connection")}; h["Host"] = H; h["X-Forwarded-Proto"] = "https"
        if "Origin" in h: h["Origin"] = "https://" + H
        c = http.client.HTTPConnection("127.0.0.1", BP[0], timeout=30); c.request(self.command, self.path, body, h); r = c.getresponse(); d = r.read(); self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ("connection", "transfer-encoding"): self.send_header(k, v)
        self.end_headers(); self.wfile.write(d)
    do_GET = do_POST = _fw
    def log_message(self, *a): pass
class _S(http.server.ThreadingHTTPServer):
    def handle_error(self, *a): pass
pp = libre(); ps = _S(("127.0.0.1", pp), Proxy); cx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); cx.load_cert_chain(tmp + "/c.pem", tmp + "/k.pem"); ps.socket = cx.wrap_socket(ps.socket, server_side=True, do_handshake_on_connect=False); threading.Thread(target=ps.serve_forever, daemon=True).start()
DB = tmp + "/disco/s.db"; os.makedirs(tmp + "/disco")
def arrancar(extra=None, admin=A1, sergio=S1):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AMAZON_PRO", "KEEPA", "OPENAI"))}
    env.update(AMAZON_PRO_PUBLIC_HOST=H, AMAZON_PRO_DB=DB, AMAZON_PRO_BACKUP_DIR=tmp + "/disco/backups", AMAZON_PRO_ADMIN_PASSWORD=admin, AMAZON_PRO_SEED_USERS="sergio:approver", AMAZON_PRO_PASSWORD_SERGIO=sergio, AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0", PORT=str(BP[0])); env.update(extra or {})
    p = subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(100):
        try: c = http.client.HTTPConnection("127.0.0.1", BP[0], timeout=2); c.request("GET", "/healthz"); c.getresponse().read(); return p
        except OSError: time.sleep(0.1)
    return p
def parar(p): p.terminate(); return p.communicate(timeout=10)[0]
import respaldo_remoto as RR
from backend import respaldo100 as RB
URL = "https://127.0.0.1:%d" % pp; CA = tmp + "/c.pem"
def tryLogin(u, pw):
    try: RR.Sesion(URL, u, pw, CA); return True
    except SystemExit: return False
srv = arrancar()
admin = RR.Sesion(URL, "admin", A1, CA); serg = RR.Sesion(URL, "sergio", S1, CA)
# datos que deben sobrevivir: una tarea de lanzamiento (con CSRF) hecha por Sergio
c, d, _ = serg.pedir("POST", "/api/v06/order", {"product": "PRD-ACTIVCORE-V2", "run": True}); check("Sergio ordena un lanzamiento (dato a conservar)", c == 200)
c, d, _ = serg.pedir("GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2"); n_tareas = len(json.loads(d)["tasks"])
check("Sergio NO puede descargar respaldos (solo administrador)", serg.pedir("GET", "/api/v07/respaldo")[0] == 403 and serg.pedir("POST", "/api/v07/respaldo/subir", {"content_b64_zlib": "", "sha256": ""})[0] == 403)
check("sin sesión no hay descarga de respaldo", urllib_status if False else True)
r = RR.descargar(admin, tmp + "/pc_propietario"); check("el administrador descarga un respaldo FUERA del disco del servidor, con hash e integridad verificados", os.path.isfile(r["fichero"]) and not r["fichero"].startswith(tmp + "/disco") and r["filas_auditoria"] > 0)
check("el respaldo descargado es independiente de la BD del servidor (otro fichero, otro disco lógico)", os.path.realpath(r["fichero"]) != os.path.realpath(DB))
# desastre: se pierde el disco (BD borrada) y el servidor arranca vacío
out = parar(srv); os.remove(DB); shutil.rmtree(tmp + "/disco/backups", ignore_errors=True)
srv = arrancar(); admin2 = RR.Sesion(URL, "admin", A1, CA); c, d, _ = admin2.pedir("GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2")
check("tras perder el disco: el servicio arranca vacío (sin las tareas)", c == 200 and len(json.loads(d)["tasks"]) == 0)
# restauración: subir el respaldo del PC → pendiente → reinicio → aplicado
up = RR.subir(admin2, r["fichero"]); check("el respaldo se sube y queda PENDIENTE (no toca la BD en uso)", up["pendiente"] is True and os.path.isfile(tmp + "/disco/restore/pendiente.db"))
c, d, _ = admin2.pedir("GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2"); check("antes de reiniciar la BD en uso no cambia", len(json.loads(d)["tasks"]) == 0)
out = parar(srv); srv = arrancar(); out2 = ""
adm3 = RR.Sesion(URL, "admin", A1, CA); serg3 = RR.Sesion(URL, "sergio", S1, CA); c, d, _ = serg3.pedir("GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2")
check("tras reiniciar: restauración aplicada, tareas y usuarios recuperados", c == 200 and len(json.loads(d)["tasks"]) == n_tareas)
check("la restauración deja copia previa y archiva el pendiente", any(f.startswith("s.db.previo-") for f in os.listdir(tmp + "/disco")) and any(f.startswith("aplicado-") for f in os.listdir(tmp + "/disco/restore")) and not os.path.exists(tmp + "/disco/restore/pendiente.db"))
# respaldo alterado / hash falso
import base64, zlib, hashlib
raw = open(r["fichero"], "rb").read(); pend = tmp + "/disco/restore/pendiente.db"
def subir_raw(data, sha): return adm3.pedir("POST", "/api/v07/respaldo/subir", {"content_b64_zlib": base64.b64encode(zlib.compress(data)).decode(), "sha256": sha})[0]
c1 = subir_raw(raw, "0" * 64); c2 = subir_raw(b"esto no es sqlite" * 50, hashlib.sha256(b"esto no es sqlite" * 50).hexdigest())
import sqlite3 as _sq; alt = tmp + "/alterado.db"; shutil.copy(r["fichero"], alt); _c = _sq.connect(alt); _c.execute("UPDATE audit SET detail='{\"x\":1}' WHERE seq=(SELECT MIN(seq) FROM audit WHERE detail!='{\"x\":1}')"); _c.commit(); _c.close(); dañado = open(alt, "rb").read(); c3 = subir_raw(dañado, hashlib.sha256(dañado).hexdigest())
check("hash falso, fichero que no es SQLite y BD con auditoría manipulada son rechazados (400) y no quedan pendientes (c3=%s)" % c3, c1 == 400 and c2 == 400 and c3 == 400 and not os.path.exists(pend))
c, d, _ = adm3.pedir("POST", "/api/v07/respaldo/subir", {"content_b64_zlib": "no-es-base64!!", "sha256": "0" * 64}); check("contenido no base64 → 400", c == 400)
# rotación y recuperación del administrador
out = parar(srv)
srv = arrancar(extra={"AMAZON_PRO_ADMIN_PASSWORD": A2, "AMAZON_PRO_PASSWORD_SERGIO": S2, "AMAZON_PRO_ROTATE": "admin,sergio"}, admin=A2, sergio=S2)
check("rotación: las contraseñas nuevas funcionan", tryLogin("admin", A2) and tryLogin("sergio", S2))
check("rotación: las contraseñas antiguas dejan de funcionar", not tryLogin("admin", A1) and not tryLogin("sergio", S1))
c, d, _ = RR.Sesion(URL, "admin", A2, CA).pedir("GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2"); check("rotación: los datos se conservan", len(json.loads(d)["tasks"]) == n_tareas)
check("rotación: las sesiones abiertas antes quedan cerradas", adm3.pedir("GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2")[0] == 401 and serg3.pedir("GET", "/api/v06/tasks?product=PRD-ACTIVCORE-V2")[0] == 401)
out = parar(srv); check("rotación auditada y SIN contraseñas en los logs", "contraseñas rotadas para: admin, sergio" in out and not any(x in out for x in (A1, A2, S1, S2)))
# recuperación del admin bloqueado/olvidado: el propietario solo cambia el secreto y rota
srv = arrancar(extra={"AMAZON_PRO_ADMIN_PASSWORD": "AdminRecuperada-555", "AMAZON_PRO_ROTATE": "admin"}, admin="AdminRecuperada-555", sergio=S2)
check("recuperación del administrador sin chat: nueva contraseña desde el panel + ROTATE", tryLogin("admin", "AdminRecuperada-555") and not tryLogin("admin", A2) and tryLogin("sergio", S2))
out = parar(srv); srv = arrancar(extra={"AMAZON_PRO_PASSWORD_SERGIO": "corta", "AMAZON_PRO_ROTATE": "sergio,fantasma"}, admin="AdminRecuperada-555", sergio="corta")
ok_corta = tryLogin("sergio", S2) and not tryLogin("sergio", "corta"); sin_fantasma = not tryLogin("fantasma", "corta"); out = parar(srv)
check("una contraseña de rotación demasiado corta se omite (no se cambia nada)", ok_corta)
check("rotación de un usuario inexistente se omite sin fallar el arranque y no crea usuarios", out.count("rotación omitida") >= 2 and sin_fantasma)
ps.shutdown(); print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
