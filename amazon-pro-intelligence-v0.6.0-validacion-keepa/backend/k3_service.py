"""K3 · servicio: une el motor (backend/k3.py) con la caché Keepa, el producto y la revisión manual persistente (SQLite, historial + justificación)."""
import re, time
from . import k3 as M, keepa as K

REVIEW_MIN_MOTIVO = 8


def disponible(svc):
    cat = ((getattr(svc, "product", None) or {}).get("category") or "") + " " + str(((getattr(svc, "card", None) or {}).get("category") or ""))
    return bool(svc.legacy or re.search(r"capilar|cuero cabelludo", cat, re.I))


class K3Service:
    def __init__(self, store, svc):
        self.store, self.svc = store, svc; self.seg = M.Segmenter()

    # --------------------------------------------------------------- revisión manual (persistente, con historial)
    def reviews(self):
        out = {}
        with self.store.lock:
            rows = self.store.db.execute("SELECT id FROM records WHERE account_id=? AND kind='dataset' AND key LIKE ?", (self.svc.account, self.svc.prefix + "k3rev:%")).fetchall()
        for r in rows:
            d = self.store.get(self.svc.account, r["id"])["data"]; out[d["key"]] = d
        return out

    def review(self, key, decision, segmento, motivo, actor):
        key = str(key or "").strip()
        if not (re.fullmatch(r"[A-Z0-9]{10}", key.upper()) or re.fullmatch(r"INF:[a-z0-9-]{3,60}", key)):
            raise ValueError("clave de producto inválida")
        key = key if key.startswith("INF:") else key.upper()
        if decision not in ("CONFIRMAR", "RECHAZAR", "RESTABLECER"): raise ValueError("decisión inválida (CONFIRMAR, RECHAZAR o RESTABLECER)")
        motivo = str(motivo or "").strip()
        if decision != "RESTABLECER" and len(motivo) < REVIEW_MIN_MOTIVO: raise ValueError("la justificación es obligatoria (mínimo %d caracteres)" % REVIEW_MIN_MOTIVO)
        if decision == "CONFIRMAR" and segmento not in M.CODE_SEG: raise ValueError("segmento inválido")
        old = self.svc._f("dataset", "k3rev:" + key); hist = list(old["data"].get("historial", [])) if old else []
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        hist.append({"at": now, "actor": actor, "decision": decision, "segmento": segmento if decision == "CONFIRMAR" else None, "motivo": motivo[:300]})
        d = {"key": key, "estado": {"CONFIRMAR": "CONFIRMADO", "RECHAZAR": "RECHAZADO", "RESTABLECER": "AUTOMATICO"}[decision], "segmento": segmento if decision == "CONFIRMAR" else None, "actor": actor, "at": now, "motivo": motivo[:300], "historial": hist[-50:]}
        self.svc._u("dataset", "k3rev:" + key, d, actor); return d

    # --------------------------------------------------------------- datos
    def candidatos(self):
        recs = []
        for c in K.DOMAINS:
            for r in self.svc.scoped_records(c): recs.append(dict(r, country=c))
        return M.build_candidates(recs)

    def rows(self, now=None):
        cands, dups = self.candidatos(); return M.classify_all(self.seg, cands, self.reviews(), now), dups

    def own(self):
        s = self.svc.settings(); ref = self.seg.ref
        pvp = s.get("pvp_ref") or ref.get("pvp_propuesto_eur"); ml = self.svc.content if self.svc.norm == "ml" else ref["formato_ml"]
        dur = ref.get("duracion_dias_teorica")
        return {"nombre": ref["nombre"], "pvp": pvp, "pvp_estado": "PROPUESTO (no aprobado)", "ml": ml, "pvp_100ml": round(pvp / ml * 100, 2) if pvp and ml else None, "coste_dia": round(pvp / dur, 2) if pvp and dur else None,
                "coste_dia_estado": "TEÓRICO: %s" % ref["dosis_estado"] if dur else "NO DISPONIBLE", "ficha": {k: ref[k] for k in ("categoria_real", "necesidad_principal", "zona", "tipo_tratamiento", "aclarado", "regulacion", "formato_ml", "dosis_ml_dia", "publico", "evidencia", "activos", "posicionamiento", "canal")}}

    def filtrar(self, rows, g):
        sub, org = (g.get("subgrupo") or "").upper(), (g.get("origen") or "").lower()
        seg, pais, activo, mn, mx, app = (g.get("segmento") or "", (g.get("country") or "").upper(), norm_(g.get("activo")), _num(g.get("min_ml")), _num(g.get("max_ml")), norm_(g.get("aplicacion")))
        out = []
        for r in rows:
            a = r["automatic"]
            if seg and r["codigo"] != seg: continue
            if sub and (r.get("subgrupo") or "") != sub: continue
            if org and r["grupo_origen"] != org: continue
            if pais and (r["country"] or "") != pais: continue
            if activo and not any(activo in x for x in a["activos"]): continue
            if mn is not None and (a["volumen_ml"] is None or a["volumen_ml"] < mn): continue
            if mx is not None and (a["volumen_ml"] is None or a["volumen_ml"] > mx): continue
            if app and app not in norm_(a["tipo"]) and app not in norm_(a["zona"]): continue
            out.append(r)
        return out

    def resumen(self, g=None, now=None):
        rows, dups = self.rows(now); own = self.own(); allrows = rows; view = self.filtrar(rows, g or {})
        pan = M.panels(allrows, own["pvp"], own["ml"], self.seg.t["muestra_min_precio"])
        cnt = {c: sum(1 for r in allrows if r["codigo"] == c) for c in M.CODE_SEG}
        origen = {"keepa": sum(1 for r in allrows if r["grupo_origen"] == "keepa"), "referencia_sin_asin": sum(1 for r in allrows if r["grupo_origen"] == "referencia_sin_asin")}
        sub = {"premium": cnt["premium"], "funcional_especializado": sum(1 for r in allrows if r["codigo"] == "funcional" and r["subgrupo"] == "ESPECIALIZADO"), "funcional_general": sum(1 for r in allrows if r["codigo"] == "funcional" and r["subgrupo"] != "ESPECIALIZADO")}
        return {"origen_conteo": origen, "subgrupos": sub, "pvp_nota": "El PVP es el PROPUESTO por AHT. K3 no recomienda ni modifica el PVP y no usa precios históricos, sin fecha o de maqueta.", "disponible": True, "version": self.seg.cfg["version"], "categoria": self.seg.cfg["categoria"], "pesos": self.seg.w, "umbrales": self.seg.t, "propio": own, "conteo": cnt, "n_total": len(allrows), "n_visibles": len(view), "paneles": pan, "filas": view, "duplicados": dups,
                "nota_precio": "El precio NO interviene en la equivalencia ni en el segmento. Solo se usan precios ACTUAL/RECIENTE (≤30 d) para estadísticos y posición; los HISTÓRICOS se muestran como referencia.",
                "aviso_evidencia": "Clasificación automática por título, marca y formato (+ datos de maqueta marcados como no verificados). Es REVISABLE: confirma o rechaza con justificación."}


def norm_(s): return M.norm(s) if s else ""


def _num(x):
    try: return float(x) if x not in (None, "") else None
    except (TypeError, ValueError): return None
