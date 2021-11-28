#!/usr/bin/env python3
#
# formatter.py
#
# brief:  python module for path formatting based on supplied criteria; can be executed as a script
#
# usage:  * import formatter
#               - this is needed to be used as a module
#         * formatter.py --dir <DIR> --mode 'dryrun' --formatter 'basenames_to_lower'
#               - to execute this as a script; this particular example lists all uppercase containing filenames in <DIR>
#
# author: acegene <acegene22@gmail.com>

import argparse
import difflib
import os

from typing import Any, Dict, List, Sequence, Union

from utils import cli_utils
from utils import format_utils
from utils import filter_utils
from utils import path_utils
from utils.argparse_utils import ArgumentParserWithDefaultChecking, DirAction
from utils.log_manager import LogManager

PathLike = Union[str, bytes, os.PathLike]


def _parse_input(args: Sequence[str] = None) -> List[Dict]:
    """Parse cmd line inputs; set, check, and fix script's default variables"""

    def validate_args(args: argparse.Namespace) -> None:
        """Ensure inputs to parser were valid"""
        logger.error_false(hasattr(args, "formatter"), ValueError("Must specify '--formatter'."), sys_exit=True)

    def generate_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", action=DirAction, default=".", help="Directory for git repo")
        parser.add_argument("--formatter", "-f", action="append", required=True, help="Formatter with its args")
        parser.add_argument("--filters", required=True, help="Filter script args")
        group_case = parser.add_mutually_exclusive_group(required=True)
        group_case.add_argument("--mode", "-m", choices=["dryrun", "force", "prompt"], help="Formatter execution mode")
        return parser

    def generate_parser_basenames_to_lower(dir_: PathLike, mode: str) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--mode", "-m", default=mode, help="Formatter execution mode")
        return parser

    def generate_parser_whitespace(dir_: PathLike, mode: str) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--mode", "-m", default=mode, help="Formatter execution mode")
        parser.add_argument("--eol", "-e", default="lf", help="End of line character(s)")
        return parser

    #### cmd line args parser
    ## toplevel script parser
    parser = generate_parser()
    args = parser.parse_args(args)
    validate_args(args)
    ## generate formatter specific arg parsers
    parser_basenames_to_lower = generate_parser_basenames_to_lower(args.dir, args.mode)
    parser_whitespace = generate_parser_whitespace(args.dir, args.mode)
    #### construct formatter subcommand parser dict
    formatter_parsers = {"basenames_to_lower": parser_basenames_to_lower, "whitespace": parser_whitespace}
    #### construct formatter with formatter operation/args dict
    formatter_lst = []
    for formatter_cmd in args.formatter:
        formatter_cmd_split = cli_utils.shell_split(formatter_cmd)
        f_type = formatter_cmd_split[0]
        try:
            formatter_parser = formatter_parsers[f_type]
        except KeyError:
            logger.error_exit(
                ValueError(f"Formatter type '{f_type}' must be one of {list(formatter_parsers.keys())}."), sys_exit=True
            )
        args_internal = formatter_parser.parse_args(formatter_cmd_split[1:])
        args_formatter = {attr: val for attr, val in args_internal.__dict__.items()}
        formatter_lst.append({"formatter": f_type, "args": args_formatter})
    #### return args
    return formatter_lst, args.filters


def formatter_basenames_to_lower(objs: PathLike, mode):
    objs_modified = []
    objs_unmodified = []
    if mode == "dryrun":
        for obj in objs:
            if not path_utils.is_path_basename_lower(obj):
                print(f"    {obj}")
            objs_unmodified.append(obj)
    elif mode == "prompt":
        for obj in objs:
            if not path_utils.is_path_basename_lower(obj):
                if cli_utils.prompt_return_bool(f"    {obj} : rename (y/n)? ", ["yes", "y"]):
                    obj_changed = format_utils.path_basename_to_lower(obj)
                    objs_modified.append(obj_changed)
                    continue
            objs_unmodified.append(obj)
    elif mode == "force":
        for obj in objs:
            if not path_utils.is_path_basename_lower(obj):
                obj_changed = format_utils.path_basename_to_lower(obj)
                objs_modified.append(obj_changed)
            else:
                objs_unmodified.append(obj)
    else:
        logger.error_exit(ValueError(f"Unexpected mode '{mode}'."), sys_exit=True)
    return objs_modified, objs_unmodified


def formatter_whitespace(objs: PathLike, mode: str, eol: str):
    objs_modified = []
    objs_unmodified = []
    for obj in objs:
        with open(obj, "rb") as open_file:
            content = open_file.read()
            content_modified = format_utils.convert_newlines(content, eol=eol)
            content_modified = format_utils.convert_tabs_to_spaces(content_modified)
            content_modified = format_utils.remove_trailing_line_spaces(content_modified, eol=eol)
            content_modified = format_utils.one_trailing_newline(content_modified, eol=eol)
        if mode == "dryrun":
            if content != content_modified:
                print(f"INFO: file {obj} would be changed")
            objs_unmodified.append(obj)
        elif mode == "prompt":
            if content != content_modified:
                with open(obj, "r", encoding="cp437") as open_file:
                    tmp_obj = path_utils.generate_tmp_from_path(obj)
                    with open(tmp_obj, "wb") as open_tmp_file:
                        open_tmp_file.write(content_modified)
                    try:
                        with open(tmp_obj, "r", encoding="cp437") as open_tmp_file:
                            diff = difflib.unified_diff(
                                open_file.readlines(),
                                open_tmp_file.readlines(),
                                fromfile="original",
                                tofile="edited",
                            )
                            for line in diff:
                                print(line)
                    except UnicodeDecodeError as err:
                        objs_unmodified.append(obj)
                        os.remove(tmp_obj)
                        raise err

                if cli_utils.prompt_return_bool(
                    f"INFO: ############ change {obj} with diff shown above? ", ["yes", "y"]
                ):
                    objs_modified.append(obj)
                    os.replace(tmp_obj, obj)
                else:
                    objs_unmodified.append(obj)
                    os.remove(tmp_obj)
            else:
                objs_unmodified.append(obj)
        elif mode == "force":
            logger.error_exit(ValueError(f"Mode '{mode}' is not supported."), sys_exit=True)
            objs_unmodified.append(obj)
        else:
            logger.error_exit(ValueError(f"Unexpected mode '{mode}'."), sys_exit=True)
    return objs_modified, objs_unmodified


def formatter_run(formatter: str, objs: PathLike, args: Dict) -> Sequence[Any]:
    if formatter == "basenames_to_lower":
        return formatter_basenames_to_lower(objs, **args)
    if formatter == "whitespace":
        return formatter_whitespace(objs, **args)
    logger.error_exit(ValueError(f"Unexpected formatter '{formatter}'."), sys_exit=True)


def main(args: Sequence[str] = None) -> None:
    formatters, args_filters = _parse_input(args)
    #### parse filters
    objs = filter_utils.main(cli_utils.shell_split(args_filters))
    for formatter in formatters:
        objs_modified, objs_unmodified = formatter_run(formatter["formatter"], objs, formatter["args"])
        print("UNMODIFIED below:")
        for obj in objs_unmodified:
            print(f"    {obj}")
        print("MODIFIED below:")
        for obj in objs_modified:
            print(f"    {obj}")


if __name__ == "__main__":
    with LogManager(__name__, filename="debug.log") as logger:
        main()
else:
    logger = LogManager(__name__, filename="debug.log")
