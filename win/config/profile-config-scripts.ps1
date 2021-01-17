## script to generate a powershell profile and populate it with a preferred default set of cmds
##
## if no profile exists create one
if (!(Test-Path $profile)){New-Item -Type File -Force $PROFILE}
## path to append profile cmds to
$profile_path = "$($HOME)\Documents\PowerShell\Microsoft.PowerShell_profile.ps1"
## cmds to append to profile file
$profile_commands = '$FormatEnumerationLimit = -1',
                    '$env:GWSPS = "$($env:GWS)\scripts\win\ps1"',
                    '$env:GWSPY = "$($env:GWS)\scripts\py"',
                    '$GWSPS = "$env:GWSPS"',
                    '$GWSPY = "$env:GWSPY"'
## check if cmds exist in file, otherwise append them
foreach ($cmd in $profile_commands){
    $file_str = Get-Content $profile_path | Select-String -SimpleMatch $cmd
    if ($file_str -eq $null){
        echo $cmd >> $profile_path
    }
}