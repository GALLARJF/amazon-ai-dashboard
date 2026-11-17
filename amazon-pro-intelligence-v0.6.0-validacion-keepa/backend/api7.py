"""V0.7 — rutas /api/v07/*. El servidor aplica sesión y CSRF antes de llamar; aquí: acceso al catálogo y rol. Solo lectura de datos ya obtenidos (sin red, sin gasto)."""
from . import keepa_real as KR, expediente7 as EX, director7 as D7, export100 as XP, plan100 as PL, respaldo100 as RB
from .catalog import ACCOUNT_ID


def handle(APP, s, method, path, q, b):
    g = lambda k: (q.get(k) or [None])[0]
    p = path[len("/api/v07/"):]
    if p.startswith("respaldo"):   # V1.0 cloud: exportar/subir respaldos FUERA del disco del servidor (solo administrador)
        if s["role"] != "admin": raise PermissionError("solo el administrador gestiona respaldos")
        st = APP["store"]
        if method == "GET" and p == "respaldo":
            data, sha = RB.exportar_bytes(st.path); st.audit(None, s["username"], "backup.export", {"sha256": sha, "bytes": len(data)})
            return ("raw", data, "application/octet-stream", {"Content-Disposition": 'attachment; filename="respaldo.db"', "X-Backup-SHA256": sha, "X-Content-Type-Options": "nosniff"})
        if method == "POST" and p == "respaldo/subir":
            import base64, zlib
            try: raw = zlib.decompress(base64.b64decode(str((b or {}).get("content_b64_zlib") or ""), validate=True), 0, 50_000_000)
            except Exception: raise ValueError("contenido inválido (se espera base64 de zlib)")
            try: r = RB.guardar_pendiente(st.path, raw, str((b or {}).get("sha256") or ""))
            except RB.RespaldoError as e: raise ValueError(str(e))
            st.audit(None, s["username"], "backup.upload", {"sha256": (b or {}).get("sha256"), "bytes": len(raw)})
            return {**r, "aviso": "Se aplicará al REINICIAR el servicio (en Render: Manual Deploy → Restart). La base actual se conserva como copia previa."}
        raise LookupError(p)
    if not APP["store"].can_access(s, ACCOUNT_ID): raise PermissionError("sin acceso al catálogo")
    if method == "GET":
        if p == "keepa-real":
            pid = g("product")
            if not APP["catalog"].get(pid or ""): raise LookupError("producto inexistente")
            return KR.load(pid)
        if p == "briefing": return D7.briefing(APP, g("product"))
        if p == "expediente":
            fmt = g("fmt") or "json"
            if fmt not in ("json", "md"): raise ValueError("fmt debe ser json o md")
            d = EX.build(APP, g("product"))
            if fmt == "md": return ("raw", EX.to_markdown(d).encode("utf-8"), "text/markdown; charset=utf-8", {"Content-Disposition": 'attachment; filename="expediente_v07_%s.md"' % d["product_id"]})
            return d
        if p == "plan": return PL.build(APP, g("product"))
        if p == "export":
            pid = g("product"); fmt = g("fmt") or "csv"
            if fmt not in ("csv", "html", "md"): raise ValueError("fmt debe ser csv, html o md")
            if not APP["catalog"].get(pid or ""): raise LookupError("producto inexistente")
            kr = KR.load(pid); cols, rows = XP.competidores_filas(kr)
            meta = {"producto": pid, "estado": kr.get("state"), "fuente": kr.get("source"), "consultado": kr.get("consulted_at"), "aviso": "Datos reales de Keepa; comparabilidad NO CONFIRMADA; sin gasto en esta exportación"}
            body = {"csv": XP.a_csv, "html": lambda c, r, m: XP.a_html("Competidores " + str(pid), c, r, m), "md": lambda c, r, m: XP.a_md("Competidores " + str(pid), c, r, m)}[fmt]
            ct = {"csv": "text/csv; charset=utf-8", "html": "text/html; charset=utf-8", "md": "text/markdown; charset=utf-8"}[fmt]
            return ("raw", body(cols, rows, meta).encode("utf-8"), ct, {"Content-Disposition": 'attachment; filename="%s"' % XP.nombre("competidores_" + str(pid), fmt), "X-Content-Type-Options": "nosniff"})
    raise LookupError(p)
