# Python module for tools related to command line interfaces
#
# usage
#   * from utils import cli_utils
#       * adding this to a python file allows usage of functions as cli_utils.func()
#
# author: acegene <acegene22@gmail.com>

import json
import os
import re
import shlex
import subprocess
import sys

from typing import Callable, List, Optional, Sequence


def parse_range(range_in: str, raise_: bool = True) -> Optional[List[int]]:
    """Generate a list from <range_in>

    Args:
        range_in (str): String to extract range_in from
        raise_ (bool): Determines whether an invalid <range_in> leads to a raised exc or return None

    Returns:
        Optional[List[int]]: List of ints extracted from <range_in> or None if invalid and <raise_> == False

    Raises:
        ValueError: If <range_in> is invalid

    See Also:
        https://stackoverflow.com/questions/4726168/parsing-command-line-input-for-numbers
    """

    #### local funcs
    def new_list_elems_removed(elems, lst):
        return list(filter(lambda x: x not in elems, lst))

    #### set and use error type for param errors
    error = None
    error = TypeError if not error and not isinstance(range_in, str) else error
    error = ValueError if not error and range_in == "" else error
    error = (
        ValueError
        if not error and not all((c.isdigit() for c in new_list_elems_removed(["-", ","], range_in)))
        else error
    )
    error = ValueError if not error and not all((c.isdigit() for c in [range_in[0], range_in[-1]])) else error
    if error:
        print(f"ERROR: expect str with only positive ints, commas and hyphens, given {range_in}")
        if raise_:
            raise error
        return None
    result = []
    for section in range_in.split(","):
        x = section.split("-")
        result += list(range(int(x[0]), int(x[-1]) + 1))
    return sorted(result)


def prompt_return_bool(msg: str, true_strs: Sequence[str]) -> bool:
    choice = input(msg)
    if choice in true_strs:
        return True
    return False


def prompt_with_exec(msg: str, exec_strs: Sequence[str], callable_: Callable, *args, **kwargs) -> bool:
    choice = input(msg)
    if choice in exec_strs:
        callable_(*args, **kwargs)
        return True
    return False


def cmdline_split(s, platform="this"):
    """Multi-platform variant of shlex.split() for command-line splitting.
    For use with subprocess, for argv injection etc. Using fast REGEX.

    platform: 'this' = auto from current platform;
              1 = POSIX;
              0 = Windows/CMD
              (other values reserved)

    https://stackoverflow.com/a/35900070/10630957

    """
    # pylint: disable=[too-many-branches]
    if platform == "this":
        platform = sys.platform != "win32"
    if platform == 1:
        re_cmd_lex = r""""((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)"""
    elif platform == 0:
        re_cmd_lex = r""""((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)"""
    else:
        raise AssertionError(f"unkown platform {platform}")

    args = []
    accu = None  # collects pieces of one arg
    for qs, qss, esc, pipe, word, white, fail in re.findall(re_cmd_lex, s):
        if word:
            pass  # most frequent
        elif esc:
            word = esc[1]
        elif white or pipe:
            if accu is not None:
                args.append(accu)  # type: ignore [unreachable]
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

    Args:
        cmd: Cmd str to extract into a Sequence[str]

    Returns:
        <cmd> split as a Sequence[str]

    See Also:
        https://stackoverflow.com/questions/44945815/how-to-split-a-string-into-command-line-arguments-like-the-shell-in-python

    TODO:
        Write a version of this that doesn't invoke a subprocess
    """
    if os.name == "posix":
        return shlex.split(cmd)

    if not cmd:  # TODO: check if this always works
        return []
    full_cmd = (
        f"{subprocess.list2cmdline([sys.executable, '-c', 'import sys, json; print(json.dumps(sys.argv[1:]))',])} {cmd}"
    )
    ret = subprocess.check_output(full_cmd).decode()
    ret_val: Sequence[str] = json.loads(ret)
    assert all((isinstance(val, str) for val in ret_val)), f"type(ret_val)={type(ret_val)}; ret_val={ret_val}"
    return ret_val
