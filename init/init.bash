#!/bin/bash
#
# descr: adds sourcing of this repo's src.bash in ~/.bash_aliases

set -u

_init() {
    #### hardcoded vars
    ## dirs
    local script_path="${BASH_SOURCE[0]}"
    local dir_script="$(cd "$(dirname "${script_path}")"; pwd -P)" && [ "${dir_script}" != '' ] || ! __echo -se "ERROR: dir_script=''" || return 1
    local dir_repo="$(cd "${dir_script}" && cd $(git rev-parse --show-toplevel) && echo ${PWD})" && [ "${dir_repo}" != '' ] || ! __echo -se "ERROR: dir_repo=''" || return 1
    ## includes
    . "${dir_repo}/shell/__supplemental-functions.bash" || ! echo "ERROR: sourcing failed" || return 1
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