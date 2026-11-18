"""K4 · ficha de costes faltantes con fuente, fecha, unidad, moneda y estado de validación + guarda anti-duplicación.
El coste histórico de 10,03 €/ud es PARCIAL/DESCONOCIDO en alcance: se registra como TOTAL con `incluye` sin confirmar y NO se suma a componentes
hasta que AHT declare qué contiene. Si se declara un total con `incluye`, añadir un componente ya incluido se rechaza (duplicación)."""
from . import eu
from .k4_store import now

CONCEPTOS = ["cogs", "inbound", "prep", "fulfillment", "storage", "returns", "referral", "promo", "other", "ads_acos"]
FICHA = ["cogs", "inbound", "prep", "fulfillment", "storage", "returns", "promo", "other"]  # la comisión Amazon sale de la tarifa verificada (eu.REFERRAL_SRC) y Ads es un dato de campaña, no un coste unitario
ESTADOS_VAL = ("PENDIENTE_VALIDAR", "VALIDADO", "RECHAZADO")
HIST = {"producto": "PRD-ACTIVCORE-V2", "concepto": "cogs", "valor": 10.03, "unidad": "EUR/ud", "moneda": "EUR", "fuente": "Coste unitario histórico documentado por AHT (sin IVA); alcance NO confirmado",
        "fecha": "2026-11-16", "estado_validacion": "PENDIENTE_VALIDAR", "es_total": 1, "incluye": []}


class Costs:
    def __init__(self, k4):
        self.k = k4

    def seed(self):
        if not self.k.q("SELECT 1 FROM k4_costs WHERE producto=? AND valor=10.03", (HIST["producto"],)):
            self.add(HIST, actor="sistema", _seed=True)

    def add(self, d, actor, _seed=False):
        for k in ("producto", "concepto", "unidad", "moneda", "fuente", "fecha"):
            if not d.get(k): raise ValueError("falta " + k)
        if d["concepto"] not in CONCEPTOS: raise ValueError("concepto desconocido")
        v = d.get("valor")
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0): raise ValueError("valor inválido")
        est = d.get("estado_validacion", "PENDIENTE_VALIDAR")
        if est not in ESTADOS_VAL: raise ValueError("estado de validación inválido")
        inc = list(d.get("incluye") or [])
        if any(c not in CONCEPTOS for c in inc): raise ValueError("incluye contiene conceptos desconocidos")
        es_total = 1 if d.get("es_total") else 0
        # guarda de duplicación
        for r in self.k.q("SELECT * FROM k4_costs WHERE producto=? AND vigente=1 AND es_total=1 AND estado_validacion!='RECHAZADO'", (d["producto"],)):
            ya = set(__import__("json").loads(r["incluye"]))
            if not es_total and d["concepto"] in ya:
                raise ValueError(f"duplicación: el total #{r['id']} ya incluye «{d['concepto']}»; retire el total o excluya el concepto")
        if es_total and not inc and not _seed:
            raise ValueError("un coste total exige declarar qué conceptos incluye")
        c = self.k.x("INSERT INTO k4_costs(producto,concepto,valor,unidad,moneda,fuente,fecha,estado_validacion,incluye,es_total,pais,nota,creado_por,creado) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (d["producto"], d["concepto"], v, d["unidad"], d["moneda"], d["fuente"], d["fecha"], est, self.k.j(inc), es_total, d.get("pais"), (d.get("nota") or "")[:300], actor, now()))
        self.k.audit(actor, "k4.coste.alta", {"id": c.lastrowid, "producto": d["producto"], "concepto": d["concepto"], "estado": est})
        return c.lastrowid

    def validate(self, cid, estado, actor, incluye=None):
        if estado not in ESTADOS_VAL: raise ValueError("estado inválido")
        r = self.k.q("SELECT * FROM k4_costs WHERE id=?", (cid,))
        if not r: raise LookupError("coste inexistente")
        if incluye is not None:
            if any(c not in CONCEPTOS for c in incluye): raise ValueError("incluye inválido")
            self.k.x("UPDATE k4_costs SET incluye=? WHERE id=?", (self.k.j(incluye), cid))
        self.k.x("UPDATE k4_costs SET estado_validacion=? WHERE id=?", (estado, cid))
        self.k.audit(actor, "k4.coste.validacion", {"id": cid, "estado": estado})

    def ficha(self, producto):
        """Ficha de costes faltantes: una fila por concepto con valor vigente, estado y qué falta."""
        rows = self.k.q("SELECT * FROM k4_costs WHERE producto=? AND vigente=1 AND estado_validacion!='RECHAZADO' ORDER BY id", (producto,))
        out = []
        tot = [r for r in rows if r["es_total"]]
        for c in FICHA:
            own = [r for r in rows if r["concepto"] == c and not r["es_total"]]
            cov = [r for r in tot if c in __import__("json").loads(r["incluye"])]
            amb = [r for r in tot if r["concepto"] == c and not __import__("json").loads(r["incluye"])]
            it = (own or cov or amb or [None])[0]
            if it is None:
                out.append({"concepto": c, "etiqueta": eu.LABEL.get(c, c), "estado": "FALTA", "valor": None, "unidad": None, "moneda": None, "fuente": None, "fecha": None, "accion": "Aportar valor con fuente y fecha (factura, tarifa oficial o export de Seller Central)"})
            else:
                aviso = "Alcance del total NO confirmado: declarar qué conceptos incluye antes de usarlo en márgenes" if (it in amb) else None
                out.append({"concepto": c, "etiqueta": eu.LABEL.get(c, c), "estado": it["estado_validacion"], "valor": it["valor"], "unidad": it["unidad"], "moneda": it["moneda"], "fuente": it["fuente"], "fecha": it["fecha"],
                            "id": it["id"], "es_total": bool(it["es_total"]), "incluye": __import__("json").loads(it["incluye"]), "accion": aviso or ("Validar" if it["estado_validacion"] == "PENDIENTE_VALIDAR" else None)})
        return out

    def assumptions(self, producto, pais):
        """Supuestos para eu.unit_economics. Solo se usa un coste si está VALIDADO (→DOCUMENTADO) o es el histórico con alcance de COGS (→HISTORICO_A_REVALIDAR). Nunca se inventan."""
        a = eu.default_assumptions([pais])[pais]
        for k in ("cogs", "inbound", "prep", "fulfillment", "storage", "returns", "promo", "other"):
            a[k] = eu.fld()
        for it in self.ficha(producto):
            c = it["concepto"]
            if it["estado"] == "FALTA" or it.get("valor") is None or c not in a or c in ("referral", "ads_acos"): continue
            if it["estado"] == "VALIDADO":
                a[c] = eu.fld(it["valor"], "DOCUMENTADO", it["fuente"], it["fecha"])
            elif c == "cogs":  # histórico pendiente: se usa como hipótesis revalidable para COGS solamente
                a[c] = eu.fld(it["valor"], "HISTORICO_A_REVALIDAR", it["fuente"], it["fecha"])
        return a
