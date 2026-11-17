"""V1.0 (V1-08) — Copia de seguridad, restauración y apertura segura de la BD SQLite.
Copia coherente con la API de backup de SQLite + hash SHA-256 en fichero hermano; la restauración verifica hash, integridad y cadena de auditoría ANTES de tocar nada,
y deja una copia del estado previo. Una BD corrupta falla de forma controlada: nunca se borra ni se sobrescribe."""
import hashlib, os, shutil, sqlite3, time

class RespaldoError(Exception): pass

def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def verificar(path):
    """Devuelve {ok, integridad, auditoria, filas_auditoria, motivo}. No modifica el fichero (abre en solo lectura)."""
    if not os.path.isfile(path): return {"ok": False, "motivo": "no existe"}
    try:
        c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
        ic = c.execute("PRAGMA integrity_check").fetchone()[0]
        if ic != "ok": c.close(); return {"ok": False, "integridad": ic, "motivo": "integridad SQLite fallida"}
        import json, hashlib as H
        from .store import canon
        rows = c.execute("SELECT seq,ts,account_id,actor,action,detail,prev_hash,hash FROM audit ORDER BY seq").fetchall(); c.close(); prev = "0" * 64
        for r in rows:
            body = canon({"ts": r[1], "account": r[2], "actor": r[3], "action": r[4], "detail": json.loads(r[5])})
            if r[6] != prev or H.sha256((prev + body).encode()).hexdigest() != r[7]: return {"ok": False, "integridad": ic, "motivo": "cadena de auditoría rota en seq %s" % r[0]}
            prev = r[7]
        return {"ok": True, "integridad": ic, "auditoria": "íntegra", "filas_auditoria": len(rows)}
    except sqlite3.DatabaseError as e:
        return {"ok": False, "motivo": "BD ilegible o corrupta: %s" % type(e).__name__}

def respaldar(db_path, dest_dir):
    os.makedirs(dest_dir, exist_ok=True); v = verificar(db_path)
    if not v["ok"]: raise RespaldoError("no se respalda una BD no íntegra: " + v["motivo"])
    out = os.path.join(dest_dir, "respaldo_%s.db" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    src = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True); dst = sqlite3.connect(out); src.backup(dst); dst.close(); src.close()
    h = _sha(out); open(out + ".sha256", "w").write("%s  %s\n" % (h, os.path.basename(out)))
    return {"fichero": out, "sha256": h, "bytes": os.path.getsize(out), "verificacion": verificar(out)}

def restaurar(respaldo, db_path):
    sidecar = respaldo + ".sha256"
    if not os.path.isfile(sidecar): raise RespaldoError("falta el hash .sha256 del respaldo")
    if open(sidecar).read().split()[0] != _sha(respaldo): raise RespaldoError("el hash no coincide: respaldo alterado o dañado")
    v = verificar(respaldo)
    if not v["ok"]: raise RespaldoError("respaldo no íntegro: " + v["motivo"])
    previo = None
    if os.path.exists(db_path):
        previo = "%s.previo-%s" % (db_path, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())); shutil.copy2(db_path, previo)
    tmp = db_path + ".restaurando"; shutil.copy2(respaldo, tmp); os.replace(tmp, db_path)
    return {"restaurado": db_path, "copia_previa": previo, "verificacion": verificar(db_path)}

def abrir_seguro(db_path):
    """Comprueba la BD antes de abrirla. Si está corrupta lanza RespaldoError y NO la modifica."""
    if os.path.exists(db_path):
        v = verificar(db_path)
        if not v["ok"]: raise RespaldoError("la BD está dañada (%s); no se ha modificado. Restaura un respaldo con restaurar()." % v["motivo"])
    return True
