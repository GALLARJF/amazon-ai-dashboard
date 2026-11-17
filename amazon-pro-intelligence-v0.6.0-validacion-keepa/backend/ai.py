"""Adaptador de proveedor de IA V0.3 (configurable y seguro).
 * La clave SOLO se lee de variables de entorno del servidor; nunca se envía al navegador, ni se registra, ni aparece en errores.
 * Proveedores: none | mock (SIMULADO, determinista, sin red) | anthropic | openai_compat.
 * Las llamadas de pago exigen además AMAZON_PRO_AI_ENABLE=1 (doble consentimiento explícito) y un presupuesto por ejecución.
 * Modo de cada ejecución: REAL (host oficial de proveedor) | PRUEBA_LOCAL (servidor local de pruebas) | SIMULADA (mock) — se registra siempre.
 * El coste es una ESTIMACIÓN: tokens (reportados por el proveedor si los hay; si no, estimados chars/4) × precios configurados por el operador.
   Si no hay precios configurados el coste es null (no se inventan tarifas)."""
import hashlib, json, os, re, socket, threading, time, urllib.parse, urllib.request, urllib.error

OFFICIAL = {"anthropic": {"api.anthropic.com"}, "openai_compat": {"api.openai.com"}, "openai": {"api.openai.com"}}
PROVIDERS = ("none", "mock", "anthropic", "openai_compat", "openai")

# Tarifas OFICIALES de OpenAI (USD por 1M tokens, tier Standard, contexto corto). Fuente: https://developers.openai.com/api/docs/pricing
# y https://developers.openai.com/api/docs/models — verificadas el 2026-11-16. Son ESTIMACIONES de referencia: la factura real manda.
# El operador puede sobrescribirlas con AMAZON_PRO_AI_PRICE_IN / _OUT. Modelos fuera de la tabla sin precio configurado → no se llama (PRECIO_DESCONOCIDO).
EXPLAIN = {
    "IA_DESHABILITADA": "La IA está desactivada (AMAZON_PRO_AI_ENABLE=0). No se ha enviado nada ni se ha cobrado nada. Para probar, cambia ese valor a 1 en tu archivo ai.env y reinicia.",
    "SIN_CLAVE": "No se encuentra la clave de OpenAI. Ejecuta CONFIGURAR_CLAVE.bat, pega la clave en ai.env y reinicia. No se ha cobrado nada.",
    "SIN_MODELO": "No hay modelo configurado. Revisa AMAZON_PRO_AI_MODEL en ai.env (p. ej. gpt-6-luna) y reinicia. No se ha cobrado nada.",
    "SIN_PROVEEDOR": "No hay proveedor de IA configurado. Revisa AMAZON_PRO_AI_PROVIDER=openai en tu archivo ai.env.",
    "SIN_PRESUPUESTO_MENSUAL": "Falta el presupuesto mensual (AMAZON_PRO_AI_MONTHLY_BUDGET) en ai.env. Sin él la app no se arriesga a gastar. No se ha cobrado nada.",
    "PRECIO_DESCONOCIDO": "El modelo configurado no tiene tarifa conocida y la app no puede controlar el gasto. Usa el perfil «economico» o define las tarifas. No se ha cobrado nada.",
    "REASONING_NO_SOPORTADO": "El nivel de razonamiento elegido no existe para ese modelo (p. ej. «none» en gpt-6.1-sol). Pon AMAZON_PRO_AI_REASONING=low. No se ha cobrado nada.",
    "HOST_NO_PERMITIDO": "La dirección del proveedor no está permitida (solo https://api.openai.com). Revisa AMAZON_PRO_AI_BASE_URL. No se ha enviado nada.",
    "PRESUPUESTO_ENTRADA_EXCEDIDO": "El texto a enviar supera el límite de tokens de entrada configurado. No se ha enviado nada.",
    "PRESUPUESTO_COSTE_EXCEDIDO": "El coste máximo posible de esta consulta supera el tope por ejecución (AMAZON_PRO_AI_MAX_COST). No se ha enviado nada.",
    "PRESUPUESTO_MENSUAL_EXCEDIDO": "Se alcanzaría el presupuesto mensual (incluye reservas inciertas). No se ha enviado nada. Revisa el gasto o concilia las llamadas inciertas.",
    "IA_OCUPADA": "Ya hay otra consulta de IA en curso. Espera a que termine y vuelve a intentarlo.",
    "PRIMERA_LLAMADA_SOLO_SINTETICO": "Por seguridad, hasta verificar la IA real solo puede enviarse a OpenAI el expediente «SINTÉTICO · PRUEBA API». Selecciónalo en el desplegable. No se ha enviado nada.",
    "IA_NO_SOLICITADA": "Esta respuesta es determinista (sin IA) porque no se solicitó la síntesis con IA.",
    "IA_CONTRADICE_DECISION_DETERMINISTA": "La IA contradecía la decisión determinista (por ejemplo, recomendaba un país o un GO que el cálculo no respalda). Se descartó su texto y se muestra el resultado determinista.",
    "CONFIRMACION_REQUERIDA": "Falta tu confirmación para la primera llamada de pago. No se ha enviado nada.",
    "HTTP_400": "OpenAI rechazó la petición (400): suele ser un ajuste no válido para ese modelo. No debería haberse cobrado nada; revisa el modelo y el razonamiento en ai.env.",
    "HTTP_401": "OpenAI no aceptó la clave (401): está mal copiada (¿espacios o comillas?), fue revocada o es de otro proyecto. Corrígela en ai.env. No se cobra nada por esto.",
    "HTTP_403": "OpenAI denegó el acceso (403): tu proyecto o clave no tiene permiso para este modelo. Revisa permisos en platform.openai.com. No se cobra nada por esto.",
    "HTTP_404": "OpenAI no encuentra el modelo (404): tu cuenta quizá no tiene acceso al modelo configurado. Ejecuta tools\\check_openai_models.py o prueba otro perfil. No se cobra nada por esto.",
    "HTTP_429": "OpenAI dice «demasiadas peticiones» o «sin saldo/límite alcanzado» (429). Comprueba en platform.openai.com → Billing que tienes crédito y límite disponible, y espera un minuto. No se cobra nada por esto.",
    "HTTP_408": "OpenAI tardó demasiado (408). El consumo queda como INCIERTO: revísalo en el panel de OpenAI y concílialo.",
    "TIMEOUT": "OpenAI no respondió a tiempo. Puede que la consulta sí se haya cobrado: queda como consumo INCIERTO (se reserva el peor caso). Revísalo en el panel de OpenAI y concílialo.",
    "ERROR_DE_RED": "No se pudo conectar con OpenAI (red, cortafuegos o DNS). Si la conexión ni llegó a salir, no se cobra nada.",
    "RESPUESTA_NO_JSON": "OpenAI (o algo en medio) devolvió una respuesta que no se entiende. Consumo INCIERTO: revísalo en el panel de OpenAI.",
    "RESPUESTA_INESPERADA": "La respuesta de OpenAI no tiene el formato esperado. Consumo INCIERTO: revísalo en el panel de OpenAI.",
    "ERROR_PROVEEDOR": "OpenAI devolvió un error en la respuesta. Consumo INCIERTO: revísalo en el panel de OpenAI.",
    "RESPUESTA_VACIA": "OpenAI respondió sin texto. Se cobró lo consumido (ver tokens); prueba otra vez o sube AMAZON_PRO_AI_MAX_OUT.",
    "ERROR_INTERNO": "Fallo interno al llamar a OpenAI. Consumo INCIERTO: revísalo en el panel de OpenAI."}


def explain(code):
    """Explicación en lenguaje llano para un código de motivo/error (nunca incluye datos sensibles)."""
    c = str(code or "")
    if c in EXPLAIN: return EXPLAIN[c]
    if c.startswith("RESPUESTA_INCOMPLETA"): return "OpenAI cortó la respuesta por llegar al máximo de tokens. Se cobró lo consumido (ver tokens). Sube AMAZON_PRO_AI_MAX_OUT si quieres respuestas más largas."
    if c.startswith("RESPUESTA_NO_ANCLADA"): return "OpenAI respondió, pero incluyó cifras que no están en los datos calculados; por seguridad se descartó y se muestra el resumen determinista. La consulta sí se cobró."
    if c.startswith("HTTP_5"): return "Fallo en los servidores de OpenAI (%s). Consumo INCIERTO: revísalo en el panel de OpenAI y concílialo." % c
    if c.startswith("HTTP_"): return "OpenAI devolvió el error %s. Revisa platform.openai.com." % c[5:]
    return c


PRICE_VERIFIED_ON = "2026-11-16"
PRICE_SOURCE = "https://developers.openai.com/api/docs/pricing"
PRICES = {  # modelo: (entrada, entrada_en_caché, salida)
    "gpt-6-luna": (0.10, 0.01, 0.50), "gpt-6.1-terra": (1.00, 0.05, 5.00),
    "gpt-6.1-sol": (2.00, 0.10, 10.00), "gpt-6-astra": (10.00, 1.00, 50.00)}
MODEL_EFFORTS = {"gpt-6-luna": ("none", "low", "medium", "high", "xhigh", "max"), "gpt-6.1-terra": ("none", "low", "medium", "high", "xhigh", "max"),
                 "gpt-6.1-sol": ("low", "medium", "high", "xhigh", "max"), "gpt-6-astra": ("low", "medium", "high", "xhigh", "max")}  # docs oficiales de modelos, 2026-11-16


def prices_age_days(today=None):
    import datetime
    t = datetime.date.fromisoformat(today) if today else datetime.date.today()
    return (t - datetime.date.fromisoformat(PRICE_VERIFIED_ON)).days


PROFILES = {"economico": "gpt-6-luna", "razonamiento": "gpt-6.1-sol", "maximo": "gpt-6-astra"}
EFFORTS = ("none", "low", "medium", "high", "xhigh", "max")
LOOPBACK = {"127.0.0.1", "localhost"}


class AIError(Exception):
    def __init__(self, code):
        super().__init__(code); self.code = code


def _post(url, headers, body, timeout):  # punto de sustitución en tests
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def est_tokens(s):
    return max(1, (len(s) + 3) // 4)


def config(env=None):
    e = os.environ if env is None else env
    prov = (e.get("AMAZON_PRO_AI_PROVIDER") or "none").strip().lower()
    if prov not in PROVIDERS:
        prov = "none"
    def f(k):
        try:
            return float(e[k]) if e.get(k) else None
        except ValueError:
            return None
    profile = (e.get("AMAZON_PRO_AI_PROFILE") or "").strip().lower() or None
    if profile not in PROFILES:
        profile = None
    default_model = "mock-determinista" if prov == "mock" else (PROFILES.get(profile or "economico") if prov == "openai" else None)
    cfg = {"provider": prov, "profile": profile, "model": e.get("AMAZON_PRO_AI_MODEL") or default_model,
           "enabled": e.get("AMAZON_PRO_AI_ENABLE") == "1", "base_url": e.get("AMAZON_PRO_AI_BASE_URL") or None,
           "price_in_per_mtok": f("AMAZON_PRO_AI_PRICE_IN"), "price_out_per_mtok": f("AMAZON_PRO_AI_PRICE_OUT"), "currency": e.get("AMAZON_PRO_AI_CURRENCY") or "USD",
           "max_output_tokens": int(f("AMAZON_PRO_AI_MAX_OUT") or 1200), "max_input_tokens": int(f("AMAZON_PRO_AI_MAX_IN") or 12000),
           "max_cost_per_run": f("AMAZON_PRO_AI_MAX_COST"), "monthly_budget": f("AMAZON_PRO_AI_MONTHLY_BUDGET"),
           "reasoning_effort": (e.get("AMAZON_PRO_AI_REASONING") or "low").strip().lower(), "allow_loopback": e.get("AMAZON_PRO_AI_ALLOW_LOOPBACK") == "1", "timeout": min(120, max(1, f("AMAZON_PRO_AI_TIMEOUT") or 40)),
           "max_concurrent": min(4, max(1, int(f("AMAZON_PRO_AI_MAX_CONCURRENT") or 1)))}
    if cfg["reasoning_effort"] not in EFFORTS:
        cfg["reasoning_effort"] = "low"
    if prov == "openai":  # defaults de seguridad: tope por ejecución siempre presente; el mensual es obligatorio para llamar
        if cfg["max_cost_per_run"] is None:
            cfg["max_cost_per_run"] = 0.05
        cfg["max_output_tokens"] = int(f("AMAZON_PRO_AI_MAX_OUT") or 2500)  # incluye tokens de razonamiento
    key_var = {"anthropic": "ANTHROPIC_API_KEY", "openai_compat": "AMAZON_PRO_AI_API_KEY", "openai": "OPENAI_API_KEY"}.get(prov)
    cfg["key_var"] = key_var
    cfg["_key"] = e.get(key_var) if key_var else None
    pi, po = prices(cfg)
    cfg["_price_in"], cfg["_price_out"], cfg["price_source"] = pi, po, ("configurado_por_operador" if cfg["price_in_per_mtok"] is not None else ("oficial_openai_%s" % PRICE_VERIFIED_ON if pi is not None else None))
    return cfg


def prices(cfg):
    """Precios efectivos (entrada, salida) USD/1M: los del operador; si no, tabla oficial verificada para el modelo; si no, None."""
    if cfg["price_in_per_mtok"] is not None and cfg["price_out_per_mtok"] is not None:
        return cfg["price_in_per_mtok"], cfg["price_out_per_mtok"]
    if cfg["provider"] == "openai" and cfg["model"] in PRICES:
        t = PRICES[cfg["model"]]; return t[0], t[2]
    return None, None


def public_status(cfg):
    """Estado para el frontend: SIN claves ni valores."""
    p = cfg["provider"]
    if p == "none":
        st, real = "SIN IA CONFIGURADA", False
    elif p == "mock":
        st, real = "PROVEEDOR SIMULADO (no es IA real)", False
    elif not cfg["_key"]:
        st, real = f"IA SIN CLAVE ({cfg['key_var']} ausente) · ejecuciones reales PENDIENTES", False
    elif not cfg["enabled"]:
        st, real = "CLAVE PRESENTE · IA DESHABILITADA (AMAZON_PRO_AI_ENABLE≠1)", False
    elif not cfg["model"]:
        st, real = "FALTA AMAZON_PRO_AI_MODEL", False
    elif p == "openai" and cfg["_price_in"] is None:
        st, real = "MODELO SIN TARIFA CONOCIDA: configura AMAZON_PRO_AI_PRICE_IN/OUT", False
    elif p == "openai" and cfg["monthly_budget"] is None:
        st, real = "FALTA AMAZON_PRO_AI_MONTHLY_BUDGET (presupuesto mensual obligatorio)", False
    else:
        st, real = "IA CONFIGURADA · sin ejecución real verificada aún", True
    return {"provider": p, "model": cfg["model"], "status": st, "can_call": real or p == "mock", "key_present": bool(cfg["_key"]), "key_format_ok": (bool(cfg["_key"]) and cfg["_key"].startswith("sk-") and len(cfg["_key"]) >= 20 and not any(c.isspace() or c in "\"'" for c in cfg["_key"])) if cfg["_key"] else None, "enabled": cfg["enabled"],
            "prices_verified_on": PRICE_VERIFIED_ON if cfg["provider"] == "openai" else None, "prices_stale": cfg["provider"] == "openai" and prices_age_days() > 45, "prices_configured": cfg["_price_in"] is not None, "price_source": cfg["price_source"], "profile": cfg["profile"], "currency": cfg["currency"],
            "budget": {"max_output_tokens": cfg["max_output_tokens"], "max_input_tokens": cfg["max_input_tokens"], "max_cost_per_run": cfg["max_cost_per_run"], "monthly_budget": cfg["monthly_budget"]}}


def cost(cfg, tin, tout):
    pi, po = cfg.get("_price_in"), cfg.get("_price_out")
    if pi is None:
        pi, po = prices(cfg)
    if pi is None or po is None:
        return None
    return (tin * pi + tout * po) / 1e6


def _mode(cfg, url):
    h = urllib.parse.urlparse(url).hostname
    if cfg["provider"] == "mock":
        return "SIMULADA"
    if h in LOOPBACK:
        return "PRUEBA_LOCAL"
    return "REAL"


def _endpoint(cfg):
    if cfg["provider"] == "anthropic":
        return "https://api.anthropic.com/v1/messages" if not cfg["base_url"] else cfg["base_url"].rstrip("/") + "/v1/messages"
    base = (cfg["base_url"] or "https://api.openai.com").rstrip("/")
    return base + ("/v1/responses" if cfg["provider"] == "openai" else "/v1/chat/completions")


def _host_ok(cfg, url):
    u = urllib.parse.urlparse(url); h = u.hostname
    if h in LOOPBACK:
        return cfg["allow_loopback"] and u.scheme in ("http", "https")
    extra = {x.strip() for x in (os.environ.get("AMAZON_PRO_AI_HOSTS") or "").split(",") if x.strip()}
    return u.scheme == "https" and h in (OFFICIAL.get(cfg["provider"], set()) | extra)


def _mock_answer(system, user):
    """Respuesta SIMULADA: extractiva a partir de los hechos del prompt. No es razonamiento de un modelo."""
    facts = re.findall(r"^\[(F\d+)\] (.+)$", user, re.M)
    body = "\n".join(f"- {t} [{i}]" for i, t in facts[:12]) or "- No hay hechos suficientes."
    return "RESPUESTA SIMULADA (proveedor mock, no es IA real). Resumen extractivo de los hechos verificados:\n" + body


def complete(cfg, system, user, month_spent=0.0, ledger=None):
    """Ejecuta una llamada. Devuelve dict con text/model/provider/mode/tokens/cost/duration_ms. Lanza AIError(code) con códigos fijos."""
    p = cfg["provider"]
    if p == "none":
        raise AIError("SIN_PROVEEDOR")
    tin_est = est_tokens(system + user)
    if tin_est > cfg["max_input_tokens"]:
        raise AIError("PRESUPUESTO_ENTRADA_EXCEDIDO")
    est_cost = cost(cfg, tin_est, cfg["max_output_tokens"])
    if cfg["max_cost_per_run"] is not None and est_cost is not None and est_cost > cfg["max_cost_per_run"]:
        raise AIError("PRESUPUESTO_COSTE_EXCEDIDO")
    t0 = time.time()
    if p == "mock":
        text = _mock_answer(system, user)
        return {"text": text, "model": cfg["model"], "provider": p, "mode": "SIMULADA", "tokens_in": tin_est, "tokens_out": est_tokens(text), "token_source": "estimado",
                "cost": cost(cfg, tin_est, est_tokens(text)), "duration_ms": int((time.time() - t0) * 1000), "endpoint": None}
    if not cfg["_key"]:
        raise AIError("SIN_CLAVE")
    if not cfg["enabled"]:
        raise AIError("IA_DESHABILITADA")
    if not cfg["model"]:
        raise AIError("SIN_MODELO")
    url = _endpoint(cfg)
    if not _host_ok(cfg, url):
        raise AIError("HOST_NO_PERMITIDO")
    if p == "openai" and cfg["model"] in MODEL_EFFORTS and cfg["reasoning_effort"] not in MODEL_EFFORTS[cfg["model"]]:
        raise AIError("REASONING_NO_SOPORTADO")  # p. ej. «none» no existe en gpt-6.1-sol / gpt-6-astra
    token = None; real = _mode(cfg, url) == "REAL"
    if p == "openai":  # presupuestos obligatorios ANTES de gastar: peor caso = entrada estimada + salida máxima (incluye razonamiento)
        if cfg["_price_in"] is None:
            raise AIError("PRECIO_DESCONOCIDO")
        if cfg["monthly_budget"] is None:
            raise AIError("SIN_PRESUPUESTO_MENSUAL")
        worst = cost(cfg, tin_est, cfg["max_output_tokens"])
        if cfg["max_cost_per_run"] is not None and worst > cfg["max_cost_per_run"]:
            raise AIError("PRESUPUESTO_COSTE_EXCEDIDO")
        if not _acquire(cfg):
            raise AIError("IA_OCUPADA")  # límite de llamadas simultáneas (por defecto 1): sin colas ni reintentos automáticos
        try:
            ledger = ledger if ledger is not None else MemoryLedger(month_spent)
            token = ledger.reserve(worst, cfg["monthly_budget"], real, cfg["model"])  # ATÓMICO: comprueba y descuenta en una sola operación
            if token is None:
                raise AIError("PRESUPUESTO_MENSUAL_EXCEDIDO")
        except BaseException:
            _release_slot(); raise
    try:
        res = _call(cfg, system, user, url, tin_est, t0, ledger, token, real)
        res["text"] = _redact(cfg, res["text"]); return res
    except AIError as e:
        if getattr(e, "partial", None): e.partial["text"] = _redact(cfg, e.partial.get("text") or "")
        raise
    except BaseException:  # cualquier fallo no clasificado tras la reserva: consumo INCIERTO (se cobra el peor caso hasta conciliar)
        if token is not None: ledger.uncertain(token, "EXCEPCION_NO_CLASIFICADA")
        raise AIError("ERROR_INTERNO")
    finally:
        if p == "openai": _release_slot()


def _redact(cfg, text):
    """Defensa en profundidad: si un proveedor (o un intermediario) devolviera la clave dentro del texto, nunca se guarda ni se muestra."""
    k = cfg.get("_key")
    return text.replace(k, "[CLAVE-OCULTA]") if k and len(k) >= 8 and isinstance(text, str) else text


def _call(cfg, system, user, url, tin_est, t0, ledger, token, real):
    p = cfg["provider"]
    def fin(kind, actual=None, note=""):  # cierra la reserva: settle | uncertain | release
        if token is None: return
        if kind == "settle": ledger.settle(token, actual, note)
        elif kind == "uncertain": ledger.uncertain(token, note)
        else: ledger.release(token, note)
    if p == "anthropic":
        hdr = {"x-api-key": cfg["_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"}
        body = {"model": cfg["model"], "max_tokens": cfg["max_output_tokens"], "system": system, "messages": [{"role": "user", "content": user}]}
    elif p == "openai":
        hdr = {"Authorization": "Bearer " + cfg["_key"], "content-type": "application/json"}
        body = {"model": cfg["model"], "instructions": system, "input": user, "max_output_tokens": cfg["max_output_tokens"], "store": False, "reasoning": {"effort": cfg["reasoning_effort"]}}
    else:
        hdr = {"Authorization": "Bearer " + cfg["_key"], "content-type": "application/json"}
        body = {"model": cfg["model"], "max_tokens": cfg["max_output_tokens"], "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    try:
        status, raw = _post(url, hdr, json.dumps(body).encode(), cfg["timeout"])
    except urllib.error.HTTPError as e:
        # 4xx (400/401/403/404/429…): la petición fue RECHAZADA, no se factura → se libera la reserva. 408/409 y 5xx: estado desconocido → incierto.
        if 400 <= e.code < 500 and e.code not in (408, 409):
            fin("release", note="HTTP_%d" % e.code)
        else:
            fin("uncertain", note="HTTP_%d" % e.code)
        raise AIError("HTTP_%d" % e.code)  # el cuerpo del error no se registra (puede contener datos de cuenta)
    except urllib.error.URLError as e:
        # rechazo de conexión / DNS: la petición nunca llegó → liberar. Resto (timeout, reset): pudo procesarse → incierto.
        if isinstance(e.reason, (ConnectionRefusedError, socket.gaierror)):
            fin("release", note="SIN_CONEXION"); raise AIError("ERROR_DE_RED")
        fin("uncertain", note="RED_" + type(e.reason).__name__); raise AIError("TIMEOUT" if isinstance(e.reason, (socket.timeout, TimeoutError)) else "ERROR_DE_RED")
    except (TimeoutError, socket.timeout):
        fin("uncertain", note="TIMEOUT"); raise AIError("TIMEOUT")
    except OSError:
        fin("uncertain", note="RED_OSError"); raise AIError("ERROR_DE_RED")
    try:
        j = json.loads(raw)
    except ValueError:
        fin("uncertain", note="RESPUESTA_NO_JSON"); raise AIError("RESPUESTA_NO_JSON")
    try:
        if p == "openai":
            if j.get("error"):
                fin("uncertain", note="ERROR_PROVEEDOR"); raise AIError("ERROR_PROVEEDOR")
            parts = [c.get("text", "") for it in j.get("output", []) if it.get("type") == "message" for c in it.get("content", []) if c.get("type") == "output_text"]
            text = "".join(parts)
            u = j.get("usage") or {}
            tin, tout = u.get("input_tokens"), u.get("output_tokens"); src = "reportado_por_proveedor"
            rt = (u.get("output_tokens_details") or {}).get("reasoning_tokens")
            if not isinstance(tin, int) or not isinstance(tout, int) or tin < 0 or tout < 0:
                tin, tout, src = tin_est, cfg["max_output_tokens"], "estimado_peor_caso"  # sin uso fiable: se contabiliza el peor caso
            c = cost(cfg, tin, tout)
            if src != "reportado_por_proveedor":
                fin("uncertain", note="SIN_USO_REPORTADO")
            else:
                fin("settle", c, "ok")
            if j.get("status") == "incomplete":
                inc = {"text": text, "tokens_in": tin, "tokens_out": tout, "cost": c, "token_source": src}
                e = AIError("RESPUESTA_INCOMPLETA_" + str((j.get("incomplete_details") or {}).get("reason") or "desconocida")); e.partial = inc; raise e
            if not text.strip():
                e = AIError("RESPUESTA_VACIA"); e.partial = {"text": "", "tokens_in": tin, "tokens_out": tout, "cost": c, "token_source": src}; raise e
            rid = j.get("id") if isinstance(j.get("id"), str) and j.get("id") else None
            origin = bool(_mode(cfg, url) == "REAL" and status == 200 and j.get("object") == "response" and rid and src == "reportado_por_proveedor")  # HTTPS verificado + host oficial + forma de respuesta documentada + uso reportado
            return {"text": text, "model": j.get("model") or cfg["model"], "provider": p, "mode": _mode(cfg, url), "tokens_in": tin, "tokens_out": tout, "reasoning_tokens": rt,
                    "response_id": rid, "origin_verified": origin, "http_status": status, "token_source": src, "cost": c, "duration_ms": int((time.time() - t0) * 1000), "endpoint": urllib.parse.urlparse(url).hostname}
        if p == "anthropic":
            text = "".join(b.get("text", "") for b in j["content"] if b.get("type") == "text")
            tin, tout = j["usage"]["input_tokens"], j["usage"]["output_tokens"]; src = "reportado_por_proveedor"
        else:
            text = j["choices"][0]["message"]["content"]
            u = j.get("usage") or {}
            tin, tout = u.get("prompt_tokens"), u.get("completion_tokens"); src = "reportado_por_proveedor"
            if tin is None or tout is None:
                tin, tout, src = tin_est, est_tokens(text), "estimado"
    except (KeyError, IndexError, TypeError, AttributeError):
        fin("uncertain", note="RESPUESTA_INESPERADA"); raise AIError("RESPUESTA_INESPERADA")
    return {"text": text, "model": j.get("model") or cfg["model"], "provider": p, "mode": _mode(cfg, url), "tokens_in": tin, "tokens_out": tout, "token_source": src,
            "cost": cost(cfg, tin, tout), "duration_ms": int((time.time() - t0) * 1000), "endpoint": urllib.parse.urlparse(url).hostname}


# ---- control de simultaneidad y libro de presupuesto en memoria (el de producción es Store.reserve/settle/…) ----
_SLOT = {"n": 0, "lock": threading.Lock()}


def _acquire(cfg):
    with _SLOT["lock"]:
        if _SLOT["n"] >= cfg["max_concurrent"]:
            return False
        _SLOT["n"] += 1; return True


def _release_slot():
    with _SLOT["lock"]:
        _SLOT["n"] = max(0, _SLOT["n"] - 1)


class MemoryLedger:
    """Libro de presupuesto atómico en memoria (pruebas / uso sin base de datos). Misma interfaz que Store: reserve/settle/uncertain/release."""
    def __init__(self, spent=0.0):
        self.lock = threading.Lock(); self.rows = {}; self.n = 0
        if spent: self.rows["base"] = {"state": "settled", "worst": spent, "actual": spent, "real": True}
    def reserve(self, worst, budget, real, model=None):
        with self.lock:
            committed = sum((r["actual"] if r["state"] == "settled" else r["worst"]) for r in self.rows.values() if r["state"] in ("reserved", "uncertain", "settled") and r["real"] == real)
            if committed + worst > budget + 1e-12:
                return None
            self.n += 1; self.rows[self.n] = {"state": "reserved", "worst": worst, "actual": None, "real": real}; return self.n
    def settle(self, t, actual, note=""):
        with self.lock: self.rows[t].update(state="settled", actual=actual)
    def uncertain(self, t, note=""):
        with self.lock: self.rows[t]["state"] = "uncertain"
    def release(self, t, note=""):
        with self.lock: self.rows[t]["state"] = "released"
    def committed(self):
        with self.lock: return sum((r["actual"] if r["state"] == "settled" else r["worst"]) for r in self.rows.values() if r["state"] in ("reserved", "uncertain", "settled"))

NUM = re.compile(r"(?<![\w.])-?\d+(?:[.,]\d+)?")


def _numbers(s):
    out = set()
    for m in NUM.findall(s):
        try:
            out.add(round(float(m.replace(",", ".")), 4))
        except ValueError:
            pass
    return out


def grounding(answer, facts_text):
    """Heurística de anclaje: toda cifra de la respuesta debe coincidir con una cifra de los hechos suministrados (igual, o redondeada a los decimales con que se escribe).
    No prueba veracidad: detecta cifras inventadas evidentes. Devuelve {ok, ungrounded[]}."""
    allowed = _numbers(facts_text)
    ungrounded = []
    for m in NUM.findall(answer):
        try:
            v = float(m.replace(",", "."))
        except ValueError:
            continue
        if re.fullmatch(r"F\d+", m):
            continue
        d = len(m.replace(',', '.').split('.')[1]) if re.search(r'[.,]\d', m) else 0
        if any(abs(v - a) < 1e-9 or abs(round(a, d) - v) < 1e-9 for a in allowed):
            continue
        ungrounded.append(m)
    cites = set(re.findall(r"\[(F\d+)\]", answer))
    return {"ok": not ungrounded, "ungrounded": sorted(set(ungrounded))[:20], "cited": sorted(cites)}
