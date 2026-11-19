"""K4 · exportación ejecutiva PDF (stdlib) y SVG con control de fuentes y derechos. Una imagen SOLO sale si está VERIFICADA con derecho «exportar» y copia local; si no, marcador con la autorización que falta.
Cada exportación queda en la auditoría. El PNG se genera en el navegador a partir del SVG (sin dependencias)."""
import base64, textwrap
from xml.sax.saxutils import escape
from .k4_store import now


def _lineas(ctx, d, bm):
    L = [("h1", "AHT · Amazon Pro Intelligence · Informe ejecutivo K4"), ("t", "Producto: %s · País: %s · Entorno: %s · Generado: %s" % (ctx["producto"], ctx["pais"], ctx["entorno"], now())), ("t", "")]
    L += [("h2", "Dictamen de precio: %s (tipo %d) · confianza %s" % (d["tipo_nombre"], d["tipo"], d["confianza"]))]
    pa = d["precio_actual"]; L.append(("t", "PVP propuesto: %s € (%s)" % (pa.get("pvp_propuesto"), pa.get("estado"))))
    if d.get("intervalo_recomendado"): iv = d["intervalo_recomendado"]; L.append(("t", "Intervalo: %.2f–%.2f € (%s)" % (iv["min"], iv["max"], iv["base"])))
    for a in d["justificacion"]: L.append(("t", "[%s] %s" % (a["clase"], a["texto"])))
    L += [("t", "Acción propuesta: " + d["proxima_accion"]), ("t", "Criterio de revisión: " + d["criterio_revision"]), ("t", "")]
    if d["faltantes"]:
        L.append(("h2", "Datos faltantes y cómo obtenerlos"))
        for f in d["faltantes"]: L.append(("t", "- %s → %s" % (f["dato"], f["como"])))
    if d["riesgos"]:
        L.append(("h2", "Riesgos"))
        for r in d["riesgos"]: L.append(("t", "- " + r))
    L.append(("h2", "Benchmarking (%d referencias)" % len(bm["items"])))
    for it in bm["items"][:25]:
        im = it["imagen"]; L.append(("t", "- %s · %s · %s · eq. %s · %s €/100 ml [%s]%s" % (it["segmento"], it["marca"] or "n/d", it["asin"] or "sin ASIN", it["equivalencia"], it["precio_100ml"] if it["precio_100ml"] is not None else "SIN PRECIO", it["clase_precio"], "" if im["estado"] == "VERIFICADA" else " · IMAGEN PENDIENTE DE VERIFICAR")))
    L += [("t", ""), ("h2", "Fuentes y derechos"), ("t", "Fuentes: " + "; ".join(d["fuentes"])), ("t", "Las imágenes se omiten salvo derecho de exportación verificado. Datos sintéticos: " + ("SÍ (SINTETICO_DEMO)" if ctx["entorno"] != "PRODUCCION" else "NO")),
          ("t", "Equivalencia K3 ESTIMADA; no es validación comercial independiente. Ningún precio se ha modificado en Amazon.")]
    return L


def _pdf(lines):
    pages, cur, y = [], [], 800
    def esc(s): return s.replace("≥", ">=").replace("≤", "<=").replace("→", "->").replace("≈", "~").replace("∩", "y").encode("cp1252", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    for kind, txt in lines:
        sz, w = (15, 70) if kind == "h1" else (11, 90) if kind == "h2" else (9, 105)
        for ln in (textwrap.wrap(txt, w) or [""]):
            if y < 50: pages.append(cur); cur, y = [], 800
            cur.append("BT /F%d %d Tf 40 %d Td (%s) Tj ET" % (2 if kind != "t" else 1, sz, y, esc(ln))); y -= sz + 4
    pages.append(cur); objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join("%d 0 R" % (5 + 2 * i) for i in range(len(pages)))
    objs.append(("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(pages))).encode())
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    for i, pg in enumerate(pages):
        objs.append(("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>" % (6 + 2 * i)).encode())
        c = "\n".join(pg).encode("latin-1"); objs.append(b"<< /Length %d >>\nstream\n" % len(c) + c + b"\nendstream")
    out = bytearray(b"%PDF-1.4\n"); offs = []
    for i, o in enumerate(objs, 1): offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out); out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs: out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, x)
    return bytes(out)


def _svg(K, ctx, d, bm):
    h = 120 + 78 * min(len(bm["items"]), 14) + 70; r = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="%d" font-family="Helvetica,Arial,sans-serif"><rect width="100%%" height="100%%" fill="#0b1020"/>' % h,
        '<text x="24" y="36" fill="#e6f1ff" font-size="20">AHT · K4 · %s · %s</text>' % (escape(ctx["producto"]), escape(ctx["pais"])),
        '<text x="24" y="62" fill="#7ee0ff" font-size="14">Dictamen: %s · confianza %s</text>' % (escape(d["tipo_nombre"]), d["confianza"]), '<text x="24" y="84" fill="#9fb3d1" font-size="12">%s</text>' % escape(d["proxima_accion"][:120])]
    y = 110
    for it in bm["items"][:14]:
        im = it["imagen"]; r.append('<rect x="24" y="%d" width="852" height="70" rx="8" fill="#121a33" stroke="#1f2b52"/>' % y)
        pend = True
        if im["estado"] == "VERIFICADA" and im["derechos"].get("exportar") and im.get("tiene_copia"):
            try:
                mime, raw = K.media.file(im["id"], "exportar"); r.append('<image x="32" y="%d" width="54" height="54" href="data:%s;base64,%s"/>' % (y + 8, mime, base64.b64encode(raw).decode())); pend = False
            except Exception: pass
        if pend: r.append('<rect x="32" y="%d" width="54" height="54" fill="none" stroke="#ffb454" stroke-dasharray="4"/><text x="34" y="%d" fill="#ffb454" font-size="7">IMAGEN PENDIENTE</text>' % (y + 8, y + 38))
        r.append('<text x="100" y="%d" fill="#e6f1ff" font-size="13">%s · %s</text>' % (y + 26, escape(it["segmento"]), escape((it["marca"] or "n/d") + " " + (it["asin"] or "sin ASIN"))))
        r.append('<text x="100" y="%d" fill="#9fb3d1" font-size="11">eq. %s · %s €/100 ml [%s]</text>' % (y + 46, it["equivalencia"], it["precio_100ml"] if it["precio_100ml"] is not None else "SIN PRECIO", escape(it["clase_precio"])))
        y += 78
    r.append('<text x="24" y="%d" fill="#6c7da3" font-size="10">Fuentes: %s · Imágenes solo con derecho de exportación verificado · Equivalencia estimada</text></svg>' % (y + 20, escape("; ".join(d["fuentes"])[:150])))
    return "".join(r).encode("utf-8")


def exportar(K, ctx, d, bm, fmt, actor):
    n_img = sum(1 for it in bm["items"] if it["imagen"]["estado"] == "VERIFICADA" and it["imagen"]["derechos"].get("exportar"))
    K.k.audit(actor, "k4.export", {"fmt": fmt, "producto": ctx["producto"], "pais": ctx["pais"], "imagenes_exportadas": n_img, "entorno": ctx["entorno"]})
    if fmt == "pdf": return _pdf(_lineas(ctx, d, bm)), "application/pdf", "k4_%s_%s.pdf" % (ctx["producto"], ctx["pais"])
    return _svg(K, ctx, d, bm), "image/svg+xml", "k4_%s_%s.svg" % (ctx["producto"], ctx["pais"])
