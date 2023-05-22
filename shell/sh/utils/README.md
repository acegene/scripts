# sh/utils
## Collection of sh compliant utils
## usage
* files in this dir should be sourced, NOT executed as a script
## notes
* the emphasis should be reliable, predictable, and debuggable behavior, NOT speed
* files use shebang `#!/usr/bin/env sh` -> see https://unix.stackexchange.com/q/29608
* files in sh/utils can and do depend on other files in sh/utils; consider sourcing via the following
  * `for file in 'DIR/sh/utils/'*.sh; do . "${file}"; done`
## Known POSIX/portability exceptions
* `local` for function specific variable scoping is used
## code quality tips
* https://www.shellcheck.net
* https://google.github.io/styleguide/shellguide.html
* http://www.etalabs.net/sh_tricks.html
