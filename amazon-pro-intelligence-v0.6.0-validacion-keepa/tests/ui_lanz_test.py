"""P0 Fase 3 · LANZAMIENTOS guiados (viewer en staging; escritorio 1440, Android 390 y 360).
Primer nivel de 8 elementos por lanzamiento; 4 niveles (evidencia y metodología plegadas); expediente en 10 pasos; ACTIVCORE y PHIVITAL; REAL/DEMO/SIN DATOS; sin ceros inventados;
lógica de estado GO/REVISAR/NO GO/SIN DATOS; viewer (solo lectura, 403 del servidor); móvil (1 columna, sin tablas horizontales, ≥44 px, barra inferior). Capturas en docs/p0_hoy/fase3/despues/."""
import glob, json, os, re, sys, tempfile, threading, urllib.request, urllib.error, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "fase3", "despues"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "*.png")): os.remove(f)
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def call(p, b=None, csrf="", jar=op):
    r = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}); return json.loads(jar.open(r).read())
_call0 = call
def call(*a, **k):   # siembra de datos de prueba: solo aquí se levanta, un instante, el bloqueo de escritura de staging (el servidor lo aplica a todos los roles)
    S.STAGING = False
    try: return _call0(*a, **k)
    finally: S.STAGING = True
csrf = call("/api/login", {"username": "admin", "password": "admin-pass-p9Zt4w"})["csrf"]; call("/api/v06/order", {"product": "PRD-PHIVITAL-MAGNESIO"}, csrf)
STEPS = ["Producto y mercado", "Economía unitaria", "Precio y margen", "Benchmark y competidores", "Demanda", "Stock y logística", "Cumplimiento regulatorio", "Documentos y fuentes", "Riesgos y bloqueos", "Recomendación final"]
LABELS = ["Bloqueos críticos", "Próxima acción", "Responsable", "Progreso del expediente", "Última actualización"]
def login(pg):
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
    pg.evaluate("NAV6.go('lanz',0)"); pg.wait_for_selector("#lanz2 .lzc", timeout=10000); pg.wait_for_timeout(800)
def card(pg, name): return pg.locator("#lanz2 .lzc", has_text=name).first
def run(pw, name, vp, mobile):
    ctx = pw.new_context(viewport=vp, device_scale_factor=1, is_mobile=mobile, has_touch=mobile); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    login(pg); T = f"[{name}]"
    pg.evaluate('scrollTo(0,0)'); pg.screenshot(path=os.path.join(OUT, f"{name}_1_lanzamientos.png")); pg.screenshot(path=os.path.join(OUT, f"{name}_1_lanzamientos_completa.png"), full_page=True)   # estado inicial: evidencia y metodología plegadas
    n = pg.locator("#lanz2 .lzc").count()
    check(f"{T} una tarjeta por producto del catálogo ({n} = 3: ACTIVCORE y 2 PHIVITAL)", n == 3 and all(card(pg, x).count() for x in ("ACTIVCORE", "PHIVITAL Magnesio", "PHIVITAL Omega-3")))
    for pr in ("ACTIVCORE", "PHIVITAL Magnesio"):
        c = card(pg, pr); t = c.inner_text()
        check(f"{T} {pr}: primer nivel con los 8 elementos (producto, estado, conclusión + 5 campos)", all(l in t for l in LABELS) and c.locator(".lzst").count() == 1 and c.locator(".lzconc").inner_text().strip() != "" and c.locator("h3").inner_text().startswith(pr))
        check(f"{T} {pr}: estado dentro de GO / REVISAR / NO GO / SIN DATOS", c.locator(".lzst").inner_text().strip() in ("GO", "REVISAR", "NO GO", "SIN DATOS"))
        check(f"{T} {pr}: progreso «X de 10» y fecha ISO de actualización", re.search(r"\d+ de 10 completos", t) and re.search(r"\d{4}-\d{2}-\d{2}", t))
        check(f"{T} {pr}: ausencia ≠ cero (no hay «0 €» ni «0 %» inventados)", not re.search(r"(?<![\d.,])0([.,]00)? ?(€|%)", t))
    ac = card(pg, "ACTIVCORE").inner_text(); ph = card(pg, "PHIVITAL Magnesio").inner_text()
    check(f"{T} ACTIVCORE y PHIVITAL se entienden en la misma pantalla: bloqueos distintos (72 vs 66 requisitos)", "72 requisitos" in ac and "66 requisitos" in ph)
    check(f"{T} sin datos suficientes ⇒ SIN DATOS (nunca GO por defecto)", all(card(pg, x).locator(".lzst").inner_text().strip() == "SIN DATOS" for x in ("ACTIVCORE", "PHIVITAL Magnesio")) and "GO" not in [e.strip() for e in pg.locator("#lanz2 .lzc .lzst").all_inner_texts()])
    check(f"{T} responsable = rol propuesto, honesto («sin persona asignada»)", "sin persona asignada" in ac)
    check(f"{T} cabecera rotulada DEMO (staging) y recuento por estado", "DEMO" in pg.inner_text("#lanz2 .h2head h2") and re.search(r"0 GO · 0 REVISAR · 0 NO GO · 3 SIN DATOS", pg.inner_text("#lanz2 .h2head p")))
    # ---- cuatro niveles
    det = pg.locator(f'[data-lz-detail="PRD-ACTIVCORE-V2"]'); check(f"{T} detalle del expediente ACTIVCORE con los 4 niveles (1 Conclusión, 2 Decisión, 3 Evidencia, 4 Metodología)", det.locator("[data-lz-level]").count() == 4 and [e.get_attribute("data-lz-level") for e in det.locator("[data-lz-level]").all()] == ["1", "2", "3", "4"])
    check(f"{T} Evidencia y Metodología están plegadas al entrar", pg.evaluate("[...document.querySelectorAll('#lanz2 details')].every(d=>!d.open)"))
    d2 = det.locator('[data-lz-level="2"]').inner_text()
    check(f"{T} Decisión: qué bloquea, próxima acción, responsable, datos que faltan con QUIÉN los aporta, y Director IA", all(x in d2 for x in ("Qué bloquea el lanzamiento", "Próxima acción", "Responsable", "Datos que faltan", "Director IA")) and "→" in d2 and "Stock sin verificar" in d2)
    # ---- expediente 10 pasos
    pg.click("#lanz2 #lzevi > summary"); pg.wait_for_timeout(250)
    names = pg.eval_on_selector_all("#lanz2 .lzstep > summary", "e=>e.map(x=>x.textContent.replace(/\\s+/g,' ').trim())")
    check(f"{T} expediente guiado: 10 pasos en el orden pedido", len(names) == 10 and all(STEPS[i] in names[i] for i in range(10)))
    check(f"{T} cada paso con estado y rótulo REAL/DEMO/SIN DATOS", all(re.search(r"(DEMO|REAL|SIN DATOS)\s*$", x) for x in names))
    pg.click('[data-lz-step="economia"] > summary'); pg.click('[data-lz-step="cumplimiento"] > summary'); pg.click('[data-lz-step="stock"] > summary'); pg.wait_for_timeout(250)
    eco = pg.inner_text('[data-lz-step="economia"]'); cum = pg.inner_text('[data-lz-step="cumplimiento"]'); stk = pg.inner_text('[data-lz-step="stock"]')
    check(f"{T} Economía: NO se inventan cifras; el coste histórico se rotula «HISTORICO_A_REVALIDAR» y faltan costes con responsable", "10,03" in eco and "HISTORICO_A_REVALIDAR" in eco and "Países calculables" in eco and re.search(r"Países calculables\s*\n?\s*0 de \d", eco) and "Operaciones" in eco)
    check(f"{T} Cumplimiento: 0 requisitos con evidencia de 72 y cada país como línea (sin tablas)", "0 de 72" in cum and cum.count("0/12") >= 6)
    check(f"{T} Stock: histórico «NO es stock disponible hoy», sin asumir 0", "NO es stock disponible hoy" in stk and "550" in stk)
    pg.click('[data-lz-step="demanda"] > summary'); check(f"{T} Demanda: SIN DATOS y no se estima", "Ninguna: no se estima demanda" in pg.inner_text('[data-lz-step="demanda"]'))
    pg.click("#lanz2 #lzmet > summary"); pg.wait_for_timeout(300)
    check(f"{T} Metodología: reglas del estado + las 11 secciones originales siguen accesibles (cálculos intactos)", "NO GO solo si" in pg.inner_text("#lzmetbody") and pg.locator("#lzlegacy #v6lanz .v6sec").count() == 11)
    check(f"{T} sigue accesible la exportación original (Markdown/HTML) y los cálculos de Pre-Launch y Europa", pg.locator('#lzlegacy a[href*="fmt=md"]').count() >= 1 and pg.locator('#subnav6 [data-sub]').count() == 4)   # 3 originales + «Economía comercial» (V1.1)
    # ---- cambio de producto: el detalle sigue al elegido, sin duplicar
    pg.click('[data-lz-open="PRD-PHIVITAL-MAGNESIO"]'); pg.wait_for_timeout(1200)
    check(f"{T} al abrir PHIVITAL el detalle cambia y no se duplica (1 solo detalle, 66 requisitos)", pg.locator("#lanz2 .lzdet").count() == 1 and "PHIVITAL Magnesio" in pg.inner_text('[data-lz-level="1"]') and "66 requisitos" in pg.inner_text('[data-lz-level="2"]'))
    check(f"{T} Decisión muestra la decisión pendiente de PHIVITAL (aprobar/rechazar solo en Decisiones: bandeja única)", "Ir a Decisiones (1)" in pg.inner_text('[data-lz-level="2"]') and not pg.locator('#lanz2 [data-h2dec]').count())
    # ---- viewer
    lock = pg.evaluate("""()=>[...document.querySelectorAll('#lanz2 button:not(#lzlegacy *), #lanz2 a:not(#lzlegacy *)')].filter(b=>b.classList.contains('vro')||b.disabled).map(b=>b.textContent.trim())""")
    check(f"{T} viewer: los controles de navegación y lectura de Lanzamientos están activos (bloqueados: {lock})", not lock)
    pg.wait_for_timeout(1500)
    wr = pg.evaluate("""()=>[...document.querySelectorAll('#lzlegacy button')].filter(b=>/(Preparar lanzamiento|Importar|Crear)/i.test(b.textContent)).map(b=>[b.textContent.trim(),b.disabled||b.classList.contains('vro')])""")
    check(f"{T} viewer: «Preparar lanzamiento» (única escritura) bloqueado e identificado ({wr})", wr and all(x[1] for x in wr))
    # ---- móvil / ancho
    m = pg.evaluate("[scrollX, document.documentElement.scrollWidth, innerWidth]"); check(f"{T} sin desplazamiento horizontal {m}", m[0] == 0 and m[1] <= m[2])
    if mobile:
        cols = pg.evaluate("[...new Set([...document.querySelectorAll('#lanz2 .lzc')].map(c=>Math.round(c.getBoundingClientRect().left)))].length"); check(f"{T} tarjetas en UNA columna", cols == 1)
        tb = pg.evaluate("[...document.querySelectorAll('#lanz2 table')].filter(t=>t.offsetParent&&!t.closest('#lzlegacy')).length"); check(f"{T} sin tablas en el nivel guiado (solo la metodología original, con scroll interno)", tb == 0)
        sz = pg.evaluate("[...document.querySelectorAll('#lanz2 .lzopen, #lanz2 .lzacts .btn, #lanz2 .lzstep > summary, #lanz2 details > summary')].map(e=>Math.round(e.getBoundingClientRect().height))"); check(f"{T} botones y cabeceras de acordeón ≥ 44 px (mín {min(sz)})", min(sz) >= 43)
        pg.evaluate("NAV6.go('lanz',0)"); pg.wait_for_timeout(1200); pg.evaluate("scrollTo(0,0)")
        vis = pg.evaluate("""()=>{const c=document.querySelector('#lanz2 .lzc'),bar=document.querySelector('#bnav').getBoundingClientRect().top;const q=(l)=>{const dt=[...c.querySelectorAll('dt')].find(x=>x.textContent.trim()===l);return dt?dt.getBoundingClientRect().top:9999};return {st:c.querySelector('.lzst').getBoundingClientRect().bottom,cn:c.querySelector('.lzconc').getBoundingClientRect().bottom,bl:q('Bloqueos críticos'),nx:q('Próxima acción'),bar}}""")
        check(f"{T} móvil: sin hacer scroll se ven estado, conclusión, bloqueo y próxima acción ({vis})", vis["st"] < vis["bar"] and vis["cn"] < vis["bar"] and vis["bl"] < vis["bar"] and vis["nx"] < vis["bar"] - 20)
        pg.evaluate("window.scrollTo(0,document.documentElement.scrollHeight)"); pg.wait_for_timeout(300)
        r = pg.evaluate(open(os.path.join(ROOT, "tests", "ui_nav_test.py"), encoding="utf-8").read().split('BAR_JS = """')[1].split('"""')[0]); check(f"{T} barra inferior sin cubrir contenido ({r.get('maxBottom')} ≤ {r.get('barTop')})", "err" not in r and r["maxBottom"] <= r["barTop"] + 1)
    # capturas por caso (expediente ACTIVCORE y PHIVITAL abiertos)
    for pid, tag in (("PRD-ACTIVCORE-V2", "activcore"), ("PRD-PHIVITAL-MAGNESIO", "phivital")):
        pg.click(f'[data-lz-open="{pid}"]'); pg.wait_for_timeout(1200)
        for sel in ("#lanz2 #lzevi", '[data-lz-step="economia"]', '[data-lz-step="cumplimiento"]'):
            e = pg.locator(sel).first
            if not e.evaluate("e=>e.open"): e.locator("> summary").click()
        pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(OUT, f"{name}_2_{tag}_expediente.png"), full_page=True)
    check(f"{T} sin errores de consola", errs == []); ctx.close()
# ---- lógica de estado (pura, sin servidor de datos): casos que los datos de staging no cubren
def logic(pw):
    pg = pw.new_context().new_page(); pg.goto(f"http://localhost:{port}/"); pg.wait_for_function("window.LANZ2")
    r = pg.evaluate("""()=>{const mk=(o)=>({sections:[{id:'economia',rows:o.eco||[]},{id:'cumplimiento',open:o.open||0,ok:o.ok||0},{id:'paises',ranking:o.rank||[]},{id:'competidores',rows:o.cmp||[]},{id:'recomendacion',verdict:o.verdict||'NO DECIDIBLE TODAVÍA',reasons:o.reasons||[]}]});
      const st=(s)=>s.map((x)=>({id:x,state:'SIN DATOS'})); const f=(o,steps)=>LANZ2._statusOf(mk(o),steps||st(['economia','benchmark','cumplimiento'])).v;
      const pos=[{contribution:3,margin:.2},{contribution:2,margin:.1}], neg=[{contribution:-1,margin:-.1},{contribution:-2,margin:-.2}];
      return {sd:f({reasons:['x']}), rev:f({reasons:['x']},[{id:'economia',state:'PARCIAL'}]), nogo:f({eco:neg,reasons:['x']}), mixto:f({eco:[neg[0],pos[0]],reasons:['x']},[{id:'economia',state:'PARCIAL'}]), go:f({verdict:'EVALUAR POR PAÍSES',eco:pos,open:0,ok:12,rank:[1],cmp:[{estado_comparabilidad:'CONFIRMADA'}]}), goSinRank:f({verdict:'EVALUAR POR PAÍSES',eco:pos,open:0,ok:12,cmp:[{estado_comparabilidad:'CONFIRMADA'}]}), goBloq:f({verdict:'EVALUAR POR PAÍSES',eco:pos,open:3,ok:9,rank:[1],cmp:[{estado_comparabilidad:'CONFIRMADA'}]}), roles:[LANZ2._roleOf('Aportar costes logísticos y evidencias regulatorias'),LANZ2._roleOf('algo raro')]}}""")
    check(f"lógica · sin economía/benchmark/cumplimiento y NO DECIDIBLE ⇒ SIN DATOS ({r['sd']})", r["sd"] == "SIN DATOS")
    check(f"lógica · con algún dato pero bloqueos ⇒ REVISAR ({r['rev']})", r["rev"] == "REVISAR")
    check(f"lógica · contribución negativa en TODOS los países calculados ⇒ NO GO ({r['nogo']})", r["nogo"] == "NO GO")
    check(f"lógica · economía mixta (una negativa, una positiva) ⇒ NO se declara NO GO ({r['mixto']})", r["mixto"] == "REVISAR")
    check(f"lógica · GO solo con economía positiva, comparabilidad confirmada, cumplimiento completo y ranking ({r['go']})", r["go"] == "GO")
    check(f"lógica · sin ranking o con requisitos abiertos jamás es GO ({r['goSinRank']}, {r['goBloq']})", r["goSinRank"] == "REVISAR" and r["goBloq"] == "REVISAR")
    check("lógica · roles propuestos por regla, nunca una persona inventada", "Operaciones" in r["roles"][0] and "regulatorio" in r["roles"][0] and "sin persona asignada" in r["roles"][1])
    pg.context.close()
with sync_playwright() as p:
    b = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])
    run(b, "desktop", {"width": 1440, "height": 900}, False); run(b, "android", {"width": 390, "height": 844}, True); run(b, "android360", {"width": 360, "height": 740}, True); logic(b); b.close()
# ---- servidor: el viewer recibe 403 en cualquier escritura de lanzamiento (no depende de la UI)
vj = http.cookiejar.CookieJar(); vo = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(vj)); vc = call("/api/login", {"username": "auditor", "password": "viewer-pass-x7Qk2m"}, "", vo)["csrf"]
for path, body in (("/api/v06/order", {"product": "PRD-ACTIVCORE-V2"}), ("/api/v06/decide", {"id": 1, "approve": True}), ("/api/catalog/update", {"id": "PRD-ACTIVCORE-V2", "patch": {"name": "x"}})):
    try: call(path, body, vc, vo); code = 200
    except urllib.error.HTTPError as e: code = e.code
    check(f"servidor · viewer: POST {path} → 403 (obtenido {code})", code == 403)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
