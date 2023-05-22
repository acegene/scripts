#!/usr/bin/env sh
#
# author: acegene <acegene22@gmail.com>

#### descr: check if the given args can be located, useful to see if prereq funcs exist
#### usage: __are_refs <MAYBE_REF1> <MAYBE_REF2>
#### return: 127 if any ref can not be found
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
#### global: log_context optional var describing where this func was called from
#### stderr: if ref can not be found print error and name ref
#### warning: the dependencies of this func must NOT also call this func
__are_refs() {
    #### verify util prereqs
    command -v __log >/dev/null 2>&1 || {
        printf >&2 '%s\n' "FATAL: ${log_context-UNKNOWN_CONTEXT}: __are_refs: reference to '__log' does NOT exist"
        exit 127
    }
    #### verify args
    [ "${#}" != '0' ] || {
        __log -f "__are_refs: expects at least one arg"
        exit 1
    }
    #### start func body
    while [ "${#}" != '0' ]; do
        command -v "${1}" >/dev/null 2>&1 || {
            __log -f "reference to '${1}' does NOT exist"
            return 127
        }
        shift
    done
}

#### descr: check if <VAR> is empty
#### usage: __is_empty <VAR>
#### return: 1 if <VAR> is NOT empty
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### see: https://stackoverflow.com/a/16753536
#### warning: passing a var with the form "${VAR-}" will NOT distinguish between non-assigned or empty
__is_empty() {
    #### verify util prereqs
    __are_refs __is_eq __log || exit "${?}"
    #### verify args
    __is_eq "${#}" '1' || {
        __log -f "__is_empty: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    [ -z "${1}" ]
}

#### descr: check if <LHS> and <RHS> are exactly equal
#### usage: __is_eq <LHS> <RHS>
#### return: 1 if <LHS> is NOT the same as <RHS>
#### exit: 1 if there is NOT exactly two args
#### exit: 127 if any necessary refs are missing
__is_eq() {
    #### verify util prereqs
    __are_refs __log || exit "${?}"
    #### verify args
    [ "${#}" = '2' ] || {
        __log -f "__is_eq: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    [ "${1}" = "${2}" ]
}

#### descr: check if <ARG> is 'false'
#### usage: __is_false <ARG>
#### return: 1 if <ARG> is 'true'
#### exit: 1 if there is NOT exactly one arg
#### exit: 2 if <ARG> is NOT one of 'true' or 'false'
#### exit: 127 if any necessary refs are missing
__is_false() {
    #### verify util prereqs
    __are_refs __is_eq __log || exit "${?}"
    #### verify args
    __is_eq "${#}" '1' || {
        __log -f "__is_false: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    case "${1}" in
    true) return 1 ;;
    false) return 0 ;;
    *)
        __log -f "__is_false: given arg '${1}' rather than the required true/false."
        exit 2
        ;;
    esac
}

#### descr: check if <MAYBE_FUNC> is a recognized func
#### usage: __is_func <MAYBE_FUNC>
#### return: 127 if <MAYBE_FUNC> is NOT a recognized func
#### exit: 1 if there is NOT at least one arg
#### exit: 127 if any necessary refs are missing
__is_func() {
    #### verify util prereqs
    __are_refs __is_eq __log || exit "${?}"
    #### verify args
    __is_eq "${#}" '1' || {
        __log -f "__is_func: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    command -V "${1}" 2>/dev/null | grep -qwi func || return 127
}

#### descr: check if <ARG> is empty
#### usage: __is_int <ARG>
#### return: 1 if <ARG> is empty
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### warning: passing a var with the form "${VAR-}" will NOT distinguish between non-assigned or empty
__is_not_empty() {
    #### verify util prereqs
    __are_refs __is_eq __log || exit "${?}"
    #### verify args
    __is_eq "${#}" '1' || {
        __log -f "__is_not_empty: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    [ -n "${1}" ]
}

#### descr: check if <LHS> and <RHS> are NOT exactly equal
#### usage: __is_not_eq <LHS> <RHS>
#### return: 1 if <LHS> is the same as <RHS>
#### exit: 1 if there is NOT exactly two args
#### exit: 127 if any necessary refs are missing
__is_not_eq() {
    #### verify util prereqs
    __are_refs __is_eq __log || exit "${?}"
    #### verify args
    __is_eq "${#}" '2' || {
        __log -f "__is_not_eq: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    [ "${1}" != "${2}" ]
}

#### descr: check if <ARG> can be located; useful to see if prereq funcs exist
#### usage: __is_ref <ARG>
#### return: 127 if <ARG> can not be located
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### global: log_context optional var describing where this func was called from
#### warning: the dependencies of this func must NOT also call this func
__is_ref() {
    #### verify util prereqs
    command -v __log >/dev/null 2>&1 || {
        printf >&2 '%s\n' "FATAL: ${log_context-UNKNOWN_CONTEXT}: __is_ref: reference to '__log' does NOT exist"
        exit 127
    }
    #### verify args
    [ "${#}" = '1' ] || {
        __log -f "__is_not_empty: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    command -v "${1}" >/dev/null 2>&1 || return 127
}

#### descr: checks if <ARG> is 'true'
#### usage: __is_true <ARG>
#### return: 1 if <ARG> is 'false'
#### exit: 1 if there is NOT exactly one arg
#### exit: 2 if <ARG> is NOT one of 'true' or 'false'
#### exit: 127 if any necessary refs are missing
__is_true() {
    #### verify util prereqs
    __are_refs __is_eq __log || exit "${?}"
    #### verify args
    __is_eq "${#}" '1' || {
        __log -f "__is_not_empty: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    case "${1}" in
    true) return 0 ;;
    false) return 1 ;;
    *)
        __log -f "__is_true given arg '${1}' rather than the required true/false."
        exit 2
        ;;
    esac
}
