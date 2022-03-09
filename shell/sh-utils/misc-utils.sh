#!/usr/bin/env sh
#
# owner: acegene
#
# deps: * print-utils.sh # __log __print_err __print_out
#       * validation-utils.sh # __are_refs

#### descr: Read from stdin and pass output to stdout ie read user input
#### usage: __get_user_input
#### stdout: user typed input
#### prereq: funcs are defined: __are_refs __is_eq __log __print_out
__get_user_input() {
    #### verify prereqs for execution
    __are_refs __is_eq __log __print_out || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '0' || {
        __log -f "__get_user_input: expects no args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    read -r __private___get_user_input_input || return "${?}"
    __print_out "${__private___get_user_input_input}"
}

#### descr: Read from stdin and pass output to stdout ie read user input; typed input is hidden from user shell
#### usage: __get_user_input_hidden
#### stdout: user typed input
#### prereq: funcs are defined: __are_refs __is_eq __log __print_out
#### warning: this is not necessarily secure
#### todo: investigate security of potential implementations and provide secure use cases
__get_user_input_hidden() {
    #### verify prereqs for execution
    __are_refs __is_eq __log __print_out || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '0' || {
        __log -f "__get_user_input_hidden: expects no args: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    stty -echo
    read -r __private___get_user_input_hidden_input || return "${?}"
    stty echo
    __print_out "${__private___get_user_input_hidden_input}"
}

#### descr: prompt user with <PROMPT> and then loop until reponse is either y/n
#### usage: __yes_no_prompt <PROMPT> && cmd_if_yes || cmd_if_not_yes
#### usage: if __yes_no_prompt <PROMPT>; then cmd_if_yes; else cmd_if_not_yes; fi
#### return: 1 if the input from the user is any of [n, N, no, NO, No]
#### exit: 1 if there is NOT exactly one arg
#### exit: 127 if any necessary refs are missing
#### prereq: funcs are defined: __are_refs __is_eq __log __print_err
__yes_no_prompt() {
    #### verify prereqs for execution
    __are_refs __is_eq __log __print_err || exit "${?}"
    #### verify args for execution
    __is_eq "${#}" '1' || {
        __log -f "__yes_no_prompt: expects exactly one arg: given '${#}': args='${*}'"
        exit 1
    }
    #### start func body
    __private___yes_no_prompt_response=''
    __print_err "${1}"
    while true; do
        read -r __private___yes_no_prompt_response
        case "${__private___yes_no_prompt_response}" in
        y | Y | yes | YES | Yes) return 0 ;;
        n | N | no | NO | No) return 1 ;;
        *) __log -e "Prompt error, please respond y or n." ;;
        esac
    done
}
