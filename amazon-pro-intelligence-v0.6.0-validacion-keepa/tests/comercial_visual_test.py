"""V1.1 — Evidencia visual de «Economía comercial» (staging local, viewer, solo lectura): 1440/390/360/Pixel 7, 0 errores JS, 0 externas, 0 escrituras, sin texto roto."""
import os, re, socket, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
for k in list(os.environ):
    if k.startswith(("AMAZON_PRO_", "KEEPA_", "OPENAI_", "ANTHROPIC_")): os.environ.pop(k)
PWV = "viewer-pass-x7Qk2m"
os.environ.update(AMAZON_PRO_STAGING="1", AMAZON_PRO_SEED_VIEWERS="auditor", AMAZON_PRO_PASSWORD_AUDITOR=PWV, PLAYWRIGHT_BROWSERS_PATH=os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
EXT = []; _c = socket.socket.connect
def _no_net(self, addr, *a, **k):
    if addr[0] not in ("127.0.0.1", "localhost", "::1"): EXT.append(addr); raise AssertionError("RED PROHIBIDA")
    return _c(self, addr, *a, **k)
socket.socket.connect = _no_net
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "docs", "comercial", "capturas"); os.makedirs(OUT, exist_ok=True)
R = []
def check(n, c, extra=""): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n + ((" → " + str(extra)) if (extra and not c) else ""))
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w")
port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
BAD = re.compile(r"\bundefined\b|\bNaN\b|\[object |\{\{|Traceback")
VPS = [("1440", dict(viewport={"width": 1440, "height": 900})), ("390", dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)), ("360", dict(viewport={"width": 360, "height": 780}, is_mobile=True, has_touch=True)), ("pixel7", None)]
with sync_playwright() as p:
    br = p.chromium.launch()
    for vp, kw in VPS:
        ctx = br.new_context(**(dict(p.devices["Pixel 7"]) if vp == "pixel7" else kw)); pg = ctx.new_page(); perr = []; cerr = []; reqs = []; wr = []
        pg.on("pageerror", lambda e: perr.append(str(e))); pg.on("console", lambda m: cerr.append(m.text) if m.type == "error" and "401" not in m.text else None)
        pg.on("request", lambda r: (reqs.append(r.url) if not r.url.startswith(("http://localhost", "http://127.0.0.1", "data:", "blob:")) else None, wr.append(r.method + " " + r.url) if r.method != "GET" and "/api/login" not in r.url else None))
        pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#lgOpen", state="attached"); pg.click("#lgOpen"); pg.fill("#lgU", "auditor"); pg.fill("#lgP", PWV); pg.click("#lgGo")
        pg.wait_for_selector(".sessu"); pg.wait_for_timeout(1200)
        pg.evaluate("NAV6.go('lanz',3)"); pg.wait_for_selector("#comRoot .card", timeout=20000); pg.wait_for_timeout(800)
        txt = pg.inner_text("#comRoot")
        check(f"[{vp}] muestra 15,40 / 14,81 / 14,62 y NO AUTORIZADO", all(x in txt for x in ("15,40", "14,81", "14,62", "NO AUTORIZADO")), txt[:300])
        check(f"[{vp}] sin texto roto", not BAD.search(txt))
        check(f"[{vp}] sin entradas editables en el panel (viewer solo lectura)", pg.locator("#comRoot input, #comRoot textarea, #comRoot select, #comRoot button").count() == 0)
        check(f"[{vp}] sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
        pg.locator("#comRoot details").evaluate_all("els=>els.forEach(e=>e.open=true)"); pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(OUT, f"economia_comercial_{vp}.png"), full_page=True)
        check(f"[{vp}] 0 errores JS/consola, 0 externas, 0 escrituras", not perr and not cerr and not reqs and not wr, (perr, cerr, reqs[:2], wr[:2]))
        ctx.close()
    br.close()
check("cero conexiones externas (socket)", not EXT)
print("%d/%d OK" % (sum(R), len(R))); sys.exit(0 if all(R) else 1)
