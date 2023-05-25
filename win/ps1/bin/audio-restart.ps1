$ErrorActionPreference = 'Stop'

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "EXEC: cd '$PWD'; & '$PSCommandPath' $args # as admin powershell"
    Start-Process PowerShell -Verb RunAs "-NoExit -NoProfile -ExecutionPolicy Bypass -Command `"cd '$PWD'; & '$PSCommandPath' $args`""
    exit
}

Start-Process -FilePath "cmd.exe"  -ArgumentList '/c net stop audiosrv && net stop AudioEndpointBuilder && net start audiosrv && net start AudioEndpointBuilder'
