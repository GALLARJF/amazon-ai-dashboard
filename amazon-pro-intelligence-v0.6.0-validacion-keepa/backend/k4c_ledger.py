"""K4 · Consejero · F1 — LIBRO DE EVIDENCIAS persistente: fuente (procedencia, fecha, tipo, calidad, vigencia), extracto literal corto, afirmaciones ligadas a extractos, hipótesis y consultas.
Integridad: un extracto solo entra si aparece literalmente en el texto de la fuente (hash del texto guardado, no copia completa). Entorno SINTETICO nunca se mezcla con REAL."""
import hashlib, json, re, uuid
from .k4_store import now

TIPOS_FUENTE = ("PRIMARIA", "SECUNDARIA", "TERCIARIA")   # PRIMARIA: norma, ficha oficial, estudio original/revisión publicada, dato propio · SECUNDARIA: prensa, consultoras, farmacias, blogs
CALIDAD = ("ALTA", "MEDIA", "BAJA", "MUY_BAJA"); RANGO_CAL = {"ALTA": 3, "MEDIA": 2, "BAJA": 1, "MUY_BAJA": 0}
TIPOS_DATO = ("ACTUAL", "HISTORICO", "ATEMPORAL")
TIPOS_AFIRMACION = ("HECHO", "HIPOTESIS", "INFERENCIA", "FALTANTE", "DECISION")
SCHEMA = """
CREATE TABLE IF NOT EXISTS k4c_fuente(id TEXT PRIMARY KEY, url TEXT, titulo TEXT, tipo_fuente TEXT, organismo TEXT, fecha_publicacion TEXT, fecha_acceso TEXT, hash TEXT, calidad TEXT, tipo_dato TEXT, vigente_hasta TEXT, entorno TEXT, proveedor TEXT, inv_id TEXT, objeto TEXT);
CREATE TABLE IF NOT EXISTS k4c_extracto(id TEXT PRIMARY KEY, fuente_id TEXT, texto TEXT, localizador TEXT, hash TEXT, hipotesis TEXT, efecto INTEGER);
CREATE TABLE IF NOT EXISTS k4c_inv(id TEXT PRIMARY KEY, pregunta TEXT, producto TEXT, estado TEXT, entorno TEXT, modo TEXT, creado TEXT, plan TEXT, informe TEXT, veredicto TEXT, actor TEXT);
CREATE TABLE IF NOT EXISTS k4c_afirmacion(id TEXT PRIMARY KEY, inv_id TEXT, tipo TEXT, texto TEXT, extractos TEXT, relacion TEXT, confianza TEXT, datos TEXT, estado TEXT);
CREATE TABLE IF NOT EXISTS k4c_hipotesis(id TEXT, inv_id TEXT, texto TEXT, origen TEXT, estado TEXT, puntuacion REAL, datos TEXT, PRIMARY KEY(id, inv_id));
CREATE TABLE IF NOT EXISTS k4c_prediccion(id INTEGER PRIMARY KEY AUTOINCREMENT, inv_id TEXT, indicador TEXT, esperado TEXT, ventana_dias INTEGER, estado TEXT, observado TEXT, creado TEXT);
"""
def sha(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()
def norm(t): return re.sub(r"\s+", " ", str(t)).strip().lower()


class Libro:
    def __init__(self, k4):
        self.k = k4; k4.s.db.executescript(SCHEMA); k4.s.db.commit(); self._txt = {}

    def add_fuente(self, doc, inv_id, proveedor, entorno, fecha_acceso=None):
        if doc.get("tipo_fuente") not in TIPOS_FUENTE or doc.get("calidad") not in CALIDAD or doc.get("tipo_dato") not in TIPOS_DATO: raise ValueError("fuente: tipo_fuente/calidad/tipo_dato inválidos")
        if entorno not in ("SINTETICO", "REAL"): raise ValueError("entorno inválido")
        if entorno == "SINTETICO" and not str(doc["url"]).startswith("sintetico://"): raise ValueError("una fuente sintética debe usar sintetico://")
        if entorno == "REAL" and str(doc["url"]).startswith("sintetico://"): raise ValueError("no se mezcla lo sintético con lo real")
        fid = "F-" + sha(inv_id + doc["url"])[:10]
        self._txt[fid] = doc["texto"]
        if not self.k.q("SELECT 1 FROM k4c_fuente WHERE id=?", (fid,)):
            self.k.x("INSERT INTO k4c_fuente VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (fid, doc["url"], doc.get("titulo", "")[:200], doc["tipo_fuente"], doc.get("organismo", ""), doc.get("fecha_publicacion"), fecha_acceso or now()[:10], sha(doc["texto"]), doc["calidad"], doc["tipo_dato"], doc.get("vigente_hasta"), entorno, proveedor, inv_id, doc.get("objeto") or "INGREDIENTE"))
        return fid

    def add_extracto(self, fuente_id, texto, localizador="", hipotesis=None, efecto=0, texto_fuente=None):
        src = texto_fuente if texto_fuente is not None else self._txt.get(fuente_id)
        if src is None: raise LookupError("fuente sin texto en memoria")
        if len(texto) > 400: raise ValueError("extracto demasiado largo (máx. 400)")
        if norm(texto) not in norm(src): raise ValueError("el extracto no aparece literalmente en la fuente")
        eid = "X-" + sha(fuente_id + texto)[:10]
        if not self.k.q("SELECT 1 FROM k4c_extracto WHERE id=?", (eid,)): self.k.x("INSERT INTO k4c_extracto VALUES(?,?,?,?,?,?,?)", (eid, fuente_id, texto, localizador, sha(texto), hipotesis, int(efecto)))
        return eid

    def fuente(self, fid): r = self.k.q("SELECT * FROM k4c_fuente WHERE id=?", (fid,)); return r[0] if r else None
    def extracto(self, eid):
        r = self.k.q("SELECT * FROM k4c_extracto WHERE id=?", (eid,)); return r[0] if r else None
    def extractos_de(self, inv_id): return self.k.q("SELECT x.*, f.calidad, f.tipo_fuente, f.tipo_dato, f.fecha_publicacion, f.url, f.titulo, f.objeto FROM k4c_extracto x JOIN k4c_fuente f ON f.id=x.fuente_id WHERE f.inv_id=?", (inv_id,))
    def fuentes_de(self, inv_id): return self.k.q("SELECT * FROM k4c_fuente WHERE inv_id=?", (inv_id,))

    def nueva_inv(self, pregunta, producto, entorno, modo, actor):
        iid = "INV-" + uuid.uuid4().hex[:8]
        self.k.x("INSERT INTO k4c_inv VALUES(?,?,?,?,?,?,?,?,?,?,?)", (iid, pregunta[:500], producto, "EN_CURSO", entorno, modo, now(), None, None, None, actor)); return iid

    def guardar_inv(self, iid, estado, plan=None, informe=None, veredicto=None):
        self.k.x("UPDATE k4c_inv SET estado=?, plan=COALESCE(?,plan), informe=COALESCE(?,informe), veredicto=COALESCE(?,veredicto) WHERE id=?", (estado, json.dumps(plan, ensure_ascii=False, default=str) if plan else None, json.dumps(informe, ensure_ascii=False, default=str) if informe else None, json.dumps(veredicto, ensure_ascii=False, default=str) if veredicto else None, iid))

    def inv(self, iid):
        r = self.k.q("SELECT * FROM k4c_inv WHERE id=?", (iid,))
        if not r: raise LookupError("investigación inexistente")
        d = dict(r[0])
        for k in ("plan", "informe", "veredicto"): d[k] = json.loads(d[k]) if d[k] else None
        return d

    def guardar_afirmaciones(self, iid, afs, estados=None):
        for a in afs:
            self.k.x("INSERT OR REPLACE INTO k4c_afirmacion VALUES(?,?,?,?,?,?,?,?,?)", (iid + ":" + a["id"], iid, a["tipo"], a["texto"], json.dumps(a.get("citas") or []), a.get("relacion"), a.get("confianza"), json.dumps(a, ensure_ascii=False, default=str), (estados or {}).get(a["id"], "SIN_VERIFICAR")))

    def guardar_hipotesis(self, iid, hs):
        for h in hs: self.k.x("INSERT OR REPLACE INTO k4c_hipotesis VALUES(?,?,?,?,?,?,?)", (h["id"], iid, h["texto"], h["origen"], h.get("estado"), h.get("puntuacion"), json.dumps(h, ensure_ascii=False, default=str)))

    def libro(self, iid):
        return {"fuentes": self.fuentes_de(iid), "extractos": self.extractos_de(iid), "consultas": self.k.q("SELECT ts,rol,proveedor,metodo,consulta,n_resultados,coste_eur,estado,error FROM k4c_consulta WHERE inv_id=? ORDER BY id", (iid,)),
                "afirmaciones": [dict(json.loads(r["datos"]), estado_verificacion=r["estado"]) for r in self.k.q("SELECT * FROM k4c_afirmacion WHERE inv_id=?", (iid,))], "hipotesis": [json.loads(r["datos"]) for r in self.k.q("SELECT datos FROM k4c_hipotesis WHERE inv_id=?", (iid,))]}
