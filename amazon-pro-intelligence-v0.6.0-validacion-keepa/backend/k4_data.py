"""K4 · datos comerciales: importación documentada (CSV de Seller Central / Ads / manual) y KPIs con contrato de Medida.
Los adaptadores SP-API/Ads siguen NO OPERATIVOS hasta autorización. Los datos SINTÉTICOS llevan entorno SINTETICO_DEMO y NUNCA entran en consultas de PRODUCCION.
Ausencia de datos = SIN_DATO (nunca 0)."""
import csv, hashlib, io, uuid
from . import k4_contracts as C
from .k4_store import now

MAX_FILAS = 5000
TIPOS = {
    "sales": {"tabla": "k4_sales", "req": ["producto", "pais", "fecha"], "num": ["unidades", "ventas_netas", "sesiones", "pedidos", "devoluciones_uds", "precio_medio"], "txt": ["canal", "moneda"], "dinero": ["ventas_netas", "precio_medio"]},
    "ads": {"tabla": "k4_ads", "req": ["producto", "pais", "fecha"], "num": ["gasto", "ventas_ads", "clics", "impresiones"], "txt": ["moneda"], "dinero": ["gasto", "ventas_ads"]},
    "inventory": {"tabla": "k4_inventory", "req": ["producto", "pais", "fecha"], "num": ["stock"], "txt": [], "dinero": []},
}
ORIGENES_IMPORT = ("EXPORT_SELLER_CENTRAL", "EXPORT_ADS", "MANUAL_AHT", "SINTETICO")
CONECTORES = {"SPAPI": "NO OPERATIVO · adaptador de solo lectura sin autorización ni credenciales; solo probado con simulador", "ADS": "NO OPERATIVO · adaptador de solo lectura sin autorización ni credenciales; solo probado con simulador"}


class Data:
    def __init__(self, k4):
        self.k = k4

    def import_csv(self, tipo, texto, entorno, origen, nombre, actor):
        if tipo not in TIPOS: raise ValueError("tipo de importación desconocido")
        if entorno not in C.ENTORNOS: raise ValueError("entorno inválido")
        if origen not in ORIGENES_IMPORT: raise ValueError("origen de importación no permitido")
        if (origen == "SINTETICO") != (entorno == "SINTETICO_DEMO"): raise ValueError("los datos sintéticos deben ir con entorno SINTETICO_DEMO y a la inversa")
        sha = hashlib.sha256((tipo + entorno + texto).encode()).hexdigest()
        if self.k.q("SELECT 1 FROM k4_import WHERE sha256=?", (sha,)): raise ValueError("importación duplicada (mismo contenido ya cargado)")
        rd = csv.DictReader(io.StringIO(texto)); spec = TIPOS[tipo]
        cols = [c.strip().lower() for c in (rd.fieldnames or [])]
        falt = [c for c in spec["req"] if c not in cols]
        if falt: raise ValueError("faltan columnas: " + ", ".join(falt))
        ok, rech = [], []
        for i, row in enumerate(rd, start=2):
            if i - 1 > MAX_FILAS: raise ValueError("demasiadas filas (máx. %d)" % MAX_FILAS)
            r = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            try:
                if not C.iso_date(r["fecha"]): raise ValueError("fecha inválida")
                if not r["producto"] or len(r["pais"]) != 2: raise ValueError("producto/país inválidos")
                v = {}
                for n in spec["num"]:
                    if r.get(n, "") == "": v[n] = None; continue
                    x = float(r[n].replace(",", ".")) if r[n].count(",") <= 1 and r[n].count(".") == 0 else float(r[n])
                    if x < 0 or x != x: raise ValueError(n + " negativo/NaN")
                    v[n] = x
                for n in spec["txt"]: v[n] = r.get(n) or None
                if any(v.get(n) is not None for n in spec["dinero"]) and not v.get("moneda"): raise ValueError("importe sin moneda")
                ok.append((r["producto"], r["pais"].upper(), r["fecha"][:10], v))
            except ValueError as e:
                rech.append({"fila": i, "motivo": str(e)})
        iid = "IMP-" + uuid.uuid4().hex[:8]
        self.k.x("INSERT INTO k4_import VALUES(?,?,?,?,?,?,?,?,?,?,?)", (iid, tipo, entorno, origen, nombre, sha, len(ok), self.k.j(rech[:50]), "CSV documentado", actor, now()))
        cols_t = spec["num"] + spec["txt"]
        for p, pais, f, v in ok:
            names = ["import_id", "producto", "pais", "fecha"] + cols_t + ["entorno", "origen"]
            self.k.x("INSERT INTO %s(%s) VALUES(%s)" % (spec["tabla"], ",".join(names), ",".join("?" * len(names))), [iid, p, pais, f] + [v.get(c) for c in cols_t] + [entorno, origen])
        self.k.audit(actor, "k4.import", {"id": iid, "tipo": tipo, "entorno": entorno, "filas": len(ok), "rechazadas": len(rech)})
        return {"id": iid, "filas": len(ok), "rechazadas": rech[:20], "n_rechazadas": len(rech)}

    @staticmethod
    def _where(f, tabla, entorno):
        w, a = ["entorno=?"], [entorno]
        for k, col in (("producto", "producto"), ("pais", "pais"), ("canal", "canal")):
            if f.get(k) and not (k == "canal" and tabla != "k4_sales"):
                w.append(col + "=?"); a.append(f[k].upper() if k == "pais" else f[k])
        if f.get("desde"): w.append("fecha>=?"); a.append(f["desde"])
        if f.get("hasta"): w.append("fecha<=?"); a.append(f["hasta"])
        return " AND ".join(w), a

    def kpis(self, f, entorno="PRODUCCION"):
        """KPIs como Medidas. `f`: producto, pais, canal, desde, hasta. Nunca mezcla entornos."""
        if entorno not in C.ENTORNOS: raise ValueError("entorno inválido")
        per = "%s..%s" % (f.get("desde") or "inicio", f.get("hasta") or "hoy")
        def M(v, u, fuente, fecha, **kw):
            return C.medida(v, u, fuente, fecha, periodo=per, entorno=entorno, **kw) if v is not None else C.medida(None, u, None, None, periodo=per, entorno=entorno, **kw)
        out = {}
        w, a = self._where(f, "k4_sales", entorno)
        s = self.k.q("SELECT COUNT(*) n, SUM(unidades) u, SUM(ventas_netas) v, SUM(sesiones) se, SUM(pedidos) pe, SUM(devoluciones_uds) dv, MAX(fecha) fe, MIN(moneda) m1, MAX(moneda) m2, MIN(origen) o FROM k4_sales WHERE " + w, a)[0]
        conf = "ALTA" if s["o"] in ("EXPORT_SELLER_CENTRAL",) else "MEDIA"
        if s["n"]:
            mon = s["m1"] if s["m1"] == s["m2"] else None
            out["unidades"] = M(s["u"], "uds", s["o"], s["fe"], confianza=conf) if s["u"] is not None else M(None, "uds", None, None)
            out["ventas_netas"] = M(s["v"], "EUR" if mon == "EUR" else (mon or "mixto"), s["o"], s["fe"], moneda=mon, confianza=conf) if (s["v"] is not None and mon) else M(None, "EUR", None, None, moneda=None)
            out["sesiones"] = M(s["se"], "sesiones", s["o"], s["fe"], confianza=conf) if s["se"] is not None else M(None, "sesiones", None, None)
            out["conversion"] = M(round(s["pe"] / s["se"], 4), "ratio", s["o"], s["fe"], denominador="sesiones", metodologia="pedidos / sesiones", confianza=conf, estado="DERIVADO") if (s["pe"] is not None and s["se"]) else M(None, "ratio", None, None)
            out["tasa_devolucion"] = M(round(s["dv"] / s["u"], 4), "ratio", s["o"], s["fe"], denominador="unidades", metodologia="devoluciones / unidades", confianza=conf, estado="DERIVADO") if (s["dv"] is not None and s["u"]) else M(None, "ratio", None, None)
        else:
            for k, u in (("unidades", "uds"), ("ventas_netas", "EUR"), ("sesiones", "sesiones"), ("conversion", "ratio"), ("tasa_devolucion", "ratio")): out[k] = M(None, u, None, None)
        w, a = self._where(f, "k4_ads", entorno)
        d = self.k.q("SELECT COUNT(*) n, SUM(gasto) g, SUM(ventas_ads) v, MAX(fecha) fe, MIN(origen) o, MIN(moneda) m1, MAX(moneda) m2 FROM k4_ads WHERE " + w, a)[0]
        if d["n"] and d["g"] is not None and d["v"] and d["m1"] == d["m2"] and d["m1"]:
            out["gasto_ads"] = M(d["g"], d["m1"], d["o"], d["fe"], moneda=d["m1"], confianza="MEDIA")
            out["acos"] = M(round(d["g"] / d["v"], 4), "ratio", d["o"], d["fe"], denominador="ventas atribuidas a Ads", metodologia="gasto / ventas atribuidas (base de IVA según informe)", confianza="MEDIA", estado="DERIVADO")
        else:
            out["gasto_ads"] = M(None, "EUR", None, None); out["acos"] = M(None, "ratio", None, None)
        w, a = self._where(f, "k4_inventory", entorno)
        i = self.k.q("SELECT stock, fecha, origen FROM k4_inventory WHERE " + w + " ORDER BY fecha DESC LIMIT 1", a)
        out["stock"] = M(i[0]["stock"], "uds", i[0]["origen"], i[0]["fecha"], confianza="MEDIA") if i and i[0]["stock"] is not None else M(None, "uds", None, None)
        return out

    def dias_observados(self, f, entorno="PRODUCCION"):
        w, a = self._where(f, "k4_sales", entorno)
        r = self.k.q("SELECT COUNT(DISTINCT fecha) n FROM k4_sales WHERE " + w, a)
        return r[0]["n"] or None

    def niveles_precio(self, producto, pais, entorno="PRODUCCION"):
        """Niveles de precio observados con unidades (para elasticidad observada, ≥2 niveles distintos con ≥3 días cada uno)."""
        rows = self.k.q("SELECT ROUND(precio_medio,1) p, SUM(unidades) u, COUNT(DISTINCT fecha) d FROM k4_sales WHERE producto=? AND pais=? AND entorno=? AND precio_medio IS NOT NULL AND unidades IS NOT NULL GROUP BY ROUND(precio_medio,1)", (producto, pais.upper(), entorno))
        return [{"precio": r["p"], "uds_dia": r["u"] / r["d"], "dias": r["d"]} for r in rows if r["d"] >= 3]

    def estado_conectores(self):
        return {k: {"estado": "NO_OPERATIVO", "detalle": v} for k, v in CONECTORES.items()}
