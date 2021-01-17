Set-ExecutionPolicy RemoteSigned -Force

$ErrorActionPreference = 'Stop'

try {choco -v} catch{
	Write-Output "NOTE:Seems Chocolatey is not installed, installing now"
    	Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

$pkgs_always = '7zip','autohotkey','discord','ffmpeg','firefox','git','gitkraken','googlechrome'
			   'malwarebytes','microsoft-windows-terminal','nordvpn','notepadplusplus','python3',
			   'spotify','steam','teamviewer','utorrent','vlc','vscode'
$pkgs_maybe = 'bitnami-xampp','itunes','javaruntime','razer-synapse-2'
$pkgs_broken = 'battle.net'

ForEach ($PackageName in $Packages)
{
    choco install $PackageName -y --acceptlicense
}