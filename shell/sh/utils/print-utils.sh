#!/usr/bin/env sh
#
# owner: acegene

#### descr: print cmd in a manner which can be copied and executed
#### usage: __display_cmd <CMD> <*CMD_ARGS>
#### exit: 127 if any necessary refs are missing
#### stdout: all args combined as a cmd that can be copied and executed
__display_cmd() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __is_eq __print_out __printf_q || exit "${?}"
    #### start func body
    __is_eq "${#}" '0' && return
    local args_out=''
    args_out="$(__printf_q "${1}")"
    shift
    local arg=''
    for arg in "${@}"; do
        args_out="${args_out} $(__printf_q "${arg}")"
    done
    __print_out "${args_out}"
}

#### descr: log copyable cmd to stderr and then execute it
#### usage: __exec <CMD> <*CMD_ARGS>
#### return: ERROR_CODE where ERROR_CODE is the result of the args executed as a cmd with args
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stdout: stdout of the cmd being executed
#### stderr: info log stating cmd to be executed and stderr of the cmd being executed
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__exec() {
    #### verify util prereqs
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args
    __is_not_eq "${#}" '0' || {
        __log -f "__exec: expects at least one arg"
        exit 1
    }
    #### start func body
    __log -i "executing: $(__display_cmd "${@}")"
    "${@}"
}

#### descr: log copyable cmd to stderr and then execute it; log copyable cmd to stderr on failure
#### usage: __exec_w_err <CMD> <*CMD_ARGS>
#### return: ERROR_CODE where ERROR_CODE is the result of the args executed as a cmd with args
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stdout: stdout of the cmd being executed
#### stderr: info log stating cmd to be executed and stderr of the cmd being executed; error log on cmd failure
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__exec_w_err() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args
    __is_not_eq "${#}" '0' || {
        __log -f "__exec_w_err: expects at least one arg"
        exit 1
    }
    #### start func body
    __exec "${@}"
    local error_code="${?}"
    [ "${error_code}" = '0' ] || ! __log -e "failed to execute: $(__display_cmd "${@}")" || return "${error_code}"
}

#### descr: log copyable cmd to stderr and then execute it; log copyable cmd to stderr on failure; ignore cmd stderr
#### usage: __exec_w_err_w_no_cmd_err <CMD> <*CMD_ARGS>
#### return: ERROR_CODE where ERROR_CODE is the result of the args executed as a cmd with args
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stdout: stdout of the cmd being executed
#### stderr: info log stating cmd to be executed; error log on cmd failure
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__exec_w_err_w_no_cmd_err() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args
    __is_not_eq "${#}" '0' || {
        __log -f "__exec_w_err: expects at least one arg"
        exit 1
    }
    #### start func body
    __exec "${@}" 2>/dev/null
    local error_code="${?}"
    [ "${error_code}" = '0' ] || ! __log -e "failed to execute: $(__display_cmd "${@}")" || return "${error_code}"
}

#### descr: log copyable cmd to stderr and then execute it; ignore cmd stderr
#### usage: __exec_w_no_cmd_err <CMD> <*CMD_ARGS>
#### return: ERROR_CODE where ERROR_CODE is the result of the args executed as a cmd with args
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stdout: stdout of the cmd being executed
#### stderr: info log stating cmd to be executed
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__exec_w_no_cmd_err() {
    #### verify util prereqs
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args
    __is_not_eq "${#}" '0' || {
        __log -f "__exec: expects at least one arg"
        exit 1
    }
    #### start func body
    __log -i "executing: $(__display_cmd "${@}")"
    "${@}" 2>/dev/null
}

#### descr: execute cmd; log copyable cmd to stderr on failure
#### usage: __exec_only_err <CMD> <*CMD_ARGS>
#### return: ERROR_CODE where ERROR_CODE is the result of the args executed as a cmd with args
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stdout: stdout of the cmd being executed
#### stderr: stderr of the cmd being executed; failure log on cmd failure
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__exec_only_err() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args
    __is_not_eq "${#}" '0' || {
        __log -f "__exec_w_err: expects at least one arg"
        exit 1
    }
    #### start func body
    "${@}"
    local error_code="${?}"
    [ "${error_code}" = '0' ] || ! __log -e "failed to execute: $(__display_cmd "${@}")" || return "${error_code}"
}

#### descr: execute cmd; log copyable cmd to stderr on failure; ignore cmd stderr
#### usage: __exec_only_err_w_no_cmd_err <CMD> <*CMD_ARGS>
#### return: ERROR_CODE where ERROR_CODE is the result of the args executed as a cmd with args
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stdout: stdout of the cmd being executed
#### stderr: failure log on cmd failure
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__exec_only_err_w_no_cmd_err() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args
    __is_not_eq "${#}" '0' || {
        __log -f "__exec_w_err: expects at least one arg"
        exit 1
    }
    #### start func body
    "${@}" 2>/dev/null
    local error_code="${?}"
    [ "${error_code}" = '0' ] || ! __log -e "failed to execute: $(__display_cmd "${@}")" || return "${error_code}"
}

#### descr: log to stderr with log lvl and consistent formatting
#### usage: __log [-f|-e|-w|-i|-d] <*MSGS>
#### exit: 1 if the first arg is NOT one of [-f, -e, -w, -i, -d]
#### global: log_context optional var describing where this func was called from
#### prereq: fuctions are defined: __print_err_nl
#### warning: this func must NOT directly or indirectly call any of [__are_refs, __is_ref]
#### todo: consider creating similar func that takes a format string
__log() {
    #### start func body
    case "${1}" in
    -f | --fatal) shift && __print_err_nl "FATAL: ${log_context-UNKNOWN_CONTEXT}: ${*}" ;;
    -e | --error) shift && __print_err_nl "ERROR: ${log_context-UNKNOWN_CONTEXT}: ${*}" ;;
    -w | --warning) shift && __print_err_nl "WARNING: ${log_context-UNKNOWN_CONTEXT}: ${*}" ;;
    -i | --info) shift && __print_err_nl "INFO: ${log_context-UNKNOWN_CONTEXT}: ${*}" ;;
    -d | --debug) shift && __print_err_nl "DEBUG: ${log_context-UNKNOWN_CONTEXT}: ${*}" ;;
    *)
        __print_err_nl "FATAL: ${log_context-UNKNOWN_CONTEXT}: __log given unrecognized lvl of '${1}'"
        exit 1
        ;;
    esac
}

#### descr: combine args with delimiter=' ' then print to stderr
#### usage: __print_err <*ARGS>
#### stderr: args combined with delimiter=' '
#### see: http://www.etalabs.net/sh_tricks.html
__print_err() { printf >&2 %s "${*}"; }

#### descr: combine args with delimiter=' ' then print to stderr with trailing newline
#### usage: __print_err_nl <*ARGS>
#### stderr: args combined with delimiter=' ' with trailing newline
#### see: http://www.etalabs.net/sh_tricks.html
__print_err_nl() { printf >&2 '%s\n' "${*}"; }

#### descr: combine args with delimiter=' ' then print to stdout
#### usage: __print_out <*ARGS>
#### stdout: args combined with delimiter=' '
#### see: http://www.etalabs.net/sh_tricks.html
__print_out() { printf %s "${*}"; }

#### descr: combine args with delimiter=' ' then print to stdout with trailing newline
#### usage: __print_out_nl <*ARGS>
#### stdout: args combined with delimiter=' ' with trailing newline
#### see: http://www.etalabs.net/sh_tricks.html
__print_out_nl() { printf '%s\n' "${*}"; }

#### descr: print <VAR> in a form copyable into an sh shell
#### usage: __printf_q <VAR>
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### stdouts: <ARG> representable in a copyable form for an sh shell
#### see: https://github.com/koalaman/shellcheck/wiki/SC3050
__printf_q() {
    #### verify util prereqs
    __are_refs __is_eq __log || exit "${?}"
    #### verify args
    __is_eq "${#}" '1' || {
        __log -f "__printf_q: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    printf "'%s'" "$(printf '%s' "${1}" | sed -e "s/'/'\\\\''/g")"
}
