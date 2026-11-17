param([string]$Carpeta)
$ErrorActionPreference = "Stop"
$Carpeta = (Resolve-Path $Carpeta).Path
$icono = Join-Path $Carpeta "assets\aht_amazon_pro.ico"
$destino = Join-Path $Carpeta "INICIAR.bat"
if (-not (Test-Path $destino)) { throw "No se encuentra INICIAR.bat en $Carpeta" }
$escritorio = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $escritorio "AHT Amazon Pro Intelligence.lnk"
$sh = New-Object -ComObject WScript.Shell
$a = $sh.CreateShortcut($lnk)
$a.TargetPath = $destino
$a.WorkingDirectory = $Carpeta
$a.IconLocation = $icono
$a.Description = "AHT Amazon Pro Intelligence (local, solo este ordenador)"
$a.WindowStyle = 7
$a.Save()
Write-Host " Acceso directo creado: $lnk"
