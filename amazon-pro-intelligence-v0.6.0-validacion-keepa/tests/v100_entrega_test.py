"""V1.0 · V1-12 — Entrega candidata: informe generado del estado real, honesto con lo NO verificado; ZIP sin claves con hash; no se etiqueta producción."""
import os, re, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "tools")); os.environ["AHT_PROYECTO"] = ROOT
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
import coordinador as C, informe_v100 as IV, matriz_v100 as M, ficha_v100 as F
html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read(); srv = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()
check("versión coherente V1.0.0-candidata en interfaz y servidor", html.count("V1.0.0-candidata") >= 2 and "Amazon Pro Intelligence V1.0.0-candidata" in srv)
t = open(IV.generar(os.path.join(ROOT, "INFORME_V100.md")), encoding="utf-8").read(); e = C.estado()
check("informe: secciones obligatorias", all(h in t for h in ("## Qué incluye", "## Objetivos V1.0", "## Matriz de aceptación", "## Pruebas", "## Auditoría", "## Qué NO está verificado", "## Bloqueos externos", "## Límites respetados")))
check("informe: declara CANDIDATA, no producción", "CANDIDATA: no es producción" in t and not re.search(r"(?i)listo para producción|operativo en producción", t))
check("informe: Windows NO verificado, conexiones no reales y ausencia de auditoría independiente", "no se declara verificado" in t and "Auditoría independiente: NO hubo" in t and "simuladas" in t)
dev = {o["clave"]: o for o in e["objetivos"] if o.get("tipo") == "dev" and o["clave"].startswith("V1-")}
check("informe: los objetivos V1 con su estado REAL del coordinador", len(dev) >= 13 and all(re.search(r"\| %s \| %s \|" % (k, o["estado"]), t) for k, o in dev.items()))
check("todos los objetivos previos al de entrega figuran HECHO", all(o["estado"] == "HECHO" for k, o in dev.items() if k != "V1-12"))
check("matriz: las cifras del informe coinciden con la matriz", all("- %s: %d" % (c, sum(1 for r in M.REQ if r[1] == c)) in t for c in M.CATS))
p = e.get("pruebas") or {}
check("informe: cifras = último QA registrado y ninguna suite (salvo esta, que se evalúa a sí misma) falla", bool(p.get("resultados")) and not [r for r in p["resultados"] if r["estado"] != "PASA" and r["suite"] != "v1.0-entrega"] and ("Resumen: %s pasan" % p["pasan"]) in t)
check("informe: lista los bloqueos de la ficha", all(f[0] in t for f in F.FICHA))
check("informe: sin 'None', trazas ni claves", "None" not in t and "Traceback" not in t and not C.SECRETO.search(t))
check("el escaneo del proyecto está limpio", C.escaneo() == [])
z = C.respaldo(); check("respaldo: ZIP con sha256 y más de 100 ficheros", os.path.isfile(z["archivo"]) and len(z["sha256"]) == 64 and z["ficheros"] > 100)
zf = zipfile.ZipFile(z["archivo"]); names = zf.namelist()
check("ZIP: sin .env, .db, claves ni PARAR", not any(n.endswith((".env", ".db", ".pyc")) or "/PARAR" in n or os.path.basename(n) in ("keepa.env", "ai.env") for n in names))
check("ZIP: informe, matriz, ficha, manual, instalación, backend V1 y pruebas V1", all(any(n.endswith(s) for n in names) for s in ("INFORME_V100.md", "MATRIZ_ACEPTACION_V100.md", "FICHA_INTEGRACIONES_V100.md", "MANUAL_SERGIO_V100.md", "INSTALACION_V100.md", "backend/finanzas100.py", "backend/respaldo100.py", "tests/ui_v100_test.py")))
check("ZIP: capturas de la interfaz V1.0 (60+) y evidencias Keepa reales", any("CAPTURAS_UI/6" in n for n in names) and any("evidencia_keepa_real" in n for n in names))
blob = "".join(zf.read(n).decode("utf-8", "ignore") for n in names if n.endswith((".py", ".js", ".md", ".json", ".csv", ".bat", ".sh", ".html", ".jsonl")))
check("ZIP: ningún texto con aspecto de clave real (salvo centinelas de pruebas)", not [m for m in C.SECRETO.finditer(blob) if not C.FALSO.search(blob[max(0, m.start() - 80):m.end() + 80])])
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
