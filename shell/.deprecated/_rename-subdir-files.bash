#!/bin/bash
#
# descr: assisted manual renaming and movement of files/dirs to parent_dir/out_dir
#
# usage: _rename-subdir-files.bash --dir /abc/def --outdir /abc/def/ will list files/dirs inside of 'dir'. Selecting a dir will then
#            list all of its files/dirs selected. Selecting a file will allow options of actions to take (rename, mv to parent). Enabling
#
# notes: 'use_out_dir' via 'TURN ON/OFF MV TO OUT_DIR' allows any selected files/dirs to be moved to 'out_dir'
#
# todos: auto creating of out_dir
#        consider to utilize $REPLY to take in ranges for select
#        consider reverse option
#        consider exempt file extensions
#        return propagation

__parse_args(){
    while (( "${#}" )); do
        case "${1}" in
            -d|--dir)
                dir=$(__dir_relative_to_absolute "${2}") && shift || ! echo "invalid --dir arg" || return 1
            ;;
            -o|--outdir) # optional directory to move renamed files into, usage: --outdir /abc/def/fds
                out_dir=$(__dir_relative_to_absolute "${2}") && out_dir_set='true' && shift || ! echo "invalid --outdir arg" || return 2
            ;;
            -m|--maxdepth)
                local regex='^[-+]?([1-9][[:digit:]]*|0)$'
                [[ "${2}" =~ ${regex} && "${2}" -ge 0 ]] && depth="${2}" && shift || ! echo "invalid --maxdepth arg" || return 3
            ;;
            -r|--rename) # necessary to perform any file renaming, test output without this option first
                rename='true'
            ;;
            -s|--suppress) # suppress output in relation to renaming
                suppress='true'
            ;;
            *)
                echo "invalid input: ${1}" && return 4
            ;;
        esac
        shift
    done
}

__target_operation_select() {
    local target="${1}"

    while true; do
        local parent_dir=$(dirname -- "$(dirname -- "${target}")")/
        local target_base=$(basename -- "${target}") && [ -d "${target}" ] && target_base="${target_base}/"

        echo "Select operation for target=${target}"
        select option in "rename" "mv ${target} to parent_dir=${parent_dir}" "${trash_dir}" "show directory contents" "ABORT"; do
            case "${option}" in
                "ABORT")
                    echo "aborting..."
                    return 0
                    ;;
                "rename")
                    "${scriptpath}"/_inject.py "${target}" || ! echo "_inject.py not found, aborting ${0}" || return 5
                    echo
                    read -e -p "" target_rename # -e allows use of arrows in input buffer
                    [[ "${#target_rename}" != 0 ]] && [[ "${target_rename}" != "${target}" ]] && __rename_mv_operation "${target}" "${target_rename}"\
                        && echo "---------------------" || echo "rename aborted..."
                    [ -f "${target}" ] || [ -d "${target}" ] || ! target="${target_rename}" || break
                    continue
                    ;;
                "mv ${target} to parent_dir=${parent_dir}")
                    __rename_mv_operation "${target}" "${parent_dir}${target_base}"
                    [ -f "${target}" ] || [ -d "${target}" ] || return 0
                    continue
                    ;;
                "${trash_dir}")
                    echo "---------------------" && [ -d "${target}" ] && ls "${target}" || echo "${target}"
                    __yes_no_prompt "Ensure above is ok to send to trash (y/n): " "${target} not sent to ${trash_dir}" || continue
                    __rename_mv_operation "${target}" "${parent_dir}${target_base}"
                    continue
                    ;;
                "show directory contents")
                    ls "$(dirname ${target})/"; continue
                    ;;
                *)
                    continue
                    ;;
            esac
        done
    done
}

_rename_subdir_files() {
    local scriptpath="$( cd "$(dirname -- "$0")" ; pwd -P )/"
    local src1="${scriptpath}_helper-funcs.bash"
    [[ -f "${src1}" ]] && . "${src1}" || ! echo "${src1} not found" || return 6

    local dir="${PWD}/" # default
    local out_dir="${dir}" # default
    local use_out_dir=0 # default
    local depth=3 # default
    local trash_dir="~/.trash/"
    local rename='false' # default
    local suppress='false' # default
    __parse_args "${@}" || return "${?}"

    while true; do
        local i=0
        local files_and_dirs=()
        local dirs=()
        local files=()
        while IFS= read -r -d $'\0' f; do files_and_dirs[i++]="$f"; done < <(find "${dir}" -maxdepth "${depth}" -type d -print0)
        while IFS= read -r -d $'\0' f; do files_and_dirs[i++]="$f"; done < <(find "${dir}" -maxdepth 1 -type f -print0)
        i=0
        while [ -d "${files_and_dirs[i]}" ]; do
            [[ "${files_and_dirs[i]}" != */ ]] && files_and_dirs[i]="${files_and_dirs[i]}/"
            [[ "${files_and_dirs[i]}" != "${out_dir}"* ]] && dirs+=( "${files_and_dirs[i]}" )
            ((i=i+1))
        done
        while [ -f "${files_and_dirs[i]}" ]; do
            files+=( "${files_and_dirs[i]}" )
            ((i=i+1))
        done
        echo
        select target in "../" "TURN ON/OFF MV TO OUT_DIR" "----    files    ----" "${files[@]}" "---- DIRECTORIES ----" "${dirs[@]:1}" "---- CURRENT DIR ----"\
            "${dirs[0]}" "ABORT"; do
            case "${target}" in
                "ABORT")
                    echo "aborting..."
                    return 0
                    ;;
                "../")
                    dir="$(dirname "$dir")/"
                    break
                    ;;
                "TURN ON/OFF MV TO OUT_DIR")
                    [[ "${out_dir}" == '' ]] && echo "ERROR: out_dir is not set, will not allow mv to out_dir" && continue
                    [[ "${use_out_dir}" == 0 ]] && use_out_dir=1 || use_out_dir=0
                    [[ "${use_out_dir}" == 1 ]] && ([ -d  "${out_dir}" ] || mkdir "${out_dir}")
                    echo "use_out_dir=${use_out_dir} out_dir=${out_dir}"
                    continue
                    ;;
                "---- CURRENT DIR ----"|"---- DIRECTORIES ----"|"----    files    ----")
                    continue
                    ;;
                *)
                    [ "${target}" == "" ] && echo "ERROR: bad value passed: ${REPLY}" && continue
                    [ "${use_out_dir}" == 1 ] && __rename_mv_operation "${target}" "${out_dir}""$(basename -- "${target}")" && break
                    [ "${target}" == "${dir}" ] && echo && __target_operation_select "${dir}" && break
                    [ -d "${target}" ] && dir="${target}" && break
                    [ -f "${target}" ] && echo "---------------------" && __target_operation_select "${target}" && break
                    echo "ERROR: the target=${target} was not handled correctly"
                    break
                    ;;
            esac
        done
    done
}

_rename_subdir_files "${@}" || exit "${?}"
