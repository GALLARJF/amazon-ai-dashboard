"""V0.6 (F1/F2) — INICIO: resumen ejecutivo honesto. Cada gráfico responde a una pregunta de negocio y declara fuente, periodo, actualización y estado del dato.
Sin datos reales → SIN DATOS / NO DETERMINABLE / PENDIENTE DE CONEXIÓN (nunca ceros que simulen ausencia). Los datos sintéticos solo existen en modo DEMO, separado."""
import random, time
from . import eu as E, econ6 as X

CHART_Q = {
    "ventas": "¿Cuánto vendo y cuánto gano?",
    "competencia": "¿Cómo estoy de precio frente a la competencia?",
    "publicidad": "¿Qué retorno me da la publicidad?",
    "posicionamiento": "¿Dónde estoy posicionado frente al mercado?",
}


def _chart(cid, state, source, period, updated, series=None, why=None, **kw):
    return {"id": cid, "question": CHART_Q[cid], "state": state, "source": source, "period": period, "updated": updated, "series": series or [], "why": why, **kw}


def demo(today=None):
    """Datos SINTÉTICOS deterministas para demostrar la interfaz. NUNCA se mezclan con datos reales: el cliente muestra un aviso permanente."""
    rnd = random.Random(2026); days = [time.strftime("%Y-%m-%d", time.gmtime(1759276800 + i * 86400)) for i in range(30)]
    sales = [round(180 + 40 * rnd.random() + i * 2, 2) for i in range(30)]; margin = [round(s * 0.28, 2) for s in sales]; spend = [round(s * 0.18, 2) for s in sales]
    return {"mode": "DEMO", "banner": "DEMO · DATOS SINTÉTICOS · NO SON REALES", "days": days, "sales": sales, "margin": margin, "spend": spend, "ads_sales": [round(s * 0.55, 2) for s in sales],
            "own_price": 24.9, "comp": [("Competidor A", 22.5), ("Competidor B", 27.9), ("Competidor C", 31.0)], "bsr": [round(9000 - i * 90 + 500 * rnd.random()) for i in range(30)],
            "kpis": {"ventas": sum(sales), "margen": sum(margin), "acos": 0.18, "tacos": 0.10}}


class Home:
    def __init__(self, catalog, svc_for, importer, ops, launch=None):
        self.cat, self.svc_for, self.imp, self.ops, self.launch = catalog, svc_for, importer, ops, launch

    def build(self, pid=None):
        today = time.strftime("%Y-%m-%d"); prods = self.cat.list(); sel = [p for p in prods if not pid or p["id"] == pid]
        if pid and not sel:
            raise ValueError("producto inexistente")
        summ = {p["id"]: self.imp.summary(p["id"]) for p in sel}
        has_ops = any(s.get("state") == "IMPORTADO" for s in summ.values())
        prelaunch = all(p.get("commercial_state", "PRELANZAMIENTO") in ("IDEA", "DESARROLLO", "PRELANZAMIENTO") for p in sel) and not has_ops
        risks = []
        for p in sel:
            if p["regulatory"]["state"] == "PENDIENTE":
                risks.append({"product": p["id"], "name": p["name"], "level": "ALTO" if p.get("commercial_state") == "LANZADO" else "MEDIO", "risk": "Documentación regulatoria PENDIENTE", "why": "Sin PIF/CPSR/etiquetado documentados no se puede publicar/confiar en el listing"})
            unsup = [c["text"] for c in (p.get("claims") or []) if c.get("state") != "RESPALDADO"]
            if unsup:
                risks.append({"product": p["id"], "name": p["name"], "level": "ALTO", "risk": "%d claim(s) sin respaldo" % len(unsup), "why": "No pueden usarse en listing/anuncios"})
            if not p["costs"]:
                risks.append({"product": p["id"], "name": p["name"], "level": "MEDIO", "risk": "Costes sin documentar", "why": "Sin costes no hay contribución ni ACoS de equilibrio"})
        # --- KPIs
        sales_imp = [s["sales"] for s in summ.values() if isinstance(s.get("sales"), dict) and "total" in s["sales"]]
        ads_imp = [s["ads"] for s in summ.values() if isinstance(s.get("ads"), dict) and "spend" in s["ads"]]
        k = []
        if prelaunch:
            comp = [p for p in sel if self.cat.completeness(p) == []]
            n_comp = 0
            for p in sel:
                svc = self.svc_for(p["id"]); n_comp += sum(len(((svc.country_data().get(c) or {}).get("benchmark") or {}).get("rows", [])) for c in E.COUNTRIES)
            k = [{"id": "fichas", "label": "Fichas completas", "value": "%d/%d" % (len(comp), len(sel)), "state": "REAL", "hint": "campos del catálogo con fuente y fecha"},
                 {"id": "competidores", "label": "Competidores identificados", "value": n_comp if n_comp else "SIN DATOS", "state": "REAL" if n_comp else "SIN DATOS", "hint": "ASIN en caché Keepa asociados a tus productos"},
                 {"id": "regulatorio", "label": "Productos con regulatorio documentado", "value": "%d/%d" % (sum(1 for p in sel if p["regulatory"]["state"] not in ("PENDIENTE",)), len(sel)), "state": "REAL", "hint": "estado en la ficha"},
                 {"id": "decisiones", "label": "Decisiones por aprobar", "value": len(self.ops.decisions()), "state": "REAL", "hint": "bandeja única"}]
        else:
            k = [{"id": "ventas", "label": "Ventas importadas", "value": round(sum(s["total"] for s in sales_imp), 2) if sales_imp else "SIN DATOS", "unit": "€", "state": "IMPORTADO" if sales_imp else "SIN DATOS",
                  "hint": "informes de Amazon importados" if sales_imp else "importa un informe de ventas de Amazon"},
                 {"id": "contribucion", "label": "Contribución", "value": "NO DETERMINABLE", "state": "NO DETERMINABLE", "hint": "REAL exige liquidaciones de Amazon; la ESTIMADA exige costes completos + ventas importadas"},
                 {"id": "ads", "label": "ACoS publicidad", "value": (round(sum(a["spend"] for a in ads_imp) / sum(a["sales"] for a in ads_imp), 4) if ads_imp and sum(a["sales"] for a in ads_imp) else "SIN DATOS"), "state": "IMPORTADO" if ads_imp else "SIN DATOS", "hint": "informe de Amazon Ads importado" if ads_imp else "importa un informe de publicidad"},
                 {"id": "riesgo", "label": "Productos en riesgo", "value": len({r["product"] for r in risks}), "state": "REAL", "hint": "reglas sobre la ficha (regulatorio, claims, costes)"}]
        # --- gráficos
        ch = []
        ser = self.imp.series(pid, "ventas") if pid else []
        ch.append(_chart("ventas", "IMPORTADO" if ser else "SIN DATOS", "Informe de ventas de Amazon importado" if ser else "—", "%s → %s" % (ser[0]["date"], ser[-1]["date"]) if ser else "—", summ.get(pid, {}).get("latest_import") if pid else None, series=ser,
                         why=None if ser else "Selecciona un producto e importa un informe de ventas; sin él no se dibuja nada (no se simulan ceros)."))
        comp_series, own = [], None
        if pid:
            p = sel[0]; svc = self.svc_for(pid); ref = (p["pvp"].get("REF") or {}).get("v"); cont = (p["format"] or {}).get("content")
            own = round(ref / cont * 100, 2) if ref and cont else None
            for c in E.COUNTRIES:
                bm = (svc.country_data().get(c) or {}).get("benchmark")
                if bm and bm.get("price_norm") and bm["price_norm"].get("median") is not None:
                    comp_series.append({"country": c, "median": bm["price_norm"]["median"], "n": bm["used"], "norm_unit": bm["norm_unit"]})
        ch.append(_chart("competencia", "PARCIAL" if comp_series else "SIN DATOS", "Keepa (caché) · comparables confirmados/automáticos" if comp_series else "—", "último dato en caché" if comp_series else "—", None, series=comp_series, own_price_norm=own,
                         why=None if comp_series else "Sin comparables con precio normalizado: ejecuta el descubrimiento (requiere aprobación de presupuesto Keepa)."))
        ads_s = self.imp.series(pid, "publicidad") if pid else []
        ch.append(_chart("publicidad", "IMPORTADO" if ads_s else "SIN DATOS", "Informe de Amazon Ads importado" if ads_s else "—", "%s → %s" % (ads_s[0]["date"], ads_s[-1]["date"]) if ads_s else "—", None, series=ads_s,
                         why=None if ads_s else "Sin informe de publicidad importado. La conexión con la Ads API está PENDIENTE DE CONEXIÓN."))
        ch.append(_chart("posicionamiento", "PENDIENTE DE CONEXIÓN", "BSR/posición propia: requiere SP-API o informe", "—", None, series=[],
                         why="El BSR de la competencia está en Keepa, pero tu posición propia solo puede venir de Amazon (SP-API) o de un informe importado: NO DETERMINABLE hoy."))
        work = self.ops.tasks(states=("EN_CURSO", "PENDIENTE", "ESPERA_APROBACION", "BLOQUEADA"), product=pid, limit=30)
        return {"date": today, "mode": "PRELANZAMIENTO" if prelaunch else "OPERACIÓN", "product": pid, "kpis": k, "charts": ch, "risks": risks, "work": work, "decisions": self.ops.decisions(product=pid) if pid else self.ops.decisions(),
                "ops": self.ops.summary(), "imports": summ, "banner": None}
