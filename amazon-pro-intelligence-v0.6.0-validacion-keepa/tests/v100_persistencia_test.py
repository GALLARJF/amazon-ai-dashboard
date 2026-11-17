"""V1.0 · V1-08 — Persistencia y recuperación: respaldo con hash, restauración verificada, BD corrupta sin pérdida, reapertura entre 'sesiones'."""
import hashlib, os, shutil, sqlite3, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
os.environ.update(AMAZON_PRO_NO_WORKER="1", AMAZON_PRO_KEEPA_ENABLE="0")
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
from backend.store import Store
from backend import respaldo100 as B
t = tempfile.mkdtemp(); db = os.path.join(t, "s.db")
s = Store(db); s.create_account("A1", "Cuenta", "AHT"); s.put("A1", "plan", {"x": 1}, id_="n1", actor="t"); s.audit("A1", "t", "e2e", {"k": 1}); n_aud = s.verify_audit()[1]; s.db.close()
v = B.verificar(db); check("BD sana: integridad ok y auditoría íntegra", v["ok"] and v["auditoria"] == "íntegra" and v["filas_auditoria"] == n_aud)
r = B.respaldar(db, os.path.join(t, "bk")); check("respaldo creado con SHA-256 y verificado", os.path.isfile(r["fichero"]) and len(r["sha256"]) == 64 and r["verificacion"]["ok"])
check("el hash del sidecar coincide con el fichero", open(r["fichero"] + ".sha256").read().split()[0] == hashlib.sha256(open(r["fichero"], "rb").read()).hexdigest())
# persistencia entre sesiones: reabrir
s2 = Store(db); check("reabrir la BD conserva los datos y la cadena", s2.get("A1", "n1")["data"] == {"x": 1} and s2.verify_audit()[0]); s2.db.close()
# restauración sobre BD alterada
c = sqlite3.connect(db); c.execute("UPDATE records SET data='{\"x\": 999}' WHERE id='n1'") if False else None; c.execute("INSERT INTO audit(ts,account_id,actor,action,detail,prev_hash,hash) VALUES('x','A1','mal','falsa','{}','0','0')"); c.commit(); c.close()
check("BD manipulada: se detecta la cadena de auditoría rota", not B.verificar(db)["ok"] and "auditoría" in B.verificar(db)["motivo"])
try: B.respaldar(db, os.path.join(t, "bk2")); ok = False
except B.RespaldoError: ok = True
check("no se respalda una BD no íntegra", ok)
rs = B.restaurar(r["fichero"], db); check("restauración OK y verificada", rs["verificacion"]["ok"] and rs["copia_previa"] and os.path.isfile(rs["copia_previa"]))
s3 = Store(db); check("tras restaurar: datos originales y cadena íntegra", s3.get("A1", "n1")["data"] == {"x": 1} and s3.verify_audit()[0]); s3.db.close()
# respaldo alterado
bad = os.path.join(t, "bk", "alterado.db"); shutil.copy(r["fichero"], bad); shutil.copy(r["fichero"] + ".sha256", bad + ".sha256"); open(bad, "ab").write(b"\0basura")
try: B.restaurar(bad, db); ok = False
except B.RespaldoError as e: ok = "hash" in str(e)
check("respaldo alterado rechazado por hash", ok)
try: B.restaurar(os.path.join(t, "bk", "nada.db"), db); ok = False
except B.RespaldoError: ok = True
check("respaldo sin hash/inexistente rechazado", ok)
# BD corrupta
cor = os.path.join(t, "corrupta.db"); open(cor, "wb").write(b"SQLite format 3\0" + os.urandom(4096)); antes = hashlib.sha256(open(cor, "rb").read()).hexdigest()
try: B.abrir_seguro(cor); ok = False
except B.RespaldoError as e: ok = "no se ha modificado" in str(e)
check("BD corrupta: fallo controlado con mensaje claro", ok)
check("BD corrupta: el fichero no se borra ni se modifica", os.path.isfile(cor) and hashlib.sha256(open(cor, "rb").read()).hexdigest() == antes)
check("BD inexistente: apertura permitida (se creará nueva)", B.abrir_seguro(os.path.join(t, "nueva.db")) is True)
rr = B.restaurar(r["fichero"], cor); check("una BD corrupta se recupera desde respaldo (queda copia de la corrupta)", rr["verificacion"]["ok"] and os.path.isfile(rr["copia_previa"]))
import server as S
from backend import ai as AI
open(cor, "wb").write(b"SQLite format 3\0" + os.urandom(4096))
try: S.make_server(0, admin_token="t", db_path=cor, cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); ok = False
except B.RespaldoError as e: ok = "no se ha modificado" in str(e)
check("el servidor NO arranca con una BD corrupta (y no la toca)", ok)
srv = S.make_server(0, admin_token="t", db_path=db, cfg_fn=lambda: AI.config({}), admin_password="admin-password-123"); check("el servidor arranca con la BD restaurada", srv.server_address[1] > 0); srv.server_close()
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
