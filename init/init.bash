#!/bin/bash
#
# descr: adds sourcing of this repo's src.bash in ~/.bash_aliases

set -u

_init() {
    #### hardcoded vars
    ## dirs
    local path_this="${BASH_SOURCE[0]}"
    local dir_this="$(cd "$(dirname "${path_this}")"; pwd -P)" && [ "${dir_this}" != '' ] || ! __echo -se "ERROR: dir_this=''" || return 1
    local dir_repo="$(cd "${dir_this}" && cd $(git rev-parse --show-toplevel) && echo ${PWD})" && [ "${dir_repo}" != '' ] || ! __echo -se "ERROR: dir_repo=''" || return 1
    ## includes
    . "${dir_repo}/shell/_helper-funcs.bash" || ! echo "ERROR: sourcing failed" || return 1
    ## files
    local bash_aliases="${HOME}/.bash_aliases"
    local bashrc="${HOME}/.bashrc"
    local src="${dir_repo}/src/src.bash"
    #### lines to add to files
    local lines_bash_aliases=('[ -f '"'${src}'"' ] && . '"'${src}'")
    #### create files/dirs if not found
    __check_if_obj_exists -ct 'file' "${bash_aliases}" || return "${?}"
    local status=''; status="$(__check_if_obj_exists -cot 'file' "${bashrc}")" || return "${?}"; [ "${status}" == 'created' ] && echo ". '${bash_aliases}'" >> "${bashrc}"
    #### add lines to files if not found
    __append_line_to_file_if_not_found -vf "${bash_aliases}" "${lines_bash_aliases[@]}"
}

_init "${@}" || exit "${?}"