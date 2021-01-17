#!/bin/bash

# purpose: assisted manual renaming of files that match glob 'pattern' arg, then moves to 'outdir' if defined
# usage: _manual_mv.bash *.txt --outdir /abc/def/ will assist renaming of all .txt files in current dir and place files into /abc/def/

# TODO: show why the regex is failing
# TODO: consider purging from display files already renamed (maybe refresh entire search as an option after purge)
# TODO: when using -o arg you are stuck moving a file unless you enter nothing

__parse_script_arguments() {
local out_dir_set='false'
local num_other_args=0
while (( "${#}" )); do
    case "${1}" in
        -d|--dir) # directory to search, usage: --dir /abc/def/ghi/
            dir=$(__dir_relative_to_absolute "${2}") && shift || ! echo "invalid --dir arg" || return 1
        ;;
        -o|--outdir) # optional directory to move renamed files into, usage: --outdir /abc/def/fds
            out_dir=$(__dir_relative_to_absolute "${2}") && out_dir_set='true' && shift || ! echo "invalid --outdir arg" || return 2
        ;;
        -m|--maxdepth) # how deep to search through 'dir', usage: --maxdepth unsigned_integer
            local regex='^[-+]?([1-9][[:digit:]]*|0)$'
            [[ "${2}" =~ ${regex} && "${2}" -ge 0 ]] && depth="${2}" && shift || ! echo "invalid --maxdepth arg" || return 3
        ;;
        -r|--rename) # necessary to perform any file renaming, test output without this option first
            rename='true'
        ;;
        -s|--suppress) # suppress output in relation to renaming
            suppress='true'
        ;;
        *) # maximum one arg accepted to search files to rename, usage: "*.java" will find all .java files
            [[ "${num_other_args}" == 0 ]] && pattern="${1}" && num_other_args=1 || ! echo "invalid: expects max one glob arg" || return 4
        ;;        
    esac
    shift
done
[[ "${out_dir_set}" == 'false' ]] && out_dir="${dir}"
return 0
} # __parse_script_arguments

_manual_mv () {
local scriptpath="$( cd "$(dirname -- "$0")" ; pwd -P )/"
local src1="${scriptpath}_helper-funcs.bash"
[[ -f "${src1}" ]] && . "${src1}" || ! echo "${src1} not found" || return 5

local dir="${PWD}/" # default
local out_dir="${dir}" # default
local depth='1' # default
local pattern='*' # default
local rename='false' # default
local suppress='false' # default
__parse_script_arguments "${@}" || return "${?}"

echo "searching dir=${dir} for pattern=${pattern} with depth=${depth} to move to out_dir=${out_dir}"; echo
local break_while=0
while [ "${break_while}" != 1 ]; do
    unset files i
    while IFS= read -r -d $'\0' f; do files[i++]="$f"; done < <(find "${dir}" -maxdepth "${depth}" -type f -name "${pattern}" -printf '%P\0')
    select file in "${files[@]}" "Abort script"; do
        case "${file}" in
            ${pattern})
                echo "${dir}${file}"
                local base_file="$(basename -- "${file}")"
                local dir_file=$(__dir_relative_to_absolute "$(dirname -- "${dir}${file}")")
                "${scriptpath}"_inject.py "${base_file}"  || ! echo "_inject.py not found, aborting ${0}" || return 6
                echo
                read -e -p "" rename_input # -e allows use of arrows in input buffer
                local regex='^[]0-9a-zA-Z,!.\ _[$-]+$'
                [[ "${rename_input}" =~ ${regex} ]] || ! echo "ERROR: invalid characters passed to regex" || break
                [[ "${#rename_input}" != 0 ]] && ([[ "${rename_input}" != "${base_file}" ]] || [[ "${out_dir}" != "${dir}" ]])\
                    || ! echo "rename aborted..." || continue
                [[ "${out_dir}" != "${dir}" ]] && __rename_mv_operation "${dir}${file}" "${out_dir}${rename_input}"\
                    || __rename_mv_operation "${dir}${file}" "${dir_file}${rename_input}"
                echo "---------------------" && break
                ;;
            "Abort script")
                echo "aborting..."
                break_while=1
                break
                ;;
            *)
                echo "This is not a number"
                ;;
        esac
    done
done
} # _manual-mv

_manual_mv "${@}" || exit "${?}"