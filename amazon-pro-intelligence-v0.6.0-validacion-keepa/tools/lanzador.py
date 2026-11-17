"""Lanzador de AHT Amazon Pro Intelligence (Windows/Linux/macOS).
Hace: 1) comprueba el puerto, 2) evita instancias duplicadas, 3) arranca el servidor local (solo 127.0.0.1),
4) abre el navegador, 5) muestra errores claros, 6) sale limpiamente (Ctrl+C o cerrar la ventana).
No imprime ni empaqueta claves: ai.env y keepa.env los lee el propio servidor."""
import http.client, json, os, signal, socket, subprocess, sys, time, webbrowser
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("AMAZON_PRO_PORT", "8765"))

def es_nuestra(port, timeout=1.5):
    """True si en ese puerto ya responde NUESTRA app (instancia ya en marcha)."""
    try:
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        c.request("GET", "/api/status", headers={"Host": f"localhost:{port}"}); r = c.getresponse(); j = json.loads(r.read().decode() or "{}")
        return r.status == 200 and isinstance(j, dict) and "write_actions" in j
    except (OSError, ValueError):
        return False

def puerto_libre(port):
    s = socket.socket(); s.settimeout(1)
    if os.name != "nt": s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ignora TIME_WAIT (en Windows no: permitiría robar puerto)
    try:
        s.bind(("127.0.0.1", port)); return True
    except OSError:
        return False
    finally:
        s.close()

def elegir(port):
    """Devuelve (accion, puerto, mensaje): 'abrir' (ya está en marcha), 'arrancar' o 'error'."""
    if es_nuestra(port): return "abrir", port, f"Ya hay una instancia en http://localhost:{port}: se abre sin duplicar."
    if puerto_libre(port): return "arrancar", port, ""
    for p in range(port + 1, port + 10):
        if es_nuestra(p): return "abrir", p, f"Ya hay una instancia en http://localhost:{p}."
        if puerto_libre(p): return "arrancar", p, f"El puerto {port} está ocupado por otro programa; se usa el {p}."
    return "error", port, f"Los puertos {port}-{port + 9} están ocupados por otros programas. Ciérralos o define AMAZON_PRO_PORT."

def main(argv=None, abrir_navegador=True):
    accion, port, msg = elegir(PORT)
    if msg: print(" " + msg)
    if accion == "error":
        print(" ERROR: " + msg); return 2
    url = f"http://localhost:{port}"
    if accion == "abrir":
        if abrir_navegador: webbrowser.open(url)
        return 0
    py = sys.executable or "python"
    print(f" Arrancando AHT Amazon Pro Intelligence en {url} (solo accesible desde este ordenador).")
    print(" Para salir: cierra esta ventana o pulsa Ctrl+C. Las claves se leen de ai.env / keepa.env (nunca se muestran).")
    def _stop(*_): raise KeyboardInterrupt
    try: signal.signal(signal.SIGTERM, _stop)  # ANTES de arrancar el servidor: si no, un SIGTERM temprano mata al lanzador y deja el servidor huérfano (bloqueo intermitente V0.6.1)
    except (ValueError, OSError): pass
    try:
        proc = subprocess.Popen([py, os.path.join(ROOT, "server.py"), str(port)], cwd=ROOT)
    except OSError as e:
        print(f" ERROR: no se pudo iniciar Python/servidor: {e}"); return 3
    try:
        for _ in range(60):
            if proc.poll() is not None:
                print(f" ERROR: el servidor se cerró al arrancar (código {proc.returncode}). Revisa los mensajes de arriba."); return 4
            if es_nuestra(port): break
            time.sleep(0.25)
        else:
            print(" ERROR: el servidor no responde tras 15 s."); proc.terminate(); return 5
        if abrir_navegador: webbrowser.open(url)
        return proc.wait()
    except KeyboardInterrupt:
        print("\n Cerrando de forma segura…"); proc.terminate()
        try: proc.wait(timeout=8)
        except subprocess.TimeoutExpired: proc.kill()
        return 0

if __name__ == "__main__":
    sys.exit(main())
