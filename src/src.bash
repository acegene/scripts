#!/bin/bash
#
# descr: this file is sourced via this repo's init.bash

_src(){
    #### hardcoded vars
    local path_this="${BASH_SOURCE[0]}"
    local dir_this="$(cd "$(dirname "${path_this}")"; pwd -P)" && [ "${dir_this}" != '' ] || ! __echo -se "ERROR: dir_this=''" || return 1
    local dir_repo="$(cd "${dir_this}" && cd $(git rev-parse --show-toplevel) && echo ${PWD})" && [ "${dir_repo}" != '' ] || ! __echo -se "ERROR: dir_repo=''" || return 1
    local dir_bin="${dir_repo}/bin"
    #### exports
    export PATH="${PATH}:${dir_bin}"
    export GWSS="${dir_repo}"
    export GWSPS="${dir_repo}/win/ps1"
    export GWSPY="${dir_repo}/py"
    export GWSST="${dir_repo}/storage"
    #### aliases
    alias gwss="cd ${GWSS} && git status -sb"
    alias gwss="cd ${GWSS} && git status -sb"
    alias gwsps="cd ${GWSPS} && git status -sb"
    alias gwspy="cd ${GWSPY} && git status -sb"
    alias gwssh="cd ${GWSSH} && git status -sb"
    alias gwsst="cd ${GWSST} && git status -sb"
}

_src "${@}" || exit "${?}"