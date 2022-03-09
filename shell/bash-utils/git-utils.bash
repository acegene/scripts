#!/usr/bin/env bash
#
# owner: acegene
#
# deps: * math-utils.sh # __is_between_inclusive_int
#       * misc-utils.bash # __join
#       * misc-utils.sh # __yes_no_prompt
#       * path-utils.sh # __is_dir
#       * print-utils.sh # __execute_w_err __log __print_err_nl __print_out
#       * validation-utils.sh # __are_refs __is_empty __is_eq __is_not_empty
#
# todos: * consider how to use: git lfs migrate import --skip-fetch --yes HEAD

#### descr: check if <REPO> is clean
#### usage: __is_repo_clean <REPO>
#### return: 1 if <REPO> is not clean
#### exit: 1 if there is NOT exactly one non-empty arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_empty __is_eq __is_not_empty __log
__is_repo_clean() {
    #### verify prereqs for execution
    __are_refs __is_empty __is_eq __is_not_empty __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_repo_clean: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__is_repo_clean: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1}" status --porcelain --untracked-files=all)"
}

#### descr: check if <REPO> is clean; submodules are ignored
#### usage: __is_repo_clean_ignore_submodules <REPO>
#### return: 1 if <REPO> is not clean; submodules are ignored
#### exit: 1 if there is NOT exactly one non-empty arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_empty __is_eq __is_not_empty __log
__is_repo_clean_ignore_submodules() {
    #### verify prereqs for execution
    __are_refs __is_empty __is_eq __is_not_empty __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_repo_clean_ignore_submodules: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__is_repo_clean_ignore_submodules: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1}" status --porcelain --ignore-submodules)"
}

#### descr: check if <REPO_PATH> is clean; submodules and untracked files are ignored
#### usage: __is_repo_clean_ignore_submodules_ignore_untracked <REPO_PATH>
#### return: 1 if <REPO_PATH> is not clean; submodules and untracked files are ignored
#### exit: 1 if there is NOT exactly one non-empty arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_empty __is_eq __is_not_empty __log
__is_repo_clean_ignore_submodules_ignore_untracked() {
    #### verify prereqs for execution
    __are_refs __is_empty __is_eq __is_not_empty __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_repo_clean_ignore_submodules_ignore_untracked: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__is_repo_clean_ignore_submodules_ignore_untracked: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1}" status --porcelain --ignore-submodules --untracked-files=no)"
}

#### descr: check if <REPO> is clean; untracked files are considered
#### usage: __is_repo_clean_ignore_untracked <REPO>
#### return: 1 if <REPO> is not clean; untracked files are considered
#### exit: 1 if there is NOT exactly one non-empty arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_empty __is_eq __is_not_empty __log
__is_repo_clean_ignore_untracked() {
    #### verify prereqs for execution
    __are_refs __is_empty __is_eq __is_not_empty __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_repo_clean_ignore_untracked: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__is_repo_clean_ignore_untracked: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    __is_empty "$(git -C "${1}" status --porcelain --untracked-files=no)"
}

#### descr: clones a repo given its <REPO_PATH> and <REPO_URL>
#### usage: __repo_clone <REPO_PATH> <REPO_URL>
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT exactly one non-empty arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __execute_w_err __is_dir __is_eq __is_not_empty __log __yes_no_prompt
__repo_clone() {
    #### verify prereqs for execution
    __are_refs __execute_w_err __is_dir __is_eq __is_not_empty __log __yes_no_prompt || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '2' || {
        __log -f "__repo_clone: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__repo_clone: repo_path var must NOT be empty'
        exit 1
    }
    __is_not_empty "${2}" || {
        __log -f '__repo_clone: repo_url var must NOT be empty'
        exit 1
    }
    #### start func body
    local repo_path="${1}"
    local repo_url="${2}"
    #### prompt user to delete $repo_path if it exists
    if __is_dir "${repo_path}"; then
        __yes_no_prompt "PROMPT: Path ${repo_path} already exists. Do you want to erase it and clone from scratch? y/n: " && { __execute_w_err rm -rf -- "${repo_path}" || return "${?}"; }
    fi
    #### create $repo_path if it does not exist
    if ! __is_dir "${repo_path}"; then
        __execute_w_err mkdir "${repo_path}" || return "${?}"
        __execute_w_err cd "${repo_path}" || return "${?}"
        __execute_w_err git clone "${repo_url}" . || return "${?}"
    fi
}

#### descr: checkout <REPO_BRANCH> and align with <REPO_REMOTE>/<REPO_BRANCH> for <REPO_PATH>
#### usage: __repo_pull_latest <REPO_PATH>
#### usage: __repo_pull_latest <REPO_PATH> <REPO_BRANCH> <REPO_REMOTE>
#### param: $1 repo_path
#### param: $2 repo_branch: default=master
#### param: $3 repo_remote: default=origin
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT between one and three args inclusive
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __execute_w_err __is_between_inclusive_int __is_not_empty __is_repo_clean_ignore_submodules __log __yes_no_prompt
__repo_pull_latest() {
    #### verify prereqs for execution
    __are_refs __execute_w_err __is_not_empty __is_repo_clean_ignore_submodules __log __yes_no_prompt || exit "${?}"
    #### verify args for execution
    __is_between_inclusive_int "${#}" '1' '3' || {
        __log -f "__repo_pull_latest: expects between one and three args: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__repo_pull_latest: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    local repo_path="${1}"
    local repo_branch="${2-master}"
    local repo_remote="${3-origin}"
    #### prompt user on whether to overwrite changes to repo if they exist
    if ! __is_repo_clean_ignore_submodules "${repo_path}"; then
        __execute_w_err git -C "${repo_path}" status --ignore-submodules || return "${?}"
        if ! __yes_no_prompt "PROMPT: ${repo_path} is not clean, see git status above. Should we delete/overwrite this content? (y/n): "; then
            __log -i "FAILURE: skipping pull of '${repo_path}'"
            return 1
        fi
    fi
    #### forcefully change repo to desired branch and sync it with upstream
    __execute_w_err git -C "${repo_path}" fetch -f --update-head-ok "${repo_remote}" "${repo_branch}:${repo_branch}" || return "${?}"
    __execute_w_err git -C "${repo_path}" checkout -f "${repo_branch}" || return "${?}"
    __execute_w_err git -C "${repo_path}" reset --hard HEAD || return "${?}"
    __log -i "__repo_pull_latest: repo '${repo_path}' checked out branch '${repo_branch}' and aligned with latest '${repo_remote}/${repo_branch}'"
}

#### descr: pulls all initialized submodules for a given <REPO_PATH_W_SUBMODULES>
#### usage: __repo_pull_latest_submodules <REPO_PATH_W_SUBMODULES>
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT exactly one non-empty arg
#### exit: 127 if any necessary refs are missing
#### prereqs: functions are defined: __are_refs __execute_w_err __is_between_inclusive_int __is_not_empty __join __log __yes_no_prompt || exit "${?}"
#### warning: this function has alot of subtleties that are easy to overlook wen editing
#### todo: consider named pipe/file descriptor rather than 3
__repo_pull_latest_submodules() {
    #### verify prereqs for execution
    __are_refs __execute_w_err __is_between_inclusive_int __is_not_empty __join __log __yes_no_prompt || exit "${?}"
    #### verify args for execution
    __is_between_inclusive_int "${#}" '1' '3' || {
        __log -f "__repo_pull_latest_submodules: expects between one and three args: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__repo_pull_latest_submodules: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    local repo_path="${1}"
    local repo_branch="${2-master}"
    local repo_remote="${3-origin}"
    #### collect data regarding which submodules are clean (uncommited/untracked)
    #### results are newline separated matching 'clean-submodule_path' or 'dirty-submodule_path'
    local are_submodules_clean=''
    # shellcheck disable=SC2016
    are_submodules_clean="$(git -C "${repo_path}" submodule --quiet foreach '[ -z "$(git status --porcelain --untracked-files=all)" ] && printf %s\\n "clean-${path}" || printf %s\\n "dirty-${path}"')" || return "${?}"
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
            __execute_w_err git -C "${repo_path}/${submodule_path_tmp}" status
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
    printf >&2 %s\\n "*******Beginning submodule pulling for ${repo_path}*******"
    local submodules_pull_case_pattern=''
    local submodules_skip_case_pattern=''
    submodules_pull_case_pattern="'$(__join "'|'" "${submodules_pull[@]}")'" || return "${?}"
    submodules_skip_case_pattern="'$(__join "'|'" "${submodules_skip[@]}")'" || return "${?}"
    # shellcheck disable=SC2016
    git -C "${repo_path}" submodule foreach ':
case "${path}" in
'"${submodules_pull_case_pattern}"') git fetch -f --update-head-ok '"${repo_remote} ${repo_branch}:${repo_branch}"' && git checkout -f master && git reset --hard HEAD ;;
'"${submodules_skip_case_pattern}"') printf >&2 %s\\n "INFO: '"${BASE_THIS}"': skipping ${path}" ;;
*) printf >&2 %s\\n "ERROR: '"${BASE_THIS}"': unexpected submodule input: ${path}"; return 1 ;;
esac' || return "${?}"
}

#### descr: rebase <REPO_PATH> onto <REPO_REMOTE>/<REPO_BRANCH> with prompts and error handling
#### usage: __repo_rebase <REPO_PATH>
#### usage: __repo_rebase <REPO_PATH> <REPO_BRANCH> <REPO_REMOTE>
#### param: $1 repo_path
#### param: $2 repo_branch: default=master
#### param: $3 repo_remote: default=origin
#### return: 2 on skip due user prompt in cases where repo is clean
#### return: 3 on rebase failure
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT between one and three args inclusive
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __execute_w_err __is_between_inclusive_int __is_not_empty __is_repo_clean_ignore_submodules __log __yes_no_prompt
#### todo: properly handle robust rebase abort
__repo_rebase() {
    #### verify prereqs for execution
    __are_refs __execute_w_err __is_between_inclusive_int __is_not_empty __is_repo_clean_ignore_submodules __log __yes_no_prompt || exit "${?}"
    #### verify args for execution
    __is_between_inclusive_int "${#}" '1' '3' || {
        __log -f "__repo_rebase: expects between one and three args: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__repo_rebase: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    local repo_path="${1}"
    local repo_branch="${2-master}"
    local repo_remote="${3-origin}"
    #### prompt user on whether to skip if repo is unclean
    if ! __is_repo_clean_ignore_submodules "${repo_path}"; then
        __execute_w_err git -C "${repo_path}" status --ignore-submodules || return "${?}"
        if ! __yes_no_prompt "PROMPT: repo '${repo_path}' is not clean, see git status above. Should we delete/overwrite this content? (y/n): "; then
            __log -i "FAILURE: repo '${repo_path}' the rebase was skipped"
            return 2
        fi
    fi
    #### attempt rebase and fallback to abort when non zero error code occurs
    __execute_w_err git -C "${repo_path}" fetch --quiet "${repo_remote}" "${repo_branch}" || return "${?}"
    __execute_w_err git -C "${repo_path}" reset --quiet HEAD || return "${?}"
    if ! __execute_w_err git -C "${repo_path}" rebase "${repo_remote}/${repo_branch}"; then
        __execute_w_err git -C "${repo_path}" rebase --abort
        __log -i "FAILURE: repo '${repo_path}' the rebase FAILED onto '${repo_remote}/${repo_branch}'"
        return 3
    fi
    __log -i "__repo_rebase: repo '${repo_path}' was rebased onto '${repo_remote}/${repo_branch}'"
}

#### descr: rebase each submodule for <REPO_PATH> onto <REPO_REMOTE>/<REPO_BRANCH> with prompts and error handling
#### usage: __repo_rebase_submodules <REPO_PATH>
#### usage: __repo_rebase_submodules <REPO_PATH> <REPO_BRANCH> <REPO_REMOTE>
#### param: $1 repo_path
#### param: $2 repo_branch: default=master
#### param: $3 repo_remote: default=origin
#### return: 2 if skips occur due to user prompt in cases where repo is clean
#### return: 3 if rebase failures occur
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT between one and three args inclusive
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __execute_w_err __is_between_inclusive_int __is_not_empty __log __print_err_nl __yes_no_prompt
#### todo: consider named pipe/file descriptor rather than 3
#### todo: properly handle robust rebase abort
__repo_rebase_submodules() {
    #### verify prereqs for execution
    __are_refs __execute_w_err __is_between_inclusive_int __is_not_empty __log __print_err_nl __yes_no_prompt
    #### verify args for execution
    __is_between_inclusive_int "${#}" '1' '3' || {
        __log -f "__repo_rebase_submodules: expects between one and three args: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__repo_rebase_submodules: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    local repo_path="${1}"
    local repo_branch="${2-master}"
    local repo_remote="${3-origin}"
    #### get custom parsable status on submodules (sms)
    local status_sms_initial=''
    status_sms_initial="$(__repo_status_submodules "${repo_path}")" || return "${?}"
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
            __execute_w_err git -C "${repo_path}/${sm_path}" status --ignore-submodules || return "${?}"
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
            __execute_w_err git -C "${repo_path}/${sm_path}" fetch --quiet "${repo_remote}" "${repo_branch}" || return "${?}"
            __execute_w_err git -C "${repo_path}/${sm_path}" reset --quiet HEAD || return "${?}"
            if __execute_w_err git -C "${repo_path}/${sm_path}" rebase "${repo_remote}/${repo_branch}"; then
                status_sms_success+=("SUCCESS ${sm_status}")
            else
                __execute_w_err git -C "${repo_path}/${sm_path}" rebase --abort
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
    __log -i "__repo_rebase_submodules: repo '${repo_path}' submodules were rebased onto '${repo_remote}/${repo_branch}' successfully"
}

#### descr: setup git credentials for <REPO_PATH>
#### usage: __repo_set_git_credentials <REPO_PATH>
#### usage: __repo_set_git_credentials <REPO_PATH> <GIT_NAME> <GIT_EMAIL>
#### param: $1 repo_path
#### param: $2 git_name: default=''
#### param: $3 git_email: default=''
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT between one and three args inclusive
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __execute_w_err __is_between_inclusive_int __is_empty __is_not_empty __log
__repo_set_git_credentials() {
    #### verify prereqs for execution
    __are_refs __execute_w_err __is_between_inclusive_int __is_empty __is_not_empty __log || exit "${?}"
    #### verify args for execution
    __is_between_inclusive_int "${#}" '1' '3' || {
        __log -f "__repo_set_git_credentials: expects between one and three args: given '${#}': args='${*}'"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__repo_set_git_credentials: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    local repo_path="${1}"
    local git_name="${2-}"
    local git_email="${3-}"
    #### setup git credential
    __print_err "*******Git Credentials for ${repo_path}*******"
    ## setup git username
    if __is_empty "${git_name}"; then
        __print_err "PROMPT: Insert your <Name Surname> like: Marco Ross: "
        read -r git_name || return "${?}"
    fi
    __execute_w_err git -C "${repo_path}" config user.name "${git_name}" || return "${?}"
    ## setup git email
    if __is_empty "${git_email}"; then
        __print_err "PROMPT: Insert your email used in BMW Github: "
        read -r git_email || return "${?}"
    fi
    __execute_w_err git -C "${repo_path}" config user.email "${git_email}" || return "${?}"
    #### provide details to user
    __log -i "The Username and Password will be specific to ${repo_path}"
    __log -i "Your Git credentials have been saved in: ${repo_path}.git/config"
}

#### descr: setup git credentials for <REPO_PATH1> <REPO_PATH2> ... <REPO_PATHN>
#### usage: __repos_set_git_credentials <REPO_PATH1> <REPO_PATH2> ... <REPO_PATHN>
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_not_eq __is_not_empty __join __log __repo_set_git_credentials __yes_no_prompt
__repos_set_git_credentials() {
    #### verify prereqs for execution
    __are_refs __is_not_empty __is_not_eq __join __log __repo_set_git_credentials __yes_no_prompt || exit "${?}"
    #### verify args for execution
    __is_not_eq "${#}" '0' || {
        __log -f "__repos_set_git_credentials: expects at least one arg"
        exit 1
    }
    __is_not_empty "${1}" || {
        __log -f '__repos_set_git_credentials: repo_path var must NOT be empty'
        exit 1
    }
    #### start func body
    local repo_path="${1}"
    __log -i "Listing repos to alter git credentials: '$(__join "' '" "${@}")'"
    if [ "${#}" != '1' ] && __yes_no_prompt "PROMPT: would you like to use the same git user.name and user.email for all repos above? (y/n): "; then
        local git_name=''
        local git_email=''
        __print_err "PROMPT: Insert your <Name Surname> like: Marco Ross: "
        read -r git_name || return "${?}"
        __print_err "PROMPT: Insert your email used in BMW Github: "
        read -r git_email || return "${?}"
        while (("${#}")); do
            __repo_set_git_credentials "${repo_path}" "${git_name}" "${git_email}" || return "${?}"
            shift
        done
    else
        while (("${#}")); do
            __repo_set_git_credentials "${repo_path}" || return "${?}"
            shift
        done
    fi
}

#### descr: for each submodule in <REPO_PATH> write one line of details to stdout
#### usage: __repo_status_submodules <REPO_PATH>
#### return: !0 on failure of any cmd execution
#### exit: 1 if there is NOT exactly one arg
#### stdout: for each submodule: branch/state hash clean/dirty path
#### note: untracked files are considered
#### prereq: funcs are defined: __are_refs __is_eq __log
__repo_status_submodules() {
    #### verify prereqs for execution
    __are_refs __is_eq __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__repo_status_submodules: expects exactly one args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    # shellcheck disable=SC2016
    git -C "${1}" submodule --quiet foreach ':
__private_submodule_details="$(git rev-parse --abbrev-ref HEAD)"
__private_submodule_details="${__private_submodule_details} ${sha1}"
__private_submodule_details="${__private_submodule_details} $([ -z "$(git status --porcelain --untracked-files=all)" ] && printf %s "clean" || printf %s "dirty")"
__private_submodule_details="${__private_submodule_details} ${path}"
printf %s\\n "${__private_submodule_details}"'
}
