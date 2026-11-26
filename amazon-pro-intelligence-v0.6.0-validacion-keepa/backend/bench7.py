"""Rediseño F2 — Benchmarking a pantalla completa: /api/bench7/*. LOCAL, SIN RED, SIN GASTO, SIN TOKENS KEEPA.
Solo lee: catálogo, caché/evidencia local de Keepa (keepa_real.load) y el estado público de Keepa (sin clave, sin llamar).
Guarda cada petición y su resultado como registro `bench7_run` en el SQLite actual (historial persistente). Nunca escribe en Amazon.
El prompt libre se guarda y se asocia al contexto; su interpretación por IA está PENDIENTE (no se simula)."""
import re, time
from . import keepa_real as KR, keepa as KP
from .catalog import ACCOUNT_ID

ASIN = re.compile(r"^B0[A-Z0-9]{8}$")
PERIODS = {"dia": "Día", "semana": "Semana", "mes": "Mes", "anio": "Año"}
SC_FIELDS = ("pvp", "coste_unit", "comision_pct", "logistica_unit", "ads_unit")   # escenario: solo con datos aportados por el usuario


def _today(): return time.strftime("%Y-%m-%d", time.gmtime())


def _num(v, lo, hi, name):
    if v in (None, ""): return None
    if isinstance(v, bool) or not isinstance(v, (int, float)): raise ValueError(name + " debe ser numérico")
    if not (lo <= v <= hi): raise ValueError(name + " fuera de rango")
    return float(v)


def clean_context(c):
    if c is None: c = {}
    if not isinstance(c, dict) or set(c) - {"product", "asin", "country", "period", *SC_FIELDS}: raise ValueError("contexto con campos no permitidos")
    o = {"product": str(c.get("product") or "")[:60], "asin": str(c.get("asin") or "").upper().strip()[:10], "country": str(c.get("country") or "ES").upper(), "period": str(c.get("period") or "mes")}
    if o["asin"] and not ASIN.match(o["asin"]): raise ValueError("ASIN inválido (B0 + 8 caracteres)")
    if o["country"] not in KP.DOMAINS: raise ValueError("país no soportado")
    if o["period"] not in PERIODS: raise ValueError("periodo inválido")
    o["pvp"] = _num(c.get("pvp"), 0.01, 100000, "pvp"); o["coste_unit"] = _num(c.get("coste_unit"), 0, 100000, "coste_unit")
    o["comision_pct"] = _num(c.get("comision_pct"), 0, 1, "comision_pct (0–1)"); o["logistica_unit"] = _num(c.get("logistica_unit"), 0, 100000, "logistica_unit"); o["ads_unit"] = _num(c.get("ads_unit"), 0, 100000, "ads_unit")
    return o


def scenarios(c):
    miss = [k for k in SC_FIELDS if c.get(k) is None]
    if miss: return {"state": "NO CALCULABLE", "faltan": miss, "nota": "No se supone ningún coste ausente."}
    def one(pvp, ads):
        com = pvp * c["comision_pct"]; contrib = pvp - c["coste_unit"] - com - c["logistica_unit"] - ads
        return {"pvp": round(pvp, 2), "comision": round(com, 2), "ads": round(ads, 2), "contribucion_unit": round(contrib, 2), "contribucion_pct": round(contrib / pvp * 100, 2)}
    return {"state": "ESTIMADO", "nota": "Hipótesis del usuario; contribución antes de overhead general.", "filas": [{"escenario": "Base", **one(c["pvp"], c["ads_unit"])}, {"escenario": "PVP −10 %", **one(c["pvp"] * 0.9, c["ads_unit"])}, {"escenario": "Ads +25 %", **one(c["pvp"], c["ads_unit"] * 1.25)}]}


def build(APP, prompt, ctx):
    pid = ctx["product"]; prod = APP["catalog"].get(pid) if pid else None
    kr = KR.load(pid) if prod else None
    real = bool(kr and kr.get("state") == "REAL")
    src = [{"fuente": "Keepa", "estado": "CACHÉ LOCAL" if real else "NO CONSULTADA", "fecha": kr.get("consulted_at") if real else None, "evidencia": kr.get("source") if real else "Sin consulta autorizada: no se usa cuota (0 tokens)."},
           {"fuente": "Amazon (SP-API/Ads)", "estado": "NO CONSULTADA", "fecha": None, "evidencia": "Conector de solo lectura no habilitado en esta pantalla."},
           {"fuente": "Web", "estado": "NO CONSULTADA", "fecha": None, "evidencia": "Sin navegación automática en esta entrega (pendiente)."}]
    comp = []
    if real:
        for r in kr["competitors"][:25]:
            comp.append({"asin": r["asin"], "marca": r["brand"], "producto": r["title"], "precio_eur": r["price_eur"], "fecha_precio": r["price_as_of"], "bsr": r.get("bsr"), "origen": "REAL (Keepa, caché local)"})
    sections = [
        {"id": "fuentes", "titulo": "Fuentes y evidencia", "tipo": "tabla", "filas": src},
        {"id": "mercado", "titulo": "BSR, precios, ofertas e histórico", "estado": "REAL (caché local)" if real else "NO DISPONIBLE", "tipo": "tabla", "filas": comp,
         "nota": None if real else "No hay evidencia real de Keepa para este producto; consultarla requiere autorización expresa y cuota."},
        {"id": "ventas", "titulo": "Ventas estimadas", "estado": "NO DISPONIBLE", "tipo": "texto", "texto": "Las ventas estimadas (si se calculan) se mostrarán SIEMPRE separadas de las reales y marcadas ESTIMADO. Hoy no hay ventas reales ni estimación."},
        {"id": "escenarios", "titulo": "Costes y escenarios de contribución", "tipo": "escenarios", **scenarios(ctx)}]
    if real and kr["summary"].get("price_median_fresh") is not None:
        sections[1]["resumen"] = {"competidores": kr["summary"]["n"], "con_precio": kr["summary"]["n_priced"], "mediana_precio_fresco_eur": kr["summary"]["price_median_fresh"], "mediana_100ml": kr["summary"]["per_100ml_median"]}
    resp = [f"Petición recibida para {prod['name'] if prod else (pid or 'sin producto')} · {ctx['country']} · {PERIODS[ctx['period']]}."]
    resp.append("Modo LOCAL: no se ha llamado a Keepa, Amazon ni a la web, y no se ha consumido cuota ni gastado nada.")
    resp.append("Datos de mercado: " + ("hay evidencia real en caché local (ver tabla, con fecha y fuente)." if real else "NO DISPONIBLES para este producto."))
    resp.append("Escenarios: " + ("calculados con tus hipótesis (ESTIMADO)." if ctx and scenarios(ctx)["state"] == "ESTIMADO" else "NO CALCULABLES: faltan datos que no se inventan."))
    resp.append("Interpretación libre del prompt por IA: PENDIENTE (el prompt queda guardado en el historial).")
    return {"mode": "LOCAL · SIN RED · SIN KEEPA", "answer": "\n".join(resp), "sections": sections, "network_calls": 0, "tokens_spent_now": 0}


def keepa_status(APP):
    cfg = KP.config(APP["keepa_env"]()); st = KP.public_status(cfg); kp = APP["keepa"]
    return {"clave_presente": st["key_present"], "formato_plausible": st["key_format_ok"], "habilitado": st["enabled"], "puede_llamar": st["can_call"], "modo": st["mode"],
            "tokens_en_cache": {k: v for k, v in kp.tokens.items() if k != "at"}, "consulta_real_realizada_ahora": False, "red": 0,
            "nota": "Suscripción activa ≠ acceso a la API: esta pantalla no valida la cuota (no llama a Keepa). Verificarla requiere autorización expresa."}


def handle(APP, s, method, path, q, b):
    g = lambda k: (q.get(k) or [None])[0]; p = path[len("/api/bench7/"):]; st = APP["store"]
    if not st.can_access(s, ACCOUNT_ID): raise PermissionError("sin acceso al catálogo")
    if method == "GET":
        if p == "opciones":
            return {"productos": [{"id": x["id"], "nombre": x["name"], "asin": x.get("asin") or ""} for x in APP["catalog"].list()][:200], "paises": sorted(KP.DOMAINS), "periodos": [{"id": k, "l": v} for k, v in PERIODS.items()]}
        if p == "keepa": return keepa_status(APP)
        if p == "historial":
            return {"items": [{"id": r["id"], "creado": r["created_at"], "prompt": r["data"]["prompt"][:160], "contexto": r["data"]["context"], "modo": r["data"]["result"]["mode"]} for r in st.list(ACCOUNT_ID, "bench7_run", 50)],
                    "persistencia": "SQLite actual (registros bench7_run); incluido en el respaldo existente."}
        if p == "run":
            r = st.get(ACCOUNT_ID, str(g("id") or ""))
            if not r or r["kind"] != "bench7_run": raise LookupError(p)
            return {"id": r["id"], "creado": r["created_at"], **r["data"]}
        raise LookupError(p)
    if method == "POST" and p == "run":
        if s.get("viewer"): raise PermissionError("solo lectura (viewer)")
        if not isinstance((b or {}).get("prompt"), str) or not b["prompt"].strip() or len(b["prompt"]) > 4000: raise ValueError("prompt requerido (≤4000 caracteres)")
        ctx = clean_context(b.get("context")); res = build(APP, b["prompt"].strip(), ctx)
        rid = st.put(ACCOUNT_ID, "bench7_run", {"prompt": b["prompt"].strip(), "context": ctx, "result": res, "fecha": _today()}, actor=s["username"])
        return {"id": rid, "creado": _today(), "prompt": b["prompt"].strip(), "context": ctx, "result": res}
    raise LookupError(p)
