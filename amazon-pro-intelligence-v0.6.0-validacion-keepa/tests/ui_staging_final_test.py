"""CORRECCIÓN FINAL DE STAGING (sin funcionalidades nuevas). Staging real en proceso: auditor→viewer, admin y approver también sin escritura,
todas las escrituras → 403 (salvo login/logout), cero «PRODUCCIÓN» y cero «datos reales», controles de escritura desactivados en todas las pantallas
(incl. ?legacy=1), cero llamadas externas, P1 de presentación, capturas 1440/390/360 y Chrome Android emulado. Capturas: docs/p0_hoy/final_staging/<vp>/."""
import glob, json, os, re, socket, sys, tempfile, threading, urllib.request, urllib.error, http.cookiejar as CJ
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
for k in list(os.environ):
    if k.startswith("AMAZON_PRO_"): os.environ.pop(k)
PW = {"admin": "admin-pass-p9Zt4w", "auditor": "viewer-pass-x7Qk2m", "sergio": "approver-pass-m4Rt8z"}
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR=PW["auditor"], AMAZON_PRO_SEED_USERS="sergio:approver", AMAZON_PRO_PASSWORD_SERGIO=PW["sergio"])
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
EXT = []; _c = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(addr); raise AssertionError("RED PROHIBIDA")
    return _c(self, addr, *a, **k)
socket.socket.connect = _no_net
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "final_staging"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password=PW["admin"]); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "*", "*.png")): os.remove(f)
# ------------------------------------------------------------------ 1. servidor
def hreq(method, path, body=None, jar=None, csrf=""):
    rq = urllib.request.Request(f"http://localhost:{port}" + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf})
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)) if jar is not None else urllib.request.build_opener()
    try:
        with op.open(rq) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b"{}")
        except Exception: return e.code, {}
check("auditor inicia sesión con rol viewer (respuesta del servidor)", hreq("POST", "/api/login", {"username": "auditor", "password": PW["auditor"]}, CJ.CookieJar())[1].get("role") == "viewer")
WRITES = [("POST", "/api/v06/decide", {"id": 1, "approve": True}), ("POST", "/api/approvals/decide", {"account": "activcore-eu", "id": "x", "decision": "approve"}), ("POST", "/api/catalog/update", {"id": "PRD-ACTIVCORE-V2", "patch": {"name": "x"}}),
          ("POST", "/api/v06/order", {"product": "PRD-ACTIVCORE-V2"}), ("POST", "/api/connectors/test", {"name": "sp-api"}), ("POST", "/api/dossiers", {"name": "x"}), ("POST", "/api/ai/chat", {"q": "hola"}),
          ("POST", "/api/eu/analyze", {}), ("POST", "/api/k4/import", {"csv": "a"}), ("POST", "/api/competidores/import", {}), ("POST", "/api/inexistente", {}), ("PUT", "/api/catalog/update", {}), ("PATCH", "/api/catalog/update", {}), ("DELETE", "/api/dossiers/1", None)]
for user in ("admin", "sergio", "auditor"):
    jar = CJ.CookieJar(); c, j = hreq("POST", "/api/login", {"username": user, "password": PW[user]}, jar)
    check(f"[{user}] login permitido en staging (rol {j.get('role')})", c == 200 and j.get("role") == {"admin": "admin", "sergio": "approver", "auditor": "viewer"}[user])
    codes = [hreq(m, p, b, jar, j.get("csrf", ""))[0] for m, p, b in WRITES]
    check(f"[{user}] TODAS las escrituras (POST/PUT/PATCH/DELETE, con CSRF válido) → 403 {codes.count(403)}/{len(codes)}", all(x == 403 for x in codes))
    check(f"[{user}] la lectura sigue funcionando (GET /api/status → 200)", hreq("GET", "/api/status", None, jar)[0] == 200)
    check(f"[{user}] logout permitido", hreq("POST", "/api/logout", {}, jar, j.get("csrf", ""))[0] == 200)
# usuario auditor preexistente con rol admin → se fuerza a viewer al arrancar
import sqlite3
from backend.store import Store
tdb = os.path.join(tmp, "pre.db"); st0 = Store(tdb); st0.create_user("auditor", PW["auditor"], "admin", []); S.seed_viewers(st0)
check("un «auditor» preexistente con rol admin queda como viewer al sembrar (staging)", st0.db.execute("SELECT role FROM users WHERE username='auditor'").fetchone()[0] == "viewer")
# ------------------------------------------------------------------ 2. navegador
SUBS = [("hoy", 1), ("ventas", 2), ("prod", 4), ("lanz", 3), ("dir", 2), ("dec", 1), ("adm", 2)]
TXT = """()=>{const o=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const p=n.parentElement;if(!p||/^(SCRIPT|STYLE)$/.test(p.tagName))continue;o.push(n.nodeValue)}
 document.querySelectorAll('[title],[placeholder],[aria-label],option').forEach(e=>{o.push(e.title||'',e.placeholder||'',e.getAttribute('aria-label')||'')});return o.join('\\n')}"""
BAD = re.compile(r"PRODUCCI[ÓO]N|datos? reales?|\bdato real", re.I)
WRITE = r"(^\s*\+|guardar|crear|nuevo|nueva|aprobar|rechazar|lanzar|ejecutar|analizar|importar|publicar|activar|archivar|añadir|editar|enviar|proponer|investigar|reanudar|probar|confirmar|eliminar|borrar|registrar|validar|generar|iniciar|aplicar|actualizar|solicitar|reconciliar|fijar|descartar|marcar|verificar|subir|cargar|restaurar|respaldo|preguntar|medir|refrescar|restablecer|desactivar|pausar|detener|programar|asignar|sincronizar|vaciar|ejemplo|dossier|coworker|chat|aprobaci)"
CTRL = """(re)=>{const R=new RegExp(re,'i'),K='#lgOut,#lgOpen,#lgForm *,.ro-ok,[data-tab],#nav6 *,#bnav *,#subnav6 *,[data-k4v],[data-k4bv],[data-h2f],[data-h2go],[data-h2prod],[data-x4go],[data-x4open],a.btn,#dmode,summary,.chip[data-k4exp360],#legacy *';
 return [...document.querySelectorAll('button,input,textarea,label.btn')].filter(e=>(e.checkVisibility?e.checkVisibility():true)&&!e.disabled&&e.getAttribute('aria-disabled')!=='true'&&!e.matches(K)&&!e.closest('#tabs')&&!e.closest('#plLeft')&&(e.type==='file'||e.tagName==='TEXTAREA'||(e.tagName==='INPUT'&&/^(text|search|number|email|date)?$/.test(e.type)&&!e.closest('.k4xf,.eufil,.k4f,.filters,#lgForm'))||R.test(e.textContent||e.value||'')||(e.dataset&&e.dataset.act&&!/^(demo-on|demo-off|goto-lanz|open-chat|cancel)$/.test(e.dataset.act)))).map(e=>(e.id||e.tagName)+':'+((e.textContent||e.value||e.placeholder||'').trim().slice(0,40)))}"""
LOCAL = lambda u: u.startswith(f"http://localhost:{port}") or u.startswith("data:") or u.startswith("blob:")
def route(r):
    if LOCAL(r.request.url): r.continue_()
    else: EXT.append(r.request.url); r.abort()
ANDROID = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
def login(pg, user):
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", user); pg.fill("#lgP", PW[user]); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
def ctxpg(pw, vp, mobile, ua=None, device=None):
    kw = dict(p.devices[device]) if device else dict(viewport=vp, device_scale_factor=1, is_mobile=mobile, has_touch=mobile, **({"user_agent": ua} if ua else {}))
    ctx = pw.new_context(**kw); ctx.route("**/*", route); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); return pg, errs
def audit_screens(pg, name, user, shots, errs):
    T = f"[{name}/{user}]"; bad_txt = []; ctrl = []; hs = []; fic = []; n = 0
    pre = pg.evaluate(TXT); bad_txt += [("pre-login", m) for m in BAD.findall(pre)]
    for sec, cnt in SUBS:
        for i in range(cnt):
            pg.evaluate(f"NAV6.go('{sec}',{i})"); pg.wait_for_timeout(1400); n += 1
            if (sec, i) == ("lanz", 2) and pg.locator(".eucard[data-pid]").count(): pg.locator(".eucard[data-pid]").first.click(); pg.wait_for_selector(".euconc", timeout=15000); pg.wait_for_timeout(800)
            if sec == "adm" and i == 1: pg.wait_for_selector("#tab-panel.on", timeout=6000)
            bad_txt += [(f"{sec}{i}", m) for m in BAD.findall(pg.evaluate(TXT))]
            ctrl += [(f"{sec}{i}", c) for c in pg.evaluate(CTRL, WRITE)]
            m = pg.evaluate("[scrollX, document.documentElement.scrollWidth, document.documentElement.clientWidth]"); hs += [(f"{sec}{i}", m)] if (m[0] != 0 or m[1] > m[2] + 1) else []
            fic += [] if "DATOS FICTICIOS — NO REPRESENTAN RESULTADOS DE AHT" in pg.inner_text("#modeBar") else [f"{sec}{i}"]
            if shots: pg.evaluate("scrollTo(0,0)"); pg.screenshot(path=os.path.join(shots, f"{sec}_{i}.png"))
    check(f"{T} {n} pantallas: cero «PRODUCCIÓN» y cero «datos reales» (texto, atributos y opciones) {bad_txt[:2]}", n == 15 and not bad_txt)
    check(f"{T} {n} pantallas: ningún control de escritura activo {ctrl[:3]}", not ctrl)
    check(f"{T} marca «DATOS FICTICIOS — NO REPRESENTAN RESULTADOS DE AHT» visible en todas las pantallas {fic[:2]}", not fic)
    check(f"{T} sin desplazamiento horizontal de página {hs[:2]}", not hs)
    check(f"{T} sin errores de JavaScript {errs[:1]}", not errs)
with sync_playwright() as p:
    pw = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])
    for name, vp, mobile, ua in (("1440", {"width": 1440, "height": 900}, False, None), ("390", {"width": 390, "height": 844}, True, ANDROID), ("360", {"width": 360, "height": 740}, True, ANDROID)):
        d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
        for user in ("auditor", "admin"):
            pg, errs = ctxpg(pw, vp, mobile, ua); login(pg, user)
            check(f"[{name}] sesión visible «{user} · {'viewer' if user == 'auditor' else 'admin'}» (nunca admin para el auditor)", pg.inner_text(".sessu").strip() == f"{user} · {'viewer' if user == 'auditor' else 'admin'}")
            check(f"[{name}/{user}] banner permanente «STAGING · DATOS SINTÉTICOS · NO USAR PARA DECISIONES REALES»", "STAGING · DATOS SINTÉTICOS · NO USAR PARA DECISIONES REALES" in pg.inner_text("#envBanner"))
            audit_screens(pg, name, user, d if user == "auditor" else None, errs)
            if user == "auditor" and name in ("1440", "390"):
                T = f"[{name}]"
                # P1-6 / P1-7
                pg.evaluate("NAV6.go('ventas',0)"); pg.wait_for_timeout(700)
                check(f"{T} Panel DEMO ya no está en Ventas", pg.locator("#subnav6 [data-sub]", has_text="Panel DEMO").count() == 0)
                pg.evaluate("NAV6.go('adm',0)"); pg.wait_for_timeout(700)
                check(f"{T} Administración → «Laboratorio DEMO»", pg.locator("#subnav6 [data-sub]", has_text="Laboratorio DEMO").count() == 1)
                pg.click('#subnav6 [data-sub]:has-text("Laboratorio DEMO")'); pg.wait_for_selector("#tab-panel.on .ficticio", timeout=8000)
                check(f"{T} Laboratorio DEMO muestra el panel y la marca de datos ficticios", pg.locator("#tab-panel .ficticio").inner_text().strip() == "DATOS FICTICIOS — NO REPRESENTAN RESULTADOS DE AHT" and pg.locator("#tab-panel #kpis .kpi").count() >= 1)
                # P1-8 Pre-Launch agrupado
                pg.evaluate("NAV6.go('lanz',1)"); pg.wait_for_selector("#plRight .plarea", timeout=8000); pg.wait_for_timeout(500)
                g = pg.evaluate("[...document.querySelectorAll('#plRight .plarea summary')].map(e=>e.textContent.replace(/ \\(\\d+\\)/,'').trim())")
                check(f"{T} Pre-Launch: bloqueos agrupados por área {g}", len(g) >= 2 and all(x in ("Economía", "Mercado", "Regulatorio", "Contenido", "Logística") for x in g) and g == sorted(g, key=["Economía", "Mercado", "Regulatorio", "Contenido", "Logística"].index) and "Inviabilidad" not in pg.inner_text("#plRight"))
                # P1-9 Europa
                pg.evaluate("NAV6.go('lanz',2)"); pg.wait_for_timeout(1200)
                if pg.locator(".eucard[data-pid]").count() and not pg.locator(".euconc").count(): pg.locator(".eucard[data-pid]").first.click()
                pg.wait_for_selector(".euconc", timeout=15000); pg.wait_for_timeout(500)
                o = pg.evaluate("(()=>{const c=document.querySelector('.euconc'),k=document.querySelector('.euconc + .kpis');return {t:c.innerText,before:!!k}})()")
                check(f"{T} Europa: primero Conclusión, País, Confianza, Motivo y Datos faltantes (antes de los KPI)", o["before"] and all(x.lower() in o["t"].lower() for x in ("Conclusión", "País", "Confianza", "Motivo", "Datos faltantes")))
                # P1-10 Competencia
                pg.evaluate("NAV6.go('prod',2)"); pg.wait_for_selector(".k4tc", timeout=10000); pg.wait_for_timeout(500)
                o = pg.evaluate("({cards:[...document.querySelectorAll('.k4tc')].filter(e=>e.checkVisibility()).length,tabvis:[...document.querySelectorAll('table.k4cmp')].filter(e=>e.checkVisibility()).length,inEvi:!!document.querySelector('#k4evi table.k4cmp'),open:document.querySelector('#k4evi').open,w:document.documentElement.scrollWidth,iw:innerWidth})")
                check(f"{T} Competencia: tarjetas ({o['cards']}) y tabla completa solo dentro de «Evidencia» (plegada)", o["cards"] >= 4 and o["tabvis"] == 0 and o["inEvi"] and not o["open"] and o["w"] <= o["iw"] + 1)
                pg.evaluate("document.querySelector('#k4evi').open=true"); pg.wait_for_timeout(300)
                check(f"{T} Competencia: al abrir «Evidencia» aparece la tabla completa", pg.evaluate("[...document.querySelectorAll('table.k4cmp')].filter(e=>e.checkVisibility()).length") == 1)
        # modo ?legacy=1: pestañas antiguas, mismos criterios
        if name == "1440":
            for user in ("auditor", "admin"):
                pg, errs = ctxpg(pw, vp, mobile, ua); pg.goto(f"http://localhost:{port}/?legacy=1"); pg.wait_for_selector("#lgOpen", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", user); pg.fill("#lgP", PW[user]); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
                tabs = pg.evaluate("[...document.querySelectorAll('#tabs [data-tab]')].map(b=>b.dataset.tab)"); bad = []; ctrl = []
                for t in tabs:
                    pg.evaluate(f"document.querySelector('#tabs [data-tab={t}]').click()"); pg.wait_for_timeout(1200)
                    pg.evaluate("document.querySelectorAll('main.tab.on details').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
                    bad += [(t, m) for m in BAD.findall(pg.evaluate(TXT))]
                    ctrl += [(t, c) for c in pg.evaluate(CTRL, WRITE)]
                check(f"[legacy/{user}] {len(tabs)} pestañas antiguas: cero «PRODUCCIÓN»/«datos reales» {bad[:2]} y sin controles de escritura activos {ctrl[:3]}", len(tabs) >= 10 and not bad and not ctrl)
    # Chrome Android emulado (dispositivo Pixel 7 de Playwright + UA Android)
    d = os.path.join(OUT, "android_pixel7"); os.makedirs(d, exist_ok=True)
    pg, errs = ctxpg(pw, None, True, device="Pixel 7"); login(pg, "auditor")
    check("[Pixel 7 · Chrome Android] UA Android/Chrome y sesión «auditor · viewer»", "Android" in pg.evaluate("navigator.userAgent") and "Chrome" in pg.evaluate("navigator.userAgent") and pg.inner_text(".sessu").strip() == "auditor · viewer")
    audit_screens(pg, "Pixel 7", "auditor", d, errs)
check("CERO llamadas externas (navegador + sockets del proceso)", not EXT)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
