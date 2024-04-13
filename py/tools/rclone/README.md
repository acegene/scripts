## Installation
https://rclone.org/install/
- windows
    - download exe and place in ~/bin 
- linux
    - sudo -v ; curl https://rclone.org/install.sh | sudo bash

## Config setup
One time setup configs:
- Google Drive:
    - setup non encrypted acccess
        - https://rclone.org/drive/
            - `rclone config`
                - name=remote
    - setup encrypted access
        - https://rclone.org/crypt/
            - `rclone config`
                - name=secret
                - remote=remote:crypt

- location of cfg:
    - linux: ~/.config/rclone/rclone.conf
    - windows: ~\AppData\Roaming\rclone\rclone.conf

## One time setup of remote:
```
## need to manually create synced/crypt synced/uncrypt dirs on remote
rclone mkdir remote:synced/uncrypt/bk
rclone touch remote:synced/uncrypt/content/text/RCLONE_TEST
rclone mkdir remote:synced/crypt
rclone mkdir secret:bk
rclone touch secret:content/text/RCLONE_TEST
```

## One time setup of local powershell:
```
## need to manually create "$($HOME)\Documents\synced\crypt\text\" "$($HOME)\Documents\synced\uncrypt\text\"
$loc_unc="$($HOME)\Documents\synced\uncrypt\text"
$rem_unc='remote:synced/uncrypt/content/text'
rclone copyto "$($rem_unc)/RCLONE_TEST" "$($loc_unc)\RCLONE_TEST"
rclone bisync --resync "$($loc_unc)" "$($rem_unc)" --check-access --verbose

$loc_unc="$($HOME)\Documents\synced\crypt\text"
$rem_unc='secret:content/text'
rclone copyto "$($rem_unc)/RCLONE_TEST" "$($loc_unc)\RCLONE_TEST"
rclone bisync --resync "$($loc_unc)" "$($rem_unc)" --check-access --verbose
```
