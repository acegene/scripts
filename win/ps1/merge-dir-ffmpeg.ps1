param (
    [Parameter(Mandatory=$false)]
    [string]$dir_merge = $(throw "dir_merge missing"),
    [Parameter(Mandatory=$false, ValueFromRemainingArguments=$true)]
    $unspecified_args
)

# TODO: allow current directory

$ErrorActionPreference = "Stop"

if (!(Test-Path -LiteralPath $dir_merge)) {Write-Host "ERROR: $dir_merge does not exist"; exit 1}

. "$($GWSPS)\_helper-funcs.ps1" # Group-Unspecified-Args
. "$($GWSPS)\merge-ffmpeg.ps1" # Merge-Ffpeg
. "$($GWSPS)\globals.ps1" # $regex_vid_exts

$unspecified_named,$unspecified_unnamed = Group-Unspecified-Args @unspecified_args

$logs_dir = "$($HOME)\Documents\logs-gws"
New-Item -ItemType Directory -Force -Path $logs_dir | Out-Null
$log_merge_dir = "$($logs_dir)\log-merge-dir-$((Get-Date).tostring("yy-MM-dd-hhmmss")).txt"
function Merge-Dir-Ffmpeg {
    param (
        [Parameter(Mandatory=$false)]
        [string]$dir_merge = $(throw "dir_merge missing"),
        [Parameter(Mandatory=$false)]
        [string]$dir_out = $(throw "dir_out missing")
    )
    if (!(Test-Path -LiteralPath $dir_merge)) {Write-Host "ERROR: $dir_merge does not exist"; exit 1}
    if (!(Test-Path -LiteralPath $dir_out)) {Write-Host "ERROR: $dir_out does not exist"; exit 2}

    $dir_merge = Join-Path -Path $dir_merge -ChildPath ""
    if ($PSBoundParameters.ContainsKey('dir_out')) {$dir_out = Join-Path -Path $dir_out -ChildPath ""}

    $regex = "^.*-pt([0-9][0-9]?)\.($regex_vid_exts)$"
    $files = (Get-ChildItem $dir_merge | Where-Object { $_.Name -match $regex }).Name
    
    $lambda_extract_pt_num = {[regex]::match($_, $regex).captures.groups[1].value -as [int]}
    $files = $files | Sort-Object $lambda_extract_pt_num
    $num_files = $($files).Length
    if($num_files -eq 0) {return}

    $extension = [System.IO.Path]::GetExtension("$($files[0])")
    $file_extensionless = [System.IO.Path]::GetFileNameWithoutExtension("$($files[0])") -replace “....$”
    $regex_files = "^.*-pt","\$extension$"
    $regex_files = "$file_extensionless-pt","$extension"
    
    $num_files = $($files).Length
    for ($i=1; $i -le $num_files; $i++) {
        $files[$i-1] = "$($dir_merge)$($files[$i-1])"
        if (!($($files[$i-1]) | Select-String -SimpleMatch "$($dir_merge)$($regex_files[0])$i$($regex_files[1])")){
            Write-Host "ERROR: $($files[$i-1]) does not match the expected form"
            return
        }
    }
    # Write-Host $files
    if ($PSBoundParameters.ContainsKey('dir_out')){
        $file_out = "$($dir_out)$($file_extensionless)$($extension)"
    }else{
        $file_out = "$($dir_merge)$($file_extensionless)$($extension)"
    }
    
    Merge-Ffmpeg $file_out $files
}

Get-ChildItem $dir_merge -Recurse -Directory | ForEach-Object {
    Merge-Dir-Ffmpeg -dir_merge $_.FullName @unspecified_named @unspecified_unnamed
} | Tee-Object -FilePath $log_merge_dir