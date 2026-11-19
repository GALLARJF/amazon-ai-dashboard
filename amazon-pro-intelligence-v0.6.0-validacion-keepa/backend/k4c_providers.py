"""K4 · Consejero Estratégico · F1 — interfaces INDEPENDIENTES DEL PROVEEDOR + router con permisos, estados y presupuesto.
Roles: llm · busqueda · lectura · herramienta · verificador. Un proveedor REAL (modo != SIMULADO) está BLOQUEADO mientras no exista autorización expresa (flag `autorizacion_externa`, hoy siempre falsa)
y mientras el tope de gasto sea 0. Toda llamada queda registrada (k4c_consulta). Sin credenciales reales en este código."""
import time
from .k4_store import now

ROLES = ("llm", "busqueda", "lectura", "herramienta", "verificador")
ESTADOS = ("OPERATIVA", "NO_OPERATIVA", "REQUIERE_AUTORIZACION")
MODOS = ("SIMULADO", "LOCAL", "REAL")


class Proveedor:
    rol = None; nombre = "base"; modo = "SIMULADO"
    def estado(self): return {"estado": "NO_OPERATIVA", "motivo": "no implementado"}
    def coste_estimado(self, **kw): return 0.0
    def contrato(self): return {"rol": self.rol, "nombre": self.nombre, "modo": self.modo}


class ProveedorLLM(Proveedor):
    rol = "llm"
    def completar(self, sistema, usuario, esquema=None):
        """-> {'json': dict|None, 'texto': str, 'tokens_in': int, 'tokens_out': int, 'coste_eur': float, 'modo': str}"""
        raise NotImplementedError

class ProveedorBusqueda(Proveedor):
    rol = "busqueda"
    def buscar(self, consulta, max_resultados=5):
        """-> [{'url','titulo','snippet','fecha'}]"""
        raise NotImplementedError

class ProveedorLectura(Proveedor):
    rol = "lectura"
    def leer(self, url):
        """-> {'url','titulo','texto','fecha_publicacion','tipo_fuente','organismo','calidad','tipo_dato'}"""
        raise NotImplementedError

class Herramienta(Proveedor):
    rol = "herramienta"
    def ejecutar(self, **args): raise NotImplementedError

class VerificadorBase(Proveedor):
    rol = "verificador"
    def verificar(self, informe, libro, hoy=None): raise NotImplementedError


class AdaptadorLLMExterno(ProveedorLLM):
    """Envuelve el adaptador `ai.py` ya existente (OpenAI/Anthropic/openai_compat). NO OPERATIVO hasta autorización: no hace ninguna llamada de red."""
    nombre = "ai.py"; modo = "REAL"
    def __init__(self, cfg): self.cfg = cfg
    def estado(self): return {"estado": "REQUIERE_AUTORIZACION", "motivo": "IA externa desactivada y gasto 0 €; requiere autorización expresa, clave en el servidor y tope"}
    def completar(self, sistema, usuario, esquema=None): raise PermissionError("IA externa no autorizada")

class BusquedaExternaNoImplementada(ProveedorBusqueda):
    nombre = "busqueda_externa"; modo = "REAL"
    def estado(self): return {"estado": "NO_OPERATIVA", "motivo": "adaptador real previsto en F3 (búsqueda de pago desactivada)"}
    def buscar(self, consulta, max_resultados=5): raise PermissionError("búsqueda externa no autorizada")

class LecturaExternaNoImplementada(ProveedorLectura):
    nombre = "lectura_externa"; modo = "REAL"
    def estado(self): return {"estado": "NO_OPERATIVA", "motivo": "adaptador real previsto en F3 (hosts permitidos)"}
    def leer(self, url): raise PermissionError("lectura externa no autorizada")


class Router:
    def __init__(self, k4, autorizacion_externa=False, clock=time.time):
        self.k = k4; self.reg = {}; self.autorizacion_externa = bool(autorizacion_externa); self.clock = clock
        k4.s.db.executescript("""CREATE TABLE IF NOT EXISTS k4c_consulta(id INTEGER PRIMARY KEY AUTOINCREMENT, inv_id TEXT, ts TEXT, rol TEXT, proveedor TEXT, metodo TEXT, consulta TEXT, n_resultados INTEGER, coste_eur REAL, estado TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS k4c_cfg(k TEXT PRIMARY KEY, v TEXT);"""); k4.s.db.commit()
        for k, v in (("tope_inv_eur", "0"), ("tope_mes_eur", "0")):
            if not k4.q("SELECT 1 FROM k4c_cfg WHERE k=?", (k,)): k4.x("INSERT INTO k4c_cfg VALUES(?,?)", (k, v))

    def registrar(self, proveedor, alias=None):
        if proveedor.rol not in ROLES: raise ValueError("rol desconocido")
        if proveedor.modo not in MODOS: raise ValueError("modo desconocido")
        self.reg[(proveedor.rol, alias or proveedor.nombre)] = proveedor

    def proveedor(self, rol, nombre=None):
        c = [v for (r, n), v in self.reg.items() if r == rol and (nombre is None or n == nombre)]
        if not c: raise LookupError("sin proveedor para " + rol)
        return c[0]

    def limites(self, tope_inv=None, tope_mes=None, actor="sistema"):
        for k, v in (("tope_inv_eur", tope_inv), ("tope_mes_eur", tope_mes)):
            if v is not None:
                if v < 0: raise ValueError("tope inválido")
                self.k.x("UPDATE k4c_cfg SET v=? WHERE k=?", (str(v), k)); self.k.audit(actor, "k4c.limite", {k: v})
        g = {r["k"]: float(r["v"]) for r in self.k.q("SELECT * FROM k4c_cfg")}
        gm = self.k.q("SELECT COALESCE(SUM(coste_eur),0) s FROM k4c_consulta WHERE ts>=?", (now()[:7],))[0]["s"]
        return {"tope_inv_eur": g["tope_inv_eur"], "tope_mes_eur": g["tope_mes_eur"], "gasto_mes_eur": gm}

    def gasto_inv(self, inv_id): return self.k.q("SELECT COALESCE(SUM(coste_eur),0) s FROM k4c_consulta WHERE inv_id=?", (inv_id,))[0]["s"]

    def estado(self):
        out = []
        for (r, n), p in sorted(self.reg.items()):
            e = dict(p.estado()); real = p.modo == "REAL"
            if real and not self.autorizacion_externa and e["estado"] == "OPERATIVA": e = {"estado": "REQUIERE_AUTORIZACION", "motivo": "proveedor REAL sin autorización expresa"}
            out.append(dict(rol=r, nombre=n, modo=p.modo, **e))
        return {"proveedores": out, "limites": self.limites(), "autorizacion_externa": self.autorizacion_externa, "gasto_adicional_autorizado_eur": 0}

    def llamar(self, rol, metodo, inv_id=None, nombre=None, **args):
        p = self.proveedor(rol, nombre); consulta = str(args.get("consulta") or args.get("url") or args.get("usuario") or args.get("nombre") or metodo)[:300]
        def log(est, n=None, coste=0.0, err=None): self.k.x("INSERT INTO k4c_consulta(inv_id,ts,rol,proveedor,metodo,consulta,n_resultados,coste_eur,estado,error) VALUES(?,?,?,?,?,?,?,?,?,?)", (inv_id, now(), rol, p.nombre, metodo, consulta, n, coste, est, err))
        if p.modo == "REAL" and not self.autorizacion_externa: log("BLOQUEADA_SIN_AUTORIZACION", err="proveedor REAL sin autorización"); raise PermissionError("proveedor REAL sin autorización expresa")
        st = p.estado()
        if st["estado"] != "OPERATIVA": log("NO_OPERATIVA", err=st.get("motivo")); raise PermissionError("proveedor no operativo: " + str(st.get("motivo")))
        est = p.coste_estimado(**args); lim = self.limites()
        if est > 0 and (self.gasto_inv(inv_id) + est > lim["tope_inv_eur"] + 1e-9 or lim["gasto_mes_eur"] + est > lim["tope_mes_eur"] + 1e-9): log("BLOQUEADA_PRESUPUESTO", coste=0.0, err="coste %.4f € supera el tope" % est); raise PermissionError("presupuesto insuficiente")
        try: res = getattr(p, metodo)(**args)
        except Exception as e: log("ERROR", err=type(e).__name__ + ": " + str(e)[:150]); raise
        coste = float(res.get("coste_eur", est)) if isinstance(res, dict) else est
        log("OK", n=(len(res) if isinstance(res, list) else 1), coste=coste); return res
