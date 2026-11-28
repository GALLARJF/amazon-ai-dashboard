"""V1.1 — Lectura de informes de Amazon Ads (CSV de TÉRMINOS DE BÚSQUEDA descargado por una persona). SOLO LECTURA: no llama a ninguna API, no escribe en Amazon, no gasta.
Calcula CPC, CVR, ACoS (gasto / ventas atribuidas) y TACoS (gasto / ventas totales del periodo, denominador EXPLÍCITO y solo si se aportan). Las ventas «no atribuidas a Ads»
(totales − atribuidas) NO se llaman orgánicas. Cada recomendación lleva evidencia y explicación; ninguna se ejecuta: se exporta para ejecución humana externa."""
import csv, io, re
from . import importer as IM
from . import comercial as CM

ALIASES = {
    "termino": ["término de búsqueda de cliente", "termino de busqueda de cliente", "customer search term", "término de búsqueda", "search term", "término", "termino"],
    "campana": ["nombre de la campaña", "campaign name", "campaña", "campana"], "concordancia": ["tipo de concordancia", "match type", "concordancia"],
    "impresiones": ["impresiones", "impressions"], "clics": ["clics", "clicks"], "gasto": ["gasto", "spend", "coste", "cost"],
    "ventas": ["ventas totales de 7 días", "7 day total sales", "ventas de 7 días", "ventas", "sales"], "pedidos": ["pedidos totales de 7 días", "7 day total orders (#)", "7 day total orders", "pedidos", "orders"],
}
MAX_FILAS = 20000


def parse(raw):
    if len(raw) > IM.MAX_BYTES: raise ValueError("archivo demasiado grande (>5 MB)")
    try: text = raw.decode("utf-8-sig")
    except UnicodeDecodeError: text = raw.decode("latin-1")
    if not text.strip(): raise ValueError("archivo vacío")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    rows = [r for r in csv.reader(io.StringIO(text), dialect) if any(c.strip() for c in r)]
    if len(rows) < 2: raise ValueError("el archivo no tiene filas de datos")
    if len(rows) - 1 > MAX_FILAS: raise ValueError("demasiadas filas (máx. %d)" % MAX_FILAS)
    heads = [IM.norm_h(h) for h in rows[0]]; idx = {}
    for k, al in ALIASES.items():
        for a in al:
            if a in heads: idx[k] = heads.index(a); break
    falta = [k for k in ("termino", "clics", "gasto") if k not in idx]
    if falta: raise ValueError("no es un informe de términos de búsqueda: faltan columnas " + ", ".join(falta))
    out = []
    for r in rows[1:]:
        g = lambda k: r[idx[k]] if k in idx and idx[k] < len(r) else None
        out.append({"termino": (g("termino") or "").strip()[:120], "campana": (g("campana") or "").strip()[:120] or None, "concordancia": (g("concordancia") or "").strip().lower() or None,
                    "impresiones": IM.parse_num(g("impresiones")), "clics": IM.parse_num(g("clics")), "gasto": IM.parse_num(g("gasto")), "ventas": IM.parse_num(g("ventas")), "pedidos": IM.parse_num(g("pedidos"))})
    return out


def _div(a, b):
    return round(a / b, 4) if a is not None and b else None


def metricas(filas, ventas_totales=None):
    s = lambda k: round(sum(f[k] for f in filas if f.get(k) is not None), 2)
    gasto, ventas, clics, pedidos = s("gasto"), s("ventas"), s("clics"), s("pedidos")
    m = {"gasto": gasto, "ventas_atribuidas": ventas, "clics": clics, "pedidos": pedidos, "cpc": _div(gasto, clics), "cvr": _div(pedidos, clics), "acos": _div(gasto, ventas),
         "acos_denominador": "ventas atribuidas del informe de Ads (la base con/sin IVA se confirma en el informe real)"}
    if ventas_totales is None:
        m.update(tacos=None, tacos_nota="NO DETERMINABLE: falta el total de ventas del periodo (informe de ventas, mismo periodo y base de IVA)", ventas_no_atribuidas=None)
    else:
        vt = CM._num(ventas_totales, "ventas_totales", 0, 1e9)
        m.update(tacos=_div(gasto, vt), tacos_denominador="ventas totales del periodo aportadas", ventas_no_atribuidas=round(vt - ventas, 2),
                 ventas_no_atribuidas_nota="ventas totales − ventas atribuidas a Ads; NO se interpretan como orgánicas (incluyen otros canales de atribución, ventanas y pedidos sin clic)")
        if vt < ventas: m["aviso"] = "las ventas totales son menores que las atribuidas: revisar periodo y base de IVA"
    return m


def recomendaciones(filas, acos_objetivo=None, cpc_actual=None, dias_desde_fin_informe=None, ventana_dias=None, min_clics_negativa=None):
    """Propuestas con evidencia. Los umbrales son PARÁMETROS que debe fijar una persona (no se inventan): sin ellos se explica qué falta."""
    out = []; faltan = []
    if min_clics_negativa is None: faltan.append("min_clics_negativa (clics mínimos sin ventas para proponer una negativa)")
    if ventana_dias is None or dias_desde_fin_informe is None: faltan.append("ventana_dias y dias_desde_fin_informe (cierre de la ventana de atribución)")
    if acos_objetivo is None: faltan.append("acos_objetivo (se deriva de la contribución del motor económico)")
    for f in filas:
        t, cl, ve, ga, pe = f["termino"], f.get("clics") or 0, f.get("ventas") or 0, f.get("gasto") or 0, f.get("pedidos") or 0
        ev = {"termino": t, "campana": f.get("campana"), "concordancia": f.get("concordancia"), "clics": cl, "gasto": ga, "ventas": ve, "pedidos": pe,
              "cpc": _div(ga, cl), "cvr": _div(pe, cl), "acos": _div(ga, ve)}
        if min_clics_negativa is not None and cl >= min_clics_negativa and ve == 0:
            if ventana_dias is not None and dias_desde_fin_informe is not None and dias_desde_fin_informe >= ventana_dias:
                out.append({"tipo": "negativa", "accion_propuesta": "añadir como negativa (exacta o de frase) en la campaña", "evidencia": ev,
                            "explicacion": "%d clics y 0 ventas con la ventana de atribución (%d días) ya cerrada" % (cl, ventana_dias), "ejecuta": "persona, fuera de la herramienta"})
            else:
                out.append({"tipo": "esperar", "accion_propuesta": "no actuar todavía", "evidencia": ev, "explicacion": "sin ventas, pero la ventana de atribución puede seguir abierta o no se conoce", "ejecuta": "nadie"})
        elif ve > 0 and acos_objetivo is not None and f.get("concordancia") in ("broad", "amplia", "auto", "automática", "automatica", None, ""):
            if ev["acos"] is not None and ev["acos"] <= acos_objetivo:
                out.append({"tipo": "migrar_a_manual", "accion_propuesta": "crear el término en concordancia exacta (y de frase) en una campaña manual", "evidencia": ev,
                            "explicacion": "ACoS %.1f %% ≤ objetivo %.1f %% con %d pedido(s); evidencia limitada si hay pocos pedidos" % (ev["acos"] * 100, acos_objetivo * 100, pe), "ejecuta": "persona, fuera de la herramienta"})
        if cpc_actual is not None and ev["cvr"] and ve and pe and acos_objetivo is not None:
            vpp = ve / pe; puja = round(ev["cvr"] * vpp * acos_objetivo, 2)
            if cpc_actual > puja:
                out.append({"tipo": "bajar_puja", "accion_propuesta": "puja máxima orientativa %.2f €" % puja, "evidencia": {**ev, "venta_por_pedido": round(vpp, 2), "cpc_actual": cpc_actual},
                            "explicacion": "puja máx. = CVR × venta por pedido × ACoS objetivo; el CPC actual la supera", "ejecuta": "persona, fuera de la herramienta"})
    return {"recomendaciones": out, "parametros_que_faltan": faltan, "n": len(out), "escritura_amazon": "NINGUNA: esta herramienta no escribe en Amazon Ads"}


def exportacion_csv(recs):
    """CSV para ejecución humana externa. No se envía a ningún sitio."""
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["# PROPUESTAS PARA REVISIÓN Y EJECUCIÓN HUMANA EXTERNA. Esta herramienta no escribe en Amazon Ads."])
    w.writerow(["tipo", "termino", "campana", "concordancia", "clics", "gasto", "ventas", "accion_propuesta", "explicacion"])
    for r in recs:
        e = r["evidencia"]; w.writerow([_safe(r["tipo"]), _safe(e.get("termino")), _safe(e.get("campana")), _safe(e.get("concordancia")), e.get("clics"), e.get("gasto"), e.get("ventas"), _safe(r["accion_propuesta"]), _safe(r["explicacion"])])
    return buf.getvalue()


def _safe(v):
    """Neutraliza inyección de fórmulas en hojas de cálculo (=, +, -, @, tab, CR al inicio)."""
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s
