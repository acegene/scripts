$ErrorActionPreference = "Stop"

$dir = Split-Path -Parent $PSCommandPath
$state_file = "nord-switch-state.txt"
$state_file_path = "$($dir)/$($state_file)"
if (!(Test-Path "$state_file_path")){New-Item -path $dir -name $state_file -type "file" | Out-Null}
$file_data = Get-Content $state_file_path
if ($file_data -ne 'Germany') {
    $group = 'Germany'
    cmd /c 'cd "C:\Program Files\NordVPN" & nordvpn -c --group-name "Germany"'
}else{
    $group = 'Switzerland'
    cmd /c 'cd "C:\Program Files\NordVPN" & nordvpn -c --group-name "Switzerland"'
}

$group | Out-File -FilePath $state_file_path