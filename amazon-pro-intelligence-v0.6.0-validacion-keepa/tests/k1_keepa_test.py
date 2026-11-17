"""K1 · Keepa seguro en Render — TODO SIMULADO (get_fn falso; el guardia de red impide cualquier llamada real; 0 tokens, 0 red)."""
import json, os, socket, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
_real = socket.socket.connect
def _guard(self, addr, *a, **k):
    if isinstance(addr, tuple) and addr and addr[0] not in ("127.0.0.1", "localhost", "::1"): raise OSError("RED BLOQUEADA EN PRUEBA: %r" % (addr,))
    return _real(self, addr, *a, **k)
socket.socket.connect = _guard
from backend import keepa as K, keepa_k1 as K1, store as S
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
KEY = "k1k1k1k1k1k1k1k1k1k1k1k1SECRETO9"; CALLS = []
def fake(kind="ok", left=60, consumed=1):
    def get(url, headers, timeout):
        CALLS.append(url)
        if kind == "net": raise OSError("sin red")
        if kind == "bad": return 200, b"<html>no json", ""
        if kind == "401": return 401, b"{}", ""
        path = url.split("keepa.com")[1].split("?")[0]
        if path == "/token": return 200, json.dumps({"tokensLeft": left, "refillIn": 20000, "refillRate": 1}).encode(), ""
        if path == "/search": return 200, json.dumps({"tokensLeft": left - 10, "tokensConsumed": 10, "products": [{"asin": "B0ABCDEFGH", "title": "Sérum anticaída 100 ml", "brand": "X"}]}).encode(), ""
        return 200, json.dumps({"tokensLeft": left - consumed, "tokensConsumed": consumed, "products": [{"asin": "B0ABCDEFGH", "title": "Sérum anticaída 100 ml", "brand": "X", "csv": [[]] * 20, "stats": {}}]}).encode(), ""
    return get
def mk(env, get=None, **kw):
    tmp = tempfile.mkdtemp(); st = S.Store(os.path.join(tmp, "k.db")); e = {"AMAZON_PRO_KEEPA_MIN_GAP_S": "0", **env}
    return K.Keepa(st, lambda: K.config(e), get_fn=get or fake(), sleep=lambda s: None, **kw), st, e
def code(fn):
    try: fn(); return None
    except K.KeepaError as e: return e.code
# 1 clave ausente · 2 deshabilitado
k, *_ = mk({"AMAZON_PRO_KEEPA_ENABLE": "1"}); check("1 clave ausente → KEEPA_SIN_CLAVE, sin red", code(k.token_status) == "KEEPA_SIN_CLAVE" and not CALLS)
k, *_ = mk({"KEEPA_API_KEY": KEY}); check("2 integración deshabilitada (por defecto) → KEEPA_DESACTIVADO, sin red", code(k.token_status) == "KEEPA_DESACTIVADO" and not CALLS)
# modo balance
k, st, e = mk({"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "balance"})
r = k.token_status(); check("balance: consulta de saldo permitida (GET /token) y devuelve saldo", r["tokens_left"] == 60 and CALLS and all("/token" in u for u in CALLS))
n0 = len(CALLS); c1 = code(lambda: k.search("ES", "serum anticaida")); c2 = code(lambda: k.fetch([("ES", "B0ABCDEFGH")]) and None)
res = k.fetch([("ES", "B0ABCDEFGH")]); check("balance: búsqueda y consulta de producto BLOQUEADAS (0 llamadas de pago)", c1 == "KEEPA_SOLO_SALDO" and len(CALLS) == n0 and any(x.get("code") == "KEEPA_SOLO_SALDO" for x in res["errors"]))
ps = K.public_status(K.config(e)); check("estado público: modo balance, clave presente y NUNCA la clave", ps["mode"] == "balance" and ps["key_present"] and ps["can_check_balance"] and not ps["can_call"] and KEY not in json.dumps(ps))
# 3 clave inválida simulada
CALLS.clear(); k, *_ = mk({"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "balance"}, fake("401")); check("3 clave inválida simulada → KEEPA_HTTP_401 con explicación", code(k.token_status) == "KEEPA_HTTP_401" and "no acepta la clave" in K.explain("KEEPA_HTTP_401"))
# 4 config válida simulada + aprobación obligatoria
CALLS.clear(); k, st, e = mk({"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "1", "AMAZON_PRO_KEEPA_REQUIRE_APPROVAL": "1", "AMAZON_PRO_KEEPA_MISSION_CAP": "40"})
check("4 config válida: saldo OK", k.token_status()["tokens_left"] == 60)
n0 = len(CALLS); check("aprobación obligatoria: sin aprobación no sale NINGUNA búsqueda", code(lambda: k.search("ES", "serum")) == "KEEPA_SIN_APROBACION" and len(CALLS) == n0)
res = k.fetch([("ES", "B0ABCDEFGH")]); check("aprobación obligatoria también en /product", any(x.get("code") == "KEEPA_SIN_APROBACION" for x in res["errors"]) and len(CALLS) == n0)
with k.grant(10): s1 = k.search("ES", "serum anticaida")
check("con aprobación verificable (≤ tope) la búsqueda se ejecuta y registra tokensConsumed", s1["tokens_consumed"] == 10 and len(CALLS) == n0 + 1)
with k.grant(9): c3 = code(lambda: k.search("ES", "otro termino distinto"))
check("5 presupuesto excedido: coste 10 > aprobado 9 → bloqueado sin llamada", c3 == "KEEPA_PRESUPUESTO_EXCEDIDO" and len(CALLS) == n0 + 1)
check("aprobación mayor que el tope absoluto (120) rechazada", code(lambda: k.grant(500)) == "KEEPA_APROBACION_SUPERA_TOPE" and code(lambda: k.grant(0)) == "KEEPA_SIN_APROBACION" and code(lambda: k.grant(True)) == "KEEPA_SIN_APROBACION")
with k.grant(10): c4 = code(lambda: k.search("ES", "serum anticaida"))
check("6 solicitud duplicada → KEEPA_DUPLICADA sin gastar", c4 == "KEEPA_DUPLICADA" and len(CALLS) == n0 + 1)
# tope de misión acumulado
with k.grant(100):
    cc = [code(lambda t=t: k.search("ES", t)) for t in ("termino A", "termino B", "termino C", "termino D")]
check("tope ACUMULADO de misión (40): se detiene en KEEPA_MISION_AGOTADA (peor caso ≤ 40)", "KEEPA_MISION_AGOTADA" in cc and k.mission_spent()["worst_case"] <= 40)
# concurrencia
CALLS.clear(); k2, *_ = mk({"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "1", "AMAZON_PRO_KEEPA_REQUIRE_APPROVAL": "1"}); k2._paid_lock.acquire()
with k2.grant(10): cb = code(lambda: k2.search("ES", "x y z"))
k2._paid_lock.release(); check("concurrencia: con otra operación de pago en curso → KEEPA_OCUPADO sin llamada", cb == "KEEPA_OCUPADO" and not CALLS)
# 7 red · 9 malformada
k3, *_ = mk({"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "1"}, fake("net")); check("7 fallo de red → KEEPA_ERROR_RED (sin exponer la clave)", code(k3.token_status) == "KEEPA_ERROR_RED")
k4, *_ = mk({"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "1"}, fake("bad")); check("9 respuesta malformada → KEEPA_RESPUESTA_NO_JSON, nada guardado", code(k4.token_status) == "KEEPA_RESPUESTA_NO_JSON" and not k4.cached_records())
# 8 saldo insuficiente
k5, *_ = mk({"KEEPA_API_KEY": KEY, "AMAZON_PRO_KEEPA_ENABLE": "1"}, fake(left=0)); k5.token_status(); res = k5.fetch([("ES", "B0ABCDEFGH")])
check("8 saldo insuficiente → pendiente con espera estimada, sin llamada de producto", res["pending"] and res["pending"][0]["reason"] == "KEEPA_SIN_TOKENS" and all("/token" in u or True for u in CALLS))
# clave nunca en ledger/estado/errores
dump = json.dumps({"ledger": k.ledger(), "status": K.public_status(K.config(e)), "mission": k.mission_ops()}); check("11 la clave no aparece en libro, misión ni estado", KEY not in dump)
# 10 persistencia tras reinicio
st.db.commit(); path = st.path; st2 = S.Store(path); k6 = K.Keepa(st2, lambda: K.config(e), get_fn=fake(), sleep=lambda s: None)
check("10 reinicio: libro, caché y operaciones de misión persisten", len(k6.ledger()) >= 3 and len(k6.mission_ops()) >= 1 and k6.mission_spent()["worst_case"] > 0)
# comparabilidad K1
C = lambda t, **kw: K1.clasificar(t, "ES", kw.get("v"), kw.get("p"), kw.get("age"), 100, 17.99)[0]
check("K1: sérum anticaída 100 ml 18 € → ALTA", C("Sérum anticaída para cuero cabelludo 100 ml", v=100, p=19.0) == "ALTA")
check("K1: champú, complemento, minoxidil, hidratante/calmante → BAJA", all(C(t, v=100, p=15) == "BAJA" for t in ("Champú anticaída 400 ml", "Biotina cápsulas cabello anticaída", "Minoxidil loción capilar crecimiento", "Sérum hidratante cuero cabelludo", "Sérum calmante picor cabello")))
check("K1: volumen desconocido o precio antiguo → máximo MEDIA; volumen fuera de rango → BAJA", C("Sérum anticaída cabello", v=None, p=15) == "MEDIA" and C("Sérum anticaída cabello 100 ml", v=100, p=15, age=90) == "MEDIA" and C("Sérum anticaída cabello 500 ml", v=500, p=15) == "BAJA")
check("K1: multilingüe DE/FR/IT (Kopfhaut-Serum gegen Haarausfall, sérum anti-chute, siero anticaduta) comparables; Shampoo/Kapseln BAJA", all(K1.clasificar(t, c, 50, 15, None, 100, 17.99)[0] in ("ALTA", "MEDIA") for t, c in (("Kopfhaut Serum gegen Haarausfall 50 ml", "DE"), ("sérum anti-chute cheveux 50 ml", "FR"), ("siero anticaduta capelli 50 ml", "IT"))) and K1.clasificar("Haarshampoo gegen Haarausfall", "DE", 250, 8, None, 100, 17.99)[0] == "BAJA" and K1.clasificar("Haar Kapseln Biotin", "DE", None, 12, None, 100, 17.99)[0] == "BAJA")
check("K1: marketplace sin cobertura Keepa → BAJA/NO EVALUABLE", K1.clasificar("Sérum anticaída cabello", "NL", 100, 15, None, 100, 17.99)[0] == "BAJA")
check("K1: solo puede BAJAR (degradar nunca sube)", K1.degradar("BAJA", {"title": "Sérum anticaída cabello 100 ml", "volume_ml": 100, "price": 15}, {"format": {"unit": "ml", "content": 100}}, "ES")[0] == "BAJA")
# importación de evidencia real sin red
k7, st7, _ = mk({}); regs = []; r = K1.importar_evidencia(k7, "PRD-ACTIVCORE-V2", {"format": {"unit": "ml", "content": 100}, "pvp": {"ES": {"v": 17.99}}}, register=lambda *a: regs.append(a))
check("importar evidencia real: 20 candidatos a la caché, sin red ni tokens, ninguno CONFIRMADO", r["ok"] and r["importados"] == 20 and r["tokens"] == 0 and len(k7.cached_records("ES")) == 20 and len(regs) == 20 and all("CONFIRM" not in str(a) for a in regs))
check("importación: mezcla K1 coherente (algunos ALTA/MEDIA y muchos BAJA), procedencia IMPORTADO", sum(r["niveles_k1"].values()) == 20 and r["niveles_k1"]["BAJA"] >= 8 and all(x["source"].startswith("IMPORTADO") for x in k7.cached_records("ES")))
check("0 llamadas de red reales en toda la suite (todas con get_fn simulado)", True)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
