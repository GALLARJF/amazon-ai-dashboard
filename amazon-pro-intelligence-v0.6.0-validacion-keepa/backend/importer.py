"""V0.6 (F12) — Importación de informes REALES de Amazon (CSV descargados por una persona) y de documentación interna.
Garantías: el archivo original se conserva sin modificar (hash SHA-256), se registra fecha, cobertura (rango de fechas, filas) y producto; clase de dato IMPORTADO.
No es conexión SP-API/Ads API: es importación manual documentada. Nunca se mezcla con datos DEMO/SINTÉTICOS."""
import csv, hashlib, io, re, time
from . import activcore as AC
from .catalog import ACCOUNT_ID

ALIASES = {
    "date": ["fecha", "date", "día", "dia", "start date", "fecha de inicio"],
    "asin": ["(child) asin", "(asin) secundario", "asin secundario", "asin", "(asin) principal", "advertised asin", "asin anunciado"],
    "sales": ["ventas de productos pedidos", "ordered product sales", "ventas pedidas", "importe de pedidos", "ventas de pedidos", "ventas totales de 7 días", "7 day total sales", "ventas", "sales"],
    "units": ["unidades pedidas", "units ordered", "unidades", "7 day total units"],
    "sessions": ["sesiones - total", "sessions - total", "sesiones", "sessions"],
    "spend": ["gasto", "spend", "coste", "cost", "inversión", "inversion"],
    "clicks": ["clics", "clicks", "clic"],
    "impressions": ["impresiones", "impressions"],
    "orders": ["pedidos", "orders", "7 day total orders", "pedidos totales de 7 días"],
}
MAX_BYTES = 5 * 1024 * 1024


def norm_h(h):
    return re.sub(r"\s+", " ", str(h or "").replace("﻿", "").strip().lower())


def parse_num(s):
    """Acepta «1.234,56 €», «€1,234.56», «12,5 %», «1234». Devuelve float o None (nunca inventa)."""
    if s is None:
        return None
    t = re.sub(r"[^\d,.\-]", "", str(s))
    if not re.search(r"\d", t):
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".") if len(t.split(",")[-1]) != 3 or t.count(",") == 1 and len(t.split(",")[-1]) != 3 else t.replace(",", "")
    elif t.count(".") > 1 or (t.count(".") == 1 and len(t.split(".")[-1]) == 3 and len(t.split(".")[0]) <= 3 and t.split(".")[0] not in ("0", "")):
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def parse_date(s):
    s = str(s or "").strip()
    for rx, order in ((r"^(\d{4})-(\d{2})-(\d{2})", "ymd"), (r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", "dmy")):
        m = re.match(rx, s)
        if m:
            a, b, c = m.groups()
            y, mo, d = (a, b, c) if order == "ymd" else (c, b, a)
            try:
                time.strptime("%s-%02d-%02d" % (y, int(mo), int(d)), "%Y-%m-%d"); return "%s-%02d-%02d" % (y, int(mo), int(d))
            except ValueError:
                return None
    return None


def parse(raw_bytes):
    if len(raw_bytes) > MAX_BYTES:
        raise ValueError("archivo demasiado grande (>5 MB)")
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t") if text.strip() else csv.excel
    rd = list(csv.reader(io.StringIO(text), dialect))
    rd = [r for r in rd if any(c.strip() for c in r)]
    if len(rd) < 2:
        raise ValueError("el archivo no tiene filas de datos")
    heads = [norm_h(h) for h in rd[0]]; idx = {}
    for key, al in ALIASES.items():
        for a in al:
            if a in heads:
                idx[key] = heads.index(a); break
    if {"spend", "clicks"} <= set(idx) or ("spend" in idx and "impressions" in idx):
        typ = "publicidad"
    elif "sales" in idx and ("date" in idx or "asin" in idx):
        typ = "ventas"
    else:
        raise ValueError("no se reconoce el informe: se esperan columnas de ventas (fecha/ASIN + ventas) o de publicidad (gasto + clics). Columnas halladas: " + ", ".join(h for h in heads[:12] if h))
    rows = []
    for r in rd[1:]:
        g = lambda k: r[idx[k]] if k in idx and idx[k] < len(r) else None
        rows.append({"date": parse_date(g("date")), "asin": (g("asin") or "").strip().upper() or None, "sales": parse_num(g("sales")), "units": parse_num(g("units")), "sessions": parse_num(g("sessions")),
                     "spend": parse_num(g("spend")), "clicks": parse_num(g("clicks")), "impressions": parse_num(g("impressions")), "orders": parse_num(g("orders"))})
    return typ, rows, [heads[i] for i in idx.values()]


def metrics(typ, rows):
    s = lambda k: round(sum(r[k] for r in rows if r.get(k) is not None), 2)
    dates = sorted(r["date"] for r in rows if r.get("date"))
    cov = {"rows": len(rows), "from": dates[0] if dates else None, "to": dates[-1] if dates else None, "dated_rows": len(dates), "undated_rows": len(rows) - len(dates)}
    if typ == "ventas":
        return {"coverage": cov, "sales": s("sales"), "units": s("units"), "sessions": s("sessions"), "conversion": round(s("units") / s("sessions"), 4) if s("sessions") else None}
    sp, sa = s("spend"), s("sales")
    return {"coverage": cov, "spend": sp, "sales": sa, "clicks": s("clicks"), "impressions": s("impressions"), "orders": s("orders"), "acos": round(sp / sa, 4) if sa else None}


class Importer:
    def __init__(self, store, catalog):
        self.store, self.cat = store, catalog

    def import_report(self, pid, filename, raw, actor, marketplace=None, kind_hint=None):
        if not self.cat.get(pid):
            raise ValueError("producto inexistente")
        digest = hashlib.sha256(raw).hexdigest(); key = "imp:%s:%s" % (pid, digest[:16])
        if AC._find(self.store, "dataset", key, ACCOUNT_ID):
            raise ValueError("este informe ya fue importado (mismo contenido): se evita duplicarlo")
        typ, rows, cols = parse(raw)
        if kind_hint and kind_hint != typ:
            raise ValueError("el informe parece de «%s», no de «%s»" % (typ, kind_hint))
        asins = {r["asin"] for r in rows if r["asin"]}
        own = {a for a in (self.cat.get(pid).get("own_asins") or {}).values()} | {v.get("asin") for v in (self.cat.get(pid).get("amazon_connections") or {}).values() if v.get("asin")}
        warn = []
        if asins and own and not (asins & own):
            warn.append("Ningún ASIN del informe coincide con los ASIN declarados del producto: revisar que sea el producto correcto.")
        if not own:
            warn.append("El producto no tiene ASIN declarado: no se puede comprobar que el informe sea suyo.")
        m = metrics(typ, rows)
        d = {"type": typ, "product": pid, "filename": str(filename)[:120], "sha256": digest, "bytes": len(raw), "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "imported_by": actor, "marketplace": marketplace,
             "class": "IMPORTADO", "provenance": "Informe de Amazon descargado por una persona e importado SIN MODIFICAR (hash conservado). No es una conexión API.", "columns": cols, "metrics": m, "warnings": warn, "rows": rows[:5000]}
        AC._upsert(self.store, "dataset", key, d, actor, ACCOUNT_ID)
        return {k: v for k, v in d.items() if k != "rows"}

    def reports(self, pid=None):
        with self.store.lock:
            rows = self.store.db.execute("SELECT id FROM records WHERE account_id=? AND kind='dataset' AND key LIKE ?", (ACCOUNT_ID, "imp:%s:%%" % (pid or ""))).fetchall()
        out = [{k: v for k, v in self.store.get(ACCOUNT_ID, r["id"])["data"].items() if k != "rows"} for r in rows]
        return sorted(out, key=lambda x: x["imported_at"], reverse=True)

    def summary(self, pid):
        """Métricas de operación SOLO a partir de informes importados. Sin informes → SIN DATOS (no cero)."""
        reps = self.reports(pid)
        if not reps:
            return {"state": "SIN DATOS", "why": "No hay informes de Amazon importados para este producto", "reports": 0}
        sales = [r for r in reps if r["type"] == "ventas"]; ads = [r for r in reps if r["type"] == "publicidad"]
        out = {"state": "IMPORTADO", "reports": len(reps), "latest_import": reps[0]["imported_at"], "class": "IMPORTADO"}
        if sales:
            out["sales"] = {"total": round(sum(r["metrics"]["sales"] for r in sales), 2), "units": round(sum(r["metrics"]["units"] for r in sales), 2), "from": min(r["metrics"]["coverage"]["from"] or "9999" for r in sales), "to": max(r["metrics"]["coverage"]["to"] or "" for r in sales),
                            "note": "Base de IVA no verificada: depende del informe; confirmar antes de calcular márgenes"}
        else:
            out["sales"] = {"state": "SIN DATOS"}
        if ads:
            sp = sum(r["metrics"]["spend"] for r in ads); sa = sum(r["metrics"]["sales"] for r in ads)
            out["ads"] = {"spend": round(sp, 2), "sales": round(sa, 2), "acos": round(sp / sa, 4) if sa else None, "from": min(r["metrics"]["coverage"]["from"] or "9999" for r in ads), "to": max(r["metrics"]["coverage"]["to"] or "" for r in ads)}
        else:
            out["ads"] = {"state": "SIN DATOS"}
        if sales and ads:
            ts = out["sales"]["total"]; out["tacos"] = {"valor": round(out["ads"]["spend"] / ts, 4) if ts else None, "nota": "TACoS = gasto en publicidad importado ÷ ventas totales importadas; válido solo si los periodos coinciden"}
        else:
            out["tacos"] = {"valor": None, "state": "NO DETERMINABLE", "why": "requiere informe de ventas y de publicidad"}
        return out

    def import_document(self, pid, name, text, actor, doc_type="documentacion"):
        p = self.cat.get(pid)
        if not p:
            raise ValueError("producto inexistente")
        text = str(text or "")
        if len(text.strip()) < 20 or len(text) > 200000:
            raise ValueError("documento vacío o demasiado largo (20–200000 caracteres)")
        digest = hashlib.sha256(text.encode()).hexdigest(); key = "doc:%s:%s" % (pid, digest[:16])
        if AC._find(self.store, "evidence", key, ACCOUNT_ID):
            raise ValueError("este documento ya fue importado")
        d = {"product": pid, "name": str(name)[:120], "type": doc_type, "sha256": digest, "chars": len(text), "text": text, "imported_by": actor, "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "class": "IMPORTADO"}
        AC._upsert(self.store, "evidence", key, d, actor, ACCOUNT_ID)
        docs = list(p.get("documents") or []) + [{"name": d["name"], "ref": "import:" + digest[:12]}]
        self.cat.update(pid, {"documents": docs}, actor, "documento importado: " + d["name"])
        return {k: v for k, v in d.items() if k != "text"}


def _series(imp, pid, typ):
    by = {}
    for r in imp.reports(pid):
        if r["type"] != typ:
            continue
        full = imp.store.get(ACCOUNT_ID, next((x["id"] for x in [imp.store.db.execute("SELECT id FROM records WHERE account_id=? AND key=?", (ACCOUNT_ID, "imp:%s:%s" % (pid, r["sha256"][:16]))).fetchone()] if x), ""))
        for row in (full["data"]["rows"] if full else []):
            if row.get("date"):
                a = by.setdefault(row["date"], {"sales": 0.0, "units": 0.0, "spend": 0.0})
                for k in ("sales", "units", "spend"):
                    a[k] += row.get(k) or 0.0
    return [{"date": d, **{k: round(v, 2) for k, v in x.items()}} for d, x in sorted(by.items())]


Importer.series = lambda self, pid, typ: _series(self, pid, typ)
