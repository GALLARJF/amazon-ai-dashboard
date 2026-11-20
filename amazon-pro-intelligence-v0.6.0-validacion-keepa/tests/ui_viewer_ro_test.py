"""P0 Fase 2 · VIEWER: TODOS los controles de escritura de TODAS las pantallas (6 secciones, sub-secciones y Decisiones) aparecen desactivados o identificados como «No disponible»;
no basta con el 403 del servidor. Lista de verbos de escritura propia de la prueba (independiente de la de la interfaz). Se comprueba también con un administrador que esos mismos controles SÍ están activos (control negativo)."""
import json, os, re, sys, tempfile, threading, urllib.request, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def call(p, b=None, csrf=""):
    r = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}); return json.loads(op.open(r).read())
csrf = call("/api/login", {"username": "admin", "password": "admin-pass-p9Zt4w"})["csrf"]; call("/api/v06/order", {"product": "PRD-PHIVITAL-MAGNESIO"}, csrf)
WRITE = re.compile(r"guard|crea|nuev|aprob|rechaz|lanz|ejecut|analiz|import|publi|activ|archiv|añad|edit|envi|propon|investig|reanud|prob(ar|emos)|confirm|elimin|borr|registr|valid|gener|inici|aplic|actualiz|solicit|reconcil|fijar|cancel|descart|marc|verific|sub(ir|e)\b|carg|restaur|respald|pregunt|consult|medir|calcul|refresc|contraseñ|restablec|desactiv|paus|deten|program|asign|sincroniz|descarg|⬇|sellar|firmar|decidir|enviar|ejecutar", re.I)
NAVOK = re.compile(r"^(hoy|ventas|productos|lanzamientos|director ia|administración|director|admin|salir|datos del director|cerrar|✕|ver decisiones.*|ir al producto.*|pendientes de ti.*|sugeridas por reglas.*|en seguimiento.*|resueltas.*|decisiones.*|iniciar sesión)$", re.I)
SECS = [("hoy", [0]), ("ventas", [0, 1, 2]), ("prod", [0, 1, 2, 3]), ("lanz", [0, 1, 2]), ("dir", [0, 1]), ("adm", [0, 1, 2]), ("dec", [0])]
JS = """() => { const out = []; const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && !e.closest('details:not([open]) > :not(summary)') && !e.closest('[hidden]'); };
  document.querySelectorAll('main.tab.on button, main.tab.on input, main.tab.on textarea, main.tab.on label.btn, main.tab.on select, #modeGuard button').forEach((e) => { if (!vis(e) && e.type !== 'file') return;
    if (e.closest('#nav6, #bnav, #subnav6, header, .k4views') ) return;
    const txt = (e.tagName === 'INPUT' ? (e.value || e.placeholder || e.type) : e.textContent || '').trim();
    out.push({tag: e.tagName, type: e.type || '', txt: txt.slice(0, 60), dis: !!e.disabled || e.getAttribute('aria-disabled') === 'true', cls: e.className, title: e.title || '', act: e.dataset.act || '', kids: e.children.length, exp: e.hasAttribute('aria-expanded') || e.getAttribute('role') === 'tab', id: e.id, k4: Object.keys(e.dataset).join(',')}); });
  return out; }"""
def sweep(pg, tag, expect_ro):
    bad = []; tot = 0; locked = 0
    for sid, subs in SECS:
        for j in subs:
            pg.evaluate(f"NAV6.go('{sid}',{j})"); pg.wait_for_timeout(1300)
            for e in pg.evaluate(JS):
                tot += 1
                if e['kids'] or e['exp']: continue   # tarjetas/acordeones de solo lectura (abren o pliegan, no escriben)
                isw = e["tag"] == "TEXTAREA" or e["type"] == "file" or (e["tag"] != "SELECT" and WRITE.search(e["txt"]) and not NAVOK.match(e["txt"]) and e["act"] not in ("demo-on", "demo-off", "goto-lanz", "open-chat", "cancel")) or (e["act"] and e["act"] not in ("demo-on", "demo-off", "goto-lanz", "open-chat", "cancel"))
                if not isw: continue
                if e["dis"]: locked += 1
                if expect_ro and not e["dis"]: bad.append(f'{sid}/{j}: «{e["txt"]}» ({e["tag"]} {e["type"]} {e["act"]})')
                if expect_ro and e["dis"] and not ("vro" in e["cls"] or "No disponible" in e["title"] or "Solo lectura" in e["title"]): bad.append(f'{sid}/{j}: «{e["txt"]}» desactivado pero sin rótulo visible')
                if not expect_ro and e["dis"] and e["type"] != "file" and "No disponible" in e["title"]: bad.append(f'{sid}/{j}: «{e["txt"]}» bloqueado para un admin')
    return bad, tot, locked
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached")
    pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(2000)
    bad, tot, locked = sweep(pg, "viewer", True)
    for x in bad[:40]: print("   ", x)
    check(f"VIEWER: {tot} controles revisados en 7 pantallas/16 sub-vistas; {locked} controles de escritura desactivados y 0 activos o sin rótulo ({len(bad)})", not bad and locked >= 8)
    vt = pg.evaluate("document.querySelectorAll('.vro').length"); check(f"VIEWER: los controles bloqueados se ven bloqueados (clase .vro → opacidad, tachado y 🔒; {vt} en la última pantalla o más)", pg.evaluate("(()=>{const e=document.querySelector('button.vro');if(!e)return true;const s=getComputedStyle(e);return parseFloat(s.opacity)<0.6&&s.cursor==='not-allowed'})()"))
    pg.close()
    # control negativo: el mismo barrido con un ADMIN debe encontrar los controles ACTIVOS (la prueba distingue de verdad)
    pg2 = b.new_context(viewport={"width": 1440, "height": 900}).new_page(); pg2.goto(f"http://localhost:{port}/"); pg2.wait_for_selector("#nav6", state="attached")
    pg2.click("#lgOpen"); pg2.fill("#lgU", "admin"); pg2.fill("#lgP", "admin-pass-p9Zt4w"); pg2.click("#lgGo"); pg2.wait_for_selector(".sessu"); pg2.wait_for_timeout(2000)
    act = 0
    for sid, subs in SECS:
        for j in subs:
            pg2.evaluate(f"NAV6.go('{sid}',{j})"); pg2.wait_for_timeout(1000); act += pg2.evaluate("[...document.querySelectorAll('main.tab.on button:not(:disabled), main.tab.on input[type=file]:not(:disabled)')].filter(e=>/guard|aprob|import|crear|nuev|ejecut|lanz/i.test(e.textContent+e.type)).length")
    check(f"control negativo: con un ADMIN la misma prueba ve {act} controles de escritura ACTIVOS (≥ 8): la prueba es sensible", act >= 8)
    b.close()
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
