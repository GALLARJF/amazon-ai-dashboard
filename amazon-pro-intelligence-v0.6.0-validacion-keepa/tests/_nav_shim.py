"""Fase 4 · F — adaptador de migración de las suites heredadas a la NAVEGACIÓN NUEVA (sin ?legacy=1).
Las suites antiguas actúan sobre las 13 pestañas (#tabs), que en la navegación nueva están ocultas y cuyo contenido original vive dentro de bloques plegados «Metodología».
Este módulo (solo pruebas, ninguna línea de la aplicación): 1) hace clic programático en #tabs (como hace nav.js); 2) espera #tabs en estado «attached»;
3) despliega los <details> de la presentación nueva para que la pantalla original sea localizable. No sustituye ninguna aserción."""
from playwright.sync_api import Page, BrowserContext
_click, _wait, _new_page, _sel = Page.click, Page.wait_for_selector, BrowserContext.new_page, Page.select_option
CSS = "body.shell6 .k4views,body.shell6 [data-act=\"demo-on\"],body.shell6 [data-act=\"demo-off\"],body.shell6 #badge,body.shell6 #v6inicio .v6demo,body.shell6 #v6inicio .filters{display:revert!important}body.shell6 #tabs{display:flex!important}"
OPEN = "(function(){const st=document.createElement('style');st.textContent='"+CSS.replace("'","\\'")+"';document.addEventListener('DOMContentLoaded',()=>document.head.appendChild(st));})();"+"(function(){const o=()=>document.querySelectorAll('details.h2det:not([open]),details.lzfold:not([open])').forEach(d=>{d.open=true});new MutationObserver(o).observe(document,{childList:true,subtree:true});setInterval(o,300);})();"
def click(self, selector, *a, **k):
    if isinstance(selector, str) and (selector.startswith("#tabs button") or selector.startswith("[data-tab=")): return self.locator(selector).first.evaluate("e=>e.click()")
    return _click(self, selector, *a, **k)
def select_option(self, selector, value=None, *a, **k):
    # el selector de producto heredado de Lanzamientos lo retira a propósito el aislamiento de la Fase 3: se fija el mismo estado que fija su manejador (V06.state.pid + render)
    if isinstance(selector, str) and selector.startswith("#v6Prod-lanz") and isinstance(value, str):
        return self.evaluate("v=>self.LANZ2?LANZ2.select(v):(V06.state.pid=v,V06.render())", value)
    return _sel(self, selector, value, *a, **k)
def wait_for_selector(self, selector, *a, **k):
    if selector == "#v6Prod-lanz": return None
    if selector == "#tabs" and "state" not in k: k["state"] = "attached"
    return _wait(self, selector, *a, **k)
def new_page(self, *a, **k):
    if not getattr(self, "_shim", False): self.add_init_script(OPEN); self._shim = True
    return _new_page(self, *a, **k)
Page.click, Page.wait_for_selector, BrowserContext.new_page, Page.select_option = click, wait_for_selector, new_page, select_option
