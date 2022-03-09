#!/usr/bin/env sh
#
# owner: acegene
#
# deps: * validation-utils.sh # __are_refs __is_eq __is_not_eq

#### descr: print cmd in a manner which can be copied and executed
#### usage: __display_cmd <CMD> <--ARG1> <ARG2>
#### exit: 127 if any necessary refs are missing
#### stdout: all args combined as a cmd that can be copied and executed
#### prereq: funcs are defined: __are_refs __print_out __is_eq __printf_q
__display_cmd() {
    #### verify prereqs for execution
    __are_refs __print_out __is_eq __printf_q || exit "${?}"
    #### start func body
    __is_eq "${#}" '0' && return
    __private___display_cmd_args_out="$(__printf_q "${1}")"
    shift
    for __private___display_cmd_arg in "${@}"; do
        __private___display_cmd_args_out="${__private___display_cmd_args_out} $(__printf_q "${__private___display_cmd_arg}")"
    done
    __print_out "${__private___display_cmd_args_out}"
}

#### descr: display copyable cmd to stderr and then execute it
#### usage: __execute <CMD> <--ARG1> <ARG2>
#### return: ERROR_CODE where ERROR_CODE is the result of the args executed as a cmd with args
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stderr: execution log plus failure log on cmd failure
#### prereq: funcs are defined: __are_refs __display_cmd __execute __is_not_eq __log
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__execute() {
    #### verify prereqs for execution
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args for execution
    __is_not_eq "${#}" '0' || {
        __log -f "__execute: expects at least one arg"
        exit 1
    }
    #### start func body
    __log -i "executing: $(__display_cmd "${@}")"
    "${@}"
}

#### descr: display copyable cmd to stderr and then execute it; log to stderr on failure
#### usage: __execute_w_err <CMD> <--ARG1> <ARG2>
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stderr: execution log plus failure log on cmd failure
#### prereq: funcs are defined: __are_refs __display_cmd __execute __is_not_eq __log
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__execute_w_err() {
    #### verify prereqs for execution
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args for execution
    __is_not_eq "${#}" '0' || {
        __log -f "__execute_w_err: expects at least one arg"
        exit 1
    }
    #### start func body
    __execute "${@}"
    __private___execute_w_err_error_code="${?}"
    [ "${__private___execute_w_err_error_code}" = '0' ] || ! __log -e "failed to execute: $(__display_cmd "${@}")" || return "${__private___execute_w_err_error_code}"
}

#### descr: executes cmd; log to stderr on failure
#### usage: __execute_w_err <CMD> <--ARG1> <ARG2>
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### stderr: failure log on cmd failure
#### prereq: funcs are defined: __are_refs __display_cmd __is_not_eq __log
#### warning: only works with basic cmds; i.e no special symbols (redirections, &&, ||, ;)
__execute_w_err_q() {
    #### verify prereqs for execution
    __are_refs __display_cmd __is_not_eq __log || exit "${?}"
    #### verify args for execution
    __is_not_eq "${#}" '0' || {
        __log -f "__execute_w_err: expects at least one arg"
        exit 1
    }
    #### start func body
    "${@}"
    __private___execute_w_err_q_error_code="${?}"
    [ "${__private___execute_w_err_q_error_code}" = '0' ] || ! __log -e "failed to execute: $(__display_cmd "${@}")" || return "${__private___execute_w_err_q_error_code}"
}

#### descr: log to stderr with log lvl and consistent formatting
#### usage: __log [-f|-e|-w|-i|-d] <MSG>
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
#### usage: __print_err <VAR1>
#### usage: __print_err <VAR1> <VAR2> <VAR3>
#### stderr: args combined with delimiter=' '
#### note: http://www.etalabs.net/sh_tricks.html
__print_err() { printf >&2 %s "${*}"; }

#### descr: combine args with delimiter=' ' then print to stderr with trailing newline
#### usage: __print_err_nl <VAR1>
#### usage: __print_err_nl <VAR1> <VAR2> <VAR3>
#### stderr: args combined with delimiter=' ' with trailing newline
#### note: http://www.etalabs.net/sh_tricks.html
__print_err_nl() { printf >&2 '%s\n' "${*}"; }

#### descr: combine args with delimiter=' ' then print to stdout
#### usage: __print_out <VAR1>
#### usage: __print_out <VAR1> <VAR2> <VAR3>
#### stdout: args combined with delimiter=' '
#### note: http://www.etalabs.net/sh_tricks.html
__print_out() { printf %s "${*}"; }

#### descr: combine args with delimiter=' ' then print to stdout with trailing newline
#### usage: __print_out_nl <VAR1>
#### usage: __print_out_nl <VAR1> <VAR2> <VAR3>
#### stdout: args combined with delimiter=' ' with trailing newline
#### note: http://www.etalabs.net/sh_tricks.html
__print_out_nl() { printf '%s\n' "${*}"; }

#### descr: print <VAR> in a form copyable into an sh shell
#### usage: __printf_q <VAR>
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### stdouts: <ARG> representable in a copyable form for an sh shell
#### note: https://github.com/koalaman/shellcheck/wiki/SC3050
#### prereq: funcs are defined: __are_refs __is_eq __log
__printf_q() {
    #### verify prereqs for execution
    __are_refs __is_eq __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__printf_q: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    printf "'%s'" "$(printf '%s' "${1}" | sed -e "s/'/'\\\\''/g")"
}
