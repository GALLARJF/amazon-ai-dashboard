"""V0.7 — rutas /api/v07/*. El servidor aplica sesión y CSRF antes de llamar; aquí: acceso al catálogo y rol. Solo lectura de datos ya obtenidos (sin red, sin gasto)."""
from . import keepa_real as KR, expediente7 as EX, director7 as D7
from .catalog import ACCOUNT_ID


def handle(APP, s, method, path, q, b):
    g = lambda k: (q.get(k) or [None])[0]
    if not APP["store"].can_access(s, ACCOUNT_ID): raise PermissionError("sin acceso al catálogo")
    p = path[len("/api/v07/"):]
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
            if fmt == "md": return ("raw", EX.to_markdown(d).encode("utf-8"), "text/markdown; charset=utf-8", {})
            return d
    raise LookupError(p)
