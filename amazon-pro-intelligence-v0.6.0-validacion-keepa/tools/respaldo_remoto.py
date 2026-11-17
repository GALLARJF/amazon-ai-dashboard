#!/usr/bin/env python3
"""Respaldo y restauración REMOTOS de Amazon Pro Intelligence (modo cloud), pensado para ejecutarse en el PC del propietario: guarda el respaldo FUERA del disco del servidor.
  python tools/respaldo_remoto.py descargar https://tu-servicio.onrender.com --usuario admin --carpeta respaldos
  python tools/respaldo_remoto.py subir     https://tu-servicio.onrender.com --usuario admin --archivo respaldos/respaldo_XXXX.db
La contraseña se pide en el terminal (getpass) o se lee de AMAZON_PRO_PASSWORD; nunca se pasa por argumentos ni se imprime. Verifica el certificado TLS (salvo --ca para pruebas)."""
import argparse, base64, getpass, hashlib, http.cookiejar, json, os, ssl, sys, time, urllib.error, urllib.request, zlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend import respaldo100 as RB

class Sesion:
    def __init__(self, base, usuario, password, ca=None):
        if not base.startswith("https://"): raise SystemExit("la URL debe ser https://")
        self.base = base.rstrip("/"); ctx = ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), urllib.request.HTTPSHandler(context=ctx))
        c, d, _ = self.pedir("POST", "/api/login", {"username": usuario, "password": password})
        if c != 200: raise SystemExit("inicio de sesión rechazado (%s)" % c)
        self.csrf = json.loads(d)["csrf"]
    def pedir(self, m, path, body=None):
        rq = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None, method=m, headers={"Content-Type": "application/json", "X-CSRF-Token": getattr(self, "csrf", "")})
        try:
            with self.op.open(rq, timeout=60) as r: return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e: return e.code, e.read(), dict(e.headers)

def descargar(s, carpeta):
    c, d, h = s.pedir("GET", "/api/v07/respaldo")
    if c != 200: raise SystemExit("el servidor rechazó la descarga (%s): ¿es administrador?" % c)
    sha = h.get("X-Backup-SHA256", "")
    if hashlib.sha256(d).hexdigest() != sha: raise SystemExit("hash distinto: descarga dañada, no se guarda")
    os.makedirs(carpeta, exist_ok=True); f = os.path.join(carpeta, "respaldo_%s.db" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())); open(f, "wb").write(d); open(f + ".sha256", "w").write("%s  %s\n" % (sha, os.path.basename(f)))
    v = RB.verificar(f)
    if not v["ok"]: raise SystemExit("el respaldo descargado no es íntegro: " + v["motivo"])
    return {"fichero": f, "sha256": sha, "filas_auditoria": v["filas_auditoria"]}

def subir(s, archivo):
    raw = open(archivo, "rb").read(); sha = hashlib.sha256(raw).hexdigest()
    c, d, _ = s.pedir("POST", "/api/v07/respaldo/subir", {"content_b64_zlib": base64.b64encode(zlib.compress(raw)).decode(), "sha256": sha})
    if c != 200: raise SystemExit("el servidor rechazó el respaldo (%s): %s" % (c, d.decode("utf-8", "replace")[:200]))
    return json.loads(d)

if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("accion", choices=["descargar", "subir"]); a.add_argument("url"); a.add_argument("--usuario", default="admin"); a.add_argument("--carpeta", default="respaldos"); a.add_argument("--archivo"); a.add_argument("--ca")
    x = a.parse_args(); pw = os.environ.get("AMAZON_PRO_PASSWORD") or getpass.getpass("Contraseña de %s: " % x.usuario); s = Sesion(x.url, x.usuario, pw, x.ca)
    print(json.dumps(descargar(s, x.carpeta) if x.accion == "descargar" else subir(s, x.archivo), indent=1, ensure_ascii=False))
