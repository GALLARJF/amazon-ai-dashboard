"""Pruebas del ciclo de desarrollo: dependencias, 3 intentos -> BLOQUEADO y continuar con independientes, HECHO al pasar, guardia."""
import os, sys, tempfile, shutil, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); tmp = tempfile.mkdtemp(); os.makedirs(os.path.join(tmp, "tests"))
os.environ["AHT_PROYECTO"] = tmp; sys.path.insert(0, os.path.join(ROOT, "tools"))
import coordinador as C, desarrollo as D
n = ok = 0
def chk(c, m):
    global n, ok; n += 1; ok += bool(c); print(("OK   " if c else "FALLO ") + m)
open(os.path.join(tmp, "tests", "run_all.sh"), "w").write("")
D.BACKLOG_V1[:] = []
D.BACKLOG[:] = [("T-1", 1, "falla siempre", "s", "python3 -c 'import sys; sys.exit(1)'", []), ("T-2", 2, "depende de T-1", "s", "python3 -c 'pass'", ["T-1"]), ("T-3", 3, "independiente", "s", "python3 -c 'pass'", [])]
C.main(["x", "init"]); chk(D.sembrar()["nuevos"] == 3 and D.sembrar()["nuevos"] == 0, "sembrar es idempotente")
s = D.siguiente(); chk(s["objetivo"]["clave"] == "T-1", "elige primero la de menor prioridad")
r = D.verificar("T-1"); chk(r["estado"] == "EN_CURSO" and r["intento"] == 1, "1.er fallo: sigue en curso")
D.verificar("T-1"); r = D.verificar("T-1"); chk(r["estado"] == "BLOQUEADO" and r["intento"] == 3, "3.er fallo: BLOQUEADO")
s = D.siguiente(); chk(s["objetivo"]["clave"] == "T-3", "bloqueado: continúa con tarea independiente y NO con la dependiente")
r = D.verificar("T-3"); chk(r["estado"] == "HECHO", "aceptación OK -> HECHO")
s = D.siguiente(); chk(s["objetivo"] is None and s["bloqueados"] == ["T-1"], "sin ejecutables: informa los bloqueados")
open(os.path.join(tmp, "PARAR"), "w").write("prueba"); chk(D.siguiente()["objetivo"] is None, "la guardia (PARAR) impide empezar trabajo"); os.remove(os.path.join(tmp, "PARAR"))
chk(C.verificar()["ok"], "registro íntegro tras el ciclo")
shutil.rmtree(tmp); print("%d/%d OK" % (ok, n)); sys.exit(0 if ok == n else 1)
