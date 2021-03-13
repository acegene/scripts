# init.ps1
#
# descr: overwrite terminal settings with custom repo settings

$ErrorActionPreference = "Stop"

function _init {
    #### hardcoded values
    $dir_this = $PSScriptRoot # not compatible with PS version < 3.0
    $path_terminal_settings_symlink = "$($dir_this)\settings.json"
    $path_terminal_settings = "$($HOME)\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
    #### cfg windows terminal
    if (!(Test-Path "$path_terminal_settings")){
        echo "ERROR: cannot find: $path_terminal_settings, aborting terminal cfg setup"
    }elseif(!(Test-Path $path_terminal_settings_symlink)){
        echo "ERROR: cannot find: $path_terminal_settings_symlink, aborting terminal cfg setu"
    }elseif([string]::IsNullOrEmpty((Get-Item "$path_terminal_settings").Target)){
        echo "INFO: terminal cfg orig: $($path_terminal_settings)"
        echo "INFO: terminal cfg link: $($path_terminal_settings_symlink)"
        $confirmation = Read-Host -Prompt 'PROMPT: replace above orig with link? y/n'
        if ("$confirmation" -eq 'yes' -Or "$confirmation" -eq 'y') {
             Remove-Item -Force "$path_terminal_settings"
             $null = New-Item -Path "$path_terminal_settings" -ItemType SymbolicLink -Value "$path_terminal_settings_symlink"
        }else{
            echo "WARNING: aborting terminal cfg setup, consider installing and using Windows Terminal!"
        }
    }else{
        echo "INFO: seems like terminal cfg is already installed"
    }
}

_init @args