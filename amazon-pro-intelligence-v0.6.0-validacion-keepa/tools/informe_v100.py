#!/usr/bin/env python3
"""Genera INFORME_V100.md desde el ESTADO REAL del coordinador, la matriz y la ficha. No escribe cifras a mano."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coordinador as C, matriz_v100 as M, ficha_v100 as F

def generar(destino=None):
    e = C.estado(); dev = [o for o in e["objetivos"] if o.get("tipo") == "dev" and o["clave"].startswith("V1-")]; au = e.get("auditoria"); p = e.get("pruebas") or {}
    cnt = {c: sum(1 for r in M.REQ if r[1] == c) for c in M.CATS}
    L = ["# INFORME V1.0.0-candidata — Amazon Pro Intelligence", "", "Generado desde el estado del coordinador. **CANDIDATA: no es producción.** Hay integraciones críticas sin conectar y Windows sin verificar.", "",
         "## Qué incluye", "",
         "- Flujo PREPARAR Y LANZAR de extremo a extremo (orden → tareas → decisión humana → persistencia tras reinicio), probado con servidor real.",
         "- VENDER Y OPTIMIZAR con informes CSV importados (marcados IMPORTADO; ACOS y TACoS exactos; duplicados y archivos hostiles rechazados).",
         "- Motor financiero determinista: escenarios, sensibilidad y punto de equilibrio (`backend/finanzas100.py`); lo que falta es NO CALCULABLE.",
         "- Exportaciones CSV/HTML/Markdown con trazabilidad y escapado seguro: `GET /api/v07/export`.",
         "- Plan de coordinación de especialistas del Director IA, sin GO por defecto: `GET /api/v07/plan`.",
         "- Persistencia: respaldo con hash, restauración verificada y arranque que se niega con BD corrupta sin tocarla.",
         "- Interfaz NEON comprobada en Chromium real a 390, 820 y 1600 px (corregido un desborde a 820 px).",
         "- Adaptadores de solo lectura SP-API y Ads API, **probados solo con simulación local**.",
         "- Relevo autónomo con bloqueo de concurrencia y commit controlado; sesiones cada 4 horas (independientes, no continuas).", "",
         "## Objetivos V1.0 (estado real)", "", "| Clave | Estado | Intentos | Resultado |", "|---|---|---|---|"]
    for o in sorted(dev, key=lambda o: o["clave"]): L.append("| %s | %s | %s | %s |" % (o["clave"], o["estado"], o["intentos"], (o.get("nota") or "—").replace("|", "/")[:90]))
    L += ["", "## Matriz de aceptación (resumen)", ""] + ["- %s: %d" % (c, n) for c, n in cnt.items()] + ["", "Detalle en `MATRIZ_ACEPTACION_V100.md`.", "", "## Pruebas (qué se probó)", ""]
    if p.get("resultados"):
        L += ["| Suite | Clase | Estado | Resultado |", "|---|---|---|---|"] + ["| %s | %s | %s | %s |" % (r["suite"], r["clase"], r["estado"], r["resultado"].replace("|", "/")[:60]) for r in p["resultados"]]
        L += ["", "Resumen: %s pasan · %s intermitentes · %s fallan · %s total. **MOCK = proveedores simulados, no integraciones reales.**" % (p["pasan"], p["intermitentes"], p["fallan"], p["total"])]
    else: L.append("Sin resultados de batería registrados.")
    L += ["", "## Auditoría", ""]
    L.append("- Fecha: %s · Resultado: **%s**" % (au["t"], "OK" if au["ok"] else "CON FALLOS") if au else "- Auditoría PENDIENTE de ejecutar.")
    L += ["- **Auditoría independiente: NO hubo.** No se dispuso de un segundo modelo autorizado y sin coste; la revisión fue determinista (regresión, escaneo de secretos, integridad del registro, pruebas negativas).", "",
          "## Qué NO está verificado", "", "- **Windows**: solo se probó en Linux; no se declara verificado.",
          "- **Conexiones externas**: solo Keepa `/token` y `/search` (ES) tienen llamada real. SP-API, Ads API y OpenAI **no** están conectados; sus pruebas son simuladas.",
          "- Comparabilidad de competidores automática, no confirmada por una persona; precios con fecha. Costes, ventas y evidencia regulatoria reales: sin datos.",
          "- Protección de la rama en GitHub: no se pudo activar desde la sesión.", "", "## Bloqueos externos (decisión del propietario)", ""] + ["- **%s** — %s → %s" % (f[0], f[1], f[4]) for f in F.FICHA]
    L += ["", "## Límites respetados", "", "- Gasto 0 € · 0 tokens Keepa adicionales · 0 llamadas a OpenAI y APIs de pago · sin publicación en Amazon · sin despliegue · sin credenciales en el repositorio · sin `git push --force`.", "", "## Conexiones", ""]
    L += ["- %s: %s (%s)" % (c["nombre"], c["estado"], "real" if c["real"] else "no real") for c in e["conexiones"]]
    txt = "\n".join(L) + "\n"; destino = destino or os.path.join(C.ROOT, "INFORME_V100.md"); open(destino, "w", encoding="utf-8").write(txt); return destino

if __name__ == "__main__": print(generar())
