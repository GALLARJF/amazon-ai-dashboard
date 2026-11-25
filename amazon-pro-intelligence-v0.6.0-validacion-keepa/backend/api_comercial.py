"""V1.1 — rutas /api/v08/*: motor económico comercial y lectura de Ads. GET de cálculo puro (el viewer puede usarlas); la única escritura es la importación ADMIN de un informe CSV
descargado por una persona (almacén local; nunca escribe en Amazon). Sin red, sin gasto, sin secretos."""
import hashlib, time, re
from . import comercial as CM, ads_lectura as AL, activcore as AC
from .catalog import ACCOUNT_ID


def _f(q, k, default=None, lo=0.0, hi=1e9):
    v = (q.get(k) or [None])[0]
    if v in (None, ""): return default
    try: x = float(v.replace(",", "."))
    except ValueError: raise ValueError(k + ": número inválido")
    if not lo <= x <= hi: raise ValueError("%s: entre %s y %s" % (k, lo, hi))
    return x


def _ov(q):
    """Parámetros simulados por la petición: ov.<nombre>=valor. Se marcan como simulados en la respuesta."""
    out = {}
    for k, v in q.items():
        if k.startswith("ov."):
            n = k[3:]
            out[n] = v[0] if n == "ventas_ads_base" else _f({k: v}, k, None, 0, 100000)
    return out


def _reports(APP):
    st = APP["store"]
    with st.lock:
        rows = st.db.execute("SELECT id FROM records WHERE account_id=? AND kind='dataset' AND key LIKE 'adsterm:%'", (ACCOUNT_ID,)).fetchall()
    out = []
    for r in rows:
        d = st.get(ACCOUNT_ID, r["id"])["data"]; out.append(d)
    return sorted(out, key=lambda x: x["imported_at"], reverse=True)


def handle(APP, s, method, path, q, b):
    if not APP["store"].can_access(s, ACCOUNT_ID): raise PermissionError("sin acceso al catálogo")
    p = path[len("/api/v08/"):]
    if method == "POST":
        if s.get("viewer"): raise PermissionError("solo lectura (viewer)")
        if p != "ads/importar": raise LookupError(p)
        if s["role"] != "admin": raise PermissionError("solo el administrador importa informes")
        import base64
        try: raw = base64.b64decode(str((b or {}).get("content_b64") or ""), validate=True)
        except Exception: raise ValueError("content_b64 inválido")
        filas = AL.parse(raw); digest = hashlib.sha256(raw).hexdigest(); key = "adsterm:" + digest[:16]
        if AC._find(APP["store"], "dataset", key, ACCOUNT_ID): raise ValueError("este informe ya fue importado (mismo contenido)")
        d = {"type": "ads_terminos", "id": digest[:16], "sha256": digest, "filename": str((b or {}).get("filename") or "informe.csv")[:120], "bytes": len(raw), "filas": filas,
             "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "imported_by": s["username"], "class": "IMPORTADO",
             "provenance": "Informe de Amazon Ads descargado por una persona e importado SIN MODIFICAR (hash conservado). No es una conexión API. Nunca se mezcla con datos DEMO."}
        AC._upsert(APP["store"], "dataset", key, d, s["username"], ACCOUNT_ID)
        return {k: v for k, v in d.items() if k != "filas"} | {"n_filas": len(filas)}
    if method != "GET": raise LookupError(p)
    if p == "comercial/parametros":
        return {"parametros": CM.parametros(), "regla": "ningún parámetro está «verificado» sin evidencia oficial; estimado = comunicado por la auditoría; pendiente = por confirmar"}
    if p == "comercial/economia":
        inc = None
        e = CM.economia_unitaria((q.get("canal") or ["FBA"])[0].upper(), int(_f(q, "lote", 1, 1, 2)), _f(q, "pvp", None, 0.5, 5000), _f(q, "ventas", 300, 1, 1e6), _f(q, "dias", 90, 1, 3650),
                                 _f(q, "tacos", None, 0, 1), _f(q, "descuento", 0.0, 0, 0.9), inc, _f(q, "regulacion_aparte", 0.0, 0, 1000), _f(q, "muestras", 0.0, 0, 1e7), _f(q, "fijos", None, 0, 1e7), _ov(q))
        return {"economia": e, "objetivos": CM.objetivos(e)}
    if p == "comercial/simulador":
        return CM.simulador(dias=int(_f(q, "dias", 90, 1, 3650)), overrides=_ov(q))
    if p == "comercial/tesoreria":
        return CM.tesoreria(_f(q, "compradas", 550, 1, 1e7), int(_f(q, "lote", 1, 1, 2)), _f(q, "vendidas", 100, 0, 1e7), _f(q, "tacos", 0.0, 0, 1), (q.get("canal") or ["FBA"])[0].upper(), _f(q, "pvp", None, 0.5, 5000), _f(q, "dias", 90, 1, 3650), _ov(q))
    if p == "comercial/piloto":
        return CM.piloto(int(_f(q, "ventas", 100, 1, 100)), int(_f(q, "dias", 90, 1, 3650)), _ov(q))
    if p == "comercial/presupuesto":
        t = int(_f(q, "tramo", -1, -1, 3)); r = CM.presupuesto_escalonado()
        if t >= 0:
            r["evaluacion"] = CM.evaluar_escalado(t, (q.get("aprobacion") or [""])[0] == "1", {"contribucion_tras_ads_ud": _f(q, "contribucion"), "ventas_atribuidas": _f(q, "ventas_atribuidas")})
        return r
    if p == "comercial/alertas":
        return {"alertas": CM.alertas(_f(q, "gasto"), _f(q, "tramo_importe"), _f(q, "contribucion"), _f(q, "stock"), _f(q, "demanda_diaria"), _f(q, "plazo_reposicion"), None, _f(q, "dias_ultimo_clic"), _f(q, "ventana"))}
    if p == "comercial/checklist":
        return {"checklist": CM.checklist(), "sincronizado_con": "GALLARJF/activcore-launch-control (PR #1)"}
    if p == "comercial/ads":
        reps = _reports(APP)
        if not reps: return {"estado": "SIN DATOS", "mensaje": "No hay informes de términos de búsqueda importados. No se muestran datos de demostración.", "informes": []}
        rid = (q.get("report") or [None])[0]; rep = next((r for r in reps if r["id"] == rid), reps[0])
        m = AL.metricas(rep["filas"], _f(q, "ventas_totales"))
        rec = AL.recomendaciones(rep["filas"], _f(q, "acos_objetivo", None, 0, 1), _f(q, "cpc_actual"), _f(q, "dias_desde_fin", None, 0, 3650), _f(q, "ventana", None, 0, 60), _f(q, "min_clics", None, 1, 10000))
        if (q.get("fmt") or [""])[0] == "csv":
            return ("raw", AL.exportacion_csv(rec["recomendaciones"]).encode(), "text/csv; charset=utf-8", {"Content-Disposition": "attachment; filename=propuestas_ads.csv"})
        return {"estado": "DATOS IMPORTADOS", "clase": "IMPORTADO", "informe": {k: v for k, v in rep.items() if k != "filas"}, "metricas": m, **rec, "informes": [r["id"] for r in reps]}
    raise LookupError(p)
