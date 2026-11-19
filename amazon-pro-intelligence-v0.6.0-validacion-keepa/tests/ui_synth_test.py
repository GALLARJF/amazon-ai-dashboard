"""V0.3.4 — UI real (Playwright): el expediente «SINTÉTICO · PRUEBA API» aparece en el desplegable del Director, la primera llamada de pago exige confirmación,
los errores se explican en llano y la respuesta se marca como procedente de OpenAI solo si se verifica. SIN red: AI._post parcheado para api.openai.com."""
import hashlib, json, os, sys, tempfile, threading, urllib.error, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from playwright.sync_api import sync_playwright
import server as S
from backend import ai as AI
OUT = os.path.join(ROOT, "capturas"); R = []
def check(n, c): R.append((n, bool(c))); print(("OK   " if c else "FAIL ") + n)
KEY = "sk-proj-CENTINELA-UI-0f1e2d3c4b5a69788796-NO-REAL"
ENV = {"AMAZON_PRO_AI_PROVIDER": "openai", "OPENAI_API_KEY": KEY, "AMAZON_PRO_AI_ENABLE": "1", "AMAZON_PRO_AI_MONTHLY_BUDGET": "2", "AMAZON_PRO_AI_MAX_COST": "0.02"}
CALLS = []; MODE = {"m": "401"}
def fake_post(url, headers, body, timeout):
    assert url == "https://api.openai.com/v1/responses", url
    CALLS.append(1)
    if MODE["m"] == "401": raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, io.BytesIO(b'{"error":{"message":"bad key ' + headers["Authorization"].encode() + b'"}}'))
    return 200, json.dumps({"id": "resp_ui_0001", "object": "response", "status": "completed", "model": "gpt-6-luna-2026", "output": [{"type": "message", "content": [{"type": "output_text", "text": "Resumen del expediente sintético: la decisión determinista es GO [F1]. Falta documentar el vídeo [F2]."}]}], "usage": {"input_tokens": 1100, "output_tokens": 90, "output_tokens_details": {"reasoning_tokens": 30}}})
AI._post = fake_post
srv = S.make_server(0, admin_token="t", db_path=os.path.join(tempfile.mkdtemp(), "s.db"), cfg_fn=lambda: AI.config(ENV), admin_password="admin-password-123"); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); st = S.APP["store"]
ph = "phivital-pendiente"; dig = lambda: hashlib.sha256(json.dumps([r for r in st.list(ph, "dossier")], sort_keys=True, default=str).encode()).hexdigest()
from backend import pilot as P
st.put(ph, "dossier", {"name": "PHIVITAL Magnesio · piloto", "origin": "INCOMPLETO", "dossier": P.template()}, key="phivital-magnesio", actor="admin")
before = dig(); n_ph = len(st.list(ph, "dossier"))
import time
def wait_text(pg, sub, n=1, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if pg.inner_text("#chat").count(sub) >= n: return True
        pg.wait_for_timeout(150)
    return False
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 1600, "height": 840}).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    pg.goto(f"http://localhost:{port}/?legacy=1"); pg.wait_for_selector("#tabs"); pg.click("#tabs button[data-tab=panel]"); pg.wait_for_selector("#kpis .kpi"); pg.click("#lgOpen"); pg.fill("#lgU", "admin"); pg.fill("#lgP", "admin-password-123"); pg.click("#lgGo"); pg.wait_for_selector(".sessu"); pg.wait_for_timeout(800)
    opts = pg.eval_on_selector_all("#dirDossier option", "els => els.map(e => e.textContent)")
    check("el desplegable ofrece «SINTÉTICO · PRUEBA API» etiquetado como prueba segura", any("SINTÉTICO · PRUEBA API" in o and "prueba segura" in o for o in opts))
    check("el desplegable conserva el expediente PHIVITAL tal cual", any("PHIVITAL" in o.upper() for o in opts))
    check("hay un botón visible para probar la API con el sintético", pg.is_visible("#dirSynth"))
    pg.select_option("#dirDossier", "__synth__"); pg.wait_for_timeout(300)
    check("el expediente sintético queda seleccionado", pg.eval_on_selector("#dirDossier", "e => e.value") == "__synth__")
    # 1) cancelar la confirmación: nada sale, nada se cobra
    pg.fill("#chatIn", "resumen general"); pg.press("#chatIn", "Enter"); pg.wait_for_selector(".confirm-box")
    box = pg.inner_text(".confirm-box")
    check("diálogo de confirmación: modelo, coste máximo, qué se envía y que la clave no sale", "gpt-6-luna" in box and "Coste máximo" in box and "SINTÉTICO" in box and "clave no sale" in box)
    pg.screenshot(path=f"{OUT}/09_confirmacion_primera_llamada_1600x840.png")
    pg.click("#cfNo"); pg.wait_for_timeout(500)
    check("cancelar: mensaje claro, CERO llamadas a OpenAI", "Cancelado" in pg.inner_text("#chat") and not CALLS)
    # 2) confirmar con error 401: explicación comprensible
    pg.fill("#chatIn", "resumen general"); pg.press("#chatIn", "Enter"); pg.wait_for_selector(".confirm-box"); pg.click("#cfYes"); wait_text(pg, 'no aceptó la clave')
    t = pg.inner_text("#chat")
    check("error 401 explicado en llano (clave mal copiada/revocada, no se cobra) y sin secretos", "OpenAI no aceptó la clave" in t and "No se cobra nada" in t and KEY not in t and len(CALLS) == 1)
    pg.screenshot(path=f"{OUT}/10_error_explicado_1600x840.png")
    check("tras un 401 la IA real NO queda verificada y la reserva se libera", not st.real_ai_verified() and st.ai_usage()["real_cost"] == 0)
    # 3) confirmar con éxito
    MODE["m"] = "ok"; pg.click("#dirSynth"); pg.wait_for_selector(".confirm-box"); pg.click("#cfYes"); wait_text(pg, 'procede de OpenAI')
    t = pg.inner_text("#chat")
    check("respuesta REAL con procedencia verificada, id de respuesta, modelo, duración, tokens y coste estimado", "procede de OpenAI" in t and "resp_ui_0001" in t and "1100/90" in t and "coste est." in t and "IA REAL" in t)
    pg.screenshot(path=f"{OUT}/11_respuesta_real_verificada_1600x840.png")
    check("IA real verificada solo tras éxito con procedencia", st.real_ai_verified())
    # 4) ya verificada: no vuelve a pedir confirmación para el sintético
    n = len(CALLS); pg.fill("#chatIn", "otra pregunta"); pg.press("#chatIn", "Enter"); wait_text(pg, 'otra pregunta'); wait_text(pg, 'Decisión determinista', 3); pg.wait_for_timeout(500)
    check("verificada la IA real, ya no se pide confirmación para el sintético", not pg.query_selector(".confirm-box") and len(CALLS) == n + 1)
    # 5) PHIVITAL tras verificar: sigue sin tocarse
    check("sin errores JS ni CSP", not errs)
    b.close()
calls = st.ai_calls()
check("registro mínimo de llamadas: solo estado, duración, tokens, coste, modelo e id (sin textos ni secretos)", calls and all(set(c) <= {"status", "error", "mode", "model", "duration_ms", "tokens_in", "tokens_out", "cost_estimate", "currency", "response_id", "origin_verified", "ts"} for c in calls) and KEY not in json.dumps(calls))
check("el expediente PHIVITAL no se ha alterado en ningún momento", dig() == before and len(st.list(ph, "dossier")) == n_ph == 1)
check("la clave no está en la BD ni en los registros", KEY not in json.dumps(st.audit_list(None, 500)) and KEY not in json.dumps([r for k in ("ai_run", "query", "task") for a in ("sintetico-primera-llamada",) for r in st.list(a, k)], default=str))
f = sum(1 for _, c in R if not c); print(f"{len(R) - f}/{len(R)} OK"); sys.exit(1 if f else 0)
