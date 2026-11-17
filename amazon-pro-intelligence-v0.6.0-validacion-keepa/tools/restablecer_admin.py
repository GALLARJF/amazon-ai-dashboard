"""Restablece SOLO la contraseña del usuario «admin». No toca expedientes, cuentas, configuración ni ai.env.
- Hace antes una copia de seguridad de la base de datos (data/copias/).
- Cierra todas las sesiones abiertas (obliga a iniciar sesión de nuevo).
- Deja constancia en la auditoría (sin contraseña, sin token).
- No desactiva la autenticación. No lee ni imprime la clave de OpenAI."""
import getpass, os, secrets, socket, sqlite3, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)


def db_path():
    return os.environ.get("AMAZON_PRO_DB") or os.path.join(ROOT, "data", "amazon_pro.db")


def server_running(port=8765):
    s = socket.socket(); s.settimeout(0.7)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def backup(path):
    d = os.path.join(os.path.dirname(path), "copias"); os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, "amazon_pro_ANTES_de_restablecer_" + time.strftime("%Y%m%d_%H%M%S") + ".db")
    src = sqlite3.connect(path, timeout=5); out = sqlite3.connect(dst)
    try:
        src.backup(out)
    finally:
        out.close(); src.close()
    return dst


def restablecer(path, new_password):
    """Devuelve (ok, mensaje). Lógica separada para poder probarla."""
    from backend.store import Store
    if len(new_password) < 10:
        return False, "La contraseña debe tener al menos 10 caracteres."
    copia = backup(path)
    st = Store(path)
    n_before = st.db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    had = st.db.execute("SELECT 1 FROM users WHERE username='admin'").fetchone() is not None
    st.create_user("admin", new_password, "admin", [])  # misma función que el primer arranque; mismo hash scrypt+sal
    with st.lock:
        st.db.execute("DELETE FROM sessions"); st.db.commit()
    st.audit(None, "system", "admin.password_reset", {"usuario": "admin", "existia": had, "sesiones_cerradas": True})
    n_after = st.db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    st.db.close()
    if n_before != n_after:
        return False, "ERROR inesperado: cambió el número de registros. Restaura la copia: " + copia
    return True, copia


def main():
    p = db_path()
    print("\n  RESTABLECER CONTRASEÑA DE ADMIN (no borra nada)\n")
    if not os.path.exists(p):
        print("  No encuentro la base de datos en:\n   ", p, "\n  Si usabas OTRA carpeta de la app, ejecuta este archivo desde ESA carpeta."
              "\n  (Si es la primera vez que usas la app, no hace falta restablecer nada: INICIAR.bat te mostrará la contraseña.)")
        return 1
    if server_running():
        print("  La aplicación está abierta. Cierra la ventana negra de INICIAR.bat y vuelve a ejecutar esto.")
        return 1
    print("  Escribe la NUEVA contraseña (mínimo 10 caracteres). No se verá al escribir.")
    print("  Si pulsas solo ENTER, se genera una aleatoria que se muestra UNA vez.\n")
    a = getpass.getpass("  Nueva contraseña: ")
    if a:
        if a != getpass.getpass("  Repítela:         "):
            print("\n  No coinciden. No se ha cambiado nada."); return 1
        pw, shown = a, False
    else:
        pw, shown = secrets.token_urlsafe(14), True
    ok, msg = restablecer(p, pw)
    if not ok:
        print("\n  ", msg); return 1
    print("\n  LISTO. Usuario: admin")
    if shown:
        print("  Contraseña nueva (solo se muestra ahora, apúntala):", pw)
    print("  Copia de seguridad previa:", msg)
    print("  Tus expedientes, cuentas y ai.env NO se han tocado. Ya puedes abrir INICIAR.bat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
