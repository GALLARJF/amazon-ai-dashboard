"""P0 Fase 3.1 · AISLAMIENTO ESTRICTO POR PRODUCTO (prueba de contaminación cruzada con datos CENTINELA).
Cada producto recibe valores únicos (stock, coste, PVP, documento, competidor, ASIN). Se recorren los 4 niveles de cada expediente (con todo abierto, incluido el legado y el panel V0.7)
y se demuestra que ningún valor, competidor, coste, stock, documento o nombre de un producto aparece en otro. También: acordeones móviles, indicador de producto activo y coherencia del estado."""
import json, os, re, sys, tempfile, threading, time, urllib.request, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "fase3_1", "despues"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def call(p, b=None, csrf=""):
    r = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}); return json.loads(op.open(r).read())
_call0 = call
def call(*a, **k):   # siembra de datos de prueba: solo aquí se levanta, un instante, el bloqueo de escritura de staging (el servidor lo aplica a todos los roles)
    S.STAGING = False
    try: return _call0(*a, **k)
    finally: S.STAGING = True
csrf = call("/api/login", {"username": "admin", "password": "admin-pass-p9Zt4w"})["csrf"]; call("/api/v06/order", {"product": "PRD-PHIVITAL-MAGNESIO"}, csrf)
ACT, MAG, OME = "PRD-ACTIVCORE-V2", "PRD-PHIVITAL-MAGNESIO", "PRD-PHIVITAL-OMEGA3"
# ---- centinelas: valores únicos por producto (los de OMEGA no incluyen competidor: su benchmark propio debe seguir SIN DATOS aunque los otros dos tengan)
SEN = {ACT: dict(stock=71011, cogs=7.71, pvp=71.71, doc="SENT-ACT-DOC-ALFA", asin="B0SENTAC01", brand="SENTACTBRAND", price=71.77),
       MAG: dict(stock=72022, cogs=7.22, pvp=72.72, doc="SENT-MAG-DOC-BETA", asin="B0SENTMG01", brand="SENTMAGBRAND", price=72.77),
       OME: dict(stock=73033, cogs=7.33, pvp=73.73, doc="SENT-OME-DOC-GAMA", asin=None, brand=None, price=None)}
def seed(pid, d):
    f = lambda v: {"v": v, "status": "DOCUMENTADO", "source": "Centinela de prueba de aislamiento", "date": "2026-11-20"}
    call("/api/catalog/update", {"id": pid, "patch": {"stock": f(d["stock"]), "costs": {"cogs": f(d["cogs"])}, "pvp": {"REF": f(d["pvp"])}, "documents": [{"name": d["doc"], "type": "CENTINELA", "date": "2026-11-20", "ref": "ref-" + d["doc"]}]}, "note": "centinela"}, csrf)
def seed_comp(pid, d):
    rec = {"country": "ES", "marketplace": "amazon.es", "asin": d["asin"], "brand": d["brand"], "title": d["brand"] + " competidor", "url": "", "volume_ml": 100, "units": 1, "volume_source": "titulo", "price": d["price"], "currency": "EUR", "price_source": "centinela", "price_list": None, "bsr": 1234, "bsr_category_name": "x", "bsr_date": "2026-11-20", "rating": None, "reviews": None, "fetched_at": time.time()}
    S.APP["keepa"]._cache_put(9, d["asin"], "search", rec)
    if pid != ACT: S.svc_for(pid).register_candidate("ES", d["asin"], "ALTA", 90, "centinela", "test", "test")
for pid, d in SEN.items(): seed(pid, d)
NAME = {ACT: "ACTIVCORE", MAG: "Magnesio", OME: "Omega-3"}
def login(pg):
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
    pg.evaluate("NAV6.go('lanz',0)"); pg.wait_for_selector("#lanz2 .lzc", timeout=10000); pg.wait_for_timeout(800)
def prog(pg, pid): return re.search(r"(\d+) de 10 completos · (\d+) parciales", pg.locator(f'[data-lz-card="{pid}"]').inner_text()).groups()
def open_all(pg):
    """Abre los 4 niveles y todo lo desplegable (pasos, secciones v0.7) para que el texto del DOM sea el máximo posible."""
    pg.evaluate("document.querySelectorAll('#lanz2 details').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#lanz2 button.v7-toggle').forEach(b=>{b.click()})"); pg.wait_for_timeout(300)
def pick(pg, pid): pg.click(f'[data-lz-open="{pid}"]'); pg.wait_for_function("(p)=>document.querySelector('[data-lz-detail]')&&document.querySelector('[data-lz-detail]').dataset.lzDetail===p&&!!document.querySelector('#lzlegacy section.v7[data-product=\"'+p+'\"] .v7-keepa')", arg=pid, timeout=15000); pg.wait_for_timeout(700)
def tokens(pid, d): return [str(d["stock"]), d["doc"], f"{d['pvp']:.2f}".replace(".", ","), f"{d['cogs']:.2f}".replace(".", ",")] + ([d["asin"], d["brand"], f"{d['price']:.2f}".replace(".", ",")] if d["asin"] else [])
with sync_playwright() as p:
    b = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])
    # ---------- etapa 1: sin competidores en ningún producto -> progreso base de cada tarjeta
    ctx = b.new_context(viewport={"width": 1440, "height": 900}); pg = ctx.new_page(); login(pg); base = {pid: prog(pg, pid) for pid in SEN}; ctx.close()
    seed_comp(ACT, SEN[ACT]); seed_comp(MAG, SEN[MAG])
    for name, vp, mob in (("desktop", {"width": 1440, "height": 900}, False), ("android", {"width": 390, "height": 844}, True), ("android360", {"width": 360, "height": 740}, True)):
        ctx = b.new_context(viewport=vp, device_scale_factor=1, is_mobile=mob, has_touch=mob); pg = ctx.new_page(); errs = []; T = f"[{name}]"
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
        login(pg)
        # ---------- coherencia de estado y progreso (item 4)
        now = {pid: prog(pg, pid) for pid in SEN}
        check(f"{T} 4 · el benchmark de otro producto NO cuenta como evidencia: el progreso de OMEGA no cambia {base[OME]} → {now[OME]}", base[OME] == now[OME])
        check(f"{T} 4 · el progreso de ACTIVCORE y MAGNESIO sí cambia con SU propio benchmark (parciales {base[ACT][1]}→{now[ACT][1]}, {base[MAG][1]}→{now[MAG][1]})", int(now[ACT][1]) == int(base[ACT][1]) + 1 and int(now[MAG][1]) == int(base[MAG][1]) + 1)
        for pid in SEN:
            pick(pg, pid); pg.screenshot(path=os.path.join(OUT, f"{name}_{NAME[pid].lower().replace('-', '')}_inicial.png"), full_page=True); open_all(pg); T2 = f"{T} {NAME[pid]}"
            txt = pg.evaluate("document.querySelector('.lzdet').textContent"); bench = pg.evaluate("document.querySelector('[data-lz-step=benchmark]').textContent")
            own = tokens(pid, SEN[pid]); missing_own = [t for t in own if t not in txt]
            check(f"{T2} sus propios centinelas SÍ aparecen en el expediente (no es una prueba vacía): faltan {missing_own}", not missing_own)
            leaks = {o: [t for t in tokens(o, SEN[o]) if t in txt] for o in SEN if o != pid}; names = [NAME[o] for o in SEN if o != pid and NAME[o] not in {"Magnesio", "Omega-3"} or (o != pid and pid == ACT)]
            check(f"{T2} niveles 1-4 + legado + panel V0.7: NINGÚN centinela de otro producto {leaks}", all(not v for v in leaks.values()))
            nm = [NAME[o] for o in SEN if o != pid and NAME[o] not in pg.inner_text('[data-lz-detail] .lzl1').split("·")[0]]
            check(f"{T2} ningún nombre de otro producto dentro del expediente ({[n for n in nm if n in txt]})", not [n for n in nm if n in txt])
            lvl = {l: pg.evaluate(f"(document.querySelector('[data-lz-level=\"{l}\"]')||{{}}).textContent||''") for l in "1234"}
            check(f"{T2} cada uno de los 4 niveles por separado está libre de otros productos", all(not any(t in lvl[l] for o in SEN if o != pid for t in tokens(o, SEN[o])) for l in lvl) and all(lvl[l] for l in lvl))
            if pid == OME: check(f"{T2} sin benchmark propio: «SIN DATOS» (aunque ACTIVCORE y MAGNESIO sí tengan competidores)", "Competidores con datos\n" in bench.replace("Competidores con datos", "Competidores con datos\n") and re.search(r"Competidores con datos\s*0", bench) and "SIN DATOS" in bench)
            else: check(f"{T2} benchmark propio con su competidor centinela {SEN[pid]['asin']}", SEN[pid]["asin"] in txt and re.search(r"Competidores con datos\s*[1-9]", bench))
            k = pg.evaluate("(document.querySelector('#lzlegacy section.v7 .v7-keepa')||{}).textContent||''")
            if pid != ACT: check(f"{T2} panel Keepa del legado: SIN DATOS propio, sin competidores ni nombres de ACTIVCORE", "SIN DATOS" in k and "ACTIVCORE" not in k and "<table" not in pg.evaluate("document.querySelector('#lzlegacy section.v7 .v7-keepa').innerHTML"))
            sel = pg.evaluate("document.querySelectorAll('#lzlegacy select[data-v6prod]').length"); check(f"{T2} el selector legacy que lista a otros productos no está en el expediente ({sel})", sel == 0)
            check(f"{T2} indicador «Producto activo» = {NAME[pid]}", NAME[pid] in pg.inner_text(".lzactive"))
            ref = pg.inner_text('[data-lz-level="1"]'); check(f"{T2} datos de cuenta separados: enlace rotulado «Fuente general de la cuenta»", pg.locator("[data-lz-scope] [data-lz-general]").count() == 1 and "no son de este producto" in pg.evaluate("document.querySelector('[data-lz-scope]').textContent"))
            # conmutación rápida: A → B → A no deja restos
            if pid == MAG:
                pg.click(f'[data-lz-open="{ACT}"]'); pg.click(f'[data-lz-open="{OME}"]'); pg.wait_for_timeout(5000); open_all(pg); t3 = pg.evaluate("document.querySelector('.lzdet').textContent")
                check(f"{T2} cambios rápidos ACTIVCORE→OMEGA no dejan restos de ACTIVCORE/MAGNESIO ({[x for x in tokens(ACT, SEN[ACT]) + tokens(MAG, SEN[MAG]) if x in t3]})", not [x for x in tokens(ACT, SEN[ACT]) + tokens(MAG, SEN[MAG]) if x in t3] and pg.locator("#lzlegacy section.v7").count() == 1 and pg.get_attribute("#lzlegacy section.v7", "data-product") == OME)
            if pid == OME or True: pg.screenshot(path=os.path.join(OUT, f"{name}_{NAME[pid].lower().replace('-', '')}_expediente.png"), full_page=True) if (mob or pid) else None
        # ---------- acordeones móviles (item 3)
        if mob:
            pick(pg, ACT); pg.evaluate("document.querySelectorAll('#lanz2 details').forEach(d=>d.open=false)"); pg.wait_for_timeout(300)
            st = pg.evaluate("[document.querySelector('#lzevi').open, document.querySelector('#lzmet').open]"); check(f"{T} 3 · Evidencia y Metodología inician cerradas {st}", st == [False, False])
            pg.click("#lzmet > summary"); pg.wait_for_timeout(300); st = pg.evaluate("[document.querySelector('#lzevi').open, document.querySelector('#lzmet').open]")
            pg.click("#lzevi > summary"); pg.wait_for_timeout(300); st2 = pg.evaluate("[document.querySelector('#lzevi').open, document.querySelector('#lzmet').open]")
            pg.click("#lzmet > summary"); pg.wait_for_timeout(300); st3 = pg.evaluate("[document.querySelector('#lzevi').open, document.querySelector('#lzmet').open]")
            check(f"{T} 3 · abrir Metodología cierra Evidencia ({st}) y abrir Evidencia cierra Metodología ({st2}) y viceversa ({st3})", st == [False, True] and st2 == [True, False] and st3 == [False, True])
            hs = {}
            for lv in ("lzevi", "lzmet"):
                pg.evaluate("document.querySelectorAll('#lanz2 details').forEach(d=>d.open=false)"); pg.click(f"#{lv} > summary")
                if lv == "lzevi": pg.evaluate("document.querySelectorAll('#lanz2 .lzstep').forEach(d=>d.open=true)")
                else: pg.click("#lzorig > summary")
                pg.wait_for_timeout(500); hs[lv] = pg.evaluate("document.documentElement.scrollHeight")
            pg.evaluate("document.querySelectorAll('#lanz2 button.v7-toggle').forEach(b=>b.click())"); pg.wait_for_timeout(400); extremo = pg.evaluate("document.documentElement.scrollHeight")
            check(f"{T} 3 · con cada nivel abierto (Evidencia con los 10 pasos; Metodología con las secciones originales) la página mide {hs} ≤ 10.000 px (extremo, con todos los desplegables del panel V0.7: {extremo})", max(hs.values()) <= 10000)
            both = pg.evaluate("document.querySelectorAll('#lanz2 details').forEach(d=>d.open=true); document.documentElement.scrollHeight"); pg.evaluate("document.querySelectorAll('#lanz2 details').forEach(d=>d.open=false)")
            check(f"{T} 3 · toda la información sigue accesible (los dos niveles se abren de uno en uno; ambos juntos por código mediría {both})", pg.locator("#lzevi .lzstep").count() == 10 and pg.locator("#lzlegacy #v6lanz .v6sec").count() == 11)
            pg.click("#lzevi > summary"); pg.wait_for_timeout(300); pg.evaluate("window.scrollTo(0, 1800)"); pg.wait_for_timeout(300)
            ind = pg.evaluate("(()=>{const r=document.querySelector('.lzactive').getBoundingClientRect();return [Math.round(r.top),Math.round(r.height),innerHeight]})()")
            check(f"{T} 3 · el indicador del producto activo permanece visible al desplazarse {ind}", ind[0] >= 0 and ind[0] < 60 and ind[1] >= 43 and "ACTIVCORE" in pg.inner_text(".lzactive"))
            pg.screenshot(path=os.path.join(OUT, f"{name}_evidencia_con_indicador.png"))
            m = pg.evaluate("[scrollX, document.documentElement.scrollWidth, innerWidth]"); check(f"{T} sin desplazamiento horizontal {m}", m[0] == 0 and m[1] <= m[2])
        check(f"{T} sin errores de consola", errs == []); ctx.close()
    # ---------- lógica de estado (item 4): sin comparabilidad confirmada no hay GO
    pg = b.new_context().new_page(); pg.goto(f"http://localhost:{port}/"); pg.wait_for_function("window.LANZ2")
    r = pg.evaluate("""()=>{const mk=(cmp)=>({sections:[{id:'economia',rows:[{contribution:3,margin:.2}]},{id:'cumplimiento',open:0,ok:12},{id:'paises',ranking:[1]},{id:'competidores',rows:cmp},{id:'recomendacion',verdict:'EVALUAR POR PAÍSES',reasons:[]}]});
      const st=[{id:'economia',state:'OK'}]; const f=(c)=>LANZ2._statusOf(mk(c),st).v;
      return {sin:f([]), auto:f([{estado_comparabilidad:'AUTOMATICA'}]), mixto:f([{estado_comparabilidad:'CONFIRMADA'},{estado_comparabilidad:'SUGERIDA'}]), conf:f([{estado_comparabilidad:'CONFIRMADA'},{estado_comparabilidad:'CONFIRMADA'}])}}""")
    check(f"estado · sin competidores o sin comparabilidad confirmada NUNCA es GO ({r})", r["sin"] == "REVISAR" and r["auto"] == "REVISAR" and r["mixto"] == "REVISAR" and r["conf"] == "GO")
    r2 = pg.evaluate("""()=>{const S=LANZ2._stepsOf({sections:[{id:'economia',rows:[]},{id:'competidores',rows:[]},{id:'cumplimiento'},{id:'recomendacion',reasons:[]},{id:'ficha',missing:[]},{id:'europa',countries:[]}]},{id:'X',name:'X',brand:'X',pvp:{},costs:{},stock:{v:null},documents:[],images:[]});
      return {eco:S.find(s=>s.id==='economia').state, pre:S.find(s=>s.id==='precio').state, stock:S.find(s=>s.id==='stock').state, line:S.find(s=>s.id==='stock').lines[0][1]}}""")
    check(f"estado · SIN DATOS no se convierte en cero: economía/precio/stock SIN DATOS y stock «{r2['line']}»", r2["eco"] == "SIN DATOS" and r2["pre"] == "SIN DATOS" and r2["stock"] == "SIN DATOS" and "0 uds" not in r2["line"] and "SIN DATOS" in r2["line"])
    b.close()
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
