# set-quick-access.ps1
#
# descr: quickly clear or edit the file explorer quick access menu of unpinned entries
#
# usage: set-quick-access.ps1 -clear
#            removes all unpinned entires from quick access
#
# warns: file explorer is force reloaded during the clear process
#
# todos: enable editing of quick-access entries, see: https://gallery.technet.microsoft.com/Set-QuickAccess-117e9a89

$ErrorActionPreference = "Stop"

function _set-quick-access {
    param (
        [switch]$clear
    )
    #### hardcoded values
    if ($clear) {
        Write-Host "INFO: clearing quick access..." -NoNewline

        Get-ChildItem $env:APPDATA\Microsoft\Windows\Recent\* -File -Force -Exclude desktop.ini | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem $env:APPDATA\Microsoft\Windows\Recent\AutomaticDestinations\* -File -Force -Exclude desktop.ini, f01b4d95cf55d32a.automaticDestinations-ms | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem $env:APPDATA\Microsoft\Windows\Recent\CustomDestinations\* -File -Force -Exclude desktop.ini | Remove-Item -Force -ErrorAction SilentlyContinue

        #### clear unpinned folders from Quick Access, using the Verbs() method
        $UnpinnedQAFolders = (0,0)
        While ($UnpinnedQAFolders) {
            $UnpinnedQAFolders = (((New-Object -ComObject Shell.Application).Namespace("shell:::{679f85cb-0220-4080-b29b-5540cc05aab6}").Items() |
            where IsFolder -eq $true).Verbs() | where Name -match "Remove from Quick access")
            If ($UnpinnedQAFolders) { $UnpinnedQAFolders.DoIt() }
        }

        Write-Host "`nSUCCESS:"
        Stop-Process -Name explorer -Force

        Remove-Variable UnpinnedQAFolders
    }
}

_set-quick-access @args
