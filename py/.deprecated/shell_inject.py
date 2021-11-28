#!/usr/bin/env python3
#
# descr: allows a bash (shell?) script to prewrite input into stdin for the user
#
# usage: shell_inject.py

import fcntl, sys, termios

del sys.argv[0]
for c in " ".join(sys.argv):
    fcntl.ioctl(sys.stdin, termios.TIOCSTI, c)
