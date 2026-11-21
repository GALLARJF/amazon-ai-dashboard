"""V1.0 (V1-13) — Adaptadores de SOLO LECTURA para Amazon SP-API y Amazon Ads API.
Garantías: credenciales solo desde variables de entorno / ficheros .env locales (nunca en código ni respuestas); 0 € de gasto; solo GET (+ POST únicamente al endpoint de token LWA);
lista blanca de rutas; modo REAL exige credenciales completas Y la variable AMAZON_PRO_LIVE_<SERVICIO>=1; el modo SIMULADO solo habla con 127.0.0.1 y marca origen='SIMULADO' en cada respuesta.
Un servicio NUNCA se declara operativo: como máximo 'CONFIGURADO · SIN VERIFICAR' hasta que una persona registre una verificación real."""
import json, re, urllib.error, urllib.parse, urllib.request

class ConectorError(Exception): pass

SERVICIOS = {
    "spapi": {"nombre": "Amazon SP-API", "vars": ["AMAZON_PRO_SPAPI_CLIENT_ID", "AMAZON_PRO_SPAPI_CLIENT_SECRET", "AMAZON_PRO_SPAPI_REFRESH_TOKEN"], "hosts": {"sellingpartnerapi-eu.amazon.com"},
              "token_url": "https://api.amazon.com/auth/o2/token", "rutas": [r"^/orders/v0/orders$", r"^/fba/inventory/v1/summaries$", r"^/catalog/2022-04-01/items(/[A-Z0-9]{10})?$", r"^/reports/2021-06-30/reports(/[A-Za-z0-9\-]+)?$", r"^/finances/v0/financialEventGroups$", r"^/finances/v0/financialEvents$", r"^/finances/2024-06-19/transactions$"], "live": "AMAZON_PRO_LIVE_SPAPI"},
    "ads": {"nombre": "Amazon Ads API", "vars": ["AMAZON_PRO_ADS_CLIENT_ID", "AMAZON_PRO_ADS_CLIENT_SECRET", "AMAZON_PRO_ADS_REFRESH_TOKEN"], "hosts": {"advertising-api-eu.amazon.com"},
            "token_url": "https://api.amazon.com/auth/o2/token", "rutas": [r"^/v2/profiles$", r"^/v2/sp/campaigns$", r"^/v2/sp/adGroups$", r"^/v2/sp/keywords$", r"^/reporting/reports/[A-Za-z0-9\-]+$"], "live": "AMAZON_PRO_LIVE_ADS"},
}
LOOP = {"127.0.0.1", "localhost"}

class Conector:
    def __init__(self, svc, environ=None):
        if svc not in SERVICIOS: raise ConectorError("servicio desconocido")
        self.svc, self.d = svc, SERVICIOS[svc]; self.env = environ if environ is not None else {}
    def faltan(self): return [v for v in self.d["vars"] if not str(self.env.get(v, "")).strip()]
    def estado(self):
        f = self.faltan()
        if f: return {"servicio": self.d["nombre"], "estado": "NO CONECTADO", "faltan": f, "operativo": False, "nota": "Sin credenciales. Se guardan en un fichero .env local, nunca en GitHub, Drive ni chat."}
        live = str(self.env.get(self.d["live"], "")) == "1"
        return {"servicio": self.d["nombre"], "estado": "CONFIGURADO · SIN VERIFICAR" + ("" if live else " · LECTURA REAL DESACTIVADA"), "faltan": [], "operativo": False, "nota": "Solo una prueba real registrada por una persona permite llamarlo operativo."}
    def _ruta_ok(self, path):
        return any(re.match(p, path) for p in self.d["rutas"])
    def get(self, path, params=None, modo="SIMULADO", base_url=None, transport=None):
        if modo not in ("SIMULADO", "REAL"): raise ConectorError("modo inválido")
        u = urllib.parse.urlsplit(path)
        if u.scheme or u.netloc or ".." in path or not path.startswith("/"): raise ConectorError("ruta no permitida")
        if not self._ruta_ok(u.path): raise ConectorError("ruta fuera de la lista blanca de solo lectura")
        if modo == "REAL":
            if self.faltan(): raise ConectorError("modo REAL imposible: faltan credenciales")
            if str(self.env.get(self.d["live"], "")) != "1": raise ConectorError("lectura REAL desactivada (%s != 1)" % self.d["live"])
            host = sorted(self.d["hosts"])[0]; url = "https://%s%s" % (host, u.path)
        else:
            if not base_url: raise ConectorError("modo SIMULADO requiere un servidor local")
            bu = urllib.parse.urlsplit(base_url)
            if bu.hostname not in LOOP: raise ConectorError("el modo SIMULADO solo puede usar 127.0.0.1")
            url = base_url.rstrip("/") + u.path
        if params: url += "?" + urllib.parse.urlencode({str(k)[:40]: str(v)[:200] for k, v in list(params.items())[:10]})
        hdr = {"Accept": "application/json", "User-Agent": "AHT-AmazonPro/1.0 (solo lectura)"}
        try:
            body = (transport or self._http)(url, hdr)
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise ConectorError("fallo de transporte: %s" % type(e).__name__)
        return {"origen": modo, "servicio": self.d["nombre"], "solo_lectura": True, "coste_eur": 0.0, "datos": body, "aviso": "SIMULADO: no proviene de Amazon" if modo == "SIMULADO" else "Dato real de solo lectura, sin verificar por una persona"}
    @staticmethod
    def _http(url, hdr):
        rq = urllib.request.Request(url, headers=hdr, method="GET")
        with urllib.request.urlopen(rq, timeout=15) as r: return json.loads(r.read(2_000_000).decode("utf-8"))

def estados(environ=None):
    return [Conector(s, environ).estado() for s in SERVICIOS]
