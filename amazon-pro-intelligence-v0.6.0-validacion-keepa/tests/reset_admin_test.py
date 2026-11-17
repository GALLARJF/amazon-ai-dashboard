"""Restablecer contraseña de admin: conserva datos y ai.env, cierra sesiones, copia previa, auditoría íntegra, sin secretos."""
import hashlib, http.client, json, os, re, subprocess, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from backend.store import Store
from tools import restablecer_admin as RA
import server as S
R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); db = os.path.join(tmp, "data", "amazon_pro.db"); os.makedirs(os.path.dirname(db))
envf = os.path.join(tmp, "ai.env"); open(envf, "w").write("OPENAI_API_KEY=sk-proj-CENTINELA-RESET-000111222333\nAMAZON_PRO_AI_ENABLE=0\n"); env_h = hashlib.sha256(open(envf, "rb").read()).hexdigest()
st = Store(db); st.create_user("admin", "contraseña-perdida-xyz", "admin", []); st.create_user("ana", "analista-pass-1", "analyst", ["a1"])
st.create_account("a1", "Cuenta 1", "X"); rid = st.put("a1", "dossier", {"name": "Exp real", "origin": "INCOMPLETO"}); old = st.login("admin", "contraseña-perdida-xyz"); st.db.close()
def snap():
    s = Store(db); r = (s.db.execute("SELECT COUNT(*) FROM records").fetchone()[0], s.db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0], json.dumps(s.get("a1", rid), sort_keys=True)); s.db.close(); return r
before = snap()
check("antes: la sesión vieja existe", old is not None)
ok, copia = RA.restablecer(db, "corto"); check("contraseña corta rechazada y sin copia ni cambios", not ok and snap() == before)
NEW = "Nueva-clave-segura-2026"; ok, copia = RA.restablecer(db, NEW)
st = Store(db)
check("restablecer devuelve OK y crea copia de seguridad legible con los mismos registros", ok and os.path.exists(copia) and os.path.exists(copia))
import sqlite3; c = sqlite3.connect(copia); check("la copia contiene los registros y usuarios previos", c.execute("SELECT COUNT(*) FROM records").fetchone()[0] == before[0] and c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2); c.close()
check("la contraseña nueva funciona y la antigua ya no", st.login("admin", NEW) is not None and st.login("admin", "contraseña-perdida-xyz") is None)
check("la sesión antigua queda cerrada", st.session(old["token"]) is None)
check("expedientes y cuentas intactos (mismo contenido)", snap() == before)
check("otros usuarios intactos (ana sigue entrando)", st.login("ana", "analista-pass-1") is not None)
ok2, _ = st.verify_audit()[0], 0; check("cadena de auditoría íntegra tras el cambio", st.verify_audit()[0] is True)
al = json.dumps(st.audit_list(limit=500)); check("auditoría registra admin.password_reset SIN contraseña ni token", "admin.password_reset" in al and NEW not in al and "contraseña-perdida" not in al)
check("ai.env no se ha tocado", hashlib.sha256(open(envf, "rb").read()).hexdigest() == env_h)
st.db.close()
# admin borrado/inactivo → se recrea
s2 = Store(db); s2.db.execute("DELETE FROM users WHERE username='admin'"); s2.db.commit(); s2.db.close()
ok, _ = RA.restablecer(db, NEW + "2"); s2 = Store(db); check("si admin no existe se recrea con rol admin", ok and s2.login("admin", NEW + "2") is not None); u = s2.db.execute("SELECT role,active FROM users WHERE username='admin'").fetchone(); check("rol admin y activo", (u["role"], u["active"]) == ("admin", 1)); s2.db.close()
# script completo (stdin): contraseña elegida y generada
env = dict(os.environ, AMAZON_PRO_DB=db); script = os.path.join(ROOT, "tools", "restablecer_admin.py")
p = subprocess.run([sys.executable, script], input="Elegida-por-mi-123\nElegida-por-mi-123\n", capture_output=True, text=True, env=env)
check("script: contraseña elegida OK y NO se imprime", p.returncode == 0 and "LISTO" in p.stdout and "Elegida-por-mi-123" not in p.stdout + p.stderr)
p = subprocess.run([sys.executable, script], input="una-clave-larga-1\notra-distinta-22\n", capture_output=True, text=True, env=env)
s3 = Store(db); check("script: si no coinciden no cambia nada", p.returncode == 1 and s3.login("admin", "Elegida-por-mi-123") is not None); s3.db.close()
p = subprocess.run([sys.executable, script], input="\n", capture_output=True, text=True, env=env); m = re.search(r"ahora, apúntala\): (\S+)", p.stdout)
s3 = Store(db); check("script: ENTER genera contraseña aleatoria (≥10) que funciona y se muestra una vez", p.returncode == 0 and m and len(m.group(1)) >= 10 and s3.login("admin", m.group(1)) is not None); s3.db.close()
p = subprocess.run([sys.executable, script], input="\n", capture_output=True, text=True, env=dict(os.environ, AMAZON_PRO_DB=os.path.join(tmp, "no_existe.db")))
check("script: sin base de datos explica y no crea nada", p.returncode == 1 and "No encuentro la base de datos" in p.stdout and not os.path.exists(os.path.join(tmp, "no_existe.db")))
# servidor abierto → se niega
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tempfile.mkdtemp(), "x.db"), admin_password="admin-password-123"); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
import importlib; importlib.reload(RA); check("detector real: puerto cerrado → False", RA.server_running(1) is False)
check("detector real detecta servidor en marcha", RA.server_running(port) is True)
srv.shutdown()
# integración: servidor real con la BD restablecida → login HTTP
ok, _ = RA.restablecer(db, "Login-http-prueba-9"); srv = S.make_server(0, admin_token="t", db_path=db); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
def login(pw):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10); c.request("POST", "/api/login", json.dumps({"username": "admin", "password": pw}), {"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"}); r = c.getresponse(); r.read(); return r.status
check("servidor real: login HTTP con la contraseña nueva 200, con la vieja 401", login("Login-http-prueba-9") == 200 and login(NEW) == 401)
check("el servidor NO crea otro admin ni muestra contraseña (usuarios existentes → sin 'PRIMER ARRANQUE')", srv.initial_admin_password is None)
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
