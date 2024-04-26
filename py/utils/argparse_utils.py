import argparse
import os
import re

from utils import path_utils


def parsed_args_to_str(args, k_v_delim=": ", arg_delim="\n", prefix="  "):
    return arg_delim.join(f"{prefix}{arg}{k_v_delim}{getattr(args, arg)}" for arg in vars(args))


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
                if isinstance(
                    arg, (argparse._StoreTrueAction, argparse._StoreFalseAction)  # pylint: disable=protected-access
                ):
                    continue
                arg(self.parser, args_, arg.default, "TODO:")
                if arg.type is not None:
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
        except re.error as e:
            raise SystemExit(f"ValueError: Regex pattern '{values}' is not valid.") from e


class PathType:
    """

    https://stackoverflow.com/a/33181083/10630957

    """

    # pylint: disable=too-few-public-methods
    def __init__(self, exists=True, type_="file", dash_ok=True):
        """
        exists:
             True: a path that does exist
             False: a path that does not exist, in a valid parent directory
             None: don't care
        type_: file, dir, symlink, None, or a function returning True for valid paths
             None: don't care
        dash_ok: whether to allow "-" as stdin/stdout"""

        assert exists in (True, False, None)
        assert type_ in ("file", "dir", "symlink", None) or hasattr(type_, "__call__")

        self._exists = exists
        self._type = type_
        self._dash_ok = dash_ok
        self._path_hdlr_dict = {
            "dir": os.path.isdir,
            "file": os.path.isfile,
            "symlink": os.path.islink,
            None: lambda _: True,
        }

    def __call__(self, path_str):
        if path_str == "-":
            # the special argument "-" means sys.std{in,out}
            if self._type == "dir":
                raise argparse.ArgumentTypeError("standard input/output (-) not allowed as directory path")
            if self._type == "symlink":
                raise argparse.ArgumentTypeError("standard input/output (-) not allowed as symlink path")
            if not self._dash_ok:
                raise argparse.ArgumentTypeError("standard input/output (-) not allowed")
            return path_str

        path_exists = os.path.exists(path_str)
        if self._exists is True:
            if not path_exists:
                raise argparse.ArgumentTypeError(f"path does not exist: '{path_str}'")
            if self._type in self._path_hdlr_dict:
                if not self._path_hdlr_dict[self._type](path_str):
                    raise argparse.ArgumentTypeError(f"path is not a {self._type}: '{path_str}'")
            elif not self._type(path_str):
                raise argparse.ArgumentTypeError(f"path not valid: '{path_str}'")
            return path_str
        if self._exists is False and path_exists:
            raise argparse.ArgumentTypeError(f"path exists: '{path_str}'")

        parent = os.path.dirname(os.path.normpath(path_str)) or "."
        if not os.path.isdir(parent):
            raise argparse.ArgumentTypeError(f"parent path is not a directory: '{parent}'")
        if not os.path.exists(parent):
            raise argparse.ArgumentTypeError(f"parent directory does not exist: '{parent}'")

        return path_str


class DirType:
    """

    https://stackoverflow.com/a/33181083/10630957

    """

    # pylint: disable=too-few-public-methods
    def __init__(self, exists=True):
        """exists:
        True: a path that does exist
        False: a path that does not exist, in a valid parent directory
        None: don't care
        """

        assert exists in (True, False, None)
        self._exists = exists

    def __call__(self, string):
        if self._exists is True:
            if not os.path.isdir(string):
                raise argparse.ArgumentTypeError(f"Path '{string}' does not exist.")
            return path_utils.path_clean(string)
        if self._exists is False:
            if os.path.isdir(string):
                raise argparse.ArgumentTypeError(f"Path '{string}' exists.")
        cleaned = path_utils.path_clean(string)
        parent = os.path.dirname(cleaned)
        if not os.path.isdir(parent):
            if os.path.exists(parent):
                raise argparse.ArgumentTypeError(f"Parent path '{parent}' is not a directory.")
            raise argparse.ArgumentTypeError(f"Parent path '{parent}' does not exist.")
        return cleaned
