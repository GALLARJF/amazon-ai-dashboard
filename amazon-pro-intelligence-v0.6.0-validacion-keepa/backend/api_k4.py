"""K4 · rutas /api/k4/*. El servidor ya aplicó sesión y CSRF. Roles: lectura = cualquier sesión con acceso al catálogo; escribir datos/medios/costes/propuestas = approver+; verificar derechos, validar costes y decidir = approver+; importar = approver+.
Solo lectura y cálculo; ninguna acción comercial externa."""
import base64, json, os
from . import k4_planner as KPL, k4_selection as KSEL, k4_umbrales as KUM, k4_bench as KB, k4_store as KS, k4_contracts as C, k4_costs as KC, k4_data as KD, k4_media as KM, k4_pricing as KP, k4_director as KDIR, k3_service as K3S, eu
from .catalog import ACCOUNT_ID
from .store import ROLES

PAISES = ("ES", "DE", "FR", "IT", "NL", "PL")
CANALES = ("FBA", "FBM", "TODOS")


class K4:
    def __init__(self, APP):
        st = APP["store"]; self.APP = APP; self.k = KS.K4Store(st)
        self.data = KD.Data(self.k); self.costs = KC.Costs(self.k); self.costs.seed()
        base = os.path.dirname(st.path) if st.path and st.path != ":memory:" else None
        self.media = KM.Media(self.k, base); self.dir = None; self.sel = KSEL.Selection(self.k); self.um = KUM.Umbrales(self.k)
        self.plan = KPL.Planner(self.k, {"dossier_precio": self._j_dossier, "medir_seguimiento": self._j_medir, "conciliar_datos": self._j_conciliar}, APP.get("ops"))

    def _j_dossier(self, prm, job):
        f = _filtros(lambda k: prm.get(k)); ctx, d = dictamen_completo(self.APP, self, f)
        med = self.media.resolve(f["producto"], "principal", None, "visualizar"); dos = KDIR.construir(d, ctx, med); self.director().guardar(dos, "planificador"); return {"dossier": dos["id"], "tipo": d["tipo"]}

    def _j_medir(self, prm, job):
        return self.director().medir(int(prm["id"]), "planificador")

    def _j_conciliar(self, prm, job):
        r = self.data.conciliar(_filtros(lambda k: prm.get(k)), "PRODUCCION"); return {"estado": r.get("estado")}

    def director(self):
        return KDIR.Director(self.k, self.APP["ops"], self.data)


def _k4(APP):
    if "k4" not in APP or APP["k4"].k.s is not APP["store"]: APP["k4"] = K4(APP)
    return APP["k4"]


def _need(s, role):
    if ROLES[s["role"]] < ROLES[role]: raise PermissionError("requiere rol " + role)


def _filtros(g):
    f = {"producto": g("producto") or "PRD-ACTIVCORE-V2", "pais": (g("pais") or "ES").upper(), "desde": g("desde"), "hasta": g("hasta"), "canal": g("canal"), "etapa": g("etapa") or "*"}
    if f["etapa"] not in KUM.ETAPAS: raise ValueError("etapa inválida")
    if f["pais"] not in PAISES + ("TODOS",): raise ValueError("país inválido")
    if f["canal"] and f["canal"] not in CANALES: raise ValueError("canal inválido")
    for k in ("desde", "hasta"):
        if f[k] and not C.iso_date(f[k]): raise ValueError(k + " inválida")
    if f["pais"] == "TODOS": f["pais"] = None
    if f["canal"] in (None, "TODOS"): f["canal"] = None
    return f


DEMO_PANEL = {"estadisticos": {"mediana_100ml": 110.0, "min_100ml": 90.0, "max_100ml": 140.0, "n": 4}, "n_precio_vigente": 4}


def demo_csv():
    """Datos SINTÉTICOS (entorno SINTETICO_DEMO, nunca producción): 28 días, dos niveles de precio observados."""
    import datetime
    d0 = datetime.date(2026, 10, 1); sa = ["producto,pais,fecha,unidades,ventas_netas,moneda,sesiones,pedidos,devoluciones_uds,precio_medio,canal"]; ad = ["producto,pais,fecha,gasto,ventas_ads,clics,impresiones,moneda"]; inv = ["producto,pais,fecha,stock"]
    for i in range(28):
        d = (d0 + datetime.timedelta(days=i)).isoformat(); p, u = (44.9, 6) if i < 14 else (49.9, 5)
        sa.append("PRD-ACTIVCORE-V2,ES,%s,%d,%.2f,EUR,%d,%d,0,%.2f,FBA" % (d, u, u * p / 1.21, 70, u, p)); ad.append("PRD-ACTIVCORE-V2,ES,%s,%.2f,%.2f,40,3000,EUR" % (d, 9.0, 60.0))
    inv.append("PRD-ACTIVCORE-V2,ES,2026-10-28,400")
    return "\n".join(sa), "\n".join(ad), "\n".join(inv)


def contexto(APP, K, f, entorno="PRODUCCION", pvp=None):
    pid = f["producto"]; svc = APP["_svc"](pid); pais = f["pais"] or "ES"
    own, panel = None, None
    if K3S.disponible(svc):
        k3 = K3S.K3Service(APP["store"], svc); rows, _ = k3.rows(); own = k3.own()
        from . import k3 as K3M
        panel = K3M.panels(rows, own["pvp"], own["ml"], k3.seg.t["muestra_min_precio"])
    else:
        own = {"pvp": svc.settings().get("pvp_ref"), "ml": svc.content, "pvp_estado": "PROPUESTO (no aprobado)"}
    kp = K.data.kpis(dict(f, pais=pais), entorno)
    costes = K.costs.assumptions(pid, pais)
    if entorno == "SINTETICO_DEMO":
        ref = (own["pvp"] / own["ml"] * 100) if own.get("pvp") and own.get("ml") else 100.0
        dp = {"estadisticos": {"mediana_100ml": round(ref * 1.1, 2), "min_100ml": round(ref * 0.9, 2), "max_100ml": round(ref * 1.4, 2), "n": 4}, "n_precio_vigente": 4, "titulo": "SINTÉTICO · premium vigente simulado"}
        panel = dict(panel or {}, premium=dp); costes = dict(costes)
        for k_, v_ in (("cogs", 9.0), ("inbound", 0.5), ("prep", 0.4), ("fulfillment", 5.0), ("storage", 0.3), ("returns", 0.6)): costes[k_] = eu.fld(v_, "DOCUMENTADO", "SINTÉTICO DEMO · no son costes reales")
    from datetime import date
    d0, d1 = C.iso_date(f.get("desde")), C.iso_date(f.get("hasta"))
    dias = ((d1 or date.today()) - d0).days + 1 if d0 else None
    dias = K.data.dias_observados(dict(f, pais=pais), entorno) or dias if not d0 else dias
    if pvp is not None: own = dict(own, pvp=pvp, pvp_estado="ESCENARIO «¿y si?» (no es el PVP propuesto)")
    cat = (getattr(svc, "product", None) or {}).get("category") or "*"
    umb = K.um.resolver(pid, cat, pais, f.get("etapa"), entorno)
    return {"umbrales": umb, "producto": pid, "pais": pais, "entorno": entorno, "fecha": date.today().isoformat(), "own": own, "panel_premium": (panel or {}).get("premium"), "costes": costes, "ficha": K.costs.ficha(pid), "kpis": kp,
            "niveles": K.data.niveles_precio(pid, pais, entorno), "dias_periodo": dias, "panel": panel}


def handle(APP, s, method, path, q, b):
    g = lambda k: (q.get(k) or [None])[0]
    p = path[len("/api/k4/"):].strip("/")
    if not APP["store"].can_access(s, ACCOUNT_ID): raise PermissionError("sin acceso al catálogo")
    K = _k4(APP); actor = s["username"]
    if method == "GET":
        if p == "estado":
            return {"fase": "K4 Fase 2 · iteración 1", "entorno_datos": "PRODUCCION", "capacidades": KDIR.capacidades(), "conectores": K.data.estado_conectores(), "gasto_adicional_eur": 0,
                    "paises": PAISES, "canales": CANALES, "productos": [{"id": x["id"], "name": x["name"]} for x in APP["catalog"].list()]}
        if p == "kpis":
            f = _filtros(g); return {"filtros": f, "kpis": K.data.kpis(f, "PRODUCCION")}
        if p == "costes":
            pid = g("producto") or "PRD-ACTIVCORE-V2"; return {"producto": pid, "ficha": K.costs.ficha(pid), "nota": "El coste histórico de 10,03 €/ud es un TOTAL de alcance NO confirmado: no se suma a componentes hasta declarar qué incluye."}
        if p == "medios":
            return {"registro": K.media.registry(g("producto"))}
        if p == "medios/resolver":
            op = g("op") or "visualizar"
            if op not in KM.OPS: raise ValueError("operación inválida")
            return K.media.resolve(g("producto") or "", g("variante") or "", g("asin"), op)
        if p.startswith("medios/") and p.endswith("/file"):
            mid = p.split("/")[1]; mime, raw = K.media.file(mid, "visualizar"); return ("raw", raw, mime, {"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store", "Content-Security-Policy": "default-src 'none'"})
        if p == "dictamen":
            f = _filtros(g); ent = g("entorno") or "PRODUCCION"
            if ent not in C.ENTORNOS: raise ValueError("entorno inválido")
            pvp = float(g("pvp")) if g("pvp") else None
            if pvp is not None and not (1 <= pvp <= 1000): raise ValueError("pvp fuera de rango")
            ctx, d = dictamen_completo(APP, K, f, ent, pvp); return {"dictamen": d, "filtros": f, "aviso_entorno": "DATOS SINTÉTICOS DE DEMOSTRACIÓN: no son ventas ni costes reales" if ent != "PRODUCCION" else None}
        if p == "dossiers":
            return {"dossiers": K.director().listar(g("producto"), g("tipo"))}
        if p.startswith("dossier/"):
            return K.director().obtener(p.split("/", 1)[1])
        if p == "seguimientos":
            return {"seguimientos": K.director().seguimientos(g("producto"))}
        if p == "benchmark/ejecutivo":
            f = _filtros(g); ej = ejecutivo_data(APP, K, f)
            if ej is None: return {"disponible": False, "motivo": "Este producto no tiene perfil de segmentación K3"}
            ctx, d = dictamen_completo(APP, K, f); ej["dictamen"] = d; ej["disponible"] = True; return ej
        if p == "umbrales":
            return {"umbrales": K.um.listar(), "ilustrativos": KUM.ILUSTRATIVOS, "descripcion": KUM.DESCR, "rangos": KUM.RANGOS, "regla": "Ningún umbral está aprobado por defecto. Los ilustrativos solo se usan en entorno SINTETICO_DEMO. Un umbral nunca activa acciones comerciales."}
        if p == "planificador":
            return K.plan.estado()
        if p == "benchmark/expediente":
            f = _filtros(g); return expediente(APP, K, f, g("key") or "")
        if p == "benchmark/explorador":
            f = _filtros(g); return explorador(APP, K, f)
        if p == "conciliar":
            f = _filtros(g); return {"filtros": f, "conciliacion": K.data.conciliar(f, "PRODUCCION")}
        if p == "benchmark":
            f = _filtros(g); ctx = contexto(APP, K, f); return benchmark(APP, K, f, ctx)
        if p == "centro":
            f = _filtros(g); ctx, d = dictamen_completo(APP, K, f)
            return {"filtros": f, "kpis": ctx["kpis"], "dictamen": {"tipo": d["tipo"], "nombre": d["tipo_nombre"], "confianza": d["confianza"], "accion": d["proxima_accion"]}, "faltantes": d["faltantes"],
                    "costes_pendientes": sum(1 for c in ctx["ficha"] if c["estado"] in ("FALTA", "PENDIENTE_VALIDAR")), "capacidades": KDIR.capacidades(), "decisiones": APP["ops"].decisions("PENDIENTE", f["producto"])[:10]}
        if p == "export":
            from . import k4_export as X
            f = _filtros(g); ctx, d = dictamen_completo(APP, K, f); fmt = g("fmt") or "pdf"
            if fmt not in ("pdf", "svg"): raise ValueError("fmt debe ser pdf o svg")
            data, mime, name = X.exportar(K, ctx, d, benchmark(APP, K, f, ctx), fmt, actor)
            return ("raw", data, mime, {"Content-Disposition": 'attachment; filename="%s"' % name, "X-Content-Type-Options": "nosniff"})
        raise LookupError(p)
    # ---------------- escritura
    if p == "demo/cargar":
        _need(s, "admin"); sa, ad, inv = demo_csv()
        if K.k.q("SELECT 1 FROM k4_import WHERE entorno='SINTETICO_DEMO'"): return {"ok": True, "nota": "ya cargados"}
        return {"ok": True, "ventas": K.data.import_csv("sales", sa, "SINTETICO_DEMO", "SINTETICO", "demo sintética", actor)["filas"], "ads": K.data.import_csv("ads", ad, "SINTETICO_DEMO", "SINTETICO", "demo sintética", actor)["filas"], "inventario": K.data.import_csv("inventory", inv, "SINTETICO_DEMO", "SINTETICO", "demo sintética", actor)["filas"], "aviso": "Entorno SINTETICO_DEMO: nunca aparece en consultas de producción"}
    if p == "importar":
        _need(s, "approver"); return K.data.import_csv(str(b.get("tipo")), str(b.get("csv") or ""), "PRODUCCION", str(b.get("origen") or "MANUAL_AHT"), str(b.get("nombre") or "")[:120], actor, reemplazar=b.get("reemplazar") is True)
    if p == "seleccion/ajustar":
        _need(s, "approver"); f = _filtros(lambda k: b.get(k)); svc = APP["_svc"](f["producto"])
        if not K3S.disponible(svc): raise ValueError("producto sin perfil K3")
        rows, _ = K3S.K3Service(APP["store"], svc).rows(); K.sel.ajustar(f["producto"], f["pais"] or "ES", str(b.get("key") or ""), str(b.get("accion") or ""), b.get("motivo"), actor, rows); return {"ok": True}
    if p == "planificador/encolar":
        _need(s, "approver"); return K.plan.encolar(str(b.get("kind")), b.get("producto"), b.get("pais"), b.get("params"), actor=actor)
    if p == "planificador/tick":
        _need(s, "admin"); return K.plan.tick()
    if p == "planificador/parada":
        _need(s, "admin"); return K.plan.parada(b.get("on") is True, actor, str(b.get("motivo") or ""))
    if p == "planificador/cancelar":
        _need(s, "approver"); K.plan.cancelar(int(b.get("id")), actor); return {"ok": True}
    if p == "umbrales":
        _need(s, "approver"); return {"id": K.um.proponer(b, actor), "estado": "PROPUESTO", "nota": "Debe aprobarlo otra persona; no activa ninguna acción comercial"}
    if p == "umbrales/aprobar":
        _need(s, "approver"); K.um.aprobar(int(b.get("id")), b.get("aprobar") is True, actor); return {"ok": True}
    if p == "costes":
        _need(s, "approver"); return {"id": K.costs.add(b, actor)}
    if p == "costes/validar":
        _need(s, "approver"); K.costs.validate(int(b.get("id")), str(b.get("estado")), actor, b.get("incluye")); return {"ok": True}
    if p == "medios":
        _need(s, "approver"); mid = K.media.add(b, actor, b.get("contenido_b64")); return {"id": mid, "estado": "PENDIENTE", "nota": "Registrada sin derechos: verifica el permiso antes de mostrarla o exportarla"}
    if p == "medios/verificar":
        _need(s, "approver"); K.media.verify(str(b.get("id")), str(b.get("estado")), b.get("derechos") or {}, actor, str(b.get("permiso") or "")); return {"ok": True}
    if p == "dossier":
        _need(s, "analyst"); f = _filtros(lambda k: b.get(k)); ctx, d = dictamen_completo(APP, K, f)
        med = K.media.resolve(f["producto"], str(b.get("variante") or "principal"), b.get("asin"), "visualizar")
        dos = KDIR.construir(d, ctx, med); K.director().guardar(dos, actor); return dos
    if p == "dossier/proponer":
        _need(s, "approver"); return K.director().proponer(str(b.get("id")), actor)
    if p == "seguimiento/ejecucion":
        _need(s, "approver"); K.director().registrar_ejecucion(int(b.get("id")), str(b.get("ejecutor") or actor), str(b.get("fecha")), actor); return {"ok": True}
    if p == "seguimiento/medir":
        _need(s, "approver"); return K.director().medir(int(b.get("id")), actor)
    if p == "nuevo-producto":
        _need(s, "analyst"); did = K.director().nuevo_producto(b, actor); return {"id": did, "dossier": K.director().obtener(did)}
    raise LookupError(p)


def ejecutivo_data(APP, K, f):
    pid = f["producto"]; svc = APP["_svc"](pid); pais = f["pais"] or "ES"
    if not K3S.disponible(svc): return None
    k3 = K3S.K3Service(APP["store"], svc); rows, _ = k3.rows(); sel = K.sel.seleccionar(rows, pid, pais); by = {r["key"]: r for r in rows}
    def img(asin, own):
        if asin or own: return K.media.resolve(pid, "principal", None if own else asin, "visualizar")
        return K.media.pending(pid, "principal", None, "Referencia sin ASIN: aportar foto propia o permiso del titular")
    out = KB.ejecutivo(k3.own(), [{"row": by[s["key"]], "sel": s} for s in sel["seleccion"]], img)
    out["seleccion"] = {"regla": sel["regla"], "ajustes": sel["ajustes"]}; out["filtros"] = f; out["pvp_nota"] = k3.own()["pvp_estado"]
    return out


def dictamen_completo(APP, K, f, ent="PRODUCCION", pvp=None):
    ctx = contexto(APP, K, f, ent, pvp); d = KP.dictamen(ctx)
    ej = ejecutivo_data(APP, K, f) if ent == "PRODUCCION" else None
    return ctx, KP.informe(d, (ej or {}).get("ventajas_lista"))


def benchmark(APP, K, f, ctx):
    """Comparativa visual centrada en el producto propio: cada tarjeta lleva imagen resuelta (VERIFICADA) o marcador con la autorización que falta."""
    panel = ctx.get("panel") or {}; svc = APP["_svc"](f["producto"]); items = []
    if K3S.disponible(svc):
        rows, _ = K3S.K3Service(APP["store"], svc).rows()
        for r in rows:
            if f["pais"] and r["country"] != f["pais"]: continue
            items.append({"key": r["key"], "marca": r["brand"], "titulo": r["title"], "asin": r["asin"], "pais": r["country"], "segmento": r["segmento"], "codigo": r["codigo"], "subgrupo": r.get("subgrupo"), "equivalencia": r["equivalencia"], "confianza": (r["confianza"] or {}).get("nivel"),
                          "precio": r["price"], "precio_100ml": r["price_100ml"], "clase_precio": r["price_class"], "fecha_precio": r["price_as_of"], "origen": r["grupo_origen"], "imagen": K.media.resolve(f["producto"], "principal", r["asin"], "visualizar") if r["asin"] else K.media.pending(f["producto"], "principal", None, "Referencia sin ASIN: aportar foto propia o permiso del titular")})
    own = ctx["own"]
    return {"filtros": f, "propio": {"nombre": svc.product.get("name") if getattr(svc, "product", None) else f["producto"], "pvp": own.get("pvp"), "pvp_estado": own.get("pvp_estado"), "ml": own.get("ml"), "imagen": K.media.resolve(f["producto"], "principal", None, "visualizar")}, "items": items, "paneles": panel,
            "nota": "Las imágenes solo se muestran si están VERIFICADAS con derecho de visualización. Sin autorización: IMAGEN PENDIENTE DE VERIFICAR."}


def _rows(APP, f):
    svc = APP["_svc"](f["producto"])
    if not K3S.disponible(svc): return None, None
    k3 = K3S.K3Service(APP["store"], svc); rows, _ = k3.rows(); return k3, rows


def explorador(APP, K, f):
    """Nivel 2: tabla compacta de TODAS las referencias (sin fotos), con la marca de las 5 elegidas. Búsqueda/filtro/orden se hacen en cliente sobre este JSON."""
    k3, rows = _rows(APP, f)
    if rows is None: return {"disponible": False}
    pais = f["pais"] or "ES"; sel = K.sel.seleccionar(rows, f["producto"], pais); en = {x["key"]: x for x in sel["seleccion"]}
    out = [{"key": r["key"], "marca": r["brand"], "titulo": r["title"], "asin": r["asin"], "pais": r["country"], "segmento": r["segmento"], "codigo": r["codigo"], "equivalencia": r["equivalencia"], "confianza": (r["confianza"] or {}).get("nivel"),
            "precio": r["price"], "precio_100ml": r["price_100ml"], "clase_precio": r["price_class"], "fecha_precio": r["price_as_of"], "en_comparativa": r["key"] in en, "motivo_seleccion": (en.get(r["key"]) or {}).get("origen_seleccion")} for r in rows if not f["pais"] or r["country"] == f["pais"]]
    return {"disponible": True, "filtros": f, "total": len(out), "items": out, "seleccion": {"regla": sel["regla"], "ajustes": sel["ajustes"], "claves": list(en)}, "nota": "Puntuación K3 alta no equivale a información verificada: la confianza y el estado del precio se muestran aparte."}


def expediente(APP, K, f, key):
    """Nivel 3: expediente 360° de una referencia."""
    k3, rows = _rows(APP, f)
    if rows is None: raise LookupError("producto sin perfil K3")
    r = next((x for x in rows if x["key"] == key), None)
    if not r: raise LookupError("referencia")
    ej = ejecutivo_data(APP, K, f); col = next((c for c in (ej or {}).get("competidores", []) if c["key"] == key), None)
    if col is None:
        from . import k4_bench as _b; col = _b._comp(r); col.pop("_activos", None); col.pop("_p100", None)
    img = K.media.resolve(f["producto"], "principal", r["asin"], "visualizar") if r["asin"] else K.media.pending(f["producto"], "principal", None, "Referencia sin ASIN: aportar foto propia o permiso del titular")
    return {"key": key, "marca": r["brand"], "titulo": r["title"], "asin": r["asin"], "pais": r["country"], "segmento": r["segmento"], "codigo": r["codigo"], "subgrupo": r.get("subgrupo"), "imagen": img, "celdas": col["celdas"],
            "precio": {"vigente": r["price"] if r["price_class"] in ("ACTUAL", "RECIENTE") else None, "clase": r["price_class"], "fecha": r["price_as_of"], "ultimo_conocido": r["price"], "por_100ml": r["price_100ml"], "historico_nota": "El histórico detallado procede de Keepa ya almacenado (sin llamadas nuevas); un precio no vigente nunca entra en estadísticos."},
            "equivalencia": {"valor": r["equivalencia"], "confianza": r["confianza"], "nota": "Estimación K3; no validación comercial independiente"}, "ventajas_propias": (ej or {}).get("ventajas_lista", []), "propio": (ej or {}).get("propio", {}).get("celdas")}
