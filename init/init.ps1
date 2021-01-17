# init.ps1
#
# descr: generate a powershell profile with aliases configs etc

$ErrorActionPreference = "Stop"

################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################
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
                # If a value had been found, $CurrentParamName would have
                # been nulled out again
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
    $src_path = "$($dir_repo)\src\src.ps1"
    $path_prof = "$($HOME)\Documents\PowerShell\Microsoft.PowerShell_profile.ps1"
    #### lines to append
    $cmd_args = "$($named_args.Keys | % { "-$($_)" + " '$($named_args.Item($_))'" }) "
    $cmd_args += "$($unnamed_args | % { "'$($_)'" })"
    if ($cmd_args -eq " ''"){$cmd_args = ""}
    $prof_cmd = ". '$($src_path)' $($cmd_args)"
    #### check if lines exist in file, otherwise append them
    if ($(((Get-Content -Raw $path_prof) -split '\n')[-1]) -ne ''){
        $prof_cmd = "`r`n$($prof_cmd)"
    }
    $file_str = Get-Content $path_prof | Select-String -SimpleMatch $prof_cmd
    if ($file_str -eq $null){
        echo $prof_cmd >> $path_prof
    }
}

_init @args