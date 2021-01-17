function Concat-Ffpeg {
    param (
        [Parameter(Mandatory=$false, Position=0)]
        [string]$concat_out = $(throw "pos0: concat_out missing"),
        [Parameter(Mandatory=$false, Position=1)]
        [string[]]$files = $(throw "pos1: files missing"), 
        [Parameter()]
        [switch]$write
    )

    $ErrorActionPreference = "Stop"

    . "$($GWSPS)\_helper-funcs.ps1" # Force-Resolve-Path

    $concat_out = Force-Resolve-Path $concat_out
    $dir = "$(Split-Path -Path $concat_out)"
    $tmp_txt = "$($dir)\tmp-txt-$((Get-Date).tostring("yyMMddhhmmss")).txt"

    try {
        foreach ($f in $files){
            ## ffmpeg likes unix style forward slashes 
            $f = $f -replace "\\","/"
            echo "file '$f'" >> $tmp_txt
        }
        echo $concat_out
        cat $tmp_txt
        if($write.IsPresent) {
            $confirmation = Read-Host -Prompt 'select yes/no on whether to merge files above'
            if ($confirmation -eq 'yes' -Or $confirmation -eq 'y') {
                ffmpeg -f concat -safe 0 -i $tmp_txt -c copy $concat_out
                if ($? -And $(Test-Path $concat_out)) {
                    foreach ($f in $files){
                        Write-Host "removing $f"
                        rm $f -Force
                    }
                }
            }
        }
    }
    finally {
        # Write-Host "removing $tmp_txt"
        rm $tmp_txt -Force
    }
}