#!/usr/bin/env sh
#
# owner: acegene
#
# deps: * print-utils.sh # __log __print_out
#       * validation-utils.sh # __are_refs __is_eq

#### descr: check if <INT> is between <LOWER_BOUND> and <UPPER_BOUND>; bounds are excluded
#### usage: __is_between_int <INT> <LOWER_BOUND> <UPPER_BOUND>
#### return: 1 if <INT> is NOT between <LOWER_BOUND> and <UPPER_BOUND>; bounds are excluded
#### exit: 1 if there is NOT exactly two args
#### exit: 2 if any arg is NOT an int
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __is_int __log
__is_between_exclusive_int() {
    #### verify prereqs for execution
    __are_refs __is_eq __is_int __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '3' || {
        __log -f "__is_between_exclusive_int: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    __is_int "${1}" || {
        __log -f "__is_between_exclusive_int: expects int: given '${1}'"
        exit 2
    }
    __is_int "${2}" || {
        __log -f "__is_between_exclusive_int: expects int: given '${2}'"
        exit 2
    }
    __is_int "${3}" || {
        __log -f "__is_between_exclusive_int: expects int: given '${3}'"
        exit 2
    }
    #### start func body
    [ "${1}" -gt "${2}" ] && [ "${1}" -lt "${3}" ]
}

#### descr: check if <INT> is between <LOWER_BOUND> and <UPPER_BOUND>; bounds are included
#### usage: __is_between_inclusive_int <INT> <LOWER_BOUND> <UPPER_BOUND>; bounds are included
#### return: 1 if <INT> is NOT between <LOWER_BOUND> and <UPPER_BOUND>
#### exit: 1 if there is NOT exactly two args
#### exit: 2 if any arg is NOT an int
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __is_int __log
__is_between_inclusive_int() {
    #### verify prereqs for execution
    __are_refs __is_eq __is_int __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '3' || {
        __log -f "__is_between_inclusive_int: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    __is_int "${1}" || {
        __log -f "__is_between_inclusive_int: expects int: given '${1}'"
        exit 2
    }
    __is_int "${2}" || {
        __log -f "__is_between_inclusive_int: expects int: given '${2}'"
        exit 2
    }
    __is_int "${3}" || {
        __log -f "__is_between_inclusive_int: expects int: given '${3}'"
        exit 2
    }
    #### start func body
    [ "${1}" -ge "${2}" ] && [ "${1}" -le "${3}" ]
}

#### descr: check if int <LHS> is greater than int <RHS>
#### usage: __is_greater_int <LHS> <RHS>
#### return: 1 if <LHS> is NOT greater than <RHS>
#### exit: 1 if there is NOT exactly two args
#### exit: 2 if any arg is NOT an int
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __is_int __log
__is_greater_int() {
    #### verify prereqs for execution
    __are_refs __is_eq __is_int __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '2' || {
        __log -f "__is_greater_int: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    __is_int "${1}" || {
        __log -f "__is_greater_int: expects int: given '${1}'"
        exit 2
    }
    __is_int "${2}" || {
        __log -f "__is_greater_int: expects int: given '${2}'"
        exit 2
    }
    #### start func body
    [ "${1}" -gt "${2}" ]
}

#### descr: checks if <MAYBE_INT> is an integer
#### usage: __is_int <MAYBE_INT>
#### return: 1 if <MAYBE_INT> is NOT in a form like [0, 1, 01, -01, -21]
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __log
__is_int() {
    #### verify prereqs for execution
    __are_refs __is_eq __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_int: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    case "${1#[-]}" in
    *[!0123456789]*) return 1 ;;
    '') return 1 ;;
    *) return 0 ;;
    esac
}

#### descr: check if int <LHS> is less than int <RHS>
#### usage: __is_less_int <LHS> <RHS>
#### return: 1 if <LHS> is NOT less than <RHS>
#### exit: 1 if there is NOT exactly two args
#### exit: 2 if any arg is NOT an int
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __is_int __log
__is_less_int() {
    #### verify prereqs for execution
    __are_refs __is_eq __is_int __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '2' || {
        __log -f "__is_less_int: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    __is_int "${1}" || {
        __log -f "__is_less_int: expects int: given '${1}'"
        exit 2
    }
    __is_int "${2}" || {
        __log -f "__is_less_int: expects int: given '${2}'"
        exit 2
    }
    #### start func body
    [ "${1}" -lt "${2}" ]
}

#### descr: check if <ARG> is a positive float
#### usage: __is_pos_float <ARG>
#### return: 0 only when <ARG> is a positive float
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __log __print_out
__is_pos_float() {
    #### verify prereqs for execution
    __are_refs __is_eq __log __print_out || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_pos_float: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __print_out "${1}" | grep '^[0-9]*[.]\?[0-9]*$' | grep -q '..*'
}
