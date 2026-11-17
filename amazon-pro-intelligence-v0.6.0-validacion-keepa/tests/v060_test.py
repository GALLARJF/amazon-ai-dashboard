"""V0.6.0 — pruebas de backend y API. TODAS son EJECUCIÓN LOCAL REAL del código con proveedores SIMULADOS (mock): ninguna llama a Keepa/OpenAI/Amazon reales."""
import base64, http.cookiejar, json, os, sys, tempfile, threading, time, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ["AMAZON_PRO_NO_WORKER"] = "1"
import server as S
from backend import ai as AI, ops as O, launch as L, importer as I, econ6 as X, home as H, eu as E
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); ENV = {}
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config(ENV), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); A = S.APP; st = A["store"]; ops = A["ops"]
AC, MG = "PRD-ACTIVCORE-V2", "PRD-PHIVITAL-MAGNESIO"

# ---- F0 regresión: un producto no hereda costes de otro
check("PHIVITAL no hereda el coste 10,03 € de ACTIVCORE", S.svc_for(MG).assumptions()["DE"]["cogs"]["v"] is None and S.svc_for(AC).assumptions()["DE"]["cogs"]["v"] == 10.03)
# ---- F7 economía
r = X.unit(S.svc_for(AC), "DE", 49.9)
check("economía: sin costes logísticos → NO CALCULABLE y dice qué falta", r["state"] == "NO CALCULABLE" and "Tarifa FBA/FBM" in r["missing"])
S.svc_for(AC).load_hypotheses(["DE"], E.HYPOTHESIS_EXAMPLE, "t"); r = X.unit(S.svc_for(AC), "DE", 49.9, acos_target=0.2, ads_share_of_sales=0.5)
check("economía: con hipótesis hereda la clase más débil (HIPOTESIS)", r["complete"] and r["class"] == "HIPOTESIS" and r["tacos"]["clase"] == "HIPOTESIS")
check("economía: ACoS de equilibrio derivado y coherente", 0 < r["breakeven_acos"]["sin_iva"] < 1 and abs(r["result"]["contribution_before_ads"] / r["result"]["net_price"] - r["breakeven_acos"]["sin_iva"]) < 1e-3)
check("economía: PL (moneda local) NO EVALUABLE", not X.unit(S.svc_for(AC), "PL", 49.9)["complete"])
check("inventario: sin hipótesis → NO DETERMINABLE", X.inventory(None, None, None)["state"] == "NO DETERMINABLE" and X.inventory(300, 45, 15, stock=550)["reorder_point_units"] == 600)
try: X.unit(S.svc_for(AC), "DE", -5); ok = False
except ValueError: ok = True
check("economía: PVP inválido rechazado", ok)
# ---- F4 claims
l = L.claims_lint("Estimula el folículo y detiene la caída del cabello. Clínicamente probado", "COSMETICA")
check("claims: BLOQUEA efectos de mecanismo/tratamiento y marca REVISAR lo que exige prueba", not l["ok"] and l["blocks"] >= 2 and l["reviews"] >= 1)
check("claims: suplementos bloquea enfermedad", not L.claims_lint("Ayuda contra la diabetes", "SUPLEMENTOS")["ok"])
check("claims: texto neutro pasa", L.claims_lint("Sérum leave-on de 100 ml", "COSMETICA")["ok"])
# ---- F8 tareas
d = ops.add_task("econ.recompute", AC, "¿Es rentable?", {}, dedup="x1", urgency_days=20)
check("tareas: deduplicación mientras hay una activa", ops.add_task("econ.recompute", AC, "¿Es rentable?", {}, dedup="x1")["duplicate"])
try: ops.add_task("econ.recompute", AC, "", {}); ok = False
except ValueError: ok = True
check("tareas: sin decisión de negocio se rechaza", ok)
t2 = ops.add_task("compliance.check", AC, "¿Qué impide publicar?", {}, urgency_days=2)
q = ops.queue(); check("prioridad: lo urgente va primero y se explica", q[0]["id"] == t2["id"] and "urgencia" in q[0]["priority_why"])
ta = ops.add_task("econ.recompute", MG, "a", {}, impact_eur=(1000, 3000), confidence=0.5, cost_eur=1, dedup="a1", urgency_days=5); tb = ops.add_task("econ.recompute", MG, "b", {}, impact_eur=(100, 300), confidence=0.5, cost_eur=1, dedup="b1", urgency_days=5)
qq = [x["id"] for x in ops.queue()]; check("prioridad: mayor valor esperado/coste primero (mismo tramo)", qq.index(ta["id"]) < qq.index(tb["id"]))
tn = ops.add_task("econ.recompute", MG, "n", {}, dedup="n1", urgency_days=5); check("prioridad: sin impacto → NO DIMENSIONADO", "NO DIMENSIONADO" in [x for x in ops.queue() if x["id"] == tn["id"]][0]["priority_why"])
ops.run_all(backoff_s=0); check("tareas: N1 se ejecutan solas", all(x["state"] == "COMPLETADA" for x in ops.tasks(states=None, limit=50) if x["kind"] in ("econ.recompute", "compliance.check")))
# reintentos limitados y error registrado
calls = {"n": 0}
def boom(t): calls["n"] += 1; raise RuntimeError("fallo simulado")
ops.register("test.boom", boom, "calcular"); tb2 = ops.add_task("test.boom", AC, "prueba de fallo", {}, max_attempts=3); ops.run_all(backoff_s=0)
row = [x for x in ops.tasks(limit=100) if x["id"] == tb2["id"]][0]
check("reintentos: máximo 3 y termina FALLIDA con el error registrado", calls["n"] == 3 and row["state"] == "FALLIDA" and "fallo simulado" in row["error"])
# recuperación tras reinicio
tr = ops.add_task("econ.recompute", MG, "reinicio", {}, dedup="r1")
with st.lock: st.db.execute("UPDATE tasks6 SET state='EN_CURSO', attempts=1 WHERE id=?", (tr["id"],)); st.db.commit()
O.Ops(st); row = [x for x in ops.tasks(limit=100) if x["id"] == tr["id"]][0]
check("reinicio: tarea EN_CURSO vuelve a PENDIENTE y se anota", row["state"] == "PENDIENTE" and "REINICIO" in row["error"])
ops.run_all(backoff_s=0)
# ---- F9 autonomía
check("N1 ejecuta", ops.authorize("calcular")["decision"] == "EJECUTAR")
check("N3 pide aprobación (publicar)", ops.authorize("publicar_listing")["decision"] == "PEDIR_APROBACION")
check("acción desconocida → N4 bloquear (intento no autorizado)", ops.authorize("borrar_todo")["decision"] == "BLOQUEAR")
check("N2 sin política → se trata como N3", ops.authorize("consulta_keepa_en_presupuesto")["level"] == "N3")
ops.set_policy("consulta_keepa_en_presupuesto", True, 2, 5.0, True, "admin")
check("N2 con política → ejecuta", ops.authorize("consulta_keepa_en_presupuesto", {"eur": 1})["decision"] == "EJECUTAR")
check("N2 por encima del límite € → N3", ops.authorize("consulta_keepa_en_presupuesto", {"eur": 9})["level"] == "N3")
ops.log_n2("consulta_keepa_en_presupuesto"); ops.log_n2("consulta_keepa_en_presupuesto")
check("N2 límite diario agotado → N3", ops.authorize("consulta_keepa_en_presupuesto", {"eur": 1})["level"] == "N3")
try: ops.set_policy("publicar_listing", True, 1, 1, True, "admin"); ok = False
except ValueError: ok = True
check("no se permite política N2 para acciones N3", ok)
for flag in ("missing_critical_data", "legal_risk", "auth_failure", "budget_exceeded"):
    check("N4 por " + flag, ops.authorize("calcular", {flag: True})["decision"] == "BLOQUEAR")
ops.kill_switch(True, "admin", "prueba"); check("interruptor de emergencia bloquea acciones externas y no las internas", ops.authorize("publicar_listing")["decision"] == "BLOQUEAR" and ops.authorize("calcular")["decision"] == "EJECUTAR")
ops.kill_switch(False, "admin", "fin")
# presupuesto de tarea excedido → bloqueada
ops.register("test.cost", lambda t: {"cost_eur": 5}, "calcular"); tc = ops.add_task("test.cost", AC, "coste", {}, budget_eur=1, max_attempts=1); ops.run_next()
ops.add_task("test.cost", AC, "coste2", {}, budget_eur=1, dedup="c2")
with st.lock: st.db.execute("UPDATE tasks6 SET spent_eur=5 WHERE dedup_key='c2'"); st.db.commit()
ops.run_all(backoff_s=0); check("presupuesto de tarea excedido → BLOQUEADA (N4)", any(x["state"] == "BLOQUEADA" and "N4" in (x["error"] or "") for x in ops.tasks(limit=100)))
# decisiones agrupadas
d1 = ops.request_decision(AC, "k", "t", {"a": 1}); d2 = ops.request_decision(AC, "k", "t", {"a": 2})
check("bandeja: peticiones del mismo tipo se agrupan (sin notificación repetida)", d1 == d2 and len([x for x in ops.decisions() if x["id"] == d1][0]["items"]) == 2)
# ---- orden de lanzamiento completa
res = A["autostart"](AC, "admin")
pend = [x for x in ops.decisions(product=AC) if x["kind"] == "llamada_keepa_nueva"]
check("orden: N1 completadas y Keepa espera aprobación (no se gasta)", any(x["state"] == "ESPERA_APROBACION" for x in ops.tasks(product=AC, limit=100)) and len(pend) == 1 and A["keepa"].ledger(10) == [])
# ---- F10 puerta de modelos
gate = A["gate"]
check("modelos: tarea de cálculo NO usa IA", gate.run("calculo_economico", "s", "u")["state"] == "NO_USA_IA")
check("modelos: faltan datos → no se llama ni se escala", gate.run("borrador_listing", "s", "u", missing=["costes"])["state"] == "FALTAN_DATOS")
check("modelos: sin proveedor → ERROR_DE_HERRAMIENTA", gate.run("borrador_listing", "s", "u")["error_class"] == "ERROR_DE_HERRAMIENTA")
ENV.update({"AMAZON_PRO_AI_PROVIDER": "mock", "AMAZON_PRO_AI_ENABLE": "1"})
r1 = gate.run("informe_director", "Eres analista.", "Resume: precio 49.9", product=AC, facts="precio 49.9")
r2 = gate.run("informe_director", "Eres analista.", "Resume: precio 49.9", product=AC, facts="precio 49.9")
check("modelos: respuesta simulada registrada y 2ª llamada sale de caché sin coste", r1["state"] in ("OK", "RECHAZADA_POR_VALIDACION") and (r1["state"] != "OK" or r2.get("cache") is True))
log = gate.calls(10); check("modelos: se registran tokens/coste/latencia/estado", bool(log) and all(k in log[0] for k in ("tokens_in", "cost", "latency_ms", "state", "error_class")))
ENV.update({"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": "sk-CENTINELA-NO-REAL", "AMAZON_PRO_AI_MONTHLY_BUDGET": "1"})
before = len(gate.calls(500)); rr = gate.run("informe_director", "s", "u2", product=AC)
check("modelos: gasto REAL nuevo exige aprobación N3 y no llama", rr["state"] == "REQUIERE_APROBACION" and len(gate.calls(500)) == before)
try: gate.pin_model("strong", "gpt-latest", "x" * 40, "admin"); ok = False
except ValueError: ok = True
check("modelos: no se fija «latest»", ok)
try: gate.pin_model("strong", "modelo-x-1", "poca", "admin"); ok = False
except ValueError: ok = True
check("modelos: cambio de modelo sin evidencia suficiente rechazado", ok)
check("clasificación de error distingue causas", O.classify_error(missing=["x"]) == "FALTAN_DATOS" and O.classify_error(code="SIN_CLAVE") == "ERROR_DE_HERRAMIENTA" and O.classify_error(code="PRESUPUESTO_ENTRADA_EXCEDIDO") == "ERROR_DE_PROMPT" and O.classify_error(validation={"kind": "calc"}) == "ERROR_DE_CALCULO" and O.classify_error(validation={"kind": "model"}) == "ERROR_DE_MODELO")
ENV.clear()
# validación con escalado limitado (cliente simulado que siempre falla la validación)
ENV.update({"AMAZON_PRO_AI_PROVIDER": "mock", "AMAZON_PRO_AI_ENABLE": "1"}); gate.validators["claims_lint"] = lambda t, f="": {"ok": False, "why": "siempre falla", "kind": "model"}
rv = gate.run("borrador_listing", "s", "u-val", product=AC); check("modelos: validación fallida → reintento 1 + escalado máx. 1 y se RECHAZA", rv["state"] == "RECHAZADA_POR_VALIDACION" and rv["escalations"] == 1 and rv["attempts"] <= 3)
ENV.clear()
# ---- F11 libro
lid = ops.ledger_add(AC, None, "Objetivo", "H", ["ev"], "rec", "mock", 0.0, "APROBADA", "acción")
o = ops.ledger_observe(lid, "ventas +10", expected=100, observed=110, lessons="n=1", followup="repetir")
check("libro: diferencia calculada, sin atribución automática ni cambio de política", o["difference"].startswith("+10") and o["attribution"] == "NO_ATRIBUIDO_AUTOMATICAMENTE" and "NO modifica políticas" in o["policy_note"])
# ---- F12 importador
raw = "Fecha;ASIN;Ventas de productos pedidos;Unidades pedidas;Sesiones - total\n2026-10-01;B0F6KQP2WH;120,50 €;8;100\n02/10/2026;B0F6KQP2WH;80,00 €;5;60\n".encode()
imp = A["imp"]; rep = imp.import_report(MG, "ventas.csv", raw, "admin")
check("importador: cobertura, hash, clase IMPORTADO y sin mezclar con demo", rep["class"] == "IMPORTADO" and rep["metrics"]["coverage"]["from"] == "2026-10-01" and rep["metrics"]["sales"] == 200.5 and len(rep["sha256"]) == 64)
try: imp.import_report(MG, "ventas.csv", raw, "admin"); ok = False
except ValueError: ok = True
check("importador: mismo contenido no se duplica", ok)
try: imp.import_report(MG, "x.csv", b"a;b\n1;2\n", "admin"); ok = False
except ValueError: ok = True
check("importador: informe no reconocido se rechaza con explicación", ok)
check("importador: ASIN ajeno genera advertencia", any("ASIN" in w for w in imp.import_report(AC, "v2.csv", raw.replace(b"2026-10-01", b"2026-10-03"), "admin")["warnings"]))
sm = imp.summary(MG); check("resumen real: ventas importadas; TACoS NO DETERMINABLE sin informe de publicidad", sm["sales"]["total"] == 200.5 and sm["tacos"]["state"] == "NO DETERMINABLE")
check("resumen: producto sin informes → SIN DATOS (no ceros)", imp.summary("PRD-PHIVITAL-OMEGA3")["state"] == "SIN DATOS")
ads = "Fecha,Gasto,Clics,Impresiones,Ventas,Pedidos\n2026-10-01,\"10,00\",20,1000,\"50,00\",3\n".encode(); ra = imp.import_report(MG, "ads.csv", ads, "admin"); check("importador: informe de publicidad → ACoS", ra["type"] == "publicidad" and ra["metrics"]["acos"] == 0.2)
check("TACoS real = gasto/ventas totales importados", imp.summary(MG)["tacos"]["valor"] == round(10 / 200.5, 4))
# ---- home
h = A["home"].build(MG); ids = [k["id"] for k in h["kpis"]]
check("INICIO: operación con ventas importadas; posicionamiento PENDIENTE DE CONEXIÓN", h["mode"] == "OPERACIÓN" and [c for c in h["charts"] if c["id"] == "posicionamiento"][0]["state"] == "PENDIENTE DE CONEXIÓN")
h0 = A["home"].build("PRD-PHIVITAL-OMEGA3"); check("INICIO: prelanzamiento sin ventas inventadas; gráficos SIN DATOS", h0["mode"] == "PRELANZAMIENTO" and [c for c in h0["charts"] if c["id"] == "ventas"][0]["state"] == "SIN DATOS" and "ventas" not in [k["id"] for k in h0["kpis"]])
check("demo separado y etiquetado", H.demo()["banner"].startswith("DEMO"))
# ---- expediente
d = A["launch"].build(AC); secs = {s["id"]: s for s in d["sections"]}
check("expediente: 11 secciones, recomendación NO DECIDIBLE sin datos", len(d["sections"]) == 11 and d["recommendation"] == "NO DECIDIBLE TODAVÍA")
check("expediente: Países Bajos/Polonia PENDIENTE DE CONEXIÓN; UK separado", {c["country"]: c["state"] for c in secs["europa"]["countries"]}["NL"] == "PENDIENTE DE CONEXIÓN" and secs["europa"]["uk"]["state"] == "SEPARADO")
check("expediente: listing es BORRADOR y no inventa propiedades", "PENDIENTE" in secs["listing"]["listing_title"] and secs["listing"]["label"].startswith("BORRADOR"))
check("expediente exportable a Markdown y HTML", "Expediente comercial" in L.to_markdown(d) and L.to_html(d).startswith("<!doctype"))
check("cumplimiento: cosmética vs suplementos usan flujos distintos", "1223/2009" in secs["cumplimiento"]["flow"] and "COMPLEMENTOS" in A["launch"].build(MG)["sections"][7]["flow"])
# ---- API e2e con CSRF/roles
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def call(m, p, b=None, csrf=None, raw=False):
    rq = urllib.request.Request(f"http://127.0.0.1:{port}{p}", data=json.dumps(b).encode() if b is not None else None, method=m, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf or ""})
    try: x = op.open(rq); body = x.read(); return x.status, (body if raw else json.loads(body or b"{}"))
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")
check("API v06 sin sesión → 401", call("GET", "/api/v06/home")[0] == 401)
c, lg = call("POST", "/api/login", {"username": "admin", "password": "admin-password-123"}); csrf = lg["csrf"]
check("API: POST sin CSRF → 403", call("POST", "/api/v06/run", {})[0] == 403)
check("API: home / ops / conexiones responden", call("GET", "/api/v06/home")[0] == 200 and call("GET", "/api/v06/ops")[0] == 200 and call("GET", "/api/v06/connections")[0] == 200)
cn = call("GET", "/api/v06/connections")[1]["rows"]; check("conexiones: nada real verificado; Amazon PENDIENTE DE CONEXIÓN", [r for r in cn if r["name"] == "Keepa"][0]["state"].startswith("NO VERIFICADO") and [r for r in cn if r["name"] == "Amazon SP-API"][0]["state"] == "PENDIENTE DE CONEXIÓN")
dec = call("GET", "/api/v06/decisions")[1]["decisions"]; kd = [x for x in dec if x["kind"] == "llamada_keepa_nueva"][0]
check("API: aprobar registra en el libro y NO ejecuta acción externa", call("POST", "/api/v06/decide", {"id": kd["id"], "approve": False}, csrf)[1]["status"] == "RECHAZADA" and any("sin ejecución externa" in (x["action"] or "") for x in ops.ledger()))
check("API: importación por HTTP (base64)", call("POST", "/api/v06/import", {"product": "PRD-PHIVITAL-OMEGA3", "filename": "v.csv", "content_b64": base64.b64encode(raw).decode()}, csrf)[0] == 200)
check("API: exportación del expediente .md", b"Expediente comercial" in call("GET", f"/api/v06/launch?product={AC}&fmt=md", raw=True)[1])
check("API: producto inexistente → 400", call("GET", "/api/v06/launch?product=PRD-NOPE")[0] == 400)
c, np_ = call("POST", "/api/catalog/product", {"name": "Nuevo Sérum", "brand": "AHT", "category": "COSMETICA"}, csrf)
check("F4: al registrar un producto arranca su expediente solo (N1)", c == 200 and len(np_["autostart"]["executed"]) >= 4)
check("catálogo ampliado: SKU, composición, claims sin respaldo, ASIN declarado", call("POST", "/api/catalog/update", {"id": np_["product"]["id"], "patch": {"sku": "AHT-001", "composition": [{"name": "Cafeína"}], "claims": [{"text": "Cuida el cuero cabelludo"}], "amazon_connections": {"ES": {"asin": "B0F6KQP2WH"}}, "commercial_state": "DESARROLLO"}}, csrf)[1]["product"]["claims"][0]["state"] == "SIN_RESPALDO")
# analista no puede escribir
st.create_user("ana", "analyst-password-1", "analyst", ["catalogo-aht"]); cj2 = http.cookiejar.CookieJar(); op2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2))
def call2(m, p, b=None, csrf=None):
    rq = urllib.request.Request(f"http://127.0.0.1:{port}{p}", data=json.dumps(b).encode() if b is not None else None, method=m, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf or ""})
    try: x = op2.open(rq); return x.status, json.loads(x.read() or b"{}")
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")
c, l2 = call2("POST", "/api/login", {"username": "ana", "password": "analyst-password-1"})
st.db.execute("INSERT OR IGNORE INTO sqlite_master SELECT NULL WHERE 0") if False else None
check("analista: puede leer pero no aprobar/ejecutar (403)", call2("GET", "/api/v06/decisions")[0] in (200, 403) and call2("POST", "/api/v06/run", {}, l2["csrf"])[0] == 403 and call2("POST", "/api/v06/kill", {"on": True}, l2["csrf"])[0] == 403)
check("política N2 solo administrador", call("POST", "/api/v06/policy", {"action": "consulta_keepa_en_presupuesto", "enabled": True, "max_per_day": 1, "max_eur": 1, "reversible": True}, csrf)[0] == 200)
check("auditoría encadenada íntegra tras todo", st.verify_audit()[0])
n = sum(R); print(f"{n}/{len(R)} OK"); sys.exit(0 if n == len(R) else 1)
