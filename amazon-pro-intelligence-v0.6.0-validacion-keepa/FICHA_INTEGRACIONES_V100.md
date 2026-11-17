# Ficha única de integraciones bloqueadas — V1.0

No se pide ningún secreto por chat: las credenciales se guardan en ficheros locales del PC del propietario, nunca en GitHub ni Drive. Esta ficha agrupa TODO lo que requiere tu autorización.

## Keepa /product y DE/FR/IT/UK

- **Estado hoy:** BLOQUEADA (sin clave; solo ES /search verificado)
- **Credencial (dónde, sin valor):** keepa.env local: AMAZON_PRO_KEEPA_KEY (fichero en tu PC, fuera de GitHub/Drive)
- **Permiso mínimo:** Solo lectura; tope por consulta
- **Acción que debes autorizar:** Entregar la clave en keepa.env y autorizar un tope de tokens
- **Coste:** Tokens Keepa (tú decides el tope)
- **Cómo se verificará:** /token (gratis) y 1 consulta acotada

## OpenAI (IA generativa)

- **Estado hoy:** BLOQUEADA (API de pago no autorizada)
- **Credencial (dónde, sin valor):** ai.env local: OPENAI_API_KEY
- **Permiso mínimo:** Modelo y tope mensual en € fijados en la política N3
- **Acción que debes autorizar:** Autorizar gasto máximo mensual y crear la clave
- **Coste:** € por uso (tope que fijes)
- **Cómo se verificará:** 1 llamada mínima con tope y registro en ModelGate

## Amazon SP-API (pedidos, inventario, catálogo)

- **Estado hoy:** SIN ADAPTADOR TODAVÍA (objetivo V1-13) · NO CONECTADO
- **Credencial (dónde, sin valor):** sp_api.env local: client id, client secret, refresh token (no se piden por chat)
- **Permiso mínimo:** Solo lectura (pedidos, inventario, informes)
- **Acción que debes autorizar:** Registrar la app en Seller Central y autorizarla en solo lectura
- **Coste:** 0 € (API gratuita)
- **Cómo se verificará:** Llamada de solo lectura a un endpoint de sandbox/producción sin escritura

## Amazon Ads API

- **Estado hoy:** SIN ADAPTADOR TODAVÍA (objetivo V1-13) · NO CONECTADO
- **Credencial (dónde, sin valor):** ads.env local: client id, client secret, refresh token
- **Permiso mínimo:** Solo lectura de informes; sin crear ni modificar campañas
- **Acción que debes autorizar:** Solicitar acceso a la Ads API y autorizar el perfil
- **Coste:** 0 € (API gratuita; el gasto publicitario no se toca)
- **Cómo se verificará:** Listar perfiles (solo lectura)

## Windows (ejecución del servidor y la UI)

- **Estado hoy:** NO VERIFICADO (la sesión es Linux)
- **Credencial (dónde, sin valor):** —
- **Permiso mínimo:** —
- **Acción que debes autorizar:** Ejecutar python server.py en tu PC y lanzar tests/run_all.sh equivalente; enviar el resultado
- **Coste:** 0 €
- **Cómo se verificará:** Salida de las pruebas en tu Windows

## Costes, precio objetivo y ventas reales

- **Estado hoy:** SIN DATOS
- **Credencial (dónde, sin valor):** —
- **Permiso mínimo:** —
- **Acción que debes autorizar:** Sergio/José: aportar costes y precio objetivo por producto (ficha del producto)
- **Coste:** 0 €
- **Cómo se verificará:** Motor económico pasa de NO CALCULABLE a CALCULADO

## Evidencia regulatoria cosmética ACTIVCORE

- **Estado hoy:** SIN EVIDENCIA
- **Credencial (dónde, sin valor):** —
- **Permiso mínimo:** —
- **Acción que debes autorizar:** Laboratorios Klein / responsable: informe de seguridad, PIF, notificación CPNP
- **Coste:** según proveedor
- **Cómo se verificará:** Registro de claims pasa de PENDIENTE_EVIDENCIA

## Protección de la rama en GitHub

- **Estado hoy:** NO PUDE CONFIGURARLA (el proxy no permite escribir en esa API)
- **Credencial (dónde, sin valor):** —
- **Permiso mínimo:** Settings → Branches (admin del repositorio)
- **Acción que debes autorizar:** Activar protección para aht-v100-desarrollo: sin force-push ni borrado
- **Coste:** 0 €
- **Cómo se verificará:** —
