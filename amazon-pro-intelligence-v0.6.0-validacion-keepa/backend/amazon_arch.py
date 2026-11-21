"""Fase 4 · E — ARQUITECTURA de integración con Amazon (SP-API y Ads API). SOLO DECLARATIVA: no abre sockets, no lee credenciales, no llama a nadie.
Cada capacidad indica servicio, rutas de solo lectura (las que admite la lista blanca de backend/conectores100.py), cómo se obtiene HOY (informe importado) y su estado.
Todo está DESACTIVADO por defecto: activar exige credenciales en variables de entorno del servidor Y la variable AMAZON_PRO_LIVE_<SERVICIO>=1 Y una verificación humana.
Ninguna capacidad publica productos ni modifica precios, inventario o campañas (no existen rutas de escritura)."""
ESTADO = "ARQUITECTURA PREPARADA · DESACTIVADA · SIN LLAMADAS REALES"
CAPACIDADES = [
    {"id": "sp-catalogo", "servicio": "spapi", "nombre": "Catálogo", "rutas": ["/catalog/2022-04-01/items"], "alimenta": "ficha del producto (ASIN, atributos, imágenes)", "hoy": "ficha manual con fuente y fecha"},
    {"id": "sp-pedidos", "servicio": "spapi", "nombre": "Pedidos", "rutas": ["/orders/v0/orders"], "alimenta": "ventas y unidades reales", "hoy": "informe de ventas importado (CSV)"},
    {"id": "sp-inventario", "servicio": "spapi", "nombre": "Inventario FBA", "rutas": ["/fba/inventory/v1/summaries"], "alimenta": "stock disponible hoy", "hoy": "existencias históricas a revalidar"},
    {"id": "sp-informes", "servicio": "spapi", "nombre": "Informes", "rutas": ["/reports/2021-06-30/reports"], "alimenta": "informes de negocio, liquidaciones y tarifas", "hoy": "importación manual del informe"},
    {"id": "sp-tarifas", "servicio": "spapi", "nombre": "Tarifas", "rutas": ["/reports/2021-06-30/reports"], "alimenta": "tarifa FBA/FBM, almacenaje y devoluciones del margen", "hoy": "NO DETERMINABLE: la estimación de tarifas de la API es POST y queda fuera; se leen del informe de tarifas"},
    {"id": "sp-finanzas", "servicio": "spapi", "nombre": "Finanzas", "rutas": ["/finances/v0/financialEventGroups", "/finances/v0/financialEvents", "/finances/2024-06-19/transactions"], "alimenta": "liquidaciones y comisiones reales", "hoy": "SIN DATOS"},
    {"id": "ads-campanas", "servicio": "ads", "nombre": "Campañas", "rutas": ["/v2/profiles", "/v2/sp/campaigns", "/v2/sp/adGroups"], "alimenta": "estructura de publicidad (lectura)", "hoy": "SIN DATOS"},
    {"id": "ads-palabras", "servicio": "ads", "nombre": "Palabras clave", "rutas": ["/v2/sp/keywords"], "alimenta": "keywords activas (lectura)", "hoy": "SIN DATOS"},
    {"id": "ads-metricas", "servicio": "ads", "nombre": "Gasto, ventas atribuidas, ACoS y ROAS", "rutas": ["/reporting/reports/{id}"], "alimenta": "ACoS, ROAS y gasto por campaña", "hoy": "informe de publicidad importado (CSV); crear informes por API es POST y requiere una decisión aparte"},
]
VARIABLES_RENDER = {
    "spapi": {"estado_servidor": ["SPAPI_CLIENT_ID", "SPAPI_CLIENT_SECRET", "SPAPI_REFRESH_TOKEN"], "adaptador": ["AMAZON_PRO_SPAPI_CLIENT_ID", "AMAZON_PRO_SPAPI_CLIENT_SECRET", "AMAZON_PRO_SPAPI_REFRESH_TOKEN"], "interruptor": "AMAZON_PRO_LIVE_SPAPI"},
    "ads": {"estado_servidor": ["ADS_CLIENT_ID", "ADS_CLIENT_SECRET", "ADS_REFRESH_TOKEN"], "adaptador": ["AMAZON_PRO_ADS_CLIENT_ID", "AMAZON_PRO_ADS_CLIENT_SECRET", "AMAZON_PRO_ADS_REFRESH_TOKEN"], "interruptor": "AMAZON_PRO_LIVE_ADS"},
    "global": ["AMAZON_PRO_CONNECTORS (lista: sp-api,ads; vacía = ninguna llamada de red)"],
}
def manifiesto():
    from backend import conectores100 as C
    import re
    ok = lambda svc, r: any(re.match(p, r.replace("{id}", "abc-123")) for p in C.SERVICIOS[svc]["rutas"])
    return {"estado": ESTADO, "solo_lectura": True, "escritura": "NO IMPLEMENTADA", "capacidades": [dict(c, permitida=all(ok(c["servicio"], r) for r in c["rutas"]), estado="DESACTIVADA") for c in CAPACIDADES], "variables": VARIABLES_RENDER}
