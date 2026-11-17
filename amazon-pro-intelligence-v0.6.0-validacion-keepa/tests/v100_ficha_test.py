import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "tools")); sys.path.insert(0, os.path.join(ROOT, "tools"))
import ficha_v100 as F, matriz_v100 as M
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
t = F.generar()
check("cubre Keepa, OpenAI, SP-API, Ads API, Windows y regulatorio", all(re.search(k, t) for k in ("Keepa", "OpenAI", "SP-API", "Ads API", "Windows", "regulatoria")))
check("cada integración tiene los 6 campos", all(len(x) == 7 and all(x) for x in F.FICHA))
check("no contiene secretos (ni cadenas largas alfanuméricas ni asignaciones de claves)", not re.search(r"[A-Za-z0-9]{32,}", t) and not re.search(r"(?i)(key|secret|token)\s*=\s*\S{8,}", t))
check("no pide secretos por chat y los ubica en ficheros locales", "no se pide ningún secreto por chat" in t.lower() and ".env local" in t)
check("coherente con la matriz: todo BLOQUEADO de la matriz aparece en la ficha", all(any(w in t for w in re.findall(r"[A-Za-zÁ-ú\-]{4,}", r[0])[:2]) for r in M.REQ if r[1] == "BLOQUEADO"))
check("Windows figura NO VERIFICADO", "NO VERIFICADO" in t)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
