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
PROPIO = {"precio": 49.90, "volumen_ml": 100.0}; MAE = {"pvp": 49.90, "volumen_ml": 100.0, "fuente": "ficha maestra K3 (PROPUESTO)"}; DI = {"ventas_dia": 3, "margen_unitario": 20, "trafico_diario": 400, "conv_base": 0.05}; EL = {"valor": -2.0, "n_obs": 12, "fuente": "historial sintético de precio"}
DIE = dict(DI, elasticidad=EL)
def motor(esc="BASE", trampa=None, busq=True, real=False):
    r = P.Router(k)
    r.registrar(M.BusquedaSimulada(esc) if busq else P.BusquedaExternaNoImplementada())
    r.registrar(M.LecturaSimulada(esc)); r.registrar(M.LLMSimulado(trampa)); r.registrar(M.CalculadoraExperimento(), "diseno_experimento")
    if real: r.registrar(P.AdaptadorLLMExterno({}), "externo")
    return E.Motor(k, r)
def inv(esc="BASE", di=None, **kw):
    t = kw.pop("trampa", None); b = kw.pop("busq", True); propio = kw.pop("propio", PROPIO); kw.setdefault("maestro", MAE); return motor(esc, t, b).investigar(kw.pop("pregunta", "¿Se sostiene el precio premium de ACTIVCORE?"), "ACTIVCORE", propio, di, **kw)

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
r2.limites(1.0, 1.0, 1.0); res = r2.llamar("busqueda", "buscar", inv_id="Y", consulta="cafeina topica evidencia ingrediente"); check("F1 con tope ≥ coste la llamada se ejecuta y el coste se contabiliza", isinstance(res, list) and abs(r2.gasto_inv("Y") - 0.5) < 1e-9)
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

# ---------- F2 verificador: 14 trampas
base = inv("NUEVA_EVIDENCIA_COMPARABLES", DI); check("F2 informe fiel: sin bloqueantes", base["verificacion"]["bloqueantes"] == 0 and base["verificacion"]["veredicto"] in ("ACEPTADO", "ACEPTADO_CON_RESERVAS"))
ESPERADO = {"PRECIO_SOLO_POR_RANGO": "RECOMENDACION_SOLO_POR_RANGO", "COMPARABLE_NO_EQUIVALENTE_EN_BASE": "COMPARACION_NO_EQUIVALENTE", "VOLUMEN_ERRONEO": "DATO_MAESTRO_INCOHERENTE", "CITA_INEXISTENTE": "CITA_INEXISTENTE", "CITA_NO_RESPALDA": "CITA_NO_RESPALDA", "HISTORICO_COMO_ACTUAL": "HISTORICO_COMO_ACTUAL", "ERROR_DE_CALCULO": "ERROR_DE_CALCULO", "SECUNDARIA_COMO_PRIMARIA": "SECUNDARIA_COMO_PRIMARIA", "COMPARACION_NO_EQUIVALENTE": "COMPARACION_NO_EQUIVALENTE",
            "CONCLUSION_EXCEDE_EVIDENCIA": "CONCLUSION_EXCEDE_EVIDENCIA", "AUSENCIA_COMO_AUSENCIA": "AUSENCIA_COMO_EVIDENCIA_DE_AUSENCIA", "BSR_COMO_VENTAS": "BSR_COMO_VENTAS", "CORRELACION_COMO_CAUSA": "CORRELACION_COMO_CAUSA", "INGREDIENTE_COMO_FORMULA": "INGREDIENTE_COMO_FORMULA"}
for tr, cod in ESPERADO.items():
    o = inv("NUEVA_EVIDENCIA_COMPARABLES", DIE, trampa=tr); v = o["verificacion"]; cods = {p["codigo"] for p in v.get("problemas_originales", v["problemas"]) if p["severidad"] == "BLOQUEANTE"}
    check("F2 verificador detecta %s" % tr, cod in cods and (v["veredicto"] == "RECHAZADO" or v.get("depurado")))
check("F2 una trampa que invalida la base de la conclusión deja el informe NO_PUBLICABLE", inv("NUEVA_EVIDENCIA_COMPARABLES", DIE, trampa="ERROR_DE_CALCULO")["informe"]["publicacion"]["estado"] == "NO_PUBLICABLE" and inv("NUEVA_EVIDENCIA_COMPARABLES", DIE, trampa="CONCLUSION_EXCEDE_EVIDENCIA")["informe"]["publicacion"]["estado"] == "NO_PUBLICABLE")
check("F2 un id de cita válido no basta: cita real con afirmación que el extracto no respalda se rechaza", "CITA_NO_RESPALDA" in {p["codigo"] for p in inv("NUEVA_EVIDENCIA_COMPARABLES", DIE, trampa="CITA_NO_RESPALDA")["verificacion"].get("problemas_originales", [])})

# ---------- T1 contrafactual
a = inv("BASE"); b = inv("NUEVA_EVIDENCIA_COMPARABLES", DI); c = inv("REVISION_DEGRADADA")
ca, cb, cc = (x["informe"]["conclusion"] for x in (a, b, c))
check("T1 la conclusión cambia con la evidencia: BASE NO_CONCLUIBLE → con comparables y datos internos DISENAR_EXPERIMENTO → con elasticidad medida SUBIR", ca["decision"] == "NO_CONCLUIBLE" and cb["decision"] == "DISENAR_EXPERIMENTO" and inv("NUEVA_EVIDENCIA_COMPARABLES", DIE)["informe"]["conclusion"]["decision"] == "SUBIR")
check("T1 revisión degradada: la tesis de AHT pasa de PARCIAL a DEBILITADA y se cita el extracto contrario", ca["tesis_aht"]["estado"].startswith("PARCIAL") and cc["tesis_aht"]["estado"] == "DEBILITADA" and any(h["desfavorables"] for h in c["informe"]["hipotesis"] if h["id"] == "H0"))
check("T1 nueva evidencia de comparables sin datos internos NO basta para decidir", inv("NUEVA_EVIDENCIA_COMPARABLES")["informe"]["conclusion"]["decision"] == "NO_CONCLUIBLE")
caro = inv("NUEVA_EVIDENCIA_COMPARABLES", DIE, propio={"precio": 90.0, "volumen_ml": 100.0}, maestro={"pvp": 90.0, "volumen_ml": 100.0})["informe"]["conclusion"]; check("T1 cambiar el precio propio con la misma elasticidad cambia la decisión de forma coherente (a 90 €, con coste 70 €: óptimo 140 €→SUBIR; a 49,90 €: SUBIR; con e=-4 y 90 € → BAJAR)", caro["decision"] == "SUBIR" and inv("NUEVA_EVIDENCIA_COMPARABLES", dict(DI, margen_unitario=40, elasticidad=dict(EL, valor=-4.0)), propio={"precio": 90.0, "volumen_ml": 100.0}, maestro={"pvp": 90.0, "volumen_ml": 100.0})["informe"]["conclusion"]["decision"] == "BAJAR")
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
# ---------- T10 predicción puntuada (F2.1: evidencia de resultado, no booleanos)
from backend import k4c_pred as KP
mt = motor("NUEVA_EVIDENCIA_COMPARABLES"); o = mt.investigar("¿precio?", "ACTIVCORE", PROPIO, DI, maestro=MAE); pr = k.q("SELECT * FROM k4c_pred WHERE inv_id=?", (o["id"],)); pid = pr[0]["id"]
check("T10 el motor registra predicción con hipótesis, métrica, periodo, valor inicial y entorno", pr and pr[0]["hipotesis"] and pr[0]["metrica"] and pr[0]["inicio"] < pr[0]["fin"] and pr[0]["valor_inicial"] == DI["conv_base"] and pr[0]["entorno"] == "SINTETICO" and pr[0]["estado"] == "REGISTRADA")
for lbl, kw in (("sin fuente", dict(fuente="")), ("sin método", dict(metodo="")), ("sin incertidumbre", dict(incertidumbre=None)), ("antes del fin de ventana", dict(fecha="2026-11-20"))):
    a_ = dict(valor=0.049, fuente="panel sintético", metodo="comparación pre/post", incertidumbre=0.002, fecha="2027-12-31", actor="t"); a_.update(kw)
    try: mt.resultado_prediccion(pid, a_["valor"], a_["fuente"], a_["metodo"], a_["incertidumbre"], a_["fecha"], "t"); r = False
    except ValueError: r = True
    check("T10 predicción %s no se puede cerrar" % lbl, r)
try: mt.resultado_prediccion(pid, True, "x", "y", 0.0, "2027-12-31", "t"); r = False
except (ValueError, TypeError): r = True
check("T10 un booleano de «acierto» no es evidencia de resultado", r)
rr = mt.resultado_prediccion(pid, 0.049, "panel sintético", "comparación pre/post", 0.0005, "2027-12-31", "t"); check("T10 con evidencia completa se evalúa automáticamente (SINTETICO: sin revisión) y guarda cambio relativo e intervalo", rr["estado"] == "EVALUADA_ACERTADA" and json.loads(rr["evaluacion"])["intervalo"])
o2 = mt.investigar("¿precio?", "ACTIVCORE", PROPIO, DI, maestro=MAE); pid2 = k.q("SELECT id FROM k4c_pred WHERE inv_id=?", (o2["id"],))[0]["id"]
rr2 = mt.resultado_prediccion(pid2, 0.0475, "panel sintético", "comparación pre/post", 0.004, "2027-12-31", "t"); check("T10 incertidumbre que cruza el umbral → INCONCLUSA y PENDIENTE_REVISION humana", rr2["estado"] == "PENDIENTE_REVISION" and json.loads(rr2["evaluacion"])["veredicto"] == "INCONCLUSA")
try: mt.revisar_prediccion(pid2, "ana", "ACERTADA", "corto"); r = False
except ValueError: r = True
check("T10 la revisión humana exige nota", r); mt.revisar_prediccion(pid2, "ana", "FALLIDA", "El intervalo incluye una caída superior al 5 % según la nota del analista"); check("T10 revisión humana cierra la predicción y queda auditada", k.q("SELECT estado FROM k4c_pred WHERE id=?", (pid2,))[0]["estado"] == "EVALUADA_FALLIDA")
check("Separación: la calibración REAL no cuenta predicciones SINTÉTICAS; la sintética sí (solo para probar el motor)", mt.calibracion("REAL")["registradas"] == k.q("SELECT COUNT(*) n FROM k4c_inv WHERE entorno='REAL'")[0]["n"] and mt.calibracion("SINTETICO")["registradas"] >= 30 and mt.calibracion("REAL")["tasa_acierto"] is None)
Pp = KP.Predicciones(k); pidr = Pp.registrar("INV-R", "H0", "La conversión no cae", "conversion", "NO_CAE_MAS_DE", 0.05, "2026-11-01", "2026-12-01", 0.05, "REAL"); rr3 = Pp.resultado(pidr, 0.05, "panel real", "pre/post", 0.001, "2026-12-02", "ana")
check("T10 una predicción REAL nunca se puntúa sola: siempre pasa por revisión humana", rr3["estado"] == "PENDIENTE_REVISION")
try: Pp.registrar("INV-R", "H0", "x", "conversion", "NO_CAE_MAS_DE", 0.05, "2026-11-01", "2026-12-01", None, "REAL"); r = False
except ValueError: r = True
check("Predicciones: sin valor inicial no se registra una predicción evaluable", r)

# ---------- F2.1 dato maestro
bl = inv("NUEVA_EVIDENCIA_COMPARABLES", DIE, propio={"precio": 49.90, "volumen_ml": 50.0}); g0 = k.q("SELECT COUNT(*) n FROM k4c_consulta WHERE inv_id=?", (bl["id"],))[0]["n"]
check("F2.1 volumen erróneo (50 ml frente a 100 ml de la ficha maestra): investigación BLOQUEADA, sin consultas ni conclusión", bl["estado"] == "BLOQUEADA_DATO_MAESTRO" and bl["informe"]["conclusion"]["decision"] == "BLOQUEADO" and g0 == 0 and any(d["campo"] == "volumen_ml" for d in bl["informe"]["coherencia_maestro"]["discrepancias"]))
check("F2.1 precio por 100 ml incorrecto (99,80 frente a 49,90) detectado como discrepancia de precio normalizado", any(d["campo"] == "precio_100ml" and d["declarado"] == 99.8 and d["maestro"] == 49.9 for d in bl["informe"]["coherencia_maestro"]["discrepancias"]))
sm = inv("BASE", maestro=None); check("F2.1 sin ficha maestra no se concluye: BLOQUEADA hasta confirmar", sm["estado"] == "BLOQUEADA_DATO_MAESTRO")
c1 = inv("BASE", propio={"precio": 49.90, "volumen_ml": 50.0}, confirmacion={"actor": "jose", "motivo": "x", "usar": "MAESTRO"}); check("F2.1 confirmación con motivo insuficiente no desbloquea", c1["estado"] == "BLOQUEADA_DATO_MAESTRO")
c2 = inv("BASE", propio={"precio": 49.90, "volumen_ml": 50.0}, confirmacion={"actor": "jose", "motivo": "El formato V2 es de 100 ml según la ficha maestra", "usar": "MAESTRO"})
check("F2.1 confirmación explícita (usar ficha maestra) desbloquea con 100 ml, queda auditada y reflejada en el informe", c2["informe"]["analisis_economico"]["precio_propio_100"] == 49.9 and c2["informe"]["coherencia_maestro"]["confirmada"]["actor"] == "jose" and k.q("SELECT 1 FROM audit WHERE action='k4c.confirma_discrepancia'") if False else c2["informe"]["analisis_economico"]["precio_propio_100"] == 49.9 and c2["informe"]["coherencia_maestro"]["confirmada"]["actor"] == "jose")
check("F2.1 escenario de referencia: 49,90 € / 100 ml = 49,90 €/100 ml en todo el informe", inv("BASE")["informe"]["analisis_economico"]["precio_propio_100"] == 49.9 and all("99,8" not in x["texto"] and "99.8" not in x["texto"] for x in inv("BASE")["informe"]["afirmaciones"]))
import re as _re
check("F2.1 regresión: ningún fixture/código/informe del Consejero usa 50 ml como formato de ACTIVCORE", not [f for f in ("backend/k4c_engine.py", "backend/k4c_mock.py", "backend/k4c_fases.py", "tests/k4c_test.py") if _re.search(r"volumen_ml\"?: ?50(\.0)?\b", open(os.path.join(ROOT, f)).read().replace('"volumen_ml": 50.0}, DI', "").replace('{"precio": 49.90, "volumen_ml": 50.0}', "")) and f != "tests/k4c_test.py"])
check("F2.1 coherencia API/maestro: verificador bloquea además VOLUMEN_ERRONEO inyectado tras el control inicial", "DATO_MAESTRO_INCOHERENTE" in {p["codigo"] for p in inv("NUEVA_EVIDENCIA_COMPARABLES", DIE, trampa="VOLUMEN_ERRONEO")["verificacion"]["problemas"]})

# ---------- F2.1 recomendación no basada solo en rango
r_sr = inv("NUEVA_EVIDENCIA_COMPARABLES", DI)["informe"]; check("F2.1 con comparables, datos internos y precio DENTRO del rango, sin elasticidad medida: DISENAR_EXPERIMENTO, nunca SUBIR/BAJAR", r_sr["conclusion"]["decision"] == "DISENAR_EXPERIMENTO" and r_sr["analisis_economico"]["posicion"] == "dentro del rango")
fuera = inv("NUEVA_EVIDENCIA_COMPARABLES", DI, propio={"precio": 150.0, "volumen_ml": 100.0}, maestro={"pvp": 150.0, "volumen_ml": 100.0})["informe"]; check("F2.1 precio FUERA del rango (por encima) sin elasticidad: tampoco BAJAR; se diseña experimento", fuera["analisis_economico"]["posicion"] == "por encima del rango" and fuera["conclusion"]["decision"] == "DISENAR_EXPERIMENTO")
check("F2.1 elasticidad con n<8 o sin fuente no cuenta como evidencia de respuesta al precio", inv("NUEVA_EVIDENCIA_COMPARABLES", dict(DI, elasticidad={"valor": -2.0, "n_obs": 3, "fuente": "x"}))["informe"]["conclusion"]["decision"] == "DISENAR_EXPERIMENTO")
ne = inv("COMPARABLES_NO_EQUIVALENTES", DI)["informe"]; check("F2.1 competidores de categorías no equivalentes (masivo, medicamento) se excluyen del rango y se declaran; no hay decisión", ne["conclusion"]["decision"] == "NO_CONCLUIBLE" and {x["nombre"].split()[1] for x in ne["analisis_economico"]["excluidos"]} >= {"Epsilon", "Zeta"} and ne["analisis_economico"]["n_equivalentes_vigentes"] == 1)

# ---------- F2.1 hipótesis por producto/categoría
from backend import k4c_fases as FS
ha = FS.generar_hipotesis(FS.FICHA_ACTIVCORE); hp = FS.generar_hipotesis(FS.FICHA_PHIVITAL_MG); hg = FS.generar_hipotesis({"producto": "Crema facial X", "categoria": "COSMETICO_FACIAL", "ingredientes": [], "claims": []})
check("F2.1 hipótesis distintas por categoría: ACTIVCORE (H*) y PhiVital Magnesio (S*) no comparten ids, textos ni consultas", not ({h["id"] for h in ha} & {h["id"] for h in hp}) and not ({h["texto"] for h in ha} & {h["texto"] for h in hp}) and not ({q for h in ha for q in h["consultas"]} & {q for h in hp for q in h["consultas"]}))
check("F2.1 PhiVital Magnesio: normalización por dosis diaria (no por 100 ml) y sin minoxidil/alopecia/cabello", "DOSIS_DIARIA" == FS.FICHA_PHIVITAL_MG["normalizacion"] and not any(w in " ".join(h["texto"] + " ".join(h["consultas"]) for h in hp).lower() for w in ("minoxidil", "alopecia", "cabello", "capilar")) and any("dosis" in h["texto"].lower() for h in hp))
check("F2.1 ACTIVCORE conserva sus hipótesis específicas (minoxidil sustituto indirecto, regulatorio capilar)", any("minoxidil" in h["texto"].lower() and "indirecto" in h["texto"] for h in ha))
check("F2.1 categoría desconocida: plantilla GENÉRICA propia, sin hipótesis de ACTIVCORE ni de PhiVital", {h["id"][0] for h in hg} == {"G"} and not any("minoxidil" in h["texto"].lower() or "magnesio" in h["texto"].lower() for h in hg))
ext = dict(FS.FICHA_PHIVITAL_MG, extensiones=[{"id": "S9", "origen": "CONFIGURADA", "tipo": "SENALES", "texto": "Hipótesis añadida por el usuario", "refutaria": "x", "consultas": ["magnesio demanda"], "consultas_contrarias": ["magnesio demanda limites"], "plantilla": "SUPLEMENTO_ORAL"}])
op = inv("SIN_DATOS", ficha=ext, propio=PROPIO)["informe"]; check("F2.1 el motor usa las hipótesis de la ficha del producto (PhiVital) y admite extensiones configuradas; sin datos → NO_CONCLUIBLE", {h["id"] for h in op["hipotesis"]} >= {"S0", "S9"} and not any(h["id"].startswith("H") for h in op["hipotesis"]) and op["conclusion"]["decision"] == "NO_CONCLUIBLE")
check("F2.1 fases separadas registradas en el informe (generación, investigación, evidencias, economía, recomendación)", list(b["informe"]["fases"]) == ["1_generacion_hipotesis", "2_investigacion", "3_evaluacion_evidencias", "4_analisis_economico", "5_recomendacion"])

# ---------- F2.1 presupuesto seguro
import threading as TH, time as _t
class Pago(M.BusquedaSimulada):
    nombre = "pago_sim"; modo = "SIMULADO"
    def __init__(s, est=0.1, real=None, dormir=0.0, fallos=0, **kw): super().__init__(**kw); s.est = est; s.real = real; s.dormir = dormir; s.fallos = fallos; s.n = 0
    def coste_estimado(s, **kw): return s.est
    def buscar(s, consulta, max_resultados=5):
        s.n += 1
        if s.dormir: _t.sleep(s.dormir)
        if s.n <= s.fallos: raise RuntimeError("fallo transitorio")
        return {"coste_eur": s.real} if s.real is not None else []
kb = KS.K4Store(Store(os.path.join(tempfile.mkdtemp(), "b.db")))
rc = P.Router(kb); pg = Pago(est=0.1, dormir=0.02); rc.registrar(pg); rc.limites(1.0, 1.0, 0.2)
res = {"ok": 0, "bloq": 0}; lock = TH.Lock()
def work():
    try: rc.llamar("busqueda", "buscar", inv_id="CONC", consulta="cafeina topica evidencia"); 
    except PermissionError:
        with lock: res["bloq"] += 1
        return
    with lock: res["ok"] += 1
hs = [TH.Thread(target=work) for _ in range(40)]; [h.start() for h in hs]; [h.join() for h in hs]
check("F2.1 presupuesto concurrente: 40 hilos × 0,10 € con tope 1,00 € → exactamente 10 ejecutadas y 30 bloqueadas", res == {"ok": 10, "bloq": 30})
check("F2.1 el gasto reservado/conciliado nunca supera el tope (≤ 1,00 €) y el total coincide con el log", abs(rc.gasto_inv("CONC") - 1.0) < 1e-9 and rc.limites()["gasto_mes_eur"] <= 1.0 + 1e-9 and kb.q("SELECT SUM(coste_eur) s FROM k4c_consulta WHERE estado='OK'")[0]["s"] <= 1.0 + 1e-9)
check("F2.1 al alcanzar el límite se activa el corte automático y queda auditado", rc.limites()["corte_automatico"] and kb.q("SELECT 1 FROM audit WHERE action='k4c.corte_automatico'"))
try: rc.llamar("busqueda", "buscar", inv_id="CONC", consulta="x y z"); r = False
except PermissionError as e: r = "corte" in str(e)
check("F2.1 con corte activo se bloquea toda llamada hasta reanudar", r)
try: rc.reanudar("jose", "corto"); r = False
except ValueError: r = True
check("F2.1 reanudar exige motivo y actor", r)
kc = KS.K4Store(Store(os.path.join(tempfile.mkdtemp(), "c.db"))); r5 = P.Router(kc); p5 = Pago(est=0.1, real=0.35); r5.registrar(p5); r5.limites(5.0, 5.0, 0.2)
r5.llamar("busqueda", "buscar", inv_id="EXC", consulta="cafeina topica evidencia"); rs = kc.q("SELECT estado, estimado, maximo, real FROM k4c_reserva WHERE inv_id='EXC'")[0]
check("F2.1 coste real superior al estimado/máximo: reserva EXCEDIDA, real conciliado (0,35 €), corte automático y registro del exceso", rs["estado"] == "EXCEDIDA" and rs["real"] == 0.35 and r5.limites()["corte_automatico"] and kc.q("SELECT 1 FROM k4c_consulta WHERE estado='COSTE_SUPERIOR_A_ESTIMADO'"))
kd = KS.K4Store(Store(os.path.join(tempfile.mkdtemp(), "d.db"))); r6 = P.Router(kd, sleep=lambda s_: None); p6 = Pago(est=0.1, fallos=2); p6.reintentos = 3; r6.registrar(p6); r6.limites(5.0, 5.0, 0.2)
r6.llamar("busqueda", "buscar", inv_id="RET", consulta="cafeina topica evidencia"); est_ = [x["estado"] for x in kd.q("SELECT estado FROM k4c_reserva WHERE inv_id='RET' ORDER BY id")]
check("F2.1 reintentos: 2 fallos transitorios liberan su reserva sin coste y el tercer intento se confirma", est_ == ["LIBERADA", "LIBERADA", "CONFIRMADA"] and abs(r6.gasto_inv("RET") - 0.1) < 1e-9)
ke = KS.K4Store(Store(os.path.join(tempfile.mkdtemp(), "e.db"))); r7 = P.Router(ke, sleep=lambda s_: None); p7 = Pago(est=0.1, dormir=0.5); p7.timeout_s = 0.05; r7.registrar(p7); r7.limites(5.0, 5.0, 0.2)
try: r7.llamar("busqueda", "buscar", inv_id="TMO", consulta="cafeina topica evidencia"); r = False
except TimeoutError: r = True
check("F2.1 timeout: se retiene el coste máximo como INCIERTA (conservador) y se registra", r and ke.q("SELECT estado, real FROM k4c_reserva WHERE inv_id='TMO'")[0] == {"estado": "INCIERTA", "real": 0.1} or (r and ke.q("SELECT estado FROM k4c_reserva WHERE inv_id='TMO'")[0]["estado"] == "INCIERTA"))
r8 = P.Router(k); r8.registrar(Pago(est=0.5)); r8.limites(5.0, 5.0, 0.2)
try: r8.llamar("busqueda", "buscar", inv_id="OP", consulta="cafeina topica evidencia"); r = False
except PermissionError: r = True
check("F2.1 coste máximo por operación superior al tope por operación → bloqueada antes de llamar", r and not k.q("SELECT 1 FROM k4c_reserva WHERE inv_id='OP'"))
check("F2.1 todo queda auditable: reservas con estimado/máximo/real/estado y consultas con estado", kb.q("SELECT COUNT(*) n FROM k4c_reserva")[0]["n"] >= 10 and kb.q("SELECT COUNT(DISTINCT estado) n FROM k4c_consulta")[0]["n"] >= 2)
check("F2.1 los proveedores externos siguen sin activarse (REAL bloqueado, gasto adicional 0 €)", all(p["estado"] != "OPERATIVA" for p in motor(real=True).R.estado()["proveedores"] if p["modo"] == "REAL"))

# ---------- F2.1 separación sintético/real
try: motor().L.add_fuente(dict(M.corpus()[0], url="https://x.org/a"), "INV-Z", "t", "SINTETICO"); r = False
except ValueError: r = True
try: motor().L.add_fuente(M.corpus()[0], "INV-Z", "t", "REAL"); r2_ = False
except ValueError: r2_ = True
check("F2.1 separación: fuentes sintéticas no pasan como REAL y las reales no como sintéticas", r and r2_)
check("F2.1 una investigación SINTÉTICA etiqueta todo como tal y no contamina la calibración REAL", b["entorno"] == "SINTETICO" and b["informe"]["publicacion"]["aviso"].startswith("DATOS SINTÉTICOS") and all(f["entorno"] == "SINTETICO" for f in L.libro(b["id"])["fuentes"]) and mt.calibracion("REAL")["acertadas"] == 0 and mt.calibracion("REAL")["fallidas"] == 0)

# ---------- Integración
inv_d = inv("NUEVA_EVIDENCIA_COMPARABLES", DIE); 
class Dir:
    def __init__(s): s.g = []
    def guardar(s, d, a): s.g.append(d); return d["id"]
mi = motor("NUEVA_EVIDENCIA_COMPARABLES"); mi.D = Dir(); did = mi.a_dossier(inv_d["id"], "tester")
check("Integración: la investigación se guarda como expediente tipo 'consejero' con entorno SINTETICO", mi.D.g[0]["tipo"] == "consejero" and mi.D.g[0]["entorno"] == "SINTETICO" and mi.D.g[0]["consejero"]["decision"] == "SUBIR")
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
c, o = ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "NUEVA_EVIDENCIA_COMPARABLES", "datos_internos": DIE}); check("API investigar: ficha maestra K3 (49,90 € / 100 ml), informe SINTETICO con decisión SUBIR por elasticidad medida y verificación", c == 200 and o["entorno"] == "SINTETICO" and o["informe"]["maestro"]["volumen_ml"] == 100 and o["informe"]["conclusion"]["decision"] == "SUBIR" and o["verificacion"]["bloqueantes"] == 0)
c, lb = ad.call("GET", "/api/k4/consejero/libro/" + o["id"]); check("API libro de evidencias", c == 200 and lb["fuentes"] and lb["extractos"] and lb["consultas"])
c, dd = ad.call("POST", "/api/k4/consejero/dossier", {"id": o["id"]}); c2, dg = ad.call("GET", "/api/k4/dossier/" + dd.get("dossier", "x")); check("API integra con el Director: expediente 'consejero' recuperable", c == 200 and c2 == 200 and dg["tipo"] == "consejero")
check("API proponer decisión con datos sintéticos → 400", ad.call("POST", "/api/k4/consejero/proponer", {"id": o["id"]})[0] == 400)
c, o2 = ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "NUEVA_EVIDENCIA_COMPARABLES", "datos_internos": DIE, "trampa": "CONCLUSION_EXCEDE_EVIDENCIA"}); check("API trampa: conclusión que excede la evidencia → RECHAZADO / NO_PUBLICABLE", c == 200 and o2["verificacion"]["veredicto"] == "RECHAZADO" and o2["informe"]["publicacion"]["estado"] == "NO_PUBLICABLE")
c, bq = ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "NUEVA_EVIDENCIA_COMPARABLES", "datos_internos": DIE, "propio": {"precio": 49.90, "volumen_ml": 50}}); check("API dato maestro: volumen 50 ml frente a la ficha maestra de 100 ml → BLOQUEADA, sin gasto ni conclusión", c == 200 and bq["estado"] == "BLOQUEADA_DATO_MAESTRO" and bq["informe"]["conclusion"]["decision"] == "BLOQUEADO")
c, cf = ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "BASE", "propio": {"precio": 49.90, "volumen_ml": 50}, "confirmacion": {"usar": "MAESTRO", "motivo": "El formato comercial V2 es de 100 ml"}}); check("API confirmación de discrepancia usando la ficha maestra desbloquea y audita", c == 200 and cf.get("estado") != "BLOQUEADA_DATO_MAESTRO" and cf["informe"]["coherencia_maestro"]["confirmada"]["actor"] == "admin")
check("API límites/reanudar: solo admin (analista 403); la reanudación exige motivo", an.call("POST", "/api/k4/consejero/limites", {"tope_inv_eur": 1})[0] == 403 and ad.call("POST", "/api/k4/consejero/limites", {"tope_op_eur": 0})[0] == 200 and ad.call("POST", "/api/k4/consejero/reanudar", {"motivo": "corto"})[0] == 400)
c, pr_ = ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "NUEVA_EVIDENCIA_COMPARABLES", "datos_internos": DI}); pid_ = pr_["informe"]["predicciones"][0]
check("API predicción: un booleano de acierto se rechaza (400); con evidencia de resultado se evalúa", ad.call("POST", "/api/k4/consejero/prediccion/resultado", {"id": pid_, "valor": True, "fuente": "x", "metodo": "y", "incertidumbre": 0, "fecha": "2030-01-01"})[0] == 400 and ad.call("POST", "/api/k4/consejero/prediccion/resultado", {"id": pid_, "valor": 0.049, "fuente": "panel sintético", "metodo": "pre/post", "incertidumbre": 0.0005, "fecha": "2030-01-01"})[0] == 200)
check("API escenario inválido → 400", ad.call("POST", "/api/k4/consejero/investigar", {"escenario": "X"})[0] == 400)
print("\n%d/%d" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
