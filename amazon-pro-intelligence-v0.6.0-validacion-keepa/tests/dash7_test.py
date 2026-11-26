"""Rediseño fase 1 — Dashboard AHT simplificado: cálculo (node), navegación, filtros, auth/rol viewer, demo vs Sin datos, funciones internas preservadas, capturas 1920/1440/390."""
import json, os, re, socket, subprocess, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in list(os.environ):
    if k.startswith(("AMAZON_PRO_", "KEEPA_", "OPENAI_", "ANTHROPIC_")): os.environ.pop(k)
PW = "viewer-pass-x7Qk2m"
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR=PW, PLAYWRIGHT_BROWSERS_PATH=os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
EXT = []; _c = socket.socket.connect
def _nn(self, a, *x, **k):
    if a[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(a); raise AssertionError("RED PROHIBIDA")
    return _c(self, a, *x, **k)
socket.socket.connect = _nn
R = []
def check(n, c, e=""): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n + ((" → " + str(e)) if (e and not c) else ""))
# ---- cálculo puro (node)
js = """const D=require('./js/dash7calc.js');const o={};
o.base=D.compute({line:'all',period:'mes'});o.dia=D.compute({period:'dia'});o.anio=D.compute({period:'anio'});
o.lines=D.LINES.map(l=>D.compute({line:l.id,period:'mes'}));o.w=D.weighted(o.lines);o.avg=o.lines.reduce((a,x)=>a+x.contribPct,0)/o.lines.length;
o.subs=D.compute({line:'phivital',sub:'sup',period:'mes'});o.subs2=D.compute({line:'phivital',sub:'dep',period:'mes'});o.phi=D.compute({line:'phivital',period:'mes'});
o.cty=D.compute({region:'eu',country:'ES',period:'mes'});o.reg=D.compute({region:'eu',period:'mes'});o.na=D.compute({region:'am',period:'mes'});o.loss=D.compute({line:'all',period:'mes'});o.ser=D.series({},'bruto');o.sers=['bruto','neto','uds','ads','contrib','pct'].map(m=>JSON.stringify(D.series({},m)));o.fut=D.FUTURE.map(x=>x.id);o.regs=D.REGIONS.map(x=>x.id+':'+x.countries.map(c=>c.id).join(','));
o.empty=D.compute({line:'nada',period:'mes'});console.log(JSON.stringify(o));"""
o = json.loads(subprocess.check_output(["node", "-e", js], cwd=ROOT).decode()); b = o["base"]
check("ejemplo de dirección exacto: 49900 / 41239,67 / 1000 / 4990 / 8990 / 7485 / 5410 / 14364,67 / 34,83 %", (b["bruto"], b["neto"], b["uds"], b["ads"], b["fab"], b["com"], b["log"], b["contrib"], b["contribPct"]) == (49900, 41239.67, 1000, 4990, 8990, 7485, 5410, 14364.67, 34.83), b)
check("contribución = neto − fabricación − comisiones − logística − publicidad (sin overhead)", round(b["neto"] - b["fab"] - b["com"] - b["log"] - b["ads"], 2) == b["contrib"])
check("donut: 5 tramos que suman las ventas netas y el 100 %", len(b["donut"]) == 5 and round(sum(x["eur"] for x in b["donut"]), 2) == b["neto"] and abs(sum(x["pct"] for x in b["donut"]) - 100) < 0.05)
check("ratio ponderado sobre netas (no promedio de %): suma de líneas = consolidado y ≠ promedio simple", o["w"] == 34.83 and abs(o["avg"] - o["w"]) > 0.01 and round(sum(x["neto"] for x in o["lines"]), 2) == b["neto"], (o["w"], o["avg"]))
check("las 5 líneas AHT suman el consolidado en todas las magnitudes", all(round(sum(x[k] for x in o["lines"]), 2) == b[k] for k in ("bruto", "neto", "uds", "ads", "contrib")))
check("PHIVITAL: Suplementos + Nutrición deportiva = PHIVITAL", round(o["subs"]["neto"] + o["subs2"]["neto"], 2) == o["phi"]["neto"] and o["subs"]["uds"] + o["subs2"]["uds"] == o["phi"]["uds"])
check("Región/País: Europa + América = consolidado; España ⊂ Europa", round(o["reg"]["neto"] + o["na"]["neto"], 2) == b["neto"] and 0 < o["cty"]["neto"] < o["reg"]["neto"])
check("periodo: día = 1/30, año = ×12 del mes", abs(o["dia"]["neto"] - b["neto"] / 30) < 0.02 and abs(o["anio"]["neto"] - b["neto"] * 12) < 0.05)
check("selección vacía → «Sin datos» (null), nunca ceros inventados", o["empty"]["contribPct"] is None and o["empty"]["donut"] == [] and o["empty"]["rows"] == 0 and o["empty"]["empty"] is True and all(o["empty"][k] is None for k in ("bruto","neto","uds","ads","contrib")))
check("regiones: Europa ES/DE/FR/IT y América US; CA/MX solo como futuros no activos", o["regs"] == ["eu:ES,DE,FR,IT", "am:US"] and o["fut"] == ["CA", "MX"])
check("series demo: 12 puntos, formas distintas por KPI", len(o["ser"]) == 12 and len(set(o["sers"])) == 6)
# ---- interfaz
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "rediseno", "capturas"); os.makedirs(OUT, exist_ok=True)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w")
port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
BAD = re.compile(r"\bundefined\b|\bNaN\b|\[object |\{\{|Traceback")
with sync_playwright() as p:
    br = p.chromium.launch()
    for vp, w, h in (("1920x1080", 1920, 1080), ("1440x900", 1440, 900), ("390x844", 390, 844)):
        pg = br.new_page(viewport={"width": w, "height": h}, is_mobile=(w < 500), has_touch=(w < 500)); perr = []; ext = []; wr = []
        pg.on("pageerror", lambda e: perr.append(str(e)))
        pg.on("request", lambda r: (ext.append(r.url) if not r.url.startswith(("http://localhost", "data:", "blob:")) else None, wr.append(r.method + r.url) if r.method != "GET" and "/api/login" not in r.url else None))
        pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#lgOpen", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", PW); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1200)
        t = pg.inner_text("#dash7")
        check(f"[{vp}] KPI y donut con el ejemplo coherente, rotulado DEMO", all(x in t for x in ("49.900,00 €", "41.239,67 €", "1.000", "4.990,00 €", "14.364,67 €", "34,83 %", "DEMO · DATOS FICTICIOS", "Fabricación", "Contribución")), t[:200])
        check(f"[{vp}] sin texto roto", not BAD.search(t))
        vis = lambda s: pg.locator(s).first.is_visible() if pg.locator(s).count() else False
        check(f"[{vp}] sin menú lateral ni navegación Lanzamientos/Mis ventas/Productos visible", not any(vis(s) for s in ("#nav6bar", "#subnav6", "#bnav", "#tabs", "header.top")))
        hb = [x.strip() for x in pg.locator("#hdr7 button:visible").all_inner_texts() if x.strip()]
        check(f"[{vp}] cabecera: marca AHT, Benchmarking, Director IA y sesión", any("AHT" in x for x in hb) and "Benchmarking" in hb and "Director IA" in hb and pg.locator("#hdr7 .sessu").count() == 1 and len(hb) <= 5, hb)
        check(f"[{vp}] filtros: línea, región, país y periodo Día/Semana/Mes/Año", pg.locator("#f7Line").count() == 1 and pg.locator("#f7Reg").count() == 1 and pg.locator("#f7Cty").count() == 1 and pg.locator("#f7Per option").all_inner_texts() == ["Día", "Semana", "Mes", "Año"] and pg.locator("#f7Line option").all_inner_texts() == ["Consolidado AHT", "PHIVITAL", "Cosmética", "Home & Care", "Agricultura", "Nuevas tecnologías"] and pg.locator("#f7Line").evaluate("e=>e.closest('label').innerText.split('\\n')[0].startsWith('AHT')") and pg.locator("#f7Reg option").all_inner_texts() == ["Global", "Europa", "América"])
        check(f"[{vp}] subdivisión PHIVITAL solo con PHIVITAL", pg.locator("#f7Sub").count() == 0)
        pg.select_option("#f7Line", "phivital"); pg.wait_for_timeout(200)
        check(f"[{vp}] PHIVITAL → Todas / Suplementos nutricionales / Nutrición deportiva", pg.locator("#f7Sub option").all_inner_texts() == ["Todas", "Suplementos nutricionales", "Nutrición deportiva"])
        pg.select_option("#f7Sub", "sup"); pg.wait_for_timeout(200); n_sup = pg.inner_text("#dash7")
        check(f"[{vp}] el filtro cambia las cifras (PHIVITAL·Suplementos ≠ consolidado)", "41.239,67" not in n_sup and "Sin datos" not in n_sup)
        pg.select_option("#f7Line", "all"); pg.select_option("#f7Reg", "eu"); pg.wait_for_timeout(200)
        cs = pg.locator("#f7Cty option").all_inner_texts()
        check(f"[{vp}] País depende de Región (Europa → ES/DE/FR/IT, sin EE. UU.)", [c for c in cs if "futuro" not in c] == ["Todos", "España", "Alemania", "Francia", "Italia"], cs)
        pg.select_option("#f7Reg", "am"); pg.wait_for_timeout(150); ca = pg.locator("#f7Cty option").all_inner_texts()
        check(f"[{vp}] América → EE. UU.; Canadá y México deshabilitados como futuros configurables", "Estados Unidos" in ca and any("Canadá" in c and "futuro" in c for c in ca) and any("México" in c for c in ca) and pg.locator("#f7Cty option[disabled]").count() == 2, ca)
        pg.select_option("#f7Reg", "eu"); pg.wait_for_timeout(100)
        pg.select_option("#f7Reg", "all"); pg.select_option("#f7Per", "dia"); pg.wait_for_timeout(200)
        check(f"[{vp}] periodo Día reescala (41.239,67/30 = 1374,66 €)", "1.374,66" in pg.inner_text("#dash7"))
        pg.select_option("#f7Per", "mes"); pg.wait_for_timeout(200)
        check(f"[{vp}] Mes restablece el ejemplo", "14.364,67 €" in pg.inner_text("#dash7"))
        if w == 1920 or w == 1440:
            check(f"[{vp}] 16:9 sin desplazamiento vertical del dashboard", pg.evaluate("document.documentElement.scrollHeight <= innerHeight + 2"), pg.evaluate("document.documentElement.scrollHeight"))
        check(f"[{vp}] sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
        check(f"[{vp}] chat Director IA: compositor multilínea, adjuntos, micrófono, enviar y pantalla completa", pg.locator("#c7In").evaluate("e=>e.tagName") == "TEXTAREA" and pg.locator("#c7File").count() == 1 and pg.locator("#c7Mic").count() == 1 and pg.locator("#c7Send").count() == 1 and pg.locator("#c7Full").count() == 1)
        check(f"[{vp}] viewer: compositor en solo lectura, con aviso", pg.locator("#c7In").is_disabled() and pg.locator("#c7Ro").is_visible())
        check(f"[{vp}] notificaciones rotuladas DEMO, con estado, evidencia y contexto", all(x in pg.inner_text("#n7") for x in ("DEMO", "Estado:", "Evidencia:", "Contexto:")))
        check(f"[{vp}] seis KPI con gráfico individual diferenciado (línea, área, barras, escalones, puntos, medidor)", pg.locator(".k7[data-k] svg.sp7").count() == 6 and len({pg.locator(f".k7[data-k={k}] svg.sp7").inner_html() for k in ("bruto", "neto", "uds", "ads", "contrib", "pct")}) == 6 and pg.locator(".k7[data-k=ads] svg rect").count() == 12 and pg.locator(".k7[data-k=uds] svg polygon").count() == 1 and pg.locator(".k7[data-k=bruto] svg polyline").count() == 1 and "Serie DEMO" in pg.locator(".k7[data-k=bruto] svg title").inner_html())
        check(f"[{vp}] chat vacío sin textos de ejemplo", pg.inner_text("#c7Log").strip() == "" and pg.locator("#c7Log .muted").count() == 0)
        # estado del chat estable al cambiar filtros (nodo y borrador conservados; fullscreen conservado)
        pg.evaluate("window.__chatNode = document.getElementById('c7In'); document.getElementById('c7In').disabled = false; document.getElementById('c7In').value = 'borrador de prueba'")
        pg.select_option("#f7Line", "cosm"); pg.select_option("#f7Per", "semana"); pg.select_option("#f7Reg", "eu"); pg.wait_for_timeout(250)
        check(f"[{vp}] filtros no destruyen el chat: mismo nodo y borrador conservados", pg.evaluate("window.__chatNode === document.getElementById('c7In') && document.getElementById('c7In').value === 'borrador de prueba'"))
        check(f"[{vp}] el contexto de filtros se muestra junto al chat", "Cosmética" in pg.inner_text("#c7Ctx") and "Europa" in pg.inner_text("#c7Ctx") and "Semana" in pg.inner_text("#c7Ctx"))
        pg.select_option("#f7Line", "all"); pg.select_option("#f7Reg", "all"); pg.select_option("#f7Per", "mes"); pg.evaluate("document.getElementById('c7In').value = ''"); pg.wait_for_timeout(150)
        pg.select_option("#f7Cty", "all")
        if w == 1920:
            pg.click("#c7Full"); pg.wait_for_timeout(250)
            check(f"[{vp}] pantalla completa por clic real ocupa la ventana", pg.evaluate("document.getElementById('chat7card').getBoundingClientRect().width > innerWidth - 40"))
            pg.keyboard.press("Escape"); pg.click("#c7Full"); pg.select_option("#f7Line", "tech"); pg.wait_for_timeout(250)
            check(f"[{vp}] pantalla completa se conserva al cambiar filtros y se sale con Escape", pg.evaluate("document.getElementById('chat7card').classList.contains('full')") is True)
            pg.keyboard.press("Escape"); pg.wait_for_timeout(150); pg.select_option("#f7Line", "all")
            check(f"[{vp}] Escape cierra la pantalla completa", not pg.evaluate("document.body.classList.contains('c7full')"))
        pg.screenshot(path=os.path.join(OUT, f"dashboard_{vp}.png"), full_page=(w < 500))
        # navegación: Director IA, marca AHT, funciones internas conservadas
        pg.click("#h7Dir"); pg.wait_for_timeout(500)
        check(f"[{vp}] Director IA abre la pantalla existente", pg.locator("#tab-dir.on").count() == 1 and "Director" in pg.inner_text("#tab-dir"))
        pg.click("#h7Brand"); pg.wait_for_timeout(400)
        check(f"[{vp}] la marca AHT vuelve al dashboard", pg.locator("#tab-dash.on").count() == 1)
        for sec, tab in (("lanz", "tab-lanz"), ("ventas", "tab-ventas"), ("prod", "tab-prod"), ("hoyold", "tab-inicio")):
            pg.evaluate(f"NAV6.go('{sec}',0)"); pg.wait_for_timeout(400)
            check(f"[{vp}] ruta interna conservada: {sec}", pg.locator(f"#{tab}.on").count() == 1)
        pg.evaluate("NAV6.go('hoy',0)"); pg.wait_for_timeout(300)
        check(f"[{vp}] 0 errores JS, 0 externas, 0 escrituras", not perr and not ext and not wr, (perr, ext[:2], wr[:2]))
        pg.close()
    br.close()
check("cero conexiones externas (socket)", not EXT)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
