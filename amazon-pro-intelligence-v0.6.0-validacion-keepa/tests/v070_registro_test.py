"""V0.7.0 · V7-06 — Todas las pruebas v0.7 están registradas en la batería (run_all.sh) y en el coordinador (SUITES); nada registrado apunta a un fichero inexistente."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ["AHT_PROYECTO"] = ROOT
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
import coordinador as C
T = os.path.join(ROOT, "tests"); run_all = open(os.path.join(T, "run_all.sh"), encoding="utf-8").read()
v7 = sorted(f for f in os.listdir(T) if re.match(r"(v070_.*_test|ui_v07_test|desarrollo_test|relevo_test)\.py$", f) and f != "v070_registro_test.py")
check("hay al menos las 7 pruebas v0.7/desarrollo esperadas: %s" % v7, {"v070_keepa_real_test.py", "v070_expediente_test.py", "v070_director_test.py", "v070_security_test.py", "ui_v07_test.py", "desarrollo_test.py"} <= set(v7))
for f in v7 + ["v070_registro_test.py"]:
    check("run_all.sh ejecuta tests/%s" % f, ("python3 tests/" + f) in run_all)
cmds = [c for _, c, _ in C.SUITES]
for f in v7 + ["v070_registro_test.py"]:
    check("SUITES del coordinador incluye tests/%s" % f, ("python3 tests/" + f) in cmds)
check("las suites del coordinador tienen nombres únicos", len({n for n, _, _ in C.SUITES}) == len(C.SUITES))
for n, c, cl in C.SUITES:
    m = re.match(r"python3 (tests/\S+\.py)$", c); check("suite «%s»: el fichero existe y la clase es válida" % n, m and os.path.isfile(os.path.join(ROOT, m.group(1))) and cl in ("MOCK", "LOCAL", "REAL-EVIDENCIA", "MOCK+NAVEGADOR", "LOCAL+NAVEGADOR"))
refs = re.findall(r"python3 tests/(\S+\.py)", run_all); check("run_all.sh: ninguna referencia a ficheros inexistentes", all(os.path.isfile(os.path.join(T, r)) for r in refs))
check("run_all.sh conserva el cierre «TODAS LAS SUITES OK» como última instrucción", run_all.strip().splitlines()[-1].startswith("[ $FAIL -eq 0 ] && echo \"TODAS LAS SUITES OK\""))
check("ninguna suite del coordinador puede usar red de pago: entorno de pruebas sin claves y Keepa desactivado", C.entorno_seguro()["AMAZON_PRO_KEEPA_ENABLE"] == "0" and not any("KEEPA_API" in k or "OPENAI" in k for k in C.entorno_seguro()))
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
