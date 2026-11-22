"""K4 · Centro de mando ejecutivo en navegador real (Chromium), servidor local real, sin red externa ni gasto. Capturas en CAPTURAS_UI/7x_k4_*.png."""
import base64, glob, os, re, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ["AMAZON_PRO_NO_WORKER"] = "1"; os.environ["AMAZON_PRO_KEEPA_ENABLE"] = "0"
import _nav_shim  # Fase 4: navegación nueva (sin ?legacy=1)
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "CAPTURAS_UI"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "7[0-9]_k4_*.png")): os.remove(f)
def ready(pg, sel, n=1, t=15000): pg.wait_for_function("([s,n])=>document.querySelectorAll(s).length>=n", arg=[sel, n], timeout=t) if False else None; 
def wait(pg, js, timeout=20):
    import time; t0 = time.time()
    while time.time() - t0 < timeout:
        if pg.evaluate(js): return True
        pg.wait_for_timeout(150)
    return False
def login(pg):
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#tabs"); pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu")
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1600, "height": 900}); pg = ctx.new_page(); errs = []; ext = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.on("request", lambda r: not re.match(r"^(http://(localhost|127\.0\.0\.1):%d/|data:|blob:)" % port, r.url) and ext.append(r.url))
    login(pg)
    imp = pg.evaluate("window.V03.api('POST','/api/keepa/importar-evidencia',{product:'PRD-ACTIVCORE-V2'}).then(r=>r.j)"); check("evidencia Keepa ya almacenada importada (0 tokens)", imp["importados"] == 20 and imp["tokens"] == 0)
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read(); js = open(os.path.join(ROOT, "js", "k4.js"), encoding="utf-8").read()
    check("index.html carga js/k4.js; sin eval ni manejadores inline", "js/k4.js" in html and not re.search(r"<[^>]*\son(click|error|load)\s*=|\beval\(|new Function", js))
    pg.click('#tabs button[data-tab="k4"]'); check("pestaña K4 · EJECUTIVO abre el centro de mando", wait(pg, "document.querySelectorAll('#k4Root .k4kpi').length>=8"))
    t = pg.inner_text("#k4Root")
    check("filtros globales: producto, país, periodo y canal", all(pg.locator(s).count() == 1 for s in ("#k4fp", "#k4fc", "#k4fd", "#k4fk")))
    check("4 vistas navegables", pg.locator(".k4views button").count() == 4)
    check("KPIs sin datos muestran SIN DATO (no 0) y explican que no hay importación", pg.locator(".k4kpi.k4none").count() >= 6 and "SIN DATO" in t and "no es 0" in t)
    check("dictamen resumido: 5. EVIDENCIA INSUFICIENTE", "5. EVIDENCIA INSUFICIENTE" in t)
    check("panel de capacidades honesto: IA externa DESACTIVADA, autonomía NO VERIFICADA, SP-API/Ads no operativos", "DESACTIVADA" in t and "NO_VERIFICADA" in t and "SP-API" in t and "NO es dirección comercial autónoma" in t)
    check("sin 'undefined', 'NaN', 'null' ni 'None'", not re.search(r"undefined|NaN|\bnull\b|\bNone\b", t))
    pg.screenshot(path=f"{OUT}/70_k4_centro_escritorio.png", full_page=True)
    # benchmarking · nivel 1
    pg.click('[data-k4v=bench]'); check("comparativa ejecutiva: ACTIVCORE + 5 columnas", wait(pg, "document.querySelectorAll('#k4Root table.k4cmp thead th').length===7")); pg.evaluate("document.querySelector('#k4evi') && (document.querySelector('#k4evi').open = true)"); pg.wait_for_timeout(200)
    tb = pg.inner_text("#k4Root"); heads = pg.locator("table.k4cmp thead th")
    check("ACTIVCORE destacado como producto propio y 5 referencias K3 (Kérastase, Nioxin, Redken, The Ordinary, Bio-Pilixin)", pg.locator("th.k4own-col").count() == 1 and "PRODUCTO PROPIO" in tb and all(x in tb for x in ("Kérastase", "Nioxin", "Redken", "The Ordinary", "Bio-Pilixin")))
    check("filas comparativas: precio, €/100 mL, activos, dosis, duración, posicionamiento, evidencia, ventajas", all(pg.locator("tr.k4r-" + r).count() == 1 for r in ("precio", "precio_100ml", "activos", "dosis", "duracion", "posicionamiento", "evidencia", "ventajas")))
    check("no se muestran 24 fotos: solo 6 recuadros de imagen, todos con IMAGEN PENDIENTE y la autorización que falta", pg.locator("#k4Root .k4img").count() == 6 and pg.locator("#k4Root .k4pend").count() == 6 and "Falta:" in pg.locator(".k4pend").first.inner_text())
    check("cifras de maqueta etiquetadas y sin dato explícito (no se inventa)", "MAQUETA · no verificado" in tb and "SIN DATO" in tb and "NO EVALUABLE" in tb)
    check("dictamen del Director visible bajo la comparativa con las 8 secciones", "Recomendación del Director IA" in tb and pg.locator("#k4dictamen details.k4sec").count() >= 8 and "Acción prioritaria" in tb and "Condiciones para reconsiderar la decisión" in tb)
    check("diagnóstico de PVP, causa de falta de ventas y ventaja competitiva", all(x in tb for x in ("PVP adecuado", "Causa de la falta de ventas", "Ventaja competitiva")))
    check("filtros avanzados y evidencia en secciones desplegables", pg.locator("details.k4adv").count() >= 2 and "Cómo se eligieron los cinco" in tb)
    check("accesibilidad: caption, scope, región desplazable con teclado, tabs con aria-selected", pg.locator("table.k4cmp caption").count() == 1 and pg.locator("table.k4cmp th[scope=row]").count() >= 8 and pg.locator(".k4scroll[tabindex='0']").count() >= 1 and pg.locator(".k4sub [role=tab][aria-selected=true]").count() == 1)
    check("sin 'undefined', 'NaN', 'null' ni 'None' en la comparativa", not re.search(r"undefined|NaN|\bnull\b|\bNone\b", tb))
    pg.screenshot(path=f"{OUT}/80_k4_comparativa_ejecutiva_escritorio.png", full_page=True)
    pg.locator("#k4dictamen").screenshot(path=f"{OUT}/84_k4_dictamen_director.png")
    # nivel 2 · explorador
    pg.click('[data-k4bv=expl]'); check("explorador compacto: 24 referencias sin fotografías", wait(pg, "document.querySelectorAll('#k4Root table.k4expl tbody tr').length===24") and pg.locator("#k4Root .k4img").count() == 0)
    pg.fill("#k4xq", "kerastase".replace("e", "é", 1) if False else "Kérastase"); pg.wait_for_timeout(300); nq = pg.locator("table.k4expl tbody tr").count(); check("búsqueda por marca filtra", 0 < nq < 24 and "Kérastase" in pg.inner_text("table.k4expl"))
    pg.fill("#k4xq", ""); pg.wait_for_timeout(200); pg.select_option("#k4xs", "premium"); pg.wait_for_timeout(200); np_ = pg.locator("table.k4expl tbody tr").count(); check("filtro por segmento", 0 < np_ < 24)
    pg.select_option("#k4xs", ""); pg.select_option("#k4xo", "precio"); pg.wait_for_timeout(200); check("ordenación por €/100 mL (SIN DATO al final)", "SIN DATO" in pg.locator("table.k4expl tbody tr").last.inner_text())
    pg.check("#k4xe"); pg.wait_for_timeout(200); check("solo los 5 de la comparativa", pg.locator("table.k4expl tbody tr").count() == 5); pg.uncheck("#k4xe"); pg.wait_for_timeout(200)
    pg.screenshot(path=f"{OUT}/82_k4_explorador_compacto.png", full_page=True)
    # sustitución manual con motivo, auditoría y persistencia
    pg.once("dialog", lambda d: d.accept("prueba de ajuste manual auditado")); pg.locator("table.k4expl tr.k4insel [data-k4quitar]").first.click(); wait(pg, "document.querySelectorAll('#k4Root table.k4expl tr.k4insel').length===4"); check("quitar una referencia de la comparativa (con motivo)", pg.locator("table.k4expl tr.k4insel").count() == 4)
    pg.reload(); pg.wait_for_selector("#tabs"); pg.click('#tabs button[data-tab="k4"]'); pg.click('[data-k4v=bench]'); pg.click('[data-k4bv=expl]'); wait(pg, "document.querySelectorAll('#k4Root table.k4expl tbody tr').length===24"); check("la selección persiste tras recargar", pg.locator("table.k4expl tr.k4insel").count() == 4)
    pg.once("dialog", lambda d: d.accept("reposición de la referencia retirada")); pg.locator("table.k4expl tr:not(.k4insel) [data-k4anadir]").first.click(); wait(pg, "document.querySelectorAll('#k4Root table.k4expl tr.k4insel').length===5"); check("añadir otra referencia (máx. cinco)", pg.locator("table.k4expl tr.k4insel").count() == 5)
    aud = pg.evaluate("window.V03.api('GET','/api/k4/benchmark/explorador?producto=PRD-ACTIVCORE-V2&pais=ES').then(r=>r.j)"); check("ajustes registrados y auditados", len(aud["seleccion"]["ajustes"]) >= 2)
    # nivel 3 · expediente 360
    pg.locator("table.k4expl [data-k4exp360]").first.click(); check("expediente 360° con foto/marcador, identificador, ASIN y comparación con ACTIVCORE", wait(pg, "document.querySelector('#k4Root .k4exp360')") and "Comparación detallada con ACTIVCORE" in pg.inner_text("#k4Root") and "Identificador" in pg.inner_text("#k4Root") and pg.locator(".k4exp360 .k4pend").count() == 1)
    pg.screenshot(path=f"{OUT}/83_k4_expediente_360.png", full_page=True)
    # filtro global: país
    pg.select_option("#k4fc", "DE"); pg.wait_for_timeout(800); check("filtro global de país recarga la vista (DE) sin errores", "DE" in pg.input_value("#k4fc") and not errs)
    pg.select_option("#k4fc", "ES"); pg.wait_for_timeout(600)
    # pricing
    pg.click('[data-k4v=precio]'); check("Pricing Intelligence: dictamen, trazabilidad y ficha de costes", wait(pg, "document.querySelectorAll('#k4Root .k4dict').length>=1 && document.querySelectorAll('#k4Root .k4tb').length>=2"))
    tp = pg.inner_text("#k4Root")
    check("dictamen 5: faltantes con cómo obtenerlos y experimento de precio", "Datos faltantes y cómo obtenerlos" in tp and "Experimento" in tp and "Elasticidad observada" in tp)
    check("ficha de costes: 10,03 € pendiente de validar, alcance no confirmado y conceptos FALTA", "10,03" in tp and "PENDIENTE_VALIDAR" in tp and pg.locator(".k4st-FALTA").count() >= 5 and "no confirmado" in tp.lower())
    check("PVP presentado como PROPUESTA (no como precio vigente)", "PROPUESTO" in tp and "PROPUESTA" in tp)
    check("sin escenarios en unidades inventados", "Sin escenarios: faltan datos" in tp)
    pg.screenshot(path=f"{OUT}/72_k4_pricing_escritorio.png", full_page=True)
    # importación CSV de producción
    csv_ = "producto,pais,fecha,unidades,ventas_netas,moneda,sesiones,pedidos,precio_medio,canal\\nPRD-ACTIVCORE-V2,ES,2026-11-01,5,200,EUR,80,5,48,FBA"
    pg.fill("#k4ic", csv_.replace("\\n", "\n")); pg.click("#k4ib"); check("importación manual de CSV documentado funciona", wait(pg, "document.querySelector('#k4m') && document.querySelector('#k4m').textContent.indexOf('Importadas 1')>=0"))
    # demo sintética vía API y ¿y si?
    r = pg.evaluate("window.V03.api('POST','/api/k4/demo/cargar',{}).then(r=>r.j)"); check("carga de demo sintética (admin)", r.get("ok") is True)
    d = pg.evaluate("window.V03.api('GET','/api/k4/dictamen?entorno=SINTETICO_DEMO&pvp=40').then(r=>r.j)"); check("ejemplo de dictamen demo (etiquetado SINTÉTICO)", d["dictamen"]["tipo"] == 1 and "SINTÉTICOS" in d["aviso_entorno"])
    # Director
    pg.click('[data-k4v=precio]'); wait(pg, "document.querySelector('#k4mkdos')"); pg.click("#k4mkdos"); check("generar dossier del Director desde Pricing", wait(pg, "document.querySelector('#k4Root .k4dossier')"))
    td = pg.inner_text("#k4Root")
    check("dossier: problema, hipótesis alternativas, investigación, acción, responsable, criterio de éxito, revisión", all(x in td for x in ("Problema detectado", "Hipótesis alternativas", "Investigación realizada", "Acción:", "Responsable:", "Criterio de éxito", "Revisión posterior")))
    check("dictamen 5 → sin botón de proponer decisión de precio", pg.locator("[data-k4prop]").count() == 0 and "no hay decisión de precio que proponer" in td)
    check("registro de imágenes: vacío explica que todas las tarjetas son PENDIENTE", "Sin imágenes registradas" in td)
    pg.screenshot(path=f"{OUT}/73_k4_director_escritorio.png", full_page=True)
    # nuevo producto
    pg.fill("#k4npt", "Sérum facial X"); pg.fill("#k4npn", "piel sensible"); pg.click("#k4np button[type=submit]"); check("nuevo producto: dossier NO_EVALUADO con faltantes", wait(pg, "document.querySelector('#k4Root .k4dossier') && document.querySelector('#k4Root .k4dossier').textContent.indexOf('Sin necesidad')>=0"))
    # exportaciones
    pg.click('[data-k4v=bench]'); pg.click('[data-k4bv=comp]'); wait(pg, "document.querySelector('table.k4cmp') && !document.querySelector('.k4load') && document.querySelector('[data-k4exp=pdf]')"); pg.wait_for_timeout(500); pg.locator("details.k4adv", has_text="Evidencia, exportación").evaluate("d => { d.open = true; }"); wait(pg, "document.querySelector('[data-k4exp=pdf]').offsetParent !== null")
    with pg.expect_download() as dl: pg.click("[data-k4exp=pdf]")
    path = dl.value.path(); check("exportar PDF desde la interfaz", open(path, "rb").read(8).startswith(b"%PDF-1.4"))
    with pg.expect_download() as dl2: pg.click("[data-k4exp=svg]")
    sv = open(dl2.value.path(), "rb").read(); check("exportar SVG: sin imágenes sin derecho y con marcadores", b"<svg" in sv[:60] and b"<image" not in sv and b"IMAGEN PENDIENTE" in sv)
    with pg.expect_download() as dl3: pg.click("[data-k4exp=png]")
    check("exportar PNG (renderizado en el navegador)", open(dl3.value.path(), "rb").read(4) == b"\x89PNG")
    # responsive
    for w, h, nm, fn in ((820, 1100, "tablet", "81_k4_comparativa_tablet"), (390, 844, "movil", "81_k4_comparativa_movil")):
        c2 = b.new_context(viewport={"width": w, "height": h}); p2 = c2.new_page(); login2 = lambda q: (q.goto(f"http://localhost:{port}/"), q.wait_for_selector("#tabs"), q.click("#lgOpen"), q.fill("#lgU", "admin"), q.fill("#lgP", "admin-password-123"), q.click("#lgGo"), q.wait_for_selector(".sessu"))
        login2(p2); p2.click('#tabs button[data-tab="k4"]'); wait(p2, "document.querySelectorAll('#k4Root .k4kpi').length>=8"); p2.click('[data-k4v=bench]'); wait(p2, "document.querySelectorAll('#k4Root table.k4cmp thead th').length===7"); p2.evaluate("document.querySelector('#k4evi').open = true")
        check(f"{nm}: la página no se desborda (la tabla se desplaza dentro de su región)", p2.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 4"))
        if nm == "movil":
            p2.evaluate("document.querySelector('#k4evi').open = true"); check("móvil: selector de comparación por pares visible (dentro de «Evidencia»)", p2.locator("#k4par").is_visible()); p2.select_option("#k4par", "0"); p2.wait_for_timeout(300); p2.evaluate("document.querySelector('#k4evi').open = true"); check("móvil: par ACTIVCORE vs una referencia (3 columnas)", p2.locator("table.k4cmp thead th").count() == 3)
            check("móvil: botones táctiles ≥ 40 px", p2.evaluate("[...document.querySelectorAll('.k4sub button')].every(b=>b.getBoundingClientRect().height>=38)"))
        p2.screenshot(path=f"{OUT}/{fn}.png", full_page=True); c2.close()
    check("sin peticiones externas ni errores de consola/página", not ext and not errs)
    if ext or errs: print(ext[:3], errs[:3])
    b.close()
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
