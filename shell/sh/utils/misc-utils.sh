#!/usr/bin/env sh
#
# author: acegene <acegene22@gmail.com>

#### descr: Read from stdin and pass output to stdout ie read user input
#### usage: __get_user_input
#### stdout: user typed input
__get_user_input() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __is_eq __log __print_out || exit "${?}"
    #### verify args
    __is_eq "${#}" '0' || {
        __log -f "__get_user_input: expects no args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local user_input=''
    read -r user_input || return "${?}"
    __print_out "${user_input}"
}

#### descr: Read from stdin and pass output to stdout ie read user input; typed input is hidden from user shell
#### usage: __get_user_input_hidden
#### stdout: user typed input
#### warning: this is not necessarily secure
#### todo: investigate security of potential implementations and provide secure use cases
__get_user_input_hidden() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __is_eq __log __print_out || exit "${?}"
    #### verify args
    __is_eq "${#}" '0' || {
        __log -f "__get_user_input_hidden: expects no args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local user_input=''
    stty -echo
    read -r user_input || return "${?}"
    stty echo
    __print_out "${user_input}"
}

#### descr: use <MULTI_CHAR_DELIM> to join all remaining args into one string and print
#### usage: __join <MULTI_CHAR_DELIM> <*ARGS>
#### usage: __join <MULTI_CHAR_DELIM> "${ARRAY[@]}"
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### stdout: all args joined with <MULTI_CHAR_DELIM>
#### note: arrays are not posix
__join() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __is_eq __log __print_err || exit "${?}"
    #### start func body
    local multi_char_delim="${1}"
    local joined="${2}"
    shift
    shift
    while __is_not_eq "${?}" '0'; do joined="${joined}${multi_char_delim}${1}"; done
    printf %s "${joined}"
}

#### descr: prompt user with <PROMPT> and then loop until reponse is either y/n
#### usage: __yes_no_prompt <PROMPT> && cmd_if_yes || cmd_if_not_yes
#### usage: if __yes_no_prompt <PROMPT>; then cmd_if_yes; else cmd_if_not_yes; fi
#### return: 1 if the input from the user is any of [n, N, no, NO, No]
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
__yes_no_prompt() {
    #### verify system prereqs
    __are_refs local || exit "${?}"
    #### verify util prereqs
    __are_refs __is_eq __log __print_err || exit "${?}"
    #### verify args
    __is_eq "${#}" '1' || {
        __log -f "__yes_no_prompt: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    local user_input=''
    __print_err "${1}"
    while true; do
        read -r user_input
        case "${user_input}" in
        y | Y | yes | YES | Yes) return 0 ;;
        n | N | no | NO | No) return 1 ;;
        *) __log -e "Prompt error, please respond y or n." ;;
        esac
    done
}
