param (
    [Parameter(Mandatory=$false, Position=0)]
    [string]$dir_concat = $(throw "pos 0 arg 'dir_concat' missing"),
    [Parameter()]
    [switch]$write
)

# TODO: allow current directory

$ErrorActionPreference = "Stop"

. "$($GWSPS)\concat-ffpeg.ps1" # Concat-Ffpeg
. "$($GWSPS)\globals.ps1" # $regex_vid_exts

$logs_dir = "$($HOME)\Documents\logs-gws"
New-Item -ItemType Directory -Force -Path $logs_dir | Out-Null
$log_concat_dir = "$($logs_dir)\log-concat-dir-$((Get-Date).tostring("yy-MM-dd-hhmmss")).txt"
function Concat-Dir-Ffmpeg {
    param (
        [Parameter(Mandatory=$false, Position=0)]
        [string]$dir_concat = $(throw "pos0: dir_concat missing"),
        [switch]$write
    )

    $dir_concat = Join-Path -Path $dir_concat -ChildPath ""

    $regex = "^.*-pt[0-9]\.($regex_vid_exts)$"
    $files = (Get-ChildItem $dir_concat | Where-Object { $_.Name -match $regex }).Name
    $num_files = $($files).Length
    if($num_files -eq 0) {return}

    $extension = [System.IO.Path]::GetExtension("$($files[0])")
    $file_extensionless = [System.IO.Path]::GetFileNameWithoutExtension("$($files[0])") -replace “....$”
    $regex_files = "^.*-pt","\$extension$"
    $regex_files = "$file_extensionless-pt","$extension"
    
    $num_files = $($files).Length
    for ($i=1; $i -le $num_files; $i++) {
        $files[$i-1] = "$($dir_concat)$($files[$i-1])"
        if (!($($files[$i-1]) | Select-String -SimpleMatch "$($dir_concat)$($regex_files[0])$i$($regex_files[1])")){
            Write-Host "ERROR: $($files[$i-1]) does not match the expected form"
            return
        }
    }
    # Write-Host $files
    $file_total = "$($dir_concat)$($file_extensionless)$($extension)"
    Concat-Ffpeg $file_total $files -write:$write.IsPresent
}

Get-ChildItem $dir_concat -Recurse -Directory | % {
    Concat-Dir-Ffmpeg $_.FullName -write:$write.IsPresent
} | Tee-Object -FilePath $log_concat_dir