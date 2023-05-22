# bash/utils
## Collection of bash compliant utils
## usage
* files in this dir should be sourced, NOT executed as a script
## notes
* the emphasis should be reliable, predictable, and debuggable behavior, NOT speed
* Files use shebang `#!/usr/bin/env bash` -> see https://unix.stackexchange.com/q/29608
* files in `bash/utils` depend on files in `bash/utils` and `sh/utils`; consider sourcing via the following
  * `for file in 'DIR/bash/utils/'*.bash; do . "${file}"; done`
  * `for file in 'DIR/sh/utils/'*.sh; do . "${file}"; done`
## code quality tips
* https://www.shellcheck.net
* https://google.github.io/styleguide/shellguide.html
