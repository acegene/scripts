# cli_utils.py
#
# brief:  python module for tools related to command line interfaces
#
# usage:  * from utils import cli_utils
#               - adding this to a python file allows usage of functions as cli_utils.func()
#
# author: acegene <acegene22@gmail.com>

import json
import os
import re
import shlex
import subprocess
import sys

from typing import Any, Callable, List, Optional, Sequence, Union

PathLike = Union[str, bytes, os.PathLike]


def parse_range(range: str, raise_: bool = True) -> Optional[List[int]]:
    """Generate a list from <range>

    https://stackoverflow.com/questions/4726168/parsing-command-line-input-for-numbers

    Imports:
        from typing import List, Optional

    Args:
        range (str): String to extract range from
        raise_ (bool): Determines whether an invalid <range> leads to a raised exc or return None

    Returns:
        Optional[List[int]]: List of ints extracted from <range> or None if invalid and <raise_> == False

    Raises:
        ValueError: If <range> is invalid
    """
    #### local funcs
    def new_list_elems_removed(elems, lst):
        return list(filter(lambda x: x not in elems, lst))

    #### set and use error type for param errors
    error = None
    error = TypeError if not error and not isinstance(range, str) else error
    error = ValueError if not error and range == "" else error
    error = (
        ValueError if not error and not all([c.isdigit() for c in new_list_elems_removed(["-", ","], range)]) else error
    )
    error = ValueError if not error and not all([c.isdigit() for c in [range[0], range[-1]]]) else error
    if error:
        print(f"ERROR: expect str with only positive ints, commas and hyphens, given {range}")
        if raise_:
            raise error
        return None
    result = []
    for section in range.split(","):
        x = section.split("-")
        result += [i for i in range(int(x[0]), int(x[-1]) + 1)]
    return sorted(result)


def prompt_return_bool(msg: str, true_strs: Sequence[str]) -> False:
    choice = input(msg)
    if choice in true_strs:
        return True
    return False


def prompt_with_exec(msg: str, exec_strs: Sequence[str], callable: Callable, *args, **kwargs) -> False:
    choice = input(msg)
    if choice in exec_strs:
        callable(*args, **kwargs)
        return True
    return False


def progressbar(it: Sequence[Any], prefix: str = "", size: int = 60, file: PathLike = sys.stderr) -> None:
    """Cli progress bar based on iterable <it>

    https://stackoverflow.com/questions/3160699/python-progress-bar

    Imports:
        import os
        import sys
        from typing import Any, Type
        PathLike = Union[str, bytes, os.PathLike]

    Args:
        it (Sequence[Any]): Sequence to iterate over for progress bar
        prefix (bool): String to print in progress bar animation
        size (int): Size of progress bar
        file (PathLike): File to write progress bar to

    Returns:
        None
    """
    count = len(it)

    def show(j):
        x = int(size * j / count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#" * x, "." * (size - x), j, count))
        file.flush()

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    file.write("\n")
    file.flush()


def cmdline_split(s, platform="this"):
    """Multi-platform variant of shlex.split() for command-line splitting.
    For use with subprocess, for argv injection etc. Using fast REGEX.

    platform: 'this' = auto from current platform;
              1 = POSIX;
              0 = Windows/CMD
              (other values reserved)

    https://stackoverflow.com/a/35900070/10630957

    """
    if platform == "this":
        platform = sys.platform != "win32"
    if platform == 1:
        RE_CMD_LEX = r""""((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)"""
    elif platform == 0:
        RE_CMD_LEX = r""""((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)"""
    else:
        raise AssertionError("unkown platform %r" % platform)

    args = []
    accu = None  # collects pieces of one arg
    for qs, qss, esc, pipe, word, white, fail in re.findall(RE_CMD_LEX, s):
        if word:
            pass  # most frequent
        elif esc:
            word = esc[1]
        elif white or pipe:
            if accu is not None:
                args.append(accu)
            if pipe:
                args.append(pipe)
            accu = None
            continue
        elif fail:
            raise ValueError("invalid or incomplete shell string")
        elif qs:
            word = qs.replace('\\"', '"').replace("\\\\", "\\")
            if platform == 0:
                word = word.replace('""', '"')
        else:
            word = qss  # may be even empty; must be last

        accu = (accu or "") + word

    if accu is not None:
        args.append(accu)

    return args


def shell_split(cmd: str) -> Sequence[str]:
    """Like 'shlex.split', but uses the Windows OS splitting syntax when run on Windows.

    https://stackoverflow.com/questions/44945815/how-to-split-a-string-into-command-line-arguments-like-the-shell-in-python

    TODO:
        Write a version of this that doesn't invoke a subprocess

    Imports:
        import json
        import os
        import shlex
        import subprocess
        from typing import Sequence

    Args:
        it (Sequence[Any]): Sequence to iterate over for progress bar
        prefix (bool): String to print in progress bar animation
        size (int): Size of progress bar
        file (PathLike): File to write progress bar to

    Returns:
        None
    """
    if os.name == "posix":
        return shlex.split(cmd)
    else:
        if not cmd:  # TODO: check if this always works
            return []
        full_cmd = f"{subprocess.list2cmdline([sys.executable, '-c', 'import sys, json; print(json.dumps(sys.argv[1:]))',])} {cmd}"
        ret = subprocess.check_output(full_cmd).decode()
        return json.loads(ret)
