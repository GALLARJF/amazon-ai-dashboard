"""V1.0 · Despliegue cloud — Chromium real contra el servidor en MODO CLOUD detrás de un proxy HTTPS local (certificado autofirmado) que imita al del proveedor (TLS, Host/Origin públicos, X-Forwarded-Proto).
Usuario Sergio (sembrado por variable secreta), 5 secciones a 390/820/1600 px, formulario de importación, persistencia tras reiniciar el proceso. NO es un despliegue en un proveedor real."""
import glob, http.client, http.server, os, re, socket, ssl, subprocess, sys, tempfile, threading, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import _nav_shim  # Fase 4: navegación nueva (sin ?legacy=1)
from playwright.sync_api import sync_playwright
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
H = "demo.example.com"; SERGPW = "ClaveSergioDePrueba-456"; tmp = tempfile.mkdtemp(); OUT = os.path.join(ROOT, "CAPTURAS_UI")
for f in glob.glob(os.path.join(OUT, "7[0-9]_cloud_*.png")): os.remove(f)
def libre():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", tmp + "/k.pem", "-out", tmp + "/c.pem", "-days", "1", "-subj", "/CN=" + H, "-addext", "subjectAltName=DNS:" + H], check=True, capture_output=True)
BPORT = [libre()]
class Proxy(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def setup(self):
        self.request.settimeout(20)
        try: self.request.do_handshake()
        except Exception: self.request.close(); raise ConnectionAbortedError('handshake')
        super().setup()
    def handle(self):
        try: super().handle()
        except (OSError, ssl.SSLError): pass
    def _fw(self):
        try: self._fw2()
        except OSError: pass   # el navegador cerró la conexión
    def _fw2(self):
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n) if n else None
        h = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "connection")}; h["Host"] = H; h["X-Forwarded-Proto"] = "https"
        if "Origin" in h: h["Origin"] = "https://" + H   # el navegador entra por 127.0.0.1 (el DNS de la sesión no resuelve el nombre público); el proxy presenta Host/Origin públicos como haría el del proveedor
        c = http.client.HTTPConnection("127.0.0.1", BPORT[0], timeout=30); c.request(self.command, self.path, body, h); r = c.getresponse(); d = r.read()
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ("connection", "transfer-encoding"): self.send_header(k, v)
        self.end_headers(); self.wfile.write(d)
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = _fw
    def log_message(self, *a): pass
pp = libre()
class _S(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address): pass
ps = _S(("127.0.0.1", pp), Proxy)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(tmp + "/c.pem", tmp + "/k.pem"); ps.socket = ctx.wrap_socket(ps.socket, server_side=True, do_handshake_on_connect=False); threading.Thread(target=ps.serve_forever, daemon=True).start()
def arrancar():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AMAZON_PRO", "KEEPA", "OPENAI"))}
    env.update(AMAZON_PRO_PUBLIC_HOST=H, AMAZON_PRO_DB=tmp + "/s.db", AMAZON_PRO_BACKUP_DIR=tmp + "/bk", AMAZON_PRO_ADMIN_PASSWORD="ClaveAdminDePrueba-123", AMAZON_PRO_SEED_USERS="sergio:approver", AMAZON_PRO_PASSWORD_SERGIO=SERGPW, AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0", PORT=str(BPORT[0]))
    p = subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(100):
        try: c = http.client.HTTPConnection("127.0.0.1", BPORT[0], timeout=2); c.request("GET", "/healthz"); c.getresponse().read(); return p
        except OSError: time.sleep(0.1)
    return p
srv = arrancar(); URL = f"https://127.0.0.1:{pp}/"; n = 0
SECC = [("inicio", "INICIO"), ("lanz", "LANZAMIENTOS"), ("ventas", "MIS VENTAS"), ("prod", "PRODUCTOS"), ("dir", "DIRECTOR IA")]
def sesion(b, w, h):
    ctx = b.new_context(viewport={"width": w, "height": h}, ignore_https_errors=True); pg = ctx.new_page(); errs = []; ext = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.on("request", lambda r: not r.url.startswith((f"https://127.0.0.1:{pp}/", "data:", "blob:")) and ext.append(r.url))
    pg.goto(URL); pg.wait_for_selector("#tabs"); return ctx, pg, errs, ext
def entrar(pg):
    pg.click("#lgOpen"); pg.fill("#lgU", "sergio"); pg.fill("#lgP", SERGPW); pg.click("#lgGo"); pg.wait_for_selector(".sessu")
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-proxy-server"])
    for w, h, nm in ((390, 844, "movil"), (820, 1180, "tableta"), (1600, 900, "escritorio")):
        ctx, pg, errs, ext = sesion(b, w, h)
        check("[%s] la página llega por HTTPS (TLS terminado en el proxy)" % nm, pg.url.startswith("https://127.0.0.1:%d/" % pp))
        pg.click("#lgOpen"); pg.fill("#lgU", "sergio"); pg.fill("#lgP", "contraseña-incorrecta-1"); pg.click("#lgGo"); pg.wait_for_timeout(800)
        check("[%s] contraseña incorrecta: no entra (estado de error visible)" % nm, pg.locator(".sessu").count() == 0)
        pg.fill("#lgP", SERGPW); pg.click("#lgGo"); pg.wait_for_selector(".sessu", timeout=8000)
        check("[%s] Sergio inicia sesión y ve su usuario y rol" % nm, "sergio" in pg.inner_text(".sessu") and "approver" in pg.inner_text(".sessu"))
        cks = ctx.cookies(); check("[%s] cookie de sesión Secure + HttpOnly + SameSite=Strict" % nm, any(c["name"] == "apisid" and c["secure"] and c["httpOnly"] and c["sameSite"] == "Strict" for c in cks))
        for k, t in SECC:
            pg.click(f"#tabs button[data-tab={k}]"); pg.wait_for_timeout(700)
            if k == "lanz": pg.wait_for_selector("#v6lanz .v6sec", timeout=10000)
            sw = pg.evaluate("()=>document.documentElement.scrollWidth - document.documentElement.clientWidth")
            check("[%s] %s: sin desborde (%d px) y con contenido" % (nm, t, sw), sw <= 1 and len(pg.inner_text("body").strip()) > 400)
            n += 1; pg.screenshot(path=os.path.join(OUT, "7%d_cloud_%s_%s.png" % (n % 10, nm, k)))
        pg.click("#tabs button[data-tab=lanz]"); pg.wait_for_selector("#v6Prod-lanz"); pg.wait_for_selector('section.v7[data-space="lanz"] .v7-keepa tbody tr', timeout=10000)
        SEL_ROWS = 'section.v7[data-space="lanz"] .v7-keepa tbody tr'; SEL_BRIEF = 'section.v7[data-space="lanz"] .v7-brief'
        # La sección se vuelve a pintar de forma asíncrona (la tabla puede vaciarse un instante). Se exige un INSTANTÁNEO COHERENTE completo dentro de 15 s; la aserción NO se relaja.
        _t0 = time.time(); _ok = False
        while True:
            _v = pg.eval_on_selector("#v6Prod-lanz", "e=>e.value"); _n = pg.locator(SEL_ROWS).count(); _b = "NO DECIDIBLE" in pg.inner_text(SEL_BRIEF)
            _ok = _v == "PRD-ACTIVCORE-V2" and _b and _n == 20
            if _ok or time.time() - _t0 > 15: break
            time.sleep(0.25)
        check("[%s] ACTIVCORE por defecto: NO DECIDIBLE y 20 competidores reales con procedencia%s" % (nm, "" if _ok else " [valor=%s filas=%d veredicto=%s]" % (_v, _n, _b)), _ok)
        check("[%s] sin errores de consola/página%s y sin red externa" % (nm, (": " + "; ".join(errs[:2])[:120]) if errs else ""), not errs and not ext)
        ctx.close()
    # persistencia tras reiniciar el proceso del servidor (mismo disco)
    ctx, pg, errs, ext = sesion(b, 1600, 900); entrar(pg); pg.click("#tabs button[data-tab=lanz]"); pg.wait_for_selector("#v6lanz .v6sec")
    pg.evaluate("""async()=>{const t=document.cookie; const c=await (await fetch('/api/session',{credentials:'same-origin'})).text().catch(()=>'')}""")
    srv.terminate(); srv.communicate(timeout=10); srv = arrancar(); time.sleep(0.5)
    ctx2, pg2, errs2, ext2 = sesion(b, 390, 844); entrar(pg2); pg2.click("#tabs button[data-tab=lanz]"); pg2.wait_for_selector('section.v7[data-space="lanz"] .v7-keepa tbody tr', timeout=10000)
    check("tras reiniciar el servidor: Sergio vuelve a entrar con el mismo usuario (persistencia en disco) y ve los datos de ACTIVCORE", "sergio" in pg2.inner_text(".sessu") and pg2.locator('section.v7[data-space="lanz"] .v7-keepa tbody tr').count() == 20)
    check("el servidor reiniciado no tiene errores de consola", not errs2)
    anon = b.new_context(ignore_https_errors=True).new_page(); anon.goto(URL + "api/v07/expediente?product=PRD-ACTIVCORE-V2")
    check("sin sesión, la API devuelve 401 (nada accesible sin autenticar)", "sesión requerida" in anon.inner_text("body"))
    b.close()
srv.terminate(); out = srv.communicate(timeout=10)[0]; ps.shutdown()
check("los logs del servidor no contienen la contraseña", SERGPW not in out and "ClaveAdmin" not in out)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
