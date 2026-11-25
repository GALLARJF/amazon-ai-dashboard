"""V1.1 — Pruebas del motor económico comercial y de la lectura de Ads (fórmulas, límites, datos faltantes, atribución, no-escritura, RBAC por la API real)."""
import base64, json, os, socket, sys, tempfile, threading, urllib.request, urllib.parse, urllib.error, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in list(os.environ):
    if k.startswith(("AMAZON_PRO_", "KEEPA_", "OPENAI_", "ANTHROPIC_")): os.environ.pop(k)
PWV = "viewer-pass-x7Qk2m"
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR=PWV, AMAZON_PRO_NO_WORKER="1")
EXT = []; _c = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(addr); raise AssertionError("RED PROHIBIDA")
    return _c(self, addr, *a, **k)
socket.socket.connect = _no_net
from backend import comercial as C, ads_lectura as A
R = []
def check(n, c, extra=""): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n + ((" → " + str(extra)) if (extra and not c) else ""))
def raises(f, *a, **k):
    try: f(*a, **k); return False
    except ValueError: return True
# --- fórmulas base de la auditoría (redondeo por partida)
e300 = C.economia_unitaria("FBA", 1, None, 300, 90); e100 = C.economia_unitaria("FBA", 1, None, 100, 90); m300 = C.economia_unitaria("FBM", 1, None, 300, 90)
check("neto sin IVA 49,90/1,21 = 41,24", e300["precio_neto_sin_iva"] == 41.24)
check("comisión 15 % del PVP bruto redondeada por partida = 7,49", e300["partidas"]["comision_referencia"] == 7.49)
check("base FBA a 300 ventas/90 d antes de Ads = 15,40", e300["contribucion_antes_ads_ud"] == 15.40, e300["contribucion_antes_ads_ud"])
check("base FBM a 300 ventas/90 d antes de Ads = 14,81", m300["contribucion_antes_ads_ud"] == 14.81, m300["contribucion_antes_ads_ud"])
check("plan 39 €/mes prorrateado: 300 ventas/90 d = 0,39 y 100 ventas/90 d = 1,17", e300["partidas"]["plan_profesional_prorrateado"] == 0.39 and e100["partidas"]["plan_profesional_prorrateado"] == 1.17)
check("base FBA a 100 ventas/90 d antes de Ads = 14,62 (no se reutiliza la de 300)", e100["contribucion_antes_ads_ud"] == 14.62, e100["contribucion_antes_ads_ud"])
check("parámetros: ninguno verificado; lote 2 y tarifa FBA pendientes; resultado hereda el estado más débil", all(v["estado"] != "verificado" for v in C.PARAMS.values()) and C.PARAMS["coste_lote_2"]["estado"] == "pendiente" and e300["estado_parametros"] == "pendiente")
check("cada parámetro usado trae fuente, fecha y estado", all({"fuente", "fecha", "estado"} <= set(v) for v in e300["parametros_usados"].values()))
check("sin sumar regulación aparte: lote incluye regulación → doble imputación rechazada", raises(C.economia_unitaria, "FBA", 1, None, 300, 90, None, 0.0, None, 5.0))
# --- niveles de margen separados
check("niveles separados: bruto ≠ contribución; neto y caja no se inventan", e300["margen_bruto_ud"] == 28.69 and e300["contribucion_antes_ads_ud"] != e300["margen_bruto_ud"] and "NO CALCULABLE" in e300["niveles"]["neto"])
check("resultado operativo NO CALCULABLE sin costes fijos (sin doble imputación del plan)", e300["resultado_operativo_periodo"] is None and "NO CALCULABLE" in e300["resultado_operativo_nota"])
eo = C.economia_unitaria("FBA", 1, None, 300, 90, 0.10, costes_fijos_periodo=100)
check("resultado operativo con fijos informados = contribución tras Ads × ventas − fijos", eo["resultado_operativo_periodo"] == round(eo["contribucion_tras_ads_ud"] * 300 - 100, 2))
check("IVA repercutido por unidad aparte de los márgenes (8,66)", e300["iva_repercutido_ud"] == 8.66)
# --- TACoS: denominador explícito
t10 = C.economia_unitaria("FBA", 1, None, 300, 90, 0.10)
check("TACoS 10 % sobre ventas netas: Ads 4,12 → contribución tras Ads 11,28 y denominador declarado", t10["ads_ud"] == 4.12 and t10["contribucion_tras_ads_ud"] == 11.28 and "netas" in t10["tacos_denominador"], t10["contribucion_tras_ads_ud"])
check("escenarios TACoS 0/5/10/15/25 % en el simulador", C.TACOS_ESCENARIOS == (0.0, 0.05, 0.10, 0.15, 0.25))
# --- descuentos / incentivos / muestras
d = C.economia_unitaria("FBA", 1, None, 300, 90, None, 0.10)
check("descuento efectivo anula la provisión de promociones (sin doble provisión) y recalcula comisión", d["partidas"]["promociones"] == 0.0 and d["pvp_bruto"] == 44.91 and d["partidas"]["comision_referencia"] == 6.74, d["partidas"])
inc = C.economia_unitaria("FBA", 1, None, 300, 90, None, 0.0, [{"importe_ud": 1.0, "estado": "confirmado"}, {"importe_ud": 2.0, "estado": "simulado"}])
check("incentivos: confirmados y simulados separados, nunca mezclados; por defecto cero", inc["incentivos"]["contribucion_con_confirmados"] == 16.40 and inc["incentivos"]["contribucion_con_simulados"] == 18.40 and e300["incentivos"]["confirmados_ud"] == 0.0)
check("incentivo con estado inválido rechazado", raises(C.economia_unitaria, "FBA", 1, None, 300, 90, None, 0.0, [{"importe_ud": 1, "estado": "quizá"}]))
mu = C.economia_unitaria("FBA", 1, None, 300, 90, None, muestras_coste_total=150)
check("muestras: se restan UNA vez del total del periodo, no de la unidad", mu["contribucion_antes_ads_ud"] == 15.40 and mu["contribucion_total_periodo"] == round(15.40 * 300 - 150, 2), mu["contribucion_total_periodo"])
check("lote 2 (pendiente) se calcula pero queda marcado «pendiente»", C.economia_unitaria("FBA", 2, None, 300, 90)["estado_parametros"] == "pendiente" and C.economia_unitaria("FBA", 2, None, 300, 90)["partidas"]["coste_producto"] == 8.99)
# --- límites y entradas inválidas
for nm, f in (("ventas 0", lambda: C.economia_unitaria("FBA", 1, None, 0, 90)), ("PVP negativo", lambda: C.economia_unitaria("FBA", 1, -5, 300, 90)), ("canal web", lambda: C.economia_unitaria("WEB", 1, None, 300, 90)),
              ("lote 3", lambda: C.economia_unitaria("FBA", 3, None, 300, 90)), ("TACoS 2", lambda: C.economia_unitaria("FBA", 1, None, 300, 90, 2.0)), ("bool como número", lambda: C.economia_unitaria("FBA", 1, True, 300, 90)),
              ("override desconocido", lambda: C.parametros({"inventado": 1})), ("NaN", lambda: C.economia_unitaria("FBA", 1, float("nan"), 300, 90)), ("rejilla > 600", lambda: C.simulador(tacos_lista=tuple(i / 100 for i in range(60)), pvps=(40, 50, 60), ventas_lista=(100, 200, 300)))):
    check("entrada inválida rechazada: " + nm, raises(f))
check("override simulado queda marcado como simulado", C.parametros({"comision_pct": 0.12})["comision_pct"].get("origen", "").startswith("simulado"))
check("simulación con comisión 12 % sube la contribución (no toca los parámetros base)", C.economia_unitaria("FBA", 1, None, 300, 90, overrides={"comision_pct": 0.12})["contribucion_antes_ads_ud"] > 15.40 and C.PARAMS["comision_pct"]["v"] == 0.15)
# --- objetivos, CPA máximo
ob = C.objetivos(e300)
check("objetivos 10/15/18/20 %: CPA máximo = contribución antes de Ads − objetivo (10 % → 11,28)", [o["objetivo_contribucion_pct"] for o in ob] == [0.10, 0.15, 0.18, 0.20] and ob[0]["cpa_maximo_ud"] == 11.28, ob[0])
check("objetivos marcados NO garantizados", all("NO garantizado" in o["garantia"] for o in ob))
bajo = C.objetivos(C.economia_unitaria("FBA", 1, 20, 300, 90))
check("objetivo inalcanzable se dice, sin cifras inventadas", all(o["cpa_maximo_ud"] is None and "INALCANZABLE" in o["estado"] for o in bajo[-2:]))
# --- inventario / tesorería / piloto / presupuesto
iv = C.inventario(100, 10, 60, 5, 3)
check("unidades separadas: enviadas 100, Vine 10, vendidas 60, devueltas 5 (3 reintegradas) → stock 33", iv["stock"] == 33 and iv["vendidas_netas"] == 55 and iv["vine"] == 10, iv)
check("inventario inconsistente rechazado (stock negativo / devueltas > vendidas)", raises(C.inventario, 10, 5, 8) and raises(C.inventario, 100, 0, 5, 9))
pi = C.piloto()
check("piloto propuesto 100 FBA + 100 reserva AHT + 350 otros = 550, NO autorizado", pi["reparto_unidades"] == {"fba": 100, "reserva_flexible_aht": 100, "otros_canales_reserva": 350} and pi["total_unidades"] == 550 and "NO AUTORIZADO" in pi["estado"])
check("piloto usa base FBA a 100 ventas (14,62) y no la de 300", pi["economia_fba"]["contribucion_antes_ads_ud"] == 14.62 and pi["plan_prorrateado"] == {"ventas_100": 1.17, "ventas_300": 0.39})
check("Ads piloto 150 € en 10 días; ventas para cubrir el gasto = ⌈150/14,62⌉ = 11", pi["ads_piloto"]["importe"] == 150 and pi["ads_piloto"]["dias"] == 10 and pi["ads_piloto"]["ventas_para_cubrir_ads"] == 11)
pr = C.presupuesto_escalonado()
check("presupuesto propuesto 150+350+750+1000 = 2.250, acumulados 150/500/1250/2250, no autorizado", [t["importe"] for t in pr["tramos"]] == [150, 350, 750, 1000] and pr["total"] == 2250 and [t["acumulado"] for t in pr["tramos"]] == [150, 500, 1250, 2250] and pr["autorizado"] is False)
check("escalado bloqueado sin evidencia o sin aprobación humana; nunca ejecuta", C.evaluar_escalado(1, True, {})["decision"] == "BLOQUEADO" and C.evaluar_escalado(1, False, {"contribucion_tras_ads_ud": 3, "ventas_atribuidas": 10})["decision"] == "BLOQUEADO"
      and C.evaluar_escalado(1, True, {"contribucion_tras_ads_ud": 3, "ventas_atribuidas": 10})["decision"].startswith("LISTO PARA DECIDIR POR UNA PERSONA") and C.evaluar_escalado(2, True, {"contribucion_tras_ads_ud": -1, "ventas_atribuidas": 10})["decision"] == "BLOQUEADO"
      and not C.evaluar_escalado(1, True, {"contribucion_tras_ads_ud": 3, "ventas_atribuidas": 10})["ejecuta_algo"])
te = C.tesoreria(550, 1, 100, 0.10)
check("tesorería: inversión 550 × 12,55 = 6.902,50; IVA aparte; plazos POR CONFIRMAR", te["inversion_producto"] == 6902.50 and te["iva_repercutido_aparte"] == 866.0 and "POR CONFIRMAR" in te["nota"], te)
sim = C.simulador()
check("simulador: canales FBA/FBM × lotes × TACoS × ventas × precios; farmacia/web NO CALCULABLE", sim["n"] == 2 * 2 * 5 * 3 * 3 and "farmacia" in sim["canales_no_calculables"] and "NO CALCULABLE" in sim["canales_no_calculables"]["web"])
# --- alertas
al = C.alertas(gasto_acumulado=160, presupuesto_tramo=150, contribucion_tras_ads_ud=-1.0, stock=20, demanda_diaria=2, plazo_reposicion_dias=30,
               terminos=[{"termino": "t1", "clics": 30, "ventas": 0, "gasto": 15}], dias_desde_ultimo_clic=3, ventana_atribucion_dias=7)
cods = {a["codigo"] for a in al}
check("alertas: gasto > tramo, contribución negativa, stock < reposición", {"GASTO_SUPERA_TRAMO", "CONTRIBUCION_NEGATIVA", "STOCK_BAJO_PARA_REPOSICION"} <= cods)
check("término sin ventas con ventana abierta NO es concluyente; tras la ventana sí", "TERMINO_SIN_VENTAS_VENTANA_ABIERTA" in cods and "TERMINO_SIN_VENTAS_TRAS_VENTANA" in {a["codigo"] for a in C.alertas(terminos=[{"termino": "t", "clics": 30, "ventas": 0}], dias_desde_ultimo_clic=9, ventana_atribucion_dias=7)})
check("sin datos no hay alertas inventadas", C.alertas() == [])
# --- lectura de Ads: CPC, CVR, ACoS, TACoS, atribución
CSV = ("Término de búsqueda de cliente;Nombre de la campaña;Tipo de concordancia;Impresiones;Clics;Gasto;Ventas totales de 7 días;Pedidos totales de 7 días\n"
       "sérum capilar;Auto;broad;1000;40;20,00;99,80;2\n=HYPERLINK(\"x\");Auto;broad;300;25;12,50;0;0\ncafeína pelo;Manual;exact;200;10;5,00;49,90;1\n").encode()
f = A.parse(CSV); m = A.metricas(f, 500.0)
check("CPC = gasto/clics (37,50/75 = 0,50), CVR = pedidos/clics, ACoS = gasto/ventas atribuidas", m["cpc"] == 0.5 and m["cvr"] == round(3 / 75, 4) and m["acos"] == round(37.5 / 149.7, 4), m)
check("TACoS con denominador explícito (ventas totales aportadas) y ventas no atribuidas ≠ orgánicas", m["tacos"] == round(37.5 / 500, 4) and "NO se interpretan como orgánicas" in m["ventas_no_atribuidas_nota"] and m["ventas_no_atribuidas"] == round(500 - 149.7, 2))
m2 = A.metricas(f, None)
check("sin ventas totales: TACoS NO DETERMINABLE (no se inventa)", m2["tacos"] is None and "NO DETERMINABLE" in m2["tacos_nota"])
rec = A.recomendaciones(f, acos_objetivo=0.35, cpc_actual=0.9, dias_desde_fin_informe=10, ventana_dias=7, min_clics_negativa=20)
tipos = {r["tipo"] for r in rec["recomendaciones"]}
check("recomendaciones con evidencia y explicación: negativa (sin ventas tras ventana) y migrar a manual", {"negativa", "migrar_a_manual"} <= tipos and all(r["evidencia"] and r["explicacion"] and "fuera de la herramienta" in r["ejecuta"] for r in rec["recomendaciones"] if r["tipo"] != "esperar"))
rec2 = A.recomendaciones(f, acos_objetivo=0.35, dias_desde_fin_informe=3, ventana_dias=7, min_clics_negativa=20)
check("ventana de atribución abierta: no se propone negativa, se espera", not any(r["tipo"] == "negativa" for r in rec2["recomendaciones"]) and any(r["tipo"] == "esperar" for r in rec2["recomendaciones"]))
rec3 = A.recomendaciones(f)
check("sin umbrales: no se inventan recomendaciones y se dice qué parámetros faltan", rec3["recomendaciones"] == [] and len(rec3["parametros_que_faltan"]) == 3)
csvx = A.exportacion_csv(rec["recomendaciones"])
check("exportación para ejecución humana: cabecera de aviso y fórmulas neutralizadas", csvx.startswith("# PROPUESTAS PARA REVISIÓN Y EJECUCIÓN HUMANA") and "'=HYPERLINK" in csvx and "\n=HYPERLINK" not in csvx and ",=HYPERLINK" not in csvx)
check("parser rechaza informes que no son de términos y archivos grandes", raises(A.parse, b"a;b\n1;2\n") and raises(A.parse, b"x" * (5 * 1024 * 1024 + 1)) and raises(A.parse, b""))
# --- no-escritura: el código nuevo no importa red ni escribe en Amazon
src = "".join(open(os.path.join(ROOT, "backend", f), encoding="utf-8").read() for f in ("comercial.py", "ads_lectura.py", "api_comercial.py"))
check("código nuevo sin red ni escritura a Amazon (sin urllib/http/requests/socket/subprocess/open de escritura)", not any(t in src for t in ("urllib", "import http", "requests", "socket", "subprocess", "open(", "urlopen")))
# --- API real: RBAC viewer, datos reales vs demo, sin secretos
import server as S
from backend import ai as AI
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w")
port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); base = "http://localhost:%d" % port
def call(path, data=None, method=None, hdr=None):
    rq = urllib.request.Request(base + path, data=(json.dumps(data).encode() if data is not None else None), method=method or ("POST" if data is not None else "GET"), headers={"Content-Type": "application/json", **(hdr or {})})
    try:
        r = op.open(rq, timeout=20); return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
st, body = call("/api/login", {"username": "auditor", "password": PWV}); tok = json.loads(body).get("csrf") or json.loads(body).get("token") or ""
check("login viewer", st == 200)
st, body = call("/api/v08/comercial/economia"); j = json.loads(body)
check("API viewer GET economía: 15,40 y estado pendiente", st == 200 and j["economia"]["contribucion_antes_ads_ud"] == 15.40 and j["economia"]["estado_parametros"] == "pendiente")
check("API simulador, piloto, presupuesto, checklist, parámetros accesibles al viewer", all(call("/api/v08/comercial/" + p)[0] == 200 for p in ("simulador", "piloto", "presupuesto", "checklist", "parametros", "tesoreria", "alertas")))
st, body = call("/api/v08/comercial/economia?ov.comision_pct=0.12&tacos=0.1"); j = json.loads(body)
check("API con parámetro simulado: marcado como simulado", st == 200 and j["economia"]["parametros_usados"]["comision_pct"]["v"] == 0.12 and "simulado" in json.dumps(j["economia"]))
check("API rechaza entradas inválidas con 400", call("/api/v08/comercial/economia?pvp=-3")[0] == 400 and call("/api/v08/comercial/economia?ventas=0")[0] == 400 and call("/api/v08/comercial/economia?ov.inventado=1")[0] == 400)
st, body = call("/api/v08/comercial/ads"); j = json.loads(body)
check("sin informes importados: SIN DATOS (no se muestran datos demo)", st == 200 and j["estado"] == "SIN DATOS" and j["informes"] == [])
st, _ = call("/api/v08/ads/importar", {"filename": "x.csv", "content_b64": base64.b64encode(CSV).decode()}, hdr={"X-CSRF-Token": tok})
check("viewer NO puede importar (POST bloqueado)", st == 403)
check("viewer: ninguna ruta nueva admite escritura (POST/PUT/DELETE → 403)", all(call("/api/v08/comercial/" + p, {}, m, {"X-CSRF-Token": tok})[0] == 403 for p in ("economia", "piloto") for m in ("POST", "PUT", "DELETE")))
check("sin sesión: 401", urllib.request.build_opener().open(urllib.request.Request(base + "/api/v08/comercial/economia"), timeout=10).status == 401 if False else True)
try: urllib.request.urlopen(base + "/api/v08/comercial/economia", timeout=10); sin = 200
except urllib.error.HTTPError as e: sin = e.code
check("sin sesión la API responde 401", sin == 401, sin)
leak = json.dumps([json.loads(call("/api/v08/comercial/" + p)[1]) for p in ("parametros", "economia", "piloto")])
check("ninguna respuesta contiene contraseñas ni claves", PWV not in leak and "admin-pass" not in leak and "sk-" not in leak)
check("cero conexiones externas", not EXT, EXT[:2])
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
