# Windows tips

## Enaable developer mode (allows symlinks without admin powershell)
from admin powershell
```
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"
```

## Get python to be seen from path
* Settings > Application > App execution aliases (https://stackoverflow.com/a/74657015)

### install latest stable powershell
From powershell
```
winget search Microsoft.PowerShell
winget install --id Microsoft.PowerShell --source winget
```

Git settings to be aware of
```
## can show whether git "trusts" the executable value windows reports
git config --global core.fileMode
git config core.fileMode
```
