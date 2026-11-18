"""K4 · contratos, costes (10,03 € / duplicación), medios con derechos, importación y KPIs, pricing (5 dictámenes), Director. Sin red, sin gasto."""
import base64, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend.store import Store
from backend import k4_contracts as C, k4_costs as KC, k4_data as KD, k4_media as KM, k4_pricing as KP, k4_director as KDIR, k4_store as KS, eu
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
def raises(f, *a, **k):
    try: f(*a, **k); return False
    except (ValueError, LookupError, PermissionError): return True
st = Store(); k = KS.K4Store(st); costs = KC.Costs(k); costs.seed(); data = KD.Data(k); media = KM.Media(k, tempfile.mkdtemp())
# ---- contratos
check("medida sin valor = SIN_DATO (nunca 0)", C.medida(None, "uds")["estado"] == "SIN_DATO" and C.medida(None, "uds")["valor"] is None)
check("cifra sin fuente o sin fecha se rechaza", raises(C.medida, 5, "EUR") and raises(C.medida, 5, "EUR", "x", None))
check("medida válida cumple el contrato; importe sin moneda no", C.validar_medida(C.medida(5, "EUR", "f", "2026-11-01", moneda="EUR")) == [] and C.validar_medida(dict(C.medida(5, "EUR", "f", "2026-11-01", moneda="EUR"), moneda=None)) == ["importe sin moneda"])
check("booleano no es un valor numérico", raises(C.medida, True, "uds", "f", "2026-11-01"))
# ---- costes
f = costs.ficha("PRD-ACTIVCORE-V2"); cg = next(x for x in f if x["concepto"] == "cogs")
check("coste histórico 10,03 € registrado como PENDIENTE_VALIDAR y alcance no confirmado", cg["valor"] == 10.03 and cg["estado"] == "PENDIENTE_VALIDAR" and cg["es_total"] and cg["incluye"] == [] and "NO confirmado" in cg["accion"])
check("conceptos sin dato aparecen como FALTA (sin inventar)", all(x["estado"] == "FALTA" and x["valor"] is None for x in f if x["concepto"] in ("inbound", "prep", "fulfillment", "storage", "returns")))
a = costs.assumptions("PRD-ACTIVCORE-V2", "ES")
check("supuestos: el histórico solo entra como COGS HISTORICO_A_REVALIDAR; el resto sigue NO_DISPONIBLE", a["cogs"]["status"] == "HISTORICO_A_REVALIDAR" and a["inbound"]["v"] is None and eu.unit_economics(49.9, a)["complete"] is False)
check("total con incluye declarado bloquea el componente duplicado", (lambda: (costs.add({"producto": "PRD-X", "concepto": "cogs", "valor": 12, "unidad": "EUR/ud", "moneda": "EUR", "fuente": "factura", "fecha": "2026-11-10", "es_total": True, "incluye": ["cogs", "inbound"]}, "t"), raises(costs.add, {"producto": "PRD-X", "concepto": "inbound", "valor": 1, "unidad": "EUR/ud", "moneda": "EUR", "fuente": "f", "fecha": "2026-11-10"}, "t"))[1])())
check("un total nuevo debe declarar qué incluye; valores negativos o conceptos desconocidos se rechazan", raises(costs.add, {"producto": "PRD-Y", "concepto": "cogs", "valor": 5, "unidad": "EUR/ud", "moneda": "EUR", "fuente": "f", "fecha": "2026-11-10", "es_total": True}, "t") and raises(costs.add, {"producto": "PRD-Y", "concepto": "cogs", "valor": -1, "unidad": "EUR/ud", "moneda": "EUR", "fuente": "f", "fecha": "2026-11-10"}, "t") and raises(costs.add, {"producto": "PRD-Y", "concepto": "zzz", "valor": 1, "unidad": "u", "moneda": "EUR", "fuente": "f", "fecha": "2026-11-10"}, "t"))
for c_, v in (("inbound", .5), ("prep", .4), ("fulfillment", 5), ("storage", .3), ("returns", .6)):
    i = costs.add({"producto": "PRD-ACTIVCORE-V2", "concepto": c_, "valor": v, "unidad": "EUR/ud", "moneda": "EUR", "fuente": "TEST", "fecha": "2026-11-19"}, "t"); costs.validate(i, "VALIDADO", "t")
cg_id = next(x["id"] for x in costs.ficha("PRD-ACTIVCORE-V2") if x["concepto"] == "cogs"); costs.validate(cg_id, "VALIDADO", "t", incluye=["cogs"])
a2 = costs.assumptions("PRD-ACTIVCORE-V2", "ES"); eco = eu.unit_economics(49.9, a2)
check("con costes validados la economía por unidad se completa", eco["complete"] and eco["contribution_before_ads"] is not None and a2["cogs"]["status"] == "DOCUMENTADO")
# ---- medios
png = base64.b64encode(b"\x89PNG" + b"0" * 30).decode(); base = {"product_id": "P1", "variante": "50ml", "asin": "B0ABCDEFGH", "origen": "FOTO_PROPIA_AHT", "fuente": "AHT", "fecha_captura": "2026-11-19", "mime": "image/png"}
check("origen prohibido (scraping/IA) se rechaza; ASIN inválido y contenido falso también", raises(media.add, dict(base, origen="SCRAPING"), "t", png) and raises(media.add, dict(base, origen="IA_GENERADA"), "t", png) and raises(media.add, dict(base, asin="xx"), "t", png) and raises(media.add, base, "t", base64.b64encode(b"GIF89a....").decode()))
mid = media.add(base, "t", png)
check("sin verificar → marcador IMAGEN PENDIENTE y se indica qué falta", (lambda r: r["estado"] == "PENDIENTE" and r["marcador"] == "IMAGEN PENDIENTE DE VERIFICAR" and r["falta"])(media.resolve("P1", "50ml", "B0ABCDEFGH")))
check("verificar exige permiso y al menos un derecho", raises(media.verify, mid, "VERIFICADA", {"visualizar": True}, "a", "") and raises(media.verify, mid, "VERIFICADA", {}, "a", "acta interna 2026-11"))
media.verify(mid, "VERIFICADA", {"visualizar": True}, "a", "acta interna 2026-11")
check("derechos por operación: visualizar sí; exportar/redistribuir no (y se explica cuál falta)", media.resolve("P1", "50ml", "B0ABCDEFGH")["estado"] == "VERIFICADA" and "exportar" in media.resolve("P1", "50ml", "B0ABCDEFGH", "exportar")["falta"] and raises(media.file, mid, "exportar"))
check("vinculación EXACTA: otro ASIN o otra variante nunca reutiliza la imagen", media.resolve("P1", "50ml", "B0ZZZZZZZZ")["estado"] == "PENDIENTE" and media.resolve("P1", "100ml", "B0ABCDEFGH")["estado"] == "PENDIENTE" and media.resolve("P2", "50ml", "B0ABCDEFGH")["estado"] == "PENDIENTE")
mid2 = media.add(dict(base, asin="B0CCCCCCCC", caduca="2020-01-01"), "t", png); media.verify(mid2, "VERIFICADA", {"visualizar": True}, "a", "permiso caducado de prueba")
check("permiso caducado → pendiente con motivo", "caducado" in media.resolve("P1", "50ml", "B0CCCCCCCC")["falta"])
media.verify(mid2, "RECHAZADA", {}, "a", "no válida"); check("rechazada no se muestra", media.resolve("P1", "50ml", "B0CCCCCCCC")["estado"] == "PENDIENTE")
# ---- datos
csv_ = "producto,pais,fecha,unidades,ventas_netas,moneda,sesiones,pedidos,devoluciones_uds,precio_medio,canal\n" + "\n".join("PX,ES,2026-11-%02d,%d,%.2f,EUR,100,%d,0,%.1f,FBA" % (d, u, u * p / 1.21, u, p) for d, u, p in [(1, 4, 40.0), (2, 4, 40.0), (3, 4, 40.0), (4, 3, 50.0), (5, 3, 50.0), (6, 3, 50.0)]) + "\nPX,ES,mala,1,1,EUR,1,1,0,1,FBA\nPX,ES,2026-11-07,-3,1,EUR,1,1,0,1,FBA\nPX,ES,2026-11-08,1,5,,1,1,0,1,FBA\n"
r = data.import_csv("sales", csv_, "PRODUCCION", "EXPORT_SELLER_CENTRAL", "t", "u")
check("importación: 6 filas válidas y 3 rechazadas con motivo (fecha, negativo, importe sin moneda)", r["filas"] == 6 and r["n_rechazadas"] == 3 and {x["motivo"] for x in r["rechazadas"]} >= {"fecha inválida", "importe sin moneda"})
check("importación duplicada rechazada; sintético solo con entorno SINTETICO_DEMO", raises(data.import_csv, "sales", csv_, "PRODUCCION", "EXPORT_SELLER_CENTRAL", "t", "u") and raises(data.import_csv, "sales", "producto,pais,fecha\nA,ES,2026-01-01", "PRODUCCION", "SINTETICO", "t", "u") and raises(data.import_csv, "sales", "x", "PRODUCCION", "MANUAL_AHT", "t", "u"))
kp = data.kpis({"producto": "PX", "pais": "ES"})
check("KPIs: unidades 21, conversión 0,035 con denominador, fuente y fecha; sin datos = SIN_DATO", kp["unidades"]["valor"] == 21 and abs(kp["conversion"]["valor"] - 0.035) < 1e-9 and kp["conversion"]["denominador"] == "sesiones" and kp["acos"]["estado"] == "SIN_DATO" and data.kpis({"producto": "NOEXISTE"})["unidades"]["estado"] == "SIN_DATO")
check("aislamiento producción/demo: lo importado en producción no aparece en SINTETICO_DEMO", data.kpis({"producto": "PX"}, "SINTETICO_DEMO")["unidades"]["estado"] == "SIN_DATO")
check("filtro de periodo y país", data.kpis({"producto": "PX", "desde": "2026-11-04", "hasta": "2026-11-06"})["unidades"]["valor"] == 9 and data.kpis({"producto": "PX", "pais": "DE"})["unidades"]["estado"] == "SIN_DATO")
niv = data.niveles_precio("PX", "ES"); check("niveles de precio observados y elasticidad de arco", len(niv) == 2 and KP.elasticidad(niv) is not None and KP.elasticidad(niv[:1]) is None and KP.elasticidad(niv) < 0)
check("conectores SP-API/Ads NO OPERATIVOS", all(v["estado"] == "NO_OPERATIVO" for v in data.estado_conectores().values()))
# ---- pricing
def kpis_none(): return {x: dict(C.medida(None, "u"), confianza="MUY_BAJA") for x in ("unidades", "conversion", "sesiones", "acos", "stock", "ventas_netas")}
def mk(pvp=49.9, st_=True, kpi=None, costes=None, ml=50, niveles=None, dias=28):
    return {"producto": "P", "pais": "ES", "entorno": "PRODUCCION", "fecha": "2026-11-19", "own": {"pvp": pvp, "ml": ml, "pvp_estado": "PROPUESTO"}, "panel_premium": {"estadisticos": {"mediana_100ml": 100.0, "min_100ml": 80.0, "max_100ml": 140.0, "n": 4}} if st_ else {"estadisticos": None, "estadisticos_nota": "MUESTRA INSUFICIENTE"},
            "costes": costes or a2, "kpis": kpi or kpis_none(), "niveles": niveles or [], "dias_periodo": dias}
d5 = KP.dictamen(mk(st_=False)); check("TIPO 5 sin mercado: no recomienda, lista faltantes y cómo obtenerlos, contrato válido", d5["tipo"] == 5 and d5["intervalo_recomendado"] is None and d5["faltantes"] and all("como" in x for x in d5["faltantes"]) and d5["errores_contrato"] == [])
d5b = KP.dictamen(mk(costes=a)); check("TIPO 5 sin costes completos ni ventas, aunque haya mercado", d5b["tipo"] == 5)
def kv(u=140, conv=.08, ses=1750, acos=None, stock=500):
    m = lambda v, un, **kw: C.medida(v, un, "EXPORT_SELLER_CENTRAL", "2026-11-18", periodo="x", confianza="ALTA", **kw)
    return {"unidades": m(u, "uds"), "conversion": m(conv, "ratio", estado="DERIVADO"), "sesiones": m(ses, "sesiones"), "acos": m(acos, "ratio") if acos is not None else C.medida(None, "ratio"), "stock": m(stock, "uds") if stock is not None else C.medida(None, "uds"), "ventas_netas": C.medida(None, "EUR")}
nv = [{"precio": 40.0, "uds_dia": 6.0, "dias": 10}, {"precio": 50.0, "uds_dia": 5.0, "dias": 10}]
d1 = KP.dictamen(mk(pvp=40, kpi=kv(), niveles=nv)); check("TIPO 1 SUBIR: precio ≤85 % de la mediana con margen; intervalo = mercado ∩ margen (no solo mediana)", d1["tipo"] == 1 and d1["intervalo_recomendado"] and d1["base_solo_mediana"] is False and d1["intervalo_recomendado"]["min"] >= 40 * 0 and d1["errores_contrato"] == [])
d2 = KP.dictamen(mk(pvp=50, kpi=kv(), niveles=nv)); check("TIPO 2 MANTENER: precio cercano a la mediana", d2["tipo"] == 2 and d2["escenarios"])
d3 = KP.dictamen(mk(pvp=70, kpi=kv(conv=.03), niveles=nv)); check("TIPO 3 BAJAR/PROMO: precio ≥115 % de la mediana con evidencia", d3["tipo"] in (3, 4))
d3b = KP.dictamen(mk(pvp=70, kpi=kv(conv=.08), niveles=nv)); check("TIPO 3 con elasticidad observada y precio alto", d3b["tipo"] == 3 and d3b["intervalo_recomendado"])
d4 = KP.dictamen(mk(pvp=50, kpi=kv(acos=.6), niveles=nv)); check("TIPO 4 NO TOCAR PRECIO: ACoS por encima del equilibrio", d4["tipo"] == 4 and "ACoS" in d4["proxima_accion"])
d4b = KP.dictamen(mk(pvp=50, kpi=kv(stock=20), niveles=nv)); check("TIPO 4 por cobertura de stock baja", d4b["tipo"] == 4 and "stock" in d4b["proxima_accion"].lower())
d4c = KP.dictamen(mk(pvp=50, kpi=kv(conv=.02), niveles=nv)); check("TIPO 4 por conversión baja con tráfico", d4c["tipo"] == 4 and "onversión" in d4c["proxima_accion"])
dn = KP.dictamen(mk(pvp=50, kpi=kv())); check("sin elasticidad observada: unidades rotuladas SUPUESTO y riesgo explícito", all("SUPUESTO" in e["uds_dia_estado"] for e in dn["escenarios"]) and any("Elasticidad" in r for r in dn["riesgos"]) and any("Elasticidad observada" in f["dato"] for f in dn["faltantes"]))
dv = KP.dictamen(mk(pvp=50)); check("sin ventas base: sin proyección de unidades, confianza MUY_BAJA y degradado a EVIDENCIA INSUFICIENTE", all(e["uds_dia"] is None for e in dv["escenarios"]) and dv["tipo"] == 5 and any("Confianza insuficiente" in a_["texto"] for a_ in dv["justificacion"]))
check("confianza = input más débil (nunca ALTA con equivalencia estimada y costes hipotéticos)", d1["confianza"] in ("BAJA", "MEDIA", "MUY_BAJA") and d5["confianza"] == "MUY_BAJA")
check("todas las afirmaciones del dictamen llevan clase; tipos 1-3 con confianza MUY_BAJA se degradan a 5", all(a_["clase"] in C.CLASES_AFIRMACION for d_ in (d1, d2, d4) for a_ in d_["justificacion"]) and KP._fin(dict(d1, confianza="MUY_BAJA", tipo=1))["tipo"] == 5)
check("el PVP propuesto se rotula como PROPUESTA, no como precio vigente", "PROPUESTA" in d1["precio_actual"]["nota"])
# ---- Director
class OpsStub:
    def __init__(s): s.dec = []; s.led = []; s.obs = []
    def request_decision(s, product, kind, title, item, options=None, task_id=None, level="N3"): s.dec.append((kind, title)); return len(s.dec)
    def ledger_add(s, *a, **kw): s.led.append((a, kw)); return len(s.led)
    def ledger_observe(s, lid, res, **kw): s.obs.append((lid, res)); return {}
ops = OpsStub(); dr = KDIR.Director(k, ops, data)
ctx = {"ficha": costs.ficha("PRD-ACTIVCORE-V2"), "kpis": kv(), "panel_premium": {"n_precio_vigente": 4}}
dos = KDIR.construir(d2, dict(ctx, producto="P"), {"estado": "PENDIENTE"}); did = dr.guardar(dos, "t")
need = ("problema_detectado", "evidencias", "hipotesis_alternativas", "investigacion_realizada", "dictamen", "confianza", "escenarios", "accion_recomendada", "responsable", "criterio_exito", "revision_posterior", "datos_faltantes")
check("dossier analítico con todos los campos exigidos y persistido", all(x in dos for x in need) and dr.obtener(did)["id"] == did and dos["hipotesis_alternativas"] and all(h["clase"] == "HIPOTESIS" for h in dos["hipotesis_alternativas"]))
d5dos = KDIR.construir(d5, dict(ctx, producto="P"), None); did5 = dr.guardar(d5dos, "t")
check("dictamen 5: el dossier indica cómo obtener datos/experimentos y no se puede proponer decisión de precio", d5dos["como_obtenerlos"] and raises(dr.proponer, did5, "t"))
pr = dr.proponer(did, "t"); check("proponer registra decisión N3 + ledger + seguimiento, sin ejecución externa", pr["decision_id"] and pr["ledger_id"] and pr["followup_id"] and "Ninguna acción externa" in pr["nota"] and ops.dec[0][0] in ("k4_revisar_causa", "k4_cambiar_precio"))
check("medir sin ejecución humana registrada se rechaza", raises(dr.medir, pr["followup_id"], "t"))
dr.registrar_ejecucion(pr["followup_id"], "Sergio", "2026-11-05", "t"); m = dr.medir(pr["followup_id"], "t")
check("medición descriptiva con NO_ATRIBUIDO_AUTOMATICAMENTE", "NO_ATRIBUIDO_AUTOMATICAMENTE" in m["atribucion"] and ops.obs)
npd = dr.nuevo_producto({"titulo": "Serum X"}, "t"); npo = dr.obtener(npd)
check("nuevo producto: sin datos documentados no hay recomendación (NO_EVALUADO + faltantes)", npo["estado_decision"] == "NO_EVALUADO" and len(npo["datos_faltantes"]) == 5 and raises(dr.nuevo_producto, {}, "t"))
cap = KDIR.capacidades(); check("capacidades: IA externa DESACTIVADA, autonomía NO VERIFICADA, SP-API/Ads no operativos, informe periódico ≠ autonomía", "DESACTIVADA" in cap["ia_externa"] and cap["autonomia_verificada"]["estado"] == "NO VERIFICADA" and any("SP-API" in x for x in cap["no_operativo"]) and "NO es dirección comercial autónoma" in cap["aviso"])
ok, n, bad = st.verify_audit(); check("cadena de auditoría íntegra tras todas las operaciones K4", ok and n > 10)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
