"""AUDITORÍA VISUAL AUTENTICADA DE STAGING (solo lectura; sin funcionalidades nuevas).
Arranca el servidor EN PROCESO con AMAZON_PRO_STAGING=1 (misma configuración que render.staging.yaml: datos sintéticos, conectores apagados), inicia sesión
por la interfaz real como viewer («auditor») y recorre las 6 secciones/15 pantallas a 1440, 390, 360 y Pixel 7. Comprueba: sesión viewer, banner de datos
sintéticos, sin «PRODUCCIÓN» ni «datos reales», sin texto roto (undefined/NaN/[object), sin errores JS ni de consola, sin imágenes rotas, sin desbordamiento
horizontal de la página, cero llamadas externas. Capturas en docs/p0_hoy/auditoria_visual_staging/<vp>/. NO es el staging real de Render (ver informe)."""
import glob, json, os, re, socket, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
for k in list(os.environ):
    if k.startswith("AMAZON_PRO_"): os.environ.pop(k)
PW = {"admin": "admin-pass-p9Zt4w", "auditor": "viewer-pass-x7Qk2m"}   # valores de PRUEBA locales (ya presentes en la batería); no son credenciales reales
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR=PW["auditor"], PLAYWRIGHT_BROWSERS_PATH=os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
EXT = []; _c = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(addr); raise AssertionError("RED PROHIBIDA")
    return _c(self, addr, *a, **k)
socket.socket.connect = _no_net
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "p0_hoy", "auditoria_visual_staging"); os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, "*", "*.png")): os.remove(f)
R = []; FINDINGS = []
def check(n, c, extra=""):
    R.append(bool(c)); print(("OK   " if c else "FAIL ") + n + (("  → " + extra) if (extra and not c) else ""))
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password=PW["admin"])
port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
SUBS = [("hoy", 1), ("ventas", 2), ("prod", 4), ("lanz", 3), ("dir", 2), ("dec", 1), ("adm", 2)]
VPS = [("1440", dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1)), ("390", dict(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True)),
       ("360", dict(viewport={"width": 360, "height": 780}, device_scale_factor=1, is_mobile=True, has_touch=True)), ("pixel7", None)]
BAD = re.compile(r"\bundefined\b|\bNaN\b|\[object |\bnull\b(?!\s*[,:(])|\{\{|\}\}|Traceback")
with sync_playwright() as p:
    br = p.chromium.launch()
    for vp, kw in VPS:
        d = os.path.join(OUT, vp); os.makedirs(d, exist_ok=True)
        ctx = br.new_context(**(dict(p.devices["Pixel 7"]) if vp == "pixel7" else kw)); pg = ctx.new_page(); perr = []; cerr = []; reqs = []
        pg.on("pageerror", lambda e: perr.append(str(e))); pg.on("console", lambda m: cerr.append(m.text) if m.type == "error" else None)
        pg.on("request", lambda r: reqs.append(r.url) if not r.url.startswith(("http://localhost", "http://127.0.0.1", "data:", "blob:")) else None)
        pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#lgOpen", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", PW["auditor"]); pg.click("#lgGo")
        pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1500)
        body = pg.inner_text("body")
        check(f"[{vp}] sesión iniciada por la interfaz como viewer (texto «viewer» visible)", re.search(r"viewer", body, re.I) is not None)
        check(f"[{vp}] banner de datos sintéticos visible", re.search(r"DATOS FICTICIOS|SINTÉTIC", body, re.I) is not None)
        n = 0
        for s, c in SUBS:
            for i in range(c):
                pg.evaluate(f"NAV6.go('{s}',{i})"); pg.wait_for_timeout(1300); n += 1
                if (s, i) == ("lanz", 2) and pg.locator(".eucard[data-pid]").count(): pg.locator(".eucard[data-pid]").first.click(); pg.wait_for_selector(".euconc", timeout=15000); pg.wait_for_timeout(500)
                txt = pg.inner_text("body"); tag = f"{s}{i}"
                pg.screenshot(path=os.path.join(d, f"{tag}.png"), full_page=(vp in ("1440", "390")))   # 360/Pixel 7: solo viewport (peso del repositorio)
                ov = pg.evaluate("()=>({sw:document.documentElement.scrollWidth,iw:window.innerWidth})")
                if ov["sw"] > ov["iw"] + 1: FINDINGS.append(f"[{vp}] {tag}: desbordamiento horizontal de página ({ov['sw']} > {ov['iw']})")
                m = BAD.search(txt)
                if m: FINDINGS.append(f"[{vp}] {tag}: texto roto «{m.group(0)}»")
                if re.search(r"PRODUCCI[ÓO]N|datos reales", txt, re.I) and not re.search(r"DEMO|SINT", txt, re.I): FINDINGS.append(f"[{vp}] {tag}: aparece PRODUCCIÓN/datos reales")
                broken = pg.evaluate("()=>[...document.images].filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src.slice(-60))")
                if broken: FINDINGS.append(f"[{vp}] {tag}: imágenes rotas {broken}")
        check(f"[{vp}] {n} pantallas recorridas con captura", n == sum(c for _, c in SUBS))
        check(f"[{vp}] sin errores JS (pageerror)", not perr, "; ".join(perr[:3]))
        ce = [x for x in cerr if "favicon" not in x.lower()]
        check(f"[{vp}] sin errores de consola (salvo 4xx de lectura esperados)", not [x for x in ce if not re.search(r"40[134]|403 \(Forbidden\)", x)], "; ".join(ce[:3]))
        check(f"[{vp}] cero peticiones externas", not reqs, "; ".join(reqs[:3]))
        ctx.close()
    br.close()
check("cero conexiones de socket externas", not EXT, str(EXT[:3]))
check("hallazgos visuales automáticos = 0", not FINDINGS, " | ".join(FINDINGS[:8]))
json.dump({"findings": FINDINGS, "ok": sum(R), "total": len(R)}, open(os.path.join(OUT, "resultado.json"), "w"), ensure_ascii=False, indent=1)
print(f"{sum(R)}/{len(R)} OK" + ("" if not FINDINGS else f" · {len(FINDINGS)} hallazgos"))
for f in FINDINGS: print("  HALLAZGO", f)
sys.exit(0 if all(R) else 1)
