# init.ps1
#
# descr: generate a powershell profile with aliases configs etc
#
# todos: robustness of terminal cfg setup

$ErrorActionPreference = "Stop"

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "EXEC: cd '$PWD'; & '$PSCommandPath' $args # as admin powershell"
    Start-Process PowerShell -Verb RunAs "-NoExit -NoProfile -ExecutionPolicy Bypass -Command `"cd '$PWD'; & '$PSCommandPath' $args`""
    exit
}

################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################
# yymmdd: 210228
# generation cmd on the following line:
# python "${GWSPY}/write-btw.py" "-t" "ps1" "-w" "${GWSS}/init/init.ps1" "-x" "Group-Unspecified-Args"

function Group-Unspecified-Args {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        $ExtraParameters
    )

    $ParamHashTable = @{}
    $UnnamedParams = @()
    $CurrentParamName = $null
    $ExtraParameters | ForEach-Object -Process {
        if ($_ -match "^-") {
            # Parameter names start with '-'
            if ($CurrentParamName) {
                # Have a param name w/o a value; assume it's a switch
                # If a value had been found, $CurrentParamName would have been nulled out again
                $ParamHashTable.$CurrentParamName = $true
            }

            $CurrentParamName = $_ -replace "^-|:$"
        }
        else {
            # Parameter value
            if ($CurrentParamName) {
                $ParamHashTable.$CurrentParamName += $_
                $CurrentParamName = $null
            }
            else {
                $UnnamedParams += $_
            }
        }
    } -End {
        if ($CurrentParamName) {
            $ParamHashTable.$CurrentParamName = $true
        }
    }

    return $ParamHashTable,$UnnamedParams
}
################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################

function _init {
    param (
        [Parameter(Mandatory=$false, ValueFromRemainingArguments=$true)]
        $unspecified_args
    )
    #### collect cmd args
    $named_args,$unnamed_args = Group-Unspecified-Args @unspecified_args
    #### hardcoded values
    $path_this = $PSCommandPath # not compatible with PS version < 3.0
    $dir_this = $PSScriptRoot # not compatible with PS version < 3.0
    $dir_repo = "$(pushd $(git -C $($dir_this) rev-parse --show-toplevel); echo $PWD; popd)"
    # $dir_bin = "$($dir_repo)\bin"
    $path_src = "$($dir_repo)\src\src.ps1"
    $terminal_script_path = "$($dir_repo)\win\cfg\terminal-cfg\terminal-cfg.ps1"
    #### includes
    . "$($dir_repo)\src\cfg.ps1"
    #### if no profile exists create one
    if (!(Test-Path $path_ps_profile)){New-Item -Type File -Force $path_ps_profile}
    if (!(Test-Path $path_ps_profile_2)){New-Item -Type File -Force $path_ps_profile_2}
    #### lines to append
    $cmd_args = "$($named_args.Keys | % { "-$($_)" + " '$($named_args.Item($_))'" }) "
    $cmd_args += "$($unnamed_args | % { "'$($_)'" })"
    if ($cmd_args -eq " ''"){$cmd_args = ""}
    $prof_cmd = ". '$($path_src)' $($cmd_args)"
    #### check if lines exist in file, otherwise append them
    if ($(((Get-Content -Raw $path_ps_profile) -split '\n')[-1]) -ne ''){
        $prof_cmd = "`r`n$($prof_cmd)"
    }
    $file_str = Get-Content $path_ps_profile | Select-String -SimpleMatch $prof_cmd
    if ($file_str -eq $null){
        echo $prof_cmd >> $path_ps_profile
    }
    if ($(((Get-Content -Raw $path_ps_profile_2) -split '\n')[-1]) -ne ''){
        $prof_cmd = "`r`n$($prof_cmd)"
    }
    $file_str = Get-Content $path_ps_profile_2 | Select-String -SimpleMatch $prof_cmd
    if ($file_str -eq $null){
        echo $prof_cmd >> $path_ps_profile_2
    }
    #### cfg windows terminal
    & $terminal_script_path
}

_init @args