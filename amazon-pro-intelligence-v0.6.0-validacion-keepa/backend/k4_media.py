"""K4 · registro de medios con procedencia y derechos POR OPERACIÓN. Vinculación EXACTA producto+variante+ASIN(+país+volumen): jamás se devuelve una imagen aproximada.
Sin fuente autorizada → marcador «IMAGEN PENDIENTE DE VERIFICAR» indicando QUÉ autorización falta. Prohibido: scraping, imágenes generadas por IA, reutilización sin permiso."""
import base64, hashlib, json, os, re, uuid
from .k4_store import now

OPS = ("visualizar", "almacenar", "transformar", "exportar", "redistribuir")
ORIGENES = {"FOTO_PROPIA_AHT": "Foto propia de AHT", "FOTO_PROPIA_DE_PRODUCTO_AJENO": "Foto tomada por AHT de unidad comprada", "FABRICANTE_AUTORIZADO": "Fabricante con permiso escrito",
            "CATALOGO_SPAPI_PROPIO": "Catálogo SP-API de producto propio", "AMAZON_CREATORS_API": "Amazon Creators/PA-API (enlace remoto)", "KEEPA_ENLACE": "Keepa imagesCSV (enlace; términos no verificados)"}
PROHIBIDOS = {"SCRAPING", "IA_GENERADA", "CAPTURA_NO_AUTORIZADA"}
MIMES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_BYTES = 1_000_000
ASIN = re.compile(r"^[A-Z0-9]{10}$")
FALTA_POR_ORIGEN = {"KEEPA_ENLACE": "Permiso escrito de Keepa/titular para mostrar, almacenar y exportar la imagen", "AMAZON_CREATORS_API": "Cuenta Associates + aprobación de CSP (img-src) y no almacenar/exportar",
                    "FABRICANTE_AUTORIZADO": "Permiso escrito del fabricante", "FOTO_PROPIA_DE_PRODUCTO_AJENO": "Confirmación legal de uso/exportación", "CATALOGO_SPAPI_PROPIO": "Autorización SP-API de la cuenta AHT"}


class Media:
    def __init__(self, k4, base_dir):
        self.k = k4; self.dir = os.path.join(base_dir, "media") if base_dir else None

    @staticmethod
    def _key(d):
        for k in ("product_id", "variante"):
            if not d.get(k): raise ValueError("falta " + k)
        a = d.get("asin")
        if a and not ASIN.match(a): raise ValueError("ASIN inválido")

    def add(self, d, actor, contenido_b64=None):
        o = d.get("origen")
        if o in PROHIBIDOS: raise ValueError("origen prohibido (" + o + "): no se admite scraping, IA ni capturas no autorizadas")
        if o not in ORIGENES: raise ValueError("origen desconocido")
        self._key(d)
        if not d.get("fuente") or not d.get("fecha_captura"): raise ValueError("faltan fuente y fecha_captura")
        mime = sha = path = None; nb = None
        if contenido_b64:
            raw = base64.b64decode(contenido_b64, validate=True)
            if len(raw) > MAX_BYTES: raise ValueError("imagen demasiado grande")
            mime = d.get("mime")
            if mime not in MIMES: raise ValueError("mime no permitido")
            magic = {"image/png": b"\x89PNG", "image/jpeg": b"\xff\xd8", "image/webp": b"RIFF"}[mime]
            if not raw.startswith(magic): raise ValueError("el contenido no coincide con el tipo")
            sha = hashlib.sha256(raw).hexdigest(); nb = len(raw)
            if not self.dir: raise ValueError("almacenamiento local no disponible")
            os.makedirs(self.dir, exist_ok=True); path = os.path.join(self.dir, sha + "." + MIMES[mime])
            with open(path, "wb") as f: f.write(raw)
        elif not d.get("url_origen"): raise ValueError("aporte contenido o url_origen")
        der = {op: False for op in OPS}; der["fuente_permiso"] = ""
        mid = "MED-" + uuid.uuid4().hex[:10]
        self.k.x("INSERT INTO k4_media VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (mid, d["product_id"], d["variante"], d.get("asin"), d.get("pais"), d.get("volumen_ml"), o, d["fuente"], d.get("url_origen"), d["fecha_captura"], d.get("autor"), mime, sha, nb, path,
                  "PENDIENTE", json.dumps(der), d.get("evidencia_ref"), d.get("caduca"), actor, now(), None, None, None))
        self.k.audit(actor, "k4.media.alta", {"id": mid, "origen": o, "asin": d.get("asin")})
        return mid

    def verify(self, mid, estado, derechos, actor, permiso=""):
        r = self.k.q("SELECT * FROM k4_media WHERE id=?", (mid,))
        if not r: raise LookupError("medio inexistente")
        if estado not in ("VERIFICADA", "RECHAZADA"): raise ValueError("estado inválido")
        der = {op: bool((derechos or {}).get(op)) for op in OPS}
        if estado == "VERIFICADA":
            if not permiso or len(permiso) < 8: raise ValueError("verificar exige referencia al permiso/evidencia")
            if not any(der.values()): raise ValueError("verificar exige al menos un derecho concedido")
            if der["almacenar"] and not r[0]["path"]: raise ValueError("no hay copia local que almacenar")
        else:
            der = {op: False for op in OPS}
        der["fuente_permiso"] = permiso[:300]
        self.k.x("UPDATE k4_media SET estado=?, derechos=?, verificado_por=?, verificado_en=? WHERE id=?", (estado, json.dumps(der), actor, now(), mid))
        self.k.audit(actor, "k4.media.verificacion", {"id": mid, "estado": estado, "derechos": der})

    def pending(self, product_id, variante, asin, why):
        return {"estado": "PENDIENTE", "marcador": "IMAGEN PENDIENTE DE VERIFICAR", "falta": why, "product_id": product_id, "variante": variante, "asin": asin}

    def resolve(self, product_id, variante, asin, op="visualizar", hoy=None):
        """Coincidencia EXACTA. Devuelve medio si VERIFICADA y con derecho para `op` y vigente; si no, marcador con la autorización que falta."""
        rows = self.k.q("SELECT * FROM k4_media WHERE product_id=? AND variante=? AND COALESCE(asin,'')=COALESCE(?,'') ORDER BY creado DESC", (product_id, variante, asin))
        if not rows: return self.pending(product_id, variante, asin, "No hay ninguna imagen registrada para esta variante/ASIN: aportar foto propia o permiso de fuente")
        hoy = hoy or now()[:10]; why = None
        for r in rows:
            der = json.loads(r["derechos"])
            if r["estado"] != "VERIFICADA": why = why or "Imagen registrada sin verificar: " + FALTA_POR_ORIGEN.get(r["origen"], "verificación de derechos"); continue
            if r["caduca"] and r["caduca"] < hoy: why = why or "Permiso caducado el " + r["caduca"]; continue
            if not der.get(op): why = why or f"Verificada pero SIN derecho para «{op}»: falta autorización de {op}"; continue
            return {"estado": "VERIFICADA", "id": r["id"], "origen": r["origen"], "fuente": r["fuente"], "fecha_captura": r["fecha_captura"], "derechos": der, "tiene_copia": bool(r["path"]),
                    "url": ("/api/k4/media/" + r["id"] + "/file") if r["path"] else (r["url_origen"] if op == "visualizar" and r["origen"] == "AMAZON_CREATORS_API" else None), "asin": asin, "variante": variante}
        return self.pending(product_id, variante, asin, why or "Sin derechos")

    def file(self, mid, op="visualizar"):
        r = self.k.q("SELECT * FROM k4_media WHERE id=?", (mid,))
        if not r or r[0]["estado"] != "VERIFICADA" or not r[0]["path"]: raise LookupError("no disponible")
        if not json.loads(r[0]["derechos"]).get(op): raise PermissionError("sin derecho para " + op)
        with open(r[0]["path"], "rb") as f: return r[0]["mime"], f.read()

    def registry(self, product_id=None):
        rows = self.k.q("SELECT id,product_id,variante,asin,pais,volumen_ml,origen,fuente,fecha_captura,estado,derechos,caduca,verificado_por,verificado_en,(path IS NOT NULL) AS copia FROM k4_media WHERE (?1 IS NULL OR product_id=?1) ORDER BY creado DESC", (product_id,))
        for r in rows: r["derechos"] = json.loads(r["derechos"])
        return rows
