Set-ExecutionPolicy RemoteSigned -Force
$ErrorActionPreference = 'Stop'
try { choco -v }
catch {
	Write-Output "NOTE:Seems Chocolatey is not installed, installing now"
    	Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

$Packages = '7zip', 'googlechrome', 'firefox', 'git', 'notepadplusplus', 'vlc', 'python3', 'autohotkey.portable', 'itunes', 'vscode', 'steam', 'discord', 'spotify', 'teamviewer', 'nordvpn', 'razer-synapse-2', 'utorrent', 'malwarebytes', 'bitnami-xampp', 'battle.net'

ForEach ($PackageName in $Packages)
{
    choco install $PackageName -y --acceptlicense
}