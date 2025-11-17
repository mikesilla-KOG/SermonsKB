<#
Windows setup script for SermonsKB

This script will:
- Ensure a local virtual environment exists and is activated
- Upgrade pip and install Python dependencies from requirements.txt
- Install Whisper (openai-whisper) and CPU-only PyTorch (optional but recommended)
- Check for ffmpeg in PATH and suggest installation if missing

Usage (PowerShell, from repo root):
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\scripts\setup_windows.ps1

Note: If Chocolatey is installed, the script can optionally install ffmpeg.
#>

param(
    [switch]$InstallTorchCpu = $true,
    [switch]$TryChocoFfmpeg = $false
)

Write-Host "[SermonsKB] Starting Windows setup..." -ForegroundColor Cyan

function Ensure-Python {
    try {
        $v = & py --version 2>$null
        if ($LASTEXITCODE -eq 0) { Write-Host "Python detected via 'py': $v"; return 'py' }
    } catch {}
    try {
        $v2 = & python --version 2>$null
        if ($LASTEXITCODE -eq 0) { Write-Host "Python detected via 'python': $v2"; return 'python' }
    } catch {}
    throw "Python not found. Install Python 3.10+ from https://www.python.org/downloads/ then re-run."
}

$pythonCmd = Ensure-Python

# Create venv if missing
if (-not (Test-Path .\.venv)) {
    Write-Host "Creating virtual environment .venv" -ForegroundColor Yellow
    & $pythonCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment" }
}

# Activate venv
Write-Host "Activating virtual environment" -ForegroundColor Yellow
. .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip" -ForegroundColor Yellow
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }

# Install requirements
Write-Host "Installing requirements.txt" -ForegroundColor Yellow
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "requirements install failed" }

# Install Whisper (openai-whisper)
Write-Host "Installing openai-whisper (local Whisper)" -ForegroundColor Yellow
python -m pip install --upgrade openai-whisper
if ($LASTEXITCODE -ne 0) { Write-Warning "openai-whisper installation encountered issues; Whisper transcription may be unavailable" }

# Optional: install CPU-only PyTorch stack for Whisper acceleration
if ($InstallTorchCpu) {
    Write-Host "Installing CPU-only PyTorch (torch, torchvision, torchaudio)" -ForegroundColor Yellow
    python -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
    if ($LASTEXITCODE -ne 0) { Write-Warning "PyTorch CPU installation failed; Whisper will still work but may be slower or use other backends" }
}

# Check ffmpeg
Write-Host "Checking ffmpeg availability" -ForegroundColor Yellow
try {
    & ffmpeg -version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "ffmpeg found in PATH" -ForegroundColor Green
    } else {
        throw "ffmpeg not found"
    }
} catch {
    Write-Warning "ffmpeg not detected. yt-dlp audio extraction and Whisper require ffmpeg."
    if ($TryChocoFfmpeg) {
        try {
            choco --version | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Attempting to install ffmpeg via Chocolatey" -ForegroundColor Yellow
                choco install -y ffmpeg
            } else {
                Write-Warning "Chocolatey not found. Install ffmpeg manually from https://ffmpeg.org/download.html and add to PATH."
            }
        } catch {
            Write-Warning "Chocolatey not available. Install ffmpeg manually and re-run."
        }
    } else {
        Write-Host "Manual install instructions: https://ffmpeg.org/download.html (add bin folder to PATH)" -ForegroundColor DarkYellow
    }
}

Write-Host "[SermonsKB] Setup complete." -ForegroundColor Cyan
