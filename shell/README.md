#### Function documentation/style
```
#### descr: prints one or two given args to stdout and stderr
####        extra lines to describe func in greater detail
#### usage: __func_name <ARG1> <ARG2=null> <*ARGS>
#### return: non-zero if either of internal echo cmds fail to execute
#### return: 1 if <ARG1> is 'Hello World'
#### exit: 2 if <ARG1> is 'Exit World' 
#### stdout: stdout: '<ARG1>', '<ARG2=null>', '<*ARGS>'
#### stderr: stderr
#### note: combines all args after the first two to use as the third arg
#### see: https://www.google.com
#### prereq: echo_super is defined
#### warning: no verification of the number of args
#### todo: verify the number of args  
__func_name() {
    if [ "${1}" = 'Hello World' ]; then return 1; fi
    if [ "${1}" = 'Exit World' ]; then exit 2; fi
    arg1="${1}"
    arg2="${2-null}"
    shift 2
    echo_super "stdout: '${arg1}', '${arg2}', '${*}'" || return "${?}"
    echo_super "stderr" >&2 || return "${?}"
}
```
