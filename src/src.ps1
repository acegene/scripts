# src.ps1
#
# descr: this file is sourced via this repo's init.ps1

$ErrorActionPreference = "Stop"

function _src {
    #### hardcoded values
    $path_this = $PSCommandPath # not compatible with PS version < 3.0
    $dir_this = $PSScriptRoot # not compatible with PS version < 3.0
    $dir_repo = "$(pushd $(git -C $($dir_this) rev-parse --show-toplevel); echo $PWD; popd)"
    $dir_bin = "$($dir_repo)\win\bin"
    #### exports
    $global:GWSS = $dir_repo
    $global:GWSPS = "$($dir_repo)\win\ps1"
    $global:GWSPY = "$($dir_repo)\py"
    $global:GWSSH = "$($dir_repo)\shell"
    $global:GWSST = "$($dir_repo)\storage"
    $env:GWSST = $global:GWSST
    $env:PATH += ";$($dir_bin)"
    $env:PYTHONPATH += ";$($global:GWSPY)"
    #### aliases
    function global:gwss {cd $global:GWSS; if($?){git status -sb}}
    function global:gwsps {cd $global:GWSPS; if($?){git status -sb}}
    function global:gwspy {cd $global:GWSPY; if($?){git status -sb}}
    function global:gwssh {cd $global:GWSSH; if($?){git status -sb}}
    function global:gwsst {cd $global:GWSST; if($?){git status -sb}}
    ## nordvpn
    function global:nvs {& "$($GWSPS)\nord-switch.ps1" @args}
}

_src @args
