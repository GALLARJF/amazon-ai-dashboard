# Demostración del Director IA (V0.3)

> **Ninguna de estas ejecuciones es IA real.** Faltan clave y proveedor en este entorno: las ejecuciones reales están **pendientes**. Datos: expediente ficticio «Magnesio PRUEBA».

## 1 sin ia
- Estado del proveedor: SIN IA CONFIGURADA
- Modo del resultado: **SIN_IA** (motivo: SIN IA CONFIGURADA)
- Decisión determinista: GO
- No se registra ejecución de IA (no hubo llamada).

```
SIN IA · Resumen determinista. Decisión: GO. Sin bloqueos. GO no publica nada: la publicación sigue requiriendo aprobación explícita.
· Mercado y competencia: ok
· SEO y keywords: ok
· Precios y rentabilidad: ok
· Creatividad, imágenes y vídeos: ok
· Reputación y cumplimiento: ok — Aportar valoración propia y de competidores para comparar reputación (no se estima).
```

## 2 proveedor simulado mock
- Estado del proveedor: PROVEEDOR SIMULADO (no es IA real)
- Modo del resultado: **SIMULADA**
- Decisión determinista: GO
- Modelo: mock-determinista · modo registrado: SIMULADA · duración 0 ms
- Tokens: 936 entrada / 376 salida (estimado)
- Coste estimado: 0.008448 USD (precios de ejemplo 3/15 por millón de tokens, NO verificados)
- Anclaje de cifras: OK
- Limitaciones: La síntesis redacta solo hechos de los coworkers; no aporta datos externos. | El anclaje de cifras es heurístico: no demuestra veracidad. | EJECUCIÓN SIMULADA: no es IA real. | Tokens estimados (chars/4), no reportados por proveedor.

```
RESPUESTA SIMULADA (proveedor mock, no es IA real). Resumen extractivo de los hechos verificados:
- Decisión determinista del expediente: GO (0 causas NO-GO, 0 bloqueos, 4 avisos). [F1]
- [Mercado y competencia] 4 competidores válidos de 4 cargados (fuente+fecha ≤ 30 d, sin duplicados ni atípicos). [F2]
- [Mercado y competencia] Precio normalizado por cápsulas (envío incluido): mediana 0.1871 €, P25 0.1698 €, P75 0.2035 €. Banda para tu formato (120 cápsulas): 20.38–24.43 € (mediana 22.45 €). [F3]
- [Mercado y competencia] Tu PVP planificado 19.90 € es más caro que 1 de 4 competidores válidos (a igual formato). [F4]
- [Mercado y competencia] Referencia de reseñas (dato aportado): máx. 800 va
```

## 3 proveedor local de pruebas (camino HTTP real del adaptador)
- Estado del proveedor: IA CONFIGURADA · sin ejecución real verificada aún
- Modo del resultado: **PRUEBA_LOCAL**
- Decisión determinista: GO
- Modelo: proveedor-local-de-pruebas · modo registrado: PRUEBA_LOCAL · duración 158 ms
- Tokens: 1500 entrada / 60 salida (reportado_por_proveedor)
- Coste estimado: 0.0054 USD (precios de ejemplo 3/15 por millón de tokens, NO verificados)
- Anclaje de cifras: OK
- Limitaciones: La síntesis redacta solo hechos de los coworkers; no aporta datos externos. | El anclaje de cifras es heurístico: no demuestra veracidad. | Ejecución contra servidor local de pruebas: no cuenta como ejecución real de proveedor.

```
Síntesis de prueba: la decisión determinista es la indicada en [F1]; revisar los bloqueos listados.
```

## 4 anthropic sin clave (estado real de este entorno)
- Estado del proveedor: IA SIN CLAVE (ANTHROPIC_API_KEY ausente) · ejecuciones reales PENDIENTES
- Modo del resultado: **SIN_IA** (motivo: IA SIN CLAVE (ANTHROPIC_API_KEY ausente) · ejecuciones reales PENDIENTES)
- Decisión determinista: GO
- No se registra ejecución de IA (no hubo llamada).

```
SIN IA · Resumen determinista. Decisión: GO. Sin bloqueos. GO no publica nada: la publicación sigue requiriendo aprobación explícita.
· Mercado y competencia: ok
· SEO y keywords: ok
· Precios y rentabilidad: ok
· Creatividad, imágenes y vídeos: ok
· Reputación y cumplimiento: ok — Aportar valoración propia y de competidores para comparar reputación (no se estima).
```
