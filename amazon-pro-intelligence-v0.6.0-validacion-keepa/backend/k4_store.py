"""K4 · persistencia (SQLite, migraciones ADITIVAS: solo CREATE TABLE IF NOT EXISTS; no toca tablas existentes)."""
import json, time

SCHEMA = """
CREATE TABLE IF NOT EXISTS k4_media(id TEXT PRIMARY KEY, product_id TEXT NOT NULL, variante TEXT NOT NULL, asin TEXT, pais TEXT, volumen_ml REAL, origen TEXT NOT NULL, fuente TEXT NOT NULL,
  url_origen TEXT, fecha_captura TEXT NOT NULL, autor TEXT, mime TEXT, sha256 TEXT, bytes INTEGER, path TEXT, estado TEXT NOT NULL, derechos TEXT NOT NULL, evidencia_ref TEXT, caduca TEXT,
  subido_por TEXT, creado TEXT NOT NULL, verificado_por TEXT, verificado_en TEXT, nota TEXT);
CREATE INDEX IF NOT EXISTS ix_k4m ON k4_media(product_id, asin);
CREATE TABLE IF NOT EXISTS k4_import(id TEXT PRIMARY KEY, tipo TEXT NOT NULL, entorno TEXT NOT NULL, origen TEXT NOT NULL, nombre TEXT, sha256 TEXT, filas INTEGER, rechazadas TEXT, metodologia TEXT, subido_por TEXT, creado TEXT);
CREATE TABLE IF NOT EXISTS k4_sales(id INTEGER PRIMARY KEY AUTOINCREMENT, import_id TEXT, producto TEXT NOT NULL, pais TEXT NOT NULL, fecha TEXT NOT NULL, canal TEXT, unidades REAL, ventas_netas REAL,
  moneda TEXT, sesiones REAL, pedidos REAL, devoluciones_uds REAL, precio_medio REAL, entorno TEXT NOT NULL, origen TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_k4s ON k4_sales(producto, pais, fecha, entorno);
CREATE TABLE IF NOT EXISTS k4_ads(id INTEGER PRIMARY KEY AUTOINCREMENT, import_id TEXT, producto TEXT NOT NULL, pais TEXT NOT NULL, fecha TEXT NOT NULL, gasto REAL, ventas_ads REAL, clics REAL, impresiones REAL,
  moneda TEXT, entorno TEXT NOT NULL, origen TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_k4a ON k4_ads(producto, pais, fecha, entorno);
CREATE TABLE IF NOT EXISTS k4_inventory(id INTEGER PRIMARY KEY AUTOINCREMENT, import_id TEXT, producto TEXT NOT NULL, pais TEXT NOT NULL, fecha TEXT NOT NULL, stock REAL, entorno TEXT NOT NULL, origen TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS k4_costs(id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT NOT NULL, concepto TEXT NOT NULL, valor REAL, unidad TEXT NOT NULL, moneda TEXT NOT NULL, fuente TEXT NOT NULL,
  fecha TEXT NOT NULL, estado_validacion TEXT NOT NULL, incluye TEXT NOT NULL DEFAULT '[]', es_total INTEGER NOT NULL DEFAULT 0, pais TEXT, nota TEXT, creado_por TEXT, creado TEXT NOT NULL, vigente INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS k4_dossier(id TEXT PRIMARY KEY, tipo TEXT NOT NULL, producto TEXT, titulo TEXT NOT NULL, datos TEXT NOT NULL, estado TEXT NOT NULL, creado_por TEXT, creado TEXT, actualizado TEXT);
CREATE TABLE IF NOT EXISTS k4_followup(id INTEGER PRIMARY KEY AUTOINCREMENT, decision_id INTEGER, ledger_id INTEGER, producto TEXT, pais TEXT, accion TEXT NOT NULL, ejecutor TEXT, ejecutada_en TEXT,
  ventana_dias INTEGER, metrica TEXT, base TEXT, post TEXT, resultado TEXT, estado TEXT NOT NULL, creado TEXT NOT NULL, entorno TEXT NOT NULL DEFAULT 'PRODUCCION');
"""


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class K4Store:
    def __init__(self, store):
        self.s = store
        with store.lock:
            store.db.executescript(SCHEMA); store.db.commit()

    def x(self, sql, args=()):
        with self.s.lock:
            cur = self.s.db.execute(sql, args); self.s.db.commit(); return cur

    def q(self, sql, args=()):
        with self.s.lock:
            return [dict(r) for r in self.s.db.execute(sql, args).fetchall()]

    def audit(self, actor, action, detail):
        self.s.audit(None, actor, action, detail)

    @staticmethod
    def j(o):
        return json.dumps(o, ensure_ascii=False, default=str)
