# =============================================================================
# VMotors · levanta el backend (FastAPI + SQLite) y lo publica con cloudflared
# =============================================================================
# Uso:
#   .\scripts\iniciar.ps1
#
# Deja todo en una sola terminal: crea el entorno virtual si falta, genera la
# base de datos de ejemplo si no existe, arranca el backend y abre un tunel
# publico de Cloudflare que apunta a el. La URL https://xxxxx.trycloudflare.com
# que imprime cloudflared es la que se comparte con el equipo. Cerrar esta
# ventana (o Ctrl+C) apaga el tunel y el backend.
# =============================================================================

param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Write-Paso($texto) { Write-Host $texto -ForegroundColor Cyan }
function Write-Aviso($texto) { Write-Host $texto -ForegroundColor Yellow }

Write-Paso "== VMotors :: preparando el entorno =="

# 1) Entorno virtual dedicado en la raiz del repo
$venvPath = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Aviso "Creando entorno virtual en .venv ..."
    python -m venv $venvPath
}
$venvPython = Join-Path $venvPath "Scripts\python.exe"

Write-Aviso "Instalando dependencias (backend + generador de datos)..."
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r (Join-Path $RepoRoot "backend\requirements.txt")
& $venvPython -m pip install --quiet Faker

# 2) Base de datos: se genera solo la primera vez
$dbPath = Join-Path $RepoRoot "database\vmotors.db"
if (-not (Test-Path $dbPath)) {
    Write-Aviso "No existe database\vmotors.db; generando datos de ejemplo con Faker..."
    Push-Location (Join-Path $RepoRoot "database")
    & $venvPython seed_sqlite.py --reset --yes
    Pop-Location
} else {
    Write-Host "Base de datos existente: $dbPath" -ForegroundColor DarkGray
}

# 3) Configuracion del backend (.env)
$envFile = Join-Path $RepoRoot "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $RepoRoot "backend\.env.example") $envFile
    Write-Aviso "Se creo backend\.env con credenciales por omision (administrador / vmotors2026)."
    Write-Aviso "Cambielas ahi antes de compartir el enlace del tunel si le preocupa la seguridad."
}

# 4) Backend
Write-Paso "`n== Iniciando backend en http://127.0.0.1:$Port =="
$backendProc = Start-Process -FilePath $venvPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port" `
    -WorkingDirectory (Join-Path $RepoRoot "backend") `
    -WindowStyle Minimized -PassThru

Start-Sleep -Seconds 3
if ($backendProc.HasExited) {
    Write-Host "El backend no pudo iniciar. Revise los pasos anteriores." -ForegroundColor Red
    exit 1
}
Write-Host "Backend local activo: http://127.0.0.1:$Port  (usuario: administrador)" -ForegroundColor Green

# 5) Tunel publico con cloudflared
$cloudflaredCmd = Get-Command cloudflared -ErrorAction SilentlyContinue
$cloudflaredExe = if ($cloudflaredCmd) { $cloudflaredCmd.Source } else {
    # Si se acaba de instalar con winget en esta misma sesion, el PATH del
    # proceso actual puede no haberse refrescado todavia; se busca la ruta
    # tipica de instalacion como respaldo.
    $candidatos = @(
        "$env:ProgramFiles (x86)\cloudflared\cloudflared.exe",
        "${env:ProgramFiles}\cloudflared\cloudflared.exe",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Cloudflare.cloudflared*\cloudflared.exe"
    )
    (Get-Item $candidatos -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
}

if (-not $cloudflaredExe) {
    Write-Host "`ncloudflared no esta instalado en esta maquina." -ForegroundColor Red
    Write-Host "Instalelo con:  winget install --id Cloudflare.cloudflared -e" -ForegroundColor Yellow
    Write-Host "El sistema sigue disponible localmente en http://127.0.0.1:$Port" -ForegroundColor Yellow
    Wait-Process -Id $backendProc.Id
    exit 0
}

Write-Paso "`n== Abriendo tunel publico con cloudflared =="
Write-Host "(la URL https://xxxxx.trycloudflare.com aparece abajo en unos segundos; compartala con el equipo)" -ForegroundColor DarkGray
Write-Host "Presione Ctrl+C para cerrar el tunel y el backend.`n" -ForegroundColor DarkGray

try {
    & $cloudflaredExe tunnel --url "http://127.0.0.1:$Port"
} finally {
    Write-Aviso "`nCerrando backend..."
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
}
