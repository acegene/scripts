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
# date of generation: 201219
# generation cmd on the following line:
# python "${GWSPY}/write-btw.py" "-t" "ps1" "-w" "${GWSS}/init/init.ps1" "-r" "${GWSPS}/_helper-funcs.ps1" "-x" "Group-Unspecified-Args"

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
    #### if no profile exists create one
    if (!(Test-Path $profile)){New-Item -Type File -Force $profile}
    #### hardcoded values
    $path_this = $PSCommandPath # not compatible with PS version < 3.0
    $dir_this = $PSScriptRoot # not compatible with PS version < 3.0
    $dir_repo = "$(pushd $(git -C $($dir_this) rev-parse --show-toplevel); echo $PWD; popd)"
    $dir_bin = "$($dir_repo)\bin"
    $path_src = "$($dir_repo)\src\src.ps1"
    $path_prof = "$($HOME)\Documents\PowerShell\Microsoft.PowerShell_profile.ps1"
    $dir_term = "$($HOME)\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState"
    $dir_term_loc = "$($dir_repo)\win\cfg\terminal-cfg"
    #### lines to append
    $cmd_args = "$($named_args.Keys | % { "-$($_)" + " '$($named_args.Item($_))'" }) "
    $cmd_args += "$($unnamed_args | % { "'$($_)'" })"
    if ($cmd_args -eq " ''"){$cmd_args = ""}
    $prof_cmd = ". '$($path_src)' $($cmd_args)"
    #### check if lines exist in file, otherwise append them
    if ($(((Get-Content -Raw $path_prof) -split '\n')[-1]) -ne ''){
        $prof_cmd = "`r`n$($prof_cmd)"
    }
    $file_str = Get-Content $path_prof | Select-String -SimpleMatch $prof_cmd
    if ($file_str -eq $null){
        echo $prof_cmd >> $path_prof
    }
    #### cfg windows terminal
    if (!(Test-Path $dir_term)){
        echo "ERROR: cannot find: $dir_term, aborting terminal cfg setup"
    }elseif(!(Test-Path $dir_term_loc)){
        echo "ERROR: cannot find: $dir_term_loc, aborting terminal cfg setu"
    }elseif((Get-Item $dir_term).Target -eq $null){
        echo "NOTE: terminal cfg dir orig: $($dir_term)"
        echo "NOTE: terminal cfg dir link: $($dir_term_loc)"
        $confirmation = Read-Host -Prompt 'PROMPT: replace above orig dir with link dir? y/n'
        if ($confirmation -eq 'yes' -Or $confirmation -eq 'y') {
             Remove-Item -Recurse -Force $dir_term
             $null = New-Item -Path $dir_term -ItemType SymbolicLink -Value $dir_term_loc
        }else{
            echo "WARNING: aborting terminal cfg setup, consider installing and using Windows Terminal!"
        }
    }
}

_init @args