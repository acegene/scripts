#!/bin/bash
#
# descr: this file is sourced via this repo's init.bash

_src(){
    #### hardcoded vars
    local script_path="${BASH_SOURCE[0]}"
    local dir_script="$(cd "$(dirname "${script_path}")"; pwd -P)" && [ "${dir_script}" != '' ] || ! __echo -se "ERROR: dir_script=''" || return 1
    local dir_repo="$(cd "${dir_script}" && cd $(git rev-parse --show-toplevel) && echo ${PWD})" && [ "${dir_repo}" != '' ] || ! __echo -se "ERROR: dir_repo=''" || return 1
    #### exports
    export PATH="${PATH}:${dir_repo}/bin"
    export GWSS="${dir_repo}"
    #### aliases
    alias gwss="cd ${GWSS} && git status -sb"
}

_src "${@}" || exit "${?}"