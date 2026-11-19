#!/usr/bin/env python3
"""Amazon Pro Intelligence V0.3 — servidor local endurecido (hereda las garantías de V0.2 y añade API autenticada).

Garantías (verificadas en tests/security_test.py):
  * Escucha SOLO en 127.0.0.1.
  * Sirve únicamente una lista blanca de archivos estáticos (index.html, styles.css, js/*.js).
  * Conectores externos DESHABILITADOS por defecto. Se habilitan explícitamente con
    AMAZON_PRO_CONNECTORS="keepa,sp-api,ads" (lista). Sin eso no se hace ninguna llamada de red.
  * La prueba de un conector es POST + cabecera X-Admin-Token + Origin/Host locales + JSON + límite de frecuencia.
  * Ninguna respuesta contiene secretos: solo se informa de qué variables FALTAN (nombres, nunca valores).
  * Toda llamada saliente pasa por guarded_request(): lista blanca de operaciones de SOLO LECTURA.
    No existe código para cambiar precios, campañas ni publicaciones.
Uso: python3 server.py [puerto]
"""
import csv, hashlib, hmac, io, json, os, re, secrets, sys, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend import api_k4 as API4K, api6 as API6, api7 as API7, ai as AI, coworkers as COW, engine as ENG, pilot as PILOT, synthetic as SY, envfile as ENVF, keepa as KP, activcore as AC, eu as EU, eu_director as EUD, catalog as CT, discovery as DSC, k3 as K3M, k3_service as K3S
from backend.director import Director
from backend.store import Store, Forbidden

ROOT = os.path.dirname(os.path.abspath(__file__))
HOST = os.environ.get("AMAZON_PRO_BIND", "127.0.0.1")   # V1.0 cloud: 0.0.0.0 detrás del proxy HTTPS del proveedor
PUBLIC_HOST = (os.environ.get("AMAZON_PRO_PUBLIC_HOST") or os.environ.get("RENDER_EXTERNAL_HOSTNAME") or "").strip().lower()   # p. ej. mi-app.onrender.com (sin esquema)
CLOUD = bool(PUBLIC_HOST)
STAGING = os.environ.get("AMAZON_PRO_STAGING") == "1"   # entorno de auditoría: datos sintéticos, SOLO LECTURA, sin servicios de pago
STAGING_LABEL = "STAGING — DATOS SINTÉTICOS — SOLO LECTURA"
FORBIDDEN_ENV = ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "SPAPI_CLIENT_ID", "SPAPI_CLIENT_SECRET", "SPAPI_REFRESH_TOKEN",
                 "ADS_CLIENT_ID", "ADS_CLIENT_SECRET", "ADS_REFRESH_TOKEN", "H10_API_KEY")


def staging_guard():
    """STAGING no arranca si hay claves de servicios de pago, y fuerza IA/Keepa/trabajador desactivados. Devuelve las variables prohibidas encontradas (solo nombres)."""
    bad = [k for k in FORBIDDEN_ENV if os.environ.get(k)]
    if bad:
        return bad
    os.environ["AMAZON_PRO_AI_ENABLE"] = "0"; os.environ["AMAZON_PRO_KEEPA_ENABLE"] = "0"; os.environ["AMAZON_PRO_NO_WORKER"] = "1"
    return []


if STAGING and staging_guard():
    sys.exit("STAGING: variables de servicios de pago presentes (" + ", ".join(staging_guard()) + "). No se arranca. Elimínalas del entorno de staging.")

CONNECTORS = {
    "sp-api": {"label": "Amazon SP-API", "env": ["SPAPI_CLIENT_ID", "SPAPI_CLIENT_SECRET", "SPAPI_REFRESH_TOKEN"],
               "note": "Prueba de solo lectura: token LWA + marketplaceParticipations (EU)."},
    "ads": {"label": "Amazon Ads API", "env": ["ADS_CLIENT_ID", "ADS_CLIENT_SECRET", "ADS_REFRESH_TOKEN"],
            "note": "Prueba de solo lectura: token LWA + GET /v2/profiles (EU)."},
    "keepa": {"label": "Keepa", "env": ["KEEPA_API_KEY"], "note": "Prueba de solo lectura: GET /token."},
    "helium10": {"label": "Helium 10", "env": ["H10_API_KEY"], "note": "Sin API pública verificada: usar importación CSV."},
}
TESTABLE = {"sp-api", "ads", "keepa"}

# ---- Única vía de salida a Internet: lista blanca de operaciones de SOLO LECTURA ----------------
# (La única operación POST es el intercambio del refresh_token por un access_token LWA: no modifica nada comercial.)
READ_ONLY_ALLOW = [
    ("GET", "api.keepa.com", "/token"),
    ("POST", "api.amazon.com", "/auth/o2/token"),
    ("GET", "sellingpartnerapi-eu.amazon.com", "/sellers/v1/marketplaceParticipations"),
    ("GET", "advertising-api-eu.amazon.com", "/v2/profiles"),
]


class Blocked(Exception):
    pass


def _open(req, timeout):  # punto de sustitución en tests (sin red)
    return urllib.request.urlopen(req, timeout=timeout)


def guarded_request(method, url, data=None, headers=None, timeout=15):
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or not any(method == m and u.hostname == h and u.path == p for m, h, p in READ_ONLY_ALLOW):
        raise Blocked("operación no permitida (solo lectura)")
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with _open(req, timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def _lwa(prefix):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": os.environ[prefix + "_REFRESH_TOKEN"],
                                   "client_id": os.environ[prefix + "_CLIENT_ID"], "client_secret": os.environ[prefix + "_CLIENT_SECRET"]}).encode()
    _, txt = guarded_request("POST", "https://api.amazon.com/auth/o2/token", body, {"Content-Type": "application/x-www-form-urlencoded"})
    return json.loads(txt)["access_token"]


def run_test(name):
    """Devuelve (ok, código_fijo). NUNCA devuelve texto de excepciones (podrían contener secretos)."""
    try:
        if name == "keepa":
            s, t = guarded_request("GET", "https://api.keepa.com/token?key=" + urllib.parse.quote(os.environ.get("KEEPA_API_KEY") or os.environ.get("KEEPA_KEY") or ""))
            return s == 200 and "tokensLeft" in t, "KEEPA_HTTP_%d" % s
        if name == "sp-api":
            s, _ = guarded_request("GET", "https://sellingpartnerapi-eu.amazon.com/sellers/v1/marketplaceParticipations", headers={"x-amz-access-token": _lwa("SPAPI")})
            return s == 200, "SPAPI_HTTP_%d" % s
        if name == "ads":
            s, _ = guarded_request("GET", "https://advertising-api-eu.amazon.com/v2/profiles",
                                   headers={"Authorization": "Bearer " + _lwa("ADS"), "Amazon-Advertising-API-ClientId": os.environ["ADS_CLIENT_ID"]})
            return s == 200, "ADS_HTTP_%d" % s
        return False, "SIN_PRUEBA"
    except Blocked:
        return False, "BLOQUEADO_SOLO_LECTURA"
    except urllib.error.HTTPError as e:
        return False, "HTTP_%d" % e.code
    except Exception:  # noqa — deliberadamente sin detalle
        return False, "ERROR_DE_RED_O_RESPUESTA"


# ---- Estado --------------------------------------------------------------------------------------
LAST = {}
STATE = {"admin_token": None, "recent": [], "cool": {}}


def enabled_connectors():
    if STAGING: return set()   # staging: ningún conector activo, pase lo que pase con las variables
    return {x.strip() for x in os.environ.get("AMAZON_PRO_CONNECTORS", "").split(",") if x.strip()} & set(CONNECTORS)


def status():
    en = enabled_connectors(); out = []
    for k, c in CONNECTORS.items():
        missing = [e for e in c["env"] if not os.environ.get(e)]
        if k == "helium10":
            st = "SIN API VERIFICADA"
        elif k not in en:
            st = "DESHABILITADO (por defecto)"
        elif missing:
            st = "HABILITADO · SIN CREDENCIALES"
        elif k in LAST:
            st = "CONECTADO (prueba real OK)" if LAST[k]["ok"] else "ERROR EN PRUEBA"
        else:
            st = "HABILITADO · SIN PROBAR"
        out.append({"id": k, "label": c["label"], "enabled": k in en, "status": st, "missing": missing if k in en else [e for e in c["env"]],
                    "note": c["note"], "testable": k in TESTABLE and k in en and not missing, "last_test": LAST.get(k)})
    return {"connectors": out, "write_actions": "NO IMPLEMENTADAS (solo lectura)", "default": "conectores deshabilitados"}


# ---- Estado V0.3 ---------------------------------------------------------------------------------
APP = {"store": None, "director": None, "cfg_fn": AI.config, "login_fail": {}}
CSV_FIELDS = ["name", "asin", "priceGross", "shipping", "packUnits", "contentValue", "source", "date", "rating", "reviews"]
MAX_BODY = 1_500_000
KIND_WRITE = {"dossier"}


def parse_competitors_csv(text):
    """CSV de competidores → (filas, avisos). Acepta ',' o ';'. Nunca inventa: celdas vacías → None y el motor las excluirá con motivo."""
    text = text.lstrip("﻿")
    first = text.splitlines()[0] if text.strip() else ""
    delim = ";" if first.count(";") > first.count(",") else ","
    rd = csv.DictReader(io.StringIO(text), delimiter=delim)
    cols = {(c or "").strip(): c for c in (rd.fieldnames or [])}
    warns = []
    missing = [c for c in ("name", "priceGross", "packUnits", "contentValue", "source", "date") if c not in cols]
    if missing:
        return [], ["Faltan columnas obligatorias: " + ", ".join(missing)]
    rows = []
    for ln, r in enumerate(rd, start=2):
        if len(rows) >= 500:
            warns.append("Límite de 500 filas: resto ignorado"); break
        def f(k):
            v = (r.get(cols.get(k, k)) or "").strip()
            if v == "":
                return None
            try:
                return float(v.replace(",", ".")) if (delim == ";" or v.count(",") == 1 and "." not in v) else float(v)
            except ValueError:
                warns.append(f"Línea {ln}: «{k}» no numérico ({v[:20]}) → vacío"); return None
        row = {"name": (r.get(cols["name"]) or "").strip()[:120], "asin": (r.get(cols.get("asin", "asin")) or "").strip()[:20], "priceGross": f("priceGross"), "shipping": f("shipping") if "shipping" in cols else 0,
               "packUnits": f("packUnits"), "contentValue": f("contentValue"), "source": (r.get(cols["source"]) or "").strip()[:120], "date": (r.get(cols["date"]) or "").strip()[:10]}
        for k in ("rating", "reviews"):
            if k in cols:
                row[k] = f(k)
        rows.append(row)
    return rows, warns


# ---- HTTP ----------------------------------------------------------------------------------------
STATIC_OK = re.compile(r"^/(js/[a-z0-9_\-]+\.js)$")
if STAGING: READ_ONLY_ALLOW = []   # staging: ninguna salida a Internet
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8"}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
SEC = {"Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
       "Cross-Origin-Resource-Policy": "same-origin", "Cache-Control": "no-store"}
if CLOUD: SEC["Strict-Transport-Security"] = "max-age=31536000"
COOKIE = "apisid"


class H(BaseHTTPRequestHandler):
    server_version = "AmazonPro/0.3"
    sys_version = ""

    def _send(self, code, body=b"", ctype="application/json", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        for k, v in {**SEC, **({"X-Env": "staging"} if STAGING else {}), **(extra or {})}.items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code=200, extra=None):
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode(), extra=extra)

    def _local_origin_ok(self):
        port = self.server.server_address[1]
        allowed_hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
        if CLOUD:   # solo el nombre público configurado, por HTTPS (el proxy del proveedor termina TLS)
            if (self.headers.get("Host") or "").lower() != PUBLIC_HOST or self.headers.get("X-Forwarded-Proto", "https") != "https":
                return False
            o = self.headers.get("Origin")
            return o is None or o == "https://" + PUBLIC_HOST
        if (self.headers.get("Host") or "") not in allowed_hosts:   # protege contra DNS rebinding
            return False
        o = self.headers.get("Origin")
        return o is None or o in {f"http://{h}" for h in allowed_hosts}

    def _token(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == COOKIE:
                return v
        return None

    def _sess(self, write=False, logout=False):
        s = APP["store"].session(self._token())
        if not s:
            self._json({"error": "sesión requerida"}, 401); return None
        if s["role"] == "viewer":   # SOLO LECTURA: nunca escribe; para leer se comporta como administrador (sin secretos: el admin tampoco los ve)
            if write and not logout:
                return self._viewer_denied()
            if write:   # cerrar su propia sesión: permitido, con CSRF
                if not hmac.compare_digest(self.headers.get("X-CSRF-Token") or "", s["csrf"]):
                    self._json({"error": "CSRF inválido"}, 403); return None
                return s
            s = {**s, "role": "admin", "viewer": True}
            return s
        if write and not hmac.compare_digest(self.headers.get("X-CSRF-Token") or "", s["csrf"]):
            self._json({"error": "CSRF inválido"}, 403); return None
        return s

    def _viewer_denied(self):
        try: APP["store"].audit(None, "viewer", "viewer.write_blocked", {"method": self.command, "path": urllib.parse.urlparse(self.path).path[:120]})
        except Exception: pass
        return self._json({"error": "solo lectura: el rol viewer no puede modificar ni ejecutar nada"}, 403) and None

    def _body(self):
        if (self.headers.get("Content-Type") or "").split(";")[0].strip() != "application/json":
            self._json({"error": "se requiere application/json"}, 415); return None
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                self._json({"error": "cuerpo demasiado grande"}, 413); return None
            b = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(b, dict):
                raise ValueError
            return b
        except Exception:
            self._json({"error": "JSON inválido"}, 400); return None

    def _acct(self, s, aid):
        if not isinstance(aid, str) or not APP["store"].can_access(s, aid):
            self._json({"error": "cuenta no permitida"}, 403); return None
        return aid

    # -------- GET --------
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); path = u.path; q = urllib.parse.parse_qs(u.query)
        if path == "/healthz":   # sin datos: solo para la comprobación de salud del proveedor
            return self._json({"ok": True})
        if not self._local_origin_ok():
            return self._json({"error": "origen no permitido"}, 403)
        if path == "/api/status":
            return self._json(status())
        if path.startswith("/api/"):
            return self._api_get(path, q)
        if path in ("/", "/index.html"):
            f = "index.html"
        elif path == "/styles.css":
            f = "styles.css"
        elif path == "/favicon.ico":
            return self._send(204)
        else:
            m = STATIC_OK.match(path)
            f = m.group(1) if m else None
        if not f or not os.path.isfile(os.path.join(ROOT, f)):
            return self._json({"error": "no encontrado"}, 404)
        with open(os.path.join(ROOT, f), "rb") as fh:
            body = fh.read()
        if STAGING and f == "index.html":   # etiqueta permanente, incrustada en el HTML (visible incluso antes de iniciar sesión)
            body = body.replace(b"<!--ENV-BANNER-->", ('<div id="envBanner" class="envbanner" role="status">' + STAGING_LABEL + '</div>').encode()).replace(b"<body>", b'<body class="staging">', 1)
        self._send(200, body, TYPES[os.path.splitext(f)[1]])

    do_HEAD = do_GET

    def _v06(self, method, path, q, b, s):
        if s.get("viewer") and method != "GET":   # segunda barrera
            return self._json({"error": "solo lectura"}, 403)
        try:
            r = (API7 if path.startswith("/api/v07/") else API4K if path.startswith("/api/k4/") else API6).handle(APP, s, method, path, q, b)
        except PermissionError as e:
            return self._json({"error": str(e) or "no permitido"}, 403)
        except LookupError:
            return self._json({"error": "no encontrado"}, 404)
        except (ValueError, TypeError, KeyError) as e:
            return self._json({"error": str(e)[:240] or "petición inválida"}, 400)
        except Exception:
            return self._json({"error": "error interno"}, 500)
        if isinstance(r, tuple) and r and r[0] == "raw":
            return self._send(200, r[1], r[2], r[3])
        return self._json(r)

    def _api_get(self, path, q):
        st = APP["store"]
        if path.startswith(("/api/v06/", "/api/v07/", "/api/k4/")):
            s = self._sess()
            if not s:
                return
            return self._v06("GET", path, q, None, s)
        if path.startswith(("/api/eu/", "/api/keepa/", "/api/catalog", "/api/discovery")):
            return self._eu_get(path, q)
        if path not in ("/api/me", "/api/accounts", "/api/ai/status", "/api/ai/usage", "/api/ai/calls", "/api/coworkers/status", "/api/records", "/api/audit", "/api/news"):
            return self._json({"error": "no encontrado"}, 404)
        if path == "/api/me":
            s = st.session(self._token())
            return self._json({"user": s["username"], "role": s["role"], "csrf": s["csrf"]} if s else {"user": None})
        s = self._sess()
        if not s:
            return
        g = lambda k: (q.get(k) or [None])[0]
        if path == "/api/accounts":
            return self._json({"accounts": st.accounts_for(s)})
        if path == "/api/ai/usage":
            if s["role"] != "admin":
                return self._json({"error": "solo administrador"}, 403)
            u = APP["store"].ai_usage(); c = APP["cfg_fn"](); u["monthly_budget"] = c["monthly_budget"]; u["currency"] = c["currency"]
            u["pending_reconcile"] = u["uncertain_calls"]; u["remaining"] = None if c["monthly_budget"] is None else round(c["monthly_budget"] - u["real_cost"], 8)
            return self._json(u)
        if path == "/api/ai/calls":  # registro mínimo de llamadas: estado, duración, tokens, coste estimado (sin secretos ni textos)
            if s["role"] != "admin":
                return self._json({"error": "solo administrador"}, 403)
            return self._json({"calls": APP["store"].ai_calls(50)})
        if path == "/api/ai/status":
            return self._json(AI.public_status(APP["cfg_fn"]()))
        if path in ("/api/coworkers/status", "/api/records", "/api/audit", "/api/news"):
            aid = self._acct(s, g("account"))
            if not aid:
                return
            if path == "/api/coworkers/status":
                return self._json({**APP["director"].coworker_status(aid), "defs": {c: {"name": COW.NAMES[c], "depends_on": COW.DEPS[c]} for c in COW.ORDER}})
            if path == "/api/audit":
                return self._json({"audit": st.audit_list(aid, 200), "chain": dict(zip(("ok", "entries", "broken_at"), st.verify_audit()))})
            if path == "/api/news":  # SOLO noticias verificadas: con fuente+URL+fecha y verificadas por un aprobador
                items = [r for r in st.list(aid, "news", 100) if r["data"].get("status") == "verificada" and r["data"].get("url") and r["data"].get("source") and r["data"].get("date")]
                return self._json({"news": items, "rule": "Solo se muestran noticias con fuente, URL y fecha verificadas por un aprobador"})
            kind = g("kind")
            if kind not in {"brand", "product", "dossier", "dataset", "evidence", "task", "ai_run", "query", "approval", "news", "cost_doc", "plan"}:
                return self._json({"error": "tipo inválido"}, 400)
            if kind == "ai_run":  # no se devuelve el texto completo en listados largos
                pass
            return self._json({"records": st.list(aid, kind, min(int(g("limit") or 100), 300))})
        return self._json({"error": "no encontrado"}, 404)

    # -------- V0.4.0: inteligencia europea ACTIVCORE + Keepa --------
    def _eu_get(self, path, q):
        s = self._sess()
        if not s:
            return
        g = lambda k: (q.get(k) or [None])[0]; svc, kp = APP["eu"], APP["keepa"]
        if path.startswith("/api/keepa/"):
            if s["role"] != "admin":
                return self._json({"error": "solo administrador"}, 403)
            if path == "/api/keepa/status":
                return self._json({**KP.public_status(KP.config(APP["keepa_env"]())), "tokens": {k: v for k, v in kp.tokens.items() if k != "at"}})
            if path == "/api/keepa/ledger":
                return self._json({"ledger": kp.ledger(100)})
            if path == "/api/keepa/export":
                c = (g("country") or "").upper() or None
                if g("fmt") == "json":
                    return self._send(200, kp.export_json(c).encode(), "application/json", {"Content-Disposition": "attachment; filename=keepa_cache.json"})
                return self._send(200, kp.export_csv(c).encode("utf-8-sig"), "text/csv; charset=utf-8", {"Content-Disposition": "attachment; filename=keepa_cache.csv"})
            return self._json({"error": "no encontrado"}, 404)
        if path.startswith("/api/catalog"):
            return self._catalog_get(path, g, s)
        if path.startswith("/api/discovery"):
            return self._disc_get(path, g, s)
        try:
            svc = svc_for(g("product"))
        except ValueError as e:
            return self._json({"error": str(e)}, 404)
        if not self._acct(s, svc.account):
            return
        if path == "/api/eu/overview":
            return self._json({"product": svc.product, "card": svc.card, "product_id": svc.pid, "category_checklist": svc.category, "norm_unit": "100 mL" if svc.norm == "ml" else "100 unidades", "settings": svc.settings(), "ranking": svc.ranking(), "coworkers": svc.coworker_panel(), "presets": EU.PRESETS,
                               "criteria": {k: {"name": EU.CRIT_NAME[k], "formula": EU.FORMULAS[k]} for k in EU.CRITERIA},
                               "keepa": KP.public_status(KP.config(APP["keepa_env"]())), "claims": [{"claim": c[0], "state": c[1], "why": c[2], "evidence": c[3]} for c in svc.claims], "usable_claims": AC.USABLE if svc.legacy else [],
                               "checklist": [{"id": i, "text": t, "ref": r} for i, t, r in svc.items], "compliance": svc.compliance(), "names": EU.NAMES, "market": EU.MARKET, "account": svc.account,
                               "discovery": APP["disc"].last_run(svc.pid), "completeness": APP["catalog"].completeness(svc.card or APP["catalog"].get(svc.pid)), "pvp_scenarios": svc.pvps})
        if path == "/api/eu/economics":
            c = (g("country") or "ES").upper(); a = svc.assumptions()
            if c not in a:
                return self._json({"error": "país desconocido"}, 400)
            try:
                pvp = float(g("pvp") or svc.settings()["pvp_ref"] or 0)
            except ValueError:
                return self._json({"error": "pvp inválido"}, 400)
            return self._json({"country": c, "assumptions": a[c], "scenarios": svc.economics_table()[c], "sensitivity": EU.sensitivity(a[c], pvp, svc.settings()["acos_target"]) if c not in EU.CURRENCY and pvp > 0 else {"status": "NO CALCULABLE", "missing": ["tipo de cambio" if pvp > 0 else "PVP de referencia"]}, "labels": EU.LABEL})
        if path == "/api/eu/benchmark":
            c = (g("country") or "DE").upper(); s_ = svc.settings(); recs = svc.scoped_records(c)
            return self._json({"country": c, "keepa_supported": c in KP.DOMAINS, "benchmark": EU.benchmark(recs, svc.registry().get(c, {}), include_suggested=s_["include_suggested"], norm=svc.norm) if recs else None,
                               "note": None if c in KP.DOMAINS else "Keepa no cubre este marketplace: NO EVALUABLE por esta vía"})
        if path.startswith("/api/eu/k3"):
            if not K3S.disponible(svc):
                return self._json({"disponible": False, "motivo": "Este producto no tiene perfil de segmentación K3 (hoy: cosmética capilar / cuero cabelludo)."})
            k3s = K3S.K3Service(APP["store"], svc)
            if path == "/api/eu/k3":
                return self._json(k3s.resumen({k: g(k) for k in ("segmento", "subgrupo", "origen", "country", "activo", "min_ml", "max_ml", "aplicacion")}))
            if path == "/api/eu/k3/explicar":
                key = str(g("key") or "").upper() if not str(g("key") or "").startswith("INF:") else g("key")
                row = next((r for r in k3s.rows()[0] if r["key"] == key), None)
                return self._json({"key": key, "explicacion": K3M.explain(row), "fila": row} if row else {"error": "producto no encontrado"}, 200 if row else 404)
            if path == "/api/eu/k3/consultas":
                return self._json(K3M.plan_consultas(k3s.seg.cfg))
            return self._json({"error": "no encontrado"}, 404)
        if path == "/api/eu/export":
            what = g("what"); fn = {"benchmark": svc.csv_benchmark, "economics": svc.csv_economics, "ranking": svc.csv_ranking}.get(what)
            if not fn:
                return self._json({"error": "exportación desconocida"}, 400)
            return self._send(200, fn().encode("utf-8-sig"), "text/csv; charset=utf-8", {"Content-Disposition": "attachment; filename=%s_%s_EU.csv" % (svc.pid, what.upper())})
        return self._json({"error": "no encontrado"}, 404)

    def _keepa_granted(self, kp, b, fn):
        """K1: con aprobación obligatoria, la aprobación (approved_tokens ≤ tope) es un permiso VERIFICABLE a nivel de llamada; sin ella no sale nada."""
        at = b.get("approved_tokens")
        if kp.cfg_fn()["require_approval"] and not (isinstance(at, int) and not isinstance(at, bool) and at >= 1):
            raise KP.KeepaError("KEEPA_SIN_APROBACION")
        if isinstance(at, int) and not isinstance(at, bool) and at >= 1:
            with kp.grant(at): return fn()
        return fn()

    def _eu_post(self, path, b, s):
        kp, role, actor = APP["keepa"], s["role"], s["username"]
        if path.startswith("/api/keepa/"):
            if role != "admin":
                return self._json({"error": "solo administrador"}, 403)
            try:
                if path == "/api/keepa/test":
                    return self._json({"ok": True, **kp.token_status()})
                items = [(str(i.get("country")), str(i.get("asin"))) for i in (b.get("items") or []) if isinstance(i, dict)][:200]
                if path == "/api/keepa/plan":
                    return self._json(kp.plan(items, history=b.get("history") is not False, rating=b.get("rating") is True))
                if path == "/api/keepa/fetch":
                    return self._json(self._keepa_granted(kp, b, lambda: kp.fetch(items, history=b.get("history") is not False, rating=b.get("rating") is True, approved_tokens=b.get("approved_tokens"))))
                if path == "/api/keepa/search":
                    return self._json(self._keepa_granted(kp, b, lambda: kp.search(str(b.get("country")), str(b.get("term")), approved_tokens=b.get("approved_tokens"))))
                if path == "/api/keepa/importar-evidencia":
                    from backend import keepa_k1 as K1
                    pid_ = str(b.get("product") or "PRD-ACTIVCORE-V2"); svc_ = APP["eu"]; r = K1.importar_evidencia(kp, pid_, APP["catalog"].get(pid_), register=lambda c, a, n, sc, why, src: svc_.register_candidate(c, a, n, sc, why, src, actor)); APP["store"].audit(None, actor, "keepa.import_evidence", {"product": b.get("product"), "n": r.get("importados")}); return self._json(r)
            except KP.KeepaError as e:
                return self._json({"ok": False, "error": e.code, "explanation": KP.explain(e.code)}, 200)
            return self._json({"error": "no encontrado"}, 404)
        if path.startswith("/api/catalog"):
            return self._catalog_post(path, b, s)
        if path.startswith("/api/discovery"):
            return self._disc_post(path, b, s)
        try:
            svc = svc_for(b.get("product"))
        except ValueError as e:
            return self._json({"error": str(e)}, 404)
        if not self._acct(s, svc.account):
            return
        if path == "/api/eu/director":
            if not isinstance(b.get("question"), str) or not b["question"].strip() or len(b["question"]) > 1000:
                return self._json({"error": "pregunta requerida (≤1000 caracteres)"}, 400)
            return self._json(EUD.EUDirector(APP["store"], svc, APP["cfg_fn"]).ask(actor, b["question"], confirm=b.get("confirm"), dry_run=b.get("dry_run") is True, use_ai=b.get("use_ai") is not False and role in ("approver", "admin")))
        if role not in ("approver", "admin"):
            return self._json({"error": "solo aprobador/administrador"}, 403)
        if path == "/api/eu/assumption":
            return self._json({"ok": True, "assumption": svc.set_assumption(b.get("country"), b.get("field"), b.get("value"), b.get("status"), b.get("source"), actor)})
        if path == "/api/eu/hypotheses":
            cs = [str(c).upper() for c in (b.get("countries") or [])]; vals = b.get("values") if isinstance(b.get("values"), dict) else EU.HYPOTHESIS_EXAMPLE
            svc.load_hypotheses(cs, vals, actor); return self._json({"ok": True, "label": "Valores cargados como HIPÓTESIS (no verificadas)"})
        if path == "/api/eu/settings":
            return self._json({"ok": True, "settings": svc.set_settings(b, actor)})
        if path == "/api/eu/k3/revision":
            if not K3S.disponible(svc):
                return self._json({"error": "producto sin perfil K3"}, 400)
            try:
                return self._json({"ok": True, "revision": K3S.K3Service(APP["store"], svc).review(b.get("key"), b.get("decision"), b.get("segmento"), b.get("motivo"), actor)})
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
        if path == "/api/eu/competitor":
            return self._json({"ok": True, "competitor": svc.set_competitor(b.get("country"), b.get("asin"), b.get("comparability"), actor, b.get("note") or "")})
        if path == "/api/eu/compliance":
            return self._json({"ok": True, "item": svc.set_compliance(b.get("country"), b.get("item"), b.get("state"), b.get("evidence"), actor)})
        return self._json({"error": "no encontrado"}, 404)

    # -------- V0.5.0: catálogo y descubrimiento --------
    def _catalog_get(self, path, g, s):
        cat = APP["catalog"]
        if path == "/api/catalog":
            return self._json({"categories": cat.categories(), "products": [{**p, "missing": cat.completeness(p)} for p in cat.list(include_archived=g("archived") == "1", category=g("category"))], "statuses": list(CT.STATUSES), "languages": list(CT.LANGS), "reg_states": list(CT.REG_STATES), "countries": list(EU.VAT)})
        if path == "/api/catalog/product":
            p = cat.get(g("id"))
            if not p:
                return self._json({"error": "producto inexistente"}, 404)
            return self._json({"product": p, "versions": cat.versions(p["id"]), "missing": cat.completeness(p), "discovery": APP["disc"].last_run(p["id"])})
        return self._json({"error": "no encontrado"}, 404)

    def _catalog_post(self, path, b, s):
        if s["role"] not in ("approver", "admin"):
            return self._json({"error": "solo aprobador/administrador"}, 403)
        cat, actor = APP["catalog"], s["username"]
        if path == "/api/catalog/product":
            prod = cat.create(b, actor)
            try:
                auto = APP["autostart"](prod["id"], actor)  # F4: al registrar un producto arranca solo su expediente comercial (N1)
            except Exception as e:  # noqa: BLE001 — el alta nunca falla por el arranque automático
                auto = {"error": str(e)[:160]}
            return self._json({"ok": True, "product": prod, "autostart": auto})
        if path == "/api/catalog/update":
            return self._json({"ok": True, "product": cat.update(str(b.get("id")), b.get("patch") or {}, actor, b.get("note") or "")})
        if path == "/api/catalog/archive":
            return self._json({"ok": True, "product": cat.archive(str(b.get("id")), b.get("archived") is not False, actor)})
        if path == "/api/catalog/category":
            return self._json({"ok": True, "category": cat.set_category(b.get("id"), b.get("name"), b.get("normalization"), b.get("subcategories"), b.get("checklist") or "GENERICA", actor)})
        return self._json({"error": "no encontrado"}, 404)

    def _disc_get(self, path, g, s):
        try:
            if path == "/api/discovery/plan":
                cs = [c for c in (g("countries") or "").upper().split(",") if c] or None
                return self._json(APP["disc"].plan(g("product"), cs, g("depth") or "normal", int(g("max") or 20)))
            if path == "/api/discovery/last":
                return self._json({"last": APP["disc"].last_run(g("product"))})
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        return self._json({"error": "no encontrado"}, 404)

    def _disc_post(self, path, b, s):
        if s["role"] != "admin":
            return self._json({"error": "solo administrador (consume tokens de Keepa)"}, 403)
        try:
            if path == "/api/discovery/run":
                cs = [str(c).upper() for c in (b.get("countries") or [])] or None
                return self._json(APP["disc"].run(str(b.get("product")), s["username"], cs, b.get("depth") or "normal", int(b.get("max") or 20), b.get("approved_tokens")))
            if path == "/api/discovery/manual":
                return self._json({"ok": True, **APP["disc"].manual(str(b.get("product")), b.get("country"), [str(a) for a in (b.get("asins") or [])], s["username"], b.get("approved_tokens"))})
        except KP.KeepaError as e:
            return self._json({"ok": False, "error": e.code, "explanation": KP.explain(e.code)})
        return self._json({"error": "no encontrado"}, 404)

    # -------- POST --------
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if not self._local_origin_ok():
            return self._json({"error": "origen no permitido"}, 403)
        if STAGING and path == "/api/connectors/test":   # staging: no existen conectores que probar
            return self._json({"error": "staging: conectores deshabilitados"}, 403)
        if path not in ("/api/login", "/api/logout"):   # BLOQUEO CENTRAL (denegación por defecto): cualquier POST de un viewer, sea cual sea la ruta
            _v = APP["store"].session(self._token())
            if _v and _v["role"] == "viewer":
                return self._viewer_denied()
        if path == "/api/connectors/test":
            return self._connector_test()
        if path == "/api/login":
            b = self._body()
            if b is None:
                return
            ip = self.client_address[0]; k = ip + "|" + str(b.get("username"))[:40]; now_ = time.time()
            fails = [t for t in APP["login_fail"].get(k, []) if now_ - t < 60]
            if len(fails) >= 5:
                return self._json({"error": "demasiados intentos; espera"}, 429, {"Retry-After": "60"})
            r = APP["store"].login(str(b.get("username") or ""), str(b.get("password") or ""))
            if not r:
                APP["login_fail"][k] = fails + [now_]
                return self._json({"error": "credenciales inválidas"}, 401)
            s = APP["store"].session(r["token"])
            return self._json({"user": s["username"], "role": s["role"], "csrf": r["csrf"]}, extra={"Set-Cookie": f"{COOKIE}={r['token']}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800" + ("; Secure" if CLOUD else "")})
        if not path.startswith("/api/"):
            return self._json({"error": "no encontrado"}, 404)
        s = self._sess(write=True, logout=(path == "/api/logout"))
        if not s:
            return
        if path == "/api/logout":
            APP["store"].logout(self._token())
            return self._json({"ok": True}, extra={"Set-Cookie": f"{COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0" + ("; Secure" if CLOUD else "")})
        b = self._body()
        if b is None:
            return
        try:
            return self._api_post(path, b, s)
        except Forbidden:
            return self._json({"error": "prohibido"}, 403)
        except ValueError as e:
            return self._json({"error": str(e)[:200]}, 400)
        except Exception:
            return self._json({"error": "error interno"}, 500)

    def _api_post(self, path, b, s):
        st, dr = APP["store"], APP["director"]
        role = s["role"]
        if path.startswith(("/api/v06/", "/api/v07/", "/api/k4/")):
            return self._v06("POST", path, {}, b, s)
        if path.startswith(("/api/eu/", "/api/keepa/", "/api/catalog", "/api/discovery")):
            return self._eu_post(path, b, s)
        if path == "/api/accounts":
            if role != "admin":
                return self._json({"error": "solo administrador"}, 403)
            if not all(isinstance(b.get(k), str) and b[k].strip() for k in ("id", "name", "legal_entity")) or not re.fullmatch(r"[a-z0-9\-]{3,40}", b["id"]):
                return self._json({"error": "id (a-z0-9-), name y legal_entity obligatorios"}, 400)
            st.create_account(b["id"], b["name"][:80], b["legal_entity"][:120], (b.get("seller_central_ref") or None), b.get("marketplaces") or ["amazon.es"], actor=s["username"])
            return self._json({"ok": True})
        if path == "/api/ai/reconcile":  # el admin fija el coste REAL (del panel de OpenAI) de una reserva incierta
            if role != "admin":
                return self._json({"error": "solo administrador"}, 403)
            try:
                st.reconcile(str(b.get("id") or ""), b.get("actual_cost"), actor=s["username"])
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "usage": st.ai_usage()})
        aid = self._acct(s, b.get("account"))
        if not aid:
            return
        actor = s["username"]
        if path == "/api/dossiers":
            d = b.get("dossier")
            if not isinstance(d, dict) or "econ" not in d or "product" not in d:
                return self._json({"error": "expediente inválido"}, 400)
            full = ENG.create_empty(d["product"].get("regType", "cosmetico"), (d.get("logistics") or {}).get("mode", "FBA"))
            for k in ("product", "econ", "competitors", "keywords", "claims", "regulatory", "content", "logistics", "listing", "pvpScenarios", "cvrPct", "adBudgetMonth", "ownRating", "costDocs", "notes"):
                if k in d:
                    full[k] = d[k]
            full["econ"] = {**ENG.DEFAULTS, **full["econ"]}
            origin = PILOT.derive_origin(full, b.get("origin") if b.get("origin") in ("USUARIO", "DEMO", "PRUEBA") else "USUARIO")
            i = st.put(aid, "dossier", {"name": str(b.get("name") or full["product"].get("name") or "Expediente")[:100], "origin": origin, "brand": b.get("brand"), "pilot": ((st.get(aid, b["id"]) or {}).get("data") or {}).get("pilot") if b.get("id") else None, "dossier": full}, id_=b.get("id"), key=str(b.get("name") or "")[:100] or None, actor=actor)
            return self._json({"id": i})
        if path == "/api/pilot/phivital/init":
            ex = [r for r in st.list(aid, "dossier", 50) if r["data"].get("pilot") == "phivital-magnesio"]
            if ex:
                return self._json({"id": ex[0]["id"], "existing": True})
            i = st.put(aid, "dossier", {"name": "PHIVITAL Magnesio · piloto", "origin": "INCOMPLETO", "pilot": "phivital-magnesio", "dossier": PILOT.template()}, key="phivital-magnesio", actor=actor)
            return self._json({"id": i, "existing": False})
        if path == "/api/dossiers/evaluate":
            rec = st.get(aid, str(b.get("id")))
            if not rec or rec["kind"] != "dossier":
                return self._json({"error": "expediente inexistente"}, 404)
            ev = PILOT.assess(rec["data"]["dossier"], b.get("today") or time.strftime("%Y-%m-%d", time.gmtime()))
            dd = rec["data"]["dossier"]; prices = {round(float(x), 2) for x in (dd.get("pvpScenarios") or []) if isinstance(x, (int, float))}
            if isinstance(dd["econ"].get("price"), (int, float)): prices.add(round(dd["econ"]["price"], 2))
            mp_ = (ev["sections"].get("minPrice") or {}).get("commercial")
            if mp_: prices.add(mp_)
            ev["scenarios"] = ENG.scenarios(dd["econ"], sorted(prices)) if len(prices) < 15 else []
            st.audit(aid, actor, "dossier.evaluate", {"id": rec["id"], "decision": ev["decision"], "counts": ev["counts"]})
            return self._json({"evaluation": ev})
        if path == "/api/competitors/import":
            rec = st.get(aid, str(b.get("dossier")))
            if not rec or rec["kind"] != "dossier":
                return self._json({"error": "expediente inexistente"}, 404)
            csv_text = b.get("csv")
            if not isinstance(csv_text, str) or len(csv_text) > 1_000_000:
                return self._json({"error": "csv requerido (≤1 MB)"}, 400)
            rows, warns = parse_competitors_csv(csv_text)
            if not rows:
                return self._json({"error": "CSV sin filas válidas", "warnings": warns}, 400)
            data = rec["data"]; data["dossier"]["competitors"] = rows
            h = hashlib.sha256(csv_text.encode()).hexdigest()
            did = st.put(aid, "dataset", {"type": "competidores_csv", "rows": len(rows), "sha256": h, "dossier": rec["id"], "warnings": warns, "filename": str(b.get("filename") or "")[:100]}, actor=actor, key=h[:16])
            st.put(aid, "evidence", {"type": "csv_competidores", "dataset": did, "sha256": h, "source": "importación CSV del usuario", "at": time.strftime("%Y-%m-%d", time.gmtime())}, actor=actor)
            st.put(aid, "dossier", data, id_=rec["id"], actor=actor)
            return self._json({"imported": len(rows), "warnings": warns, "dataset": did, "evaluation_preview": ENG.benchmark(data["dossier"], time.strftime("%Y-%m-%d", time.gmtime()))["n"]})
        if path == "/api/director/ask":
            if not isinstance(b.get("question"), str) or not b["question"].strip() or len(b["question"]) > 1000:
                return self._json({"error": "pregunta requerida (≤1000 caracteres)"}, 400)
            r = dr.analyze(aid, str(b.get("dossier")), actor, b["question"], b.get("coworkers") if isinstance(b.get("coworkers"), list) else None, confirm=b.get("confirm"))
            return self._json(r)
        if path == "/api/approvals":
            rec = st.get(aid, str(b.get("dossier")))
            if not rec:
                return self._json({"error": "expediente inexistente"}, 404)
            ev = PILOT.assess(rec["data"]["dossier"], time.strftime("%Y-%m-%d", time.gmtime()))
            i = st.put(aid, "approval", {"dossier": rec["id"], "status": "pendiente", "requested_by": actor, "decision_at_request": ev["decision"], "note": str(b.get("note") or "")[:300], "scope": "Solicitud de lanzamiento (NO ejecuta ninguna acción en Amazon)"}, actor=actor)
            return self._json({"id": i, "decision": ev["decision"]})
        if path == "/api/approvals/decide":
            if role not in ("approver", "admin"):
                return self._json({"error": "solo aprobador/administrador"}, 403)
            a = st.get(aid, str(b.get("id")))
            if not a or a["kind"] != "approval" or a["data"]["status"] != "pendiente":
                return self._json({"error": "aprobación inexistente o ya resuelta"}, 404)
            dec = b.get("decision")
            if dec not in ("aprobada", "rechazada"):
                return self._json({"error": "decision inválida"}, 400)
            rec = st.get(aid, a["data"]["dossier"])
            cur = PILOT.assess(rec["data"]["dossier"], time.strftime("%Y-%m-%d", time.gmtime()))["decision"]
            if dec == "aprobada" and cur != "GO":
                return self._json({"error": f"no se puede aprobar: la evaluación actual es {cur}"}, 409)
            if a["data"]["requested_by"] == actor and dec == "aprobada":
                return self._json({"error": "el solicitante no puede aprobar su propia solicitud"}, 409)
            a["data"].update({"status": dec, "decided_by": actor, "decision_now": cur, "reason": str(b.get("reason") or "")[:300]})
            st.put(aid, "approval", a["data"], id_=a["id"], actor=actor)
            return self._json({"ok": True, "status": dec})
        if path == "/api/news":
            for k in ("title", "url", "source", "date"):
                if not isinstance(b.get(k), str) or not b[k].strip():
                    return self._json({"error": f"{k} obligatorio"}, 400)
            if not re.fullmatch(r"https://[^\s]{4,300}", b["url"]) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", b["date"]):
                return self._json({"error": "url https y fecha AAAA-MM-DD obligatorias"}, 400)
            i = st.put(aid, "news", {"title": b["title"][:200], "url": b["url"], "source": b["source"][:100], "date": b["date"], "status": "pendiente", "added_by": actor}, actor=actor)
            return self._json({"id": i, "status": "pendiente (requiere verificación de un aprobador)"})
        if path == "/api/news/verify":
            if role not in ("approver", "admin"):
                return self._json({"error": "solo aprobador/administrador"}, 403)
            n = st.get(aid, str(b.get("id")))
            if not n or n["kind"] != "news":
                return self._json({"error": "noticia inexistente"}, 404)
            n["data"].update({"status": "verificada", "verified_by": actor}); st.put(aid, "news", n["data"], id_=n["id"], actor=actor)
            return self._json({"ok": True})
        return self._json({"error": "no encontrado"}, 404)

    def _connector_test(self):
        if (self.headers.get("Content-Type") or "").split(";")[0].strip() != "application/json":
            return self._json({"error": "se requiere application/json"}, 415)
        if not hmac.compare_digest(self.headers.get("X-Admin-Token") or "", STATE["admin_token"] or "\0"):
            return self._json({"error": "token de administrador requerido"}, 401)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 2048:
                return self._json({"error": "cuerpo demasiado grande"}, 413)
            name = json.loads(self.rfile.read(n) or b"{}").get("name")
        except Exception:
            return self._json({"error": "JSON inválido"}, 400)
        if name not in TESTABLE:
            return self._json({"error": "conector no probable"}, 404)
        if name not in enabled_connectors():
            return self._json({"error": "conector deshabilitado (AMAZON_PRO_CONNECTORS)"}, 403)
        missing = [e for e in CONNECTORS[name]["env"] if not os.environ.get(e)]
        if missing:
            return self._json({"ok": False, "detail": "FALTAN_CREDENCIALES", "missing": missing})
        now = time.time()
        STATE["recent"] = [t for t in STATE["recent"] if now - t < 60]
        if len(STATE["recent"]) >= 6 or now - STATE["cool"].get(name, 0) < 15:
            return self._json({"error": "demasiadas pruebas; espera"}, 429, {"Retry-After": "15"})
        STATE["recent"].append(now); STATE["cool"][name] = now
        ok, code = run_test(name)
        LAST[name] = {"ok": ok, "detail": code, "at": time.strftime("%Y-%m-%d %H:%M:%S")}
        self._json(LAST[name])

    def do_PUT(self):
        v = APP["store"].session(self._token()) if self._local_origin_ok() else None
        if v and v["role"] == "viewer": return self._viewer_denied()
        self._json({"error": "método no permitido"}, 405)
    do_DELETE = do_PATCH = do_PUT
    do_DELETE = do_PATCH = do_PUT

    def log_message(self, fmt, *a):
        if CLOUD:   # registro de acceso sin cookies, cabeceras ni cuerpos (el proveedor lo conserva en sus logs)
            try: print("%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), (fmt % a)[:200]), flush=True)
            except Exception: pass


def bootstrap(store, admin_password=None):
    """Primer arranque: crea usuario admin y una cuenta por defecto con titular POR CONFIRMAR (no se asume titularidad)."""
    created = None
    SY.ensure(store)  # el ÚNICO expediente sintético para la primera llamada real (idempotente)
    if not store.db.execute("SELECT 1 FROM users").fetchone():
        created = admin_password or os.environ.get("AMAZON_PRO_ADMIN_PASSWORD") or secrets.token_urlsafe(14)
        store.create_user("admin", created, "admin", [])
        store.create_account("phivital-pendiente", "PhiVital · Amazon.es", "POR CONFIRMAR (titular legal del Seller Central)", None, ["amazon.es"], actor="system")
    return created


def seed_users(store):
    """V1.0 cloud: crea usuarios adicionales SIN contraseñas en el chat. AMAZON_PRO_SEED_USERS="sergio:approver,ana:analyst"; la contraseña de cada uno va en la variable
    secreta AMAZON_PRO_PASSWORD_<NOMBRE> del panel del proveedor. Idempotente: nunca sobrescribe un usuario existente. Devuelve los nombres creados (sin contraseñas)."""
    from backend.catalog import ACCOUNT_ID as _AID
    out = []
    for item in (os.environ.get("AMAZON_PRO_SEED_USERS") or "").split(","):
        name, _, role = item.strip().partition(":")
        if not name or not name.isidentifier() or role not in ("analyst", "approver"): continue   # nunca se crean administradores por esta vía
        if store.db.execute("SELECT 1 FROM users WHERE username=?", (name,)).fetchone(): continue
        pw = os.environ.get("AMAZON_PRO_PASSWORD_" + name.upper()) or ""
        if len(pw) < 12: continue   # sin contraseña segura no se crea
        store.create_user(name, pw, role, [_AID]); out.append(name)
    return out


def seed_viewers(store):
    """Usuarios SOLO LECTURA: AMAZON_PRO_SEED_VIEWERS="auditor"; la contraseña va en el secreto AMAZON_PRO_PASSWORD_<NOMBRE> (≥12). Idempotente; nunca sobrescribe."""
    out = []
    for name in [x.strip() for x in (os.environ.get("AMAZON_PRO_SEED_VIEWERS") or "").split(",")]:
        if not name or not name.isidentifier(): continue
        if store.db.execute("SELECT 1 FROM users WHERE username=?", (name,)).fetchone(): continue
        pw = os.environ.get("AMAZON_PRO_PASSWORD_" + name.upper()) or ""
        if len(pw) < 12: continue
        store.create_user(name, pw, "viewer", []); out.append(name)
    return out


def rotate_credentials(store):
    """V1.0 cloud: recuperación del administrador y rotación de contraseñas SIN chat. El propietario cambia el secreto en el panel del proveedor y pone AMAZON_PRO_ROTATE="admin,sergio";
    al arrancar se aplican (mín. 12 caracteres), se cierran las sesiones de esos usuarios y se audita sin contraseñas. Después conviene quitar AMAZON_PRO_ROTATE (reaplicarlo es inofensivo)."""
    hechos = []
    for name in [x.strip() for x in (os.environ.get("AMAZON_PRO_ROTATE") or "").split(",") if x.strip()]:
        var = "AMAZON_PRO_ADMIN_PASSWORD" if name == "admin" else "AMAZON_PRO_PASSWORD_" + name.upper()
        try: store.rotate_password(name, os.environ.get(var) or ""); hechos.append(name)
        except (ValueError, LookupError) as e: print("rotación omitida para", name, "-", type(e).__name__, flush=True)
    return hechos


def backup_loop(db_path, every_h=24, keep=7):
    from backend import respaldo100 as RB
    d = os.environ.get("AMAZON_PRO_BACKUP_DIR") or os.path.join(os.path.dirname(db_path), "backups")
    while True:
        try:
            r = RB.respaldar(db_path, d); print("respaldo creado:", os.path.basename(r["fichero"]), r["sha256"][:12], flush=True)
            olds = sorted(f for f in os.listdir(d) if f.endswith(".db"))
            for f in olds[:-keep]:
                for x in (f, f + ".sha256"):
                    try: os.remove(os.path.join(d, x))
                    except OSError: pass
        except Exception as e:  # noqa: BLE001
            print("respaldo FALLÓ:", type(e).__name__, flush=True)
        time.sleep(every_h * 3600)


def svc_for(pid):
    """Servicio europeo del producto (contexto del catálogo). Se reconstruye en cada petición: una edición de la ficha se aplica de inmediato."""
    ctx = APP["catalog"].ctx(pid or "PRD-ACTIVCORE-V2")
    if ctx is None:
        raise ValueError("producto inexistente")
    return AC.EUService(APP["store"], APP["keepa"], ctx)


def make_server(port=8765, admin_token=None, db_path=None, cfg_fn=None, admin_password=None, keepa_env_fn=None, keepa_get=None):
    STATE["admin_token"] = admin_token or os.environ.get("AMAZON_PRO_ADMIN_TOKEN") or secrets.token_urlsafe(24)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    _dbp = db_path or os.environ.get("AMAZON_PRO_DB") or os.path.join(ROOT, "data", "amazon_pro.db")
    if _dbp != ":memory:":
        from backend import respaldo100 as _RB
        _res = _RB.aplicar_pendiente(_dbp)
        if _res: print("restauración pendiente:", "APLICADA" if _res.get("restaurado") else "RECHAZADA (" + str(_res.get("motivo"))[:120] + ")", flush=True)
        _RB.abrir_seguro(_dbp)   # V1.0: una BD dañada detiene el arranque con mensaje claro y SIN tocarla
    APP["store"] = Store(_dbp)
    APP["cfg_fn"] = cfg_fn or AI.config
    APP["director"] = Director(APP["store"], APP["cfg_fn"])
    APP["keepa_env"] = keepa_env_fn or (lambda: None)  # None → os.environ (cargado desde keepa.env al arrancar)
    APP["keepa"] = KP.Keepa(APP["store"], lambda: KP.config(APP["keepa_env"]()), get_fn=keepa_get)
    AC.ensure(APP["store"])
    APP["catalog"] = CT.Catalog(APP["store"]); APP["catalog"].ensure()
    APP["eu"] = AC.EUService(APP["store"], APP["keepa"]); APP["eudir"] = EUD.EUDirector(APP["store"], APP["eu"], APP["cfg_fn"])  # ACTIVCORE heredado (V0.4.0)
    APP["disc"] = DSC.Discovery(APP["store"], APP["keepa"], APP["catalog"], svc_for)
    APP["_svc"] = svc_for
    API6.setup(APP, svc_for)
    APP["login_fail"] = {}
    srv = ThreadingHTTPServer((HOST, port), H)
    srv.initial_admin_password = bootstrap(APP["store"], admin_password)
    srv.seeded_users = seed_users(APP["store"]) + seed_viewers(APP["store"])
    srv.rotated_users = rotate_credentials(APP["store"])
    return srv


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT") or 8765)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    if CLOUD and len(os.environ.get("AMAZON_PRO_ADMIN_PASSWORD") or "") < 12:
        sys.exit("MODO CLOUD: define el secreto AMAZON_PRO_ADMIN_PASSWORD (mínimo 12 caracteres) en el panel del proveedor. No se arranca sin él (no se imprimen contraseñas en los logs).")
    if CLOUD:   # K1: valores prudentes por defecto en la nube (el propietario puede cambiarlos en el panel; nunca activan Keepa por sí solos)
        os.environ.setdefault("AMAZON_PRO_KEEPA_REQUIRE_APPROVAL", "1"); os.environ.setdefault("AMAZON_PRO_KEEPA_MISSION_CAP", "60")
    _ef = ENVF.load()  # configuración de IA desde el archivo local seguro (fuera del proyecto)
    _kf = ENVF.load(ENVF.keepa_path())  # configuración de Keepa (fuera del proyecto)
    srv = make_server(port)
    print(f"Archivo de configuración de IA: {_ef['path']} → " + ("ENCONTRADO" if _ef["found"] else "NO existe todavía (la IA seguirá desactivada)") + (f" · ajustes cargados: {', '.join(_ef['names_loaded'])}" if _ef["names_loaded"] else ""))
    print("Archivo de configuración de Keepa: " + _kf["path"] + " → " + ("ENCONTRADO" if _kf["found"] else "NO existe todavía (Keepa desactivado)"))
    print(f"Amazon Pro Intelligence V1.0.0-candidata → " + (f"https://{PUBLIC_HOST} (modo cloud, solo HTTPS, con inicio de sesión)" if CLOUD else f"http://localhost:{port}  (solo 127.0.0.1)"))
    print("Conectores habilitados:", ", ".join(sorted(enabled_connectors())) or "NINGUNO (por defecto)")
    print("IA:", AI.public_status(AI.config())["status"])
    if srv.initial_admin_password and not CLOUD:
        print("PRIMER ARRANQUE · usuario: admin · contraseña (solo se muestra ahora):", srv.initial_admin_password)
    if CLOUD:
        print("usuarios creados desde variables secretas:", ", ".join(srv.seeded_users) or "ninguno nuevo", flush=True)
        if srv.rotated_users: print("contraseñas rotadas para:", ", ".join(srv.rotated_users), "(quita AMAZON_PRO_ROTATE cuando termines)", flush=True)
        _dbp_ = os.environ.get("AMAZON_PRO_DB") or os.path.join(ROOT, "data", "amazon_pro.db")
        threading.Thread(target=backup_loop, args=(_dbp_, float(os.environ.get("AMAZON_PRO_BACKUP_HOURS") or 24)), daemon=True).start()
    if not os.environ.get("AMAZON_PRO_ADMIN_TOKEN") and not CLOUD:
        print("Token de administrador de conectores (solo esta sesión):", STATE["admin_token"])
    if not os.environ.get("AMAZON_PRO_NO_WORKER"):  # trabajador en segundo plano: ejecuta SOLO tareas permitidas (N1/N2); lo demás espera aprobación
        def _worker():
            while True:
                time.sleep(5)
                try:
                    APP["ops"].run_next()
                except Exception:  # noqa: BLE001
                    pass
        threading.Thread(target=_worker, daemon=True).start()
    srv.serve_forever()
