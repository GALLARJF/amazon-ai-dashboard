"""V1.0 · V1-02 — Matriz de aceptación en 4 categorías, generada con evidencia real del coordinador (nunca marca real lo simulado)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "tools"))
CATS = ["VERIFICADO REAL", "VERIFICADO SIMULADO", "IMPLEMENTADO NO VERIFICADO", "BLOQUEADO"]
# (requisito, categoría, evidencia/causa, propietario si bloqueado)
REQ = [
 ("Servidor HTTP + SQLite, auditoría encadenada, aislamiento de roles", "VERIFICADO REAL", "suites v0.6/v0.7 locales (servidor y BD reales en Linux)", ""),
 ("Interfaz NEON en Chromium real (Playwright), 5 secciones, capturas", "VERIFICADO REAL", "ui_v07_test + capturas; solo Chromium/Linux", ""),
 ("Keepa /token y /search dominio ES", "VERIFICADO REAL", "docs_v06/evidencia_keepa_real (10 tokens consumidos)", ""),
 ("GitHub: lectura, push, ramas, bloqueo de concurrencia por compare-and-swap", "VERIFICADO REAL", "relevo_test 14/14 con remoto bare local; push real a GALLARJF/amazon-ai-dashboard", ""),
 ("Google Drive: subida de partes de texto", "VERIFICADO REAL", "partes publicados en AHT_AMAZON_PRO_AUTONOMIA", ""),
 ("Tareas programadas: sesiones independientes (mínimo 1 h), no continuas", "VERIFICADO REAL", "ejecución real de V7-02/03/04; cron */15 rechazado", ""),
 ("Director IA determinista, nunca GO por defecto", "VERIFICADO SIMULADO", "v070_director_test con datos Keepa reales guardados, sin IA generativa", ""),
 ("Expediente comercial ACTIVCORE con huecos y desbloqueos", "VERIFICADO SIMULADO", "v070_expediente_test; economía NO CALCULABLE por falta de costes", ""),
 ("Motor económico (econ6) y lanzamiento", "VERIFICADO SIMULADO", "suites v0.6 con datos de prueba", ""),
 ("Flujo PREPARAR Y LANZAR de extremo a extremo con persistencia", "IMPLEMENTADO NO VERIFICADO", "faltan prueba E2E y reinicio de servidor (V1-03)", ""),
 ("VENDER Y OPTIMIZAR con CSV importados", "IMPLEMENTADO NO VERIFICADO", "importador existe; falta prueba de flujo completo (V1-04)", ""),
 ("Exportaciones CSV/HTML/MD", "IMPLEMENTADO NO VERIFICADO", "md/json del expediente probados; CSV/HTML pendientes (V1-06)", ""),
 ("Copia de seguridad/restauración y BD corrupta", "IMPLEMENTADO NO VERIFICADO", "pendiente V1-08", ""),
 ("Móvil: sin desbordes horizontales a 820 px (.hr/.sess)", "IMPLEMENTADO NO VERIFICADO", "defecto conocido preexistente (V1-09)", ""),
 ("Producto por defecto ACTIVCORE (la captura mostró PHIVITAL Magnesio)", "IMPLEMENTADO NO VERIFICADO", "defecto conocido (V1-09)", ""),
 ("Keepa /product y dominios DE/FR/IT/UK", "BLOQUEADO", "sin clave Keepa disponible y sin gasto autorizado", "José: nueva clave en keepa.env local + autorizar tokens"),
 ("OpenAI (IA generativa)", "BLOQUEADO", "API de pago no autorizada", "José: autorizar gasto y clave en ai.env local"),
 ("Amazon SP-API y Ads API", "BLOQUEADO", "sin credenciales ni permisos de vendedor", "José/Sergio: autorizar app y permisos de solo lectura"),
 ("Ejecución en Windows", "BLOQUEADO", "no hay entorno Windows en la sesión; no se declara verificado", "José: ejecutar la prueba en su PC"),
 ("Evidencia regulatoria ACTIVCORE (cosmético UE)", "BLOQUEADO", "requiere documentos del fabricante, no inventados", "José/Laboratorios Klein"),
 ("Costes, ventas y márgenes reales", "BLOQUEADO", "sin datos reales aportados", "Sergio/José: costes y precio objetivo"),
]
def generar():
    out = ["# Matriz de aceptación V1.0", "", "Generada por tools/matriz_v100.py. Sin datos inventados; simulado ≠ real.", ""]
    for c in CATS:
        fil = [r for r in REQ if r[1] == c]
        out += ["## %s (%d)" % (c, len(fil)), "", "| Requisito | Evidencia / causa | Propietario |", "|---|---|---|"]
        out += ["| %s | %s | %s |" % (r[0], r[2], r[3] or "—") for r in fil] + [""]
    return "\n".join(out)
if __name__ == "__main__":
    open(os.path.join(ROOT, "MATRIZ_ACEPTACION_V100.md"), "w", encoding="utf-8").write(generar()); print("OK", len(REQ))
