#!/bin/bash
#
# descr: this file is sourced via this repo's init.bash

_src(){
    #### hardcoded vars
    local PATH_THIS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)/$(basename -- "${BASH_SOURCE[0]}")"
    local DIR_THIS="$(dirname -- "${PATH_THIS}")"
    local dir_repo="$(cd -- "${DIR_THIS}" && cd -- "$(git rev-parse --show-toplevel)" && echo "${PWD}")" && [ "${dir_repo}" != '' ] || ! __echo -se "ERROR: dir_repo=''" || return 1
    # local dir_bin="${dir_repo}/bin"
    local dir_bin_shell="${dir_repo}/shell/bin"
    #### exports
    export GWSS="${dir_repo}"
    export GWSPS="${dir_repo}/win/ps1"
    export GWSPY="${dir_repo}/py"
    export GWSSH="${dir_repo}/shell"
    export GWSST="${dir_repo}/storage"
    export PATH="${PATH}:${dir_bin_shell}"
    export PYTHONPATH="${PATH}:${GWSPY}"
    #### aliases
    alias gwss="cd ${GWSS} && git status -sb"
    alias gwss="cd ${GWSS} && git status -sb"
    alias gwsps="cd ${GWSPS} && git status -sb"
    alias gwspy="cd ${GWSPY} && git status -sb"
    alias gwssh="cd ${GWSSH} && git status -sb"
    alias gwsst="cd ${GWSST} && git status -sb"
}

_src "${@}" || exit "${?}"