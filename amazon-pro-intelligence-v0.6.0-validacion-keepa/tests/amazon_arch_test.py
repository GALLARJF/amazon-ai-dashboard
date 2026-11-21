"""Fase 4 · E — arquitectura Amazon (SP-API y Ads API): declarativa, desactivada por defecto, solo lectura, sin credenciales en el repositorio, sin llamadas reales."""
import os, re, socket, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
calls = []
socket.socket.connect = lambda *a, **k: calls.append(a) or (_ for _ in ()).throw(OSError("red bloqueada en la prueba"))
from backend import amazon_arch as A, conectores100 as C
m = A.manifiesto()
need = {"Catálogo", "Pedidos", "Inventario FBA", "Informes", "Tarifas", "Finanzas", "Campañas", "Palabras clave", "Gasto, ventas atribuidas, ACoS y ROAS"}
check("cubre catálogo, pedidos, inventario, informes, tarifas, finanzas, campañas, palabras clave y gasto/ACoS/ROAS", {c["nombre"] for c in m["capacidades"]} == need)
check("todas las capacidades DESACTIVADAS y dentro de la lista blanca de solo lectura", all(c["estado"] == "DESACTIVADA" and c["permitida"] for c in m["capacidades"]))
check("declarado solo lectura; escritura NO IMPLEMENTADA", m["solo_lectura"] and m["escritura"] == "NO IMPLEMENTADA")
check("la lista blanca no admite rutas de escritura (publicar, precios, inventario, campañas)", not any(re.search(r"listings|feeds|pricing|submit|create|update|delete|sp/campaigns/\w+|bid", r, re.I) for s in C.SERVICIOS.values() for r in s["rutas"]))
for svc in ("spapi", "ads"):
    c = C.Conector(svc, {}); e = c.estado()
    check(f"{svc}: sin credenciales → NO CONECTADO y no operativo", e["estado"] == "NO CONECTADO" and not e["operativo"] and e["faltan"])
    try: c.get(C.SERVICIOS[svc]["rutas"][0].strip("^$").replace("(/[A-Z0-9]{10})?", ""), modo="REAL"); ok = False
    except C.ConectorError: ok = True
    check(f"{svc}: modo REAL imposible sin credenciales + AMAZON_PRO_LIVE_*", ok)
    full = {v: "x" for v in C.SERVICIOS[svc]["vars"]}
    try: C.Conector(svc, full).get(C.SERVICIOS[svc]["rutas"][0].strip("^$").replace("(/[A-Z0-9]{10})?", ""), modo="REAL"); ok = False
    except C.ConectorError: ok = True
    check(f"{svc}: con credenciales pero sin AMAZON_PRO_LIVE_* sigue sin llamar", ok)
for bad in ("/listings/2021-08-01/items/A/B", "/feeds/2021-06-30/feeds", "/products/pricing/v0/price", "/sp/campaigns/123"):
    try: C.Conector("spapi", {}).get(bad); ok = False
    except C.ConectorError: ok = True
    check(f"ruta de escritura/no permitida rechazada: {bad}", ok)
check("variables de Render documentadas (servidor + adaptador + interruptor LIVE)", all(m["variables"][s]["variables"] and m["variables"][s]["interruptor"].startswith("AMAZON_PRO_LIVE_") for s in ("spapi", "ads")))
check("cero conexiones de red abiertas durante la prueba", not calls)
# sin secretos en el repositorio
pat = re.compile(r"(Atzr\|[A-Za-z0-9_\-]{20,}|amzn1\.(oa2-client|application-oa2-client)\.[0-9a-f]{20,}|amzn1\.sp\.solution\.[0-9a-f-]{20,}|sk-[A-Za-z0-9]{30,}|ghp_[A-Za-z0-9]{30,})")
hits = []
for d, ds, fs in os.walk(ROOT):
    ds[:] = [x for x in ds if x not in (".git", "__pycache__", "node_modules")]
    for f in fs:
        if f.endswith((".py", ".js", ".md", ".yaml", ".yml", ".json", ".bat", ".html", ".env", ".txt", ".csv")):
            try: t = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
            except OSError: continue
            if pat.search(t): hits.append(os.path.relpath(os.path.join(d, f), ROOT))
check(f"ninguna credencial ni token con formato Amazon/OpenAI/GitHub en el repositorio {hits[:3]}", not hits)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
