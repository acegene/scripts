#!/bin/bash

__parse_args(){
    while (( "${#}" )); do
        case "${1}" in
            -d|--dir) dir=$(__dir_relative_to_absolute "${2}") && shift || ! echo "invalid --dir arg" || return 1 ;;
            -m|--maxdepth)
                local regex='^[-+]?([1-9][[:digit:]]*|0)$'
                [[ "${2}" =~ ${regex} && "${2}" -ge 0 ]] && depth="${2}" && shift || ! echo "invalid --maxdepth arg" || return 3
            ;;
            -r|--remove) remove='true' ;; # will not remove any files unless this option is set
            *) echo "ERROR: invalid input: ${1}" && return 3 ;;        
        esac
        shift
    done
    return 0
}

_rm_mac_junk() {
    local scriptpath="$( cd "$(dirname -- "$0")" ; pwd -P )/"
    local src1="${scriptpath}_helper-funcs.bash"
    [[ -f "${src1}" ]] && . "${src1}" || ! echo "${src1} not found" || return 4

    local dir="${PWD}/" # default
    local depth=5 # default
    local remove='false' # default
    local total_file_size='0'
    local file_size='0'
    __parse_args "${@}" || return "${?}"

    unset mac_files_print i
    while IFS= read -r -d $'\0' f; do mac_files_print[i++]="$f"; done < <(find "${dir}" -maxdepth "${depth}" -type f  -regex '.+/\._.+' -print0 | xargs -0n 1 du -0k | sort -nz | cut -z -f2 | xargs -0 du -0sh)
    for file in "${mac_files_print[@]}"; do echo "${file}"; done
    __yes_no_prompt "Remove above files? (y/n)" "...aborting" || return 5
    for file in "${mac_files_print[@]}"; do [[ "${remove}" == 'true' ]] && echo "${file}" | cut -f2 | xargs -d '\n' rm -- || echo "option --remove to allow deletion"; done
}

_rm_mac_junk "${@}" || return "${?}"