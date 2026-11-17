# Seguridad: auditoría, autenticación y permisos (V0.2)

## 1. Estado de los controles
| Control | V0.1 | V0.2 | Verificación |
|---|---|---|---|
| Secretos fuera del navegador | Solo variables de entorno | Igual + respuestas sin secretos + errores con códigos fijos | `tests/security_test.py` (secretos falsos; ninguno aparece en respuestas ni en el JS) |
| Conectores | Activos si había variables de entorno | **Deshabilitados por defecto**; requieren `AMAZON_PRO_CONNECTORS` explícito | test |
| Prueba de conector | `GET` sin autenticación (efecto lateral, CSRF) | `POST` + `X-Admin-Token` + `application/json` + Origin/Host locales + 15 s de enfriamiento + 6/min | test |
| Servidor de archivos | Servía todo el directorio (incl. `server.py`, tests, informes) | Lista blanca: `index.html`, `styles.css`, `js/*.js` | test con rutas de traversal |
| Cabeceras | Ninguna | CSP estricta, nosniff, X-Frame-Options, no-referrer, no-store | test |
| Salida a Internet | Libre desde el servidor | `guarded_request()`: lista blanca de 4 operaciones de lectura (+ intercambio de token LWA) | test: PUT/DELETE/POST de escritura bloqueados |
| Acciones comerciales de escritura | No existían | No existen (ni código ni endpoints) | test de código + diseño |
| Escucha de red | 127.0.0.1 | 127.0.0.1 (verificado) | test |

## 2. Amenazas consideradas
| Amenaza | Mitigación en V0.2 | Pendiente |
|---|---|---|
| Página web externa que llama al servidor local (CSRF) | Sin efectos por GET; POST exige token, JSON y Origin local | — |
| DNS rebinding | Se valida la cabecera `Host` | — |
| Fuga de secretos por logs/errores | Sin logs de petición; errores con códigos fijos; los secretos nunca se serializan | La clave de Keepa viaja en la URL por diseño de su API: nunca se registra |
| Exposición de código/datos | Lista blanca de estáticos | — |
| Manipulación de aprobaciones en `localStorage` | Solo son registros, no ejecutan nada | Almacén servidor con firma/auditoría |
| Ejecución de cambios comerciales | No hay conector de escritura | Diseño aparte (ver §4) |
| XSS | Contenido escapado; CSP `script-src 'self'`, sin scripts en línea | Revisión externa |

## 3. Diseño de autenticación (NO implementado; requisito antes de uso multiusuario)
- **Identidad**: SSO con el proveedor de Executive Neon (OIDC). La app no almacena contraseñas. Sesión por cookie `HttpOnly; Secure; SameSite=Strict`, caducidad corta y renovación.
- **Autorización**: comprobada en el **servidor** en cada endpoint (nunca solo en la interfaz).
- **Secretos**: gestor de secretos (no ficheros ni `.env` en repositorio); rotación; credenciales con privilegios mínimos y **solo lectura**.
- **Auditoría**: registro inmutable de quién consultó, exportó, aprobó o probó una conexión (usuario, hora, recurso, resultado).

### Matriz de permisos
| Acción | Lector | Analista | Aprobador | Administrador |
|---|:-:|:-:|:-:|:-:|
| Ver panel, alertas, Director | ✔ | ✔ | ✔ | ✔ |
| Importar CSV / crear expedientes | — | ✔ | ✔ | ✔ |
| Exportar paquete de integración | — | ✔ | ✔ | ✔ |
| Proponer cambios (cola de aprobación) | — | ✔ | ✔ | ✔ |
| **Aprobar** o rechazar propuestas | — | — | ✔ | — |
| Habilitar/probar conectores, gestionar secretos | — | — | — | ✔ |
| Ejecutar cambios en Amazon | — | — | — | **No existe** |

Reglas: quien propone no puede aprobar su propia propuesta (separación de funciones); aprobar exige doble confirmación y queda auditado.

## 4. Condiciones para cualquier conector de escritura futuro (fuera del alcance de V0.2)
Aprobación humana explícita por acción · límites de cambio (p. ej. máximo ±X % de precio) · modo simulación previo · registro de auditoría · reversión documentada · credenciales de escritura separadas de las de lectura · kill switch.
