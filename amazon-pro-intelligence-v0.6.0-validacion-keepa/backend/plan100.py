"""V1.0 (V1-07) — Plan determinista de coordinación de especialistas del Director IA. Deriva del expediente V0.7 (hechos y desbloqueos reales); sin IA, sin red, sin gasto.
Un especialista queda BLOQUEADO si su sección lo está, EN ESPERA si depende de otro bloqueado, y solo entonces LISTO_PARA_TRABAJAR. El plan NUNCA emite GO."""
from . import expediente7 as EX

ESPECIALISTAS = [  # id, nombre, sección del expediente, depende de, entradas, salidas
    ("mercado", "Analista de mercado", "mercado", [], ["competidores Keepa reales", "confirmación manual de comparabilidad"], ["mediana de precio por 100 mL", "competidores comparables confirmados"]),
    ("finanzas", "Analista financiero", "economia", [], ["costes reales (producto, logística, comisión)", "PVP objetivo"], ["contribución por unidad", "ACoS de equilibrio", "escenarios y sensibilidad"]),
    ("regulatorio", "Responsable regulatorio", "regulatorio", [], ["PIF e informe de seguridad", "evidencia de cada claim"], ["claims permitidos", "requisitos cumplidos"]),
    ("listing", "Redactor de listing", "regulatorio", ["regulatorio", "mercado"], ["claims permitidos", "posicionamiento frente a competidores"], ["borrador de listing sin claims no probados"]),
    ("ads", "Especialista en publicidad", "economia", ["finanzas", "mercado"], ["ACoS de equilibrio", "competidores confirmados"], ["plan de campañas (no se crea ninguna)"]),
    ("operaciones", "Operaciones e inventario", "producto", ["finanzas"], ["stock verificado", "plazo de reposición", "MOQ"], ["punto de pedido", "calendario de lanzamiento"]),
]
def build(APP, pid):
    ex = EX.build(APP, pid); sec = {s["id"]: s for s in ex["sections"]}; pend = ex["unlocks"]
    OK = ("COMPLETO", "CALCULADO", "REAL", "VERIFICADO")
    lis = {}; out = []
    for sid, nombre, sc, deps, ent, sal in ESPECIALISTAS:
        s = sec.get(sc, {}); st = str(s.get("state", "SIN DATOS")); mios = [u for u in pend if sc in u["unblocks"]]
        propio_ok = bool(not mios and st.startswith(OK))
        lis[sid] = propio_ok
        out.append({"id": sid, "nombre": nombre, "seccion": sc, "estado_seccion": st, "depende_de": deps, "entradas": ent, "salidas": sal, "bloqueos": [{"id": u["id"], "accion": u["title"], "propietario": u["owner"], "coste_eur": u["cost_eur"], "tokens_keepa": u["keepa_tokens"], "requiere_aprobacion": u["requires_approval"]} for u in mios]})
    for e in out:
        esperando = [d for d in e["depende_de"] if not lis.get(d)]
        e["estado"] = "BLOQUEADO" if e["bloqueos"] else ("EN ESPERA" if esperando else ("COMPLETADO" if lis[e["id"]] else "LISTO PARA TRABAJAR"))
        e["espera_a"] = esperando
    orden, hechos = [], set()
    while len(orden) < len(out):   # orden topológico estable
        prog = False
        for e in out:
            if e["id"] not in hechos and all(d in hechos for d in e["depende_de"]): orden.append(e["id"]); hechos.add(e["id"]); prog = True
        if not prog: raise ValueError("dependencias cíclicas")
    return {"product_id": pid, "veredicto": ex["verdict"], "go": False, "especialistas": out, "orden": orden,
            "siguiente": next((e["id"] for e in out if e["estado"] == "LISTO PARA TRABAJAR"), None),
            "nota": "Plan derivado del expediente; el Director no emite GO mientras existan bloqueos. Las acciones con propietario y coste requieren tu aprobación; nada se ejecuta solo.", "network_calls": 0, "tokens_spent_now": 0, "cost_now_eur": 0.0}
