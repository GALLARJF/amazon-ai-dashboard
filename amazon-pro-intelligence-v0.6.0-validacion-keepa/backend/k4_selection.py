"""K4 · selección de los 5 competidores de referencia: automática desde K3 (justificada) + ajustes manuales AUDITADOS (motivo ≥ 8 caracteres, aprobador).
Regla automática: los 5 con mayor equivalencia ESTIMADA entre PREMIUM y FUNCIONAL ESPECIALIZADO (desempate: precio vigente disponible, ASIN real). Nunca se seleccionan NO COMPARABLE ni PENDIENTE."""
from .k4_store import now

N = 5
ELEGIBLES = ("premium", "funcional")
MIN_MOTIVO = 8


def _rank(r):
    espec = 1 if (r["codigo"] == "premium" or (r["codigo"] == "funcional" and r.get("subgrupo") == "ESPECIALIZADO")) else 0
    vig = 1 if r["price_class"] in ("ACTUAL", "RECIENTE") and r["price_100ml"] is not None else 0
    return (espec, r["equivalencia"], vig, 1 if r["asin"] else 0)


def justificar(r, pos):
    a = r["automatic"]
    return "#%d por equivalencia ESTIMADA %.1f/100 (confianza %s) en el segmento %s%s; %s." % (pos, r["equivalencia"], (r["confianza"] or {}).get("nivel", "n/d"), r["segmento"], (" · " + r["subgrupo"].lower()) if r.get("subgrupo") and r["codigo"] == "funcional" else "",
        "precio vigente disponible" if r["price_class"] in ("ACTUAL", "RECIENTE") and r["price_100ml"] is not None else "SIN precio vigente (no entra en estadísticos)")


class Selection:
    def __init__(self, k4):
        self.k = k4

    def ajustes(self, producto, pais):
        return self.k.q("SELECT * FROM k4_selection WHERE producto=? AND pais=? ORDER BY id", (producto, pais))

    def seleccionar(self, rows, producto, pais):
        """rows: filas K3 (todas). Devuelve {seleccion:[...], excluidas_manual:[...], ajustes:[...]}"""
        pool = [r for r in rows if r["codigo"] in ELEGIBLES and (not pais or r["country"] == pais)]
        pool.sort(key=_rank, reverse=True); auto = pool[:N]; by = {r["key"]: r for r in rows}
        keys = [r["key"] for r in auto]; origen = {r["key"]: "K3 automática" for r in auto}
        for a in self.ajustes(producto, pais or "ES"):
            if a["accion"] == "QUITAR" and a["key"] in keys: keys.remove(a["key"]); origen.pop(a["key"], None)
            elif a["accion"] == "ANADIR" and a["key"] not in keys and a["key"] in by: keys.append(a["key"]); origen[a["key"]] = "ajuste manual de %s (%s)" % (a["actor"], a["creado"][:10])
        keys = keys[:N]
        sel = []
        for i, k in enumerate(keys, 1):
            r = by[k]; sel.append({"key": k, "posicion": i, "origen_seleccion": origen.get(k, "K3 automática"), "justificacion": justificar(r, i) if origen.get(k) == "K3 automática" else "Incluido manualmente; motivo en el registro de ajustes (equivalencia K3 %.1f, segmento %s)." % (r["equivalencia"], r["segmento"])})
        return {"seleccion": sel, "ajustes": self.ajustes(producto, pais or "ES"), "regla": "Top %d por equivalencia ESTIMADA (premium y funcional especializado). Es revisable con ajustes auditados." % N}

    def ajustar(self, producto, pais, key, accion, motivo, actor, rows):
        if accion not in ("ANADIR", "QUITAR"): raise ValueError("acción inválida")
        if len(str(motivo or "").strip()) < MIN_MOTIVO: raise ValueError("el motivo debe tener al menos %d caracteres" % MIN_MOTIVO)
        r = next((x for x in rows if x["key"] == key), None)
        if not r: raise LookupError("competidor inexistente")
        if accion == "ANADIR" and r["codigo"] in ("nocomparable", "pendiente"): raise ValueError("no se puede seleccionar un competidor NO COMPARABLE o PENDIENTE")
        cur = self.seleccionar(rows, producto, pais)["seleccion"]
        if accion == "ANADIR" and any(s["key"] == key for s in cur): raise ValueError("ya está seleccionado")
        if accion == "ANADIR" and len(cur) >= N: raise ValueError("ya hay %d competidores: quita uno antes de añadir" % N)
        if accion == "QUITAR" and not any(s["key"] == key for s in cur): raise ValueError("no está seleccionado")
        self.k.x("INSERT INTO k4_selection(producto,pais,key,accion,motivo,actor,creado) VALUES(?,?,?,?,?,?,?)", (producto, pais, key, accion, str(motivo).strip()[:300], actor, now()))
        self.k.audit(actor, "k4.seleccion." + accion.lower(), {"producto": producto, "pais": pais, "key": key, "motivo": str(motivo)[:120]})
