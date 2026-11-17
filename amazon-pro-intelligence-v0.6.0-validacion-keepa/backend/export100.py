"""V1.0 (V1-06) — Exportaciones CSV / HTML / Markdown con trazabilidad (fuente, fecha, clase) y escapado seguro.
CSV: neutraliza inyección de fórmulas (= + - @ tab CR); HTML: escapa todo; nombres de fichero saneados."""
import csv, html, io, re
FORMULA = ("=", "+", "-", "@", "\t", "\r")
def celda(v):
    s = "" if v is None else str(v)
    return "'" + s if s.startswith(FORMULA) else s
def nombre(base, ext):
    b = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(base or "export"))[:60].strip("._") or "export"
    return "%s.%s" % (b, ext)
def competidores_filas(kr):
    cols = ["asin", "marca", "titulo", "precio_eur", "precio_fecha", "bsr_o_formato_ml", "precio_100ml", "obsoleto", "comparabilidad", "fuente", "fecha_consulta", "procedencia"]
    rows = [[c.get("asin"), c.get("brand"), c.get("title"), c.get("price_eur"), c.get("price_as_of"), c.get("format_ml"), c.get("price_per_100ml"), "SI" if c.get("price_stale") else "NO",
             c.get("comparability_confirmed"), c.get("source"), c.get("consulted_at"), "REAL · NO CONFIRMADO"] for c in kr.get("competitors", [])]
    return cols, rows
def a_csv(cols, rows, meta=None):
    o = io.StringIO(); w = csv.writer(o, lineterminator="\n")
    for k, v in (meta or {}).items(): w.writerow([celda("# %s: %s" % (k, v))])
    w.writerow([celda(c) for c in cols]); [w.writerow([celda(x) for x in r]) for r in rows]
    return o.getvalue()
def a_html(titulo, cols, rows, meta=None):
    e = html.escape
    m = "".join("<li>%s: %s</li>" % (e(str(k)), e(str(v))) for k, v in (meta or {}).items())
    th = "".join("<th scope=\"col\">%s</th>" % e(str(c)) for c in cols); tr = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % e("" if x is None else str(x)) for x in r) for r in rows)
    return "<!doctype html><html lang=\"es\"><meta charset=\"utf-8\"><title>%s</title><h1>%s</h1><ul>%s</ul><table><caption>%s</caption><thead><tr>%s</tr></thead><tbody>%s</tbody></table></html>" % (e(titulo), e(titulo), m, e(titulo), th, tr)
def a_md(titulo, cols, rows, meta=None):
    esc = lambda x: ("" if x is None else str(x)).replace("|", "\\|").replace("\n", " ")
    out = ["# " + esc(titulo), ""] + ["- **%s**: %s" % (esc(k), esc(v)) for k, v in (meta or {}).items()] + ["", "| " + " | ".join(esc(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    return "\n".join(out + ["| " + " | ".join(esc(x) for x in r) + " |" for r in rows]) + "\n"
