$gws_globals = "$($GWSST)\globals.json"
$vid_extensions = (Get-Content $gws_globals | ConvertFrom-Json).globals.video_exts
$regex_vid_exts = [system.String]::Join("|", $vid_extensions)
