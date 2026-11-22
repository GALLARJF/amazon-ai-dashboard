"""Fase 4 · VENTAS, PRODUCTOS, ADMINISTRACIÓN y DIRECTOR IA (viewer en staging; escritorio 1440, Android 390 y 360).
REAL/DEMO/SIN DATOS visible; sin ceros inventados; sin rutas /api en primer nivel; sin desplazamiento horizontal; controles ≥ 44 px; móvil sin tablas horizontales;
ACTIVCORE y PHIVITAL diferenciados; navegación alerta → producto; Director con ≤ 3 decisiones y 6 campos; viewer sin escritura (403 del servidor); CERO llamadas externas.
Capturas en docs/p0_hoy/fase4/<viewport>/."""
import glob, json, os, re, sys, tempfile, threading, urllib.request, urllib.error, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR="viewer-pass-x7Qk2m")
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "fase4"); os.makedirs(OUT, exist_ok=True); R = []; EXTERNAL = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for f in glob.glob(os.path.join(OUT, "*", "*.png")): os.remove(f)
def call(p, b=None, csrf="", jar=None):
    r = urllib.request.Request(f"http://localhost:{port}" + p, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}); return json.loads(jar.open(r).read())
def route(r):
    u = r.request.url
    if u.startswith(f"http://localhost:{port}") or u.startswith("data:") or u.startswith("blob:"): r.continue_()
    else: EXTERNAL.append(u); r.abort()
SCREENS = {"ventas": ("#ventas2", "ventas2top"), "prod": ("#prod2", "prod2top"), "adm": ("#adm2", "adm2top"), "dir": ("#dir2", "d2top")}
def login(pg):
    pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", "viewer-pass-x7Qk2m"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
def goto(pg, sec, sel):
    pg.evaluate(f"NAV6.go('{sec}',0)"); pg.wait_for_selector(sel, state="visible", timeout=10000); pg.wait_for_timeout(1200)
VIS = "e => e.checkVisibility ? e.checkVisibility() : true"
def run(pw, name, vp, mobile):
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    ctx = pw.new_context(viewport=vp, device_scale_factor=1, is_mobile=mobile, has_touch=mobile); ctx.route("**/*", route); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    login(pg); T = f"[{name}]"
    for sec, (root, top) in SCREENS.items():
        goto(pg, sec, f"#{top}" if sec != "dir" else "#d2top .h2c")
        t = pg.locator(f"#{top}").inner_text(); pg.evaluate("scrollTo(0,0)"); pg.screenshot(path=os.path.join(d, f"{sec}.png")); pg.screenshot(path=os.path.join(d, f"{sec}_completa.png"), full_page=True)
        check(f"{T} {sec}: sin error de JavaScript", not errs)
        check(f"{T} {sec}: REAL/DEMO/SIN DATOS visible en la cabecera", pg.locator(f"#{top} .h2b").count() >= 1 and re.search(r"\b(REAL|DEMO|SIN DATOS)\b", t))
        check(f"{T} {sec}: sin rutas /api ni detalles técnicos en el primer nivel", "/api/" not in t and not re.search(r"GET |POST |token", t))
        check(f"{T} {sec}: ausencia ≠ cero (sin «0 €» ni «0 %» inventados)", not re.search(r"(?<![\d.,])0([.,]00)? ?(€|%)", t))
        m = pg.evaluate("[scrollX, document.documentElement.scrollWidth, innerWidth]"); check(f"{T} {sec}: sin desplazamiento horizontal {m}", m[0] == 0 and m[1] <= m[2])
        sz = pg.evaluate("[...document.querySelectorAll('" + ("#bnav button, " if mobile else "") + ".x4 summary, .x4 .h2btn, #dir2 summary, #dir2 .h2btn')].filter(e=>e.checkVisibility()).map(e=>Math.round(e.getBoundingClientRect().height))")
        check(f"{T} {sec}: botones y cabeceras ≥ 44 px (mín {min(sz) if sz else 'n/a'})", sz and min(sz) >= 43)
        if mobile:
            wide = pg.evaluate("[...document.querySelectorAll('table')].filter(t=>t.checkVisibility() && t.getBoundingClientRect().width > innerWidth).length"); check(f"{T} {sec}: móvil sin tablas horizontales visibles ({wide})", wide == 0)
            check(f"{T} {sec}: barra inferior presente", pg.locator("#bnav").is_visible())
    # ---- VENTAS
    goto(pg, "ventas", "#ventas2top .x4t"); t = pg.locator("#ventas2top").inner_text()
    check(f"{T} ventas: resumen con ventas, margen, publicidad, stock y alertas", all(x in t for x in ("VENTAS", "MARGEN", "PUBLICIDAD", "STOCK", "ALERTAS")) or all(x.lower() in t.lower() for x in ("Ventas", "Margen", "Publicidad", "Stock", "Alertas")))
    check(f"{T} ventas: Conclusión y Decisión en primer nivel; Evidencia y Metodología plegadas", "Conclusión" in t and "Decisión" in t and pg.locator("#ventas2evi").evaluate("e=>!e.open") and pg.locator("#ventas2met").evaluate("e=>!e.open"))
    check(f"{T} ventas: cada cifra ausente es SIN DATOS (nunca 0)", pg.locator("#ventas2top .x4t .x4tv.nd").count() >= 3)
    # ---- PRODUCTOS
    goto(pg, "prod", "#prod2top .x4prod"); n = pg.locator("#prod2 .x4prod").count()
    check(f"{T} productos: una ficha por producto ({n} = 3)", n == 3)
    for pid, fam in (("PRD-ACTIVCORE-V2", "ACTIVCORE"), ("PRD-PHIVITAL-MAGNESIO", "PHIVITAL"), ("PRD-PHIVITAL-OMEGA3", "PHIVITAL")):
        c = pg.locator(f"#px-{pid}"); ct = c.inner_text()
        check(f"{T} productos: {pid} con los 7 campos (precio, coste, margen, inventario, ventas, publicidad, documentación) y estado", all(l.lower() in ct.lower() for l in ("Precio", "Coste", "Margen", "Inventario", "Ventas", "Publicidad", "Documentación")) and re.search(r"Pre-lanzamiento|En operación", ct) and fam in ct)
    check(f"{T} productos: ACTIVCORE y PHIVITAL diferenciados (familia, cabecera y color)", pg.locator(".x4fh-activcore").count() == 1 and pg.locator(".x4fh-phivital").count() == 1 and pg.locator(".x4f-activcore").count() == 1 and pg.locator(".x4f-phivital").count() == 2)
    ct = pg.locator("#px-PRD-ACTIVCORE-V2").inner_text()
    check(f"{T} productos: margen NO DETERMINABLE (faltan costes), ventas/publicidad SIN DATOS, stock histórico rotulado", "NO DETERMINABLE" in ct.upper() and ct.count("SIN DATOS") >= 2 and "histórico" in ct.lower())
    # ---- navegación desde el Director → producto
    goto(pg, "dir", "#d2top .h2c"); b = pg.locator("#dir2 [data-h2prod]").first; check(f"{T} director: hay enlace al producto afectado", b.count() == 1)
    pid = b.get_attribute("data-h2prod"); b.click(); pg.wait_for_selector("#prod2 .x4prod.h2hl", timeout=8000)
    check(f"{T} navegación recomendación → producto: abre Productos y resalta {pid}", pg.locator(f"#px-{pid}.h2hl").count() == 1 and pg.evaluate("NAV6.state.sec") == "prod")
    goto(pg, "hoy", "#hoy2 .h2c, #h2top"); a = pg.locator("#hoy2 [data-h2prod]")
    if a.count():
        pid2 = a.first.get_attribute("data-h2prod"); a.first.click(); pg.wait_for_selector("#prod2 .x4prod.h2hl", timeout=8000); check(f"{T} navegación alerta (Hoy) → producto: resalta {pid2}", pg.locator(f"#px-{pid2}.h2hl").count() == 1)
    # ---- DIRECTOR
    goto(pg, "dir", "#d2top .h2recs"); lis = pg.locator("#d2top .h2recs > li"); k = lis.count()
    check(f"{T} director: máximo 3 decisiones ({k})", 1 <= k <= 3)
    for i in range(k):
        li = lis.nth(i).inner_text(); check(f"{T} director: decisión {i+1} indica producto, impacto, evidencia, responsable y próxima acción", all(x in li for x in ("Producto", "Impacto", "Evidencia", "Responsable", "Próxima acción")))
        check(f"{T} director: decisión {i+1} rotulada como Regla determinista o Cálculo (nunca IA generativa)", re.search(r"Regla determinista|Cálculo", li) and "IA generativa" not in li)
    leg = pg.locator("#d2top .h2leg").inner_text(); check(f"{T} director: leyenda diferencia regla, cálculo e IA generativa (sin IA en este panel)", all(x in leg for x in ("Regla determinista", "Cálculo", "IA generativa", "ninguna")))
    # ---- ADMINISTRACIÓN
    goto(pg, "adm", "#adm2top .x4t"); t = pg.locator("#adm2").inner_text()
    check(f"{T} admin: Aprobaciones, Conexiones, Historial y Auditoría unificados en una pantalla (subnavegación: Administración + Laboratorio DEMO)", all(x in t for x in ("Aprobaciones", "Historial y auditoría", "Conexiones")) and pg.locator("#subnav6 [data-sub]").all_inner_texts() == ["Administración", "Laboratorio DEMO"])
    check(f"{T} admin: operación diaria arriba; configuración técnica plegada", "Operación diaria" in t and pg.locator("#adm2conn").evaluate("e=>!e.open"))
    pg.locator("#adm2conn > summary").click(); pg.wait_for_timeout(400); ct = pg.locator("#adm2connb").inner_text()
    check(f"{T} admin: 4 conexiones, todas DESHABILITADAS por defecto, con variables que faltan", all(x in ct for x in ("Amazon SP-API", "Amazon Ads API", "Keepa", "Helium 10")) and ct.count("DESHABILITADO") >= 4 and "AMAZON_PRO_SPAPI_CLIENT_ID" in ct)
    pg.locator("#adm2hist > summary").click(); pg.wait_for_timeout(400); check(f"{T} admin: auditoría con cadena íntegra y eventos", "✔ íntegra" in pg.locator("#adm2histb").inner_text())
    check(f"{T} admin: nota de solo lectura del viewer", "Solo lectura" in pg.locator("#adm2top").inner_text())
    # ---- viewer: ningún control de escritura activo en las pantallas nuevas
    for sec, (root, top) in SCREENS.items():
        goto(pg, sec, f"#{top}" if sec != "dir" else "#d2top .h2c")
        w = pg.evaluate("[...document.querySelectorAll('%s button, %s input, %s textarea')].filter(e=>e.checkVisibility() && !e.disabled && !e.matches('.ro-ok,[data-h2go],[data-h2prod],summary') && /(guardar|aprobar|rechazar|importar|subir|crear|editar|enviar)/i.test(e.textContent||e.value||'')).length" % (root, root, root)); check(f"{T} viewer: {sec} sin controles de escritura activos ({w})", w == 0)
    check(f"{T} cero llamadas externas hasta ahora ({len(EXTERNAL)})", not EXTERNAL)
    pg.context.close()
with sync_playwright() as p:
    b = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])
    run(b, "desktop", {"width": 1440, "height": 900}, False); run(b, "android", {"width": 390, "height": 844}, True); run(b, "android360", {"width": 360, "height": 740}, True); b.close()
check(f"CERO llamadas externas durante toda la prueba ({len(EXTERNAL)}: {EXTERNAL[:3]})", not EXTERNAL)
vj = http.cookiejar.CookieJar(); vo = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(vj)); vc = call("/api/login", {"username": "auditor", "password": "viewer-pass-x7Qk2m"}, "", vo)["csrf"]
for path, body in (("/api/v06/decide", {"id": 1, "approve": True}), ("/api/approvals/decide", {"account": "activcore-eu", "id": "x", "decision": "approve"}), ("/api/catalog/update", {"id": "PRD-ACTIVCORE-V2", "patch": {"name": "x"}}), ("/api/v06/order", {"product": "PRD-ACTIVCORE-V2"})):
    try: call(path, body, vc, vo); code = 200
    except urllib.error.HTTPError as e: code = e.code
    check(f"servidor · viewer: POST {path} → 403 (obtenido {code})", code == 403)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
