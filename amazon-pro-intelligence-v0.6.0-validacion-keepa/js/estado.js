/* Pestaña Estado (V0.2): matriz de conexiones, bloqueos antes de operar, coworkers, paquete de integración, controles de seguridad.
   Todo lo que se muestra se deriva de estados reales (servidor / datos cargados); nada se declara operativo sin prueba. */
(function (root) {
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let adminToken = ''; // solo en memoria; nunca se guarda
  const NEEDS = {
    'sp-api': 'Ventas, costes/tarifas, inventario, reputación', ads: 'Publicidad (ACoS/TACoS), keywords', keepa: 'Competencia y precios históricos', helium10: 'Demanda y keywords',
  };

  async function fetchStatus() { try { const r = await fetch('/api/status'); if (!r.ok) throw 0; return await r.json(); } catch (e) { return null; } }

  async function render() {
    const A = root.APP, S = A.S, st = await fetchStatus(), conns = st ? st.connectors : null;
    const rowsC = ['sp-api', 'ads', 'keepa', 'helium10'].map((id) => {
      const c = conns && conns.find((x) => x.id === id); const status = c ? c.status : 'SERVIDOR NO DISPONIBLE (sin conexión)';
      const cls = status.startsWith('CONECTADO') ? 't-ok' : status.startsWith('HABILITADO') ? 't-wait' : 't-no';
      return `<tr><td><b>${{ 'sp-api': 'Amazon SP-API', ads: 'Amazon Ads', keepa: 'Keepa', helium10: 'Helium 10' }[id]}</b></td><td>${NEEDS[id]}</td><td><span class="tagst ${cls}">${esc(status)}</span></td>
        <td>${c && c.enabled && c.missing.length ? 'Faltan: ' + esc(c.missing.join(', ')) : c && !c.enabled && id !== 'helium10' ? 'Deshabilitado: AMAZON_PRO_CONNECTORS' : '—'}${c && c.last_test ? '<br>Prueba ' + esc(c.last_test.at + ' · ' + c.last_test.detail) : ''}</td>
        <td>${c && c.testable ? `<button class="btn ghost sm" data-test="${id}">Probar (lectura)</button>` : '—'}</td></tr>`;
    }).join('') + `<tr><td><b>Importación CSV</b></td><td>Ventas/costes manuales</td><td><span class="tagst ${S.source === 'csv' ? 't-ok' : 't-wait'}">${S.source === 'csv' ? 'EN USO (sin verificar vía API)' : 'DISPONIBLE · no cargado'}</span></td><td>—</td><td>—</td></tr>
      <tr><td><b>Brand Analytics</b></td><td>Términos de búsqueda, cuota</td><td><span class="tagst t-no">NO IMPLEMENTADO</span></td><td>Sin conector en V0.2</td><td>—</td></tr>
      <tr><td><b>Executive Neon</b></td><td>Ventas › Canal Amazon, Marketing, Finanzas, Logística</td><td><span class="tagst t-wait">CONTRATO LISTO · NO ENLAZADO</span></td><td>Exporta paquete JSON; no escribe en la plataforma</td><td>—</td></tr>`;

    const anyVerified = conns && conns.some((c) => c.status.startsWith('CONECTADO'));
    const B = [
      [S.source === 'demo' ? 'ABIERTO' : 'PARCIAL', 'Datos de AHT verificados', S.source === 'demo' ? 'Todo el panel usa datos DEMO.' : 'CSV importado: aún sin conciliar contra SP-API/Seller Central.'],
      [anyVerified ? 'PARCIAL' : 'ABIERTO', 'Conexiones reales con prueba', 'Ningún conector habilitado y probado con credenciales reales.'],
      ['ABIERTO', 'Tarifas de comisión verificadas', 'Las tablas de comisión por categoría son orientativas (verified:false).'],
      ['ABIERTO', 'Tarifas FBA, almacenaje y devoluciones reales', 'Se introducen a mano; falta contraste con la calculadora/informes de Amazon.'],
      ['ABIERTO', 'Base del ACoS (con/sin IVA)', 'Verificar en informes de Amazon Ads qué base usan para ventas.'],
      ['PARCIAL', 'Autenticación y permisos multiusuario', 'V0.3: usuarios locales con roles analyst/approver/admin y sesión HttpOnly; falta SSO, MFA y política de contraseñas corporativa.'],
      ['PARCIAL', 'Persistencia y auditoría', 'V0.3: SQLite local con auditoría encadenada por hash (manipulable por quien controle el fichero: falta anclaje externo, cifrado y copias de seguridad).'],
      ['ABIERTO', 'Ejecución REAL del Director IA', 'Sin clave de proveedor: adaptador y pruebas con proveedor simulado/local; ninguna ejecución real verificada ni coste real medido.'],
      ['ABIERTO', 'Titular legal y cuenta Seller Central del piloto', 'La cuenta PhiVital figura «POR CONFIRMAR»: no se asume titularidad ni se mezclan contabilidades.'],
      ['ABIERTO', 'Revisión regulatoria por especialista', 'Las listas regulatorias y de claims son plantillas orientativas.'],
      ['ABIERTO', 'Conector de escritura (precios, campañas, publicaciones)', 'No existe por diseño; requiere diseño aparte con doble aprobación y auditoría.'],
      ['ABIERTO', 'Despliegue seguro', 'Hoy solo local (127.0.0.1); falta TLS, gestión de secretos y entorno definitivo.'],
      ['ABIERTO', 'Integración real con Executive Neon', 'Contrato y exportación listos; falta acordar esquema con la plataforma e importar con upsert.'],
    ];
    const NEED = { mercado: 'Keepa / importación CSV de competidores', precios: 'Costes documentados + tarifas vigentes de Amazon', seo: 'Helium 10 / Brand Analytics (exportación)', ppc: 'Amazon Ads (informes reales)', creatividad: 'Listing real (SP-API)', inventario: 'SP-API / FBA o stock propio', cumplimiento: 'Documentación regulatoria y reseñas' };
    const cwS = (root.V03 && root.V03.V.cw) ? root.V03.V.cw.coworkers : null;
    const cw = Object.keys(NEED).map((id) => `<tr><td>${cwS && cwS[id] ? esc(cwS[id].name) : id}</td><td>${NEED[id]}</td><td>${cwS && cwS[id] ? esc(cwS[id].label) + (cwS[id].runs ? ` (${cwS[id].runs} ejec.)` : '') : 'Inicia sesión para ver el estado real'}</td></tr>`).join('');
    const pkg = root.AmazonPro.exportPackage(), errs = root.Integration.validate(pkg);
    document.getElementById('estadoRoot').innerHTML = `
      <article class="card c-cyan wide"><h3>Matriz de conexiones <small>estado real; ninguno se declara operativo sin prueba</small></h3>
        <p class="muted">${st ? 'Conectores externos DESHABILITADOS por defecto. Se activan con la variable AMAZON_PRO_CONNECTORS en el servidor.' : 'No hay servidor local (abre la app con python server.py). Ninguna conexión está activa.'}</p>
        <table class="mt"><tr><th>Fuente</th><th>Alimenta</th><th>Estado real</th><th>Detalle</th><th></th></tr>${rowsC}</table>
        ${conns && conns.some((c) => c.testable) ? `<p style="margin-top:8px"><label class="fld" style="max-width:340px">Token de administrador (solo memoria, se muestra en la consola del servidor)<input id="admTok" type="password" autocomplete="off" value="${esc(adminToken)}"></label></p>` : ''}
        <p class="note" id="testMsg"></p></article>
      <article class="card c-amber"><h3>Bloqueos antes de operar con Amazon <small>${B.filter((b) => b[0] !== 'CERRADO').length} abiertos</small></h3>${B.map((b) => `<div class="blk"><span class="chip ${b[0] === 'PARCIAL' ? 'warn' : 'nogo'}">${b[0]}</span><span><b>${esc(b[1])}</b><br><span class="muted">${esc(b[2])}</span></span></div>`).join('')}</article>
      <article class="card c-lime"><h3>Integración con Executive Neon <small>paquete idempotente</small></h3>
        <p style="font-size:13px">Paquete <code>${esc(pkg.schema)}</code>: ${pkg.channel_snapshots.length} snapshots, ${pkg.alerts.length} alertas, ${pkg.dossiers.length} expedientes, ${pkg.approvals.length} aprobaciones.<br>
        Origen: <b>${esc(pkg.source.dataSource)}</b> · ingest_allowed: <b>${pkg.ingest_allowed}</b> · validación: <b class="${errs.length ? 'ko' : 'ok'}">${errs.length ? errs.length + ' errores' : 'OK'}</b></p>
        <p class="note">IDs deterministas: re-exportar no duplica (upsert por <code>key</code>). Un paquete DEMO no debe ingestarse. La app no escribe en la plataforma principal.</p>
        <p style="margin-top:6px"><button class="btn" id="dlPkg">Descargar paquete (JSON)</button></p></article>
      <article class="card c-violet"><h3>Coworkers <small>fuentes reales necesarias</small></h3><table class="mt"><tr><th>Coworker</th><th>Fuentes reales necesarias</th><th>Estado (deducido de ejecuciones registradas)</th></tr>${cw}</table>
        <p class="note">Deterministas (sin IA). «Operativo» solo con ejecución verificada sobre datos del usuario completos. La IA del Director no tiene ninguna ejecución real verificada todavía.</p></article>
      <article class="card c-cyan"><h3>Controles de seguridad <small>servidor local</small></h3><ul style="padding-left:18px;font-size:12.5px;line-height:1.5">
        <li>Escucha solo en 127.0.0.1; sirve únicamente index, estilos y js.</li><li>Sin secretos en el navegador: credenciales solo como variables de entorno del servidor.</li>
        <li>Prueba de conectores: POST + token de administrador + origen local + límite de frecuencia.</li><li>Salida a Internet solo por lista blanca de operaciones de lectura.</li>
        <li>Sin acciones comerciales de escritura: no existe código para ello.</li><li>V0.3: sesión HttpOnly + CSRF, roles, aislamiento por cuenta, clave de IA solo en el servidor, auditoría encadenada.</li></ul></article>`;
    const tok = document.getElementById('admTok'); if (tok) tok.oninput = () => (adminToken = tok.value);
    document.getElementById('dlPkg').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(root.AmazonPro.exportPackage(), null, 2)], { type: 'application/json' })); a.download = 'executive-neon_amazon-channel_' + (pkg.period.to || 'sin-fecha') + '.json'; a.click(); };
    document.querySelectorAll('[data-test]').forEach((b) => (b.onclick = async () => {
      b.disabled = true; const m = document.getElementById('testMsg');
      try { const r = await fetch('/api/connectors/test', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Admin-Token': adminToken }, body: JSON.stringify({ name: b.dataset.test }) }); const j = await r.json(); m.textContent = r.ok ? `${b.dataset.test}: ${j.ok ? 'OK' : 'FALLO'} (${j.detail})` : 'Rechazado: ' + (j.error || r.status); } catch (e) { m.textContent = 'Sin respuesta del servidor.'; }
      render();
    }));
  }
  root.EstadoUI = { render };
})(self);
