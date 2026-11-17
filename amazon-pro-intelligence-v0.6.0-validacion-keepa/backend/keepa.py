"""Conector Keepa API (V0.4.0) — SOLO LECTURA, con control de tokens, caché, cola, límites y registro de fuentes.

Reglas:
  * La clave vive en %USERPROFILE%\\AmazonPro\\keepa.env (o variable de entorno KEEPA_API_KEY). Nunca se imprime, registra, exporta ni se envía a la IA.
  * Interruptor: AMAZON_PRO_KEEPA_ENABLE=1 (por defecto 0 → ninguna llamada de red).
  * Solo HTTPS a api.keepa.com y solo GET /token, /product, /search (lectura). No existe código de escritura.
  * Consumo: cada operación calcula ANTES el coste previsto en tokens; si supera el presupuesto por lote exige aprobación explícita.
    El coste REAL (tokensConsumed de la respuesta) se registra en el libro (keepa_ledger). Un token/minuto de recarga NO significa 1 token por producto.
  * Sin saldo (429 / tokensLeft insuficiente) NO se bloquea la aplicación: lo no consultado queda PENDIENTE con su tiempo estimado de espera.
  * Lo que Keepa no devuelve se muestra NO DISPONIBLE (None); nunca se convierte en cero.
  * Cobertura: Keepa NO cubre amazon.nl, .pl, .se, .com.be ni .ie → esos países son NO EVALUABLE por esta vía."""
import csv, gzip, hashlib, io, json, os, re, time, urllib.error, urllib.parse, urllib.request, zlib

HOST = "api.keepa.com"
ALLOWED_PATHS = {"/token", "/product", "/search"}
# Códigos de dominio de Keepa (documentados por Keepa; se verifican en la primera consulta real: un código inválido devuelve error y no gasta tokens)
DOMAINS = {"DE": 3, "FR": 4, "IT": 8, "ES": 9, "UK": 2}
UNSUPPORTED = {"NL": "amazon.nl", "PL": "amazon.pl", "SE": "amazon.se", "BE": "amazon.com.be", "IE": "amazon.ie"}
MARKET_HOST = {"DE": "amazon.de", "FR": "amazon.fr", "IT": "amazon.it", "ES": "amazon.es", "UK": "amazon.co.uk", **UNSUPPORTED}
CURRENCY = {"DE": "EUR", "FR": "EUR", "IT": "EUR", "ES": "EUR", "UK": "GBP"}
# Índices del array csv/stats.current de Keepa
IDX = {"AMAZON": 0, "NEW": 1, "RANK": 3, "LIST": 4, "COUNT_NEW": 11, "RATING": 16, "COUNT_REVIEWS": 17, "BUY_BOX": 18}
KEEPA_EPOCH_MIN = 21564000  # minutos Keepa → minutos Unix
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
SUSPECT = re.compile(r"(ignore (all |any |the )?(previous|prior|above)|system prompt|you are now|disregard|olvida (las )?instrucciones|ignora (las )?instrucciones|act as|nuevo rol|<\s*/?\s*(system|assistant)\b)", re.I)


class KeepaError(Exception):
    def __init__(self, code):
        super().__init__(code); self.code = code


EXPLAIN = {
    "KEEPA_DESACTIVADO": "Keepa está desactivado (AMAZON_PRO_KEEPA_ENABLE=0). No se ha consultado nada ni se han gastado tokens.",
    "KEEPA_SIN_CLAVE": "No se encuentra la clave de Keepa. Ejecuta CONFIGURAR_KEEPA.bat, pega la clave en keepa.env y reinicia.",
    "KEEPA_DOMINIO_NO_SOPORTADO": "Keepa no cubre ese marketplace (solo .de, .fr, .it, .es y .co.uk entre los analizados). Ese país queda NO EVALUABLE por esta vía.",
    "KEEPA_ASIN_INVALIDO": "El ASIN no tiene 10 caracteres (letras mayúsculas y números).",
    "KEEPA_SIN_TOKENS": "No hay tokens suficientes ahora. No se ha perdido nada: lo pendiente se consultará cuando haya saldo (se indica la espera estimada).",
    "KEEPA_HTTP_401": "Keepa no acepta la clave (401/402). Revisa la clave en keepa.env o la suscripción de API. No se ha consumido nada.",
    "KEEPA_HTTP_429": "Keepa indica que no quedan tokens (429). Espera la recarga; la aplicación sigue funcionando.",
    "KEEPA_HTTP_400": "Keepa rechazó la petición (400): parámetros o dominio no válidos.",
    "KEEPA_ERROR_SERVIDOR": "Keepa tuvo un error temporal (5xx). Reintenta más tarde.",
    "KEEPA_TIMEOUT": "Keepa no respondió a tiempo. Puede que se hayan consumido tokens: se registra como incierto.",
    "KEEPA_RESPUESTA_NO_JSON": "Keepa respondió algo que no es JSON válido. No se guarda nada.",
    "KEEPA_HOST_NO_PERMITIDO": "Operación bloqueada: solo se permite lectura en api.keepa.com.",
    "KEEPA_MISION_AGOTADA": "Presupuesto de la misión agotado o insuficiente para esta consulta: no se ha realizado ninguna llamada.",
    "KEEPA_DUPLICADA": "Consulta idéntica ya realizada en esta misión: se reutiliza el resultado guardado, sin gastar tokens.",
    "KEEPA_PRESUPUESTO_EXCEDIDO": "El consumo previsto supera el presupuesto autorizado del lote. Hace falta aprobación explícita.",
    "KEEPA_ERROR_RED": "No se pudo conectar con Keepa (red). Reintenta más tarde.",
}


def explain(code):
    c = str(code or "")
    if c in EXPLAIN:
        return EXPLAIN[c]
    m = re.match(r"KEEPA_HTTP_(\d+)", c)
    if m:
        n = int(m.group(1))
        return EXPLAIN["KEEPA_ERROR_SERVIDOR"] if n >= 500 else EXPLAIN.get("KEEPA_HTTP_" + str(n)) or "Keepa devolvió un error HTTP %d." % n
    return c


def sanitize_text(s, n=160):
    """Los textos de Keepa/Amazon son DATOS no confiables: sin control chars, truncados; se marca si parecen instrucciones."""
    t = re.sub(r"[\x00-\x1f\x7f]+", " ", str(s or "")); t = re.sub(r"\s+", " ", t).strip()[:n]
    return t, bool(SUSPECT.search(t))


def config(env=None):
    e = os.environ if env is None else env
    fi = lambda k, d: int(e.get(k) or d)
    key = e.get("KEEPA_API_KEY") or e.get("KEEPA_KEY") or ""
    return {"key": key, "enabled": (e.get("AMAZON_PRO_KEEPA_ENABLE") or "0").strip() == "1", "batch_budget": fi("AMAZON_PRO_KEEPA_BATCH_BUDGET", 30),
            "hard_cap": fi("AMAZON_PRO_KEEPA_HARD_CAP", 120), "cache_hours": fi("AMAZON_PRO_KEEPA_CACHE_HOURS", 24), "timeout": fi("AMAZON_PRO_KEEPA_TIMEOUT", 30),
            "chunk": max(1, min(fi("AMAZON_PRO_KEEPA_CHUNK", 10), 100)), "cost_per_asin": fi("AMAZON_PRO_KEEPA_COST_PER_ASIN", 1), "search_cost": fi("AMAZON_PRO_KEEPA_SEARCH_COST", 10),
            "min_gap_s": float(e.get("AMAZON_PRO_KEEPA_MIN_GAP_S") or 1.0),
            "mission_cap": fi("AMAZON_PRO_KEEPA_MISSION_CAP", 0), "mission_countries": [x.strip().upper() for x in (e.get("AMAZON_PRO_KEEPA_MISSION_COUNTRIES") or "").split(",") if x.strip()]}  # >0: tope ACUMULADO de la misión (V0.6 validación real); 0 = desactivado


def public_status(cfg):
    """Nunca incluye la clave; solo si existe y si parece plausible."""
    k = cfg["key"]
    return {"enabled": cfg["enabled"], "key_present": bool(k), "key_format_ok": bool(k) and len(k) >= 20 and not any(c.isspace() for c in k),
            "can_call": cfg["enabled"] and bool(k), "batch_budget": cfg["batch_budget"], "hard_cap": cfg["hard_cap"], "cache_hours": cfg["cache_hours"],
            "supported": {c: MARKET_HOST[c] for c in DOMAINS}, "unsupported": dict(UNSUPPORTED)}


def _default_get(url, headers, timeout):  # punto de sustitución en tests (sin red)
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("Content-Encoding", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b"", e.headers.get("Content-Encoding", "") if e.headers else ""


def _decode(body, enc):
    if body[:2] == b"\x1f\x8b":
        return gzip.decompress(body)
    if enc and "deflate" in enc.lower():
        try:
            return zlib.decompress(body)
        except zlib.error:
            return zlib.decompress(body, -15)
    return body


def keepa_to_unix(km):
    return (int(km) + KEEPA_EPOCH_MIN) * 60


def _series(csv_arr, price=True, max_points=400):
    """[t0,v0,t1,v1,...] → [(YYYY-MM-DD, valor)] sin -1 (sin dato). price=True → céntimos→unidad."""
    if not csv_arr:
        return []
    out = []
    for i in range(0, len(csv_arr) - 1, 2):
        v = csv_arr[i + 1]
        if v is None or v < 0:
            continue
        out.append((time.strftime("%Y-%m-%d", time.gmtime(keepa_to_unix(csv_arr[i]))), round(v / 100.0, 2) if price else v))
    return out[-max_points:]


def _last(csv_arr):
    s = [csv_arr[i + 1] for i in range(0, len((csv_arr or [])) - 1, 2)]
    s = [x for x in s if x is not None and x >= 0]
    return s[-1] if s else None


def _cur(stats, csv_arr, idx):
    """Valor actual: stats.current[idx] si existe y es válido; si no, último punto del csv."""
    try:
        v = (stats or {}).get("current", [])[idx]
        if v is not None and v >= 0:
            return v
    except (IndexError, TypeError):
        pass
    return _last(csv_arr[idx]) if csv_arr and idx < len(csv_arr) else None


VOL_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(ml|mL|ML|Ml|cl|CL|l\b|L\b)")


def parse_volume_ml(title):
    """Formato en mL extraído del TÍTULO (inferencia: calidad TÍTULO, no dato de Keepa). None si no hay."""
    m = VOL_RE.search(title or "")
    if not m:
        return None
    v = float(m.group(1).replace(",", ".")); u = m.group(2).lower()
    return round(v * (10 if u == "cl" else 1000 if u == "l" else 1), 2)


UNIT_RE = re.compile(r"(\d{1,4})\s*(?:x\s*)?(c[áa]psulas?|capsules?|caps\b|kapseln|g[ée]lules?|softgels?|perlas|tabletas?|tablets?|comprimidos?|tabletten|compresse|pastillas|gummies|sticks?|sobres?|ampollas?|ampoules?)", re.I)


def parse_units(title):
    """Nº de unidades (cápsulas, comprimidos…) extraído del TÍTULO (inferencia). None si no hay."""
    m = UNIT_RE.search(title or "")
    return int(m.group(1)) if m else None


def _bsr_category(p):
    """Categoría del BSR si Keepa la devuelve (salesRankReference/categoryTree); si no, None (NO DISPONIBLE)."""
    tree = p.get("categoryTree") or []
    name = sanitize_text(tree[-1].get("name"), 60)[0] if tree and isinstance(tree[-1], dict) else None
    ref = p.get("salesRankReference")
    return {"id": ref if isinstance(ref, int) and ref > 0 else None, "name": name or None}


def normalize_product(p, country, domain, fetched_at):
    """Registro normalizado de un producto de Keepa. Cada campo ausente = None (NO DISPONIBLE)."""
    csv_arr = p.get("csv") or []; stats = p.get("stats") or {}
    cents = lambda v: None if v is None else round(v / 100.0, 2)
    new = _cur(stats, csv_arr, IDX["NEW"]); amz = _cur(stats, csv_arr, IDX["AMAZON"]); bb = _cur(stats, csv_arr, IDX["BUY_BOX"])
    price, psrc = (bb, "buybox") if bb is not None else (new, "nuevo") if new is not None else (amz, "amazon") if amz is not None else (None, None)
    rating = _cur(stats, csv_arr, IDX["RATING"]); title, susp = sanitize_text(p.get("title")); brand, s2 = sanitize_text(p.get("brand"), 60)
    asin = str(p.get("asin") or "")
    rank_s = _series(csv_arr[IDX["RANK"]], price=False) if len(csv_arr) > IDX["RANK"] else []
    price_s = _series(csv_arr[IDX["NEW"]]) if len(csv_arr) > IDX["NEW"] else []
    return {"country": country, "marketplace": MARKET_HOST.get(country), "domain": domain, "asin": asin, "brand": brand, "title": title, "injection_suspect": susp or s2,
            "url": "https://www.%s/dp/%s" % (MARKET_HOST.get(country, ""), asin) if asin else None, "currency": CURRENCY.get(country), "volume_ml": parse_volume_ml(title), "units": parse_units(title), "bsr_category": _bsr_category(p), "bsr_date": time.strftime("%Y-%m-%d", time.gmtime(fetched_at)), "volume_source": "título (inferencia)" if parse_volume_ml(title) else None,
            "price": cents(price), "price_source": psrc, "price_as_of": (price_s[-1][0] if price_s and psrc == "nuevo" else None), "price_list": cents(_cur(stats, csv_arr, IDX["LIST"])), "bsr": _cur(stats, csv_arr, IDX["RANK"]),
            "rating": None if rating is None else round(rating / 10.0, 1), "reviews": _cur(stats, csv_arr, IDX["COUNT_REVIEWS"]), "offers_new": _cur(stats, csv_arr, IDX["COUNT_NEW"]),
            "available": None if price is None and p.get("availabilityAmazon") is None else (price is not None or p.get("availabilityAmazon") == 0),
            "price_history": price_s, "bsr_history": rank_s, "history_points": {"price": len(price_s), "bsr": len(rank_s)},
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(fetched_at)), "source": "Keepa API /product (api.keepa.com)", "evidence_quality": "ALTA" if price is not None and p.get("csv") else "BAJA",
            "seller": None}  # Keepa no devuelve el vendedor sin 'offers' (coste adicional): NO DISPONIBLE


class Keepa:
    def __init__(self, store, cfg_fn, get_fn=None, clock=time.time, sleep=time.sleep):
        self.store, self.cfg_fn, self._get, self.clock, self.sleep = store, cfg_fn, get_fn or _default_get, clock, sleep
        self.tokens = {"left": None, "refill_in_ms": None, "rate": None, "at": None}; self._last_call = 0.0
        with self.store.lock:
            self.store.db.execute("CREATE TABLE IF NOT EXISTS keepa_mission(op_id TEXT PRIMARY KEY, ts TEXT NOT NULL, path TEXT NOT NULL, params_hash TEXT NOT NULL, est_tokens INTEGER NOT NULL, confirmed_tokens INTEGER, tokens_left_after INTEGER, status TEXT NOT NULL, note TEXT)")
            self.store.db.commit()

    # ---- bajo nivel ------------------------------------------------------------------------------
    def _redact(self, s):
        k = self.cfg_fn()["key"]
        return str(s).replace(k, "[CLAVE-OCULTA]") if k else str(s)

    def _request(self, path, params, est=0):
        cfg = self.cfg_fn()
        if not cfg["enabled"]:
            raise KeepaError("KEEPA_DESACTIVADO")
        if not cfg["key"]:
            raise KeepaError("KEEPA_SIN_CLAVE")
        if path not in ALLOWED_PATHS:
            raise KeepaError("KEEPA_HOST_NO_PERMITIDO")
        op = self._mission_begin(path, params, est) if path in ("/product", "/search") else None  # parada automática por presupuesto / duplicados ANTES de la red
        try:
            gap = cfg["min_gap_s"] - (self.clock() - self._last_call)
            if gap > 0:
                self.sleep(gap)  # límite de frecuencia: separación mínima entre llamadas
            url = "https://%s%s?%s" % (HOST, path, urllib.parse.urlencode({"key": cfg["key"], **params}))
            self._last_call = self.clock()
            try:
                status, body, enc = self._get(url, {"Accept-Encoding": "gzip, deflate", "User-Agent": "AmazonProIntelligence/0.4"}, cfg["timeout"])
            except TimeoutError:
                raise KeepaError("KEEPA_TIMEOUT")
            except (urllib.error.URLError, OSError):
                raise KeepaError("KEEPA_ERROR_RED")
            try:
                txt = _decode(body, enc).decode("utf-8", "replace")
            except Exception:
                txt = ""
            j = None
            try:
                j = json.loads(txt)
            except ValueError:
                pass
            if isinstance(j, dict) and "tokensLeft" in j:
                self.tokens = {"left": j.get("tokensLeft"), "refill_in_ms": j.get("refillIn"), "rate": j.get("refillRate"), "at": self.clock()}
            if status == 429:
                raise KeepaError("KEEPA_HTTP_429")
            if status >= 400:
                raise KeepaError("KEEPA_HTTP_%d" % status)
            if not isinstance(j, dict):
                raise KeepaError("KEEPA_RESPUESTA_NO_JSON")
            if op:
                tc = j.get("tokensConsumed") if isinstance(j, dict) else None
                self._mission_end(op, "OK" if isinstance(tc, int) else "INCIERTA", tc if isinstance(tc, int) else None, None if isinstance(tc, int) else "Keepa no informó tokensConsumed: se cuenta el peor caso")
            return j
        except KeepaError as ex:
            if op:
                inc = ex.code in ("KEEPA_TIMEOUT", "KEEPA_ERROR_RED", "KEEPA_RESPUESTA_NO_JSON") or ex.code.startswith("KEEPA_HTTP_5")
                self._mission_end(op, "INCIERTA" if inc else "ERROR", None if inc else 0, ex.code)
            raise

    def _ledger(self, op, domain, n, est, consumed, status, hits=0, note=None):
        t = self.tokens
        with self.store.lock:
            self.store.db.execute("INSERT INTO keepa_ledger(ts,op,domain,n_asin,est_tokens,tokens_consumed,tokens_left,refill_rate,status,cache_hits,note) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                  (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.clock())), op, domain, n, est, consumed, t.get("left"), t.get("rate"), status, hits, note)); self.store.db.commit()

    # ---- presupuesto de MISIÓN (tope acumulado, duplicados, parada automática) ---------------------
    def mission_spent(self):
        """Consumo acumulado: CONFIRMADO (tokensConsumed de Keepa) + estimación de las operaciones inciertas/en curso (peor caso)."""
        with self.store.lock:
            r = self.store.db.execute("SELECT COALESCE(SUM(CASE WHEN status='OK' THEN confirmed_tokens WHEN status IN ('INCIERTA','EN_CURSO') THEN est_tokens ELSE COALESCE(confirmed_tokens,0) END),0) AS n, COALESCE(SUM(CASE WHEN status='OK' THEN confirmed_tokens ELSE 0 END),0) AS c FROM keepa_mission").fetchone()
        return {"worst_case": int(r["n"]), "confirmed": int(r["c"])}

    def mission_status(self):
        cap = self.cfg_fn()["mission_cap"]; sp = self.mission_spent()
        return {"cap": cap, "confirmed_spent": sp["confirmed"], "worst_case_spent": sp["worst_case"], "remaining_worst_case": max(0, cap - sp["worst_case"]) if cap else None}

    def mission_ops(self):
        with self.store.lock:
            return [dict(r) for r in self.store.db.execute("SELECT * FROM keepa_mission ORDER BY ts, op_id").fetchall()]

    def _mission_begin(self, path, params, est):
        cap = self.cfg_fn()["mission_cap"]
        if not cap:
            return None
        h = hashlib.sha256(json.dumps({"p": path, "q": {k: v for k, v in params.items()}}, sort_keys=True).encode()).hexdigest()[:16]
        with self.store.lock:
            dup = self.store.db.execute("SELECT op_id FROM keepa_mission WHERE params_hash=? AND status IN ('OK','INCIERTA','EN_CURSO')", (h,)).fetchone()
            if dup:
                raise KeepaError("KEEPA_DUPLICADA")
            if self.mission_spent()["worst_case"] + est > cap:
                raise KeepaError("KEEPA_MISION_AGOTADA")
            op = "KP-%s-%s" % (time.strftime("%Y%m%d%H%M%S", time.gmtime(self.clock())), h[:6])
            self.store.db.execute("INSERT INTO keepa_mission VALUES(?,?,?,?,?,NULL,NULL,'EN_CURSO',NULL)", (op, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.clock())), path, h, est)); self.store.db.commit()
        return op

    def _mission_end(self, op, status, confirmed=None, note=None):
        if not op:
            return
        with self.store.lock:
            self.store.db.execute("UPDATE keepa_mission SET status=?, confirmed_tokens=?, tokens_left_after=?, note=? WHERE op_id=?", (status, confirmed, self.tokens.get("left"), note, op)); self.store.db.commit()

    # ---- operaciones públicas --------------------------------------------------------------------
    def token_status(self):
        """Saldo de tokens (GET /token no consume tokens). Es también la 'consulta mínima autorizada' de validación."""
        try:
            j = self._request("/token", {})
        except KeepaError as e:
            self._ledger("token", None, 0, 0, 0, e.code); raise
        self._ledger("token", None, 0, 0, 0, "OK")
        return {"tokens_left": j.get("tokensLeft"), "refill_in_ms": j.get("refillIn"), "refill_rate_per_min": j.get("refillRate"), "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.clock()))}

    def _cache_get(self, domain, asin, params, ttl_h):
        k = "%s|%s|%s" % (domain, asin, params)
        with self.store.lock:
            r = self.store.db.execute("SELECT fetched_at,data FROM keepa_cache WHERE k=?", (k,)).fetchone()
        if r and self.clock() - r["fetched_at"] <= ttl_h * 3600:
            return json.loads(r["data"])
        return None

    def _cache_put(self, domain, asin, params, rec):
        with self.store.lock:
            self.store.db.execute("INSERT OR REPLACE INTO keepa_cache VALUES(?,?,?,?,?,?)", ("%s|%s|%s" % (domain, asin, params), domain, asin, params, self.clock(), json.dumps(rec, ensure_ascii=False))); self.store.db.commit()

    @staticmethod
    def _params(history=True, rating=False):
        return "h%d_r%d" % (history, rating)

    def plan(self, items, history=True, rating=False, ttl_h=None):
        """items = [(país, asin)]. Calcula SIN consumir: duplicados, caché, no soportados, inválidos y tokens previstos."""
        cfg = self.cfg_fn(); ttl = cfg["cache_hours"] if ttl_h is None else ttl_h; seen, todo, cached, bad, unsup = set(), [], [], [], []
        per = cfg["cost_per_asin"] + (1 if rating else 0); pk = self._params(history, rating)
        for c, a in items:
            c = str(c).upper(); a = str(a).upper().strip()
            if (c, a) in seen:
                continue
            seen.add((c, a))
            if c not in DOMAINS:
                unsup.append({"country": c, "asin": a, "reason": explain("KEEPA_DOMINIO_NO_SOPORTADO")}); continue
            if not ASIN_RE.match(a):
                bad.append({"country": c, "asin": a, "reason": explain("KEEPA_ASIN_INVALIDO")}); continue
            hit = self._cache_get(DOMAINS[c], a, pk, ttl)
            (cached if hit else todo).append((c, a, hit))
        est = per * len(todo)
        return {"to_fetch": [{"country": c, "asin": a} for c, a, _ in todo], "cached": [h for _, _, h in cached], "invalid": bad, "unsupported": unsup, "estimated_tokens": est,
                "per_asin": per, "batch_budget": cfg["batch_budget"], "hard_cap": cfg["hard_cap"], "needs_approval": est > cfg["batch_budget"], "history": history, "rating": rating,
                "note": "Estimación; el consumo REAL se lee de la respuesta (tokensConsumed) y queda en el libro."}

    def fetch(self, items, history=True, rating=False, approved_tokens=None, ttl_h=None, wait=False):
        """Consulta por lotes con presupuesto. Devuelve registros normalizados + pendientes (sin saldo) + errores. Nunca lanza por falta de saldo."""
        cfg = self.cfg_fn(); pl = self.plan(items, history, rating, ttl_h)
        out = {"products": list(pl["cached"]), "pending": [], "errors": [], "invalid": pl["invalid"], "unsupported": pl["unsupported"], "from_cache": len(pl["cached"]), "tokens_consumed": 0, "plan": {k: pl[k] for k in ("estimated_tokens", "per_asin", "batch_budget", "needs_approval")}}
        if not pl["to_fetch"]:
            self._ledger("product", None, len(pl["cached"]), 0, 0, "SOLO_CACHE", len(pl["cached"]))
            return out
        if pl["needs_approval"]:
            if not (isinstance(approved_tokens, int) and not isinstance(approved_tokens, bool) and approved_tokens >= pl["estimated_tokens"] and approved_tokens <= cfg["hard_cap"]):
                out.update(needs_approval=True, explanation=explain("KEEPA_PRESUPUESTO_EXCEDIDO"), message="Consumo previsto %d tokens > presupuesto del lote %d (tope absoluto %d). Aprueba indicando approved_tokens ≥ %d." % (pl["estimated_tokens"], cfg["batch_budget"], cfg["hard_cap"], pl["estimated_tokens"]))
                return out
        elif approved_tokens is not None and not (isinstance(approved_tokens, int) and approved_tokens >= 0):
            raise ValueError("approved_tokens inválido")
        spent = 0; budget = max(approved_tokens or 0, cfg["batch_budget"]) if pl["needs_approval"] else cfg["batch_budget"]
        by_dom = {}
        for it in pl["to_fetch"]:
            by_dom.setdefault(it["country"], []).append(it["asin"])
        stop = None
        for c, asins in by_dom.items():
            for i in range(0, len(asins), cfg["chunk"]):
                chunk = asins[i:i + cfg["chunk"]]
                if stop:
                    out["pending"] += [{"country": c, "asin": a, "reason": stop[0], "eta_minutes": stop[1]} for a in chunk]; continue
                need = pl["per_asin"] * len(chunk)
                if spent + need > budget:
                    out["pending"] += [{"country": c, "asin": a, "reason": "PRESUPUESTO_DEL_LOTE", "eta_minutes": None} for a in chunk]; continue
                left, rate = self.tokens.get("left"), self.tokens.get("rate")
                if left is not None and left < need and (self.clock() - (self.tokens.get("at") or 0)) > 20:  # saldo conocido y ANTIGUO: se refresca (GET /token no consume tokens)
                    try:
                        self.token_status(); left, rate = self.tokens.get("left"), self.tokens.get("rate")
                    except KeepaError:
                        pass
                if left is not None and left < need:
                    eta = round((need - left) / rate, 1) if rate else None
                    if wait and eta is not None and eta <= 2:
                        self.sleep(eta * 60)
                    else:
                        stop = ("KEEPA_SIN_TOKENS", eta); out["pending"] += [{"country": c, "asin": a, "reason": stop[0], "eta_minutes": eta} for a in chunk]; continue
                try:
                    j = self._request("/product", {"domain": DOMAINS[c], "asin": ",".join(chunk), "history": int(history), "stats": 90, "rating": int(rating)}, est=need)
                except KeepaError as e:
                    self._ledger("product", DOMAINS[c], len(chunk), need, None, e.code, 0, "incierto" if e.code in ("KEEPA_TIMEOUT",) or e.code.startswith("KEEPA_HTTP_5") else None)
                    if e.code == "KEEPA_HTTP_429":
                        eta = round(max(self.tokens.get("refill_in_ms") or 60000, 1) / 60000.0, 1); stop = (e.code, eta)
                        out["pending"] += [{"country": c, "asin": a, "reason": e.code, "eta_minutes": eta} for a in chunk]; continue
                    if e.code in ("KEEPA_DESACTIVADO", "KEEPA_SIN_CLAVE", "KEEPA_HTTP_401", "KEEPA_HTTP_402"):
                        out["errors"].append({"code": e.code, "explanation": explain(e.code)}); stop = (e.code, None)
                        out["pending"] += [{"country": c, "asin": a, "reason": e.code, "eta_minutes": None} for a in chunk]; continue
                    out["errors"].append({"country": c, "code": e.code, "explanation": explain(e.code)})
                    out["pending"] += [{"country": c, "asin": a, "reason": e.code, "eta_minutes": None} for a in chunk]; continue
                consumed = j.get("tokensConsumed"); spent += consumed if isinstance(consumed, int) else need; out["tokens_consumed"] += consumed if isinstance(consumed, int) else 0
                got = {str(p.get("asin")).upper(): p for p in (j.get("products") or []) if isinstance(p, dict)}
                self._ledger("product", DOMAINS[c], len(chunk), need, consumed, "OK" if len(got) == len(chunk) else "INCOMPLETA", 0, None if len(got) == len(chunk) else "faltan %d de %d" % (len(chunk) - len(got), len(chunk)))
                now = self.clock()
                for a in chunk:
                    if a in got:
                        rec = normalize_product(got[a], c, DOMAINS[c], now); self._cache_put(DOMAINS[c], a, self._params(history, rating), rec); out["products"].append(rec)
                    else:  # respuesta incompleta: NO se inventa, queda NO DISPONIBLE
                        out["pending"].append({"country": c, "asin": a, "reason": "RESPUESTA_INCOMPLETA", "eta_minutes": None})
        return out

    def search(self, country, term, approved_tokens=None):
        """Búsqueda por título (coste alto: ver search_cost). Devuelve ASIN candidatos; hay que confirmarlos antes de usarlos como competidores."""
        cfg = self.cfg_fn(); c = str(country).upper()
        if c not in DOMAINS:
            raise KeepaError("KEEPA_DOMINIO_NO_SOPORTADO")
        t, susp = sanitize_text(term, 80)
        if not t:
            raise ValueError("término vacío")
        est = cfg["search_cost"]
        if est > cfg["batch_budget"] and not (isinstance(approved_tokens, int) and not isinstance(approved_tokens, bool) and est <= approved_tokens <= cfg["hard_cap"]):
            return {"needs_approval": True, "estimated_tokens": est, "explanation": explain("KEEPA_PRESUPUESTO_EXCEDIDO")}
        j = self._request("/search", {"domain": DOMAINS[c], "type": "product", "term": t}, est=est)
        self._ledger("search", DOMAINS[c], 0, est, j.get("tokensConsumed"), "OK", 0, t[:40])
        res = []
        for p in (j.get("products") or [])[:20]:
            ti, s = sanitize_text(p.get("title")); res.append({"asin": str(p.get("asin") or ""), "title": ti, "brand": sanitize_text(p.get("brand"), 60)[0], "injection_suspect": s, "status": "CANDIDATO_SIN_CONFIRMAR"})
        recs = []
        for p in (j.get("products") or [])[:20]:
            r = normalize_product(p, c, DOMAINS[c], self.clock()); r["source"] = "Keepa API /search (api.keepa.com)"; r["status"] = "CANDIDATO_SIN_CONFIRMAR"; recs.append(r)
            if r.get("price") is not None:  # solo se guarda como dato lo que trae precio observado; el resto queda como candidato sin datos
                self._cache_put(DOMAINS[c], r["asin"], "search", r)
        return {"country": c, "term": t, "candidates": res, "records": recs, "tokens_consumed": j.get("tokensConsumed"), "tokens_left": j.get("tokensLeft"), "raw_response": j}

    # ---- lectura local / exportación --------------------------------------------------------------
    def cached_records(self, country=None):
        with self.store.lock:
            rows = self.store.db.execute("SELECT data FROM keepa_cache ORDER BY fetched_at DESC").fetchall()
        recs = [json.loads(r["data"]) for r in rows]
        return [r for r in recs if not country or r["country"] == country]

    def ledger(self, limit=100):
        with self.store.lock:
            rows = self.store.db.execute("SELECT * FROM keepa_ledger ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    COLS = ["country", "marketplace", "asin", "brand", "title", "url", "volume_ml", "units", "volume_source", "price", "currency", "price_source", "price_list", "bsr", "bsr_category_name", "bsr_date", "rating", "reviews", "offers_new", "available", "seller", "history_points_price", "fetched_at", "source", "evidence_quality", "injection_suspect"]

    def export_csv(self, country=None):
        return self.export_csv_records(self.cached_records(country))

    def export_csv_records(self, records):
        buf = io.StringIO(); w = csv.writer(buf); w.writerow(self.COLS)
        for r in records:
            row = {**r, "history_points_price": r["history_points"]["price"], "bsr_category_name": (r.get("bsr_category") or {}).get("name")}
            w.writerow([("NO DISPONIBLE" if row.get(c) is None else row.get(c)) for c in self.COLS])
        return buf.getvalue()

    def export_json(self, country=None):
        return json.dumps({"exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.clock())), "source": "Keepa API (caché local)", "records": self.cached_records(country)}, ensure_ascii=False, indent=1)
