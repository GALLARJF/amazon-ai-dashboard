"""CORRECCIÓN 4.2 — viewer realmente solo lectura en la interfaz. Recorre las 15 pantallas (+ pestañas ?legacy=1) como viewer y comprueba CERO campos
de escritura habilitados (input/select/textarea/file) y botones de escritura desactivados, con «Solo lectura — viewer» visible; navegación, filtros de vista,
acordeones y logout siguen operativos; admin conserva sus campos (servidor NO staging); escrituras del viewer → 403. 1440, 390, 360 y Pixel 7.
Capturas Pre-Launch: docs/p0_hoy/final_4_2/."""
import glob, json, os, re, socket, sys, tempfile, threading, urllib.request, urllib.error, http.cookiejar as CJ
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
for k in list(os.environ):
    if k.startswith("AMAZON_PRO_"): os.environ.pop(k)
PW = {"admin": "admin-pass-p9Zt4w", "auditor": "viewer-pass-x7Qk2m"}
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR=PW["auditor"], PLAYWRIGHT_BROWSERS_PATH="/opt/pw-browsers")
EXT = []; _c = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(addr); raise AssertionError("RED PROHIBIDA")
    return _c(self, addr, *a, **k)
socket.socket.connect = _no_net
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "final_4_2"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
def mk(staging):
    S.STAGING = staging; tmp = tempfile.mkdtemp()
    srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password=PW["admin"])
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, srv.server_address[1]
srv, port = mk(True)
ANDROID = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
SUBS = [("hoy", 1), ("ventas", 2), ("prod", 4), ("lanz", 3), ("dir", 2), ("dec", 1), ("adm", 2)]
# campos de VISUALIZACIÓN permitidos (no alteran datos)
OKF = "#lgForm *,#acSel,#dmode,#dirDossier,#fMkt,#fPeriod,#fProduct,#k4fc,#k4fd,#k4fk,#k4fp,#k4io,#k4it,#k4par,#v6Prod-ventas,#v6Prod-lanz"
FIELDS = """(ok)=>[...document.querySelectorAll('input,select,textarea')].filter(e=>e.type!=='hidden'&&!e.matches(ok)&&!(e.disabled||e.readOnly&&e.tagName!=='SELECT'&&!/^(checkbox|radio|file|range)$/.test(e.type)&&false)&&!e.disabled).map(e=>e.tagName+'#'+e.id+'@'+(e.closest('[id]')||{id:''}).id)"""
MARK = """(ok)=>[...document.querySelectorAll('input,select,textarea')].filter(e=>e.type!=='hidden'&&!e.matches(ok)&&(e.getAttribute('aria-disabled')!=='true'||!/Solo lectura — viewer/.test(e.title))).map(e=>e.tagName+'#'+e.id)"""
BTN = r"(^\s*\+|guardar|crear|nuevo|nueva|aprobar|rechazar|lanzar|ejecutar|analizar|importar|publicar|activar|archivar|añadir|editar|enviar|proponer|investigar|reanudar|probar|confirmar|eliminar|borrar|registrar|validar|generar|iniciar|aplicar|actualizar|solicitar|reconciliar|fijar|descartar|marcar|verificar|subir|cargar|restaurar|respaldo|preguntar|medir|refrescar|restablecer|desactivar|pausar|detener|programar|asignar|sincronizar|vaciar|ejemplo|dossier|coworker|chat|aprobaci)"
BTNS = """(re)=>{const R=new RegExp(re,'i'),K='#lgOut,#lgOpen,#lgForm *,.ro-ok,[data-tab],#nav6 *,#bnav *,#subnav6 *,[data-k4v],[data-k4bv],[data-h2f],[data-h2go],[data-h2prod],[data-x4go],[data-x4open],a.btn,#dmode,summary,.chip[data-k4exp360],#legacy *';
 return [...document.querySelectorAll('button,label.btn')].filter(e=>(e.checkVisibility?e.checkVisibility():true)&&!e.disabled&&e.getAttribute('aria-disabled')!=='true'&&!e.matches(K)&&!e.closest('#tabs')&&(R.test(e.textContent||'')||(e.dataset&&e.dataset.act&&!/^(demo-on|demo-off|goto-lanz|open-chat|cancel)$/.test(e.dataset.act)))).map(e=>(e.id||e.tagName)+':'+(e.textContent||'').trim().slice(0,40))}"""
def hreq(port_, method, path, body=None, jar=None, csrf=""):
    rq = urllib.request.Request(f"http://localhost:{port_}" + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf})
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        with op.open(rq) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b"{}")
        except Exception: return e.code, {}
WR = [("POST", "/api/v06/decide", {"id": 1, "approve": True}), ("POST", "/api/catalog/update", {"id": "PRD-ACTIVCORE-V2", "patch": {"name": "x"}}), ("POST", "/api/dossiers", {"name": "x"}),
      ("POST", "/api/k4/import", {"csv": "a"}), ("PUT", "/api/catalog/update", {}), ("PATCH", "/api/catalog/update", {}), ("DELETE", "/api/dossiers/1", None)]
def login(pg, user, p_, legacy=False):
    pg.goto(f"http://localhost:{p_}/" + ("?legacy=1" if legacy else "")); pg.wait_for_selector("#lgOpen", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", user); pg.fill("#lgP", PW[user]); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
def ctxpg(pw, vp, mobile, ua=None, device=None):
    kw = dict(p.devices[device]) if device else dict(viewport=vp, device_scale_factor=1, is_mobile=mobile, has_touch=mobile, **({"user_agent": ua} if ua else {}))
    ctx = pw.new_context(**kw); pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); return pg, errs
def go(pg, s, i):
    pg.evaluate(f"NAV6.go('{s}',{i})"); pg.wait_for_timeout(1400)
    if (s, i) == ("lanz", 2) and pg.locator(".eucard[data-pid]").count(): pg.locator(".eucard[data-pid]").first.click(); pg.wait_for_selector(".euconc", timeout=15000); pg.wait_for_timeout(600)
    pg.evaluate("document.querySelectorAll('main details, #v6root details, details').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
def audit(pg, name, errs, shots):
    f = []; m = []; b = []; n = 0
    for s, c in SUBS:
        for i in range(c):
            go(pg, s, i); n += 1
            f += [(f"{s}{i}", x) for x in pg.evaluate(FIELDS, OKF)]; m += [(f"{s}{i}", x) for x in pg.evaluate(MARK, OKF)]; b += [(f"{s}{i}", x) for x in pg.evaluate(BTNS, BTN)]
            if (s, i) == ("lanz", 1):
                pl = pg.evaluate("(ok)=>({total:document.querySelectorAll('#plLeft input,#plLeft select,#plLeft textarea').length,open:[...document.querySelectorAll('#plLeft input,#plLeft select,#plLeft textarea')].filter(e=>!e.disabled&&!e.matches(ok)).length,editable:[...document.querySelectorAll('#root input,#root select,#root textarea,main input,main select,main textarea')].filter(e=>e.type!=='hidden'&&!e.disabled&&!e.matches(ok)).length,badge:!!document.querySelector('#plLeft .ro-badge')})", OKF)
                check(f"[{name}] Pre-Launch: {pl['total']} campos de la calculadora, EXACTAMENTE 0 editables ({pl['open']}/{pl['editable']}), aviso «Solo lectura — viewer» visible", pl["total"] >= 20 and pl["open"] == 0 and pl["editable"] == 0 and pl["badge"])
                if shots: pg.evaluate("scrollTo(0,0)"); pg.screenshot(path=os.path.join(shots, f"prelaunch_viewer_{name.replace(" ","")}.png"))
                pg.evaluate("document.querySelector('#plLeft').scrollIntoView()"); pg.wait_for_timeout(200)
                if shots: pg.screenshot(path=os.path.join(shots, f"prelaunch_viewer_{name.replace(" ","")}_calculadora.png"))
    check(f"[{name}] viewer · {n} pantallas: cero campos de escritura habilitados {f[:3]}", n == 15 and not f)
    check(f"[{name}] viewer · todos los campos bloqueados con aria-disabled y «Solo lectura — viewer» {m[:3]}", not m)
    check(f"[{name}] viewer · todos los botones de escritura desactivados {b[:3]}", not b)
    check(f"[{name}] sin errores de JavaScript {errs[:1]}", not errs)
def nav_ok(pg, name):
    go(pg, "ventas", 0); pg.wait_for_timeout(300)
    a = pg.evaluate("document.querySelector('#nav6')?1:0"); pg.evaluate("NAV6.go('prod',2)"); pg.wait_for_timeout(1200)
    sec = pg.evaluate("NAV6.state.sec"); sub = pg.evaluate("NAV6.state.sub")
    check(f"[{name}] navegación principal y secundaria operativas (sec={sec}, sub={sub})", a == 1 and sec == "prod" and sub == 2)
    if pg.locator("#k4fc").count():
        o = pg.evaluate("(()=>{const s=document.querySelector('#k4fc');return !s.disabled&&s.options.length>0})()"); check(f"[{name}] filtro de vista (#k4fc) sigue habilitado", o)
    check(f"[{name}] selector de cuenta y DEMO/REAL habilitados", pg.evaluate("!document.querySelector('#acSel').disabled&&!document.querySelector('#dmode').disabled"))
    pg.evaluate("NAV6.go('prod',2)"); pg.wait_for_timeout(1000)
    if pg.locator("#k4evi").count():
        pg.evaluate("document.querySelector('#k4evi').open=false"); pg.locator("#k4evi > summary").click(); pg.wait_for_timeout(300)
        check(f"[{name}] acordeón «Evidencia» se abre/cierra para el viewer", pg.evaluate("document.querySelector('#k4evi').open"))
def logout_ok(pg, name):
    if not pg.locator("#lgOut").is_visible(): pg.click(".sessu"); pg.wait_for_timeout(300)
    pg.click("#lgOut"); pg.wait_for_timeout(1200)
    check(f"[{name}] cerrar sesión sigue funcionando", pg.locator(".sessu").count() == 0 or not pg.locator(".sessu").is_visible())
# ---- 1) servidor staging: viewer
for u in ("auditor",):
    jar = CJ.CookieJar(); c, j = hreq(port, "POST", "/api/login", {"username": u, "password": PW[u]}, jar)
    codes = [hreq(port, m_, p_, b_, jar, j.get("csrf", ""))[0] for m_, p_, b_ in WR]
    check(f"[staging/viewer] POST/PUT/PATCH/DELETE → 403 {codes.count(403)}/{len(codes)}", c == 200 and j.get("role") == "viewer" and all(x == 403 for x in codes))
with sync_playwright() as p:
    pw = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])
    for name, vp, mobile, ua in (("1440", {"width": 1440, "height": 900}, False, None), ("390", {"width": 390, "height": 844}, True, ANDROID), ("360", {"width": 360, "height": 740}, True, ANDROID)):
        pg, errs = ctxpg(pw, vp, mobile, ua); login(pg, "auditor", port)
        check(f"[{name}] sesión «auditor · viewer»", pg.inner_text(".sessu").strip() == "auditor · viewer")
        audit(pg, name, errs, OUT)
        nav_ok(pg, name); logout_ok(pg, name)
    pg, errs = ctxpg(pw, None, True, device="Pixel 7"); login(pg, "auditor", port)
    check("[Pixel 7] UA Android/Chrome", "Android" in pg.evaluate("navigator.userAgent") and "Chrome" in pg.evaluate("navigator.userAgent"))
    audit(pg, "Pixel 7", errs, OUT); nav_ok(pg, "Pixel 7"); logout_ok(pg, "Pixel 7")
    # legacy
    pg, errs = ctxpg(pw, {"width": 1440, "height": 900}, False); login(pg, "auditor", port, legacy=True)
    tabs = pg.evaluate("[...document.querySelectorAll('#tabs [data-tab]')].map(b=>b.dataset.tab)"); lf = []; lb = []
    for t in tabs:
        pg.evaluate(f"document.querySelector('#tabs [data-tab={t}]').click()"); pg.wait_for_timeout(1200); pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
        lf += [(t, x) for x in pg.evaluate(FIELDS, OKF + ",#tabs *")]; lb += [(t, x) for x in pg.evaluate(BTNS, BTN)]
    check(f"[legacy/viewer] {len(tabs)} pestañas antiguas: cero campos habilitados {lf[:3]} y cero botones de escritura {lb[:3]}", len(tabs) >= 10 and not lf and not lb)
    # ---- 2) servidor NO staging: admin conserva sus campos; viewer sigue 403 y bloqueado
    srv2, port2 = mk(False)
    pg, errs = ctxpg(pw, {"width": 1440, "height": 900}, False); login(pg, "admin", port2)
    go(pg, "lanz", 1); pg.wait_for_timeout(800)
    ad = pg.evaluate("(ok)=>[...document.querySelectorAll('#plLeft input,#plLeft select')].filter(e=>!e.disabled&&!e.readOnly).length", OKF); tot = pg.evaluate("document.querySelectorAll('#plLeft input,#plLeft select').length")
    check(f"[admin · no staging] Pre-Launch: {ad}/{tot} campos operativos y sin aviso de solo lectura", tot >= 20 and ad == tot and pg.locator("#plLeft .ro-badge").count() == 0)
    fld = pg.locator("#plLeft input:not([type=checkbox]):not([type=radio])").first; v0 = fld.input_value(); fld.fill("7"); check("[admin · no staging] un campo de Pre-Launch admite edición", fld.input_value() == "7")
    go(pg, "adm", 0); check("[admin · no staging] Administración mantiene controles de escritura activos", len(pg.evaluate(BTNS, BTN)) >= 1)
    jar = CJ.CookieJar(); c, j = hreq(port2, "POST", "/api/login", {"username": "auditor", "password": PW["auditor"]}, jar)
    codes = [hreq(port2, m_, p_, b_, jar, j.get("csrf", ""))[0] for m_, p_, b_ in WR]
    check(f"[no staging/viewer] POST/PUT/PATCH/DELETE → 403 {codes.count(403)}/{len(codes)}", j.get("role") == "viewer" and all(x == 403 for x in codes))
    pg, errs = ctxpg(pw, {"width": 1440, "height": 900}, False); login(pg, "auditor", port2); S.STAGING = False
    go(pg, "lanz", 1); check("[no staging/viewer] Pre-Launch también 0 editables (doble protección)", pg.evaluate("[...document.querySelectorAll('#plLeft input,#plLeft select')].filter(e=>!e.disabled).length") == 0)
check("CERO llamadas externas", not EXT)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
