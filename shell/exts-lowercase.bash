#!/bin/bash

# purpose: convert all files matching case variations of 'ext_args' to use 'ext_args' themselves
# usage: _ext-to-lowercase mp4 jpeg # will rename files in the current directory, ie abc.MP4 --> abc.mp4 and def.JpEg --> def.jpeg

__parse_script_arguments() {
local ext_args_supplied='false'
while (( "${#}" )); do
    case "${1}" in
        -d|--dir) # directory to search, usage: --dir /abc/def/ghi/
            dir=$(__dir_relative_to_absolute "${2}") && shift || ! echo "invalid --dir arg" || return 1
        ;;
        -m|--maxdepth) # how deep to search through 'dir', usage: --maxdepth unsigned_integer
            local regex='^[-+]?([1-9][[:digit:]]*|0)$'
            [[ "${2}" =~ ${regex} && "${2}" -ge 0 ]] && depth="${2}" && shift || ! echo "invalid --maxdepth arg" || return 2
        ;;
        -r|--rename) # necessary to perform any file renaming, test output without this option first
            rename='true'
        ;;
        -s|--suppress) # suppress output in relation to renaming
            suppress='true'
        ;;
        *) # all other args interpreted as extensions to search for
            [[ "${ext_args_supplied}" == false ]] && ext_args_supplied='true' && ext_args=()
            ext_args+=("${1}")
        ;;        
    esac
    shift
done
for (( i = 0; i < "${#ext_args[@]}"; i++ )); do ext_args[i]="${ext_args[i]#.}"; done # strip leading dot in arguments
ext_args=( $(__remove_and_sort_array_duplicates "${ext_args[@]}") )
} # __parse_script_arguments

__print_all_other_case_variations_of_ext() {

local ext="${1}"
local ext_vars=()
local ext_vars_minus_arg=()
local num_char_combinations="$((2**${#ext}))"
local i='0'
while [ "${i}" -lt "${#ext}" ]; do
    local iii=0
    while  [ "${iii}" -lt "${num_char_combinations}" ]; do
        local k="$((2**(${i})))"
        for ((ii = 0 ; ii < "${k}"; ii++)); do ext_vars["${iii}"]+=$(echo "${ext:${i}:1}" | awk '{ print toupper($0)}' ); ((iii=iii+1)); done
        for ((ii = 0 ; ii < "${k}"; ii++)); do ext_vars["${iii}"]+=$(echo "${ext:${i}:1}" | awk '{ print tolower($0)}' ); ((iii=iii+1)); done
    done
    ((i=i+1))
done
for (( i = 0; i < "${#ext_vars[@]}"; i++ )); do [[ "${ext_vars[i]}" == "${ext}"  ]] || ext_vars_minus_arg[i]="${ext_vars[i]}"; done
__remove_and_sort_array_duplicates "${ext_vars_minus_arg[@]}"
} # __print_all_other_case_variations_of_ext

_exts_lowercase() {
local scriptpath="$( cd "$(dirname "$0")" ; pwd -P )/"
local src1="${scriptpath}_helper-funcs.bash"; local src2="${scriptpath}"_lew-source.bash
[[ -f "${src1}" ]] && . "${src1}" || ! echo "${src1} not found" || return 3
[[ -f "${src2}" ]] && . "${src2}" || ! echo "${src2} not found" || return 4

local dir="${PWD}/" # default
local depth='1' # default
local rename='false' # default
local suppress='false' # default
local ext_args=("${DEFAULT_EXTS[@]}") # default
__parse_script_arguments "${@}" || return "${?}"

echo "${ext_args[@]}"
__yes_no_prompt "Ensure ext arg(s) above are intended and only contain alphanumeric characters (y/n): " "aborting..." || return 5

for ext in "${ext_args[@]}" ; do
    local ext_variations=( $(__print_all_other_case_variations_of_ext "${ext}") )
    for ext_var in "${ext_variations[@]}" ; do
        find "${dir}" -maxdepth "${depth}" -name "*.${ext_var}" -exec sh -c 'echo "mv ${0} --> ${0%.'"${ext_var}"'}."'"${ext}" {} \;
    done
done
__yes_no_prompt "Ensure file renames suggested above are correct (y/n): " "aborting..." || return 6
echo renaming files...
for ext in "${ext_args[@]}" ; do
    local ext_variations=( $(__print_all_other_case_variations_of_ext "${ext}") )
    for ext_var in "${ext_variations[@]}" ; do
        # the following is done in two separate lines to get around windows filesystem naming rules
        find "${dir}" -maxdepth "${depth}" -name "*.${ext_var}" | while read file; do __rename_mv_operation "${file}" "${file}_backup"; done
        find "${dir}" -maxdepth "${depth}" -name "*.${ext_var}_backup" | while read file; do __rename_mv_operation "${file}" "${file%${ext_var}_backup}${ext}"; done
    done
done
echo 'renaming finished'
}

_exts_lowercase "${@}" || exit "${?}"
