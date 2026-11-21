"""V1.0 (V1-13) + Corrección 4.1 — Adaptadores de SOLO LECTURA para Amazon SP-API y Amazon Ads API.
Garantías: credenciales solo desde variables de entorno (convención ÚNICA AMAZON_PRO_SPAPI_* / AMAZON_PRO_ADS_*), nunca en código ni en respuestas; 0 € de gasto;
solo GET (+ POST únicamente al endpoint de token LWA); lista blanca de rutas y de operaciones con parámetros obligatorios, paginación y límites acotados, 429 con espera controlada;
el access token LWA se obtiene en cada lectura, vive solo en una variable local y NUNCA se guarda, registra ni devuelve;
modo REAL exige credenciales completas Y AMAZON_PRO_LIVE_<SERVICIO>=1 (y, en el servidor, AMAZON_PRO_CONNECTORS); el modo SIMULADO solo habla con 127.0.0.1.
Un servicio NUNCA se declara operativo: como máximo 'CONFIGURADO · SIN VERIFICAR' hasta que una persona registre una verificación real.
No existe código para listings, precios, inventario (escritura), campañas, pujas, presupuestos ni feeds, y no se crean informes (POST): los informes de Ads se importan por CSV."""
import gzip, json, re, time, urllib.error, urllib.parse, urllib.request

class ConectorError(Exception):
    def __init__(self, msg, http=None): super().__init__(msg); self.http = http

LWA_URL = "https://api.amazon.com/auth/o2/token"
SERVICIOS = {
    "spapi": {"nombre": "Amazon SP-API", "vars": ["AMAZON_PRO_SPAPI_CLIENT_ID", "AMAZON_PRO_SPAPI_CLIENT_SECRET", "AMAZON_PRO_SPAPI_REFRESH_TOKEN"], "hosts": {"sellingpartnerapi-eu.amazon.com"},
              "token_url": LWA_URL, "live": "AMAZON_PRO_LIVE_SPAPI", "conn": "sp-api",
              "rutas": [r"^/sellers/v1/marketplaceParticipations$", r"^/orders/v0/orders$", r"^/fba/inventory/v1/summaries$", r"^/catalog/2022-04-01/items(/[A-Z0-9]{10})?$",
                        r"^/reports/2021-06-30/reports(/[0-9]{1,24})?$", r"^/reports/2021-06-30/documents/[A-Za-z0-9._\-]{1,120}$",
                        r"^/finances/v0/financialEventGroups$", r"^/finances/v0/financialEvents$", r"^/finances/2024-06-19/transactions$"]},
    "ads": {"nombre": "Amazon Ads API", "vars": ["AMAZON_PRO_ADS_CLIENT_ID", "AMAZON_PRO_ADS_CLIENT_SECRET", "AMAZON_PRO_ADS_REFRESH_TOKEN"], "hosts": {"advertising-api-eu.amazon.com"},
            "token_url": LWA_URL, "live": "AMAZON_PRO_LIVE_ADS", "conn": "ads",
            "rutas": [r"^/v2/profiles$", r"^/v2/sp/campaigns$", r"^/v2/sp/adGroups$", r"^/v2/sp/keywords$", r"^/reporting/reports/[A-Za-z0-9\-]{1,80}$"]},
}
LOOP = {"127.0.0.1", "localhost"}
DL_HOST = re.compile(r"^[a-z0-9.\-]+\.amazonaws\.com$")   # descarga de informes ya generados (URL prefirmada, solo GET, sin credenciales)
MAX_PAGES_HARD, MAX_PAGES_DEFAULT, MAX_RETRIES, MAX_WAIT_S, MAX_DL_BYTES = 5, 3, 3, 30.0, 5_000_000

# Operaciones de lectura declaradas. path: ruta (con {param} validados por patrón); req: obligatorios; any: al menos uno; opt: opcionales;
# pag: (parámetro_de_página, ruta_del_token_en_la_respuesta); lim: (parámetro_de_tamaño, máximo); ads: requiere perfil (cabecera Scope)
OPS = {
    "spapi": {
        "participations": {"path": "/sellers/v1/marketplaceParticipations", "req": [], "opt": []},
        "catalog_item": {"path": "/catalog/2022-04-01/items/{asin}", "pp": {"asin": r"[A-Z0-9]{10}"}, "req": ["marketplaceIds"], "opt": ["includedData", "locale"]},
        "catalog_search": {"path": "/catalog/2022-04-01/items", "req": ["marketplaceIds", "identifiers", "identifiersType"], "opt": ["includedData", "locale", "pageSize"], "pag": ("pageToken", "pagination.nextToken"), "lim": ("pageSize", 20)},
        "orders": {"path": "/orders/v0/orders", "req": ["MarketplaceIds"], "any": ["CreatedAfter", "LastUpdatedAfter"], "opt": ["CreatedBefore", "LastUpdatedBefore", "OrderStatuses", "FulfillmentChannels", "MaxResultsPerPage"], "pag": ("NextToken", "payload.NextToken"), "lim": ("MaxResultsPerPage", 100)},
        "inventory": {"path": "/fba/inventory/v1/summaries", "req": ["granularityType", "granularityId", "marketplaceIds"], "opt": ["details", "startDateTime", "sellerSkus"], "pag": ("nextToken", "pagination.nextToken")},
        "reports_list": {"path": "/reports/2021-06-30/reports", "req": [], "opt": ["reportTypes", "processingStatuses", "marketplaceIds", "pageSize", "createdSince", "createdUntil"], "pag": ("nextToken", "nextToken"), "lim": ("pageSize", 100)},
        "report_get": {"path": "/reports/2021-06-30/reports/{reportId}", "pp": {"reportId": r"[0-9]{1,24}"}, "req": [], "opt": []},
        "report_document": {"path": "/reports/2021-06-30/documents/{reportDocumentId}", "pp": {"reportDocumentId": r"[A-Za-z0-9._\-]{1,120}"}, "req": [], "opt": [], "redact_url": True},
        "report_download": {"path": "/reports/2021-06-30/documents/{reportDocumentId}", "pp": {"reportDocumentId": r"[A-Za-z0-9._\-]{1,120}"}, "req": [], "opt": [], "download": True},
        "finance_groups": {"path": "/finances/v0/financialEventGroups", "req": ["FinancialEventGroupStartedAfter"], "opt": ["FinancialEventGroupStartedBefore", "MaxResultsPerPage"], "pag": ("NextToken", "payload.NextToken"), "lim": ("MaxResultsPerPage", 100)},
        "finance_events": {"path": "/finances/v0/financialEvents", "req": ["PostedAfter"], "opt": ["PostedBefore", "MaxResultsPerPage"], "pag": ("NextToken", "payload.NextToken"), "lim": ("MaxResultsPerPage", 100)},
        "finance_transactions": {"path": "/finances/2024-06-19/transactions", "req": ["postedAfter"], "opt": ["postedBefore", "marketplaceId"], "pag": ("nextToken", "pagination.nextToken")},
    },
    "ads": {
        "profiles": {"path": "/v2/profiles", "req": [], "opt": [], "scope": False},
        "campaigns": {"path": "/v2/sp/campaigns", "req": ["profile_id"], "opt": ["startIndex", "count", "stateFilter"], "pag": "index", "lim": ("count", 100)},
        "adgroups": {"path": "/v2/sp/adGroups", "req": ["profile_id"], "opt": ["startIndex", "count", "stateFilter", "campaignIdFilter"], "pag": "index", "lim": ("count", 100)},
        "keywords": {"path": "/v2/sp/keywords", "req": ["profile_id"], "opt": ["startIndex", "count", "stateFilter", "adGroupIdFilter"], "pag": "index", "lim": ("count", 100)},
        "report_get": {"path": "/reporting/reports/{reportId}", "pp": {"reportId": r"[A-Za-z0-9\-]{1,80}"}, "req": ["profile_id"], "opt": [], "redact_url": True},
    },
}
SECRET_KEYS = re.compile(r"(access_token|refresh_token|client_secret|^url$|^location$|authorization)", re.I)

def _redact(o):
    if isinstance(o, dict): return {k: ("[OCULTO]" if SECRET_KEYS.search(str(k)) else _redact(v)) for k, v in o.items()}
    if isinstance(o, list): return [_redact(x) for x in o]
    return o

def _dig(o, dotted):
    for k in dotted.split("."):
        if not isinstance(o, dict): return None
        o = o.get(k)
    return o if isinstance(o, (str, int)) and o != "" else None

def catalogo_ops():
    return {s: {n: {"obligatorios": o.get("req", []), "alguno_de": o.get("any", []), "opcionales": o.get("opt", []), "paginacion": bool(o.get("pag")), "limite": o.get("lim")} for n, o in ops.items()} for s, ops in OPS.items()}

class Conector:
    def __init__(self, svc, environ=None):
        if svc not in SERVICIOS: raise ConectorError("servicio desconocido")
        self.svc, self.d = svc, SERVICIOS[svc]; self.env = environ if environ is not None else {}
    def faltan(self): return [v for v in self.d["vars"] if not str(self.env.get(v, "")).strip()]
    def live(self): return str(self.env.get(self.d["live"], "")) == "1"
    def estado(self):
        f = self.faltan()
        if f: return {"servicio": self.d["nombre"], "estado": "NO CONECTADO", "faltan": f, "operativo": False, "nota": "Sin credenciales. Se guardan como variables de entorno del servidor (Render), nunca en GitHub, Drive ni chat."}
        return {"servicio": self.d["nombre"], "estado": "CONFIGURADO · SIN VERIFICAR" + ("" if self.live() else " · LECTURA REAL DESACTIVADA"), "faltan": [], "operativo": False, "nota": "Solo una prueba real registrada por una persona permite llamarlo operativo."}
    def _ruta_ok(self, path):
        return any(re.match(p, path) for p in self.d["rutas"])

    # ---- token LWA: transitorio (variable local del llamante), nunca se guarda ni se devuelve
    def _lwa(self, post):
        v = self.d["vars"]; body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": self.env[v[2]], "client_id": self.env[v[0]], "client_secret": self.env[v[1]]}).encode()
        try: r = (post or self._post)(self.d["token_url"], body, {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
        except (urllib.error.URLError, OSError, ValueError) as e: raise ConectorError("no se pudo obtener el token LWA (%s)" % type(e).__name__, getattr(e, "code", None))
        except ConectorError: raise
        except Exception as e: raise ConectorError("no se pudo obtener el token LWA (%s)" % type(e).__name__)
        tok = r.get("access_token") if isinstance(r, dict) else None
        if not tok or not isinstance(tok, str): raise ConectorError("respuesta LWA sin access_token")
        return tok
    def _hdr(self, tok, path, profile):
        h = {"Accept": "application/json", "User-Agent": "AHT-AmazonPro/1.1 (solo lectura)"}
        if self.svc == "spapi": h["x-amz-access-token"] = tok
        else:
            h["Authorization"] = "Bearer " + tok; h["Amazon-Advertising-API-ClientId"] = self.env[self.d["vars"][0]]
            if path != "/v2/profiles":
                if not profile: raise ConectorError("Ads: falta profile_id (cabecera Amazon-Advertising-API-Scope)")
                h["Amazon-Advertising-API-Scope"] = str(profile)
        return h
    def _guard(self, modo, habilitado):
        if modo not in ("SIMULADO", "REAL"): raise ConectorError("modo inválido")
        if modo == "REAL":
            if not habilitado: raise ConectorError("conector no habilitado (AMAZON_PRO_CONNECTORS)")
            if self.faltan(): raise ConectorError("modo REAL imposible: faltan credenciales")
            if not self.live(): raise ConectorError("lectura REAL desactivada (%s != 1)" % self.d["live"])
    def _base(self, modo, base_url):
        if modo == "REAL": return "https://%s" % sorted(self.d["hosts"])[0]
        if not base_url: raise ConectorError("modo SIMULADO requiere un servidor local")
        if urllib.parse.urlsplit(base_url).hostname not in LOOP: raise ConectorError("el modo SIMULADO solo puede usar 127.0.0.1")
        return base_url.rstrip("/")
    def _fetch(self, url, hdr, transport, sleep):
        """GET con 429 controlado: hasta MAX_RETRIES esperas (Retry-After o 2^n s), cada una ≤ MAX_WAIT_S."""
        for intento in range(MAX_RETRIES + 1):
            try: return (transport or self._http)(url, hdr)
            except urllib.error.HTTPError as e:
                if e.code == 429 and intento < MAX_RETRIES:
                    try: w = float((e.headers or {}).get("Retry-After") or 0)
                    except (TypeError, ValueError): w = 0
                    sleep(min(max(w, 2 ** intento), MAX_WAIT_S)); continue
                raise ConectorError("Amazon respondió HTTP %d" % e.code, e.code)
            except (urllib.error.URLError, OSError, ValueError) as e:
                raise ConectorError("fallo de transporte: %s" % type(e).__name__)
            except ConectorError: raise
            except Exception as e: raise ConectorError("fallo de transporte: %s" % type(e).__name__)

    def get(self, path, params=None, modo="SIMULADO", base_url=None, transport=None, post=None, profile_id=None, habilitado=True, sleep=time.sleep):
        """Lectura de UNA ruta de la lista blanca (sin paginar). REAL: obtiene el token LWA, añade las cabeceras de autenticación y llama al host oficial."""
        u = urllib.parse.urlsplit(path)
        if u.scheme or u.netloc or ".." in path or not path.startswith("/"): raise ConectorError("ruta no permitida")
        if not self._ruta_ok(u.path): raise ConectorError("ruta fuera de la lista blanca de solo lectura")
        self._guard(modo, habilitado); url = self._base(modo, base_url) + u.path
        if params: url += "?" + urllib.parse.urlencode({str(k)[:40]: str(v)[:200] for k, v in list(params.items())[:10]})
        hdr = {"Accept": "application/json", "User-Agent": "AHT-AmazonPro/1.1 (solo lectura)"}
        if modo == "REAL": hdr = self._hdr(self._lwa(post), u.path, profile_id)
        body = self._fetch(url, hdr, transport, sleep)
        return {"origen": modo, "servicio": self.d["nombre"], "solo_lectura": True, "coste_eur": 0.0, "datos": _redact(body) if modo == "REAL" else body, "aviso": "SIMULADO: no proviene de Amazon" if modo == "SIMULADO" else "Dato real de solo lectura, sin verificar por una persona"}

    def leer(self, op, params=None, modo="REAL", habilitado=False, transport=None, post=None, download=None, sleep=time.sleep, base_url=None, max_pages=MAX_PAGES_DEFAULT):
        """Operación de lectura declarada en OPS: valida parámetros obligatorios, limita tamaño de página y nº de páginas, pagina y devuelve las páginas sin tokens."""
        spec = OPS[self.svc].get(op)
        if not spec: raise ConectorError("operación no permitida: %s" % str(op)[:40])
        p = {str(k): str(v) for k, v in (params or {}).items() if v not in (None, "")}
        pp = {k: p.pop(k, None) for k in spec.get("pp", {})}
        for k, rx in spec.get("pp", {}).items():
            if pp[k] is None: raise ConectorError("falta el parámetro obligatorio %s" % k)
            if not re.fullmatch(rx, pp[k]): raise ConectorError("parámetro %s inválido" % k)
        profile = p.pop("profile_id", None)
        allowed = set(spec.get("req", [])) | set(spec.get("opt", [])) | set(spec.get("any", [])); allowed.discard("profile_id")
        pagtok = spec["pag"][0] if isinstance(spec.get("pag"), tuple) else None
        if pagtok: allowed.add(pagtok)
        extra = set(p) - allowed
        if extra: raise ConectorError("parámetro no permitido: %s" % sorted(extra)[0][:40])
        for r in spec.get("req", []):
            if r == "profile_id":
                if not profile: raise ConectorError("falta el parámetro obligatorio profile_id")
            elif r not in p: raise ConectorError("falta el parámetro obligatorio %s" % r)
        if spec.get("any") and not any(a in p for a in spec["any"]): raise ConectorError("falta uno de: %s" % ", ".join(spec["any"]))
        if profile is not None and not re.fullmatch(r"\d{1,20}", profile): raise ConectorError("profile_id inválido")
        if spec.get("lim"):
            pn, mx = spec["lim"]
            try: n = int(p.get(pn, mx))
            except ValueError: raise ConectorError("%s inválido" % pn)
            p[pn] = str(max(1, min(n, mx)))
        mp = max(1, min(int(max_pages or MAX_PAGES_DEFAULT), MAX_PAGES_HARD))
        path = spec["path"].format(**pp)
        if not self._ruta_ok(path): raise ConectorError("ruta fuera de la lista blanca de solo lectura")
        self._guard(modo, habilitado)
        base = self._base(modo, base_url); tok = self._lwa(post) if modo == "REAL" else "SIMULADO"; hdr = self._hdr(tok, path, profile) if modo == "REAL" else {"Accept": "application/json"}
        pages, more = [], False
        if spec.get("download"):
            meta = self._fetch(base + path, hdr, transport, sleep)
            out = self._descargar(meta, download, modo)
            return self._cierra({"origen": modo, "servicio": self.d["nombre"], "op": op, "solo_lectura": True, "coste_eur": 0.0, "paginas": 1, "truncado": out.pop("_trunc", False), "datos": [out],
                                 "aviso": "Informe ya generado, descargado en solo lectura; sin verificar por una persona"}, tok)
        start = int(p.get("startIndex", 0)) if spec.get("pag") == "index" else 0
        for i in range(mp):
            q = dict(p)
            if spec.get("pag") == "index": q["startIndex"] = str(start)
            body = self._fetch(base + path + ("?" + urllib.parse.urlencode(q) if q else ""), hdr, transport, sleep)
            pages.append(_redact(body) if spec.get("redact_url") or modo == "REAL" else body)
            if pagtok:
                nxt = _dig(body, spec["pag"][1])
                if not nxt: break
                p[pagtok] = str(nxt)[:2000]
                if i == mp - 1: more = True
            elif spec.get("pag") == "index":
                cnt = int(p.get(spec["lim"][0], spec["lim"][1]))
                if not isinstance(body, list) or len(body) < cnt: break
                start += cnt
                if i == mp - 1: more = True
            else: break
        return self._cierra({"origen": modo, "servicio": self.d["nombre"], "op": op, "solo_lectura": True, "coste_eur": 0.0, "paginas": len(pages), "truncado": more, "datos": pages,
                             "aviso": "SIMULADO: no proviene de Amazon" if modo == "SIMULADO" else "Dato real de solo lectura, sin verificar por una persona"}, tok)
    def _cierra(self, out, tok):
        txt = json.dumps(out, ensure_ascii=False)
        secretos = [tok] + [str(self.env.get(v, "")) for v in self.d["vars"]]
        if any(s and len(s) >= 6 and s in txt for s in secretos): raise ConectorError("respuesta descartada: contenía un secreto")
        return out
    def _descargar(self, meta, download, modo):
        url = (meta or {}).get("payload", meta or {}).get("url") if isinstance(meta, dict) else None
        if modo != "REAL" and not url: raise ConectorError("sin URL de documento")
        h = urllib.parse.urlsplit(str(url or ""))
        if h.scheme != "https" or not DL_HOST.match(h.hostname or ""): raise ConectorError("URL de informe fuera de la lista blanca (https *.amazonaws.com)")
        raw = (download or self._download)(url)
        if not isinstance(raw, (bytes, bytearray)) or len(raw) > MAX_DL_BYTES: raise ConectorError("informe demasiado grande o inválido")
        if str((meta.get("payload", meta)).get("compressionAlgorithm", "")).upper() == "GZIP": raw = gzip.decompress(raw)[:MAX_DL_BYTES]
        try: txt = bytes(raw).decode("utf-8")
        except UnicodeDecodeError: txt = bytes(raw).decode("cp1252", "replace")
        lines = txt.splitlines()
        return {"lineas": len(lines), "cabecera": lines[0] if lines else "", "muestra": lines[1:51], "_trunc": len(lines) > 51}
    @staticmethod
    def _download(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "AHT-AmazonPro/1.1 (solo lectura)"}, method="GET"), timeout=30) as r: return r.read(MAX_DL_BYTES + 1)
    @staticmethod
    def _post(url, data, hdr):
        if url != LWA_URL: raise ConectorError("POST solo permitido al endpoint de token LWA")
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdr, method="POST"), timeout=15) as r: return json.loads(r.read(100_000).decode("utf-8"))
    @staticmethod
    def _http(url, hdr):
        rq = urllib.request.Request(url, headers=hdr, method="GET")
        with urllib.request.urlopen(rq, timeout=15) as r: return json.loads(r.read(2_000_000).decode("utf-8"))

def estados(environ=None):
    return [Conector(s, environ).estado() for s in SERVICIOS]
