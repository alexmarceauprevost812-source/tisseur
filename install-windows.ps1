# Tisseur — installation Windows (PowerShell)
#
# Vérifie Python et Git (les installe avec winget au besoin), puis crée
# une commande « tisseur » pour lancer l'outil depuis n'importe quel
# dossier.
#
# USAGE (dans PowerShell, depuis le dossier du projet) :
#   powershell -ExecutionPolicy Bypass -File install-windows.ps1
#
# NOTE : La plupart des outils de pentest (nmap, hydra, nikto...) sont
# faits pour Linux. Sur Windows, Tisseur sert surtout à la reconnaissance
# et au scan (nmap). Pour le kit complet, utilise Kali Linux ou WSL.

$ErrorActionPreference = "Stop"

Write-Host "`n[*] Installation de Tisseur (Windows)...`n"

function Test-Cmd($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

# 1. Python
if (Test-Cmd "python") {
    Write-Host "[OK] Python est deja installe."
} elseif (Test-Cmd "winget") {
    Write-Host "[*] Installation de Python via winget..."
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
} else {
    Write-Host "[!] Python n'est pas installe et winget est absent."
    Write-Host "    Installe Python depuis https://www.python.org/downloads/ (coche 'Add to PATH')."
    exit 1
}

# 2. Git
if (Test-Cmd "git") {
    Write-Host "[OK] Git est deja installe."
} elseif (Test-Cmd "winget") {
    Write-Host "[*] Installation de Git via winget..."
    winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
} else {
    Write-Host "[!] Git n'est pas installe. Installe-le depuis https://git-scm.com/download/win"
}

# 3. Trouver ou est ce script (donc ou est tisseur.py).
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$SCRIPT = Join-Path $DIR "tisseur.py"

if (-not (Test-Path $SCRIPT)) {
    Write-Host "[!] tisseur.py introuvable dans $DIR"
    Write-Host "    Lance ce script depuis le dossier du projet."
    exit 1
}

# 4. Creer la commande « tisseur » : un petit .cmd dans un dossier du PATH.
$BIN = Join-Path $env:LOCALAPPDATA "Tisseur"
New-Item -ItemType Directory -Force -Path $BIN | Out-Null

$LAUNCHER = Join-Path $BIN "tisseur.cmd"
"@echo off`r`npython `"$SCRIPT`" %*" | Set-Content -Path $LAUNCHER -Encoding ASCII

# Ajouter le dossier au PATH de l'utilisateur s'il n'y est pas deja.
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BIN*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$BIN", "User")
    Write-Host "[*] Dossier ajoute au PATH (rouvre PowerShell pour que ca prenne effet)."
}

Write-Host "`n[OK] Termine !`n"
Write-Host "Rouvre une nouvelle fenetre PowerShell, puis lance :"
Write-Host "    tisseur                           # menu interactif"
Write-Host "    tisseur --gui                     # interface graphique"
Write-Host "    tisseur --target 192.168.56.102   # lancer sur une cible"
Write-Host "    tisseur --guide                   # afficher le guide"
