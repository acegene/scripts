#!/usr/bin/env python3
#
# obj_filters.py
#
# brief:  python module for object filtering based on supplied criteria; can be executed as a script
#
# usage:  * from utils import obj_filters
#               - this is needed to be used as a module
#         * obj_filters.py --dir <DIR> --or 'files' --and 'case --has-upper --file-mode'
#               - to execute this as a script; this particular example lists all uppercase containing filenames in <DIR>
#
# author: acegene <acegene22@gmail.com>

import argparse
import os

import git  # pip install GitPython

from typing import Any, Dict, List, Sequence, Set, Union

from utils import cli_utils
from utils import path_utils
from utils.argparse_utils import ArgumentParserWithDefaultChecking, DirSetAction
from utils.log_manager import LogManager

PathLike = Union[str, bytes, os.PathLike]


class _AccumulateAndsOrsAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(
            namespace,
            "ands_ors",
            getattr(namespace, "ands_ors", []) + [{"args": cli_utils.shell_split(values), "operation": self.dest}],
        )


def _parse_input(args: Sequence[str] = None) -> List[Dict]:
    """Parse cmd line inputs; set, check, and fix script's default variables"""

    def validate_args(args: argparse.Namespace) -> None:
        """Ensure inputs to parser were valid"""
        logger.error_false(
            hasattr(args, "ands_ors"), ValueError("One of '--and' or '--or' must be specified."), sys_exit=True
        )

    def generate_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument("--and", "-a", action=_AccumulateAndsOrsAction, help="TODO")
        parser.add_argument("--or", "-o", action=_AccumulateAndsOrsAction, help="TODO")
        parser.add_argument(
            "--dir", "-d", action=DirSetAction, default=".", help="directory that serves as default for filters"
        )
        return parser

    def generate_parser_files(dir_: PathLike) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--dir", "-d", action=DirSetAction, default=dir_, help="directory for git repo")
        return parser

    def generate_parser_case():
        parser = argparse.ArgumentParser()
        parser.add_argument("--file-mode", "-f", action="store_true", help="Truncate file objs to just their basename.")
        group_case = parser.add_mutually_exclusive_group(required=True)
        group_case.add_argument("--has-upper", "-u", action="store_true", help="Filter objs with an uppercase letter.")
        group_case.add_argument("--has-lower", "-l", action="store_true", help="Filter objs with a lowercase letter.")
        return parser

    def generate_parser_git_ignored(dir_: PathLike) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--dir", "-d", action=DirSetAction, default=dir_, help="directory for git repo")
        return parser

    def generate_parser_git_staged(dir_: PathLike) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--dir", "-d", action=DirSetAction, default=dir_, help="directory for git repo")
        return parser

    def generate_parser_git_text(dir_: PathLike) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--dir", "-d", action=DirSetAction, default=dir_, help="directory for git repo")
        parser.add_argument("--eol", "-e", choices=["cr", "crlf", "lf"], default="lf", help="end of line format")
        return parser

    def generate_parser_git_tracked(dir_: PathLike) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--dir", "-d", action=DirSetAction, default=dir_, help="directory for git repo")
        return parser

    def generate_parser_git_untracked(dir_: PathLike) -> argparse.ArgumentParser:
        parser = ArgumentParserWithDefaultChecking()
        parser.add_argument("--dir", "-d", action=DirSetAction, default=dir_, help="directory for git repo")
        parser.add_argument(
            "--show-ignored", "--si", action="store_true", default=False, help="show files ignored by .gitignore"
        )
        return parser

    #### cmd line args parser
    ## toplevel script parser
    parser = generate_parser()
    args = parser.parse_args(args)
    validate_args(args)
    ## generate filter specific arg parsers
    parser_case = generate_parser_case()
    parser_files = generate_parser_files(args.dir)
    parser_git_ignored = generate_parser_git_ignored(args.dir)
    parser_git_staged = generate_parser_git_staged(args.dir)
    parser_git_tracked = generate_parser_git_tracked(args.dir)
    parser_git_untracked = generate_parser_git_untracked(args.dir)
    parser_git_text = generate_parser_git_text(args.dir)
    #### construct filter subcommand parser dict
    filter_parsers = {
        "case": parser_case,
        "files": parser_files,
        "git_ignored": parser_git_ignored,
        "git_staged": parser_git_staged,
        "git_text": parser_git_text,
        "git_tracked": parser_git_tracked,
        "git_untracked": parser_git_untracked,
    }
    #### construct filter with filter operation/args dict
    filter_lst = []
    for arg in args.ands_ors:
        f_type = arg["args"][0]
        try:
            filter_parser = filter_parsers[f_type]
        except KeyError:
            logger.error_exit(
                ValueError(f"Filter type '{f_type}' must be one of {list(filter_parsers.keys())}."), sys_exit=True
            )
        args_internal = filter_parser.parse_args(arg["args"][1:])
        args_filter = {attr: val for attr, val in args_internal.__dict__.items()}
        filter_lst.append({"filter": f_type, "operation": arg["operation"], "args": args_filter})
    #### return args
    return filter_lst


def _operation_apply(operation: str, lhs: Sequence, rhs: Sequence):
    if operation == "and":
        return set(lhs).intersection(rhs)
    if operation == "or":
        return set(lhs).union(rhs)
    logger.error_exit(ValueError("<operation> not in ['and', 'or']."), sys_exit=True)


def filter_case(objs_in: Set[PathLike], operation: str, has_lower: bool, has_upper: bool, file_mode):
    if operation == "or":
        logger.error_exit(ValueError("For filter 'case' <operation> == 'or' is not allowed."), sys_exit=True)
    if has_upper:
        convert_func = str.lower
    elif has_lower:
        convert_func = str.upper
    objs_to_process = objs_in if not file_mode else [os.path.basename(f) for f in objs_in]
    files_out = set()
    for f, f_in in zip(objs_to_process, objs_in):
        f_str = str(f)
        if f_str != convert_func(f_str):
            files_out.add(f_in)
    return files_out


def filter_files(files_in: Set[PathLike], operation: str, dir: PathLike) -> Sequence[str]:
    files_out = []
    for r, d, f in os.walk(dir):
        for file in f:
            files_out.append(path_utils.path_clean(os.path.join(r, file)))
    return _operation_apply(operation, files_in, files_out)


def filter_git_ignored(files_in: Set[PathLike], operation: str, dir: PathLike) -> Sequence[str]:
    #### generate files to process with git check_ignore
    if operation == "and":
        files_to_process = files_in
    elif operation == "or":
        files_to_process = filter_files(set(), "or", dir)
    #### initialize git var
    g = git.Git(dir)
    #### process files and check which ones are ignored
    files_out = []
    for f in files_to_process:
        try:
            git_output = g.check_ignore("--", f)
        except git.exc.GitCommandError:
            continue
        if git_output != "":
            files_out.append(path_utils.path_clean(f))
    files_out = [f for f in files_out if os.path.exists(f)]
    #### generate appropriate return depending on <operation>
    return set(files_out) if operation == "and" else set().union(files_in, files_out)


def filter_git_staged(files_in: Set[PathLike], operation: str, dir: PathLike) -> Sequence[str]:
    g = git.Git(dir)
    files_git_staged = g.diff("-z", "--cached", "--name-only", "--", str(dir)).strip("\x00").split("\x00")
    if files_git_staged == [""]:
        return _operation_apply(operation, files_in, [])
    dir_git = g.rev_parse("--show-toplevel")
    files_out = [path_utils.path_clean(os.path.join(dir_git, f)) for f in files_git_staged]
    files_out = [f for f in files_out if os.path.exists(f)]
    return _operation_apply(operation, files_in, files_out)


def filter_git_text(files_in: Set[PathLike], operation: str, dir: PathLike, eol: str):
    if operation == "or":
        logger.error_exit(ValueError("For filter 'text' <operation> == 'or' is not allowed."), sys_exit=True)
    #### initialize git var
    g = git.Git(dir)
    #### process files and check which ones are ignored
    files_out = []
    for f in files_in:
        try:
            git_output = g.check_attr("-z", "text", str(f)).strip("\x00").split("\x00")
        except git.exc.GitCommandError:
            continue
        if git_output != "" and len(git_output) > 2 and git_output[2] == "set":
            try:
                git_output = g.check_attr("-z", "eol", str(f)).strip("\x00").split("\x00")
            except git.exc.GitCommandError:
                continue
            if git_output != "" and len(git_output) > 2 and git_output[2] == eol:
                files_out.append(path_utils.path_clean(f))
    files_out = [f for f in files_out if os.path.exists(f)]
    return files_out


def filter_git_tracked(files_in: Set[PathLike], operation: str, dir: PathLike) -> Sequence[str]:
    g = git.Git(dir)
    files_git_tracked = g.ls_files("-z").strip("\x00").split("\x00")
    if files_git_tracked == [""]:
        return _operation_apply(operation, files_in, [])
    files_out = [path_utils.path_clean(os.path.join(dir, f)) for f in files_git_tracked]
    files_out = [f for f in files_out if os.path.exists(f)]
    return _operation_apply(operation, files_in, files_out)


def filter_git_untracked(files_in: Set[PathLike], operation: str, dir: PathLike, show_ignored: bool) -> Sequence[str]:
    g = git.Git(dir)
    params = ["-z", "--others"]
    if not show_ignored:
        params.append("--exclude-standard")
    files_git_untracked = g.ls_files(*params).strip("\x00").split("\x00")
    if files_git_untracked == [""]:
        return _operation_apply(operation, files_in, [])
    files_out = [path_utils.path_clean(os.path.join(dir, f)) for f in files_git_untracked]
    files_out = [f for f in files_out if os.path.exists(f)]
    return _operation_apply(operation, files_in, files_out)


def filter_run(objs: Sequence[Any], operation: str, filter_: str, args: Dict) -> Sequence[Any]:
    logger.error_assert(operation in ["and", "or"], ValueError("<operation> not in ['and', 'or']."), sys_exit=True)
    if filter_ == "case":
        return filter_case(objs, operation, **args)
    if filter_ == "files":
        return filter_files(objs, operation, **args)
    if filter_ == "git_ignored":
        return filter_git_ignored(objs, operation, **args)
    if filter_ == "git_staged":
        return filter_git_staged(objs, operation, **args)
    if filter_ == "git_text":
        return filter_git_text(objs, operation, **args)
    if filter_ == "git_tracked":
        return filter_git_tracked(objs, operation, **args)
    if filter_ == "git_untracked":
        return filter_git_untracked(objs, operation, **args)
    logger.error_exit(ValueError(f"Unexpected filter '{filter_}'."), sys_exit=True)


def main(args: Sequence[str] = None, initial_objs: Set = set()) -> None:
    filter_list = _parse_input(args)
    filter_final_result = initial_objs
    for filter_ in filter_list:
        filter_final_result = filter_run(filter_final_result, filter_["operation"], filter_["filter"], filter_["args"])
    return filter_final_result


logger = LogManager(__name__, filename="debug.log")

if __name__ == "__main__":
    try:
        objs = main()
        for obj in objs:
            print(obj)
    except Exception as err:
        logger.error_exit(err, exc_info=err)
