"""K4 · Consejero F1–F2: contratos de proveedores/router, libro de evidencias, verificador (11 trampas), motor y pruebas anti-plantilla T1–T10 (con proveedores SIMULADOS y datos SINTÉTICOS).
AVISO: superar estas pruebas valida el MOTOR, no demuestra razonamiento autónomo real de un modelo."""
import base64, http.cookiejar, json, os, sys, tempfile, threading, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ["AMAZON_PRO_NO_WORKER"] = "1"; os.environ["AMAZON_PRO_KEEPA_ENABLE"] = "0"
from backend.store import Store
from backend import k4_store as KS, k4c_providers as P, k4c_mock as M, k4c_engine as E, k4c_ledger as LG
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
k = KS.K4Store(Store(os.path.join(tempfile.mkdtemp(), "t.db")))
PROPIO = {"precio": 49.90, "volumen_ml": 50}; DI = {"ventas_dia": 3, "margen_unitario": 20, "trafico_diario": 400, "conv_base": 0.05}
def motor(esc="BASE", trampa=None, busq=True, real=False):
    r = P.Router(k)
    r.registrar(M.BusquedaSimulada(esc) if busq else P.BusquedaExternaNoImplementada())
    r.registrar(M.LecturaSimulada(esc)); r.registrar(M.LLMSimulado(trampa)); r.registrar(M.CalculadoraExperimento(), "diseno_experimento")
    if real: r.registrar(P.AdaptadorLLMExterno({}), "externo")
    return E.Motor(k, r)
def inv(esc="BASE", di=None, **kw):
    t = kw.pop("trampa", None); b = kw.pop("busq", True); propio = kw.pop("propio", PROPIO); return motor(esc, t, b).investigar(kw.pop("pregunta", "¿Se sostiene el precio premium de ACTIVCORE?"), "ACTIVCORE", propio, di, **kw)

# ---------- F1 contratos
m = motor(real=True); est = {(p["rol"], p["nombre"]): p for p in m.R.estado()["proveedores"]}
check("F1 estado: simulados OPERATIVA; IA externa REQUIERE_AUTORIZACION", est[("busqueda", "busqueda_sintetica")]["estado"] == "OPERATIVA" and est[("llm", "externo")]["estado"] == "REQUIERE_AUTORIZACION")
try: m.R.llamar("llm", "completar", inv_id="X", nombre="externo", sistema="s", usuario="u"); r = False
except PermissionError: r = True
check("F1 proveedor REAL bloqueado sin autorización y registrado en el log", r and k.q("SELECT estado FROM k4c_consulta WHERE inv_id='X'")[0]["estado"] == "BLOQUEADA_SIN_AUTORIZACION")
check("F1 límites por defecto 0 €; gasto adicional autorizado 0", m.R.limites()["tope_inv_eur"] == 0 and m.R.limites()["tope_mes_eur"] == 0 and m.R.estado()["gasto_adicional_autorizado_eur"] == 0)
class Caro(M.BusquedaSimulada):
    nombre = "caro"; modo = "SIMULADO"
    def coste_estimado(self, **kw): return 0.5
r2 = P.Router(k); r2.registrar(Caro())
try: r2.llamar("busqueda", "buscar", inv_id="Y", consulta="cafeina topica evidencia"); r = False
except PermissionError: r = True
check("F1 presupuesto: una llamada con coste > tope (0 €) se bloquea y se registra", r and k.q("SELECT estado FROM k4c_consulta WHERE inv_id='Y'")[0]["estado"] == "BLOQUEADA_PRESUPUESTO")
r2.limites(1.0, 1.0); res = r2.llamar("busqueda", "buscar", inv_id="Y", consulta="cafeina topica evidencia ingrediente"); check("F1 con tope ≥ coste la llamada se ejecuta y el coste se contabiliza", isinstance(res, list) and abs(r2.gasto_inv("Y") - 0.5) < 1e-9)
try: P.Router(k).registrar(type("Z", (P.Proveedor,), {"rol": "x"})()); r = False
except ValueError: r = True
check("F1 rol desconocido rechazado", r)
L = LG.Libro(k); doc = M.corpus()[0]
fid = L.add_fuente(doc, "INV-T", "t", "SINTETICO"); xid = L.add_extracto(fid, doc["tags"][0][2], hipotesis="H0", efecto=1)
check("F1 libro: fuente y extracto literal con hash", L.fuente(fid)["hash"] == LG.sha(doc["texto"]) and L.extracto(xid)["hash"])
try: L.add_extracto(fid, "texto que no aparece en la fuente"); r = False
except ValueError: r = True
check("F1 libro: extracto no literal rechazado", r)
try: L.add_fuente(dict(doc, url="https://ejemplo.org/x"), "INV-T", "t", "SINTETICO"); r = False
except ValueError: r = True
check("F1 libro: no se mezcla entorno SINTETICO con URL real", r)
try: L.add_fuente(dict(doc, tipo_fuente="OTRA"), "INV-T", "t", "SINTETICO"); r = False
except ValueError: r = True
check("F1 libro: tipos de fuente validados", r)

# ---------- F2 verificador: 11 trampas
base = inv("NUEVA_EVIDENCIA_COMPARABLES", DI); check("F2 informe fiel: sin bloqueantes", base["verificacion"]["bloqueantes"] == 0 and base["verificacion"]["veredicto"] in ("ACEPTADO", "ACEPTADO_CON_RESERVAS"))
ESPERADO = {"CITA_INEXISTENTE": "CITA_INEXISTENTE", "CITA_NO_RESPALDA": "CITA_NO_RESPALDA", "HISTORICO_COMO_ACTUAL": "HISTORICO_COMO_ACTUAL", "ERROR_DE_CALCULO": "ERROR_DE_CALCULO", "SECUNDARIA_COMO_PRIMARIA": "SECUNDARIA_COMO_PRIMARIA", "COMPARACION_NO_EQUIVALENTE": "COMPARACION_NO_EQUIVALENTE",
            "CONCLUSION_EXCEDE_EVIDENCIA": "CONCLUSION_EXCEDE_EVIDENCIA", "AUSENCIA_COMO_AUSENCIA": "AUSENCIA_COMO_EVIDENCIA_DE_AUSENCIA", "BSR_COMO_VENTAS": "BSR_COMO_VENTAS", "CORRELACION_COMO_CAUSA": "CORRELACION_COMO_CAUSA", "INGREDIENTE_COMO_FORMULA": "INGREDIENTE_COMO_FORMULA"}
for tr, cod in ESPERADO.items():
    o = inv("NUEVA_EVIDENCIA_COMPARABLES", DI, trampa=tr); v = o["verificacion"]; cods = {p["codigo"] for p in v.get("problemas_originales", v["problemas"]) if p["severidad"] == "BLOQUEANTE"}
    check("F2 verificador detecta %s" % tr, cod in cods and (v["veredicto"] == "RECHAZADO" or v.get("depurado")))
check("F2 una trampa que invalida la base de la conclusión deja el informe NO_PUBLICABLE", inv("NUEVA_EVIDENCIA_COMPARABLES", DI, trampa="ERROR_DE_CALCULO")["informe"]["publicacion"]["estado"] == "NO_PUBLICABLE" and inv("NUEVA_EVIDENCIA_COMPARABLES", DI, trampa="CONCLUSION_EXCEDE_EVIDENCIA")["informe"]["publicacion"]["estado"] == "NO_PUBLICABLE")
check("F2 un id de cita válido no basta: cita real con afirmación que el extracto no respalda se rechaza", "CITA_NO_RESPALDA" in {p["codigo"] for p in inv("NUEVA_EVIDENCIA_COMPARABLES", DI, trampa="CITA_NO_RESPALDA")["verificacion"].get("problemas_originales", [])})

# ---------- T1 contrafactual
a = inv("BASE"); b = inv("NUEVA_EVIDENCIA_COMPARABLES", DI); c = inv("REVISION_DEGRADADA")
ca, cb, cc = (x["informe"]["conclusion"] for x in (a, b, c))
check("T1 la conclusión cambia con la evidencia: BASE NO_CONCLUIBLE → con comparables y datos internos MANTENER", ca["decision"] == "NO_CONCLUIBLE" and cb["decision"] == "MANTENER")
check("T1 revisión degradada: la tesis de AHT pasa de PARCIAL a DEBILITADA y se cita el extracto contrario", ca["tesis_aht"]["estado"].startswith("PARCIAL") and cc["tesis_aht"]["estado"] == "DEBILITADA" and any(h["desfavorables"] for h in c["informe"]["hipotesis"] if h["id"] == "H0"))
check("T1 nueva evidencia de comparables sin datos internos NO basta para decidir", inv("NUEVA_EVIDENCIA_COMPARABLES")["informe"]["conclusion"]["decision"] == "NO_CONCLUIBLE")
caro = inv("NUEVA_EVIDENCIA_COMPARABLES", DI, propio={"precio": 120.0, "volumen_ml": 50})["informe"]["conclusion"]; check("T1 cambiar el precio propio (dato interno) cambia la decisión de forma coherente (BAJAR)", caro["decision"] == "BAJAR")
# ---------- T2 sin herramientas
t2 = inv("BASE", busq=False); i2 = t2["informe"]
check("T2 sin búsqueda: declara «no pude investigar», sin fuentes ni hechos externos, NO_CONCLUIBLE", i2["no_investigado"] and i2["conclusion"]["decision"] == "NO_CONCLUIBLE" and not k.q("SELECT 1 FROM k4c_fuente WHERE inv_id=?", (t2["id"],)) and any("No pude investigar" in x["texto"] for x in i2["afirmaciones"]) and not any(x["tipo"] == "HECHO" and x.get("citas") for x in i2["afirmaciones"]))
# ---------- T3 trazabilidad
def trazable(o):
    for x in o["informe"]["afirmaciones"]:
        if x["tipo"] == "HECHO" and not x.get("dato_interno"):
            if not x["citas"]: return False
            for cid in x["citas"]:
                ex = k.q("SELECT x.*, f.hash fh FROM k4c_extracto x JOIN k4c_fuente f ON f.id=x.fuente_id WHERE x.id=?", (cid,))
                if not ex or LG.sha(ex[0]["texto"]) != ex[0]["hash"]: return False
    return True
check("T3 0 hechos sin evidencia; cada cita existe y su hash coincide", trazable(b))
check("T3 todo número calculado se recalcula en código (todos los cálculos verificados)", all(x.get("calculo") for x in b["informe"]["afirmaciones"] if x["texto"].startswith("Precio por 100 ml")) and b["verificacion"]["bloqueantes"] == 0)
check("T3 libro persistido: consultas, fuentes, extractos y afirmaciones recuperables", len(L.libro(b["id"])["fuentes"]) >= 8 and len(L.libro(b["id"])["consultas"]) > 10 and len(L.libro(b["id"])["afirmaciones"]) >= 10)
# ---------- T4 premisa falsa
t4 = inv("BASE", premisas=[{"id": "P1", "texto": "La luteolina tópica está demostrada como eficaz en humanos"}, {"id": "P2", "texto": "La cafeína tópica mejora el recuento de cabello en alopecia androgenética"}])["informe"]["premisas"]
check("T4 premisa falsa sembrada (luteolina demostrada en humanos) es CUESTIONADA citando el extracto; la premisa cierta no se contradice", t4[0]["estado"] == "CUESTIONADA" and t4[0]["evidencia"] and t4[1]["estado"] == "RESPALDADA_POR_EXTRACTOS")
# ---------- T5 producto control
t5 = inv("SIN_DATOS", propio=PROPIO)["informe"]
check("T5 producto control sin datos: NO_CONCLUIBLE con plan de investigación y datos faltantes, sin veredicto", t5["conclusion"]["decision"] == "NO_CONCLUIBLE" and not [x for x in t5["afirmaciones"] if x["tipo"] == "HECHO" and x.get("citas")] and sum(1 for x in t5["afirmaciones"] if x["tipo"] == "FALTANTE") >= 3)
# ---------- T6 solapamiento (herramienta; umbral sin calibrar)
def ngr(t, n=3): w = t.lower().split(); return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}
def solap(i1, i2): A = ngr(" ".join(x["texto"] for x in i1["afirmaciones"])); B = ngr(" ".join(x["texto"] for x in i2["afirmaciones"])); return len(A & B) / max(1, len(A | B))
check("T6 herramienta de solapamiento: idéntico=1, informes con evidencia distinta <1 (umbral sin calibrar; requiere 2 productos reales)", solap(a["informe"], a["informe"]) == 1 and solap(a["informe"], t5) < 1)
# ---------- T8 abogado del diablo (procedimiento)
check("T8 pasada adversarial: toda hipótesis con consultas tuvo búsqueda contraria; informe fiel SUPERA", all(any(q["h"] == h["id"] and q["contraria"] for q in b["informe"]["busquedas"]) for h in b["informe"]["hipotesis"] if h["consultas"]) and b["adversarial"]["veredicto"] == "SUPERADA")
inf_x = json.loads(json.dumps(b["informe"])); inf_x["conclusion"]["cambia_si"] = []; inf_x["busquedas"] = [q for q in inf_x["busquedas"] if not q["contraria"]]; plan = motor()._plan()
check("T8 sesgo de confirmación simulado (sin búsqueda contraria ni «cambia si») → DEFICIENTE y NO_PUBLICABLE", motor().adversarial(inf_x, plan, inf_x["busquedas"], inf_x["hipotesis"])["veredicto"] == "DEFICIENTE")
# ---------- T9 estabilidad
runs = [inv("NUEVA_EVIDENCIA_COMPARABLES", DI) for _ in range(3)]
def clave(o): return (o["informe"]["conclusion"]["decision"], o["informe"]["conclusion"]["confianza"], tuple(sorted(x["texto"] for x in L.extractos_de(o["id"]))), tuple(a["texto"] for a in o["informe"]["afirmaciones"]))
check("T9 3 ejecuciones: misma decisión, mismas evidencias y mismo texto", len({clave(r) for r in runs}) == 1)
# ---------- T10 predicción puntuada
mt = motor(); o = mt.investigar("¿precio?", "ACTIVCORE", PROPIO, DI); pid = k.q("SELECT id FROM k4c_prediccion WHERE inv_id=?", (o["id"],))[0]["id"]
check("T10 el motor registra una predicción medible con ventana", k.q("SELECT estado, ventana_dias FROM k4c_prediccion WHERE id=?", (pid,))[0]["estado"] == "PENDIENTE")
mt.cerrar_prediccion(pid, {"conversion_relativa": -0.01}, True); check("T10 al cerrarla se puntúa y se calcula la calibración (con aviso de muestra insuficiente)", mt.calibracion()["acertadas"] >= 1 and "20" in mt.calibracion()["nota"])
# ---------- Integración
inv_d = inv("NUEVA_EVIDENCIA_COMPARABLES", DI); 
class Dir:
    def __init__(s): s.g = []
    def guardar(s, d, a): s.g.append(d); return d["id"]
mi = motor("NUEVA_EVIDENCIA_COMPARABLES"); mi.D = Dir(); did = mi.a_dossier(inv_d["id"], "tester")
check("Integración: la investigación se guarda como expediente tipo 'consejero' con entorno SINTETICO", mi.D.g[0]["tipo"] == "consejero" and mi.D.g[0]["entorno"] == "SINTETICO" and mi.D.g[0]["consejero"]["decision"] == "MANTENER")
try: mi.proponer_decision(inv_d["id"], "tester"); r = False
except ValueError as e: r = "SINTÉTICA" in str(e)
check("Integración: una investigación SINTÉTICA no puede proponer decisión de precio", r)
check("Seguridad: gasto de la investigación 0 € y 0 llamadas externas", inv_d["gasto_eur"] == 0 and not k.q("SELECT 1 FROM k4c_consulta WHERE estado='OK' AND proveedor='ai.py'"))
# diseño de experimento
ex = M.CalculadoraExperimento().ejecutar(trafico_diario=400, conv_base=0.05, mde_rel=0.15); ex0 = M.CalculadoraExperimento().ejecutar()
check("Experimento: tamaño de muestra y duración según tráfico/conversión (≥14 días); sin datos → NO diseñable (no recomienda 3 días fijos)", ex["disenable"] and ex["dias_estimados"] >= 14 and ex["n_por_variante"] > 1000 and not ex0["disenable"] and ex0["datos_necesarios"])
check("Experimento: con poco tráfico avisa de inviabilidad", M.CalculadoraExperimento().ejecutar(trafico_diario=20, conv_base=0.02, mde_rel=0.1)["advertencia"])

# ---------- API
import server as S
from backend import ai as AI
dbp = os.path.join(tempfile.mkdtemp(), "s.db"); srv = S.make_server(0, admin_token="t", db_path=dbp, cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); threading.Thread(target=srv.serve_forever, daemon=True).start(); port = srv.server_address[1]
class Cl:
    def __init__(s): s.cj = http.cookiejar.CookieJar(); s.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(s.cj)); s.csrf = None
    def call(s, m, p, b=None, csrf=True):
        h = {"Content-Type": "application/json"}
        if csrf and s.csrf: h["X-CSRF-Token"] = s.csrf
        rq = urllib.request.Request(f"http://127.0.0.1:{port}" + p, method=m, data=json.dumps(b).encode() if b is not None else None, headers=h)
        try: x = s.op.open(rq); return x.status, json.loads(x.read() or b"{}")
        except urllib.error.HTTPError as e: d = e.read(); return e.code, (json.loads(d) if d[:1] == b"{" else {})
ad = Cl(); c, j = ad.call("POST", "/api/login", {"username": "admin", "password": "admin-password-123"}, csrf=False); ad.csrf = j.get("csrf")
S.APP["store"].create_user("ana_an", "clave-analista-1", "analyst", ["catalogo-aht"]); an = Cl(); c, j = an.call("POST", "/api/login", {"username": "ana_an", "password": "clave-analista-1"}, csrf=False); an.csrf = j.get("csrf")
c, st = ad.call("GET", "/api/k4/consejero/estado"); check("API estado: proveedores, autorización externa false, gasto 0, aviso F1–F2", c == 200 and st["autorizacion_externa"] is False and st["gasto_adicional_autorizado_eur"] == 0 and any(p["estado"] == "REQUIERE_AUTORIZACION" for p in st["proveedores"]))
check("API analista no puede lanzar investigaciones (403)", an.call("POST", "/api/k4/consejero/investigar", {})[0] == 403)
c, o = ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "NUEVA_EVIDENCIA_COMPARABLES", "datos_internos": DI}); check("API investigar: informe SINTETICO con decisión MANTENER y verificación", c == 200 and o["entorno"] == "SINTETICO" and o["informe"]["conclusion"]["decision"] == "MANTENER" and o["verificacion"]["bloqueantes"] == 0)
c, lb = ad.call("GET", "/api/k4/consejero/libro/" + o["id"]); check("API libro de evidencias", c == 200 and lb["fuentes"] and lb["extractos"] and lb["consultas"])
c, dd = ad.call("POST", "/api/k4/consejero/dossier", {"id": o["id"]}); c2, dg = ad.call("GET", "/api/k4/dossier/" + dd.get("dossier", "x")); check("API integra con el Director: expediente 'consejero' recuperable", c == 200 and c2 == 200 and dg["tipo"] == "consejero")
check("API proponer decisión con datos sintéticos → 400", ad.call("POST", "/api/k4/consejero/proponer", {"id": o["id"]})[0] == 400)
c, o2 = ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "NUEVA_EVIDENCIA_COMPARABLES", "datos_internos": DI, "trampa": "CONCLUSION_EXCEDE_EVIDENCIA"}); check("API trampa: conclusión que excede la evidencia → RECHAZADO / NO_PUBLICABLE", c == 200 and o2["verificacion"]["veredicto"] == "RECHAZADO" and o2["informe"]["publicacion"]["estado"] == "NO_PUBLICABLE")
check("API escenario inválido → 400", ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "X"})[0] == 400)
print("\n%d/%d" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
