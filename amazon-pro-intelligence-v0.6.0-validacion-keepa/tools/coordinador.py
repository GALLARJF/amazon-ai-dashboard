#!/usr/bin/env python3
"""AHT Coordinador autónomo (V0.6.1) — registro persistente de objetivos, estado, errores, pruebas y siguientes acciones.

QUÉ ES: un programa de biblioteca estándar de Python que mantiene el estado del trabajo en AUTONOMIA/ (versionable, sin secretos) y ejecuta
        ciclos acotados: guardia (parada/gasto) -> objetivo pendiente -> QA con reintentos limitados -> registro -> informe.
QUÉ NO ES: no es ejecución continua. Solo corre cuando alguien (una sesión de Claude, una tarea programada o una persona) lo invoca.
GASTO: por diseño el coordinador NUNCA activa Keepa/OpenAI/Amazon: las pruebas se lanzan con el entorno saneado (sin claves y con
       AMAZON_PRO_KEEPA_ENABLE=0). Cualquier presupuesto >0 solo lo puede fijar el propietario editando AUTONOMIA/limites.json.
Uso:  python3 tools/coordinador.py {init|estado|ciclo|qa|objetivo|conexion|limitacion|escaneo|informe|verificar|parar|reanudar|respaldo}"""
import hashlib, json, os, re, signal, subprocess, sys, time

ROOT = os.environ.get("AHT_PROYECTO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUT = os.path.join(ROOT, "AUTONOMIA")
F_EST, F_REG, F_LIM, F_STOP, F_LOCK = (os.path.join(AUT, n) for n in ("estado.json", "registro.jsonl", "limites.json", "PARAR", "ciclo.lock"))

LIMITES = {"max_intentos_incidencia": 3, "max_ciclos_24h": 12, "max_fallos_consecutivos": 3, "timeout_suite_s": 420,
           "presupuesto_eur": 0, "keepa_tokens_max": 0, "llamadas_ia_max": 0,
           "nota": "Con 0 el coordinador bloquea cualquier gasto. Solo el propietario debe cambiar estos valores."}
SUITES = [  # nombre, comando, clase (MOCK = proveedores simulados; REAL = lee evidencias de llamadas reales ya hechas, sin red)
    ("keepa-cliente", "python3 tests/keepa_test.py", "MOCK"), ("keepa-misión", "python3 tests/keepa_mision_test.py", "MOCK"),
    ("keepa-flujo-Director", "python3 tests/keepa_mision_flow_test.py", "MOCK"), ("keepa-evidencias-reales", "python3 tests/keepa_real_evidence_test.py", "REAL-EVIDENCIA"),
    ("v0.6-operación", "python3 tests/v060_test.py", "MOCK"), ("v0.5-catálogo", "python3 tests/v050_test.py", "MOCK"), ("API", "python3 tests/api_test.py", "MOCK"),
    ("lanzador", "python3 tests/launcher_test.py", "LOCAL"), ("UI-v0.6", "python3 tests/ui_v06_test.py", "MOCK+NAVEGADOR"),
    ("v0.7-keepa-real", "python3 tests/v070_keepa_real_test.py", "REAL-EVIDENCIA"), ("v0.7-expediente", "python3 tests/v070_expediente_test.py", "MOCK"), ("v0.7-director", "python3 tests/v070_director_test.py", "MOCK"),
    ("v0.7-seguridad", "python3 tests/v070_security_test.py", "MOCK"), ("UI-v0.7", "python3 tests/ui_v07_test.py", "MOCK+NAVEGADOR"), ("P0-F4-pantallas", "python3 tests/ui_fase4_test.py", "MOCK+NAVEGADOR"), ("P0-F4-amazon", "python3 tests/amazon_arch_test.py", "MOCK"), ("P0-F4.1-lectura", "python3 tests/amazon_lectura_test.py", "MOCK"), ("P0-final-staging", "python3 tests/ui_staging_final_test.py", "MOCK+NAVEGADOR"), ("P0-4.2-viewer-total", "python3 tests/ui_viewer_ro_total_test.py", "MOCK+NAVEGADOR"), ("P0-F4.1-prod1440", "python3 tests/ui_prod_1440_test.py", "MOCK+NAVEGADOR"), ("P0-F4-paridad", "python3 tests/ui_legacy_paridad_test.py", "MOCK+NAVEGADOR"), ("P0-F2-HOY", "python3 tests/ui_hoy_test.py", "MOCK+NAVEGADOR"), ("P0-F2-modo", "python3 tests/ui_hoy_modo_test.py", "MOCK+NAVEGADOR"), ("P0-F2.1", "python3 tests/ui_fase21_test.py", "MOCK+NAVEGADOR"), ("P0-F3-lanz", "python3 tests/ui_lanz_test.py", "MOCK+NAVEGADOR"), ("P0-F3.1-aislamiento", "python3 tests/ui_lanz_aislamiento_test.py", "MOCK+NAVEGADOR"), ("P0-F3-modo", "python3 tests/ui_lanz_modo_test.py", "MOCK+NAVEGADOR"), ("P0-F2-viewer", "python3 tests/ui_viewer_ro_test.py", "MOCK+NAVEGADOR"), ("desarrollo", "python3 tests/desarrollo_test.py", "LOCAL"), ("relevo", "python3 tests/relevo_test.py", "LOCAL"), ("v1.0-matriz", "python3 tests/v100_matriz_test.py", "LOCAL"), ("v1.0-lanzar", "python3 tests/v100_lanzar_test.py", "MOCK"), ("v1.0-vender", "python3 tests/v100_vender_test.py", "MOCK"), ("v1.0-finanzas", "python3 tests/v100_finanzas_test.py", "MOCK"), ("v1.0-export", "python3 tests/v100_export_test.py", "MOCK"), ("v1.0-persistencia", "python3 tests/v100_persistencia_test.py", "MOCK"), ("v1.0-ficha", "python3 tests/v100_ficha_test.py", "MOCK"), ("v1.0-ui", "python3 tests/ui_v100_test.py", "MOCK+NAVEGADOR"), ("v1.0-plan", "python3 tests/v100_director_plan_test.py", "MOCK"), ("v1.0-conectores", "python3 tests/v100_conectores_test.py", "MOCK"), ("v1.0-docs", "python3 tests/v100_docs_test.py", "MOCK"), ("v1.0-entrega", "python3 tests/v100_entrega_test.py", "LOCAL"), ("v1.0-cloud", "python3 tests/v100_cloud_test.py", "MOCK"), ("v1.0-ui-cloud", "python3 tests/ui_v100_cloud_test.py", "MOCK+NAVEGADOR"), ("v1.0-respaldo-cloud", "python3 tests/v100_respaldo_cloud_test.py", "MOCK"), ("k1-keepa", "python3 tests/k1_keepa_test.py", "MOCK"), ("k1-http", "python3 tests/k1_http_test.py", "MOCK"), ("k2-director", "python3 tests/k2_director_test.py", "MOCK"), ("k3-segmentacion", "python3 tests/k3_segmentacion_test.py", "MOCK"), ("UI-k3", "python3 tests/ui_k3_test.py", "MOCK+NAVEGADOR"), ("k4-unidad", "python3 tests/k4_unit_test.py", "MOCK"), ("k4-planificador", "python3 tests/k4_planner_test.py", "MOCK"), ("k4-consejero", "python3 tests/k4c_test.py", "MOCK"), ("staging-viewer", "python3 tests/viewer_test.py", "MOCK"), ("ui-nav-fase1", "python3 tests/ui_nav_test.py", "MOCK+NAVEGADOR"), ("ui-nav-modo", "python3 tests/ui_nav_modo_test.py", "MOCK+NAVEGADOR"), ("k4-iter2", "python3 tests/k4_iter2_test.py", "MOCK"), ("k4-api", "python3 tests/k4_api_test.py", "MOCK"), ("UI-k4", "python3 tests/ui_k4_test.py", "MOCK+NAVEGADOR"),
    ("v0.7-registro", "python3 tests/v070_registro_test.py", "LOCAL"), ("v0.7-entrega", "python3 tests/v070_entrega_test.py", "LOCAL")]
SECRETO = re.compile(r"(KEEPA_API_KEY|OPENAI_API_KEY|api[_-]?key|secret|token)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{24,})['\"]?", re.I)
FALSO = re.compile(r"CENTINELA|FALS[OA]|FAKE|EJEMPLO|MOCK|DEMO|DUMMY|PLACEHOLDER", re.I)  # centinelas de pruebas: valores inventados a propósito
SK = re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")
SKIP_DIRS = {".git", "__pycache__", "node_modules", "CAPTURAS_UI"}


def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read(p, d):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError): return d


def _write(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True); t = p + ".tmp"
    with open(t, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(t, p)


def limites(): return {**LIMITES, **_read(F_LIM, {})}


def estado():
    e = _read(F_EST, None)
    if e is None: e = {"version": 1, "creado": now(), "objetivos": [], "incidencias": [], "ejecuciones": [], "conexiones": [], "limitaciones": [], "siguientes_acciones": [], "pruebas": {}, "ciclos": [], "fallos_consecutivos": 0}
    return e


def guardar(e): e["actualizado"] = now(); _write(F_EST, e)


def log(evento, **datos):
    """Registro de solo-añadir con cadena de hashes (detecta ediciones o borrados)."""
    os.makedirs(AUT, exist_ok=True); prev = "0" * 64
    try:
        with open(F_REG, "rb") as f:
            for ln in f: prev = json.loads(ln)["h"]
    except (OSError, ValueError): pass
    rec = {"t": now(), "e": evento, "d": datos, "p": prev}; rec["h"] = hashlib.sha256(json.dumps(rec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    with open(F_REG, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def verificar():
    prev = "0" * 64; n = 0
    try:
        with open(F_REG, encoding="utf-8") as f:
            for ln in f:
                r = json.loads(ln); h = r.pop("h")
                if r["p"] != prev or hashlib.sha256(json.dumps(r, sort_keys=True, ensure_ascii=False).encode()).hexdigest() != h: return {"ok": False, "linea": n + 1}
                prev = h; n += 1
    except OSError: return {"ok": True, "lineas": 0}
    except ValueError: return {"ok": False, "linea": n + 1}
    return {"ok": True, "lineas": n}


# ---------------------------------------------------------------- guardia: parada y gasto ----------------------------------------------------------------
def entorno_seguro():
    """Entorno para las pruebas: sin claves y con Keepa desactivado. Garantiza que un ciclo no puede gastar tokens ni llamar a APIs de pago."""
    env = {k: v for k, v in os.environ.items() if not re.search(r"KEEPA|OPENAI|ANTHROPIC_API|AWS_|SECRET|PASSWORD", k, re.I)}
    env.update(AMAZON_PRO_KEEPA_ENABLE="0", AMAZON_PRO_NO_WORKER="1", PYTHONDONTWRITEBYTECODE="1"); return env


def guardia():
    """(ok, motivo). Parada automática si: PARAR existe, hay claves/archivos de clave reales en el proyecto, el presupuesto no es 0 sin autorización,
    se superó el nº de ciclos en 24 h o hubo demasiados fallos seguidos."""
    L = limites(); e = estado()
    if os.path.exists(F_STOP): return False, "PARADA MANUAL/AUTOMÁTICA: " + (open(F_STOP, encoding="utf-8").read().strip()[:200] or "sin motivo")
    for n in ("keepa.env", "ai.env"):
        if os.path.exists(os.path.join(ROOT, n)): return False, "Hay un archivo de claves (%s) dentro del proyecto: no se ejecuta nada hasta retirarlo" % n
    if (L["presupuesto_eur"] or L["keepa_tokens_max"] or L["llamadas_ia_max"]) and not L.get("autorizado_por"):
        return False, "Presupuesto >0 sin «autorizado_por» del propietario en limites.json"
    desde = time.time() - 86400; rec = [c for c in e["ciclos"] if c["ts"] >= desde]
    if len(rec) >= L["max_ciclos_24h"]: return False, "Tope de %d ciclos en 24 h alcanzado" % L["max_ciclos_24h"]
    if e["fallos_consecutivos"] >= L["max_fallos_consecutivos"]: return False, "%d ciclos fallidos seguidos: requiere revisión humana" % e["fallos_consecutivos"]
    return True, "OK"


def parar(motivo):
    os.makedirs(AUT, exist_ok=True); open(F_STOP, "w", encoding="utf-8").write("%s · %s" % (now(), motivo)); log("PARADA", motivo=motivo)


def reanudar():
    if os.path.exists(F_STOP): os.remove(F_STOP)
    e = estado(); e["fallos_consecutivos"] = 0; guardar(e); log("REANUDADA")


def escaneo():
    """Busca claves reales en el proyecto antes de empaquetar o subir. Ignora valores obviamente falsos (un solo carácter repetido, 'xxx…')."""
    hallazgos = []
    for r, ds, fs in os.walk(ROOT):
        ds[:] = [d for d in ds if d not in SKIP_DIRS]
        for f in fs:
            p = os.path.join(r, f)
            if f.endswith((".png", ".zip", ".db", ".gz", ".ico", ".pyc", ".tar")) or os.path.getsize(p) > 3_000_000: continue
            rel = os.path.relpath(p, ROOT)
            if f in ("keepa.env", "ai.env"): hallazgos.append({"archivo": rel, "motivo": "archivo de claves"}); continue
            try: txt = open(p, encoding="utf-8", errors="ignore").read()
            except OSError: continue
            for m in SECRETO.finditer(txt):
                v = m.group(2)
                if len(set(v)) <= 2 or v.lower().startswith(("x", "tu_", "your", "pon_", "plantilla")) or "_" in v and v.isupper() or FALSO.search(v): continue
                hallazgos.append({"archivo": rel, "motivo": "posible clave (%s…)" % m.group(1), "valor_oculto": True}); break
            else:
                if [m for m in SK.findall(txt) if not FALSO.search(m)]: hallazgos.append({"archivo": rel, "motivo": "patrón sk-"})
    return hallazgos


# ---------------------------------------------------------------- QA con reintentos ----------------------------------------------------------------
def _ejecutar(cmd, timeout):
    """Ejecuta en su propio grupo de procesos y, al terminar o expirar, mata TODO el grupo (evita huérfanos que retienen tuberías)."""
    t0 = time.time(); p = subprocess.Popen(cmd, shell=True, cwd=ROOT, env=entorno_seguro(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    try: out, _ = p.communicate(timeout=timeout); rc = p.returncode; to = False
    except subprocess.TimeoutExpired:
        to = True
        try: os.killpg(p.pid, signal.SIGKILL)
        except OSError: pass
        out, _ = p.communicate(); rc = -9
    finally:
        try: os.killpg(p.pid, signal.SIGKILL)
        except OSError: pass
    txt = (out or b"").decode("utf-8", "replace"); ult = [l for l in txt.strip().splitlines() if l.strip()][-1:] or [""]
    return {"rc": rc, "timeout": to, "segundos": round(time.time() - t0, 1), "ultima_linea": ult[0][:200], "cola": txt[-600:]}


def qa(suites=None, intentos=None):
    """Ejecuta las suites; reintenta las que fallan hasta `intentos` veces EN ESTA llamada. PASA / INTERMITENTE (pasó tras reintento) / FALLA (persistente)."""
    L = limites(); e = estado(); intentos = intentos or L["max_intentos_incidencia"]; res = []
    for nombre, cmd, clase in (suites or SUITES):
        hist = []
        for i in range(1, intentos + 1):
            r = _ejecutar(cmd, L["timeout_suite_s"]); r["intento"] = i; hist.append(r)
            if r["rc"] == 0: break
        ok = hist[-1]["rc"] == 0; est = ("PASA" if len(hist) == 1 else "INTERMITENTE") if ok else "FALLA"
        res.append({"suite": nombre, "clase": clase, "estado": est, "intentos": len(hist), "resultado": hist[-1]["ultima_linea"], "segundos": hist[-1]["segundos"]})
        inc = next((x for x in e["incidencias"] if x["suite"] == nombre and x["estado"] != "RESUELTA"), None)
        if est == "PASA" and inc: inc.update(estado="RESUELTA", resuelta=now())
        if est in ("INTERMITENTE", "FALLA"):
            if not inc:
                inc = {"id": "INC-%03d" % (len(e["incidencias"]) + 1), "suite": nombre, "creada": now(), "intentos_acumulados": 0, "estado": "ABIERTA", "tipo": None, "historial": []}; e["incidencias"].append(inc)
            inc["intentos_acumulados"] += len(hist); inc["tipo"] = "INTERMITENTE" if ok else "PERSISTENTE"
            inc["historial"].append({"t": now(), "estado": est, "cola": hist[-1]["cola"][-300:]}); inc["historial"] = inc["historial"][-5:]
            if ok: inc["estado"] = "ABIERTA"
            elif inc["intentos_acumulados"] >= L["max_intentos_incidencia"]: inc["estado"] = "BLOQUEADA"
            log("INCIDENCIA", id=inc["id"], suite=nombre, estado=inc["estado"], intentos=inc["intentos_acumulados"])
    e["pruebas"] = {"ts": now(), "resultados": res, "pasan": sum(r["estado"] == "PASA" for r in res), "intermitentes": sum(r["estado"] == "INTERMITENTE" for r in res), "fallan": sum(r["estado"] == "FALLA" for r in res), "total": len(res)}
    guardar(e); log("QA", pasan=e["pruebas"]["pasan"], intermitentes=e["pruebas"]["intermitentes"], fallan=e["pruebas"]["fallan"]); return e["pruebas"]


# ---------------------------------------------------------------- objetivos, conexiones, limitaciones -------------------------------------------------
def objetivo(accion, titulo=None, oid=None, handler=None, prio=5, nota=None, cada_horas=None):
    e = estado()
    if accion == "add":
        o = {"id": "OBJ-%03d" % (len(e["objetivos"]) + 1), "titulo": titulo, "estado": "PENDIENTE", "prioridad": prio, "handler": handler, "creado": now(), "nota": nota, "cada_horas": cada_horas}; e["objetivos"].append(o)
    else:
        o = next((x for x in e["objetivos"] if x["id"] == oid), None)
        if not o: raise SystemExit("objetivo inexistente")
        o["estado"] = {"hecho": "HECHO", "bloquear": "BLOQUEADO", "reabrir": "PENDIENTE", "curso": "EN_CURSO"}[accion]; o["nota"] = nota or o.get("nota"); o["actualizado"] = now()
    e["siguientes_acciones"] = _siguientes(e); guardar(e); log("OBJETIVO", accion=accion, id=o["id"], titulo=o["titulo"], estado=o["estado"]); return o


def conexion(nombre, estado_, evidencia, real):
    """Registra una conexión con su estado y evidencia. `real` = True solo si hubo llamada real verificada."""
    e = estado(); e["conexiones"] = [c for c in e["conexiones"] if c["nombre"] != nombre]
    e["conexiones"].append({"nombre": nombre, "estado": estado_, "real": bool(real), "evidencia": evidencia, "t": now()}); guardar(e); log("CONEXION", nombre=nombre, estado=estado_, real=bool(real))


def limitacion(texto):
    e = estado()
    if texto not in e["limitaciones"]: e["limitaciones"].append(texto)
    guardar(e); log("LIMITACION", texto=texto)


def _siguientes(e):
    s = [f"{o['id']} [{o['prioridad']}] {o['titulo']}" + ("" if o.get("handler") else " (requiere a Claude/persona)") for o in sorted(e["objetivos"], key=lambda o: o["prioridad"]) if o["estado"] in ("PENDIENTE", "EN_CURSO")]
    s += [f"{i['id']} {i['suite']}: {i['estado']} tras {i['intentos_acumulados']} intentos" for i in e["incidencias"] if i["estado"] in ("ABIERTA", "BLOQUEADA")]
    return s


# ---------------------------------------------------------------- ciclo --------------------------------------------------------------------------------
def _lock():
    if os.path.exists(F_LOCK) and time.time() - os.path.getmtime(F_LOCK) < 1800: return False
    os.makedirs(AUT, exist_ok=True); open(F_LOCK, "w").write(str(os.getpid())); return True


def ciclo():
    """Un ciclo acotado: guardia -> bloqueo -> objetivo pendiente con manejador -> ejecución -> registro. Devuelve el resumen (también persistido)."""
    ok, motivo = guardia()
    if not ok: log("CICLO_BLOQUEADO", motivo=motivo); return {"ejecutado": False, "motivo": motivo}
    if not _lock(): return {"ejecutado": False, "motivo": "Otro ciclo está en curso (candado vivo < 30 min)"}
    try:
        e = estado(); ts = time.time(); sec = escaneo()
        if sec:
            parar("Escaneo de secretos: %d hallazgos (%s)" % (len(sec), ", ".join(h["archivo"] for h in sec[:3]))); return {"ejecutado": False, "motivo": "PARADA: posibles secretos", "hallazgos": sec}
        for o in e["objetivos"]:  # objetivos recurrentes: vuelven a PENDIENTE cuando pasan `cada_horas` desde la última vez
            if o.get("cada_horas") and o["estado"] == "HECHO" and time.time() - time.mktime(time.strptime(o["actualizado"], "%Y-%m-%dT%H:%M:%SZ")) + time.timezone >= o["cada_horas"] * 3600:
                o["estado"] = "PENDIENTE"; log("OBJETIVO_REABIERTO", id=o["id"])
        cand = sorted([o for o in e["objetivos"] if o["estado"] == "PENDIENTE" and o.get("handler")], key=lambda o: o["prioridad"])
        res = {"ejecutado": True, "objetivo": None, "resultado": None}
        if cand:
            o = cand[0]; res["objetivo"] = o["id"]; o["estado"] = "EN_CURSO"; guardar(e); log("OBJETIVO_INICIO", id=o["id"])
            h = {"qa": lambda: qa(), "informe": lambda: {"informe": informe()}, "respaldo": lambda: respaldo(), "escaneo": lambda: {"hallazgos": escaneo()}}.get(o["handler"])
            r = h() if h else {"error": "manejador desconocido: %s" % o["handler"]}
            e = estado(); o = next(x for x in e["objetivos"] if x["id"] == o["id"]); bien = not r.get("error") and not r.get("fallan")
            o["estado"] = "HECHO" if bien else "PENDIENTE"; o["actualizado"] = now(); o["nota"] = "ciclo: " + json.dumps(r, ensure_ascii=False)[:300]; res["resultado"] = r
            e["fallos_consecutivos"] = 0 if bien else e["fallos_consecutivos"] + 1
        else:
            res["resultado"] = "Sin objetivos automáticos pendientes: ver siguientes_acciones"
        e["ciclos"] = (e["ciclos"] + [{"ts": ts, "t": now(), "objetivo": res["objetivo"]}])[-200:]; e["ejecuciones"] = (e["ejecuciones"] + [{"t": now(), "objetivo": res["objetivo"], "segundos": round(time.time() - ts, 1)}])[-100:]
        e["siguientes_acciones"] = _siguientes(e); guardar(e); log("CICLO", objetivo=res["objetivo"]); return res
    finally:
        try: os.remove(F_LOCK)
        except OSError: pass


def respaldo():
    """Copia de seguridad local verificable (ZIP sin claves ni bases de datos). No sube nada: la subida la hace quien tenga el conector."""
    import zipfile
    sec = escaneo()
    if sec: return {"error": "hay posibles secretos; no se empaqueta", "hallazgos": sec}
    out = os.path.join(os.path.dirname(ROOT), "respaldo_%s.zip" % time.strftime("%Y%m%d_%H%M%S", time.gmtime())); n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for r, ds, fs in os.walk(ROOT):
            ds[:] = [d for d in ds if d not in {".git", "__pycache__"}]
            for f in fs:
                if f.endswith((".env", ".db", ".pyc")) or f in ("PARAR", "ciclo.lock"): continue
                z.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), os.path.dirname(ROOT))); n += 1
    h = hashlib.sha256(open(out, "rb").read()).hexdigest(); log("RESPALDO", archivo=os.path.basename(out), sha256=h, ficheros=n)
    return {"archivo": out, "sha256": h, "ficheros": n, "bytes": os.path.getsize(out)}


def informe(destino=None):
    e = estado(); L = limites(); p = e.get("pruebas") or {}; v = verificar()
    md = ["# INFORME DE ENTREGA — Amazon Pro Intelligence (coordinador autónomo)", "", "Generado: %s · Registro íntegro: **%s** (%s líneas)" % (now(), "SÍ" if v["ok"] else "NO", v.get("lineas", "?")), "",
          "## 1. Pruebas", "", "| Suite | Clase | Estado | Intentos | Resultado |", "|---|---|---|---|---|"]
    for r in p.get("resultados", []): md.append("| %s | %s | %s | %s | %s |" % (r["suite"], r["clase"], r["estado"], r["intentos"], r["resultado"].replace("|", "/")))
    md += ["", "Resumen: %s pasan · %s intermitentes · %s fallan · %s total. **MOCK = proveedores simulados, no integraciones reales.**" % (p.get("pasan", 0), p.get("intermitentes", 0), p.get("fallan", 0), p.get("total", 0)), "",
           "## 2. Conexiones (solo cuenta como verificada la que tiene llamada real y evidencia)", "", "| Conexión | Estado | Real | Evidencia |", "|---|---|---|---|"]
    for c in e["conexiones"]: md.append("| %s | %s | %s | %s |" % (c["nombre"], c["estado"], "SÍ" if c["real"] else "no", c["evidencia"].replace("|", "/")))
    md += ["", "## 3. Incidencias", ""] + (["- %s · %s · %s · %s intentos · tipo %s" % (i["id"], i["suite"], i["estado"], i["intentos_acumulados"], i["tipo"]) for i in e["incidencias"]] or ["- ninguna"])
    md += ["", "## 4. Objetivos", ""] + ["- [%s] %s %s" % (o["estado"], o["id"], o["titulo"]) for o in e["objetivos"]]
    md += ["", "## 5. Siguientes acciones", ""] + ["- " + s for s in e["siguientes_acciones"]] if e["siguientes_acciones"] else ["", "## 5. Siguientes acciones", "", "- ninguna pendiente"]
    md += ["", "## 6. Límites de gasto y parada", "", "- Presupuesto € / tokens Keepa / llamadas IA: **%s / %s / %s** (0 = bloqueado)" % (L["presupuesto_eur"], L["keepa_tokens_max"], L["llamadas_ia_max"]),
           "- Máx. ciclos/24 h: %s · Máx. fallos seguidos: %s · Máx. intentos por incidencia: %s" % (L["max_ciclos_24h"], L["max_fallos_consecutivos"], L["max_intentos_incidencia"]), "- Parada: %s" % ("**ACTIVA**" if os.path.exists(F_STOP) else "no activa"),
           "", "## 7. Limitaciones declaradas", ""] + ["- " + x for x in e["limitaciones"]]
    txt = "\n".join(md) + "\n"; destino = destino or os.path.join(ROOT, "INFORME_ENTREGA.md")
    with open(destino, "w", encoding="utf-8") as f: f.write(txt)
    log("INFORME", archivo=os.path.basename(destino)); return destino


def main(argv=None):
    a = (argv if argv is not None else sys.argv)[1:]; c = a[0] if a else "estado"; out = None
    if c == "init":
        e = estado(); guardar(e); _write(F_LIM, _read(F_LIM, {k: v for k, v in LIMITES.items()})); log("INIT"); out = {"ok": True, "dir": AUT}
    elif c == "estado": e = estado(); out = {k: e[k] for k in ("objetivos", "incidencias", "siguientes_acciones", "conexiones", "pruebas", "fallos_consecutivos")}; out["guardia"] = guardia()
    elif c == "ciclo": out = ciclo()
    elif c == "qa": out = qa()
    elif c == "objetivo":
        out = objetivo(a[1], titulo=a[2] if a[1] == "add" else None, oid=a[2] if a[1] != "add" else None, handler=(a[3] if len(a) > 3 and a[1] == "add" and a[3] != "-" else None), prio=int(a[4]) if len(a) > 4 and a[1] == "add" else 5, cada_horas=float(a[5]) if len(a) > 5 and a[1] == "add" else None)
    elif c == "conexion": conexion(a[1], a[2], a[3], a[4].lower() in ("1", "si", "sí", "real", "true")); out = {"ok": True}
    elif c == "limitacion": limitacion(a[1]); out = {"ok": True}
    elif c == "escaneo": out = {"hallazgos": escaneo()}
    elif c == "informe": out = {"informe": informe()}
    elif c == "verificar": out = verificar()
    elif c == "parar": parar(a[1] if len(a) > 1 else "manual"); out = {"parado": True}
    elif c == "reanudar": reanudar(); out = {"reanudado": True}
    elif c == "respaldo": out = respaldo()
    else: print(__doc__); return 2
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str)); return 0


if __name__ == "__main__":
    sys.exit(main())
