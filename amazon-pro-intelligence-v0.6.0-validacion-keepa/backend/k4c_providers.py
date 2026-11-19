"""K4 · Consejero Estratégico · F1 — interfaces INDEPENDIENTES DEL PROVEEDOR + router con permisos, estados y presupuesto.
Roles: llm · busqueda · lectura · herramienta · verificador. Un proveedor REAL (modo != SIMULADO) está BLOQUEADO mientras no exista autorización expresa (flag `autorizacion_externa`, hoy siempre falsa)
y mientras el tope de gasto sea 0. Toda llamada queda registrada (k4c_consulta). Sin credenciales reales en este código."""
import threading, time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from .k4_store import now

ROLES = ("llm", "busqueda", "lectura", "herramienta", "verificador")
ESTADOS = ("OPERATIVA", "NO_OPERATIVA", "REQUIERE_AUTORIZACION")
MODOS = ("SIMULADO", "LOCAL", "REAL")


class Proveedor:
    rol = None; nombre = "base"; modo = "SIMULADO"
    def estado(self): return {"estado": "NO_OPERATIVA", "motivo": "no implementado"}
    def coste_estimado(self, **kw): return 0.0
    def coste_maximo(self, **kw): return self.coste_estimado(**kw)
    timeout_s = 20.0; reintentos = 1
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
    """Router con PRESUPUESTO SEGURO: reserva atómica (una sola sentencia SQL condicional), tope por operación/investigación/mes, conciliación del coste real,
    reintentos y timeouts, corte automático y registro auditable. Los proveedores externos siguen NO ACTIVOS: aquí solo se prepara la infraestructura."""
    def __init__(self, k4, autorizacion_externa=False, clock=time.time, sleep=time.sleep):
        self.k = k4; self.reg = {}; self.autorizacion_externa = bool(autorizacion_externa); self.clock = clock; self.sleep = sleep
        k4.s.db.executescript("""CREATE TABLE IF NOT EXISTS k4c_consulta(id INTEGER PRIMARY KEY AUTOINCREMENT, inv_id TEXT, ts TEXT, rol TEXT, proveedor TEXT, metodo TEXT, consulta TEXT, n_resultados INTEGER, coste_eur REAL, estado TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS k4c_cfg(k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE IF NOT EXISTS k4c_reserva(id INTEGER PRIMARY KEY AUTOINCREMENT, inv_id TEXT, rol TEXT, proveedor TEXT, metodo TEXT, intento INTEGER, estimado REAL, maximo REAL, real REAL, estado TEXT, ts TEXT, ts_fin TEXT, mes TEXT, nota TEXT);""")
        k4.s.db.commit()
        for k, v in (("tope_inv_eur", "0"), ("tope_mes_eur", "0"), ("tope_op_eur", "0"), ("corte", "0"), ("corte_motivo", "")):
            if not k4.q("SELECT 1 FROM k4c_cfg WHERE k=?", (k,)): k4.x("INSERT INTO k4c_cfg VALUES(?,?)", (k, v))

    def registrar(self, proveedor, alias=None):
        if proveedor.rol not in ROLES: raise ValueError("rol desconocido")
        if proveedor.modo not in MODOS: raise ValueError("modo desconocido")
        self.reg[(proveedor.rol, alias or proveedor.nombre)] = proveedor

    def proveedor(self, rol, nombre=None):
        c = [v for (r, n), v in self.reg.items() if r == rol and (nombre is None or n == nombre)]
        if not c: raise LookupError("sin proveedor para " + rol)
        return c[0]

    def _cfg(self): return {r["k"]: r["v"] for r in self.k.q("SELECT * FROM k4c_cfg")}

    def limites(self, tope_inv=None, tope_mes=None, tope_op=None, actor="sistema"):
        for k, v in (("tope_inv_eur", tope_inv), ("tope_mes_eur", tope_mes), ("tope_op_eur", tope_op)):
            if v is not None:
                if v < 0: raise ValueError("tope inválido")
                self.k.x("UPDATE k4c_cfg SET v=? WHERE k=?", (str(v), k)); self.k.audit(actor, "k4c.limite", {k: v})
        g = self._cfg(); gm = self.gasto_mes()
        return {"tope_inv_eur": float(g["tope_inv_eur"]), "tope_mes_eur": float(g["tope_mes_eur"]), "tope_op_eur": float(g["tope_op_eur"]), "gasto_mes_eur": gm, "corte_automatico": g["corte"] == "1", "corte_motivo": g["corte_motivo"]}

    _CUENTA = "estado IN ('RESERVADA','CONFIRMADA','EXCEDIDA','INCIERTA')"
    def gasto_inv(self, inv_id): return self.k.q("SELECT COALESCE(SUM(COALESCE(real,maximo)),0) s FROM k4c_reserva WHERE inv_id IS ? AND " + self._CUENTA, (inv_id,))[0]["s"]
    def gasto_mes(self): return self.k.q("SELECT COALESCE(SUM(COALESCE(real,maximo)),0) s FROM k4c_reserva WHERE mes=? AND " + self._CUENTA, (now()[:7],))[0]["s"]

    def reanudar(self, actor, motivo):
        if len(str(motivo or "")) < 10: raise ValueError("motivo obligatorio (≥10 caracteres)")
        self.k.x("UPDATE k4c_cfg SET v='0' WHERE k='corte'"); self.k.audit(actor, "k4c.reanudar", {"motivo": motivo}); return self.limites()

    def _cortar(self, motivo):
        self.k.x("UPDATE k4c_cfg SET v='1' WHERE k='corte'"); self.k.x("UPDATE k4c_cfg SET v=? WHERE k='corte_motivo'", (motivo[:200],)); self.k.audit("sistema", "k4c.corte_automatico", {"motivo": motivo})

    def estado(self):
        out = []
        for (r, n), p in sorted(self.reg.items()):
            e = dict(p.estado()); real = p.modo == "REAL"
            if real and not self.autorizacion_externa and e["estado"] == "OPERATIVA": e = {"estado": "REQUIERE_AUTORIZACION", "motivo": "proveedor REAL sin autorización expresa"}
            out.append(dict(rol=r, nombre=n, modo=p.modo, **e))
        return {"proveedores": out, "limites": self.limites(), "autorizacion_externa": self.autorizacion_externa, "gasto_adicional_autorizado_eur": 0}

    def _reservar(self, inv_id, rol, p, metodo, intento, est, mx):
        """Reserva ATÓMICA: una única sentencia INSERT…SELECT condicionada a los topes (segura entre hilos y procesos). Devuelve id o None."""
        g = self._cfg(); ti, tm = float(g["tope_inv_eur"]), float(g["tope_mes_eur"]); mes = now()[:7]
        with self.k.s.lock:
            cur = self.k.s.db.execute("""INSERT INTO k4c_reserva(inv_id,rol,proveedor,metodo,intento,estimado,maximo,real,estado,ts,mes)
                SELECT ?,?,?,?,?,?,?,NULL,'RESERVADA',?,? WHERE
                (SELECT COALESCE(SUM(COALESCE(real,maximo)),0) FROM k4c_reserva WHERE inv_id IS ? AND estado IN ('RESERVADA','CONFIRMADA','EXCEDIDA','INCIERTA')) + ? <= ? + 1e-9 AND
                (SELECT COALESCE(SUM(COALESCE(real,maximo)),0) FROM k4c_reserva WHERE mes=? AND estado IN ('RESERVADA','CONFIRMADA','EXCEDIDA','INCIERTA')) + ? <= ? + 1e-9""",
                (inv_id, rol, p.nombre, metodo, intento, est, mx, now(), mes, inv_id, mx, ti, mes, mx, tm)); self.k.s.db.commit()
            return cur.lastrowid if cur.rowcount == 1 else None

    def _cerrar(self, rid, estado, real=None, nota=None):
        self.k.x("UPDATE k4c_reserva SET estado=?, real=?, ts_fin=?, nota=? WHERE id=?", (estado, real, now(), nota, rid))

    def llamar(self, rol, metodo, inv_id=None, nombre=None, **args):
        p = self.proveedor(rol, nombre); consulta = str(args.get("consulta") or args.get("url") or args.get("usuario") or args.get("nombre") or metodo)[:300]
        def log(est, n=None, coste=0.0, err=None): self.k.x("INSERT INTO k4c_consulta(inv_id,ts,rol,proveedor,metodo,consulta,n_resultados,coste_eur,estado,error) VALUES(?,?,?,?,?,?,?,?,?,?)", (inv_id, now(), rol, p.nombre, metodo, consulta, n, coste, est, err))
        if p.modo == "REAL" and not self.autorizacion_externa: log("BLOQUEADA_SIN_AUTORIZACION", err="proveedor REAL sin autorización"); raise PermissionError("proveedor REAL sin autorización expresa")
        st = p.estado()
        if st["estado"] != "OPERATIVA": log("NO_OPERATIVA", err=st.get("motivo")); raise PermissionError("proveedor no operativo: " + str(st.get("motivo")))
        cfg = self._cfg()
        if cfg["corte"] == "1": log("BLOQUEADA_CORTE", err=cfg["corte_motivo"]); raise PermissionError("corte automático activo: " + cfg["corte_motivo"])
        est = float(p.coste_estimado(**args)); mx = max(est, float(p.coste_maximo(**args))); top = float(cfg["tope_op_eur"])
        if mx > 0 and mx > top + 1e-9: log("BLOQUEADA_PRESUPUESTO", err="coste máximo %.4f € supera el tope por operación (%.4f)" % (mx, top)); raise PermissionError("coste máximo por operación excede el tope")
        intentos = max(1, int(getattr(p, "reintentos", 1))); ult = None
        for i in range(1, intentos + 1):
            rid = self._reservar(inv_id, rol, p, metodo, i, est, mx)
            if rid is None: log("BLOQUEADA_PRESUPUESTO", err="reserva rechazada: coste máximo %.4f € supera el tope" % mx); raise PermissionError("presupuesto insuficiente")
            ex = ThreadPoolExecutor(max_workers=1)
            try:
                fut = ex.submit(getattr(p, metodo), **args); res = fut.result(timeout=float(getattr(p, "timeout_s", 20.0)))
            except FutTimeout:
                self._cerrar(rid, "INCIERTA", mx, "timeout: el coste real es incierto; se retiene el máximo"); log("TIMEOUT", coste=mx, err="timeout intento %d" % i); ult = TimeoutError("timeout"); ex.shutdown(wait=False)
                if i < intentos: self.sleep(min(2 ** i * 0.1, 2.0)); continue
                raise ult
            except Exception as e:
                self._cerrar(rid, "LIBERADA", 0.0, "error sin coste: " + type(e).__name__); log("ERROR", err="intento %d: %s: %s" % (i, type(e).__name__, str(e)[:150])); ult = e; ex.shutdown(wait=False)
                if i < intentos and not isinstance(e, (PermissionError, LookupError, ValueError)): self.sleep(min(2 ** i * 0.1, 2.0)); continue
                raise
            ex.shutdown(wait=False)
            real = float(res.get("coste_eur", est)) if isinstance(res, dict) else est
            if real > mx + 1e-9:
                self._cerrar(rid, "EXCEDIDA", real, "coste real %.4f € > máximo reservado %.4f €" % (real, mx)); log("COSTE_SUPERIOR_A_ESTIMADO", coste=real, err="real %.4f > máximo %.4f" % (real, mx)); self._cortar("coste real %.4f € superó el máximo %.4f € de %s.%s" % (real, mx, p.nombre, metodo))
            else: self._cerrar(rid, "CONFIRMADA", real, "conciliado: estimado %.4f, real %.4f" % (est, real)); log("OK", n=(len(res) if isinstance(res, list) else 1), coste=real)
            g = self.limites()
            if (g["tope_inv_eur"] > 0 and self.gasto_inv(inv_id) >= g["tope_inv_eur"] - 1e-9) or (g["tope_mes_eur"] > 0 and g["gasto_mes_eur"] >= g["tope_mes_eur"] - 1e-9): self._cortar("límite de gasto alcanzado")
            return res
        raise ult
