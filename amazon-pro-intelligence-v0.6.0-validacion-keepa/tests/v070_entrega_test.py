"""V0.7.0 · V7-07 — Entrega candidata: versión coherente, informe generado desde el estado real (declara lo NO verificado), paquete ZIP sin claves y con hash registrado."""
import hashlib, json, os, re, subprocess, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "tools")); os.environ["AHT_PROYECTO"] = ROOT
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
import coordinador as C, informe_v070 as IV
html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read(); srv = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()
check("index.html: título y cabecera dicen V0.7.0 y ninguna V0.6.0", html.count("V0.7.0") >= 2 and "V0.6.0" not in html)
check("server.py: el arranque anuncia V0.7.0", "Amazon Pro Intelligence V0.7.0" in srv and "Amazon Pro Intelligence V0.6.0" not in srv)
d = IV.generar(os.path.join(ROOT, "INFORME_V070.md")); t = open(d, encoding="utf-8").read(); e = C.estado()
check("informe: secciones obligatorias (incluye, objetivos, pruebas, auditoría, NO verificado, límites)", all(h in t for h in ("## Qué incluye V0.7.0", "## Objetivos de desarrollo", "## Pruebas", "## Auditoría", "## Qué NO está verificado", "## Límites respetados")))
check("informe: declara que Windows y las conexiones externas NO están verificados y 0 €/0 tokens", "Windows" in t and "no se declara verificado" in t and "Conexiones externas" in t and "0 € · 0 tokens Keepa" in t)
dev = {o["clave"]: o for o in e["objetivos"] if o.get("tipo") == "dev"}
check("informe: lista los 7 objetivos con su estado REAL (coincide con el estado del coordinador)", len(dev) == 7 and all(re.search(r"\| %s \| %s \|" % (k, o["estado"]), t) for k, o in dev.items()))
check("informe: V7-01..V7-06 figuran HECHO (nada se da por hecho sin aceptación)", all(dev[k]["estado"] == "HECHO" for k in ("V7-01", "V7-02", "V7-03", "V7-04", "V7-05", "V7-06")))
p = e.get("pruebas") or {}; check("informe: las cifras de pruebas son las del último QA registrado", (not p.get("resultados")) or "Resumen: %s pasan · %s intermitentes · %s fallan · %s total" % (p["pasan"], p["intermitentes"], p["fallan"], p["total"]) in t)
check("informe: sin 'None' ni trazas ni claves", "None" not in t and "Traceback" not in t and not C.SECRETO.search(t))
check("el estado no contiene claves y el escaneo del proyecto está limpio", C.escaneo() == [])
z = C.respaldo(); check("respaldo: ZIP creado con sha256 y recuento", os.path.isfile(z["archivo"]) and len(z["sha256"]) == 64 and z["ficheros"] > 100)
try:
    zf = zipfile.ZipFile(z["archivo"]); names = zf.namelist(); base = names[0].split("/")[0]
    check("ZIP: sin .env, .db, claves ni PARAR", not any(n.endswith((".env", ".db", ".pyc")) or "/PARAR" in n or os.path.basename(n) in ("keepa.env", "ai.env") for n in names))
    check("ZIP: contiene informe, backend v07, pruebas v070, capturas 40+ y evidencias Keepa reales", all(any(n.endswith(s) for n in names) for s in ("INFORME_V070.md", "backend/keepa_real.py", "backend/expediente7.py", "backend/director7.py", "js/v07.js", "tests/v070_security_test.py", "CAPTURAS_UI/43_v07_director_ia.png", "docs_v06/evidencia_keepa_real/competidores_ES.json")))
    blob = "".join(zf.read(n).decode("utf-8", "ignore") for n in names if n.endswith((".py", ".js", ".md", ".json", ".csv", ".bat", ".sh", ".html", ".jsonl")))
    check("ZIP: ningún texto con aspecto de clave real (patrón del coordinador, salvo centinelas de pruebas)", not [m for m in C.SECRETO.finditer(blob) if not C.FALSO.search(blob[max(0, m.start() - 80):m.end() + 80])])
    check("ZIP: hash registrado en el log coincide con el archivo", hashlib.sha256(open(z["archivo"], "rb").read()).hexdigest() == z["sha256"] and any(("RESPALDO" in l and z["sha256"] in l) for l in open(C.F_REG, encoding="utf-8")))
finally:
    try: os.remove(z["archivo"])
    except OSError: pass
check("registro del coordinador íntegro", C.verificar()["ok"])
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
