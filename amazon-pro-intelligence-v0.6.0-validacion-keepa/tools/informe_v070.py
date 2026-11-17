#!/usr/bin/env python3
"""Genera INFORME_V070.md a partir del ESTADO REAL del coordinador (objetivos, auditoría, pruebas, conexiones). No escribe cifras a mano."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coordinador as C


def generar(destino=None):
    e = C.estado(); dev = [o for o in e["objetivos"] if o.get("tipo") == "dev" and o["clave"].startswith("V7-")]; au = e.get("auditoria"); p = e.get("pruebas") or {}
    L = ["# INFORME V0.7.0 — Entrega candidata (Amazon Pro Intelligence)", "", "Generado desde el estado del coordinador (AUTONOMIA/estado.json). Candidata: NO es producción; no se ha desplegado ni publicado nada.", "",
         "## Qué incluye V0.7.0", "",
         "- Datos reales de Keepa (única consulta autorizada, 10 tokens, ES) integrados sin red: `GET /api/v07/keepa-real`.",
         "- Expediente comercial ACTIVCORE: producto, economía, mercado, regulatorio y decisión; veredicto nunca GO por defecto: `GET /api/v07/expediente` (json/md).",
         "- Director IA determinista (sin IA): prioridades, preguntas al propietario y hechos citados: `GET /api/v07/briefing`.",
         "- Experiencia NEON: insignias de procedencia (REAL / CALCULADO / SIN DATOS / NO CONFIRMADO) en LANZAMIENTOS y DIRECTOR IA.", "",
         "## Objetivos de desarrollo (estado real)", "", "| Clave | Estado | Intentos | Resultado |", "|---|---|---|---|"]
    for o in dev: L.append("| %s | %s | %s | %s |" % (o["clave"], o["estado"], o["intentos"], (o.get("nota") or "—").replace("|", "/")[:90]))
    L += ["", "## Pruebas (qué se probó)", ""]
    if p.get("resultados"):
        L += ["| Suite | Clase | Estado | Resultado |", "|---|---|---|---|"] + ["| %s | %s | %s | %s |" % (r["suite"], r["clase"], r["estado"], r["resultado"].replace("|", "/")) for r in p["resultados"]]
        L += ["", "Resumen: %s pasan · %s intermitentes · %s fallan · %s total. **MOCK = proveedores simulados, no integraciones reales.**" % (p["pasan"], p["intermitentes"], p["fallan"], p["total"])]
    else: L.append("Sin resultados de batería registrados.")
    L += ["", "## Auditoría", ""]
    if au: L += ["- Fecha: %s · Resultado: **%s**" % (au["t"], "OK" if au["ok"] else "CON FALLOS"), "- Detalle: `%s`" % json.dumps(au["detalle"], ensure_ascii=False)]
    else: L.append("- Auditoría PENDIENTE de ejecutar.")
    L += ["", "## Qué NO está verificado", "", "- **Windows**: el lanzador y los `.bat` solo se probaron en Linux; no se declara verificado.",
          "- **Conexiones externas**: solo Keepa `/token` y `/search` (ES) tienen llamada real (2026-11-17). Sin verificar: Keepa `/product`, DE/FR/IT/UK, OpenAI, SP-API, Ads API.",
          "- Comparabilidad de competidores: automática, no confirmada por una persona. Los precios pueden ser antiguos (se muestra su fecha).",
          "- Navegador: probado con Chromium (Playwright) en Linux; no en otros navegadores ni en Windows.", "",
          "## Límites respetados", "", "- Gasto 0 € · 0 tokens Keepa adicionales · 0 llamadas a OpenAI · sin publicación en Amazon · sin despliegue · sin credenciales en el repositorio.", "",
          "## Conexiones", ""] + ["- %s: %s (%s)" % (c["nombre"], c["estado"], "real" if c["real"] else "no real") for c in e["conexiones"]]
    L += ["", "## Cómo continuar", "", "Ver `OPERACION_AUTONOMA.md` y `PLAN_FASE_SIGUIENTE.md`. Decisiones del propietario pendientes: costes logísticos, evidencias regulatorias, comparabilidad, autorización de gasto Keepa/IA."]
    txt = "\n".join(L) + "\n"; destino = destino or os.path.join(C.ROOT, "INFORME_V070.md"); open(destino, "w", encoding="utf-8").write(txt); return destino


if __name__ == "__main__": print(generar())
