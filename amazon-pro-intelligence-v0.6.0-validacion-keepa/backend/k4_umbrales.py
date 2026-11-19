"""K4 · umbrales comerciales CONFIGURABLES por producto/categoría/país/etapa y SUJETOS A APROBACIÓN. Nada queda aprobado por defecto: los valores históricos (15 %, ±15 %, 5 %, 14 d) son
ILUSTRATIVOS y solo se usan en entorno SINTETICO_DEMO. Un umbral nunca activa por sí solo un cambio comercial."""
from .k4_store import now

ILUSTRATIVOS = {"margen_min": 0.15, "ratio_bajo": 0.85, "ratio_alto": 1.15, "conv_baja": 0.05, "cobertura_min_dias": 14, "dias_ventas_min": 14}
RANGOS = {"margen_min": (0.0, 0.9), "ratio_bajo": (0.3, 1.0), "ratio_alto": (1.0, 3.0), "conv_baja": (0.0, 0.5), "cobertura_min_dias": (1, 365), "dias_ventas_min": (3, 365)}
ETAPAS = ("*", "lanzamiento", "crecimiento", "madurez")
DESCR = {"margen_min": "Margen de contribución mínimo antes de Ads", "ratio_bajo": "Precio/100 ml ≤ este múltiplo de la mediana premium ⇒ posible margen de subida", "ratio_alto": "Precio/100 ml ≥ este múltiplo ⇒ posible exceso de precio",
         "conv_baja": "Conversión (pedidos/sesiones) considerada baja", "cobertura_min_dias": "Cobertura mínima de inventario en días", "dias_ventas_min": "Días de ventas observadas necesarios para decidir"}


class Umbrales:
    def __init__(self, k4):
        self.k = k4

    def proponer(self, d, actor):
        v = d.get("valores") or {}
        if not v or set(v) - set(RANGOS): raise ValueError("valores inválidos; claves permitidas: " + ", ".join(RANGOS))
        for k, x in v.items():
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not (RANGOS[k][0] <= x <= RANGOS[k][1]): raise ValueError("%s fuera de rango %s" % (k, RANGOS[k]))
        et = d.get("etapa") or "*"
        if et not in ETAPAS: raise ValueError("etapa inválida")
        if len(str(d.get("motivo") or "")) < 8: raise ValueError("indica el motivo (mín. 8 caracteres)")
        c = self.k.x("INSERT INTO k4_umbral(producto,categoria,pais,etapa,valores,estado,motivo,propuesto_por,creado) VALUES(?,?,?,?,?,'PROPUESTO',?,?,?)", (d.get("producto") or "*", d.get("categoria") or "*", (d.get("pais") or "*").upper(), et, self.k.j(v), str(d["motivo"])[:300], actor, now()))
        self.k.audit(actor, "k4.umbral.propuesta", {"id": c.lastrowid, "alcance": [d.get("producto") or "*", d.get("categoria") or "*", d.get("pais") or "*", et]}); return c.lastrowid

    def aprobar(self, uid, aprobar, actor):
        r = self.k.q("SELECT * FROM k4_umbral WHERE id=?", (uid,))
        if not r: raise LookupError("umbral inexistente")
        if r[0]["estado"] != "PROPUESTO": raise ValueError("ya resuelto")
        if r[0]["propuesto_por"] == actor: raise ValueError("el aprobador no puede ser quien lo propuso")
        self.k.x("UPDATE k4_umbral SET estado=?, aprobado_por=?, aprobado_en=? WHERE id=?", ("APROBADO" if aprobar else "RECHAZADO", actor, now(), uid))
        self.k.audit(actor, "k4.umbral." + ("aprobado" if aprobar else "rechazado"), {"id": uid})

    def listar(self):
        out = self.k.q("SELECT * FROM k4_umbral ORDER BY id DESC LIMIT 100")
        import json
        for r in out: r["valores"] = json.loads(r["valores"])
        return out

    def resolver(self, producto, categoria, pais, etapa, entorno):
        """Devuelve {cfg, estado, alcance}. PRODUCCION: solo umbrales APROBADOS (el más específico gana; los que faltan → None). SINTETICO_DEMO: ilustrativos etiquetados."""
        import json
        if entorno != "PRODUCCION": return {"cfg": dict(ILUSTRATIVOS), "estado": "ILUSTRATIVO_SINTETICO", "alcance": "demo", "aviso": "Valores ILUSTRATIVOS en entorno sintético; no son reglas aprobadas"}
        rows = [r for r in self.k.q("SELECT * FROM k4_umbral WHERE estado='APROBADO' AND vigente=1") if r["producto"] in ("*", producto) and r["categoria"] in ("*", categoria or "*") and r["pais"] in ("*", (pais or "*").upper()) and r["etapa"] in ("*", etapa or "*")]
        if not rows: return {"cfg": None, "estado": "PENDIENTE_DE_APROBACION", "alcance": None, "aviso": "No hay umbrales APROBADOS para este alcance: no se emiten recomendaciones numéricas"}
        rows.sort(key=lambda r: ((r["producto"] != "*") * 8 + (r["categoria"] != "*") * 4 + (r["pais"] != "*") * 2 + (r["etapa"] != "*"), r["id"]))
        cfg = {}
        for r in rows: cfg.update(json.loads(r["valores"]))
        falt = [k for k in RANGOS if k not in cfg]
        return {"cfg": cfg if not falt else None, "estado": "APROBADO" if not falt else "INCOMPLETO", "alcance": [rows[-1]["producto"], rows[-1]["categoria"], rows[-1]["pais"], rows[-1]["etapa"]], "faltan": falt, "aviso": None if not falt else "Faltan valores aprobados: " + ", ".join(falt)}
