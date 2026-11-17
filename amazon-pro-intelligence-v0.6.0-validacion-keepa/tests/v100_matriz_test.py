import os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "tools"))
import matriz_v100 as M
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
t = M.generar()
check("las 4 categorías aparecen", all(("## " + c) in t for c in M.CATS))
check("todo requisito tiene categoría válida", all(r[1] in M.CATS for r in M.REQ))
check("todo BLOQUEADO nombra propietario", all(r[3] for r in M.REQ if r[1] == "BLOQUEADO"))
check("Windows y OpenAI no figuran como verificados", all(r[1] == "BLOQUEADO" for r in M.REQ if re.search("Windows|OpenAI|SP-API", r[0])))
check("lo simulado nunca figura como real", not any(r[1] == "VERIFICADO REAL" and "simulad" in r[2].lower() for r in M.REQ))
check("sin claves en el texto", not re.search(r"[A-Za-z0-9]{32,}", t))
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
