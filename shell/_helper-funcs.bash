#!/bin/bash
# This script is not necessarily meant to be ran, for notes and educational purposes

# set -o nounset # breaks on references to unfilled variables
# set -e # will cause the scipt to exit on certain types of errors it wouldnt normally

__echo(){
    #### echo that only occurs based on variables defined from the surrounding scope
    local out=''
    local send_out='false'; local stderr='false'; local obj_set='false'
    while (( "${#}" )); do
        case "${1}" in
            --err|-e) stderr='true';;
            --verbose|-v) [ "${verbose}" == 'false' ] || send_out='true';;
            --silent|-s) [ "${silent}" == 'true' ] || send_out='true';;
            -*) # convert flags grouped as in -vrb to -v -r -b
                case "${1:1}" in
                    "") echo "ERROR: arg ${1} is unexpected" && return 2;;
                    '-') break;;
                    [a-zA-Z]) echo "ERROR: arg ${1} is unexpected" && return 2;;
                    *[!a-zA-Z]*) echo "ERROR: arg ${1} is unexpected" && return 2;;
                    *);;
                esac
                set -- 'dummy' $(for ((i=1;i<${#1};i++)); do echo "-${1:$i:1}"; done) "${@:2}" # implicit shift
                ;;
            *)
                [ "${obj_set}" == 'false' ] && obj_set='true' || ! echo "ERROR: too many objs for __echo" || return 2
                out="${1}"
                ;;
        esac
        shift
    done
    [ "${send_out}" == 'false' ] || { [ "${stderr}" == 'true' ] && >&2 printf "${out}" || printf "${out}"; }
}

__yes_no_prompt(){ # __yes_no_prompt "string to print as prompt" "string to print if answered no" && cmd-if-continue || cmd-if-not-yes
    local REGEX='^[Yy]$'
    echo; read -p "${1} " -n 1 -r; echo; ! [[ "${REPLY}" =~ ${REGEX} ]] && echo "${2}" && return 1; echo
}

__remove_and_sort_array_duplicates() { # GENRES_OUT=($(__remove_array_duplicates "${GENRES_OUT[@]}"))
    echo "${@}" | tr ' ' '\n' | sort -u | tr '\n' ' ' # might have problems with newline characters
}

__remove_array_duplicates(){
    local arr=("${@}"); local n="${#arr[@]}"
    for (( i=0; i<$((n-1)); i++ )); do
        for (( j=$((i+1)); j<$n; j++ )); do
            [[ "${arr[i]}" == "${arr[j]}" ]] && arr=(${arr[@]:0:$j} ${arr[@]:$((j+1))}) && ((j--)) && ((n--))
        done
    done
    echo ${arr[@]}
}

__source_if_found(){
    [[ -f "${1}" ]] || ! echo "file=${1} not found"
}

__check_if_obj_exists() {
    local obj=''; local type=''; local out=''
    local create='false'; local verbose='false'; local silent='false'; local send_out='false'; local obj_set='false'
    while (( "${#}" )); do
        case "${1}" in
            --type|-t)
                case "${2}" in
                    file|f|dir|d) type="${2}"; shift;;
                    *) __echo -se "ERROR: bad cmd arg combination '${1} ${2}'"; return 1;;
                esac
                ;;
            --create|-c) create='true';;
            --out|-o) send_out='true';;
            --verbose|-v) verbose='true';;
            --silent|-s) silent='true';;
            -*) # convert flags grouped as in -vrb to -v -r -b
                case "${1:1}" in
                    "") __echo -se "ERROR: arg ${1} is unexpected" && return 2;;
                    '-') break;;
                    [a-zA-Z]) __echo -se "ERROR: arg ${1} is unexpected" && return 2;;
                    *[!a-zA-Z]*) __echo -se "ERROR: arg ${1} is unexpected" && return 2;;
                    *);;
                esac
                set -- 'dummy' $(for ((i=1;i<${#1};i++)); do echo "-${1:$i:1}"; done) "${@:2}" # implicit shift
                ;;
            *)
                [ "${obj_set}" == 'false' ] && obj_set='true' || ! __echo -se "ERROR: too many objs for __check_if_obj_exists" || return 2
                obj="${1}"
                ;;
        esac
        shift
    done
    [ "${#}" -le 1 ] && for x in "${@}"; do obj="${x}"; done || ! __echo -se "ERROR: too many objs for __check_if_obj_exists" || return 2

    local cmd=''; local flag=''
    case "${type}" in
        file|f) cmd='touch'; flag='f';;
        dir|d) cmd='mkdir'; flag='d';;
        *) __echo -se "ERROR: arg type '${1}' unexpected" && return 5;;
    esac

    if [ "${create}" == 'true' ] && [ ! -"${flag}" "${obj}" ]; then
        "${cmd}" "${obj}" && __echo -ve "NOTE: created ${type}: ${obj}" || ! __echo -se "ERROR: could not create ${type}: ${obj}" || return 4
        [ "${send_out}" == 'true' ] && out='created'
    fi
    [ ! -"${flag}" "${obj}" ] && __echo -ve "ERROR: ${obj} does not exist" && return 1

    printf "${out}"
}

__rename_mv_operation(){ # __rename_mv_operation "${file_to_rename}" "${name_to_rename_file_to}"
    local lhs="${1}"; local rhs="${2}"
    [ -f "${2}" ] && echo "ERROR: mv ${lhs} -> ${rhs} failed as target exists already" && return 1
    [[ "${suppress}" == 'true' ]] || ! echo "${1} -- old" || echo "${2} -- new"
    [[ "${rename}" == 'true' ]] && mv -n "${1}" "${2}"
    return 0
}

__dir_relative_to_absolute(){
    local abs_dir="${1}"
    # echo $(readlink -f $0)
    # echo "${BASH_SOURCE[1]}"
    [ -d "${abs_dir}" ] || return 1
    abs_dir=$(cd -- "${abs_dir}"/ && printf '%s.' "$PWD"); abs_dir="${abs_dir%.}"
    [[ "${abs_dir}" != */ ]] && abs_dir="${abs_dir}/" # add trailing slash
    echo "${abs_dir}"
    [ -d "${abs_dir}" ] || return 2
}

__print_num_upper_case() {
    upper=ABCDEFGHIJKMLNOPQRSTUVWXYZ
    lower=abcdefghijklmnopqrstuvwxyz
    u=${1//[^$upper]} l=${1//[^$lower]}
    printf '%d' "${#u}"
}

__append_line_to_file_if_not_found() {
    local file=''; local lines=()
    local verbose='false'; local silent='false'
    while (( "${#}" )); do
        case "${1}" in
            --file|-f) file="${2}"; shift;;
            --line|-l) line="${2}"; shift;;
            --verbose|-v) verbose='true';;
            --silent|-s) silent='true';;
            -*) # convert flags grouped as in -vrb to -v -r -b
                case "${1:1}" in
                    '-') break;;
                    "") echo "ERROR: arg ${1} is unexpected" && return 2;;
                    [a-zA-Z]) echo "ERROR: arg ${1} is unexpected" && return 2;;
                    *[!a-zA-Z]*) echo "ERROR: arg ${1} is unexpected" && return 2;;
                    *);;
                esac
                set -- 'dummy' $(for ((i=1;i<${#1};i++)); do echo "-${1:$i:1}"; done) "${@:2}" # implicit shift
                ;;
            *) lines+=("${1}");;
        esac
        shift
    done
    for line in "${@}"; do lines+=("${line}"); done
    [ ! -f "${file}" ] && __echo -se "ERROR: file not found: ${file}"
    for line in "${lines[@]}"; do
        if ! grep -qF -- "${line}" "${file}"; then
            [ "$(tail -c 1 "${file}")" != '' ] && printf '\n' >> "${file}" # ensure trailing new line
            printf "${line}\n" >> "${file}" && __echo -ve "NOTE: '${line}' added to '${file}'" || ! __echo -se "ERROR: could not add ${line} to ${file}" || return 1
        fi
    done
}

__to-investigate-dont-use-this-function() {
    # onexit(){ while caller $((n++)); do :; done; }
    # trap onexit EXIT
    # three-fingered claw technique
    yell() { echo "$0: $*" >&2; }
    die() { yell "$*"; exit 111; }
    try() { "$@" || die "cannot $*"; }
    err() {
        echo "Error occurred:"
        awk 'NR>L-4 && NR<L+4 { printf "%-5d%3s%s\n",NR,(NR==L?">>>":""),$0 }' L=$1 $0
    }
    trap 'err $LINENO' EXIT
}

__oneliners-dont-use-this-function() {
    local scriptpath="$( cd "$(dirname "$0")" ; pwd -P )/" # return path, investigate symlink behavior
    VAR=$(echo ${VAR} |  sed 's/ *//g') # removes whitespace
}