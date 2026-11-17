"""V1.0 · V1-10 — Ficha única de integraciones bloqueadas: qué credencial, qué permiso y qué acción debe autorizar el propietario. NUNCA contiene ni pide secretos por chat."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHA = [  # integración, estado hoy, credencial (dónde se guarda, sin valor), permiso/alcance mínimo, acción del propietario, coste, cómo se verificará
 ("Keepa /product y DE/FR/IT/UK", "BLOQUEADA (sin clave; solo ES /search verificado)", "keepa.env local: AMAZON_PRO_KEEPA_KEY (fichero en tu PC, fuera de GitHub/Drive)", "Solo lectura; tope por consulta", "Entregar la clave en keepa.env y autorizar un tope de tokens", "Tokens Keepa (tú decides el tope)", "/token (gratis) y 1 consulta acotada"),
 ("OpenAI (IA generativa)", "BLOQUEADA (API de pago no autorizada)", "ai.env local: OPENAI_API_KEY", "Modelo y tope mensual en € fijados en la política N3", "Autorizar gasto máximo mensual y crear la clave", "€ por uso (tope que fijes)", "1 llamada mínima con tope y registro en ModelGate"),
 ("Amazon SP-API (pedidos, inventario, catálogo)", "ADAPTADOR SOLO LECTURA IMPLEMENTADO (probado solo con simulación local) · NO CONECTADO", "sp_api.env local: client id, client secret, refresh token (no se piden por chat)", "Solo lectura (pedidos, inventario, informes)", "Registrar la app en Seller Central y autorizarla en solo lectura", "0 € (API gratuita)", "Llamada de solo lectura a un endpoint de sandbox/producción sin escritura"),
 ("Amazon Ads API", "ADAPTADOR SOLO LECTURA IMPLEMENTADO (probado solo con simulación local) · NO CONECTADO", "ads.env local: client id, client secret, refresh token", "Solo lectura de informes; sin crear ni modificar campañas", "Solicitar acceso a la Ads API y autorizar el perfil", "0 € (API gratuita; el gasto publicitario no se toca)", "Listar perfiles (solo lectura)"),
 ("Windows (ejecución del servidor y la UI)", "NO VERIFICADO (la sesión es Linux)", "—", "—", "Ejecutar python server.py en tu PC y lanzar tests/run_all.sh equivalente; enviar el resultado", "0 €", "Salida de las pruebas en tu Windows"),
 ("Costes, precio objetivo y ventas reales", "SIN DATOS", "—", "—", "Sergio/José: aportar costes y precio objetivo por producto (ficha del producto)", "0 €", "Motor económico pasa de NO CALCULABLE a CALCULADO"),
 ("Evidencia regulatoria cosmética ACTIVCORE", "SIN EVIDENCIA", "—", "—", "Laboratorios Klein / responsable: informe de seguridad, PIF, notificación CPNP", "según proveedor", "Registro de claims pasa de PENDIENTE_EVIDENCIA"),
 ("Imagen Docker construida y despliegue cloud persistente (Render Starter + disco 1 GB)", "PREPARADO, NO DESPLEGADO (7,25 USD/mes; no existe opción gratuita con disco persistente)", "Secretos en el panel de Render: AMAZON_PRO_ADMIN_PASSWORD y AMAZON_PRO_PASSWORD_SERGIO (los escribes tú, no por chat)", "Conectar GitHub (solo lectura del repositorio) y crear el servicio con el Blueprint", "Autorizar el gasto de 7,25 USD/mes, crear la cuenta de Render con tarjeta y aplicar el Blueprint", "7 USD/mes + 0,25 USD/mes de disco", "Abrir la URL HTTPS, entrar con tu usuario y pasar las pruebas funcionales contra el despliegue"),
 ("Protección de la rama en GitHub", "NO PUDE CONFIGURARLA (el proxy no permite escribir en esa API)", "—", "Settings → Branches (admin del repositorio)", "Activar protección para aht-v100-desarrollo: sin force-push ni borrado", "0 €", "—"),
]
def generar():
    o = ["# Ficha única de integraciones bloqueadas — V1.0", "", "No se pide ningún secreto por chat: las credenciales se guardan en ficheros locales del PC del propietario, nunca en GitHub ni Drive. Esta ficha agrupa TODO lo que requiere tu autorización.", ""]
    for n, e, cr, pe, ac, co, ve in FICHA:
        o += ["## " + n, "", "- **Estado hoy:** " + e, "- **Credencial (dónde, sin valor):** " + cr, "- **Permiso mínimo:** " + pe, "- **Acción que debes autorizar:** " + ac, "- **Coste:** " + co, "- **Cómo se verificará:** " + ve, ""]
    return "\n".join(o)
if __name__ == "__main__":
    open(os.path.join(ROOT, "FICHA_INTEGRACIONES_V100.md"), "w", encoding="utf-8").write(generar()); print("OK", len(FICHA))
