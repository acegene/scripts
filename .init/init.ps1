# init.ps1
#
# descr: generate a powershell profile with aliases configs etc
#
# todos: robustness of terminal cfg setup

$ErrorActionPreference = 'Stop'

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "EXEC: cd '$PWD'; & '$PSCommandPath' $args # as admin powershell"
    Start-Process PowerShell -Verb RunAs "-NoExit -NoProfile -ExecutionPolicy Bypass -Command `"cd '$PWD'; & '$PSCommandPath' $args`""
    exit
}

function _init {
    #### hardcoded values
    $dir_this = $PSScriptRoot # not compatible with PS version < 3.0
    $dir_repo = "$(Push-Location $(git -C $($dir_this) rev-parse --show-toplevel); Write-Output $PWD; Pop-Location)"
    $terminal_script_path = "$($dir_repo)\win\cfg\terminal-cfg\terminal-cfg.ps1"
    #### cfg windows terminal
    & $terminal_script_path
}

_init @args
