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

function Resolve-Path-Force {
    <#
    .SYNOPSIS
        Calls Resolve-Path but works for files that don't exist.
    .REMARKS
        From http://devhawk.net/blog/2010/1/22/fixing-powershells-busted-resolve-path-cmdlet
    #>
    param (
        [string] $FileName
    )
    $FileName = Resolve-Path $FileName -ErrorAction SilentlyContinue `
                                       -ErrorVariable _frperror
    if (-not($FileName)) {
        $FileName = $_frperror[0].TargetObject
    }
    return $FileName
}

function Upper-Lower-Case-Convert {
    param (
        [string] $dir_name,
        [Parameter()]
        [switch]$files
    )
    if ($files.IsPresent) {
        Get-ChildItem $dir_name -File -Recurse |
            ForEach-Object{
                $file_full = $_.FullName
                $file_name = $_.name
                Rename-Item -LiteralPath $file_full -NewName "$($file_name).TEMPORARY";
                Rename-Item -LiteralPath "$($file_full).TEMPORARY" -NewName "$($file_name)".ToLowerInvariant()
            }
    }else{
        Get-ChildItem $dir_name -Recurse |
            ForEach-Object{
                $file_full = $_.FullName
                $file_name = $_.name
                Rename-Item -LiteralPath $file_full -NewName "$($file_name).TEMPORARY";
                Rename-Item -LiteralPath "$($file_full).TEMPORARY" -NewName "$($file_name)".ToLowerInvariant()
            }
    }
}

