#!/usr/bin/env bash
#
# author: acegene <acegene22@gmail.com>
# deps
#   * shell/sh/utils/*.sh
# todos
#   * consider how to use: git lfs migrate import --skip-fetch --yes HEAD

#### descr: Print to stdout the ancestor relationship of <LHS_GIT_REF> and <RHS_GIT_REF>
#### usage: __git_ancestor_relationship <LHS_GIT_REF> <RHS_GIT_REF> <REPO_DIR=$PWD>
#### return: non-zero if either <LHS_GIT_REF> or <RHS_GIT_REF> could not be converted to a hash
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### see: https://stackoverflow.com/a/18345268
__git_ancestor_relationship() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __is_eq __is_not_eq __log __print_out || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '2' '3' || {
        __log -f "__git_ancestor_relationship: expects two or three args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local lhs="${1}"
    local rhs="${2}"
    local repo_dir="${3-"${PWD}"}"
    #### convert given git refs to git hashes
    lhs="$(__git_ref_to_hash "${lhs}" "${repo_dir}")" || return "${?}"
    rhs="$(__git_ref_to_hash "${rhs}" "${repo_dir}")" || return "${?}"
    #### print 'same' and return if lhs = rhs are equal
    __is_eq "${lhs}" "${rhs}" && __print_out 'same' && return
    #### determine if lhs is ancestor of rhs
    git -C "${repo_dir}" merge-base --is-ancestor "${lhs}" "${rhs}"
    local is_lhs_ancestor_exit_code="${?}"
    if __is_eq "${is_lhs_ancestor_exit_code}" '0'; then
        __print_out 'lhs'
        return
    elif __is_not_eq "${is_lhs_ancestor_exit_code}" '1'; then
        __log -e "error in execution: git merge-base --is-ancestor '${lhs}' '${rhs}'"
    fi
    #### determine if rhs is ancestor of lhs
    git -C "${repo_dir}" merge-base --is-ancestor "${rhs}" "${lhs}"
    local is_rhs_ancestor_exit_code="${?}"
    if __is_eq "${is_rhs_ancestor_exit_code}" '0'; then
        __print_out 'rhs'
        return
    elif __is_not_eq "${is_rhs_ancestor_exit_code}" '1'; then
        __log -e "error in execution: git merge-base --is-ancestor '${lhs}' '${rhs}'"
    fi
    #### neither is an ancestor of eachother
    __print_out 'neither'
}

#### descr: get the default branch name as stored locally
#### usage: __git_get_local_default_branch <REPO_DIR=$PWD> <REPO_REMOTE=origin>
#### return: non-zero on failure to get cmd
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### stdout: branch name, with remote removed e.g. master
#### see: https://stackoverflow.com/a/44750379
#### warning: this may not work repos that were not cloned
#### warning: the remote may be out of sync with the local since this is usually only updated at clone time
__git_get_local_default_branch() {
    #### verify prereqs for execution
    __are_refs __is_between_inclusive_int __log || exit "${?}"
    #### verify args for execution
    __is_between_inclusive_int "${#}" '0' '2' || {
        __log -f "__git_get_local_default_branch: expects between zero and two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    git -C "${1-"${PWD}"}" rev-parse --abbrev-ref "${2-origin}"/HEAD | sed "s|${2-origin}/||"
}

#### descr: get the default branch name by querying the remote
#### usage: __git_get_remote_default_branch <REPO_DIR=$PWD> <REPO_REMOTE=origin>
#### return: non-zero on failure to get default branch
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### stdout: branch name, with remote removed e.g. master
#### see: https://stackoverflow.com/a/50056710
__git_get_remote_default_branch() {
    #### verify prereqs for execution
    __are_refs __is_between_inclusive_int __log || exit "${?}"
    #### verify args for execution
    __is_between_inclusive_int "${#}" '0' '2' || {
        __log -f "__git_get_remote_default_branch: expects between one and two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    git -C "${1-"${PWD}"}" remote show origin | sed -n '/HEAD branch/s/.*: //p'
}

#### descr: find the oldest commit relative to <GIT_REF>
#### usage: __git_oldest_commit <GIT_REF=HEAD> <REPO_DIR=$PWD>
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__git_oldest_commit() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '2' || {
        __log -f "__git_oldest_commit: expects between zero and two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    git -C "${2-"${PWD}"}" log --format="%H" --reverse "${1-HEAD}" | head -n 1
}

#### descr: convert <GIT_REF> to its matching git-ref
#### usage: __git_ref_to_hash <GIT_REF> <REPO_DIR=$PWD>
#### return: 1 if <GIT_REF> could not be converted to a hash
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### see: https://stackoverflow.com/a/1862542
__git_ref_to_hash() {
    #### verify util prereqs
    __are_refs __exec_only_err __is_between_inclusive_int __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '1' '2' || {
        __log -f "__git_ref_to_hash: expects one or two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __exec_only_err git -C "${2-"${PWD}"}" rev-list -n 1 "${1}" || ! __log -e '__git_ref_to_hash failed' || return 1
}

#### descr: print to stdout the hash of <SUBMODULE_DIR> stored in <MODULE_REF> for <MODULE_DIR>
#### usage: __git_get_submodule_hash <SUBMODULE_DIR> <MODULE_REF=HEAD> <MODULE_DIR=$PWD>
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### stdout: the hash of <SUBMODULE_DIR> stored in <MODULE_REF> for <MODULE_DIR>
#### note: relative paths for <SUBMODULE_DIR> must be given wrt <MODULE_DIR>
__git_get_submodule_hash() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '1' '3' || {
        __log -f "__git_get_submodule_hash: expects between one and three args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    git -C "${3-"${PWD}"}" ls-tree "${2-HEAD}" "${1}" | sed 's/\t/ /g' | cut -d ' ' -f 3
}

#### descr: check if a 'git bisect' is in progress
#### usage: __is_git_bisect_in_progress <REPO_DIR=$PWD>
#### return: non-zero if there is no bisect in progress
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__is_git_bisect_in_progress() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '1' || {
        __log -f "__is_git_bisect_in_progress: expects either zero or one args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    git -C "${1-"${PWD}"}" bisect log >/dev/null 2>&1
}

#### descr: check if <MAYBE_COMMIT> is a git ref that has an associated git commit id
#### usage: __is_git_commit <MAYBE_COMMIT> <REPO_DIR=$PWD>
#### return: 1 if <MAYBE_COMMIT> is a git ref that does NOT have an associated git commit id
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__is_git_commit() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '1' '2' || {
        __log -f "__is_git_commit: expects one or two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    git -C "${2-"${PWD}"}" cat-file -e "${1}"^'{commit}'
}

#### descr: check if <REPO_DIR> is clean
#### usage: __is_repo_clean <REPO_DIR=$PWD>
#### return: 1 if <REPO_DIR> is not clean
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__is_repo_clean() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __is_empty __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '1' || {
        __log -f "__is_repo_clean: expects either zero or one args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1-"${PWD}"}" status --porcelain --untracked-files=all)"
}

#### descr: check if <REPO_DIR> is clean; submodules are ignored
#### usage: __is_repo_clean_ignore_submodules <REPO_DIR=$PWD>
#### return: 1 if <REPO_DIR> is not clean; submodules are ignored
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__is_repo_clean_ignore_submodules() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __is_empty __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '1' || {
        __log -f "__is_repo_clean_ignore_submodules: expects either zero or one args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1-"${PWD}"}" status --porcelain --ignore-submodules)"
}

#### descr: check if <REPO_DIR> is clean; submodules and untracked files are ignored
#### usage: __is_repo_clean_ignore_submodules_ignore_untracked <REPO_DIR=$PWD>
#### return: 1 if <REPO_DIR> is not clean; submodules and untracked files are ignored
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__is_repo_clean_ignore_submodules_ignore_untracked() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __is_empty __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '1' || {
        __log -f "__is_repo_clean_ignore_submodules_ignore_untracked: expects either zero or one args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1-"${PWD}"}" status --porcelain --ignore-submodules --untracked-files=no)"
}

#### descr: check if <REPO_DIR> is clean; untracked files are considered
#### usage: __is_repo_clean_ignore_untracked <REPO_DIR=$PWD>
#### return: 1 if <REPO_DIR> is not clean; untracked files are considered
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__is_repo_clean_ignore_untracked() {
    #### verify util prereqs
    __are_refs __is_empty __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '1' || {
        __log -f "__is_repo_clean_ignore_untracked: expects either zero or one args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1-"${PWD}"}" status --porcelain --untracked-files=no)"
}

#### descr: clones a repo given its <REPO_DIR> and <REPO_URL>
#### usage: __repo_clone <REPO_DIR> <REPO_URL>
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__repo_clone() {
    #### verify util prereqs
    __are_refs __exec_w_err __is_dir __is_eq __log __yes_no_prompt || exit "${?}"
    #### verify args
    __is_eq "${#}" '2' || {
        __log -f "__repo_clone: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local repo_dir="${1}"
    local repo_url="${2}"
    #### prompt user to delete $repo_dir if it exists
    if __is_dir "${repo_dir}"; then
        __yes_no_prompt "PROMPT: Path ${repo_dir} already exists. Do you want to erase it and clone from scratch? y/n: " && { __exec_w_err rm -rf -- "${repo_dir}" || return "${?}"; }
    fi
    #### create $repo_dir if it does not exist
    if ! __is_dir "${repo_dir}"; then
        __exec_w_err mkdir "${repo_dir}" || return "${?}"
        __exec_w_err cd "${repo_dir}" || return "${?}"
        __exec_w_err git clone "${repo_url}" . || return "${?}"
    fi
}

#### descr: checkout <REPO_BRANCH> and align with <REPO_REMOTE>/<REPO_BRANCH> for <REPO_DIR>
#### usage: __repo_pull_latest <REPO_DIR> <REPO_BRANCH=INFERRED_LOCAL_BRANCH> <REPO_REMOTE=origin>
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__repo_pull_latest() {
    #### verify util prereqs
    __are_refs __exec_w_err __is_repo_clean_ignore_submodules __log __yes_no_prompt || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '3' || {
        __log -f "__repo_pull_latest: expects between zero and three args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local repo_dir="${1-"${PWD}"}"
    local repo_branch=''
    repo_branch="${2-"$(__git_get_local_default_branch "${repo_dir}")"}" || return "${?}"
    local repo_remote="${3-origin}"
    #### prompt user on whether to overwrite changes to repo if they exist
    if ! __is_repo_clean_ignore_submodules "${repo_dir}"; then
        __exec_w_err git -C "${repo_dir}" status --ignore-submodules || return "${?}"
        if ! __yes_no_prompt "PROMPT: ${repo_dir} is not clean, see git status above. Should we delete/overwrite this content? (y/n): "; then
            __log -i "FAILURE: skipping pull of '${repo_dir}'"
            return 1
        fi
    fi
    #### forcefully change repo to desired branch and sync it with upstream
    __exec_w_err git -C "${repo_dir}" fetch -f --update-head-ok "${repo_remote}" "${repo_branch}:${repo_branch}" || return "${?}"
    __exec_w_err git -C "${repo_dir}" checkout -f "${repo_branch}" || return "${?}"
    __exec_w_err git -C "${repo_dir}" reset --hard HEAD || return "${?}"
    __log -i "__repo_pull_latest: repo '${repo_dir}' checked out branch '${repo_branch}' and aligned with latest '${repo_remote}/${repo_branch}'"
}

#### descr: pulls all initialized submodules for a given <REPO_DIR>
#### usage: __repo_pull_latest_submodules <REPO_DIR=$PWD> <REPO_BRANCH=INFERRED_LOCAL_BRANCH> <REPO_REMOTE=origin>
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### warning: this function has alot of subtleties that are easy to overlook wen editing
#### todo: consider named pipe/file descriptor rather than 3
__repo_pull_latest_submodules() {
    #### verify util prereqs
    __are_refs __exec_w_err __is_between_inclusive_int __join __log __yes_no_prompt || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '3' || {
        __log -f "__repo_pull_latest_submodules: expects between zero and three args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local repo_dir="${1-"${PWD}"}"
    local repo_branch=''
    repo_branch="${2-"$(__git_get_local_default_branch "${repo_dir}")"}" || return "${?}"
    local repo_remote="${3-origin}"
    #### collect data regarding which submodules are clean (uncommited/untracked)
    #### results are newline separated matching 'clean-submodule_path' or 'dirty-submodule_path'
    local are_submodules_clean=''
    # shellcheck disable=SC2016
    are_submodules_clean="$(git -C "${repo_dir}" submodule --quiet foreach '[ -z "$(git status --porcelain --untracked-files=all)" ] && printf %s\\n "clean-${path}" || printf %s\\n "dirty-${path}"')" || return "${?}"
    #### prompt user regarding dirty modules and record whether they should be skipped
    #### regarding peculiar nested reads: https://stackoverflow.com/a/46373806
    local submodules_skip=()
    local submodules_pull=()
    local submodule_clean_path=''
    while IFS= read -r submodule_clean_path <&3; do
        local submodule_path_tmp=''
        submodule_path_tmp="$(__print_out "${submodule_clean_path}" | sed 's/^.\{6\}//')" || return "${?}"
        local submodule_clean_status=''
        submodule_clean_status="$(__print_out "${submodule_clean_path}" | cut -c-5)" || return "${?}"
        case "${submodule_clean_status}" in
        clean) submodules_pull+=("${submodule_path_tmp}") ;;
        dirty)
            __exec_w_err git -C "${repo_dir}/${submodule_path_tmp}" status
            if __yes_no_prompt "PROMPT: ${submodule_path_tmp} is not clean, see git status above. Should we delete/overwrite this content? (y/n): "; then
                submodules_pull+=("${submodule_path_tmp}")
            else
                __log -i "skipping any file altering for ${submodule_path_tmp}"
                submodules_skip+=("${submodule_path_tmp}")
            fi
            ;;
        *) __log -e "Unexpected submodule clean status '${submodule_clean_status}'." && return 1 ;;
        esac
    done 3<<<"${are_submodules_clean}"
    #### pull all submodules to clean master unless they were specified as to be skipped
    printf >&2 %s\\n "*******Beginning submodule pulling for ${repo_dir}*******"
    local submodules_pull_case_pattern=''
    local submodules_skip_case_pattern=''
    submodules_pull_case_pattern="'$(__join "'|'" "${submodules_pull[@]}")'" || return "${?}"
    submodules_skip_case_pattern="'$(__join "'|'" "${submodules_skip[@]}")'" || return "${?}"
    # shellcheck disable=SC2016
    git -C "${repo_dir}" submodule foreach ':
case "${path}" in
'"${submodules_pull_case_pattern}"') git fetch -f --update-head-ok '"${repo_remote} ${repo_branch}:${repo_branch}"' && git checkout -f master && git reset --hard HEAD ;;
'"${submodules_skip_case_pattern}"') printf >&2 %s\\n "INFO: '"${log_context-UNKNOWN_CONTEXT}"': skipping ${path}" ;;
*) printf >&2 %s\\n "ERROR: '"${log_context-UNKNOWN_CONTEXT}"': unexpected submodule input: ${path}"; return 1 ;;
esac' || return "${?}"
}

#### descr: rebase <REPO_DIR> onto <REPO_REMOTE>/<REPO_BRANCH> with prompts and error handling
#### usage: __repo_rebase <REPO_DIR=$PWD> <REPO_BRANCH=INFERRED_LOCAL_BRANCH> <REPO_REMOTE=origin>
#### return: 2 on skip due user prompt in cases where repo is clean
#### return: 3 on rebase failure
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### todo: properly handle robust rebase abort
__repo_rebase() {
    #### verify util prereqs
    __are_refs __exec_w_err __is_between_inclusive_int __is_repo_clean_ignore_submodules __log __yes_no_prompt || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '3' || {
        __log -f "__repo_rebase: expects between zero and three args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local repo_dir="${1-"${PWD}"}"
    local repo_branch=''
    repo_branch="${2-"$(__git_get_local_default_branch "${repo_dir}")"}" || return "${?}"
    local repo_remote="${3-origin}"
    #### prompt user on whether to skip if repo is unclean
    if ! __is_repo_clean_ignore_submodules "${repo_dir}"; then
        __exec_w_err git -C "${repo_dir}" status --ignore-submodules || return "${?}"
        if ! __yes_no_prompt "PROMPT: repo '${repo_dir}' is not clean, see git status above. Should we delete/overwrite this content? (y/n): "; then
            __log -i "FAILURE: repo '${repo_dir}' the rebase was skipped"
            return 2
        fi
    fi
    #### attempt rebase and fallback to abort when non zero error code occurs
    __exec_w_err git -C "${repo_dir}" fetch --quiet "${repo_remote}" "${repo_branch}" || return "${?}"
    __exec_w_err git -C "${repo_dir}" reset --quiet HEAD || return "${?}"
    if ! __exec_w_err git -C "${repo_dir}" rebase "${repo_remote}/${repo_branch}"; then
        __exec_w_err git -C "${repo_dir}" rebase --abort
        __log -i "FAILURE: repo '${repo_dir}' the rebase FAILED onto '${repo_remote}/${repo_branch}'"
        return 3
    fi
    __log -i "__repo_rebase: repo '${repo_dir}' was rebased onto '${repo_remote}/${repo_branch}'"
}

#### descr: rebase each submodule for <REPO_DIR> onto <REPO_REMOTE>/<REPO_BRANCH> with prompts and error handling
#### usage: __repo_rebase_submodules <REPO_DIR=$PWD> <REPO_BRANCH=INFERRED_LOCAL_BRANCH> <REPO_REMOTE=origin>
#### return: 2 if skips occur due to user prompt in cases where repo is clean
#### return: 3 if rebase failures occur
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
#### todo: consider named pipe/file descriptor rather than 3
#### todo: properly handle robust rebase abort
__repo_rebase_submodules() {
    #### verify util prereqs
    __are_refs __exec_w_err __is_between_inclusive_int __is_not_eq __log __print_err_nl __yes_no_prompt
    #### verify args
    __is_between_inclusive_int "${#}" '0' '3' || {
        __log -f "__repo_rebase_submodules: expects between zero and three args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local repo_dir="${1-"${PWD}"}"
    local repo_branch=''
    repo_branch="${2-"$(__git_get_local_default_branch "${repo_dir}")"}" || return "${?}"
    local repo_remote="${3-origin}"
    #### get custom parsable status on submodules (sms)
    local status_sms_initial=''
    status_sms_initial="$(__repo_status_submodules "${repo_dir}")" || return "${?}"
    #### prompt user on whether to skip any non clean submodules
    local sm_status=''
    local status_sms_rebase_or_skip=()
    while IFS= read -r sm_status <&3; do
        local sm_clean_status=''
        local sm_path=''
        sm_clean_status="$(printf '%s' "${sm_status}" | cut -d ' ' -f3)" || return "${?}"
        sm_path="$(printf '%s' "${sm_status}" | cut -d ' ' -f4-)" || return "${?}"
        case "${sm_clean_status}" in
        clean) status_sms_rebase_or_skip+=("rebase ${sm_status}") ;;
        dirty)
            __exec_w_err git -C "${repo_dir}/${sm_path}" status --ignore-submodules || return "${?}"
            if __yes_no_prompt "PROMPT: submodule '${sm_path}' is not clean, see git status above. Should we delete/overwrite this content? (y/n): "; then
                status_sms_rebase_or_skip+=("rebase ${sm_status}")
            else
                status_sms_rebase_or_skip+=("skip__ ${sm_status}")
            fi
            ;;
        *) __log -e "Unexpected submodule status '${sm_status}' which gives unexpected clean status of '${sm_clean_status}'." && return 1 ;;
        esac
    done 3<<<"${status_sms_initial}"
    #### attempt rebase of submodules not set to be skipped; record success/failure/skipped for each
    local status_sms_failure=()
    local status_sms_skipped=()
    local status_sms_success=()
    for sm_status in "${status_sms_rebase_or_skip[@]}"; do
        local sm_skip_status=''
        local sm_path=''
        sm_skip_status="$(printf '%s' "${sm_status}" | cut -d ' ' -f1)" || return "${?}"
        sm_path="$(printf '%s' "${sm_status}" | cut -d ' ' -f5-)" || return "${?}"
        case "${sm_skip_status}" in
        rebase)
            __exec_w_err git -C "${repo_dir}/${sm_path}" fetch --quiet "${repo_remote}" "${repo_branch}" || return "${?}"
            __exec_w_err git -C "${repo_dir}/${sm_path}" reset --quiet HEAD || return "${?}"
            if __exec_w_err git -C "${repo_dir}/${sm_path}" rebase "${repo_remote}/${repo_branch}"; then
                status_sms_success+=("SUCCESS ${sm_status}")
            else
                __exec_w_err git -C "${repo_dir}/${sm_path}" rebase --abort
                status_sms_failure+=("FAILURE ${sm_status}")
            fi
            ;;
        skip__)
            __log -i "skipping interacting with repo '${sm_path}'"
            status_sms_skipped+=("SKIPPED ${sm_status}")
            ;;
        *) __log -e "Unexpected submodule status '${sm_status}' which gives unexpected rebase status of '${sm_skip_status}'." && return 1 ;;
        esac
    done
    #### print results
    __log -i "see key for the submodule statuses on the following line:"
    __print_err_nl '    rebase_result skip original_head original_hash original_clean_status submodule_path'
    if __is_not_eq "${#status_sms_success[@]}" '0'; then
        __log -i "the following submodules have SUCCEEDED"
        for sm_status in "${status_sms_success[@]}"; do __print_err_nl "    ${sm_status}"; done
    fi
    if __is_not_eq "${#status_sms_skipped[@]}" '0'; then
        __log -w "the following submodules were SKIPPED"
        for sm_status in "${status_sms_skipped[@]}"; do __print_err_nl "    ${sm_status}"; done
    fi
    if __is_not_eq "${#status_sms_failure[@]}" '0'; then
        __log -e "the following submodules have FAILED"
        for sm_status in "${status_sms_failure[@]}"; do __print_err_nl "    ${sm_status}"; done
    fi
    __is_eq "${#status_sms_failure[@]}" '0' || ! __log -e "there were ${#status_sms_failure[@]} failures" || return 3
    __is_eq "${#status_sms_skipped[@]}" '0' || ! __log -e "there were ${#status_sms_skipped[@]} skips" || return 2
    __log -i "__repo_rebase_submodules: repo '${repo_dir}' submodules were rebased onto '${repo_remote}/${repo_branch}' successfully"
}

#### descr: setup git credentials for <REPO_DIR>
#### usage: __repo_set_git_credentials <REPO_DIR=$PWD> <GIT_NAME=''> <GIT_EMAIL=''>
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__repo_set_git_credentials() {
    #### verify util prereqs
    __are_refs __exec_w_err __is_between_inclusive_int __is_empty __log __print_err || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '3' || {
        __log -f "__repo_set_git_credentials: expects between zero and three args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local repo_dir="${1-"${PWD}"}"
    local git_name="${2-}"
    local git_email="${3-}"
    #### setup git credential
    __print_err "*******Git Credentials for ${repo_dir}*******"
    ## setup git username
    if __is_empty "${git_name}"; then
        __print_err "PROMPT: Insert your <Name Surname> like: Marco Ross: "
        read -r git_name || return "${?}"
    fi
    __exec_w_err git -C "${repo_dir}" config user.name "${git_name}" || return "${?}"
    ## setup git email
    if __is_empty "${git_email}"; then
        __print_err "PROMPT: Insert your email used in BMW Github: "
        read -r git_email || return "${?}"
    fi
    __exec_w_err git -C "${repo_dir}" config user.email "${git_email}" || return "${?}"
    #### provide details to user
    __log -i "The Username and Password will be specific to ${repo_dir}"
    __log -i "Your Git credentials have been saved in: ${repo_dir}.git/config"
}

#### descr: setup git credentials for <*REPO_PATHS>
#### usage: __repos_set_git_credentials <*REPO_PATHS>
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### exit: 127 if any necessary refs are missing
__repos_set_git_credentials() {
    #### verify util prereqs
    __are_refs __is_not_eq __join __log __repo_set_git_credentials __yes_no_prompt || exit "${?}"
    #### verify args
    __is_not_eq "${#}" '0' || {
        __log -f "__repos_set_git_credentials: expects at least one arg"
        exit 1
    }
    #### start func body
    __log -i "Listing repos to alter git credentials: '$(__join "' '" "${@}")'"
    if [ "${#}" != '1' ] && __yes_no_prompt "PROMPT: would you like to use the same git user.name and user.email for all repos above? (y/n): "; then
        local git_name=''
        local git_email=''
        __print_err "PROMPT: Insert your <Name Surname> like: Marco Ross: "
        read -r git_name || return "${?}"
        __print_err "PROMPT: Insert your email used in BMW Github: "
        read -r git_email || return "${?}"
        while __is_not_eq "${#}" '0'; do
            local repo_dir="${1}"
            shift
            __repo_set_git_credentials "${repo_dir}" "${git_name}" "${git_email}" || return "${?}"
        done
    else
        __repo_set_git_credentials "${1}" || return "${?}"
    fi
}

#### descr: for each submodule in <REPO_DIR> write one line of details to stdout
#### usage: __repo_status_submodules <REPO_DIR=$PWD>
#### return: !0 on failure of any cmd execution
#### exit: 1 if wrong number of args
#### stdout: for each submodule: branch/state hash clean/dirty path
#### note: untracked files are considered
__repo_status_submodules() {
    #### verify util prereqs
    __are_refs __is_between_inclusive_int __log || exit "${?}"
    #### verify args
    __is_between_inclusive_int "${#}" '0' '1' || {
        __log -f "__repo_status_submodules: expects either zero or one args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    # shellcheck disable=SC2016
    git -C "${1-"${PWD}"}" submodule --quiet foreach ':
__private_submodule_details="$(git rev-parse --abbrev-ref HEAD)"
__private_submodule_details="${__private_submodule_details} ${sha1}"
__private_submodule_details="${__private_submodule_details} $([ -z "$(git status --porcelain --untracked-files=all)" ] && printf %s "clean" || printf %s "dirty")"
__private_submodule_details="${__private_submodule_details} ${path}"
printf %s\\n "${__private_submodule_details}"'
}
