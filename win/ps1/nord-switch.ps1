# nord-switch.ps1
#
# descr: script to enable quick switching of nordvpn's connected country
#
# usage: nord-switch.ps1
#            auto rotate to the next preconfigured location (see $country_keys and $country_vals below)
#        nord-switch.ps1 ge
#            set the country to ge aka Germany (see $country_keys and $country_vals below

$ErrorActionPreference = "Stop"

function _nord-switch {
    param (
        [Parameter(Mandatory=$false)]
        $country
    )
    #### hardcoded values
    ## paths
    $dir_this = Split-Path -Parent $PSCommandPath
    $file_state = "nord-switch-state.txt"
    $path_state = "$($dir_this)/$($file_state)"
    ## country hash table construction
    $country_keys = @('ge';'sw';'us')
    $country_vals = @('Germany';'Switzerland';'United States')
    $country_hash = @{}
    for ($i = 0; $i -lt $country_keys.Count; $i++)
    {
        $country_hash[$country_keys[$i]] = $country_vals[$i]
    }
    #### use cmd arg for country if provided, otherwise auto switch countries
    if ($country -ne $null) {
        if ($country_hash.ContainsKey($country)) {
            $group = $country_hash[$country]
        } else {
            Write-Host "ERROR: unrecognized country cmd arg: $country"
            exit 1
        }
    } else {
        #### create state file if needed
        if (!(Test-Path "$path_state")){New-Item -path $dir_this -name $file_state -type "file" | Out-Null}
        #### read state file
        $state = Get-Content $path_state
        #### auto switch to a different country than indicated in the state file
        for ($i = 0; $i -lt $country_vals.Count; $i++)
        {
            if ($state -eq $country_vals[$i]) {
                $group = $country_vals[$($i-1)]
            }
        }
        if ($group -eq $null) {
            $group = 'United States'
            Write-Output "WARNING: state for country '$($state)' unrecognized, using '$($group)'"
        } else {
            Write-Output "NOTE: state for country should switch from '$($state)' to '$($group)'"
        }
    }
    #### execute in cmd prompt nordvpn country switch
    cmd /c 'cd "C:\Program Files\NordVPN" & nordvpn -c --group-name "'"$group"'"'
    #### write state file
    $group | Out-File -FilePath $path_state
}

_nord-switch @args