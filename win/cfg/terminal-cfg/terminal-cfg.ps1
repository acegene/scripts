# Overwrite terminal settings with symlink to repo specified settings

$ErrorActionPreference = 'Stop'

function _init {
    #### hardcoded values
    $dir_this = $PSScriptRoot # not compatible with PS version < 3.0
    $path_terminal_settings_symlink = "$($dir_this)\settings.json"
    $dir_repo = "$(Push-Location $(git -C $($dir_this) rev-parse --show-toplevel); Write-Output $PWD; Pop-Location)"
    $path_terminal_settings = "$($HOME)\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
    #### cfg windows terminal
    if (!(Test-Path "$path_terminal_settings")) {
        Write-Host "ERROR: cannot find: $path_terminal_settings, aborting terminal cfg setup"
    } elseif (!(Test-Path $path_terminal_settings_symlink)) {
        Write-Host "ERROR: cannot find: $path_terminal_settings_symlink, aborting terminal cfg setup"
    } elseif ([string]::IsNullOrEmpty((Get-Item "$path_terminal_settings").Target)) {
        Write-Host "INFO: terminal cfg orig: $($path_terminal_settings)"
        Write-Host "INFO: terminal cfg link: $($path_terminal_settings_symlink)"
        $confirmation = Read-Host -Prompt 'PROMPT: replace above orig with link? y/n'
        if ("$confirmation" -eq 'yes' -Or "$confirmation" -eq 'y') {
            Remove-Item -Force "$path_terminal_settings"
            $null = New-Item -Path "$path_terminal_settings" -ItemType SymbolicLink -Value "$path_terminal_settings_symlink"
        } else {
            Write-Host 'WARNING: aborting terminal cfg setup, consider installing and using Windows Terminal!'
        }
    } else {
        Write-Host 'INFO: seems like terminal cfg is already installed'
    }
}

_init @args
