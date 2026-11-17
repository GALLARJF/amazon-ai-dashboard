# Guía de actualización segura (V0.3.4 → V0.4.0)
- Cada versión vive en su carpeta con su propio `data\`. V0.3.4 no se toca.
- Para conservar usuarios, expedientes y auditoría: cerrar ambas apps → copiar `V0.3.4\data\amazon_pro.db` a `V0.4.0\data\`. V0.4.0 añade tablas nuevas (caché y registro de Keepa) y la cuenta «ACTIVCORE · Inteligencia europea» sin modificar las existentes.
- Claves: `%USERPROFILE%\AmazonPro\ai.env` (OpenAI) y `keepa.env` (Keepa) están fuera de las carpetas y se reutilizan; nunca van en Git ni en el ZIP.
- Si pierdes la contraseña de admin: `RESTABLECER_ADMIN.bat` (conserva datos y claves).
- Volver atrás: abre de nuevo la carpeta V0.3.4 (su base de datos no ha cambiado; copia de seguridad recomendada antes de copiar `amazon_pro.db`).
