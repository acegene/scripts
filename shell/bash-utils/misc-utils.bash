#!/usr/bin/env bash
#
# owner: acegene

#### descr: use <MULTI_CHAR_DELIM> to join all remaining args into one string and print
#### usage: __join <MULTI_CHAR_DELIM> <ARG1> <ARG2> ... <ARGN>
#### usage: __join <MULTI_CHAR_DELIM> "${ARRAY[@]}"
#### stdout: all args joined with <MULTI_CHAR_DELIM>
__join() { local d="${1-}" && local f="${2-}" && if shift 2; then printf %s "$f" "${@/#/$d}"; fi; }
