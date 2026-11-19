"""K4 · API HTTP real: sesión, CSRF, roles, aislamiento demo/producción, derechos de imagen en export, traversal, entradas hostiles, persistencia al reiniciar, gasto 0. Sin red externa."""
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
ad = Cl(port); check("login admin", ad.login("admin", "admin-password-123") == 200)
S.APP["store"].create_user("ana_analyst", "clave-analista-1", "analyst", ["catalogo-aht", "activcore-eu"]); S.APP["store"].create_user("apro_approver", "clave-aprobador-1", "approver", ["catalogo-aht", "activcore-eu"])
an = Cl(port); an.login("ana_analyst", "clave-analista-1"); ap = Cl(port); ap.login("apro_approver", "clave-aprobador-1"); anon = Cl(port)
check("sin sesión: 401 en todas las rutas K4", all(anon.call("GET", "/api/k4/" + p)[0] == 401 for p in ("estado", "centro", "dictamen", "benchmark", "costes", "export?fmt=pdf")))
c, j, _ = ad.call("GET", "/api/k4/estado")
check("estado: gasto adicional 0 €, IA externa desactivada, conectores NO_OPERATIVO, autonomía NO VERIFICADA", c == 200 and j["gasto_adicional_eur"] == 0 and "DESACTIVADA" in j["capacidades"]["ia_externa"] and all(v["estado"] == "NO_OPERATIVO" for v in j["conectores"].values()) and j["capacidades"]["autonomia_verificada"]["estado"] == "NO VERIFICADA")
c, j, _ = ad.call("GET", "/api/k4/centro")
check("centro de mando: KPIs SIN_DATO (no 0), dictamen 5, faltantes y costes pendientes", c == 200 and j["kpis"]["unidades"]["estado"] == "SIN_DATO" and j["kpis"]["unidades"]["valor"] is None and j["dictamen"]["tipo"] == 5 and j["faltantes"] and j["costes_pendientes"] >= 5)
c, j, _ = ad.call("GET", "/api/k4/dictamen"); d = j["dictamen"]
check("dictamen de ACTIVCORE hoy = EVIDENCIA INSUFICIENTE con trazabilidad, PVP como propuesta y sin intervalo", c == 200 and d["tipo"] == 5 and d["errores_contrato"] == [] and d["intervalo_recomendado"] is None and "PROPUESTA" in d["precio_actual"]["nota"] and d["trazabilidad"])
check("filtros globales validados (país, canal, fechas, entorno, pvp)", all(ad.call("GET", "/api/k4/kpis?" + q)[0] == 400 for q in ("pais=XX", "canal=ZZZ", "desde=ayer", "hasta=2026-13-45")) and ad.call("GET", "/api/k4/dictamen?entorno=X")[0] == 400 and ad.call("GET", "/api/k4/dictamen?pvp=-5")[0] == 400 and ad.call("GET", "/api/k4/kpis?pais=DE&canal=FBA&desde=2026-01-01")[0] == 200)
check("producto inexistente → 400/404, no 500", ad.call("GET", "/api/k4/kpis?producto=PRD-NOEXISTE")[0] in (200, 400, 404) and ad.call("GET", "/api/k4/dictamen?producto=PRD-NOEXISTE")[0] in (400, 404))
c, j, _ = ad.call("GET", "/api/k4/benchmark")
check("benchmark: 5 referencias con imagen PENDIENTE y marcador; ninguna imagen sin verificar", c == 200 and len(j["items"]) >= 1 and all(i["imagen"]["estado"] == "PENDIENTE" and i["imagen"]["marcador"] == "IMAGEN PENDIENTE DE VERIFICAR" and i["imagen"]["falta"] for i in j["items"]) and j["propio"]["imagen"]["estado"] == "PENDIENTE")
asin = next((i["asin"] for i in j["items"] if i["asin"]), None)
# roles y CSRF
check("analista no puede importar, validar costes, registrar medios ni proponer (403)", all(an.call("POST", "/api/k4/" + p, b)[0] == 403 for p, b in (("importar", {"tipo": "sales", "csv": "x"}), ("costes", {}), ("costes/validar", {"id": 1, "estado": "VALIDADO"}), ("medios", {}), ("medios/verificar", {}), ("dossier/proponer", {"id": "x"}))))
check("POST sin CSRF → 403", ap.call("POST", "/api/k4/importar", {"tipo": "sales", "csv": "x"}, csrf=False)[0] == 403)
check("solo admin carga la demo sintética", ap.call("POST", "/api/k4/demo/cargar", {})[0] == 403)
# importación de producción
csv_ = "producto,pais,fecha,unidades,ventas_netas,moneda,sesiones,pedidos,precio_medio,canal\nPRD-ACTIVCORE-V2,ES,2026-11-01,5,200,EUR,80,5,48,FBA\n"
c, j, _ = ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "EXPORT_SELLER_CENTRAL", "csv": csv_, "nombre": "t"}); check("aprobador importa CSV documentado", c == 200 and j["filas"] == 1)
check("importar sintético en producción → 400", ap.call("POST", "/api/k4/importar", {"tipo": "sales", "origen": "SINTETICO", "csv": csv_})[0] == 400)
c, j, _ = ad.call("GET", "/api/k4/kpis?pais=ES"); check("KPI de producción refleja solo lo importado", j["kpis"]["unidades"]["valor"] == 5 and j["kpis"]["unidades"]["entorno"] == "PRODUCCION")
c, j, _ = ad.call("POST", "/api/k4/demo/cargar", {}); check("admin carga demo sintética (entorno SINTETICO_DEMO)", c == 200 and j["ventas"] == 28)
c, j, _ = ad.call("GET", "/api/k4/kpis?pais=ES"); check("la demo NO contamina producción (sigue 5 uds)", j["kpis"]["unidades"]["valor"] == 5)
c, j, _ = ad.call("GET", "/api/k4/dictamen?entorno=SINTETICO_DEMO"); check("dictamen demo etiquetado como SINTÉTICO y confiable solo como ejemplo", c == 200 and j["dictamen"]["entorno"] == "SINTETICO_DEMO" and "SINTÉTICOS" in j["aviso_entorno"] and j["dictamen"]["tipo"] in (1, 2, 3, 4))
c, j, _ = ad.call("GET", "/api/k4/dictamen"); check("dictamen de producción sigue sin usar datos sintéticos", j["dictamen"]["tipo"] == 5 or j["dictamen"]["entorno"] == "PRODUCCION")
# costes
c, j, _ = ad.call("GET", "/api/k4/costes"); cg = next(x for x in j["ficha"] if x["concepto"] == "cogs"); check("ficha: 10,03 € pendiente de validar con aviso de alcance", cg["valor"] == 10.03 and cg["estado"] == "PENDIENTE_VALIDAR" and "10,03" in j["nota"])
check("duplicación: total sin incluye → 400", ap.call("POST", "/api/k4/costes", {"producto": "PRD-ACTIVCORE-V2", "concepto": "cogs", "valor": 11, "unidad": "EUR/ud", "moneda": "EUR", "fuente": "f", "fecha": "2026-11-19", "es_total": True})[0] == 400)
# medios y derechos en exportación
png = base64.b64encode(b"\x89PNG" + b"0" * 40).decode()
c, j, _ = ap.call("POST", "/api/k4/medios", {"product_id": "PRD-ACTIVCORE-V2", "variante": "principal", "asin": None, "origen": "FOTO_PROPIA_AHT", "fuente": "AHT", "fecha_captura": "2026-11-19", "mime": "image/png", "contenido_b64": png}); mid = j.get("id"); check("registrar imagen propia: queda PENDIENTE sin derechos", c == 200 and j["estado"] == "PENDIENTE")
c, j, _ = ad.call("GET", "/api/k4/medios/resolver?producto=PRD-ACTIVCORE-V2&variante=principal"); check("antes de verificar: marcador pendiente", j["estado"] == "PENDIENTE")
check("el archivo no se sirve sin verificar (404)", ad.call("GET", f"/api/k4/medios/{mid}/file")[0] == 404)
check("verificar sin permiso → 400", ap.call("POST", "/api/k4/medios/verificar", {"id": mid, "estado": "VERIFICADA", "derechos": {"visualizar": True}, "permiso": ""})[0] == 400)
ap.call("POST", "/api/k4/medios/verificar", {"id": mid, "estado": "VERIFICADA", "derechos": {"visualizar": True}, "permiso": "foto propia AHT, acta 2026-11-19"})
c, j, _ = ad.call("GET", "/api/k4/medios/resolver?producto=PRD-ACTIVCORE-V2&variante=principal"); check("tras verificar con derecho de visualizar: se resuelve", j["estado"] == "VERIFICADA" and j["url"].endswith("/file"))
c, raw, h = ad.call("GET", f"/api/k4/medios/{mid}/file", raw=True); check("archivo servido con nosniff, no-store y CSP restrictiva", c == 200 and raw.startswith(b"\x89PNG") and h["X-Content-Type-Options"] == "nosniff" and "no-store" in h["Cache-Control"])
c, j, _ = ad.call("GET", "/api/k4/medios/resolver?producto=PRD-ACTIVCORE-V2&variante=principal&op=exportar"); check("sin derecho de exportar → pendiente indicando «exportar»", j["estado"] == "PENDIENTE" and "exportar" in j["falta"])
c, svg, _ = ad.call("GET", "/api/k4/export?fmt=svg", raw=True); check("SVG exportado NO incluye la imagen (sin derecho de exportación) y marca pendientes", c == 200 and b"<image" not in svg and b"IMAGEN PENDIENTE" in svg)
ap.call("POST", "/api/k4/medios/verificar", {"id": mid, "estado": "VERIFICADA", "derechos": {"visualizar": True, "almacenar": True, "exportar": True}, "permiso": "foto propia AHT, acta 2026-11-19"})
c, j, _ = ad.call("GET", "/api/k4/benchmark"); check("el producto propio muestra su imagen verificada", j["propio"]["imagen"]["estado"] == "VERIFICADA")
check("traversal / ids hostiles en medios → 404/400", all(ad.call("GET", "/api/k4/medios/" + x + "/file")[0] in (400, 404) for x in ("../../etc/passwd", "MED-x%00", "..%2f..%2fsecret")))
check("mime/contenido falsificado se rechaza", ap.call("POST", "/api/k4/medios", {"product_id": "P", "variante": "v", "origen": "FOTO_PROPIA_AHT", "fuente": "x", "fecha_captura": "2026-11-19", "mime": "image/png", "contenido_b64": base64.b64encode(b"<svg onload=alert(1)>").decode()})[0] == 400 and ap.call("POST", "/api/k4/medios", {"product_id": "P", "variante": "v", "origen": "SCRAPING", "fuente": "x", "fecha_captura": "2026-11-19", "url_origen": "http://x"})[0] == 400)
c, pdf, h = ad.call("GET", "/api/k4/export?fmt=pdf", raw=True); check("PDF válido con fuentes y derechos; formato desconocido → 400", c == 200 and pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF") and ad.call("GET", "/api/k4/export?fmt=exe")[0] == 400)
# Director
c, j, _ = an.call("POST", "/api/k4/dossier", {"producto": "PRD-ACTIVCORE-V2", "pais": "ES"}); did = j["id"]; check("analista genera dossier (solo lectura/cálculo)", c == 200 and j["dictamen"]["tipo"] == 5 and j["como_obtenerlos"] and j["capacidad"].startswith("DETERMINISTA"))
check("proponer con dictamen 5 → 400 (no hay decisión de precio)", ap.call("POST", "/api/k4/dossier/proponer", {"id": did})[0] == 400)
c, j, _ = ad.call("POST", "/api/k4/nuevo-producto", {"titulo": "<script>x</script> Serum", "necesidad": "caída"}); check("nuevo producto: dossier NO_EVALUADO", c == 200 and j["dossier"]["estado_decision"] == "NO_EVALUADO")
c, j, _ = ad.call("GET", "/api/k4/dossiers"); check("listado de dossiers persistido", len(j["dossiers"]) >= 2)
# decision N3 a partir de un dossier demo (tipo 1-4)
c, jd, _ = ad.call("GET", "/api/k4/dictamen?entorno=SINTETICO_DEMO&pvp=70")
check("¿y si? PVP 70 en demo → dictamen distinto (3/4) con intervalo o causa", jd["dictamen"]["tipo"] in (3, 4))
# seguridad
check("Host ajeno → 403 en rutas K4", ad.call("GET", "/api/k4/estado", host="evil.example")[0] == 403)
check("cabeceras: CSP sin inline y nosniff en respuestas K4", (lambda h: "script-src 'self'" in h["Content-Security-Policy"] and h["X-Content-Type-Options"] == "nosniff")(ad.call("GET", "/api/k4/estado")[2]))
check("ruta K4 desconocida → 404", ad.call("GET", "/api/k4/inexistente")[0] == 404)
# persistencia
srv.shutdown(); srv.server_close(); srv2, port2 = boot(); ad2 = Cl(port2); ad2.login("admin", "admin-password-123")
c, j, _ = ad2.call("GET", "/api/k4/kpis?pais=ES"); c2, j2, _ = ad2.call("GET", "/api/k4/dossiers"); c3, j3, _ = ad2.call("GET", "/api/k4/medios")
check("persistencia tras reinicio: datos importados, dossiers y registro de medios", j["kpis"]["unidades"]["valor"] == 5 and len(j2["dossiers"]) >= 2 and any(m["estado"] == "VERIFICADA" for m in j3["registro"]))
ok, n, bad = S.APP["store"].verify_audit(); acts = {a["action"] for a in S.APP["store"].audit_list(limit=500)}
check("auditoría íntegra y con eventos K4 (import, coste, media, export, dossier)", ok and {"k4.import", "k4.media.alta", "k4.media.verificacion", "k4.export", "k4.dossier"} <= acts)
check("el código K4 no contiene llamadas de red ni de IA externa", not re.search(r"urllib|requests|http\.client|socket|openai|anthropic", "".join(open(os.path.join(ROOT, "backend", f), encoding="utf-8").read() for f in os.listdir(os.path.join(ROOT, "backend")) if f.startswith("k4_") or f == "api_k4.py"), re.I))
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
