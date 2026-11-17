"""V0.7 — rutas /api/v07/*. El servidor aplica sesión y CSRF antes de llamar; aquí: acceso al catálogo y rol. Solo lectura de datos ya obtenidos (sin red, sin gasto)."""
from . import keepa_real as KR
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
    raise LookupError(p)
