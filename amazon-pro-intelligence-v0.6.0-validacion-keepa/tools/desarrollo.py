#!/usr/bin/env python3
"""Ciclo de desarrollo autónomo acotado (V0.7.0): desarrollo -> pruebas de aceptación -> corrección (máx. 3 intentos) -> auditoría -> nueva ejecución.

El código lo escribe una SESIÓN de Claude (manual o programada); este módulo es el que impone el proceso y deja constancia:
  siguiente            elige el próximo objetivo de desarrollo (prioridad, dependencias); lo marca EN_CURSO y muestra su especificación
  verificar OBJ-xxx    ejecuta la prueba de aceptación; PASA -> HECHO; FALLA -> intento+1; al 3.er fallo -> BLOQUEADO (se sigue con otro objetivo)
  auditoria            regresión completa (todas las suites) + escaneo de secretos + integridad del registro + no se borran pruebas anteriores
  estado               resumen del backlog V0.7.0
  sembrar              (re)crea el backlog V0.7.0 en AUTONOMIA/estado.json (idempotente por clave)
Límites heredados del coordinador: gasto 0 €, 0 tokens Keepa, 0 llamadas de IA; entorno de pruebas sin claves.
"""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coordinador as C

MAX_INTENTOS = 3
BACKLOG = [  # clave, prioridad, título, especificación (qué debe cumplir la prueba), prueba de aceptación, depende
    ("V7-01", 10, "Datos reales de Keepa integrados (sin red ni gasto)",
     "backend/keepa_real.py + GET /api/v07/keepa-real?product=<id>: carga docs_v06/evidencia_keepa_real (competidores_ES) y devuelve por competidor precio, price_as_of, BSR, fuente 'Keepa /search (real)', comparabilidad 'NO CONFIRMADA'; resumen (n, mediana y rango de precio, precio normalizado por 100 mL si hay contenido); cero llamadas de red; si falta la evidencia -> SIN DATOS (nunca ceros); títulos externos tratados como datos no fiables (sanitizados).",
     "python3 tests/v070_keepa_real_test.py", []),
    ("V7-02", 20, "Expediente comercial ACTIVCORE v0.7",
     "backend/expediente7.py + GET /api/v07/expediente?product=<id>&fmt=json|md: secciones producto, economía (con huecos), mercado real Keepa, regulatorio (requisitos sin evidencia), decisión (NO DECIDIBLE mientras falten datos: nunca GO por defecto), desbloqueos priorizados con propietario y coste (€/tokens), trazabilidad de fuente y fecha por dato; export md determinista.",
     "python3 tests/v070_expediente_test.py", ["V7-01"]),
    ("V7-03", 30, "Director IA: briefing determinista con hechos citados",
     "backend/director7.py + GET /api/v07/briefing?product=<id>: prioridades ordenadas por valor de desbloqueo, máx. 5 preguntas al propietario, hechos [F#] con categoría (DOCUMENTADO/CÁLCULO/INFERENCIA/NO DISPONIBLE), guardia que impide convertir NO DECIDIBLE en GO, texto de competidores con instrucciones inyectadas permanece como dato; funciona SIN IA (sin llamadas).",
     "python3 tests/v070_director_test.py", ["V7-01", "V7-02"]),
    ("V7-04", 40, "Experiencia NEON: Director IA, expediente y procedencia del dato",
     "js/v07.js + estilos: en DIRECTOR IA y LANZAMIENTOS mostrar briefing, expediente y datos reales de Keepa con insignias de procedencia (REAL / CALCULADO / SIN DATOS / NO CONFIRMADO), estados vacíos explicados, accesibilidad (roles/aria, foco), sin errores de consola; capturas 40+ en CAPTURAS_UI.",
     "python3 tests/ui_v07_test.py", ["V7-03"]),
    ("V7-05", 50, "Seguridad de los nuevos endpoints /api/v07/*",
     "Rol y sesión exigidos, CSRF en POST, sin exposición de claves ni rutas del servidor, límites de tamaño, errores sin traza; pruebas negativas.",
     "python3 tests/v070_security_test.py", ["V7-01"]),
    ("V7-06", 60, "Registro de suites v0.7 en la batería y el coordinador",
     "Añadir las suites v070_* y ui_v07 a tests/run_all.sh y a SUITES del coordinador; la batería completa debe pasar.",
     "python3 tests/v070_registro_test.py", ["V7-04", "V7-05"]),
    ("V7-07", 70, "Entrega candidata V0.7.0 (código, documentación, pruebas, evidencias)",
     "INFORME_V070.md (qué se probó y qué NO: Windows y conexiones externas no verificadas), ZIP sin claves con sha256, capturas, registro de auditoría; coordinador.respaldo OK.",
     "python3 tests/v070_entrega_test.py", ["V7-06"]),
]


def _o(e, clave): return next((o for o in e["objetivos"] if o.get("clave") == clave), None)

BACKLOG_V1 = [  # V1.0 — cada objetivo exige crear su prueba tests/v100_*_test.py (la prueba es la aceptación)
    ("V1-01", 5, "Infraestructura de relevo: bloqueo, recuperación y commit controlado", "tools/relevo.py --adquirir/--commit/--publicar --liberar.", "python3 tests/relevo_test.py", []),
    ("V1-02", 10, "Matriz de aceptación V1.0 (4 categorías) generada desde el estado real", "tools/matriz_v100.py genera MATRIZ_ACEPTACION_V100.md: cada requisito en VERIFICADO REAL / VERIFICADO SIMULADO / IMPLEMENTADO NO VERIFICADO / BLOQUEADO (con causa y propietario). Sin marcar real lo simulado.", "python3 tests/v100_matriz_test.py", []),
    ("V1-03", 20, "PREPARAR Y LANZAR: flujo completo ACTIVCORE con persistencia", "Flujo de extremo a extremo en la UI y API: producto → hipótesis → expediente → decisión registrada → persistencia tras reinicio del servidor. Sin datos inventados; huecos explícitos.", "python3 tests/v100_lanzar_test.py", ["V1-02"]),
    ("V1-04", 30, "VENDER Y OPTIMIZAR con informes CSV importados (datos simulados etiquetados)", "Importar CSV de ventas/anuncios, validar columnas, calcular métricas deterministas (ACOS, margen, conversión), etiqueta SIMULADO cuando el dato no sea real; rechazo de CSV malformado.", "python3 tests/v100_vender_test.py", ["V1-02"]),
    ("V1-05", 40, "Motor financiero determinista: escenarios, sensibilidad, punto de equilibrio", "Hipótesis etiquetadas como tales, resultados reproducibles, sin costes inventados: NO CALCULABLE si falta un dato.", "python3 tests/v100_finanzas_test.py", ["V1-02"]),
    ("V1-06", 50, "Exportaciones CSV/HTML/Markdown con trazabilidad", "Exportar expediente y resultados con fuente, fecha y procedencia; escapado seguro; nombre de fichero saneado.", "python3 tests/v100_export_test.py", ["V1-03", "V1-04", "V1-05"]),
    ("V1-07", 60, "Director IA: plan de coordinación de especialistas", "Plan determinista de especialistas (mercado, regulatorio, finanzas, listing, ads) con entradas, salidas, dependencias y propietario; nunca GO por defecto.", "python3 tests/v100_director_plan_test.py", ["V1-03"]),
    ("V1-08", 70, "Persistencia y recuperación: copia de seguridad, restauración y BD corrupta", "Backup/restore de SQLite verificado con hash; arranque con BD corrupta falla de forma controlada sin pérdida; persistencia entre sesiones.", "python3 tests/v100_persistencia_test.py", []),
    ("V1-09", 80, "NEON: cinco secciones en móvil y escritorio (Chromium real) y corrección de desbordes", "Playwright a 390, 820 y 1600 px: sin desbordes horizontales (incluye .hr/.sess a 820 px), producto por defecto ACTIVCORE, sin errores de consola, capturas.", "python3 tests/ui_v100_test.py", ["V1-03", "V1-04"]),
    ("V1-10", 90, "Ficha única de integraciones bloqueadas", "FICHA_INTEGRACIONES_V100.md: credencial, permiso y acción del propietario por integración (Keepa, OpenAI, SP-API, Ads API, DE/FR/IT/UK, Windows), sin pedir secretos.", "python3 tests/v100_ficha_test.py", ["V1-02"]),
    ("V1-11", 100, "Manual de Sergio v1.0 y documentación de instalación y operación", "MANUAL_SERGIO_V100.md, INSTALACION_V100.md, OPERACION: pasos verificables, sin afirmar Windows verificado.", "python3 tests/v100_docs_test.py", ["V1-03", "V1-04", "V1-10"]),
    ("V1-13", 105, "Adaptadores OpenAI, SP-API y Ads API (solo lectura) con pruebas simuladas identificadas", "backend/conectores100.py: un adaptador por servicio con credenciales leídas solo de ficheros .env locales, solo lectura, tope de gasto 0, modo SIMULADO explícito en cada respuesta (campo origen='SIMULADO'), estado NO CONECTADO sin credenciales, nunca declarar operativo sin prueba real; prueba con servidor HTTP local simulado y guardia de red.", "python3 tests/v100_conectores_test.py", ["V1-10"]),
    ("V1-14", 108, "Despliegue cloud privado: modo cloud, HTTPS, usuarios por variables secretas, respaldo y paquete Docker/Render", "server.py modo cloud (host público, solo HTTPS, cookie Secure, HSTS, /healthz, sin secretos en logs, usuarios sembrados, respaldo automático) + Dockerfile + render.yaml; probado con proceso real y proxy HTTPS local; el despliegue en proveedor NO se realiza sin autorización de coste.", "python3 tests/v100_cloud_test.py && python3 tests/ui_v100_cloud_test.py", ["V1-08", "V1-09"]),
    ("V1-12", 110, "Entrega candidata V1.0 (ZIP sin claves, copia, evidencias, bloqueos)", "Informe generado desde el estado real, ZIP sin secretos, hash, lista de bloqueos externos; NO etiquetar producción.", "python3 tests/v100_entrega_test.py", ["V1-06", "V1-07", "V1-08", "V1-09", "V1-11", "V1-13"]),
]


def sembrar():
    e = C.estado(); n = 0
    for clave, prio, titulo, spec, acept, dep in BACKLOG + BACKLOG_V1:
        if _o(e, clave): continue
        e["objetivos"].append({"id": "OBJ-%03d" % (len(e["objetivos"]) + 1), "clave": clave, "tipo": "dev", "titulo": ("V1.0 · " if clave.startswith("V1-") else "V0.7.0 · ") + titulo, "estado": "PENDIENTE", "prioridad": prio, "handler": None,
                               "spec": spec, "aceptacion": acept, "depende": dep, "intentos": 0, "historial": [], "creado": C.now(), "nota": None, "cada_horas": None}); n += 1
    C.guardar(e); C.log("DEV_SEMBRADO", nuevos=n); return {"nuevos": n, "total_dev": sum(1 for o in e["objetivos"] if o.get("tipo") == "dev")}


def _listo(e, o):
    for d in o.get("depende", []):
        x = _o(e, d)
        if not x or x["estado"] != "HECHO": return False
    return True


def siguiente():
    ok, motivo = C.guardia()
    if not ok: return {"objetivo": None, "motivo": motivo}
    e = C.estado()
    cur = [o for o in e["objetivos"] if o.get("tipo") == "dev" and o["estado"] == "EN_CURSO"]
    cand = cur or sorted([o for o in e["objetivos"] if o.get("tipo") == "dev" and o["estado"] == "PENDIENTE" and _listo(e, o)], key=lambda o: o["prioridad"])
    if not cand:
        bloq = [o["clave"] for o in e["objetivos"] if o.get("tipo") == "dev" and o["estado"] == "BLOQUEADO"]
        return {"objetivo": None, "motivo": "Sin objetivos de desarrollo ejecutables", "bloqueados": bloq}
    o = cand[0]; o["estado"] = "EN_CURSO"; o["actualizado"] = C.now(); C.guardar(e); C.log("DEV_INICIO", id=o["id"], clave=o["clave"], intentos=o["intentos"])
    return {"objetivo": {k: o[k] for k in ("id", "clave", "titulo", "spec", "aceptacion", "intentos", "historial")}, "reglas": "Escribe primero la prueba de aceptación (debe fallar), implementa, ejecuta `verificar`. Máx. %d intentos; sin gasto, sin claves, sin red de pago." % MAX_INTENTOS}


def verificar(clave):
    e = C.estado(); o = _o(e, clave) or next((x for x in e["objetivos"] if x["id"] == clave), None)
    if not o or o.get("tipo") != "dev": return {"error": "objetivo de desarrollo inexistente"}
    r = C._ejecutar(o["aceptacion"], C.limites()["timeout_suite_s"]); e = C.estado(); o = _o(e, o["clave"]); o["intentos"] += 1
    o["historial"] = (o["historial"] + [{"t": C.now(), "intento": o["intentos"], "rc": r["rc"], "resultado": r["ultima_linea"], "cola": r["cola"][-300:]}])[-5:]
    if r["rc"] == 0: o["estado"] = "HECHO"; o["nota"] = "aceptación OK: " + r["ultima_linea"]; e["fallos_consecutivos"] = 0
    elif o["intentos"] >= MAX_INTENTOS: o["estado"] = "BLOQUEADO"; o["nota"] = "BLOQUEADO tras %d intentos: %s" % (o["intentos"], r["ultima_linea"])
    else: o["estado"] = "EN_CURSO"; o["nota"] = "intento %d/%d fallido: %s" % (o["intentos"], MAX_INTENTOS, r["ultima_linea"])
    o["actualizado"] = C.now(); e["siguientes_acciones"] = C._siguientes(e); C.guardar(e)
    C.log("DEV_VERIFICAR", clave=o["clave"], estado=o["estado"], intento=o["intentos"], rc=r["rc"])
    return {"clave": o["clave"], "estado": o["estado"], "intento": o["intentos"], "rc": r["rc"], "resultado": r["ultima_linea"], "cola": r["cola"] if r["rc"] else "",
            "siguiente_paso": {"HECHO": "ejecuta `siguiente`", "EN_CURSO": "corrige y vuelve a `verificar`", "BLOQUEADO": "registrado; ejecuta `siguiente` (tareas independientes)"}[o["estado"]]}


def _git(*a):
    p = subprocess.run(["git"] + list(a), cwd=C.ROOT, capture_output=True, text=True); return p.stdout.strip() if p.returncode == 0 else None


def auditoria():
    """Auditoría independiente del código escrito: no confía en lo que dijo la sesión que lo escribió."""
    det = {}; qa = C.qa(); det["suites"] = {k: qa[k] for k in ("pasan", "intermitentes", "fallan", "total")}
    det["escaneo_secretos"] = len(C.escaneo()); det["registro_integro"] = C.verificar()["ok"]
    borr = _git("diff", "--diff-filter=D", "--name-only", "origin/aht-v060-validado...HEAD"); det["archivos_v060_borrados"] = [f for f in (borr.splitlines() if borr else []) if "/AUTONOMIA/" not in f]  # AUTONOMIA/ salió del código a propósito (vive en aht-autonomia-estado) if borr is not None else "no comprobable (sin git/origen)"
    run_all = open(os.path.join(C.ROOT, "tests", "run_all.sh"), encoding="utf-8").read() if os.path.exists(os.path.join(C.ROOT, "tests", "run_all.sh")) else ""
    tests_v7 = [f for f in os.listdir(os.path.join(C.ROOT, "tests")) if f.startswith(("v070_", "ui_v07", "relevo_", "v100_", "ui_v100")) and f.endswith(".py")]
    det["pruebas_v07_sin_registrar"] = [f for f in tests_v7 if f not in run_all]
    ok = det["suites"]["fallan"] == 0 and det["escaneo_secretos"] == 0 and det["registro_integro"] and not det["archivos_v060_borrados"]
    e = C.estado(); e["auditoria"] = {"t": C.now(), "ok": ok, "detalle": det}; C.guardar(e); C.log("DEV_AUDITORIA", ok=ok, **{k: v for k, v in det["suites"].items()})
    return {"ok": ok, "detalle": det}


def resumen():
    e = C.estado(); return {"dev": [{"clave": o["clave"], "estado": o["estado"], "intentos": o["intentos"], "depende": o["depende"], "nota": o["nota"]} for o in e["objetivos"] if o.get("tipo") == "dev"], "auditoria": e.get("auditoria"), "guardia": C.guardia()}


def main(a=None):
    a = (a if a is not None else sys.argv)[1:]; c = a[0] if a else "estado"
    out = {"sembrar": sembrar, "siguiente": siguiente, "auditoria": auditoria, "estado": resumen}.get(c, lambda: None)() if c != "verificar" else verificar(a[1])
    if out is None: print(__doc__); return 2
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str)); return 0


if __name__ == "__main__": sys.exit(main())
