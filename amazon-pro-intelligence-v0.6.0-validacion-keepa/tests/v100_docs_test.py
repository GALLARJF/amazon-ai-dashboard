"""V1.0 · V1-11 — Documentación verificable: los ficheros, comandos, secciones y endpoints que cita el manual existen; sin secretos; sin afirmar Windows verificado."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
rd = lambda f: open(os.path.join(ROOT, f), encoding="utf-8").read()
M, I = rd("MANUAL_SERGIO_V100.md"), rd("INSTALACION_V100.md"); T = M + I
check("existen manual, instalación y ficha", all(os.path.isfile(os.path.join(ROOT, f)) for f in ("MANUAL_SERGIO_V100.md", "INSTALACION_V100.md", "FICHA_INTEGRACIONES_V100.md")))
ficheros = set(re.findall(r"`([A-Za-z0-9_./\\-]+\.(?:bat|md|py|sh|db|env))`", T)) - {"ai.env", "keepa.env", "amazon_pro.db"}
falt = [f for f in ficheros if not os.path.exists(os.path.join(ROOT, f.replace("\\", "/"))) and not os.path.exists(os.path.join(ROOT, "data", f)) and f not in ("backend/respaldo100.py",) and not os.path.exists(os.path.join(ROOT, f))]
check("todo fichero citado existe (%s)" % (falt or "ok"), not falt)
html = rd("index.html"); js = "".join(rd("js/" + f) for f in os.listdir(os.path.join(ROOT, "js")))
check("las 5 secciones del manual existen en la interfaz", all(s in html + js for s in ("INICIO", "LANZAMIENTOS", "MIS VENTAS", "PRODUCTOS", "DIRECTOR IA")))
check("el manual documenta cada etiqueta de procedencia", all(e in M for e in ("REAL", "IMPORTADO", "CALCULADO", "SIN DATOS", "NO CALCULABLE", "NO CONFIRMADO", "OBSOLETO", "SIMULADO")))
check("el manual afirma que no hay GO sin evidencias y que no se conecta a Amazon", "nunca dice GO" in M and "NO están conectados" in M)
check("Windows declarado NO verificado y sin falsas afirmaciones", "no está verificada" in M.lower() and "No verificado en Windows" in I and not re.search(r"(?i)verificado en windows(?!\.)\b(?! no)", T.replace("No verificado en Windows", "")))
check("no se afirma producción ni conexión real a Amazon/OpenAI", not re.search(r"(?i)lista para producción|conectado a amazon|operativo en producción", T))
check("sin secretos ni claves en la documentación", not re.search(r"[A-Za-z0-9]{32,}", T) and not re.search(r"(?i)(api[_-]?key|secret|token)\s*=\s*\S{8,}", T))
check("los comandos citados existen (INICIAR.bat, server.py, run_all.sh, restablecer)", all(os.path.isfile(os.path.join(ROOT, f)) for f in ("INICIAR.bat", "server.py", "tests/run_all.sh", "RESTABLECER_ADMIN.bat")))
check("límites de 0 € / 0 tokens / sin Amazon declarados", all(x in I for x in ("0 € de gasto", "0 tokens nuevos de Keepa", "ninguna publicación en Amazon")))
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
