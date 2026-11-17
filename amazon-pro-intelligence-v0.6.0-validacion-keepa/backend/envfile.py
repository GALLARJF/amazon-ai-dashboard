"""Carga SEGURA de la configuración de IA desde un archivo LOCAL fuera del proyecto (V0.3.3).
Ubicación por defecto (Windows): C:\\Users\\<usuario>\\AmazonPro\\ai.env  ·  (Linux/Mac): ~/AmazonPro/ai.env  ·  se puede cambiar con AMAZON_PRO_ENV_FILE.
Reglas: solo se aceptan nombres AMAZON_PRO_AI_* y OPENAI_API_KEY; nunca se pisan variables ya definidas en el entorno; jamás se imprime ni se registra un valor."""
import os

ALLOWED_PREFIXES = ("AMAZON_PRO_AI_", "AMAZON_PRO_KEEPA_")
ALLOWED_PREFIX = "AMAZON_PRO_AI_"  # compatibilidad
ALLOWED_EXACT = {"OPENAI_API_KEY", "KEEPA_API_KEY"}


def default_path():
    return os.environ.get("AMAZON_PRO_ENV_FILE") or os.path.join(os.path.expanduser("~"), "AmazonPro", "ai.env")


def keepa_path():
    """Archivo local de Keepa (fuera del proyecto): C:\\Users\\<usuario>\\AmazonPro\\keepa.env  (cambiable con AMAZON_PRO_KEEPA_FILE)."""
    return os.environ.get("AMAZON_PRO_KEEPA_FILE") or os.path.join(os.path.expanduser("~"), "AmazonPro", "keepa.env")


def parse(text):
    """Devuelve {NOMBRE: valor}. Tolera BOM de Notepad, CRLF, comillas, comentarios (#) y espacios. Ignora el marcador PEGA_AQUI…"""
    out = {}
    for raw in text.lstrip("\ufeff").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1); k = k.strip().upper(); v = v.strip()
        if v[:1] in ("'", '"') and v.count(v[0]) >= 2:
            v = v[1:v.index(v[0], 1)]
        else:
            for sep in (" #", "\t#"):
                if sep in v: v = v.split(sep, 1)[0]
            v = v.strip()
        if not (k.startswith(ALLOWED_PREFIXES) or k in ALLOWED_EXACT) or not v or v.upper().startswith("PEGA"):
            continue
        out[k] = v
    return out


def load(path=None, environ=None):
    """Carga el archivo en el entorno del proceso. Devuelve {path, found, names_loaded, names_skipped_already_set} (SOLO nombres, nunca valores)."""
    env = os.environ if environ is None else environ
    p = path or default_path(); info = {"path": p, "found": False, "names_loaded": [], "names_already_set": []}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            vals = parse(fh.read())
    except OSError:
        return info
    info["found"] = True
    for k, v in vals.items():
        if env.get(k):
            info["names_already_set"].append(k); continue
        env[k] = v; info["names_loaded"].append(k)
    return info


def key_looks_valid(key):
    """Comprobación de forma, sin revelar nada: las claves de OpenAI empiezan por «sk-», no llevan espacios y son largas."""
    return bool(key) and key.startswith("sk-") and len(key) >= 20 and not any(c.isspace() or c in "\"'" for c in key)
