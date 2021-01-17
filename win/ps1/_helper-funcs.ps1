function Force-Resolve-Path {
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

