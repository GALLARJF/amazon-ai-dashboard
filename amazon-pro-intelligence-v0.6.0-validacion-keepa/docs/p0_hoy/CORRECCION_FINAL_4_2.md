# Corrección final 4.2 — viewer realmente solo lectura en la interfaz
Base: `226cc7b`. Sin cambios de API, cálculos, datos, usuarios, secretos ni conectores.

**Causa:** `js/ro.js` bloqueaba campos por lista negra (chat, CSV, `form input`, `textarea`); los ~58 `input/select` de Pre-Launch (`#plLeft`) y otras calculadoras quedaban habilitados.
**Arreglo:** lista BLANCA de campos de visualización permitidos (`#lgForm`, `#acSel`, `#dmode`, `#dirDossier`, `#fMkt/#fPeriod/#fProduct`, `#k4f*`, `#k4io/#k4it/#k4par`, `#v6Prod-*`); todo otro `input/select/textarea/file` queda `disabled` (+`readonly`), `aria-disabled="true"`, `title`/aviso «Solo lectura — viewer» (en staging para otros roles: «Solo lectura — staging»), estilo punteado/atenuado.

## Archivos
- `js/ro.js`, `styles.css` (bloqueo + `.vro-field`, `.ro-badge`)
- `tests/ui_viewer_ro_total_test.py` (nuevo, 52 comprobaciones), `tests/run_all.sh`, `tools/coordinador.py`
- `docs/p0_hoy/final_4_2/` (capturas Pre-Launch viewer: 1440, 390, 360, Pixel 7)

## Resultados
- Test nuevo: **52/52 OK** — viewer en 15 pantallas × 1440/390/360/Pixel 7: 0 campos habilitados, 0 botones de escritura activos; Pre-Launch 58 campos, exactamente 0 editables; 13 pestañas `?legacy=1` igual; navegación, filtros, acordeón, selector de cuenta/modo y logout operativos; admin (servidor no staging) 58/58 campos operativos y edita; viewer POST/PUT/PATCH/DELETE → 403 (7/7) en staging y no staging.
- Regresión completa `tests/run_all.sh`: todas OK salvo 2 heredadas idénticas en la base: `security_test` 49/53 (4 Keepa) y `v040` 43/45. Sin fallos nuevos.
