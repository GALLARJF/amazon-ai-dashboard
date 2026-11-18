# Cierre operativo K2 — Director IA competidores (ACTIVCORE)

Fecha: 2026-11-18 (Madrid)

## Integrado
- PR #2 fusionado en `aht-v100-desarrollo` con merge commit **6c792e9** (head del PR: ecfc4cf). Trazabilidad conservada (merge commit, sin force-push).
- Controles previos: PR mergeable/clean; la base (ce3ccd0, merge del PR #1) era ancestro del PR, no se pisó nada; sin sesion.lock en `aht-autonomia-estado`; tarea autónoma cada 4 h intacta.
- Cambios de K2 solo en backend (eu_director.py, ops.py) + tests/informes. Sin cambios de UI/JS.
- Añadido en el PR (req. 7): frescura por precio — ACTUAL ≤7 d / RECIENTE ≤30 d / HISTÓRICO >30 d / FECHA DESCONOCIDA; la posición de precio solo usa ACTUAL/RECIENTE; los históricos se listan «SOLO REFERENCIA» con advertencia.

## Pruebas (SIMULADAS/LOCALES, no contra Render)
- Coordinador QA: 36/36 PASA, 0 intermitentes, 0 fallos; auditoría ok:true.
- k2-director: 33 checks (5 intenciones, 20 ASIN con 0 tokens Keepa, candidatos vs confirmados, persistencia tras reinicio, modo cloud con proceso real, sin IA externa ni Keepa de pago).
- Corregida una carrera en tests/ui_v07_test.py (re-render del panel antes de medir en móvil); era fallo del test, no del producto.
- CI docker-build del merge: success.

## Render (REAL, comprobado desde fuera sin credenciales)
- https://amazon-pro-intelligence.onrender.com: /healthz 200 `{"ok": true}`, login 200, HSTS y CSP presentes, `/api/eu/director` sin sesión 401, Host ajeno 403. Estable durante ~5 min tras el merge.
- NO verificable: qué commit está desplegado. /healthz no expone versión, el cambio es solo backend y no tengo acceso al panel de Render. El autodeploy de Render es el valor por defecto, pero no está confirmado en el panel.

## Cinco intenciones y persistencia en el despliegue
- **NO verificadas en Render.** Requieren la contraseña admin (secreto del propietario, no se pide por chat) y no hay navegador disponible en esta sesión. Resultado solo en entorno local simulado: las 5 intenciones responden distinto y de forma determinista.

## Pendiente / errores
1. Verificación autenticada en Render (decisión de seguridad: sesión del propietario).
2. Confirmar en el panel de Render que el último deploy corresponde a 6c792e9.
3. Entre los ASIN relevantes hay 2 con precio HISTÓRICO: no se usan para competitividad actual.
4. El test de entrega v1.0 depende del último QA registrado (circular); pasa tras dos pasadas de `qa`.

## ¿K2 disponible para el usuario?
**No declarado.** Integrado y probado en local; falta comprobarlo en el entorno desplegado.

## Checklist para el propietario (2 min)
1. Panel Render → último deploy = 6c792e9 y estado Live.
2. Iniciar sesión → Director IA → pulsar los 5 chips (competidores, precio, país, datos faltantes, riesgos): deben dar respuestas distintas, competidores con marca/producto/ASIN/precio/comparabilidad/motivo y etiquetas CANDIDATO vs CONFIRMADO; precios históricos con advertencia.
3. Confirmar un competidor, forzar reinicio (Manual Deploy → Restart) y comprobar que sigue CONFIRMADO.

## Límites respetados
0 € extra, 0 tokens Keepa, sin APIs de pago ni IA externa, nada publicado en Amazon, sin secretos en chat/repo, sin force-push, SQLite/disco/usuarios intactos.
