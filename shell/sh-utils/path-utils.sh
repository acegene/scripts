#!/usr/bin/env sh
#
# owner: acegene
#
# deps: * print-utils.sh # __log __print_err __print_out_nl
#       * validation-utils.sh # __are_refs __is_empty __is_eq

#### descr: checks if <FILE> has a trailing newline, and if not, appends one
#### usage: __file_append_trailing_nl_if_none <FILE>
#### return: 1 if file does not exist
#### return: non-zero if append fails
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_empty __is_eq __is_file __log
__file_append_trailing_nl_if_none() {
    #### verify prereqs for execution
    __are_refs __is_empty __is_eq __is_file __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__file_append_trailing_nl_if_none: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __is_file "${1}" || ! __log -e "could not locate file '${1}'" || return 1
    __is_empty "$(tail -c 1 "${1}")" || printf '\n' >>"${1}"
}

#### descr: checks if <FILE> contains <LINE> and if not appends <LINE>
#### usage: __file_append_line_if_not_found <FILE> <LINE>
#### return: 1 if file does not exist
#### return: non-zero if append fails
#### exit: 1 if there is NOT exactly two args
#### exit: 127 if any necessary refs are missing
#### note: <LINE> should not contain a newline
#### note: if <LINE> is a subset of a line in <FILE> the append will not occur
#### prereq: funcs are defined: __are_refs __is_eq __is_file __log __print_out_nl
__file_append_line_if_not_found() {
    #### verify prereqs for execution
    __are_refs __is_eq __is_file __log __print_out_nl || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '2' || {
        __log -f "__file_append_line_if_not_found: expects exactly two args: given '${#}': args='${*}'"
        exit 1
    }
    __is_file "${1}" || ! __log -e "could not find '${1}'" || return 1
    if ! grep -qF -- "${2}" "${1}"; then
        __print_out_nl "${2}" >>"${1}" || ! __log -e "could not add '${2}' to '${1}'." || return 1
        __log -i "'${2}' added to '${1}'."
    fi
}

#### descr: checks if <MAYBE_DIR> is a directory or a symlink to a directory
#### usage: __is_dir <MAYBE_DIR>
#### return: 1 if <MAYBE_DIR> is NOT a directory or a symlink to a directory
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __log
__is_dir() {
    #### verify prereqs for execution
    __are_refs __is_eq __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_dir: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    [ -d "${1}" ]
}

#### descr: check if <MAYBE_FILE> is a file or a symlink to a file
#### usage: __is_file <MAYBE_FILE>
#### return: 1 if <MAYBE_FILE> is NOT a file or a symlink to a file
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __log
__is_file() {
    #### verify prereqs for execution
    __are_refs __is_eq __log || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__is_file: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    [ -f "${1}" ]
}
