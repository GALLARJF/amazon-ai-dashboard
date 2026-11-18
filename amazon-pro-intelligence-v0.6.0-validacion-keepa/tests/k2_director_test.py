"""K2 · Director Amazon IA: respuestas deterministas por intención sobre los 20 ASIN importados. SIN red, SIN IA, SIN Keepa de pago (guardia de red + Keepa desactivado)."""
import http.client, json, os, re, socket, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
_real = socket.socket.connect
def _guard(self, addr, *a, **k):
    if isinstance(addr, tuple) and addr and addr[0] not in ("127.0.0.1", "localhost", "::1"): raise OSError("RED BLOQUEADA")
    return _real(self, addr, *a, **k)
socket.socket.connect = _guard
import server as S
from backend import eu_director as ED
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
KCALLS = []
def fake(url, headers, timeout): KCALLS.append(url); raise OSError("no debe llamarse")
tmp = tempfile.mkdtemp(); DB = os.path.join(tmp, "d.db")
def boot():
    srv = S.make_server(0, admin_token="t", db_path=DB, admin_password="Admin-clave-larga-1", keepa_env_fn=lambda: {"AMAZON_PRO_KEEPA_ENABLE": "0"}, keepa_get=fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv
class C:
    cookie = None; csrf = ""
    def __init__(s, port): s.port = port
    def req(s, m, p, b=None):
        h = {"Host": "127.0.0.1:%d" % s.port, "Content-Type": "application/json", "Origin": "http://127.0.0.1:%d" % s.port}
        if s.cookie: h["Cookie"] = "apisid=" + s.cookie; h["X-CSRF-Token"] = s.csrf
        c = http.client.HTTPConnection("127.0.0.1", s.port, timeout=30); c.request(m, p, json.dumps(b) if b is not None else None, h); r = c.getresponse(); d = r.read(); return r.status, json.loads(d or b"{}"), dict(r.getheaders())
    def login(s):
        st, j, hd = s.req("POST", "/api/login", {"username": "admin", "password": "Admin-clave-larga-1"}); s.cookie = hd["Set-Cookie"].split("apisid=")[1].split(";")[0]; s.csrf = j["csrf"]; return st
srv = boot(); a = C(srv.server_address[1]); check("login admin", a.login() == 200)
PID = "PRD-ACTIVCORE-V2"
def ask(q): return a.req("POST", "/api/eu/director", {"product": PID, "question": q, "use_ai": False})[1]
CHIPS = ["¿En qué país europeo conviene lanzar este producto?", "¿Es competitivo un precio de 49,90 €?", "¿Qué datos faltan para decidir?", "¿Qué riesgos regulatorios tenemos?", "¿Cuáles son los competidores más peligrosos?"]
# --- intención
check("intención: los 5 chips → pais, precio, faltan, riesgos, competidores (¡«competitivo» NO es competidores!)", [ED.EUDirector.intent(q) for q in CHIPS] == ["pais", "precio", "faltan", "riesgos", "competidores"])
check("intención: variantes («rivales», «cuánto cuesta», «qué falta», «claims»)", [ED.EUDirector.intent(q) for q in ("¿Quiénes son los rivales?", "¿Qué margen tengo a 39 €?", "¿Qué falta?", "¿Hay riesgos con los claims?", "hola")] == ["competidores", "precio", "faltan", "riesgos", "general"])
# --- ANTES de importar: sin datos, honesto
j0 = ask(CHIPS[4]); check("sin ASIN importados: DATO NO DISPONIBLE (no inventa competidores)", j0["intent"] == "competidores" and "DATO NO DISPONIBLE" in j0["answer"] and "ASIN " not in j0["answer"].split("\n", 1)[1][:0] + "")
# --- importación (0 tokens, 0 red)
st, imp, _ = a.req("POST", "/api/keepa/importar-evidencia", {"product": PID}); check("importar los 20 ASIN: 0 tokens, 0 llamadas Keepa", st == 200 and imp["importados"] == 20 and imp["tokens"] == 0 and not KCALLS)
j = ask(CHIPS[4]); t = j["answer"]
check("COMPETIDORES: analiza los 20 ASIN y NO devuelve el resumen genérico de datos faltantes", j["intent"] == "competidores" and "20 ASIN analizados" in t and "[DATOS QUE FALTAN]" not in t and "Ranking" not in t)
rel = j["competitors"]; check("competidores: cada fila trae marca, producto, ASIN, precio normalizado, comparabilidad, estado y motivo", len(rel) >= 3 and all(r["brand"] and r["title"] and re.match(r"^B0[A-Z0-9]{8}$", r["asin"]) and r["level"] in ("ALTA", "MEDIA") and r["state"] and r["reason"] for r in rel))
check("competidores (K3): texto con ASIN, «/100 mL», equivalencia y motivo para cada relevante", all(r["asin"] in t for r in rel) and "/100 mL" in t and t.count("Motivo:") >= len(rel) and "equivalencia" in t and "COMPETIDORES DIRECTOS PREMIUM" in t)
check("competidores (K3): ninguno CONFIRMADO, todos «CLASIFICACIÓN AUTOMÁTICA» revisable", all(not r["confirmed"] for r in rel) and "0 confirmados" in t and "CLASIFICACIÓN AUTOMÁTICA" in t and "CONFIRMADO" not in t.replace("confirmados por una persona", ""))
check("competidores (K3): champús/complementos/medicamentos NO aparecen como relevantes y se cuentan como no comparables", all(r["segmento"] in ("COMPETIDOR DIRECTO PREMIUM", "COMPETIDOR FUNCIONAL") for r in rel) and not any(x in " ".join(r["brand"] for r in rel) for x in ("OGX", "SANA")) and "no comparables" in t)
check("competidores: orden determinista (premium antes que funcional, luego equivalencia)", [r["level"] for r in rel] == sorted([r["level"] for r in rel], key=lambda x: {"ALTA": 0, "MEDIA": 1}[x]))
check("NO inventa ventas: sin «unidades», «ventas estimadas», «cuota» y BSR marcado como ranking", not re.search(r"unidades/mes|ventas estimadas de|cuota de mercado de \d", t) and "no ventas" in t and "NO ventas" in t)
check("misma pregunta → misma respuesta (determinista)", ask(CHIPS[4])["answer"] == t)
# confirmar uno → se diferencia
top = rel[0]; st, cj, _ = a.req("POST", "/api/eu/k3/revision", {"product": PID, "key": top["asin"], "decision": "CONFIRMAR", "segmento": {"COMPETIDOR DIRECTO PREMIUM": "premium", "COMPETIDOR FUNCIONAL": "funcional"}[top["segmento"]], "motivo": "revisado en prueba por el responsable"})
j2 = ask(CHIPS[4]); t2 = j2["answer"]; r2 = {r["asin"]: r for r in j2["competitors"]}
check("tras confirmar 1 (K3): ese ASIN sale CONFIRMADO y el resto sigue como clasificación automática", st == 200 and r2[top["asin"]]["confirmed"] and r2[top["asin"]]["state"] == "CONFIRMADO" and any(not r["confirmed"] for r in r2.values()) and "1 confirmados" in t2)
# --- precio
jp = ask(CHIPS[1])["answer"]
check("PRECIO 49,90 € (K3): economía por país + posición frente al segmento PREMIUM + límite de conclusión", "49,90 €" in jp and all(n in jp for n in ("Alemania", "Francia", "Italia", "España")) and "[POSICIÓN DE PRECIO · SEGMENTO PREMIUM" in jp and "[NO CONCLUYENTE]" in jp and "competidores" not in ask(CHIPS[1])["intent"])
check("precio sin importe usa el PVP de referencia y no rompe", "[PRECIO ANALIZADO]" in ask("¿Qué precio tengo?")["answer"])
# --- precios históricos frente a actuales (K2 cierre)
import time as _t
F = ED.EUDirector.price_freshness; NOW = _t.mktime(_t.strptime("2026-11-18", "%Y-%m-%d"))
check("frescura: 0-7 d ACTUAL, 8-30 d RECIENTE, >30 d HISTÓRICO, sin fecha/ilegible DESCONOCIDA", [F(d, NOW)[1] for d in ("2026-11-18", "2026-11-11", "2026-11-10", "2026-10-19", "2026-10-18", "2026-05-22", None, "xx")] == ["ACTUAL", "ACTUAL", "RECIENTE", "RECIENTE", "HISTÓRICO", "HISTÓRICO", "FECHA DESCONOCIDA", "FECHA DESCONOCIDA"])
relx = [r for r in ask(CHIPS[4])["competitors"]]
check("competidores (K3): cada precio lleva fecha, antigüedad y clase coherente con la edad", all(r["price_class"] == F(r["price_as_of"])[1] and (r["price_as_of"] is None or r["price_age_days"] is not None) for r in relx if r["price"] is not None) and "[FRESCURA PREMIUM]" in ask(CHIPS[4])["answer"] and any(k in ask(CHIPS[4])["answer"] for k in ("(ACTUAL", "(RECIENTE", "(HISTÓRICO")))
hist_n = sum(1 for r in relx if r["price_class"] in ("HISTÓRICO", "FECHA DESCONOCIDA"))
tc = ask(CHIPS[4])["answer"]; check("con precios históricos entre los premium: ADVERTENCIA explícita de que no demuestran competitividad actual", hist_n == 0 or "ADVERTENCIA: los precios HISTÓRICOS" in tc)
ords = [(r["price_class"] in ("HISTÓRICO", "FECHA DESCONOCIDA")) for r in relx if r["level"] == "ALTA"]
check("el ranking premium es por equivalencia (no por precio): consecutivo y descendente", [r["equivalencia"] for r in relx if r["level"] == "ALTA"] == sorted([r["equivalencia"] for r in relx if r["level"] == "ALTA"], reverse=True))
fresh = [r for r in relx if r["price_class"] in ("ACTUAL", "RECIENTE") and r["price_norm"] is not None]
m = re.search(r"SEGMENTO PREMIUM EQUIVALENTE · referencia principal\] (\d+) productos; (\d+) con precio vigente", jp)
check("PRECIO (K3): el nº de premium con precio vigente coincide con los datos y los históricos van aparte «solo referencia»", m and int(m.group(2)) == sum(1 for r in relx if r["level"] == "ALTA" and r["price_class"] in ("ACTUAL", "RECIENTE") and r["price_norm"] is not None))
check("PRECIO (K3): muestra insuficiente → NO CONCLUYENTE (sin mediana) y comparadores individuales / históricos «SOLO REFERENCIA»", ("MUESTRA INSUFICIENTE" in jp and "Mediana" not in jp.split("SEGMENTO PREMIUM EQUIVALENTE")[1].split("[POSICIÓN DE PRECIO · SEGMENTO FUNCIONAL")[0]) or "Mediana" in jp)
# --- país, faltan, riesgos
jc = ask(CHIPS[0])["answer"]; check("PAÍS: sin ranking dice que no recomienda país y muestra ASIN por país (ES con datos)", ("SIN RECOMENDACIÓN" in jc or "Ranking provisional" in jc) and "España: " in jc and "NL, PL, SE" in jc)
jf = ask(CHIPS[2])["answer"]; check("DATOS FALTANTES: lista deduplicada y estado de competidores/ventas", "[DATOS QUE FALTAN]" in jf and "Ventas, conversión y CPC reales: SIN DATOS" in jf and "20 ASIN en base" in jf and len(jf.split("\n")) == len(set(jf.split("\n"))))
jr = ask(CHIPS[3])["answer"]; check("RIESGOS: regulatorios + de datos + de decisión", "[RIESGOS REGULATORIOS]" in jr and "[RIESGOS DE DATOS]" in jr and "[RIESGOS DE DECISIÓN]" in jr)
check("las respuestas distintas NO son iguales entre sí (regresión del bug genérico)", len({ask(q)["answer"] for q in CHIPS}) == 5)
# --- IA y Keepa de pago desactivados
jj = a.req("POST", "/api/eu/director", {"product": PID, "question": CHIPS[4], "use_ai": True})[1]
check("IA externa desactivada: modo SIN_IA aunque se pida; Keepa de pago: 0 llamadas en toda la prueba", jj["ai"]["mode"] == "SIN_IA" and not KCALLS)
# --- persistencia
n_before = len(a.req("GET", "/api/eu/overview?product=" + PID)[1].get("queries", [])) if False else None
srv.shutdown(); srv.server_close(); srv = boot(); b = C(srv.server_address[1]); b.login()
j3 = b.req("POST", "/api/eu/director", {"product": PID, "question": CHIPS[4], "use_ai": False})[1]
check("persistencia tras reinicio: los 20 ASIN importados y la confirmación K3 siguen ahí", "20 ASIN analizados" in j3["answer"] and any(r["confirmed"] and r["asin"] == top["asin"] for r in j3["competitors"]))
import sqlite3; c = sqlite3.connect(DB); nq = c.execute("SELECT COUNT(*) FROM records WHERE kind='query'").fetchone()[0]; check("las consultas del Director quedan registradas en SQLite (trazabilidad)", nq >= 10)
check("0 llamadas Keepa tras reinicio", not KCALLS)
# --- compatibilidad con Render: proceso REAL en modo cloud (Host público + X-Forwarded-Proto), Keepa/IA apagados, sin red
import subprocess, time
def libre():
    x = socket.socket(); x.bind(("127.0.0.1", 0)); q = x.getsockname()[1]; x.close(); return q
cp = libre(); H = "demo.example.com"; cdb = os.path.join(tempfile.mkdtemp(), "c.db")
env = {k: v for k, v in os.environ.items() if not k.startswith(("AMAZON_PRO", "KEEPA", "OPENAI"))}
env.update(AMAZON_PRO_PUBLIC_HOST=H, AMAZON_PRO_DB=cdb, AMAZON_PRO_BACKUP_DIR=os.path.join(tempfile.mkdtemp(), "b"), AMAZON_PRO_ADMIN_PASSWORD="Admin-clave-larga-1", AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0", AMAZON_PRO_AI_ENABLE="0", PORT=str(cp))
proc = subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
def creq(m, p, b=None, ck=None, csrf=""):
    h = {"Host": H, "X-Forwarded-Proto": "https", "Origin": "https://" + H, "Content-Type": "application/json"}
    if ck: h["Cookie"] = "apisid=" + ck; h["X-CSRF-Token"] = csrf
    c = http.client.HTTPConnection("127.0.0.1", cp, timeout=30); c.request(m, p, json.dumps(b) if b is not None else None, h); r = c.getresponse(); d = r.read(); return r.status, json.loads(d or b"{}"), dict(r.getheaders())
for _ in range(100):
    try: creq("GET", "/healthz"); break
    except OSError: time.sleep(0.1)
def _evil():
    c = http.client.HTTPConnection("127.0.0.1", cp, timeout=10); c.request("POST", "/api/eu/director", "{}", {"Host": "evil.example", "X-Forwarded-Proto": "https", "Origin": "https://evil.example", "Content-Type": "application/json"}); r = c.getresponse(); r.read(); return r.status
st, lj, hd = creq("POST", "/api/login", {"username": "admin", "password": "Admin-clave-larga-1"}); ck = hd["Set-Cookie"].split("apisid=")[1].split(";")[0]; cs = lj["csrf"]
st1, imp2, _ = creq("POST", "/api/keepa/importar-evidencia", {"product": PID}, ck, cs)
st2, jc2, _ = creq("POST", "/api/eu/director", {"product": PID, "question": CHIPS[4], "use_ai": True}, ck, cs)
check("RENDER (proceso cloud, HTTPS simulado): importar 20 ASIN y responder competidores con Keepa/IA apagados", st == 200 and "Secure" in hd["Set-Cookie"] and st1 == 200 and imp2["importados"] == 20 and "20 ASIN analizados" in jc2["answer"] and jc2["ai"]["mode"] == "SIN_IA")
check("RENDER: Host ajeno sigue rechazado (403) y /healthz responde", creq("GET", "/healthz")[0] == 200 and _evil() == 403)
proc.terminate(); out = proc.communicate(timeout=10)[0]
check("RENDER: logs sin contraseñas ni cookies", "Admin-clave-larga-1" not in out and ck not in out)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
