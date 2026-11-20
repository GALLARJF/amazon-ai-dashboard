"""P0 Fase 2.1 · correcciones tras la revisión de la Fase 2 (viewer en staging; escritorio 1440 con barras de desplazamiento clásicas, Android 390 y 360):
1 título de prioridades = nº real mostrado · 2 ningún panel/banner/franja vacío · 3 sin desplazamiento horizontal ni elementos cortados ·
4 cabecera móvil compacta con STAGING, cuenta, selector REAL/DEMO y decisiones · 5 tarjetas de decisión móviles con 5 campos visibles y «Ver detalle» (los 8 campos siguen). Capturas en docs/p0_hoy/fase2_1/despues/."""
import glob, json, os, re, sys, tempfile, threading, urllib.request, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "fase2_1", "despues"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "*.png")): os.remove(f)
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def call(p, b=None, csrf=""):
    r = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}); return json.loads(op.open(r).read())
csrf = call("/api/login", {"username": "admin", "password": "admin-pass-p9Zt4w"})["csrf"]; call("/api/v06/order", {"product": "PRD-PHIVITAL-MAGNESIO"}, csrf)
SECS = ["hoy", "dec", "dir", "ventas", "prod", "lanz", "adm"]
EMPTY_JS = """() => { const out = []; const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 30 && r.height > 3 && s.display !== 'none' && s.visibility !== 'hidden' && !e.closest('details:not([open]) > :not(summary)') && !e.closest('[hidden]') && !e.closest('svg'); };
  document.querySelectorAll('body *').forEach((e) => { if (!vis(e) || /^(SVG|PATH|HR|IMG|INPUT|SELECT|CANVAS|OPTION|SCRIPT|STYLE)$/i.test(e.tagName) || e.matches('.h2dot,.chart,.chart *')) return;
    const s = getComputedStyle(e); const painted = (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent') || (parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none');
    if (painted && e.innerText.trim() === '' && !e.querySelector('input,select,svg,img,canvas,button')) out.push(e.tagName + '#' + e.id + '.' + String(e.className).slice(0, 40) + ' ' + Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height)); });
  document.querySelectorAll('.envbanner,.modebar,.modeguard,.subnav6,.v6msg,.h2head p,.legacybar,.dq').forEach((e) => { if (vis(e) && e.innerText.trim() === '') out.push('BANNER-VACIO ' + e.className); });
  return out; }"""
CUT_JS = """() => { const cw = document.documentElement.clientWidth, out = []; const sel = ['.envbanner', 'header.top .brand', 'header.top .title h1', '#nav6 .n6', '#decChip', '#dmode', '.modebar', '#h2top .h2c', '#h2top .h2sit', '#dec2 .h2dec', '#dec2 .h2tab', '#d2top .h2c', '.sessu'];
  sel.forEach((q) => document.querySelectorAll(q).forEach((e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); if (!r.width || s.display === 'none' || e.closest('[hidden]') || getComputedStyle(e.parentElement).display === 'none') return; if (r.left < -0.5 || r.right > cw + 0.5) out.push(q + ' L' + Math.round(r.left) + ' R' + Math.round(r.right) + ' (cw ' + cw + ')'); })); return out; }"""
BAR_JS = open(os.path.join(ROOT, "tests", "ui_nav_test.py"), encoding="utf-8").read().split('BAR_JS = """')[1].split('"""')[0]
def login(pg):
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached")
    pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_selector("#h2top .h2sit", timeout=10000); pg.wait_for_timeout(1500)
def run(pw, name, vp, mobile):
    ctx = pw.new_context(viewport=vp, device_scale_factor=1, is_mobile=mobile, has_touch=mobile); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    login(pg); T = f"[{name}]"; nav = "#bnav" if mobile else "#nav6"
    # ---------------- 1 · prioridades: el título coincide con las mostradas
    n = pg.locator('[data-blk="prioridades"] li').count(); title = pg.inner_text('[data-blk="prioridades"] h3').split("\n")[0].strip()
    WORD = {0: "Prioridades", 1: "Una prioridad", 2: "Dos prioridades", 3: "Tres prioridades"}
    check(f"{T} 1 · el título «{title}» coincide con las {n} prioridades mostradas (no se inventa una tercera)", n == 2 and title.startswith(WORD[n]) and "Tres" not in title)
    # ---------------- 2 · ningún panel/franja vacío (todas las secciones)
    bad = []
    for sec in SECS:
        pg.evaluate(f"NAV6.go('{sec}',0)"); pg.wait_for_timeout(1000); bad += [f"{sec}: {x}" for x in pg.evaluate(EMPTY_JS)]
    for x in bad[:8]: print("    ", x)
    check(f"{T} 2 · ningún panel, alerta ni banner vacío en las 7 pantallas ({len(bad)})", not bad)
    pg.evaluate("NAV6.go('dec',0)"); pg.wait_for_timeout(900)
    check(f"{T} 2 · franja de modo de datos y etiqueta STAGING con texto", len(pg.inner_text("#modeBar").strip()) > 10 and "STAGING" in pg.inner_text("#envBanner"))
    # ---------------- 3 · sin desplazamiento horizontal ni elementos cortados
    offs = []
    for sec in SECS:
        pg.evaluate(f"NAV6.go('{sec}',0)"); pg.wait_for_timeout(900)
        m = pg.evaluate("[scrollX, document.documentElement.scrollWidth, document.documentElement.clientWidth, innerWidth]"); cut = pg.evaluate(CUT_JS)
        if m[0] != 0 or m[1] > m[3] or m[1] > m[2] or cut: offs.append(f"{sec}: {m} {cut[:2]}")
    for x in offs: print("    ", x)
    check(f"{T} 3 · scrollX = 0, scrollWidth ≤ innerWidth y ningún elemento cortado en las 7 pantallas", not offs)
    pg.evaluate("NAV6.go('dec',0)"); pg.wait_for_timeout(600); pg.evaluate("window.scrollTo(240, 0)"); pg.wait_for_timeout(400)
    check(f"{T} 3 · aunque algo intente desplazar la página en horizontal, vuelve a scrollX = 0", pg.evaluate("scrollX") == 0)
    pg.click(f'{nav} [data-sec="hoy"]'); pg.wait_for_timeout(500); pg.click('[data-h2go="dec"]'); pg.wait_for_selector("#tab-decisiones.on .h2dec"); pg.wait_for_timeout(500)
    check(f"{T} 3 · al entrar en DECISIONES desde HOY: scrollX = 0 y AHT y «Hoy» completos dentro de la pantalla", pg.evaluate("scrollX") == 0 and pg.evaluate("(()=>{const a=document.querySelector('.brand b').getBoundingClientRect();const h=document.querySelector('%s [data-sec=hoy]').getBoundingClientRect();return a.left>=0&&h.left>=0&&h.right<=innerWidth})()" % nav))
    # ---------------- 5 · decisiones: capturas y tarjeta
    pg.screenshot(path=os.path.join(OUT, f"{name}_2_decisiones.png"), full_page=not mobile)
    if mobile: pg.screenshot(path=os.path.join(OUT, f"{name}_2_decisiones_completa.png"), full_page=True)
    vis = lambda lab: pg.evaluate("""(l)=>{const dt=[...document.querySelectorAll('#dec2 .h2dec:first-of-type dt')].find(x=>x.textContent.trim()===l); if(!dt) return null; const r=dt.getBoundingClientRect(); return r.width>0&&r.height>0&&dt.checkVisibility({contentVisibilityAuto:true,visibilityProperty:true})}""", lab)
    FIVE = ["Acción recomendada", "Producto", "Prioridad", "Fecha límite", "Impacto estimado"]; REST = ["Responsable", "Evidencia", "Estado"]
    if mobile:
        check(f"{T} 5 · móvil: visibles al abrir Acción recomendada, Producto, Prioridad, Fecha límite e Impacto", all(vis(l) for l in FIVE))
        check(f"{T} 5 · móvil: Responsable, Evidencia y Estado quedan en «Ver detalle» (plegados), pero siguen en la tarjeta (8 campos)", not any(vis(l) for l in REST) and pg.eval_on_selector("#dec2 .h2dec", "e=>e.querySelectorAll('dt').length") == 8 and "Ver detalle" in pg.inner_text("#dec2 .h2more summary"))
        h = pg.eval_on_selector("#dec2 .h2dec", "e=>e.getBoundingClientRect().height"); lim = 520 if vp["width"] >= 390 else 560
        check(f"{T} 5 · móvil: tarjeta cerrada de {h:.0f}px ≤ {lim}px (no excesivamente larga)", h <= lim)
        check(f"{T} 5 · móvil: «Ver detalle» ≥ 44 px y botones ≥ 44 px", pg.evaluate("[...document.querySelectorAll('#dec2 .h2more summary, #dec2 button')].every(b=>b.getBoundingClientRect().height>=43)"))
        pg.click("#dec2 .h2more summary"); pg.wait_for_timeout(300)
        check(f"{T} 5 · móvil: al pulsar «Ver detalle» aparecen Responsable, Evidencia y Estado", all(vis(l) for l in REST)); pg.click("#dec2 .h2more summary")
        pg.click('[data-h2f="regla"]'); pg.wait_for_timeout(500); tops = pg.eval_on_selector_all("#dec2 .h2dec", "e=>e.map(x=>[Math.round(x.getBoundingClientRect().top+scrollY), Math.round(x.getBoundingClientRect().height)])")
        check(f"{T} 5 · móvil: con 5 sugeridas, cada tarjeta ocupa ≤ {lim}px y la siguiente empieza justo después {[t[1] for t in tops]}", len(tops) == 5 and all(t[1] <= lim for t in tops) and all(tops[i + 1][0] - (tops[i][0] + tops[i][1]) <= 24 for i in range(4)))
        pg.click('[data-h2f="pend"]')
    else:
        check(f"{T} 5 · escritorio: los 8 campos visibles sin «Ver detalle»", all(vis(l) for l in FIVE + REST) and not pg.locator("#dec2 .h2more summary").first.is_visible())
    # ---------------- 4 · cabecera móvil
    pg.evaluate("NAV6.go('hoy',0)"); pg.wait_for_timeout(1300); pg.evaluate("window.scrollTo(0,0)")
    if mobile:
        hb = pg.evaluate("Math.round(document.querySelector('#modeBar').getBoundingClientRect().bottom)")
        check(f"{T} 4 · cabecera (hasta la franja de datos) mide {hb}px ≤ 175px (antes ≈ 300)", hb <= 175)
        ok = pg.evaluate("""()=>{const v=(q)=>{const e=document.querySelector(q);if(!e)return false;const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none'&&r.left>=0&&r.right<=innerWidth}; return [v('#envBanner'),v('.sessu'),v('#dmode'),v('#decChip')]}""")
        check(f"{T} 4 · siguen visibles: STAGING, cuenta activa, selector REAL/DEMO y decisiones pendientes {ok}", all(ok) and "auditor · viewer" in pg.inner_text(".sessu") and "STAGING" in pg.inner_text("#envBanner") and pg.inner_text("#decN") == "1" and "DEMO" in pg.eval_on_selector("#dmode", "s=>s.selectedOptions[0].textContent"))
        check(f"{T} 4 · «Salir» y el selector de cuenta van dentro del menú de cuenta (cerrado: ocultos)", not pg.locator("#lgOut").is_visible() and not pg.locator("#acSel").is_visible())
        sz = pg.evaluate("""()=>[...document.querySelectorAll('.sessu,#dmode,#decChip,#bnav .bn')].map(e=>Math.round((e.closest('label')||e).getBoundingClientRect().height))"""); check(f"{T} 4 · cuenta, selector, chip y barra inferior ≥ 44 px {sorted(set(sz))}", min(sz) >= 44)
        sit = pg.evaluate("document.querySelector('.h2sit').getBoundingClientRect().bottom"); ven = pg.evaluate("document.querySelector('[data-blk=ventas]').getBoundingClientRect().top"); bar = pg.evaluate("document.querySelector('#bnav').getBoundingClientRect().top")
        check(f"{T} 4 · sin desplazar se ve la Situación general ({sit:.0f}px) y el comienzo de la siguiente tarjeta (empieza {ven:.0f}px; barra inferior {bar:.0f}px; ≥ 70px visibles)", sit < bar and bar - ven >= 70)
        pg.screenshot(path=os.path.join(OUT, f"{name}_1_hoy.png")); pg.screenshot(path=os.path.join(OUT, f"{name}_1_hoy_completa.png"), full_page=True)
        pg.click(".sessu"); pg.wait_for_timeout(300)
        okm = pg.evaluate("""()=>['#lgOut','#acSel'].map(q=>{const r=document.querySelector(q).getBoundingClientRect();return r.width>0&&r.height>=43&&r.left>=0&&r.right<=innerWidth})""")
        check(f"{T} 4 · al abrir el menú de cuenta se ven «Salir» y el selector de cuenta, táctiles y dentro de pantalla {okm}", all(okm)); pg.screenshot(path=os.path.join(OUT, f"{name}_1_hoy_menu_cuenta.png")); pg.click(".sessu"); pg.wait_for_timeout(200)
        check(f"{T} 4 · el menú de cuenta se cierra", not pg.locator("#lgOut").is_visible())
    else:
        pg.screenshot(path=os.path.join(OUT, f"{name}_1_hoy.png"), full_page=True)
    pg.evaluate("NAV6.go('dir',0)"); pg.wait_for_selector("#d2top .h2conc"); pg.wait_for_timeout(700); pg.screenshot(path=os.path.join(OUT, f"{name}_3_director.png"), full_page=not mobile)
    if mobile: pg.screenshot(path=os.path.join(OUT, f"{name}_3_director_completa.png"), full_page=True); pg.evaluate("window.scrollTo(0,document.documentElement.scrollHeight)"); pg.wait_for_timeout(300); r = pg.evaluate(BAR_JS); check(f"{T} barra inferior sin cubrir contenido en DIRECTOR ({r.get('maxBottom')} ≤ {r.get('barTop')})", "err" not in r and r["maxBottom"] <= r["barTop"] + 1)
    check(f"{T} sin errores de consola", errs == []); ctx.close()
with sync_playwright() as p:
    b = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])   # barras de desplazamiento clásicas, como un navegador de escritorio real
    run(b, "desktop", {"width": 1440, "height": 900}, False); run(b, "desktop1280", {"width": 1280, "height": 720}, False)
    run(b, "android", {"width": 390, "height": 844}, True); run(b, "android360", {"width": 360, "height": 740}, True); b.close()
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
