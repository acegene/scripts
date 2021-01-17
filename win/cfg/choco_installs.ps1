# choco_installs.ps1
#
# descr: iterate over hardcoded lists of apps and install them via the choco application manager
#
# usage: choco_installs.ps1
#
# todos: allow user response and choice of apps
#        output meaningful error report

Set-ExecutionPolicy RemoteSigned -Force

$ErrorActionPreference = 'Stop'

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "EXEC: cd '$PWD'; & '$PSCommandPath' $args # as admin powershell"
    Start-Process PowerShell -Verb RunAs "-NoExit -NoProfile -ExecutionPolicy Bypass -Command `"cd '$PWD'; & '$PSCommandPath' $args`""
    exit
}

try {choco -v} catch {
	Write-Output "NOTE: seems chocolatey aka choco not installed, installing..."
    	Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

$pkgs_always = '7zip','autohotkey','discord','ffmpeg','firefox','git','gitkraken','googlechrome',
			   'malwarebytes','microsoft-windows-terminal','nordvpn','notepadplusplus','python3',
			   'spotify','steam','teamviewer','vlc','vscode'
$pkgs_maybe = 'bitnami-xampp','itunes','javaruntime','razer-synapse-2'
$pkgs_broken = 'battle.net', 'utorrent'

ForEach ($PackageName in $Packages)
{
    choco install $PackageName -y --acceptlicense
}