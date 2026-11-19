"""Pruebas de UI V0.3 (Playwright, navegador real) + capturas. Arranca su propio servidor local con BD temporal.
Los datos del expediente «Magnesio PRUEBA» son FICTICIOS (origen PRUEBA) y se usan solo para demostrar el flujo."""
import datetime, json, os, re, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI, pilot as P
OUT = os.path.join(ROOT, "capturas"); os.makedirs(OUT, exist_ok=True); res = []
def check(n, c):
    res.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
ENV = {}
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tempfile.mkdtemp(), "ui.db"), cfg_fn=lambda: AI.config(ENV), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
st = S.APP["store"]; ACC = "phivital-pendiente"
st.create_user("ana", "analista-pass-1", "analyst", [ACC]); st.create_user("pablo", "aprobador-pass-1", "approver", [ACC])
TODAY = datetime.date.today()
ago = lambda n: (TODAY - datetime.timedelta(days=n)).isoformat()
# expediente de PRUEBA completo (ficticio) creado en servidor
d = P.template(); d["product"]["name"] = "Magnesio PRUEBA (ficticio)"
d["econ"].update(price=19.9, cost=3.0, fbaFee=3.2, acosTarget=18, vatPct=10, feeSchedule="generico_15", storageMonthly=0.1, storageMonths=2, returnsPct=3, returnProcessing=1.5)
for k in d["costDocs"]: d["costDocs"][k] = {"evidence": "PRUEBA ficticia " + k, "date": ago(5)}
d["competitors"] = [{"name": f"C{i}", "asin": f"A{i}", "priceGross": p, "shipping": 0, "packUnits": 1, "contentValue": 120, "source": "PRUEBA", "date": ago(4), "rating": 4.4, "reviews": 200 * i} for i, p in enumerate([18.5, 21, 23.9, 26], 1)]
d["keywords"] = [{"keyword": k, "volume": v, "source": "PRUEBA", "date": ago(10)} for k, v in [("magnesio", 9000), ("magnesio 120 capsulas", 2000), ("citrato de magnesio", 4000), ("magnesio sueño", 1500), ("magnesio cansancio", 900)]]
for it in list(d["regulatory"].values()) + list(d["content"].values()) + list(d["logistics"]["items"].values()): it.update(status="cumplido", evidence="PRUEBA", date=ago(3))
d["logistics"].update(stockAvailable=900, forecastUnitsMonth=300, leadTimeDays=30, coverTargetDays=45); d["listing"] = {"title": "Magnesio 120 capsulas citrato de magnesio", "bullets": ["magnesio sueño"], "backend": ""}; d["pvpScenarios"] = [17.99, 19.9, 22.9]; d["cvrPct"] = 10
st.put(ACC, "dossier", {"name": "Magnesio PRUEBA (ficticio)", "origin": "PRUEBA", "dossier": d}, key="prueba", actor="ana")
st.put(ACC, "news", {"title": "Nota de prueba verificada", "url": "https://example.com/n", "source": "Fuente de prueba", "date": ago(2), "status": "verificada", "added_by": "ana", "verified_by": "pablo"}, actor="pablo")

with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1600, "height": 840}); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    U = f"http://localhost:{port}/?legacy=1"; pg.goto(U); pg.wait_for_selector("#tabs"); pg.click("#tabs button[data-tab=panel]"); pg.wait_for_selector("#kpis .kpi")
    check("carga sin errores JS ni violaciones CSP", not errs)
    check("sin sesión: Director pide iniciar sesión y no responde con datos", "Inicia sesión" in pg.inner_text("#dirEngine"))
    pg.fill("#chatIn", "resumen"); pg.press("#chatIn", "Enter"); pg.wait_for_selector("#lgForm"); check("preguntar sin sesión abre el acceso", True); pg.click("#mClose")
    pg.screenshot(path=f"{OUT}/00_sin_sesion_1600x840.png")
    pg.click("#lgOpen"); pg.fill("#lgU", "ana"); pg.fill("#lgP", "mala-contraseña-xx"); pg.click("#lgGo"); pg.wait_for_selector("#mBody .f.warn"); check("login erróneo muestra error", True)
    pg.fill("#lgP", "analista-pass-1"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(500)
    pg.click("#tabs button[data-tab=panel]"); pg.wait_for_timeout(300)
    check("sesión iniciada con rol visible", "ana" in pg.inner_text("#sess") and "analyst" in pg.inner_text("#sess"))
    check("cuenta/titular visible (no se asume titular legal)", "POR CONFIRMAR" in pg.inner_text("#acSel"))
    check("badge del panel sigue indicando DEMO", "DEMO" in pg.inner_text("#badge"))
    check("5 KPIs, 4 gráficos SVG", pg.locator("#kpis .kpi").count() == 5 and all(pg.locator(f"#{i} svg").count() == 1 for i in ["chSales", "chComp", "chAds", "chBsr"]))
    k0 = pg.inner_text("#kpis .kpi >> nth=0"); pg.select_option("#fPeriod", "7"); k1 = pg.inner_text("#kpis .kpi >> nth=0"); pg.select_option("#fMkt", "DE"); k2 = pg.inner_text("#kpis .kpi >> nth=0"); pg.select_option("#fProduct", "DEMO-B"); k3 = pg.inner_text("#kpis .kpi >> nth=0")
    check("filtros producto/periodo/marketplace funcionan", len({k0, k1, k2, k3}) == 4); pg.select_option("#fPeriod", "30"); pg.select_option("#fMkt", "all"); pg.select_option("#fProduct", "all")
    check("cabe sin scroll horizontal a 1600x840", pg.evaluate("document.documentElement.scrollWidth<=1600"))
    check("7 coworkers visibles con estado SIN EJECUCIÓN", pg.locator(".cwb").count() == 7 and pg.locator(".cwb .st", has_text="SIN EJECUCIÓN").count() == 7)
    check("noticias: solo verificadas, con fuente y fecha", "Nota de prueba verificada" in pg.inner_text("#newsBox") and "verificada por pablo" in pg.inner_text("#newsBox"))
    alltxt = pg.inner_text("body").lower()
    check("sin indicadores falsos de operatividad", "operativo" not in alltxt.replace("«operativo» exige", "") and not re.search(r"(?<!no )(?<!ni apis )conectad[oa]", alltxt))
    # --- Director sin IA ---
    pg.select_option("#dirDossier", label=pg.locator("#dirDossier option", has_text="Magnesio PRUEBA").first.inner_text())
    pg.fill("#chatIn", "¿Cómo está el precio y la competencia?"); pg.press("#chatIn", "Enter"); pg.wait_for_selector(".mtag"); pg.wait_for_timeout(300)
    txt = pg.inner_text("#chat"); check("Director sin IA: etiqueta SIN IA y decisión determinista", "SIN IA" in txt and "Decisión determinista" in txt and "mercado → precios" in txt)
    pg.screenshot(path=f"{OUT}/02_director_sin_ia_1600x840.png")
    check("tras la consulta: mercado y precios ejecutados sobre PRUEBA (no operativos)", pg.locator(".cwb[data-cw=mercado] .st", has_text="PRUEBA").count() == 1 and pg.locator(".cwb.opn").count() == 0 and pg.locator(".cwb[data-cw=ppc] .st", has_text="SIN EJECUCIÓN").count() == 1)
    # --- Director con proveedor simulado ---
    ENV.update({"AMAZON_PRO_AI_PROVIDER": "mock", "AMAZON_PRO_AI_PRICE_IN": "3", "AMAZON_PRO_AI_PRICE_OUT": "15"}); pg.reload(); pg.wait_for_selector(".sessu"); pg.click("#tabs button[data-tab=panel]"); pg.wait_for_timeout(400)
    pg.select_option("#dirDossier", index=1); pg.fill("#chatIn", "resumen general de todo"); pg.press("#chatIn", "Enter"); pg.wait_for_selector(".m-SIMULADA"); pg.wait_for_timeout(300)
    txt = pg.inner_text("#chat"); check("Director con mock: etiqueta SIMULADA · no es IA real, con tokens y coste", "SIMULADA" in txt and "no es IA real" in txt and "tokens" in txt and "coste est." in txt)
    pg.screenshot(path=f"{OUT}/03_director_simulado_1600x840.png")
    check("IA real NO verificada declarada", "NO (pendiente)" in pg.inner_text("#cwGrid"))
    check("tras 'resumen general': 7 coworkers ejecutados sobre PRUEBA, ninguno operativo", pg.locator(".cwb .st", has_text="SIN EJECUCIÓN").count() == 0 and pg.locator(".cwb.opn").count() == 0)
    pg.click("[data-cw=ppc]"); pg.wait_for_selector("#cwOut .f"); check("detalle de coworker: hallazgos, origen y verificaciones", "PRUEBA" in pg.inner_text("#cwOut") and "✔" in pg.inner_text("#cwOut")); pg.screenshot(path=f"{OUT}/04_coworker_detalle_1600x840.png"); pg.click("#mClose")
    # --- Piloto ---
    pg.click("[data-tab=piloto]"); pg.wait_for_selector("#pilSel"); pg.wait_for_timeout(500)
    opts = pg.locator("#pilSel option").all_inner_texts(); check("piloto muestra expedientes del servidor", any("PRUEBA" in o for o in opts))
    pg.select_option("#pilSel", label=[o for o in opts if "PRUEBA" in o][0]); pg.wait_for_selector("#pilRight .dec2"); pg.evaluate("document.querySelectorAll('#pilLeft details.sec').forEach(x=>x.open=true)")
    check("expediente de PRUEBA completo → GO fundamentado (datos ficticios)", pg.inner_text("#pilRight .dec2") == "GO"); pg.wait_for_selector("#pilRight .sbar"); check("escenarios de PVP y precios normalizados visibles", pg.locator("#pilRight .sbar").count() >= 3 and "€ por cápsulas" in pg.inner_text("#pilRight"))
    pg.screenshot(path=f"{OUT}/06_piloto_prueba_GO_1600x840.png")
    pg.fill("[data-p='costDocs.cost.evidence']", ""); pg.click("#pilSave"); pg.wait_for_timeout(900)
    check("quitar la evidencia de un coste impide GO (REVISAR)", pg.inner_text("#pilRight .dec2") == "REVISAR" and "Coste sin documentar" in pg.inner_text("#pilRight"))
    pg.fill("[data-p='costDocs.cost.evidence']", "PRUEBA ficticia cost"); pg.fill("[data-p='econ.cost']", "16"); pg.click("#pilSave"); pg.wait_for_timeout(900); check("coste alto documentado → NO-GO", pg.inner_text("#pilRight .dec2") == "NO-GO")
    pg.fill("[data-p='econ.cost']", "3"); pg.click("#pilSave"); pg.wait_for_timeout(900); check("restaurar → GO", pg.inner_text("#pilRight .dec2") == "GO")
    csvp = os.path.join(tempfile.mkdtemp(), "c.csv"); open(csvp, "w").write(f"name,asin,priceGross,shipping,packUnits,contentValue,source,date\nX1,B1,18,0,1,120,PRUEBA,{ago(3)}\nX2,B2,22,0,1,120,PRUEBA,{ago(3)}\nX3,B3,25,0,1,120,PRUEBA,{ago(3)}\n")
    pg.set_input_files("#pilCsv", csvp); pg.wait_for_selector("#pilMsg:has-text('Importadas')"); check("importación CSV de competidores en servidor", "Importadas 3" in pg.inner_text("#pilMsg"))
    pg.reload(); pg.wait_for_selector(".sessu"); pg.click("#tabs button[data-tab=panel]"); pg.click("[data-tab=piloto]"); pg.wait_for_timeout(600); pg.select_option("#pilSel", label=[o for o in pg.locator("#pilSel option").all_inner_texts() if "PRUEBA" in o][0]); pg.wait_for_timeout(400)
    check("persistencia servidor: tras recargar siguen los 3 competidores importados", "3 filas cargadas" in pg.inner_text("#pilLeft"))
    pg.select_option("#pilSel", index=0); pg.wait_for_timeout(400)
    opts = pg.locator("#pilSel option").all_inner_texts()
    # --- piloto real INCOMPLETO ---
    pg.evaluate("1"); pg.click("[data-tab=panel]"); pg.click("[data-tab=piloto]")
    # crear piloto PHIVITAL vía UI: primero necesitamos que no exista
    n_before = pg.locator("#pilSel option").count()
    r = pg.evaluate("""async () => { const V = window.V03.V; const r = await window.V03.api('POST','/api/pilot/phivital/init',{account:V.account}); return r.j; }"""); pg.reload(); pg.wait_for_selector(".sessu"); pg.click("#tabs button[data-tab=panel]"); pg.click("[data-tab=piloto]"); pg.wait_for_timeout(600)
    pg.select_option("#pilSel", label=[o for o in pg.locator("#pilSel option").all_inner_texts() if "piloto" in o][0]); pg.wait_for_selector("#pilRight .dec2"); pg.evaluate("document.querySelectorAll('#pilLeft details.sec').forEach(x=>x.open=true)")
    check("piloto real: origen INCOMPLETO y decisión REVISAR (no GO, no NO-GO firme)", "INCOMPLETO" in pg.inner_text("#pilLeft") and pg.inner_text("#pilRight .dec2") == "REVISAR")
    check("piloto real: costes sin documentar listados y economía sin valores inventados", "Coste sin documentar" in pg.inner_text("#pilRight") and "Datos económicos inválidos" in pg.inner_text("#pilRight"))
    check("piloto real: sin demanda ni competidores inventados", "0 filas cargadas" in pg.inner_text("#pilLeft") and "Sin datos de demanda" in pg.inner_text("#pilRight"))
    check("piloto real: datos regulatorios pendientes visibles", pg.locator("#pilLeft .ckrow").count() >= 6)
    pg.screenshot(path=f"{OUT}/05_piloto_phivital_incompleto_1600x840.png")
    pg.click("#pilReq"); pg.wait_for_timeout(500); check("solicitud de aprobación registrada", "Solicitud registrada" in pg.inner_text("#pilMsg"))
    # --- Historial ---
    pg.click("[data-tab=hist]"); pg.wait_for_selector("#histRoot table"); pg.wait_for_timeout(300); h = pg.inner_text("#histRoot")
    check("historial: consultas, ejecuciones IA (SIMULADA), aprobaciones y auditoría íntegra", "Historial de consultas" in h and "SIMULADA" in h and "Registro de auditoría" in h and "íntegra" in h)
    check("analista no ve botones de aprobar", pg.locator("[data-ap]").count() == 0)
    pg.screenshot(path=f"{OUT}/07_historial_auditoria_1600x840.png")
    # --- Aprobador ---
    pg.click("#lgOut"); pg.wait_for_timeout(300); pg.click("#lgOpen"); pg.fill("#lgU", "pablo"); pg.fill("#lgP", "aprobador-pass-1"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(600)
    pg.click("[data-tab=hist]"); pg.wait_for_selector("[data-ap]"); check("aprobador ve botones de decisión", pg.locator("[data-ap]").count() >= 1)
    pg.once("dialog", lambda dlg: (res.append(("dialogo: " + dlg.message[:60], True)), dlg.accept())); pg.click("[data-ap=aprobada] >> nth=0"); pg.wait_for_timeout(700)
    check("aprobar un expediente que no es GO es rechazado por el servidor", any(r[0].startswith("dialogo:") and "no se puede aprobar" in r[0] for r in res))
    pg.click("[data-tab=estado]"); pg.wait_for_timeout(500); check("Estado: conexiones deshabilitadas por defecto, sin credenciales", "DESHABILITADO" in pg.inner_text("#estadoRoot"))
    check("sin errores JS en toda la sesión", not errs)
    # --- móvil ---
    m = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2); mp_ = m.new_page(); mp_.goto(U); mp_.wait_for_selector("#tabs"); mp_.click("#tabs button[data-tab=panel]"); mp_.wait_for_selector("#kpis .kpi"); mp_.wait_for_timeout(300)
    mp_.screenshot(path=f"{OUT}/08_movil_panel_390x844.png", full_page=False)
    check("móvil sin desbordamiento horizontal del documento", mp_.evaluate("document.documentElement.scrollWidth<=392"))
    b.close()
f = sum(1 for _, c in res if not c); print(f"{len(res) - f}/{len(res)} OK"); json.dump([{"check": n, "ok": c} for n, c in res], open(os.path.join(ROOT, "tests", "ui_results.json"), "w"), ensure_ascii=False, indent=1); sys.exit(1 if f else 0)
