import argparse
import os
import re

from typing import Union

from utils import path_utils

PathLike = Union[str, bytes, os.PathLike]


class ArgumentParserWithDefaultChecking:
    """TODO: ramifications not well understood"""

    # https://stackoverflow.com/a/21588198/10630957
    def __init__(self, desc=None):
        self.parser = argparse.ArgumentParser(description=desc)
        self.actions = []

    def add_argument(self, *args, **kwargs):
        action = self.parser.add_argument(*args, **kwargs)
        self.actions.append(action)
        return self

    def parse_args(self, *args):
        args_ = self.parser.parse_args(*args)
        for arg in self.actions:
            if getattr(args_, arg.dest) == arg.default:
                if type(arg) == argparse._StoreTrueAction or type(arg) == argparse._StoreFalseAction:
                    continue
                arg(self.parser, args_, arg.default, "TODO:")
                if arg.type != None:
                    arg.type(arg.default)
        return args_


class DirAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not os.path.isdir(values):
            parser.print_usage()
            raise SystemExit(f"ValueError: Path '{values}' is not a valid directory.")
        setattr(namespace, self.dest, path_utils.path_clean(values))


class RegexAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            setattr(namespace, self.dest, re.compile(values))
        except re.error:
            raise SystemExit(f"ValueError: Regex pattern '{values}' is not valid.")


from argparse import ArgumentTypeError as err
import os


class PathType(object):
    """

    https://stackoverflow.com/a/33181083/10630957

    """

    def __init__(self, exists=True, type="file", dash_ok=True):
        """exists:
             True: a path that does exist
             False: a path that does not exist, in a valid parent directory
             None: don't care
        type: file, dir, symlink, None, or a function returning True for valid paths
             None: don't care
        dash_ok: whether to allow "-" as stdin/stdout"""

        assert exists in (True, False, None)
        assert type in ("file", "dir", "symlink", None) or hasattr(type, "__call__")

        self._exists = exists
        self._type = type
        self._dash_ok = dash_ok

    def __call__(self, string):
        if string == "-":
            # the special argument "-" means sys.std{in,out}
            if self._type == "dir":
                raise err("standard input/output (-) not allowed as directory path")
            elif self._type == "symlink":
                raise err("standard input/output (-) not allowed as symlink path")
            elif not self._dash_ok:
                raise err("standard input/output (-) not allowed")
        else:
            e = os.path.exists(string)
            if self._exists == True:
                if not e:
                    raise err("path does not exist: '%s'" % string)

                if self._type is None:
                    pass
                elif self._type == "file":
                    if not os.path.isfile(string):
                        raise err("path is not a file: '%s'" % string)
                elif self._type == "symlink":
                    if not os.path.symlink(string):
                        raise err("path is not a symlink: '%s'" % string)
                elif self._type == "dir":
                    if not os.path.isdir(string):
                        raise err("path is not a directory: '%s'" % string)
                elif not self._type(string):
                    raise err("path not valid: '%s'" % string)
            else:
                if self._exists == False and e:
                    raise err("path exists: '%s'" % string)

                p = os.path.dirname(os.path.normpath(string)) or "."
                if not os.path.isdir(p):
                    raise err("parent path is not a directory: '%s'" % p)
                elif not os.path.exists(p):
                    raise err("parent directory does not exist: '%s'" % p)

        return string


class DirType(object):
    """

    https://stackoverflow.com/a/33181083/10630957

    """

    def __init__(self, exists=True):
        """exists:
        True: a path that does exist
        False: a path that does not exist, in a valid parent directory
        None: don't care
        """

        assert exists in (True, False, None)
        self._exists = exists

    def __call__(self, string):
        if self._exists == True:
            if not os.path.isdir(string):
                raise err(f"Path '{string}' does not exist.")
            return path_utils.path_clean(string)
        else:
            if self._exists == False:
                if os.path.isdir(string):
                    raise err("Path '{string}' exists.")
            cleaned = path_utils.path_clean(string)
            parent = os.path.dirname(cleaned)
            if not os.path.isdir(parent):
                if os.path.exists(parent):
                    raise err(f"Parent path '{parent}' is not a directory.")
                else:
                    raise err(f"Parent path '{parent}' does not exist.")
            return cleaned
