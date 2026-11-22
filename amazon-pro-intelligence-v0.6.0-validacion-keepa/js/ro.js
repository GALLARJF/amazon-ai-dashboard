/* P0 · Fase 2 — refuerzo VISUAL del rol viewer (solo lectura). El servidor ya responde 403 a toda escritura (no cambia);
   aquí los controles de escritura que la interfaz aún mostraba activos (subida de archivos, etiquetas «Importar», acciones con otros verbos)
   aparecen desactivados y con el texto «No disponible: solo lectura». Solo presentación. */
(function (root) {
  'use strict';
  const W = /(^\s*\+|vaciar|ejemplo|dossier|coworker|chat|guardar|crear|nuevo|nueva|aprobar|rechazar|lanzar|ejecutar|analizar|importar|publicar|activar|archivar|añadir|editar|enviar|proponer|investigar|reanudar|probar|confirmar|eliminar|borrar|registrar|validar|generar|iniciar|aplicar|actualizar|solicitar|reconciliar|fijar|cancelar|descartar|marcar|verificar|subir|cargar|restaurar|respaldo|preguntar|consultar al|medir|calcular|refrescar|cambiar contraseña|restablecer|desactivar|reanudar|pausar|detener|programar|asignar|sincronizar|exportar a)/i;
  const KEEP = '#lgOut,#lgOpen,#lgForm *,.ro-ok,[data-tab],#nav6 *,#bnav *,#subnav6 *,[data-k4v],[data-h2f],[data-h2go],[data-h2prod],[data-x4go],[data-x4open],a.btn,#dmode';
  // Campos de VISUALIZACIÓN que un viewer sí puede usar (no alteran datos): cuenta, modo, filtros y selectores de producto/expediente.
  const FIELD_OK = '#lgForm *,#acSel,#dmode,#dirDossier,#fMkt,#fPeriod,#fProduct,#k4fc,#k4fd,#k4fk,#k4fp,#k4io,#k4it,#k4par,#v6Prod-ventas,#v6Prod-lanz,[data-view-filter]';
  const MSG = () => (document.body.classList.contains('staging') && !(root.V03 && root.V03.V && root.V03.V.viewer) ? 'Solo lectura — staging' : 'Solo lectura — viewer');
  function lockField(el) {
    const m = MSG(); if (el.dataset.vroField === m) return; el.dataset.vroField = m;
    el.setAttribute('aria-disabled', 'true'); el.title = m; el.classList.add('vro', 'vro-field');
    if (el.tagName === 'SELECT' || el.type === 'checkbox' || el.type === 'radio' || el.type === 'file' || el.type === 'range') el.disabled = true; else { el.readOnly = true; el.disabled = true; }
    const host = el.closest('.card,article,section,fieldset,form,.plgrp,details,div'); if (host) { let n = host.querySelector(':scope > .ro-badge'); if (!n) { n = document.createElement('small'); n.className = 'ro-badge'; n.setAttribute('role', 'note'); host.insertBefore(n, host.firstChild); } n.textContent = m; }
  }
  function lock(el) { if (el.disabled && el.classList.contains('vro')) return; el.disabled = true; el.setAttribute('aria-disabled', 'true'); el.title = (document.body.classList.contains('staging') ? 'No disponible: staging de solo lectura' : 'No disponible: solo lectura (viewer)'); el.classList.add('vro'); }
  function apply() {
    const V = root.V03 && root.V03.V, stg = document.body.classList.contains('staging'); if (!stg && (!V || !V.viewer)) return;   // staging: solo lectura para TODOS los roles
    document.querySelectorAll('input:not([type=hidden]):not([type=button]):not([type=submit]), select, textarea').forEach((el) => { if (!el.matches(FIELD_OK)) lockField(el); });
    document.querySelectorAll('input[type=file]').forEach(lock);
    document.querySelectorAll('label.btn[for], label[for]').forEach((l) => { const t = document.getElementById(l.getAttribute('for')); if (t && t.type === 'file') { l.classList.add('vro'); l.setAttribute('aria-disabled', 'true'); l.title = (document.body.classList.contains('staging') ? 'No disponible: staging de solo lectura' : 'No disponible: solo lectura (viewer)'); } });
    document.querySelectorAll('#chips button, #chatIn, form input:not([type]), form input[type=text], textarea').forEach((el) => { if (!el.closest('#lgForm')) lock(el); });
    document.querySelectorAll('button:disabled').forEach((el) => { if (!el.classList.contains('vro') && !el.matches(KEEP) && W.test(el.textContent || '')) { el.classList.add('vro'); el.title = (document.body.classList.contains('staging') ? 'No disponible: staging de solo lectura' : 'No disponible: solo lectura (viewer)'); } });
    document.querySelectorAll('button, input[type=submit], input[type=button]').forEach((el) => { if (el.matches(KEEP) || el.disabled) return; if (W.test(el.textContent || el.value || '') || el.hasAttribute('data-act') && !/^(demo-on|demo-off|goto-lanz|open-chat|cancel)$/.test(el.dataset.act)) lock(el); });
  }
  let t; new MutationObserver(() => { clearTimeout(t); t = setTimeout(apply, 40); }).observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener('DOMContentLoaded', () => { setInterval(apply, 800); });
})(self);
