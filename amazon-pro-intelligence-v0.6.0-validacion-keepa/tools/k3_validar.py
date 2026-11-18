#!/usr/bin/env python3
"""Validación K3 contra la clasificación de referencia documentada (tests/k3/*.json). Mide aciertos, falsos positivos y falsos negativos.
«Relevante» = PREMIUM o FUNCIONAL (competidor real). FP = el motor lo da por relevante y la referencia no lo acepta; FN = la referencia lo exige relevante y el motor no.
Casos AMBIGUOS (2 etiquetas aceptables) cuentan como acierto con cualquiera y no generan FP/FN si ambas opciones están a un lado u otro."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend import k3
REL = {"premium", "funcional"}


def _recs_gold():
    d = json.load(open(os.path.join(ROOT, "docs_v06/evidencia_keepa_real/competidores_ES.json"), encoding="utf-8"))
    return [{"asin": x["asin"], "brand": x["marca"], "title": x["producto"], "volume_ml": x["formato_ml"], "price": x["precio_observado_eur"], "price_as_of": x["precio_fecha_ultimo_punto"], "bsr": x["bsr"], "country": "ES"} for x in d]


def medir(pred, gold):
    """pred: {id: codigo}; gold: {id: [aceptables]}"""
    n = ok = fp = fn = pfp = pfn = amb = 0; cm = {}; errs = []
    for k, acc in gold.items():
        p = pred.get(k)
        if p is None: continue
        n += 1; amb += len(acc) > 1; hit = p in acc; ok += hit
        cm.setdefault(acc[0], {}); cm[acc[0]][p] = cm[acc[0]].get(p, 0) + 1
        must_rel = all(a in REL for a in acc); may_rel = any(a in REL for a in acc)
        if p in REL and not may_rel: fp += 1
        if p not in REL and must_rel: fn += 1
        if p == "premium" and "premium" not in acc and not (len(acc) > 1): pfp += 1
        if p != "premium" and acc == ["premium"]: pfn += 1
        if not hit: errs.append({"id": k, "pred": p, "aceptables": acc})
    return {"n": n, "aciertos": ok, "acuerdo": round(ok / n, 3) if n else None, "ambiguos": amb, "falsos_positivos_relevante": fp, "falsos_negativos_relevante": fn, "falsos_positivos_premium": pfp, "falsos_negativos_premium": pfn, "matriz": cm, "errores": errs}


def run(seg=None, now=None):
    seg = seg or k3.Segmenter(); res = {}
    g = json.load(open(os.path.join(ROOT, "tests/k3/gold_referencia.json"), encoding="utf-8"))["casos"]
    cands, _ = k3.build_candidates(_recs_gold()); rows = k3.classify_all(seg, cands, now=now)
    pred = {(r["asin"] or r["key"]): r["codigo"] for r in rows}
    res["calibracion_20_asin_mas_5_infografia"] = medir(pred, {k: v["aceptables"] for k, v in g.items()})
    h = json.load(open(os.path.join(ROOT, "tests/k3/heldout.json"), encoding="utf-8"))["casos"]
    pr = {c["id"]: k3.SEG_CODE[seg.classify({"title": c["title"], "brand": c["brand"], "volume_ml": c["volume_ml"]})["segmento"]] for c in h}
    res["heldout_32"] = medir(pr, {c["id"]: c["aceptables"] for c in h}); res["heldout_pred"] = pr
    return res


if __name__ == "__main__":
    r = run(); r.pop("heldout_pred")
    print(json.dumps(r, ensure_ascii=False, indent=1))
