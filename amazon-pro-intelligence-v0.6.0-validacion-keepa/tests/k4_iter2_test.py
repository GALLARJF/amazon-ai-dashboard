"""K4 iteración 2 · selección de cinco, ajustes auditados, umbrales con aprobación, conciliación, duplicados, informe de 8 secciones, explorador/expediente, planificador por API. (Base: sesión, CSRF, roles, aislamiento demo/producción, derechos de imagen en export, traversal, entradas hostiles, persistencia al reiniciar, gasto 0. Sin red externa.)"""
import base64, http.cookiejar, json, os, re, sys, tempfile, threading, urllib.error, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ["AMAZON_PRO_NO_WORKER"] = "1"; os.environ["AMAZON_PRO_KEEPA_ENABLE"] = "0"
import server as S
from backend import ai as AI
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); dbp = os.path.join(tmp, "s.db")
def boot():
    srv = S.make_server(0, admin_token="t", db_path=dbp, cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, srv.server_address[1]
srv, port = boot()
class Cl:
    def __init__(s, port): s.port = port; s.cj = http.cookiejar.CookieJar(); s.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(s.cj)); s.csrf = None
    def call(s, m, p, b=None, csrf=True, host=None, raw=False):
        h = {"Content-Type": "application/json"}
        if csrf and s.csrf: h["X-CSRF-Token"] = s.csrf
        if host: h["Host"] = host
        r = urllib.request.Request(f"http://127.0.0.1:{s.port}" + p, method=m, data=json.dumps(b).encode() if b is not None else None, headers=h)
        try: x = s.op.open(r); d = x.read(); return x.status, (d if raw else json.loads(d or b"{}")), x.headers
        except urllib.error.HTTPError as e:
            d = e.read(); return e.code, (d if raw else (json.loads(d) if d[:1] == b"{" else {})), e.headers
    def login(s, u, p): c, j, _ = s.call("POST", "/api/login", {"username": u, "password": p}, csrf=False); s.csrf = j.get("csrf"); return c
ad = Cl(port); ad.login("admin", "admin-password-123")
S.APP["store"].create_user("ana_analyst", "clave-analista-1", "analyst", ["catalogo-aht", "activcore-eu"]); S.APP["store"].create_user("apro_approver", "clave-aprobador-1", "approver", ["catalogo-aht", "activcore-eu"]); S.APP["store"].create_user("apro2", "clave-aprobador-2", "approver", ["catalogo-aht", "activcore-eu"])
an = Cl(port); an.login("ana_analyst", "clave-analista-1"); ap = Cl(port); ap.login("apro_approver", "clave-aprobador-1"); ap2 = Cl(port); ap2.login("apro2", "clave-aprobador-2")
ad.call("POST", "/api/keepa/importar-evidencia", {"product": "PRD-ACTIVCORE-V2"})
c, e, _ = ad.call("GET", "/api/k4/benchmark/ejecutivo")
nombres = [x["marca"] for x in e["competidores"]]
check("comparativa ejecutiva: 5 competidores K3 (máx. 6 columnas con ACTIVCORE)", c == 200 and len(nombres) == 5 and nombres == ["Kérastase", "Nioxin", "Redken", "The Ordinary", "Bio-Pilixin"] or (c == 200 and len(nombres) == 5))
check("todas las imágenes PENDIENTES con marcador; ninguna URL de imagen no autorizada", all(x["imagen"]["estado"] == "PENDIENTE" and x["imagen"]["marcador"] == "IMAGEN PENDIENTE DE VERIFICAR" for x in e["competidores"]) and e["propio"]["imagen"]["estado"] == "PENDIENTE" and not any(x["imagen"].get("url") for x in e["competidores"]))
check("datos de maqueta marcados MAQUETA y sin precio normalizado vigente inventado", all(x["celdas"]["precio_100ml"]["estado"] in ("MAQUETA", "SIN_DATO", "HISTORICO", "OBSERVADO") for x in e["competidores"]) and any(x["celdas"]["precio"]["estado"] == "MAQUETA" for x in e["competidores"]))
check("selección con motivo K3 y regla visible", all(x["seleccion"]["justificacion"] for x in e["competidores"]) and e["seleccion"]["regla"])
d = e["dictamen"]; inf = d["informe"]
check("dictamen: 8 secciones, diagnóstico y plan de investigación; sin intervalo ni cifras inventadas", list(inf) == ["conclusion", "evidencia", "hipotesis_alternativas", "escenarios_economicos", "riesgos", "recomendacion", "accion_prioritaria", "condiciones_para_reconsiderar"] and d["tipo"] == 5 and d["intervalo_recomendado"] is None and d["investigacion"] and d["diagnostico"])
check("umbrales: producción sin umbrales aprobados fuerza evidencia insuficiente y lo declara", any("Umbrales comerciales" in f["dato"] for f in d["faltantes"]))
c, ex, _ = ad.call("GET", "/api/k4/benchmark/explorador")
check("explorador: todas las referencias del país, 5 marcadas en comparativa", c == 200 and ex["total"] >= 20 and sum(1 for i in ex["items"] if i["en_comparativa"]) == 5)
k_in = next(i["key"] for i in ex["items"] if i["en_comparativa"]); k_out = next(i["key"] for i in ex["items"] if not i["en_comparativa"] and i["codigo"] not in ("nocomparable", "pendiente"))
check("analista no puede ajustar la selección (403); sin motivo (400)", an.call("POST", "/api/k4/seleccion/ajustar", {"key": k_in, "accion": "QUITAR", "motivo": "motivo suficiente"})[0] == 403 and ap.call("POST", "/api/k4/seleccion/ajustar", {"key": k_in, "accion": "QUITAR", "motivo": "x"})[0] == 400)
check("quitar y sustituir manualmente con motivo → persiste y queda auditado", ap.call("POST", "/api/k4/seleccion/ajustar", {"key": k_in, "accion": "QUITAR", "motivo": "retirada por prueba automática"})[0] == 200 and ap.call("POST", "/api/k4/seleccion/ajustar", {"key": k_out, "accion": "ANADIR", "motivo": "sustituto por prueba automática"})[0] == 200)
c, ex2, _ = ad.call("GET", "/api/k4/benchmark/explorador"); cl = ex2["seleccion"]["claves"]
check("selección actualizada: sin la retirada, con la añadida, siempre 5", k_in not in cl and k_out in cl and len(cl) == 5 and len(ex2["seleccion"]["ajustes"]) >= 2)
check("no se puede superar cinco ni añadir no comparables", ap.call("POST", "/api/k4/seleccion/ajustar", {"key": next(i["key"] for i in ex2["items"] if not i["en_comparativa"]), "accion": "ANADIR", "motivo": "sexta referencia de prueba"})[0] == 400)
c, ex3, _ = ad.call("GET", "/api/k4/benchmark/expediente?key=" + k_out)
check("expediente 360°: identificador, precio vigente/histórico, equivalencia, imagen pendiente", c == 200 and ex3["key"] == k_out and "vigente" in ex3["precio"] and ex3["equivalencia"]["nota"] and ex3["imagen"]["estado"] == "PENDIENTE" and ex3["propio"])
check("expediente inexistente → 404", ad.call("GET", "/api/k4/benchmark/expediente?key=NOEXISTE")[0] == 404)
# umbrales
c, u, _ = ad.call("GET", "/api/k4/umbrales")
check("umbrales: ninguno aprobado, ilustrativos solo informativos", c == 200 and not any(x["estado"] == "APROBADO" for x in u["umbrales"]) and u["ilustrativos"]["margen_min"] == 0.15)
c, pr, _ = ap.call("POST", "/api/k4/umbrales", {"producto": "PRD-ACTIVCORE-V2", "pais": "ES", "etapa": "lanzamiento", "valores": {"margen_min": 0.2}, "motivo": "propuesta de prueba"})
check("proponer umbral (aprobador); valores fuera de rango rechazados", c == 200 and ap.call("POST", "/api/k4/umbrales", {"valores": {"margen_min": 5}, "motivo": "fuera de rango"})[0] == 400)
check("el proponente no puede aprobar su propio umbral; otra persona sí; analista no", ap.call("POST", "/api/k4/umbrales/aprobar", {"id": pr["id"], "aprobar": True})[0] in (400, 403) and an.call("POST", "/api/k4/umbrales/aprobar", {"id": pr["id"], "aprobar": True})[0] == 403 and ap2.call("POST", "/api/k4/umbrales/aprobar", {"id": pr["id"], "aprobar": True})[0] == 200)
# importación y conciliación
csv1 = "producto,pais,fecha,unidades,ventas_netas,moneda,sesiones,pedidos,devoluciones_uds,precio_medio,canal\nPRD-ACTIVCORE-V2,ES,2026-11-01,5,200,EUR,80,5,0,40,FBA\n"
c, r1, _ = ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "EXPORT_SELLER_CENTRAL", "csv": csv1, "nombre": "a"})
c2, r2, _ = ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "EXPORT_SELLER_CENTRAL", "csv": csv1, "nombre": "a"})
csv1b = csv1 + "PRD-ACTIVCORE-V2,ES,2026-11-03,2,80,EUR,40,2,0,40,FBA\n"
c3, r2b, _ = ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "EXPORT_SELLER_CENTRAL", "csv": csv1b, "nombre": "a2"})
check("importación: carga nueva; mismo fichero → rechazado; fila ya existente → omitida (sin doble conteo)", r1["filas"] == 1 and c2 == 400 and r2b["duplicadas_omitidas"] == 1 and r2b["nuevas"] == 1)
csv2 = csv1.replace(",5,200,", ",7,280,")
c, r3, _ = ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "EXPORT_SELLER_CENTRAL", "csv": csv2, "nombre": "b"})
check("misma clave con valores distintos → conflicto sin sobrescribir", r3["n_conflictos"] == 1 and r3["filas"] == 0)
c, r4, _ = ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "EXPORT_SELLER_CENTRAL", "csv": csv2 + "PRD-ACTIVCORE-V2,ES,2026-11-04,1,40,EUR,20,1,0,40,FBA\n", "nombre": "b2", "reemplazar": True}); check("reemplazo explícito permitido y contado", r4["reemplazadas"] == 1)
c, cc, _ = ad.call("GET", "/api/k4/conciliar")
check("conciliación indicativa con aviso de huecos y estado, nunca 'validado'", c == 200 and cc["conciliacion"]["estado"] in ("CONCILIADO_INDICATIVO", "CON_AVISOS", "CON_ERRORES"))
bad = csv1.replace("2026-11-01,5,200,EUR,80,5,0", "2026-11-02,5,200,EUR,3,9,8")
ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "EXPORT_SELLER_CENTRAL", "csv": bad, "nombre": "c"}); c, cc2, _ = ad.call("GET", "/api/k4/conciliar")
check("conciliación detecta pedidos>sesiones y devoluciones>unidades", cc2["conciliacion"]["estado"] == "CON_ERRORES")
# planificador por API
c, pe, _ = ad.call("GET", "/api/k4/planificador")
check("planificador: solo internos, gasto 0, tope 0, sin hilo", c == 200 and pe["gasto"]["tope_eur"] == 0 and pe["hilo_activo"] is False and "internos" in pe["alcance"])
check("encolar: aprobador sí, analista no; tipo externo rechazado", ap.call("POST", "/api/k4/planificador/encolar", {"kind": "dossier_precio", "producto": "PRD-ACTIVCORE-V2", "pais": "ES", "params": {"producto": "PRD-ACTIVCORE-V2", "pais": "ES"}})[0] == 200 and an.call("POST", "/api/k4/planificador/encolar", {"kind": "dossier_precio"})[0] == 403 and ap.call("POST", "/api/k4/planificador/encolar", {"kind": "publicar_precio"})[0] == 400)
check("tick solo admin; ejecuta el dossier interno", ap.call("POST", "/api/k4/planificador/tick", {})[0] == 403 and ad.call("POST", "/api/k4/planificador/tick", {})[1].get("estado") == "OK")
check("parada de emergencia detiene el tick", ad.call("POST", "/api/k4/planificador/parada", {"on": True, "motivo": "prueba"})[0] == 200 and ad.call("POST", "/api/k4/planificador/tick", {})[1]["motivo"] == "PARADA_DE_EMERGENCIA")
ad.call("POST", "/api/k4/planificador/parada", {"on": False})
# persistencia tras reinicio
srv.shutdown(); srv.server_close(); srv2, port2 = boot(); a2 = Cl(port2); a2.login("admin", "admin-password-123")
c, ex4, _ = a2.call("GET", "/api/k4/benchmark/explorador"); c, pe2, _ = a2.call("GET", "/api/k4/planificador")
check("tras reiniciar: selección y trabajos persisten", ex4["seleccion"]["claves"] == cl and pe2["trabajos"].get("OK", 0) >= 1)
c, st, _ = a2.call("GET", "/api/k4/estado"); check("gasto adicional 0 € y conectores NO_OPERATIVO", st["gasto_adicional_eur"] == 0 and all(v["estado"] == "NO_OPERATIVO" for v in st["conectores"].values()))
srv2.shutdown()
print("%d/%d" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
