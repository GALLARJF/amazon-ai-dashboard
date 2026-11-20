/* P0 · Fase 2 — refuerzo VISUAL del rol viewer (solo lectura). El servidor ya responde 403 a toda escritura (no cambia);
   aquí los controles de escritura que la interfaz aún mostraba activos (subida de archivos, etiquetas «Importar», acciones con otros verbos)
   aparecen desactivados y con el texto «No disponible: solo lectura». Solo presentación. */
(function (root) {
  'use strict';
  const W = /(guardar|crear|nuevo|nueva|aprobar|rechazar|lanzar|ejecutar|analizar|importar|publicar|activar|archivar|añadir|editar|enviar|proponer|investigar|reanudar|probar|confirmar|eliminar|borrar|registrar|validar|generar|iniciar|aplicar|actualizar|solicitar|reconciliar|fijar|cancelar|descartar|marcar|verificar|subir|cargar|restaurar|respaldo|preguntar|consultar al|medir|calcular|refrescar|cambiar contraseña|restablecer|desactivar|reanudar|pausar|detener|programar|asignar|sincronizar|exportar a)/i;
  const KEEP = '#lgOut,#lgOpen,#lgForm *,.ro-ok,[data-tab],#nav6 *,#bnav *,#subnav6 *,[data-k4v],[data-h2f],[data-h2go],[data-h2prod],a.btn,#dmode';
  function lock(el) { if (el.disabled && el.classList.contains('vro')) return; el.disabled = true; el.setAttribute('aria-disabled', 'true'); el.title = 'No disponible: solo lectura (viewer)'; el.classList.add('vro'); }
  function apply() {
    const V = root.V03 && root.V03.V; if (!V || !V.viewer) return;
    document.querySelectorAll('input[type=file]').forEach(lock);
    document.querySelectorAll('label.btn[for], label[for]').forEach((l) => { const t = document.getElementById(l.getAttribute('for')); if (t && t.type === 'file') { l.classList.add('vro'); l.setAttribute('aria-disabled', 'true'); l.title = 'No disponible: solo lectura (viewer)'; } });
    document.querySelectorAll('#chips button, #chatIn, form input:not([type]), form input[type=text], textarea').forEach((el) => { if (!el.closest('#lgForm')) lock(el); });
    document.querySelectorAll('button:disabled').forEach((el) => { if (!el.classList.contains('vro') && !el.matches(KEEP) && W.test(el.textContent || '')) { el.classList.add('vro'); el.title = 'No disponible: solo lectura (viewer)'; } });
    document.querySelectorAll('button, input[type=submit], input[type=button]').forEach((el) => { if (el.matches(KEEP) || el.disabled) return; if (W.test(el.textContent || el.value || '') || el.hasAttribute('data-act') && !/^(demo-on|demo-off|goto-lanz|open-chat|cancel)$/.test(el.dataset.act)) lock(el); });
  }
  let t; new MutationObserver(() => { clearTimeout(t); t = setTimeout(apply, 40); }).observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener('DOMContentLoaded', () => { setInterval(apply, 800); });
})(self);
