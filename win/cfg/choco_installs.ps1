# Iterate over hardcoded lists of apps and install them via the choco application manager
#
# usage
#   * choco_installs.ps1
#
# todos
#   * allow user response and choice of apps
#   * output meaningful error report

Set-ExecutionPolicy RemoteSigned -Force

$ErrorActionPreference = 'Stop'

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "EXEC: cd '$PWD'; & '$PSCommandPath' $args # as admin powershell"
    Start-Process PowerShell -Verb RunAs "-NoExit -NoProfile -ExecutionPolicy Bypass -Command `"cd '$PWD'; & '$PSCommandPath' $args`""
    exit
}

try {choco -v} catch {
    Write-Host 'INFO: seems chocolatey aka choco not installed, installing...'
    Set-ExecutionPolicy Bypass -Scope Process -Force; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# $ninite = '7zip', 'chrome', 'discord', 'firefox', 'malwarebytes', 'notepad++', 'python3', 'qbittorrent', 'spotify', 'steam', 'vlc', 'vscode'
# $ninite_maybe = 'teamviewer', 'itunes'

$pkgs_always = 'autohotkey', 'ffmpeg', 'git', 'gitkraken', 'nordvpn', 'shellcheck',
$pkgs_maybe = 'bitnami-xampp', 'microsoft-windows-terminal', 'razer-synapse-2'
$pkgs_broken = 'battle.net'
# $packages_untested = bazelisk buildifier

ForEach ($PackageName in $pkgs_always) {
    choco install $PackageName -y --acceptlicense
}
