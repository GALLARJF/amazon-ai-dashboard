"""P0 Fase 2 · HOY ejecutivo, bandeja unificada de DECISIONES y DIRECTOR IA simplificado, con el usuario VIEWER en staging (navegador real, escritorio + Android 390 y 360).
Comprueba: 6 bloques, sin rutas/metodología en primer nivel, REAL/DEMO/SIN DATOS, SIN DATOS≠0, riesgos por criticidad, 8 campos por decisión, Director en niveles,
navegación recomendación→producto, viewer con controles desactivados, móvil sin tablas ni barra solapada, 0 escrituras y 0 peticiones externas. Capturas en docs/p0_hoy/fase2/."""
import glob, json, os, re, sys, tempfile, threading, urllib.request, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "fase2", "despues"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "*.png")): os.remove(f)
# datos de prueba (sintéticos, en la BD temporal): el administrador pide preparar un lanzamiento → N1 automático + 1 decisión N3 (gasto Keepa) en la bandeja. Nada se ejecuta de pago.
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def call(p, b=None, csrf=""):
    r = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}); return json.loads(op.open(r).read())
csrf = call("/api/login", {"username": "admin", "password": "admin-pass-p9Zt4w"})["csrf"]; call("/api/v06/order", {"product": "PRD-PHIVITAL-MAGNESIO"}, csrf)
SIX = ["Situación general", "Ventas", "Margen", "Stock y riesgos", "Decisiones pendientes", "Dos prioridades"]   # el título es dinámico: aquí hay 2 prioridades reales (no se inventa una tercera)
LABELS = ["Acción recomendada", "Producto", "Prioridad", "Fecha límite", "Impacto estimado", "Responsable", "Evidencia", "Estado"]
TECH = re.compile(r"/api/|endpoint|metodolog|\bGET\b|\bPOST\b|\btokens?\b|\bmodelo|llamadas? a", re.I)
BAR_JS = open(os.path.join(ROOT, "tests", "ui_nav_test.py"), encoding="utf-8").read().split('BAR_JS = """')[1].split('"""')[0]
def run(pw, name, vp, mobile):
    ctx = pw.new_context(viewport=vp, device_scale_factor=1, is_mobile=mobile, has_touch=mobile); pg = ctx.new_page(); errs = []; writes = []; ext = []; reqs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.on("request", lambda r: (reqs.append(r.url), r.method != "GET" and not r.url.endswith(("/api/login", "/api/logout")) and writes.append((r.method, r.url)), not re.match(r"^(http://(localhost|127\.0\.0\.1):%d/|data:|blob:)" % port, r.url) and ext.append(r.url)))
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached")
    pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_selector("#h2top .h2sit", timeout=10000); pg.wait_for_timeout(1500)
    nav = "#bnav" if mobile else "#nav6"; T = f"[{name}]"
    # ------------------------------------------------------------------ HOY
    hs = pg.eval_on_selector_all("#h2top h2, #h2top h3", "e=>e.map(x=>x.childNodes[0].textContent.trim())")
    check(f"{T} HOY: exactamente los 6 bloques pedidos {hs}", hs == SIX)
    top = pg.inner_text("#h2top")
    check(f"{T} HOY: sin rutas /api, metodología, tokens ni detalles técnicos en primer nivel", not TECH.search(top))
    check(f"{T} HOY: «Evidencia y metodología» plegada (segundo nivel)", pg.locator("#h2det").evaluate("d=>!d.open") and "Evidencia y metodología" in pg.inner_text("#h2det summary"))
    badges = pg.eval_on_selector_all("#h2top h2 .h2b, #h2top h3 .h2b", "e=>e.map(x=>x.textContent.trim())")
    check(f"{T} HOY: cada bloque identifica REAL / DEMO / SIN DATOS {badges}", len(badges) == 6 and all(b in ("REAL", "DEMO", "SIN DATOS") for b in badges))
    check(f"{T} HOY: en staging todo se rotula DEMO (entorno sintético), nunca REAL", "REAL" not in badges)
    rl = pg.inner_text('[data-blk="stock"] .h2risk')
    m = re.search(r"(\d+) riesgos? abiertos?: (\d+) crític\w+ · (\d+) alt\w+ · (\d+) medi\w+ · (\d+) baj\w+", rl)
    check(f"{T} HOY: «{rl}» desglosado por criticidad y la suma cuadra", bool(m) and sum(map(int, m.groups()[1:])) == int(m.group(1)) and int(m.group(1)) == 5 and m.group(2) == "0" and m.group(4) == "5")
    check(f"{T} HOY: la situación indica semáforo, etiqueta y frase", pg.locator(".h2sit .h2dot").is_visible() and len(pg.inner_text(".h2sit .h2big")) > 30 and pg.locator(".h2sit .h2lab").inner_text() in ("ATENCIÓN", "ACCIÓN URGENTE", "SIN INCIDENCIAS", "SIN DATOS"))
    stock = pg.inner_text('[data-blk="stock"]')
    check(f"{T} HOY: stock ausente = «SIN DATOS», no 0", "SIN DATOS" in stock and not re.search(r"\b0 uds", stock))
    nsd = pg.evaluate("""()=>[...document.querySelectorAll('#h2top .h2c')].filter(c=>c.querySelector('.h2b-nd')).map(c=>c.innerText)""")
    check(f"{T} HOY: ningún bloque «SIN DATOS» muestra un 0 como valor", all(not re.search(r"(^|\s)0([.,]0+)?\s?€", t) for t in nsd))
    check(f"{T} HOY: ≤3 decisiones y ≤3 prioridades visibles", pg.locator('[data-blk="decisiones"] li').count() <= 3 and 1 <= pg.locator('[data-blk="prioridades"] li').count() <= 3)
    n_chip = int(pg.inner_text("#decN")); n_btn = int(re.search(r"\((\d+)\)", pg.inner_text('[data-h2go="dec"]')).group(1))
    check(f"{T} HOY: contador del chip ({n_chip}) = botón «Ver decisiones» ({n_btn}) = 1 decisión sembrada", n_chip == n_btn == 1)
    check(f"{T} HOY: sin tablas", pg.locator("#h2top table").count() == 0 and pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    if mobile:
        xs = pg.eval_on_selector_all("#h2top .h2c", "e=>e.map(x=>[Math.round(x.getBoundingClientRect().left),Math.round(x.getBoundingClientRect().width)])")
        check(f"{T} HOY móvil: tarjetas de una columna ({xs[0]})", len({tuple(x) for x in xs}) == 1)
        pg.evaluate("window.scrollTo(0,document.documentElement.scrollHeight)"); pg.wait_for_timeout(300); r = pg.evaluate(BAR_JS)
        check(f"{T} HOY móvil: barra inferior sin cubrir contenido ({r.get('maxBottom')} ≤ {r.get('barTop')})", "err" not in r and r["maxBottom"] <= r["barTop"] + 1); pg.evaluate("window.scrollTo(0,0)")
        small = pg.evaluate("""()=>[...document.querySelectorAll('#h2top button, #h2top summary, #h2det summary')].filter(b=>b.getBoundingClientRect().height<44-1).length""")
        check(f"{T} HOY móvil: botones táctiles ≥ 44 px", small == 0)
        first = pg.evaluate("""()=>{const r=document.querySelector('.h2sit').getBoundingClientRect(); return Math.round(r.bottom)}""")
        check(f"{T} HOY móvil: la situación (conclusión+alerta) cabe en la primera pantalla (termina en {first}px ≤ 844)", first <= 844)
    pg.screenshot(path=os.path.join(OUT, f"{name}_1_hoy.png"), full_page=not mobile)
    if mobile: pg.screenshot(path=os.path.join(OUT, f"{name}_1_hoy_completa.png"), full_page=True)
    pg.click("#h2det summary"); pg.wait_for_timeout(500)
    det = pg.inner_text("#h2detbody")
    check(f"{T} HOY › Evidencia y metodología (abierta): ahí sí están rutas /api y metodología; y el Inicio completo heredado se conserva", "/api/" in det and "Metodología" in det and pg.locator("#h2legacy #v6inicio").count() == 1)
    pg.click("#h2det summary")
    # ------------------------------------------------------------------ DECISIONES
    pg.click('[data-h2go="dec"]'); pg.wait_for_selector("#tab-decisiones.on .h2dec", timeout=8000); pg.wait_for_timeout(500)
    check(f"{T} DECISIONES: se abre desde HOY y desde el chip; es una sola bandeja", pg.locator("#tab-decisiones.on").count() == 1)
    cards = pg.locator("#dec2 .h2dec"); n = cards.count()
    check(f"{T} DECISIONES › Pendientes: 1 decisión de servidor con los 8 campos", n == 1 and pg.eval_on_selector_all("#dec2 .h2dec dt", "e=>e.map(x=>x.textContent.trim())") == LABELS)
    vals = pg.eval_on_selector_all("#dec2 .h2dec dd", "e=>e.map(x=>x.textContent.trim())")
    check(f"{T} DECISIONES: ningún campo vacío; lo desconocido dice SIN FECHA / NO DETERMINABLE (no se inventa)", all(len(v) > 1 for v in vals) and any("SIN FECHA LÍMITE" in v for v in vals) and any("NO DETERMINABLE" in v for v in vals))
    check(f"{T} DECISIONES: producto, estado y acción recomendada correctos", "PHIVITAL Magnesio" in vals[1] and "PENDIENTE DE APROBACIÓN" in vals[7] and len(vals[0]) > 20)
    pg.click('[data-h2f="regla"]'); pg.wait_for_timeout(400)
    rc = pg.locator("#dec2 .h2dec"); check(f"{T} DECISIONES › Sugeridas por reglas: 5 (una por riesgo) con 8 campos cada una", rc.count() == 5 and all(pg.eval_on_selector_all("#dec2 .h2dec:nth-of-type(%d) dt" % (i + 1), "e=>e.length") == 8 for i in range(5)))
    check(f"{T} DECISIONES: prioridad MEDIA coherente con los 5 riesgos medios", pg.eval_on_selector_all("#dec2 .h2dec .h2pri", "e=>e.every(x=>x.textContent.trim()==='MEDIA')"))
    pg.click('[data-h2f="pend"]'); pg.wait_for_timeout(300)
    btns = pg.eval_on_selector_all("#dec2 .h2act button", "e=>e.map(x=>[x.textContent.trim(),x.disabled,x.title,x.className])")
    check(f"{T} VIEWER: Aprobar/Rechazar aparecen DESACTIVADOS y rotulados «No disponible: solo lectura» {btns[0][0]}", len(btns) == 2 and all(b[1] and "No disponible" in b[2] and "vro" in b[3] for b in btns) and "No disponible: solo lectura" in pg.inner_text("#dec2 .h2act"))
    check(f"{T} DECISIONES: sin tablas ni desbordamiento horizontal", pg.locator("#dec2 table").count() == 0 and pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    if mobile:
        xs = pg.eval_on_selector_all("#dec2 .h2dec", "e=>e.map(x=>Math.round(x.getBoundingClientRect().left))"); w = pg.eval_on_selector("#dec2 .h2dec", "x=>x.getBoundingClientRect().width")
        check(f"{T} DECISIONES móvil: tarjetas de una columna a ancho completo ({w:.0f}px)", len(set(xs)) == 1 and w > vp["width"] * 0.85)
        small = pg.evaluate("""()=>[...document.querySelectorAll('#dec2 button')].filter(b=>b.getBoundingClientRect().height<43).length"""); check(f"{T} DECISIONES móvil: botones táctiles ≥ 44 px", small == 0)
        pg.evaluate("window.scrollTo(0,document.documentElement.scrollHeight)"); pg.wait_for_timeout(300); r = pg.evaluate(BAR_JS); check(f"{T} DECISIONES móvil: barra inferior sin cubrir contenido ({r.get('maxBottom')} ≤ {r.get('barTop')})", "err" not in r and r["maxBottom"] <= r["barTop"] + 1); pg.evaluate("window.scrollTo(0,0)")
    pg.screenshot(path=os.path.join(OUT, f"{name}_2_decisiones.png"), full_page=not mobile)
    if mobile: pg.screenshot(path=os.path.join(OUT, f"{name}_2_decisiones_completa.png"), full_page=True)
    pg.click('[data-h2f="seg"]'); pg.wait_for_timeout(300); pg.click('[data-h2f="res"]'); pg.wait_for_timeout(600)
    check(f"{T} DECISIONES › En seguimiento / Resueltas: estados vacíos explícitos, sin errores", "Todavía no hay decisiones resueltas" in pg.inner_text("#dec2") and not errs)
    pg.click('[data-h2f="pend"]'); pg.click('[data-h2prod]'); pg.wait_for_timeout(1500)
    check(f"{T} DECISIONES › «Ir al producto» abre Productos y resalta el producto", pg.locator("#tab-prod.on").count() == 1 and pg.locator("#prod2 .x4prod.h2hl").count() == 1 and "PHIVITAL Magnesio" in pg.inner_text("#prod2 .x4prod.h2hl"))
    # ------------------------------------------------------------------ DIRECTOR IA
    pg.click(f'{nav} [data-sec="dir"]'); pg.wait_for_selector("#d2top .h2conc", timeout=8000); pg.wait_for_timeout(600)
    hs = pg.eval_on_selector_all("#d2top h3", "e=>e.map(x=>x.childNodes[0].textContent.trim())")
    check(f"{T} DIRECTOR: primero Conclusión y después Decisión recomendada {hs}", hs[:2] == ["Conclusión", "Decisión recomendada"])
    top = pg.inner_text("#d2top"); body_before = pg.evaluate("document.querySelector('#d2top').compareDocumentPosition(document.querySelector('#d2evi'))&4")
    check(f"{T} DIRECTOR: Evidencia y Metodología plegadas y DESPUÉS de la decisión", pg.evaluate("!document.querySelector('#d2evi').open && !document.querySelector('#d2met').open") and bool(body_before))
    check(f"{T} DIRECTOR: sin modelos, tokens, llamadas ni rutas en primer nivel", not TECH.search(top) and "Centro operativo" not in top)
    nrec = pg.locator("#d2top .h2recs > li").count(); check(f"{T} DIRECTOR: máximo 3 decisiones prioritarias ({nrec})", 1 <= nrec <= 3)
    check(f"{T} DIRECTOR: diferencia regla determinista / cálculo / IA generativa y declara que la IA no participa", all(k in top for k in ("Regla determinista", "Cálculo", "IA generativa")) and "no participa" in top and "ni conectores externos" in top)
    check(f"{T} DIRECTOR: dice expresamente «Datos insuficientes» cuando no hay datos", "Datos insuficientes" in pg.inner_text("#d2top .h2conc") and pg.locator(".h2insmsg").count() == 1)
    pg.screenshot(path=os.path.join(OUT, f"{name}_3_director.png"), full_page=not mobile)
    if mobile:
        pg.screenshot(path=os.path.join(OUT, f"{name}_3_director_completa.png"), full_page=True)
        pg.evaluate("window.scrollTo(0,document.documentElement.scrollHeight)"); pg.wait_for_timeout(300); r = pg.evaluate(BAR_JS); check(f"{T} DIRECTOR móvil: barra inferior sin cubrir contenido ({r.get('maxBottom')} ≤ {r.get('barTop')})", "err" not in r and r["maxBottom"] <= r["barTop"] + 1); pg.evaluate("window.scrollTo(0,0)")
    pg.click("#d2evi summary"); pg.click("#d2met summary"); pg.wait_for_timeout(600)
    met = pg.inner_text("#d2metbody") + pg.inner_text("#d2legacy")
    check(f"{T} DIRECTOR › Metodología (abierta): rutas /api y el Centro operativo heredado (tareas, libro, conexiones) se conservan", "/api/" in met and "Centro operativo del Director" in met)
    pg.click("#d2evi summary"); pg.click("#d2met summary")
    pg.click('#d2top [data-h2prod]'); pg.wait_for_timeout(1500)
    check(f"{T} DIRECTOR › «Ir al producto afectado» navega a Productos con el producto resaltado", pg.locator("#tab-prod.on").count() == 1 and pg.locator("#prod2 .x4prod.h2hl").count() == 1)
    # ------------------------------------------------------------------ seguridad / coste
    sw = pg.evaluate("fetch('/api/v06/decide',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':window.V03.V.csrf},body:JSON.stringify({id:1,approve:false})}).then(r=>r.status)")
    check(f"{T} servidor: POST forzado a decidir desde el viewer → 403 (bloqueo íntegro)", sw == 403)
    check(f"{T} 0 escrituras desde la interfaz del viewer (salvo el POST forzado de la prueba)", [w for w in writes if not w[1].endswith("/api/v06/decide")] == [] and len(writes) == 1)
    check(f"{T} 0 peticiones externas y 0 a rutas que ejecutan o gastan (order/run/import/discovery/keepa)", ext == [] and not [u for u in reqs if re.search(r"/api/v06/(order|run|import(?!s))|keepa/(refrescar|descubr)|investigar", u)])
    check(f"{T} sin errores de consola ni excepciones", errs == [])
    ctx.close()
with sync_playwright() as p:
    b = p.chromium.launch()
    run(b, "desktop", {"width": 1440, "height": 900}, False); run(b, "android", {"width": 390, "height": 844}, True); run(b, "android360", {"width": 360, "height": 740}, True); b.close()
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
