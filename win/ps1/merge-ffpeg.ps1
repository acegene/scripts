function Merge-Ffmpeg {
    param (
        [Parameter(Mandatory=$false, Position=0)]
        [string]$merge_out = $(throw "pos0: merge_out missing"),
        [Parameter(Mandatory=$false, Position=1)]
        [string[]]$files = $(throw "pos1: files missing")
    )

    $ErrorActionPreference = "Stop"

    . "$($GWSPS)\_helper-funcs.ps1" # Resolve-Path-Force

    $merge_out = Resolve-Path-Force $merge_out
    $dir = "$(Split-Path -Path $($files[0]))"
    $tmp_txt = "$($dir)\tmp-txt-$((Get-Date).tostring("yyMMddhhmmss")).txt"

    if (!(Test-Path -LiteralPath $dir)) {Write-Host "ERROR: $dir does not exist"; exit 1}

    try {
        foreach ($f in $files){
            ## ffmpeg likes unix style forward slashes 
            $f = $f -replace "\\","/"
            $f = $f -replace "'", "'\''"
            Write-Output "file '$f'" >> $tmp_txt
        }
        Write-Host $merge_out
        Get-Content $tmp_txt
        $confirmation = Read-Host -Prompt 'select yes/no on whether to merge files above'
        if ($confirmation -eq 'yes' -Or $confirmation -eq 'y') {
            ffmpeg -f concat -safe 0 -i $tmp_txt -c copy "$merge_out"
            if ($? -And $(Test-Path $merge_out)) {
                Invoke-Item $merge_out
                foreach ($f in $files){
                    Write-Host "$f"
                }
                Write-Host $merge_out
                $confirmation = Read-Host -Prompt 'select yes/no on whether conversion worked'
                if ($confirmation -eq 'yes' -Or $confirmation -eq 'y') {
                    foreach ($f in $files){
                        Write-Host "removing $f"
                        Remove-Item $f -Force
                    }
                }
                if ($confirmation -eq 'no' -Or $confirmation -eq 'n') {
                    Remove-Item $merge_out -Force
                }
            }
        }
    }
    finally {
        try {
            Remove-Item $tmp_txt -Force
            # Write-Host "removed $tmp_txt"
        }catch{}
    }
}