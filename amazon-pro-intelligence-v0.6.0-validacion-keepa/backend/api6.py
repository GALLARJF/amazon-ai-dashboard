"""V0.6 — Montaje de módulos y rutas /api/v06/*. El servidor delega aquí; las reglas de rol y CSRF las aplica server.py antes de llamar."""
import base64, json, re, time
from . import ops as O, econ6 as X, launch as L, importer as I, home as H, eu as E, keepa as KP, ai as AI
from .catalog import ACCOUNT_ID

ORDER_STEPS = [  # (tipo de tarea, etiqueta de decisión de negocio, urgencia en días, coste €)
    ("compliance.check", "¿Qué impide publicar en cada país? (requisitos y claims)", 3, 0.0),
    ("econ.recompute", "¿Es rentable el producto por país? (con los costes reales disponibles)", 7, 0.0),
    ("discovery.plan", "¿Qué mercados investigar primero y cuánto cuesta en tokens Keepa?", 7, 0.0),
    ("listing.draft", "¿Cómo presentamos el producto sin claims no respaldados?", 14, 0.0),
    ("dossier.build", "¿Lanzamos y dónde? (expediente comercial único)", 14, 0.0),
    ("discovery.run", "¿Quiénes son los competidores reales por país? (consume tokens Keepa: requiere aprobación)", 7, 0.0),
]


def setup(APP, svc_for):
    st = APP["store"]; cat = APP["catalog"]
    ops = O.Ops(st); APP["ops"] = ops
    APP["gate"] = O.ModelGate(st, ops, APP["cfg_fn"])
    APP["gate"].validators["claims_lint"] = lambda t, f="": L.lint_validator("COSMETICA")(t, f)
    la = L.Launch(cat, svc_for, APP["disc"], ops); APP["launch"] = la
    imp = I.Importer(st, cat); APP["imp"] = imp
    APP["home"] = H.Home(cat, svc_for, imp, ops, la)

    def _store_result(pid, key, data, actor="director"):
        from . import activcore as AC
        AC._upsert(st, "dossier", "%s:%s" % (key, pid), data, actor, ACCOUNT_ID)

    def h_dossier(t):
        d = la.build(t["product"], **{k: v for k, v in (t["payload"] or {}).items() if k in ("mode", "acos_target", "ads_share")})
        _store_result(t["product"], "launch", d)
        return {"sections": len(d["sections"]), "recommendation": d["recommendation"], "stored": "launch:" + t["product"]}

    def h_econ(t):
        svc = svc_for(t["product"]); p = cat.get(t["product"]); rows = X.table(svc, svc.pvp_default or None, "FBA", None, None, [c for c in E.COUNTRIES if c not in E.CURRENCY])
        ok = sum(1 for r in rows if r.get("complete"))
        _store_result(t["product"], "econ", {"rows": rows, "at": time.strftime("%Y-%m-%d")})
        return {"countries_calculated": ok, "countries_not_calculable": len(rows) - ok, "missing_example": next((r.get("missing") for r in rows if not r.get("complete")), None)}

    def h_compliance(t):
        p = cat.get(t["product"]); d = la.listing_draft(p); svc = svc_for(t["product"]); cv = la.compliance_view(svc, p, [c for c in E.COUNTRIES if c in svc.compliance()])
        if not d["lint"]["ok"]:
            ops.request_decision(t["product"], "revision_claims", "Claims bloqueados en el borrador de %s" % p["name"], {"hallazgos": [x["term"] for x in d["lint"]["findings"] if x["level"] == "BLOQUEA"]})
        return {"requisitos_abiertos": cv["open"], "claims_bloqueados": d["lint"]["blocks"], "claims_a_revisar": d["lint"]["reviews"], "veredicto": cv["verdict"]}

    def h_dplan(t):
        pl = APP["disc"].plan(t["product"], None, "normal", 20); _store_result(t["product"], "dplan", {"plan": pl, "at": time.strftime("%Y-%m-%d")})
        return {"plan_guardado": True, "tokens_estimados": pl.get("estimated_tokens_max"), "nota": "Plan calculado sin consumir tokens"}

    def h_drun(t):
        """Descubrimiento real. Respeta el tope acumulado de misión (AMAZON_PRO_KEEPA_MISSION_CAP) y los países de misión."""
        from . import keepa as K
        cfg = K.config(APP["keepa_env"]()); ctr = cfg["mission_countries"] or None; depth = "ligera" if cfg["mission_cap"] else "normal"
        pl = APP["disc"].plan(t["product"], ctr, depth, 20)
        tk = pl.get("estimated_tokens_max") or 0
        if cfg["mission_cap"]:
            tk = min(tk, APP["keepa"].mission_status()["remaining_worst_case"])
        r = APP["disc"].run(t["product"], "director", ctr, depth, 20, tk if tk >= 1 else None)
        return {"estado": r.get("status"), "detalle": {"tokens_gastados": r.get("tokens_spent"), "pendiente": len(r.get("pending") or []), "errores": [e.get("code") for e in (r.get("errors") or [])], "paises": [{k2: c.get(k2) for k2 in ("country", "status", "candidates_found", "registered", "from_search", "tokens")} for c in r.get("countries", [])]}}

    def h_listing(t):
        p = cat.get(t["product"]); d = la.listing_draft(p); _store_result(t["product"], "listing", d); return {"borrador": True, "claims_bloqueados": d["lint"]["blocks"]}

    ops.register("dossier.build", h_dossier, "construir_expediente")
    ops.register("econ.recompute", h_econ, "calcular")
    ops.register("compliance.check", h_compliance, "clasificar")
    ops.register("discovery.plan", h_dplan, "calcular")
    ops.register("discovery.run", h_drun, "llamada_keepa_nueva")
    ops.register("listing.draft", h_listing, "preparar_borrador")
    APP["autostart"] = lambda pid, actor: order_launch(APP, pid, actor, run=True)


def order_launch(APP, pid, actor, run=True):
    """Orden «prepara el lanzamiento europeo»: crea las tareas (cada una ligada a una decisión de negocio), ejecuta lo permitido (N1) y deja lo demás en la bandeja."""
    ops = APP["ops"]
    if not APP["catalog"].get(pid):
        raise ValueError("producto inexistente")
    created = []
    for kind, label, urg, cost in ORDER_STEPS:
        r = ops.add_task(kind, pid, label, {}, dedup="%s|%s|orden" % (kind, pid), urgency_days=urg, cost_eur=cost, by=actor); created.append({"kind": kind, **r})
    done = ops.run_all(limit=20, backoff_s=0) if run else []
    return {"product": pid, "tasks": created, "executed": done, "decisions_pending": [d for d in ops.decisions(product=pid)], "note": "Se ejecuta automáticamente lo de nivel N1; el gasto de tokens Keepa queda en la bandeja para tu aprobación."}


def connections(APP):
    st = APP["store"]; kcfg = KP.config(APP["keepa_env"]()); kst = KP.public_status(kcfg); ai = AI.public_status(APP["cfg_fn"]())
    with st.lock:
        kl = st.db.execute("SELECT COUNT(*) n FROM keepa_ledger").fetchone()["n"]
        rs = st.db.execute("SELECT MAX(tokens_consumed) c FROM keepa_ledger WHERE op='search' AND status='OK' AND tokens_consumed IS NOT NULL").fetchone()["c"]
    realsearch = int(rs) if rs else 0
    return {"as_of": time.strftime("%Y-%m-%d"), "rows": [
        {"name": "Keepa", "code": "IMPLEMENTADO", "configured": bool(kst.get("configured", kst.get("enabled"))), "real_calls_logged": kl, "state": "REAL VERIFICADO (PARCIAL)" if realsearch else ("REAL VERIFICADO" if kl else "NO VERIFICADO: ninguna llamada real registrada"),
         "limits": ("Verificado con llamada real: /token gratuito, /search = %d tokens (dominio ES = 9 en amazon.es). SIN verificar: coste real de /product por ASIN, códigos de DE/FR/IT/UK, ratings y vendedor. NL/PL/SE/BE/IE no cubiertos." % realsearch) if realsearch else "Costes en tokens y códigos de dominio son supuestos de documentación de terceros hasta la primera llamada real autorizada. NL/PL/SE/BE/IE no cubiertos por el conector."},
        {"name": "OpenAI / IA", "code": "IMPLEMENTADO", "configured": ai.get("status"), "real_verified": bool(st.real_ai_verified()), "state": "REAL VERIFICADO" if st.real_ai_verified() else "NO VERIFICADO (la IA real no ha respondido nunca)", "limits": "Gasto real nuevo = N3 (aprobación)."},
        {"name": "Amazon SP-API", "code": "ADAPTADOR SOLO LECTURA (probado solo con simulación)", "state": "PENDIENTE DE CONEXIÓN", "limits": "Sin credenciales: no conectado. Solo cuenta como conectada con autenticación, permisos y operación verificados por una persona."},
        {"name": "Amazon Ads API", "code": "ADAPTADOR SOLO LECTURA (probado solo con simulación)", "state": "PENDIENTE DE CONEXIÓN", "limits": "Sin credenciales: no conectado; no crea ni modifica campañas. Mientras tanto: importación de informes reales (CSV) con fecha y cobertura."},
        {"name": "Importación de informes Amazon (CSV)", "code": "IMPLEMENTADO", "reports": len(APP["imp"].reports()), "state": "MANUAL · IMPORTADO SIN MODIFICAR", "limits": "No es monitorización continua."},
        {"name": "Importación de documentación interna", "code": "IMPLEMENTADO", "state": "MANUAL", "limits": "Texto/markdown; se guarda con hash."}]}


def _need(s, *roles):
    if s["role"] not in roles:
        raise PermissionError("rol insuficiente")


def handle(APP, s, method, path, q, b):
    if s.get("viewer") and method != "GET": raise PermissionError("solo lectura (viewer)")
    g = lambda k: (q.get(k) or [None])[0]; ops = APP["ops"]; actor = s["username"]; role = s["role"]
    if not APP["store"].can_access(s, ACCOUNT_ID):
        raise PermissionError("sin acceso al catálogo")
    p = path[len("/api/v06/"):]
    if method == "GET":
        if p == "home":
            return APP["home"].build(g("product") or None)
        if p == "demo":
            return H.demo()
        if p == "launch":
            d = APP["launch"].build(g("product"), g("mode") or "FBA")
            f = g("fmt")
            if f == "md":
                return ("raw", L.to_markdown(d).encode(), "text/markdown; charset=utf-8", {"Content-Disposition": "attachment; filename=expediente_%s.md" % g("product")})
            if f == "html":
                return ("raw", L.to_html(d).encode(), "text/html; charset=utf-8", {"Content-Disposition": "attachment; filename=expediente_%s.html" % g("product")})
            return d
        if p == "tasks":
            return {"tasks": ops.tasks(product=g("product") or None, limit=100), "queue": [{"id": t["id"], "kind": t["kind"], "why": t["priority_why"]} for t in ops.queue()[:20]]}
        if p == "decisions":
            return {"decisions": ops.decisions(g("status") or "PENDIENTE", g("product") or None)}
        if p == "ledger":
            return {"ledger": ops.ledger(product=g("product") or None)}
        if p == "ops":
            return {**ops.summary(), "policies": ops.policies(), "events": ops.events(60), "actions": O.ACTION_LEVEL, "task_policy": O.TASK_POLICY}
        if p == "ai/calls":
            _need(s, "admin"); return {"calls": APP["gate"].calls(100)}
        if p == "imports":
            return {"reports": APP["imp"].reports(g("product") or None), "summary": APP["imp"].summary(g("product")) if g("product") else None}
        if p == "connections":
            return connections(APP)
        if p == "econ":
            svc = APP["_svc"](g("product")); pvp = float(g("pvp")) if g("pvp") else (svc.pvp_default or None)
            if pvp is None:
                return {"state": "NO CALCULABLE", "why": "sin PVP"}
            return {"rows": X.table(svc, pvp, g("mode") or "FBA", float(g("acos")) if g("acos") else None, float(g("ads_share")) if g("ads_share") else None, [c for c in E.COUNTRIES if c not in E.CURRENCY]), "classes": X.CLASS_HELP}
        if p == "inventory":
            f = lambda k: float(g(k)) if g(k) not in (None, "") else None
            return X.inventory(f("units_per_month"), f("lead_time_days"), f("safety_days"), f("stock"), f("moq"))
        raise LookupError(p)
    # ---------------------------------------------------------------- POST
    if p == "lint":
        return L.claims_lint(str(b.get("text") or "")[:6000], str(b.get("category") or "COSMETICA"))
    _need(s, "approver", "admin")
    if p == "order":
        return order_launch(APP, str(b.get("product")), actor, run=b.get("run") is not False)
    if p == "run":
        return {"executed": ops.run_all(limit=int(b.get("limit") or 20), backoff_s=0)}
    if p == "task":
        return ops.add_task(str(b.get("kind")), b.get("product"), str(b.get("decision") or ""), b.get("payload") or {}, urgency_days=b.get("urgency_days"), by=actor)
    if p == "task/cancel":
        ops.cancel(int(b.get("id")), actor); return {"ok": True}
    if p == "decide":
        return ops.decide(int(b.get("id")), b.get("approve") is True, actor, str(b.get("note") or ""))
    if p == "kill":
        if not b.get("on"):
            _need(s, "admin")
        return ops.kill_switch(bool(b.get("on")), actor, str(b.get("reason") or ""))
    if p == "ledger/observe":
        return ops.ledger_observe(int(b.get("id")), str(b.get("observed_result") or ""), b.get("expected"), b.get("observed"), str(b.get("lessons") or ""), str(b.get("followup") or ""))
    if p == "import":
        raw = base64.b64decode(str(b.get("content_b64") or ""), validate=True) if b.get("content_b64") else str(b.get("content") or "").encode()
        return APP["imp"].import_report(str(b.get("product")), str(b.get("filename") or "informe.csv"), raw, actor, b.get("marketplace"), b.get("kind"))
    if p == "doc":
        return APP["imp"].import_document(str(b.get("product")), str(b.get("name") or "documento"), str(b.get("text") or ""), actor)
    _need(s, "admin")
    if p == "policy":
        return {"policies": ops.set_policy(str(b.get("action")), b.get("enabled") is True, int(b.get("max_per_day") or 0), float(b.get("max_eur") or 0), b.get("reversible") is True, actor)}
    if p == "ai/pin":
        return APP["gate"].pin_model(str(b.get("tier")), str(b.get("model")), str(b.get("evidence") or ""), actor)
    raise LookupError(p)
