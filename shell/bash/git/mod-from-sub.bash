#!/usr/bin/env bash
#
# Find the most recent module's ancestor commit for a given submodule's hash/branch
#
# author: acegene <acegene22@gmail.com>
# usage
#   * mod-from-sub --module MODULE_DIR --submodule SUB_RELATIVE_DIR
#       * find the most recent MODULE_DIR ancestor commit for HEAD in MODULE_DIR/SUB_RELATIVE_DIR
#   * mod-from-sub --submodule SUB_RELATIVE_DIR
#       * find the most recent cwd ancestor commit for HEAD in cwd/SUB_RELATIVE_DIR
#   * mod-from-sub --submodule SUB_RELATIVE_DIR --submodule-ref HEAD~1
#       * find the most recent cwd ancestor commit for HEAD~1 in cwd/SUB_RELATIVE_DIR
# prereqs
#   * newer commits of the module point to the same or newer commit of the submodule
# options
#   Primary options
#   * -m, --module=<DIR_MODULE=$PWD>             # default=cwd; path to module dir
#   * -s, --submodule=<SUBMODULE>                # relative path to submodule dir from module dir
#   * --mr, --module-ref=<COMMIT_OR_REF=origin/INFERRED_DEFAULT_BRANCH> # most recent ref to be used as a starting point on module
#   * --sr, --submodule-ref=<COMMIT_OR_REF=HEAD> # submodule commit that a module ancestor commit will be found for
#   * --module-remote=<REMOTE>                   # default=origin; remote to fetch from for module
#   Misc
#   * -h, --help                                 # display this help text and exit
# todos
#   * handle 'fatal: remote error: upload-pack: not our ref 546554554320034d3721ab2b6be7997d5019fb56'
#   * remote detection

set -u

dir_this="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && printf %s "${PWD}")" || ! printf '%s\n' "ERROR: UNKNOWN_CONTEXT: could not generate dir_this" >&2 || exit 1
base_this="$(basename -- "${BASH_SOURCE[0]}")" || ! printf '%s\n' "ERROR: UNKNOWN_CONTEXT: could not generate base_this" >&2 || exit 1
path_this="${dir_this}/${base_this}"
[ -f "${path_this}" ] && [ -d "${dir_this}" ] || ! printf '%s\n' "ERROR: UNKNOWN_CONTEXT: could not generate paths" >&2 || exit 1

# shellcheck disable=SC2034
log_context="${base_this}" # implicitly used by __log func

dir_shell="${dir_this}/../.."

for file in "${dir_shell}/bash/utils/"*.bash; do . "${file}" || exit "${?}"; done || exit "${?}"
for file in "${dir_shell}/sh/utils/"*.sh; do . "${file}" || exit "${?}"; done || exit "${?}"

__parse_args() {
    while __is_not_eq "${#}" '0'; do
        case "${1}" in
        --help | -h)
            __help
            exit "${?}"
            ;;
        #### primary options
        --module-dir | --module | --md | -m)
            dir_module="${2}"
            shift
            ;;
        --submodule-dir | --submodule | --sd | -s)
            sub="${2}"
            shift
            ;;
        --module-ref | --mr)
            ref_module="${2}"
            shift
            ;;
        --submodule-ref | --sr)
            ref_sub="${2}"
            shift
            ;;
        --module-remote | -r)
            remote_module="${2}"
            shift
            ;;
        #### handle unexpected args
        *)
            __log -e "arg '${1}' is unexpected, try '${base_this} --help'"
            return 1
            ;;
        esac
        shift
    done
}

__help() { sed >&2 '/^\([^#].*\|\)$/Q' "${path_this}"; }

#### descr: get the commit hash of <DIR_MODULE> that is the most recent ancestor of <SUBMODULE>
#### usage: __mod_from_sub <DIR_MODULE> <SUBMODULE> <REF_MODULE> <REF_SUBMODULE> <REMOTE_MODULE>
#### return: non-zero on failure to get cmd
#### exit: 1 if there is NOT between zero and two args inclusive
#### exit: 127 if any necessary refs are missing
#### stdout: commit hash of <DIR_MODULE> that is the most recent ancestor of <SUBMODULE>
#### see: https://stackoverflow.com/a/54463389/10630957
__mod_from_sub() {
    #### verify util prereqs
    __are_refs __display_cmd __exec_only_err_w_no_cmd_err __exec_w_err __git_ancestor_relationship __git_get_submodule_hash __git_oldest_commit __git_ref_to_hash __is_eq __is_not_eq __is_git_bisect_in_progress __log __print_err || exit "${?}"
    #### verify args
    __is_eq "${#}" '5' || {
        __log -f "__mod_from_sub: expects exactly five args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local dir_module="${1}"
    local sub="${2}"
    local ref_module="${3}"
    local ref_sub="${4}"
    local remote_module="${5}"
    #### determine if a fetch is necessary
    local ref_module_sub=''
    local ref_module_ancestry=''
    ref_module_sub="$(__git_get_submodule_hash "${sub}" "${ref_module}" "${dir_module}")" || ! __log -e "ref_module_sub var assignment failed" || return 1
    ref_module_ancestry="$(__git_ancestor_relationship "${ref_module_sub}" "${ref_sub}" "${dir_module}/${sub}")" || ! __log -e "ref_module_ancestry var assignment failed" || return 1
    #### check if $last_bad_submodule is actually bad (not pointing to an ancestor of $ref_sub), otherwise output $last_bad
    if [ "${ref_module_ancestry}" = 'lhs' ]; then
        __log -i "ref_module='${ref_module}' is an ancestor already; 'git fetch' must be used to look for better ancestors"
        __exec_w_err git -C "${dir_module}" fetch "${remote_module}" --quiet || return "${?}"
    fi
    #### module commits from most recent to least recent, with $first_bad and $last_bad being adjacent to the commit that git bisect determines
    local last_bad="${ref_module}"
    local first_bad=''
    local last_good=''
    local first_good=''
    first_good="$(__git_oldest_commit "${ref_module}" "${dir_module}")" || ! __log -e "first_good var assignment failed" || return 1
    #### sub commits that the above module commits point to, from most recent to least recent
    local last_bad_submodule=''
    last_bad_submodule="$(__git_get_submodule_hash "${sub}" "${last_bad}" "${dir_module}")" || ! __log -e "last_bad_submodule var assignment failed" || return 1
    local first_bad_submodule=''
    local last_good_submodule=''
    ### vars that indicate whether the associated module commit above is indeed an ancestor of $ref_sub
    local last_bad_ancestry=''
    last_bad_ancestry="$(__git_ancestor_relationship "${last_bad_submodule}" "${ref_sub}" "${dir_module}/${sub}")" || return "${?}"
    local first_bad_ancestry=''
    local last_good_ancestry=''
    #### check if $last_bad_submodule is actually bad (not pointing to an ancestor of $ref_sub), otherwise output $last_bad
    if [ "${last_bad_ancestry}" = 'lhs' ] || [ "${last_bad_ancestry}" = 'same' ]; then
        __git_ref_to_hash "${last_bad}" "${dir_module}" || return "${?}"
        return 0
    fi
    #### start git bisect
    ! __is_git_bisect_in_progress "${dir_module}" || ! __log -e "there appears to be a bisect progress; to stop it execute: $(__display_cmd git -C "${dir_module}" bisect reset)" || return 1
    __log -i "beginning git bisect"
    __exec_only_err_w_no_cmd_err git -C "${dir_module}" bisect start --no-checkout >/dev/null || return 1
    __exec_only_err_w_no_cmd_err git -C "${dir_module}" bisect bad "${last_bad}" >/dev/null || return 1
    __exec_only_err_w_no_cmd_err git -C "${dir_module}" bisect good "${first_good}" >/dev/null || return 1
    #### execute automated 'git bisect run' session and capture its stdout
    local bisect_stdout=''
    # shellcheck disable=SC2016
    bisect_stdout="$(git -C "${dir_module}" bisect run sh -c 'bisect_head_sub="$(git ls-tree BISECT_HEAD '"'${sub}'"' | sed "s/\t/ /g" | cut -d " " -f 3)"; git -C '"'${sub}'"' merge-base --is-ancestor "${bisect_head_sub}" '"'${ref_sub}'")"
    #### check whether bisect succeeded; assign first_bad based on its result then reset (abort) the bisect
    if ! __print_out_nl "${bisect_stdout}" | grep -q 'is the first bad commit'; then
        __log -e "git bisect output had unexpected form as follows:"
        __print_err "${bisect_stdout}"
        __exec_only_err_w_no_cmd_err git -C "${dir_module}" bisect reset >/dev/null || return "${?}"
        return 1
    fi
    first_bad="$(git -C "${dir_module}" show-ref --hash --verify -- refs/bisect/bad)"
    if __is_not_eq "${?}" 0; then
        __log -e "could not show-ref for 'refs/bisect/bad'"
        __exec_only_err_w_no_cmd_err git -C "${dir_module}" bisect reset >/dev/null || return "${?}"
        return 1
    fi
    __exec_only_err_w_no_cmd_err git -C "${dir_module}" bisect reset || return "${?}"
    #### $last_good is one commit earlier than $first_bad
    last_good="$(git -C "${dir_module}" rev-parse "${first_bad}"~1)" || return "${?}"
    #### determine the sub commits that $first_bad and $last_good point to
    first_bad_submodule="$(__git_get_submodule_hash "${sub}" "${first_bad}" "${dir_module}")" || return "${?}"
    last_good_submodule="$(__git_get_submodule_hash "${sub}" "${last_good}" "${dir_module}")" || return "${?}"
    #### output the associated module commit if either $first_bad_submodule or $last_good_submodule are an ancestor of $ref_sub
    first_bad_ancestry="$(__git_ancestor_relationship "${first_bad_submodule}" "${ref_sub}" "${dir_module}/${sub}")" || return "${?}" # TODO: should be redundant with last_bad check
    if [ "${first_bad_ancestry}" = 'lhs' ] || [ "${first_bad_ancestry}" = 'same' ]; then
        __git_ref_to_hash "${first_bad}" "${dir_module}" || return "${?}"
        return 0
    fi
    last_good_ancestry="$(__git_ancestor_relationship "${last_good_submodule}" "${ref_sub}" "${dir_module}/${sub}")" || return "${?}"
    if [ "${last_good_ancestry}" = 'lhs' ] || [ "${last_good_ancestry}" = 'same' ]; then
        __git_ref_to_hash "${last_good}" "${dir_module}" || return "${?}"
        return 0
    fi
    #### if things get this far there is a failure, send to stderr details for debugging
    __log -e "outputting debug details"
    __print_err_nl "    module: ${dir_module}"
    __print_err_nl "    sub: ${sub}"
    __print_err_nl "    ref_module: ${ref_module}"
    __print_err_nl "    ref_sub: ${ref_sub}"
    __print_err_nl "    remote_module: ${remote_module}"
    __print_err_nl "    last_bad: ${last_bad}"
    __print_err_nl "    first_bad: ${first_bad}"
    __print_err_nl "    last_good: ${last_good}"
    __print_err_nl "    first_good: ${first_good}"
    __print_err_nl "    last_bad_submodule: ${last_bad_submodule}"
    __print_err_nl "    first_bad_submodule: ${first_bad_submodule}"
    __print_err_nl "    last_good_submodule: ${last_good_submodule}"
    __print_err_nl "    last_bad_ancestry: ${last_bad_ancestry}"
    __print_err_nl "    first_bad_ancestry: ${first_bad_ancestry}"
    __print_err_nl "    last_good_ancestry: ${last_good_ancestry}"
    return 1
}

__main() {
    #### default vars
    local dir_module=''
    local sub=''
    local ref_module=''
    local ref_sub=''
    local remote_module=''
    #### parse args and overwrite vars
    __parse_args "${@}" || return "${?}"
    #### fill/handle empty vars
    __is_empty "${dir_module}" && dir_module="${PWD}" && __log -i "module is empty, using cwd='${dir_module}'."
    __is_empty "${sub}" && __log -e "submodule cannot be empty." && return 1
    __is_empty "${remote_module}" && remote_module='origin' && __log -i "remote_module is empty, using '${remote_module}'."
    __is_empty "${ref_module}" && ref_module="origin/$(__git_get_local_default_branch "${dir_module}" "${remote_module}")" && __log -i "ref_module is empty, using '${ref_module}'."
    __is_empty "${ref_sub}" && ref_sub='HEAD' && __log -i "ref_sub is empty, using '${ref_sub}'."
    #### find the $dir_module commit that corresponds with the $ref_sub commit on $dir_module/$sub
    local hash_module=''
    hash_module="$(__mod_from_sub "${dir_module}" "${sub}" "${ref_module}" "${ref_sub}" "${remote_module}")" || return "${?}"
    __print_err_nl "################################################################################"
    __log -i "SUCCESS: submodule='${sub}' with ref='${ref_sub}' has nearest ancestor for module='${dir_module}' on the below line."
    __print_out "${hash_module}"
    __print_err_nl ''
}

__main "${@}" || exit "${?}"
