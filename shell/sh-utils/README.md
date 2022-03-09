# sh-utils
## descr: collection of sh compliant utils
## usage:
* files in this dir should be sourced, NOT executed as a script
* each file may depend on others, please see the `# deps` section in the file heading
## notes:
* funcs added here should be as portable/POSIX compliant as feasible
* the emphasis should be reliable, predictable, and debuggable behavior, NOT speed
* Files use shebang `#!/usr/bin/env sh` -> see https://unix.stackexchange.com/q/29608
## code quality tips:
* https://www.shellcheck.net
* https://google.github.io/styleguide/shellguide.html
* http://www.etalabs.net/sh_tricks.html
