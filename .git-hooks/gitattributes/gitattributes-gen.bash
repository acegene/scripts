#!/bin/bash
#
# gitattributes-gen.bash
#
# descr: autogen this repos root .gitattributes file
#
# usage:
#
# todos: * curl doesnt return a proper error

set -u

PATH_THIS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)/"$(basename -- "${BASH_SOURCE[0]}")""
DIR_THIS="$(dirname -- "${PATH_THIS}")"
BASE_THIS="$(basename -- "${PATH_THIS}")"
[ -f "${PATH_THIS}" ] && [ -d "${DIR_THIS}" ] && [ -f "${DIR_THIS}/${BASE_THIS}" ] || ! >&2 echo "ERROR: could not generate paths" || exit 1

################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################
# yymmdd: 210228
# generation cmd on the following line:
# python "${GWSPY}/write-btw.py" "-t" "bash" "-w" "${GWS}/repos/media/.git-hooks/gitattributes/gitattributes-gen.bash" "-r" "${GWSSH}/_helper-funcs.bash" "-x" "__echo" "__check_if_objs_exist"

__echo(){
    #### echo that can watch the silent and verbose variables from the scope it was called from
    local out=''
    local send_out='false'; local stderr='false'; local obj_set='false'; local end_char='\n'
    while (( "${#}" )); do
        case "${1}" in
            --err|-e) stderr='true';;
            --verbose|-v) [ "${verbose}" == 'false' ] || send_out='true';;
            --silent|-s) [ "${silent}" == 'true' ] || send_out='true';;
            --no-newline|-n) end_char='';;
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
    [ "${send_out}" == 'false' ] || { [ "${stderr}" == 'true' ] && >&2 printf "${out}${end_char}" || printf "${out}${end_char}"; }
}

__check_if_objs_exist() {
    local objs=(); local type=''; local out=''
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
            *) objs+=("${1}");;
        esac
        shift
    done

    local cmd=''; local flag=''
    case "${type}" in
        file|f) cmd='touch'; flag='f';;
        dir|d) cmd='mkdir'; flag='d';;
        *) __echo -se "ERROR: arg type '${1}' unexpected" && return 5;;
    esac
    for ((i=0; i<${#objs[@]}; i++)); do
        if [ "${create}" == 'true' ] && [ ! -"${flag}" "${objs[$i]}" ]; then
            "${cmd}" "${objs[$i]}" && __echo -ve "INFO: created ${type}: ${objs[$i]}" || ! __echo -se "ERROR: could not create ${type}: ${objs[$i]}" || return 4
            [ "${send_out}" == 'true' ] && out='created'
        fi
        [ ! -"${flag}" "${objs[$i]}" ] && __echo -ve "ERROR: ${objs[$i]} does not exist" && return 1
    done
    printf "${out}"
}
################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################

_gitattributes_gen() {
    #### config vars
    local gitattributes_string='c++,common,java,matlab,python,swift,vim,visualstudio' # comma separated list
    #### hardcoded vars
    ## paths
    local dir_repo="$(cd -- "${DIR_THIS}" && cd -- "$(git rev-parse --show-toplevel)" && echo "${PWD}")" && [ "${dir_repo}" != '' ] || ! __echo -se "ERROR: dir_repo=''" || return 1
    ## files
    local file_gitattributes="${dir_repo}/.gitattributes"
    local file_gitattributes_backup="${DIR_THIS}/.gitattributes-backup"
    local file_gitattributes_prepend="${DIR_THIS}/.gitattributes-prepend"
    local file_gitattributes_append="${DIR_THIS}/.gitattributes-append"
    #### check if files exist, assign to variables accordingly
    if __check_if_objs_exist --verbose --type 'file' "${file_gitattributes_prepend}" "${file_gitattributes_append}"; then
        local gitattributes_append=$(cat "${file_gitattributes_append}")
        local gitattributes_prepend=$(cat "${file_gitattributes_prepend}")
    else
        local gitattributes_append=''
        local gitattributes_prepend=''
    fi
    ## url to import gitattributes templates from https://github.com/alexkaratarakis/gitattributes
    local url='https://gitattributes.io/api/'
    #### curl auto concatenated template
    local errors=''
    local curled_gitattributes=''; curled_gitattributes=$(curl --silent --insecure "${url}${gitattributes_string}") || errors="curl request failed, perhaps a bad url\n"
    [ "${errors}" == '' ] && errors=$(echo "${curled_gitattributes}" | grep 'ERROR:')
    #### overwrite content of root .gitattributes file
    if [ "${errors}" == '' ]; then
        printf "${gitattributes_prepend}\n${curled_gitattributes}\n${gitattributes_append}" > "${file_gitattributes_backup}"
        printf "${gitattributes_prepend}\n${curled_gitattributes}\n${gitattributes_append}" > "${file_gitattributes}"
    else
        echo "WARNING: ${PATH_THIS}: using ${file_gitattributes_backup} due to curl errors below"
        printf "ERROR: ${PATH_THIS}: ${errors}"
        __check_if_objs_exist --verbose --type 'file' "${file_gitattributes_backup}" || return 1
        cat "${file_gitattributes_backup}" > "${file_gitattributes}"
    fi
}

_gitattributes_gen "${@}" || exit "${?}"