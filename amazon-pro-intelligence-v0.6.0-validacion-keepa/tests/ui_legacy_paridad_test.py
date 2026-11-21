"""Fase 4 · F — paridad de componentes entre la navegación antigua (?legacy=1) y la nueva: NINGÚN encabezado de componente original desaparece (criterio 3 de PLAN_RETIRADA_LEGACY).
Se recorren TODAS las pestañas/sub-vistas en ambos modos (administrador, servidor local, sin red) y se compara el conjunto de títulos (h2/h3/h4/summary, sin cifras ni <small>).
Un título que existe en la antigua y no aparece en ningún sitio de la nueva es un componente perdido."""
import os, re, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.environ["AMAZON_PRO_NO_WORKER"] = "1"
for k in ("KEEPA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"): os.environ.pop(k, None)
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
R = []
def check(n, c): R.append(bool(c)); print(("OK   " if c else "FAIL ") + n)
tmp = tempfile.mkdtemp(); srv = S.make_server(0, admin_token="t", db_path=os.path.join(tmp, "s.db"), cfg_fn=lambda: AI.config({}), admin_password="admin-pass-p9Zt4w"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
HEAD = """() => [...document.querySelectorAll('h2,h3,h4,summary,legend,.v6sec>h3')].map(e => { const c = e.cloneNode(true); c.querySelectorAll('small,.chip,.tagst,.sub,span.n,button').forEach(x => x.remove()); return c.textContent; })
  .map(t => t.replace(/\\s+/g, ' ').replace(/[0-9]+([.,][0-9]+)?/g, '#').replace(/[()·:—–\\-]/g, ' ').replace(/\\s+/g, ' ').trim().toLowerCase()).filter(t => t.length > 3)"""
TABS = ["inicio", "lanz", "ventas", "prod", "dir", "panel", "k4", "prelaunch", "europa", "piloto", "hist", "estado", "aprob"]
def login(pg):
    pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-pass-p9Zt4w"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(2000)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page(); pg.goto(f"http://localhost:{port}/?legacy=1"); pg.wait_for_selector("#tabs"); login(pg); OLD = set()
    for t in TABS:
        pg.click(f'#tabs button[data-tab="{t}"]'); pg.wait_for_timeout(1500)
        if t == "k4":
            for v in pg.evaluate("[...document.querySelectorAll('[data-k4v]')].map(e=>e.dataset.k4v)"): pg.evaluate(f"document.querySelector('[data-k4v=\"{v}\"]').click()"); pg.wait_for_timeout(900); OLD |= set(pg.evaluate(HEAD))
        OLD |= set(pg.evaluate(HEAD))
    pg.close()
    pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page(); pg.goto(f"http://localhost:{port}/"); pg.wait_for_selector("#nav6", state="attached"); login(pg); NEW = set()
    pg.add_init_script("0")
    for sid, subs in (("hoy", [0]), ("ventas", [0, 1, 2]), ("prod", [0, 1, 2, 3]), ("lanz", [0, 1, 2]), ("dir", [0, 1]), ("adm", [0]), ("dec", [0])):
        for j in subs:
            pg.evaluate(f"NAV6.go('{sid}',{j})"); pg.wait_for_timeout(1500); pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)"); pg.wait_for_timeout(500)
            if sid == "ventas" and j == 1 or sid == "prod" and j in (1, 2) or sid == "dir" and j == 1:
                pg.wait_for_timeout(800)
            NEW |= set(pg.evaluate(HEAD))
    pg.evaluate("NAV6.setMode && NAV6.setMode('demo')"); pg.wait_for_timeout(800); pg.evaluate("NAV6.go('ventas',2)"); pg.wait_for_timeout(1500); NEW |= set(pg.evaluate(HEAD))
    b.close()
lost = sorted(OLD - NEW)
print(f"componentes (títulos) en la navegación antigua: {len(OLD)} · en la nueva: {len(NEW)} · perdidos: {len(lost)}")
for x in lost[:60]: print("   perdido:", x)
check(f"paridad: los {len(OLD)} títulos de componentes de la navegación antigua existen en la nueva (perdidos: {len(lost)})", not lost)
check("la navegación antigua tiene un volumen razonable de componentes (≥ 56)", len(OLD) >= 56)
print(f"{sum(R)}/{len(R)} OK"); sys.exit(0 if all(R) else 1)
