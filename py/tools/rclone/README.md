## Installation
https://rclone.org/install/
- linux
    - `sudo -v ; curl https://rclone.org/install.sh | sudo bash`
- windows
    - download exe and place in ~/.local/bin

## Remote setup:
### One time setup
```
## need to manually create synced/crypt synced/uncrypt dirs on remote
rclone mkdir remote:synced/uncrypt/bk
rclone touch remote:synced/uncrypt/content/RCLONE_TEST
rclone mkdir remote:synced/crypt
rclone mkdir secret:bk
rclone touch secret:content/RCLONE_TEST # creates content dir
```

## Local setup:
### One time rclone config setup:
- Google Drive:
    - setup non encrypted acccess
        - https://rclone.org/drive/
            - `rclone config`
                - name=remote
    - setup encrypted access
        - https://rclone.org/crypt/
            - `rclone config`
                - name=secret
                - remote=remote:synced/crypt

- location of cfg:
    - linux: ~/.config/rclone/rclone.conf
    - windows: ~\AppData\Roaming\rclone\rclone.conf

### One time setup of local bisync directories:
```
rclone copy secret:content/cfg/cfg-gws.json .
rclone_bisync.py --json-cfg cfg-gws.json --init
rm cfg-gws.json
```
