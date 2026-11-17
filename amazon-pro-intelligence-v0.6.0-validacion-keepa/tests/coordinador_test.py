"""Coordinador autónomo — pruebas con un proyecto TEMPORAL y suites simuladas. No usa red ni claves reales."""
import json, os, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(); os.environ["AHT_PROYECTO"] = TMP; sys.path.insert(0, os.path.join(ROOT, "tools"))
import coordinador as C
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
open(os.path.join(TMP, "flaky.py"), "w").write("import os,sys\nf='/tmp/_flaky_%d'%os.getppid() if False else os.path.join(os.path.dirname(__file__),'n.txt')\nn=int(open(f).read()) if os.path.exists(f) else 0\nopen(f,'w').write(str(n+1))\nprint('x'); sys.exit(0 if n>=1 else 1)\n")
open(os.path.join(TMP, "ok.py"), "w").write("print('5/5 OK')\n"); open(os.path.join(TMP, "bad.py"), "w").write("print('1/3 OK'); raise SystemExit(1)\n")
open(os.path.join(TMP, "hang.py"), "w").write("import subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c','import time;time.sleep(300)'])\ntime.sleep(300)\n")
open(os.path.join(TMP, "env.py"), "w").write("import os,sys\nsys.exit(1 if os.environ.get('KEEPA_API_KEY') or os.environ.get('AMAZON_PRO_KEEPA_ENABLE')!='0' else 0)\n")
C.main(["x", "init"])
# 1 PASA / INTERMITENTE / FALLA
r = C.qa([("ok", "python3 ok.py", "MOCK"), ("flaky", "python3 flaky.py", "MOCK"), ("bad", "python3 bad.py", "MOCK")], intentos=3)
est = {x["suite"]: x for x in r["resultados"]}
check("QA distingue PASA, INTERMITENTE (pasó al 2º intento) y FALLA (3 intentos)", est["ok"]["estado"] == "PASA" and est["flaky"]["estado"] == "INTERMITENTE" and est["flaky"]["intentos"] == 2 and est["bad"]["estado"] == "FALLA" and est["bad"]["intentos"] == 3)
e = C.estado(); inc = {i["suite"]: i for i in e["incidencias"]}
check("incidencias: la persistente queda BLOQUEADA tras el máximo de intentos y la intermitente ABIERTA", inc["bad"]["estado"] == "BLOQUEADA" and inc["flaky"]["tipo"] == "INTERMITENTE")
r2 = C.qa([("bad", "python3 bad.py", "MOCK")], intentos=3); e = C.estado()
check("los intentos se ACUMULAN entre ejecuciones (6) y no se crea una incidencia duplicada", [i for i in e["incidencias"] if i["suite"] == "bad"][0]["intentos_acumulados"] == 6 and len([i for i in e["incidencias"] if i["suite"] == "bad"]) == 1)
# 2 timeout + huérfanos
L = C.limites(); C._write(C.F_LIM, {**L, "timeout_suite_s": 3}); t0 = time.time()
r3 = C.qa([("hang", "python3 hang.py", "MOCK")], intentos=1)
check("timeout: mata TODO el grupo de procesos (sin huérfanos) y falla en ~3 s", r3["resultados"][0]["estado"] == "FALLA" and time.time() - t0 < 12 and os.system("pgrep -f 'time.sleep(300)' >/dev/null") != 0)
C._write(C.F_LIM, L)
# 3 entorno saneado
os.environ["KEEPA_API_KEY"] = "K" * 64; os.environ["AMAZON_PRO_KEEPA_ENABLE"] = "1"
r4 = C.qa([("env", "python3 env.py", "MOCK")], intentos=1)
check("las pruebas corren SIN claves y con Keepa desactivado aunque el entorno las tenga", r4["resultados"][0]["estado"] == "PASA")
del os.environ["KEEPA_API_KEY"]; os.environ["AMAZON_PRO_KEEPA_ENABLE"] = "0"
# 4 guardia
open(os.path.join(TMP, "keepa.env"), "w").write("KEEPA_API_KEY=" + "a1B2" * 16 + "\n")
ok, m = C.guardia(); check("guardia: un keepa.env dentro del proyecto BLOQUEA", not ok and "keepa.env" in m); os.remove(os.path.join(TMP, "keepa.env"))
check("escaneo detecta una clave en un fichero normal y no la imprime", (open(os.path.join(TMP, "n.cfg"), "w").write("KEEPA_API_KEY=" + "q9W8" * 8 + "\n"), any(h["archivo"] == "n.cfg" and "valor" not in json.dumps(h).replace("valor_oculto", "") for h in C.escaneo()))[1])
rc = C.ciclo(); check("un ciclo con posibles secretos NO se ejecuta y deja PARADA", not rc["ejecutado"] and os.path.exists(C.F_STOP)); os.remove(os.path.join(TMP, "n.cfg"))
rc = C.ciclo(); check("con PARAR activo ningún ciclo se ejecuta", not rc["ejecutado"] and "PARADA" in rc["motivo"])
C.reanudar(); ok, m = C.guardia(); check("reanudar retira la parada", ok)
C._write(C.F_LIM, {**L, "keepa_tokens_max": 10}); ok, m = C.guardia(); check("presupuesto >0 sin autorizado_por del propietario BLOQUEA", not ok and "autorizado_por" in m); C._write(C.F_LIM, L)
# 5 ciclo con objetivo y manejador
C.objetivo("add", "Pasar la batería", handler="qa", prio=1); C.objetivo("add", "Decidir fase siguiente (humano)", prio=9)
C.SUITES[:] = [("ok", "python3 ok.py", "MOCK")]
rc = C.ciclo(); e = C.estado(); o = {x["id"]: x for x in e["objetivos"]}
check("ciclo: ejecuta el objetivo con manejador, lo marca HECHO y deja el humano pendiente en siguientes_acciones", rc["ejecutado"] and o["OBJ-001"]["estado"] == "HECHO" and any("OBJ-002" in s and "requiere" in s for s in e["siguientes_acciones"]))
# 5b recurrentes
C.objetivo("add", "Mantenimiento recurrente", handler="qa", prio=1, cada_horas=1); e = C.estado(); ob = [x for x in e["objetivos"] if x["titulo"] == "Mantenimiento recurrente"][0]
C.ciclo(); e = C.estado(); ob = [x for x in e["objetivos"] if x["titulo"] == "Mantenimiento recurrente"][0]; check("recurrente: se ejecuta y queda HECHO", ob["estado"] == "HECHO")
C.ciclo(); e = C.estado(); ob = [x for x in e["objetivos"] if x["titulo"] == "Mantenimiento recurrente"][0]; check("recurrente: no se repite antes de su periodo", ob["estado"] == "HECHO")
ob["actualizado"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 7200)); C.guardar(e); C.ciclo(); e = C.estado(); ob = [x for x in e["objetivos"] if x["titulo"] == "Mantenimiento recurrente"][0]
check("recurrente: tras 2 h (periodo 1 h) se reabre y vuelve a ejecutarse", time.time() - time.mktime(time.strptime(ob["actualizado"], "%Y-%m-%dT%H:%M:%SZ")) + time.timezone < 60)
# 6 límites de ciclos y fallos consecutivos
e = C.estado(); e["ciclos"] = [{"ts": time.time(), "t": "", "objetivo": None}] * 12; C.guardar(e); ok, m = C.guardia(); check("tope de ciclos en 24 h", not ok and "ciclos" in m)
e["ciclos"] = []; e["fallos_consecutivos"] = 3; C.guardar(e); ok, m = C.guardia(); check("3 ciclos fallidos seguidos paran el sistema", not ok and "seguidos" in m)
e["fallos_consecutivos"] = 0; C.guardar(e)
# 7 candado
open(C.F_LOCK, "w").write("1"); rc = C.ciclo(); check("candado vivo evita dos ciclos simultáneos", not rc["ejecutado"] and "curso" in rc["motivo"]); os.remove(C.F_LOCK)
# 8 registro con cadena de hashes
check("registro encadenado íntegro", C.verificar()["ok"])
lines = open(C.F_REG).read().splitlines(); lines[2] = lines[2].replace('"e"', '"E"'); open(C.F_REG, "w").write("\n".join(lines) + "\n")
check("manipular el registro se DETECTA", not C.verificar()["ok"])
# 9 informe y conexiones
C.conexion("Keepa", "REAL PARCIAL", "ledger", True); C.conexion("GitHub", "NO VERIFICADO", "—", False); p = C.informe(); t = open(p, encoding="utf-8").read()
check("informe: pruebas, conexiones reales/no reales, límites y limitaciones", "## 1. Pruebas" in t and "| Keepa | REAL PARCIAL | SÍ |" in t and "| GitHub | NO VERIFICADO | no |" in t and "Presupuesto" in t)
# 10 respaldo
rb = C.respaldo(); import zipfile; z = zipfile.ZipFile(rb["archivo"]); check("respaldo: ZIP con hash, sin .env/.db", rb["sha256"] and not [n for n in z.namelist() if n.endswith((".env", ".db"))])
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
