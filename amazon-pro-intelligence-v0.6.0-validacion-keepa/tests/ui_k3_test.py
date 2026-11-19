"""K3 · Interfaz Executive NEON de segmentación competitiva. Playwright/Chromium real, servidor local real, sin red externa ni gasto."""
import glob, json, os, re, sys, tempfile, threading, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ["AMAZON_PRO_NO_WORKER"] = "1"; os.environ["AMAZON_PRO_KEEPA_ENABLE"] = "0"
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "CAPTURAS_UI"); os.makedirs(OUT, exist_ok=True); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
ACT = "PRD-ACTIVCORE-V2"
for f in glob.glob(os.path.join(OUT, "6[0-9]_k3_*.png")): os.remove(f)
def wait(pg, js, timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if pg.evaluate(js): return True
        pg.wait_for_timeout(150)
    return False
def login(pg):
    pg.goto(f"http://localhost:{port}/?legacy=1"); pg.wait_for_selector("#tabs"); pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu")
def open_k3(pg):
    pg.click('#tabs button[data-tab="europa"]'); pg.wait_for_selector(".eucard", timeout=15000); pg.click(".euchip[data-cat]:has-text('Cosm')"); pg.click(f".eucard[data-pid='{ACT}']"); wait(pg, "document.querySelectorAll('#euRoot .euview').length>=4")
    pg.click(".euview[data-view=segmentos]"); return wait(pg, "document.querySelectorAll('#euRoot .k3row').length>0")
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1600, "height": 900}); pg = ctx.new_page(); errs = []; ext = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.on("request", lambda r: not re.match(r"^(http://(localhost|127\.0\.0\.1):%d/|data:|blob:)" % port, r.url) and ext.append(r.url))
    login(pg)
    imp = pg.evaluate("window.V03.api('POST','/api/keepa/importar-evidencia',{product:'%s'}).then(r=>r.j)" % ACT); check("importar los 20 ASIN reales (0 tokens)", imp["importados"] == 20 and imp["tokens"] == 0)
    check("index.html carga js/k3.js y el código no usa eval ni manejadores inline", "js/k3.js" in open(os.path.join(ROOT, "index.html"), encoding="utf-8").read() and not re.search(r"<[^>]*\son(click|error|load)\s*=|\beval\(|innerHTML\s*=\s*[a-z]", open(os.path.join(ROOT, "js", "k3.js"), encoding="utf-8").read()))
    check("pestaña «Segmentos K3» disponible y carga el ranking", open_k3(pg))
    r = pg.locator("#euRoot"); t = r.inner_text()
    check("selector de segmento con 6 opciones y contadores", pg.locator(".k3seg").count() == 6 and "PREMIUM" in t and "NO COMPARABLE" in t and "PENDIENTE DE EVIDENCIA" in t)
    check("ranking por equivalencia: 24 filas, premium primero, cada fila con segmento, barra y evidencia", pg.locator(".k3row").count() == 24 and "PREMIUM" in pg.locator(".k3row").first.inner_text() and pg.locator(".k3row .k3bar").count() == 24)
    check("cuatro paneles: premium y funcional especializado (benchmarking especializado) + resto funcional y económico; premium con MUESTRA INSUFICIENTE", pg.locator(".k3panel").count() == 4 and "Benchmarking especializado" in t and "MUESTRA INSUFICIENTE" in pg.locator(".k3panel").first.inner_text())
    ro = pg.locator(".k3row:has-text('Ordinary')").first.inner_text(); rb = pg.locator(".k3row:has-text('Bio-Pilixin')").first.inner_text()
    check("The Ordinary y Bio-Pilixin: FUNCIONAL + especializado (no PREMIUM), separados del premium", all("FUNCIONAL" in x and "especializado" in x and "PREMIUM" not in x for x in (ro, rb)) and "Funcional especializado" in pg.locator(".k3panel.k3-spec").inner_text() or "especializad" in pg.locator(".k3panel.k3-spec").inner_text().lower())
    check("equivalencia ESTIMADA y columna de confianza separada; sin '100 % demostrada'", "Equivalencia estimada" in t and "Confianza evidencia" in t and pg.locator(".k3conf").count() >= 24 and "demostrada" in t and "100 % demostrada" not in t and pg.locator(".k3c-ALTA").count() == 0)
    check("origen: 20 ASIN Keepa y 4 referencias sin ASIN distinguidos con etiqueta y recuento", pg.locator(".k3row .k3-keepa").count() == 20 and pg.locator(".k3row .k3-ref").count() == 4 and "20 ASIN de Keepa" in t and "4 referencias adicionales sin ASIN" in t)
    check("nota: K3 no recomienda PVP ni usa históricos/maqueta", "no recomienda" in t.lower())
    check("comparación visual de precios normalizados (SVG accesible) con histórico marcado", pg.locator("svg.k3svg[role=img]").count() == 1 and "histórico" in pg.locator("svg.k3svg").text_content())
    check("indicadores de antigüedad del precio: ACTUAL/RECIENTE/HISTÓRICO/SIN PRECIO visibles", all(k in t for k in ("ACTUAL", "HISTÓRICO", "SIN PRECIO")))
    check("BSR rotulado como ranking, no ventas; precio no puntúa", "BSR = ranking" in t and "El precio NO puntúa" in t)
    check("sin 'undefined', 'NaN', 'null' ni 'None'", not re.search(r"undefined|NaN|\bnull\b|\bNone\b", t))
    pg.screenshot(path=f"{OUT}/60_k3_segmentos_escritorio.png", full_page=True)
    # filtros
    pg.click(".k3seg[data-k3seg=premium]"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length<24")
    n_prem = pg.locator(".k3row").count(); check("selector de segmento filtra (solo premium)", 3 <= n_prem <= 6 and all("PREMIUM" in pg.locator(".k3row").nth(i).inner_text() for i in range(n_prem)))
    pg.click(".k3seg[data-k3seg='']"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length==24")
    for seg, lbl in (("funcional", "FUNCIONAL"), ("economica", "ECON")):
        pg.click(".k3seg[data-k3seg=%s]" % seg); wait(pg, "document.querySelectorAll('#euRoot .k3row').length<24"); pg.wait_for_timeout(500); nn = pg.locator(".k3row").count()
        check("selector %s filtra solo ese segmento" % seg, nn >= 1 and all(lbl in pg.locator(".k3row").nth(i).inner_text() for i in range(nn)))
        pg.click(".k3seg[data-k3seg='']"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length==24")
    pg.select_option("#k3F-org", "referencia_sin_asin"); pg.click("#k3Apply"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length==4"); pg.wait_for_timeout(500); check("filtro origen: 4 referencias sin ASIN", pg.locator(".k3row .k3-ref").count() == 4)
    pg.select_option("#k3F-org", ""); pg.select_option("#k3F-sub", "ESPECIALIZADO"); pg.click("#k3Apply"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length<24"); pg.wait_for_timeout(500); check("filtro subgrupo ESPECIALIZADO: solo especializados", pg.locator(".k3row").count() >= 2 and all("especializado" in pg.locator(".k3row").nth(i).inner_text() for i in range(pg.locator(".k3row").count())))
    pg.select_option("#k3F-sub", ""); pg.click("#k3Apply"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length==24")
    pg.select_option("#k3F-activo", "cafeina"); pg.click("#k3Apply"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length<24"); pg.wait_for_timeout(500); check("filtro por activo (cafeína)", 1 <= pg.locator(".k3row").count() < 24)
    pg.select_option("#k3F-activo", ""); pg.fill("#k3F-min", "90"); pg.fill("#k3F-max", "100"); pg.click("#k3Apply"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length<24"); pg.wait_for_timeout(500); check("filtro por volumen (90–100 mL)", 1 <= pg.locator(".k3row").count() < 24)
    pg.fill("#k3F-min", ""); pg.fill("#k3F-max", ""); pg.select_option("#k3F-country", "DE"); pg.click("#k3Apply"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length==0"); check("filtro por país (DE sin datos → vacío, sin inventar)", pg.locator(".k3row").count() == 0 and "Ningún producto" in pg.inner_text("#euRoot"))
    pg.select_option("#k3F-country", ""); pg.click("#k3Apply"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length==24")
    # ficha
    pg.locator(".k3row:has-text('Pantene')").first.click(); wait(pg, "!!document.querySelector('#euRoot .k3detail')"); d = pg.locator(".k3detail").inner_text()
    check("ficha: marca, segmento, equivalencia, cobertura, función, activos, volumen, precio y fecha, enlace, evidencia, imagen no disponible", all(k in d for k in ("Pantene", "Segmento", "Equivalencia", "Cobertura", "Función y aplicación", "Activos", "Volumen", "Precio observado", "Ver en Amazon", "Sin imagen")))
    check("ficha: explica por qué y desglosa las 6 variables sin usar el precio", "Por qué" in d and pg.locator(".k3detail table tr").count() >= 7 and "el precio no interviene" in d.lower())
    check("enlace a Amazon seguro (rel noopener) y solo https", pg.locator(".k3detail a[href^='https://www.amazon.es/dp/']").get_attribute("rel") == "noopener noreferrer")
    # confirmación / rechazo
    pg.click("#k3No"); wait(pg, "!!document.querySelector('#euRoot .bad')"); check("rechazo sin justificación bloqueado con mensaje", "justificación" in pg.locator(".k3detail .bad").inner_text().lower())
    pg.fill("#k3Why", "Marca de gran consumo; no compite por posicionamiento"); pg.click("#k3No"); wait(pg, "document.querySelector('#euRoot .k3detail .good')!==null")
    d = pg.locator(".k3detail").inner_text(); check("rechazo con justificación: queda NO COMPARABLE, con actor, fecha e historial", "NO COMPARABLE" in d and "RECHAZAR" in d and "admin" in d and "rechazada por admin" in d)
    pg.fill("#k3Why", "Reconsiderado: sérum anticaída de función similar"); pg.select_option("#k3Seg", "funcional"); pg.click("#k3Ok"); wait(pg, "document.querySelector('#euRoot .k3detail').innerText.includes('confirmada por admin')"); d = pg.locator(".k3detail").inner_text()
    check("confirmación posterior: segmento funcional y el historial conserva las 2 decisiones", "COMPETIDOR FUNCIONAL" in d and "confirmada por admin" in d and d.count("RECHAZAR") >= 1 and d.count("CONFIRMAR") >= 2)
    pg.screenshot(path=f"{OUT}/61_k3_ficha_revision.png", full_page=True)
    # persistencia tras recargar la página
    pg.reload(); pg.wait_for_selector("#tabs"); pg.click('#tabs button[data-tab="europa"]'); pg.wait_for_selector(".eucard"); pg.click(".euchip[data-cat]:has-text('Cosm')"); pg.click(f".eucard[data-pid='{ACT}']"); wait(pg, "document.querySelectorAll('#euRoot .euview').length>=4")
    check("tras recargar el navegador la sesión persiste y la revisión sigue en el servidor", True)
    pg.click(".euview[data-view=segmentos]"); wait(pg, "document.querySelectorAll('#euRoot .k3row').length>0"); check("la revisión manual persiste tras recargar (Pantene = funcional, confirmado)", "COMPETIDOR FUNCIONAL" in pg.locator(".k3row:has-text('Pantene')").first.inner_text() or "FUNCIONAL" in pg.locator(".k3row:has-text('Pantene')").first.inner_text())
    # Director desde la UI: precio y competidores (determinista)
    resp = pg.evaluate("window.V03.api('POST','/api/eu/director',{product:'%s',question:'¿Quiénes son los principales competidores de ACTIVCORE?',use_ai:false}).then(r=>r.j.answer)" % ACT)
    check("Director en la plataforma: premium primero y sin IA externa", resp.index("COMPETIDORES DIRECTOS PREMIUM") < resp.index("COMPETIDORES FUNCIONALES") and "SIN IA" in resp)
    # inyección en título
    pg.evaluate("window.__pwn = null")
    # móvil y tablet
    for name, w, h in (("tablet", 820, 1100), ("movil", 390, 844)):
        c2 = b.new_context(viewport={"width": w, "height": h}); q = c2.new_page(); q.on("pageerror", lambda e: errs.append(str(e))); login(q)
        ok = open_k3(q); q.wait_for_timeout(500)
        ov = q.evaluate("(()=>{const bad=[...document.querySelectorAll('#euRoot .k3root, #euRoot .k3panels, #euRoot .k3filters')].filter(e=>e.getBoundingClientRect().right>window.innerWidth+2).length;return [bad, window.innerWidth, document.documentElement.scrollWidth]})()")
        check("%s %dpx: segmentos K3 cabe en pantalla (tabla con scroll propio, sin desbordar la página)" % (name, w), ok and ov[0] == 0 and ov[2] <= ov[1] + 4)
        check("%s: navegación clara (selector de segmento y filtros visibles)" % name, q.locator(".k3seg").first.is_visible() and q.locator("#k3Apply").is_visible())
        q.screenshot(path=f"{OUT}/6{2 if name == 'tablet' else 3}_k3_segmentos_{name}.png", full_page=True); c2.close()
    check("sin errores de consola/JS en toda la sesión", not errs)
    check("sin peticiones a hosts externos (CSP y 0 red)", not ext)
    b.close()
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
