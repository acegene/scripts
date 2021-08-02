import argparse
import os

from typing import Union

from utils import path_utils

PathLike = Union[str, bytes, os.PathLike]


class ArgumentParserWithDefaultChecking:
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


class DirSetAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        checked_dir = DirSetAction._dir_check(values)
        if checked_dir == None:
            parser.print_usage()
            raise SystemExit(f"ValueError: Path '{values}' is not a valid directory.")
        setattr(namespace, self.dest, path_utils.path_clean(checked_dir))

    def _dir_check(path: PathLike) -> PathLike:
        try:
            if os.path.isdir(path):
                return path
        except TypeError:
            pass
        return None
