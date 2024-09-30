#!/usr/bin/env python3
#
# Python module for object filtering based on supplied criteria; can be executed as a script
#
# usage
#   * from utils import filter_utils
#       * this is needed to be used as a module
#   * filter_utils.py --dir <DIR> --or 'files' --and 'case --has-upper --file-mode'
#       * to execute this as a script; this particular example lists all uppercase containing filenames in <DIR>
#
# author: acegene <acegene22@gmail.com>
import argparse
import os
import re
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Sequence
from re import Pattern
from typing import Any

import git  # python3 -m pip install GitPython
from utils import cli_utils
from utils import path_utils
from utils import re_utils
from utils.argparse_utils import DirType
from utils.argparse_utils import RegexAction
from utils.log_manager import LogManager


class _AccumulateAndsOrsAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(
            namespace,
            "ands_ors",
            getattr(namespace, "ands_ors", []) + [{"args": cli_utils.shell_split(values), "operation": self.dest}],
        )


def _parse_input(argparse_args: Sequence[str] | None = None) -> list[dict]:
    """Parse cmd line inputs; set, check, and fix script's default variables."""

    # pylint: disable=[too-many-locals,too-many-statements]
    def validate_args(args: argparse.Namespace) -> None:
        """Ensure inputs to parser were valid."""
        logger.error_assert(
            hasattr(args, "ands_ors"),
            ValueError("One of '--and' or '--or' must be specified."),
            raise_exc=SystemExit(1),
        )

    def generate_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--and", "-a", action=_AccumulateAndsOrsAction, help="TODO")
        parser.add_argument("--or", "-o", action=_AccumulateAndsOrsAction, help="TODO")
        parser.add_argument(
            "--dir",
            "-d",
            default=".",
            type=DirType(),
            help="directory that serves as default for filters",
        )
        return parser

    def generate_parser_apple_junk(dir_: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=dir_, type=DirType(), help="directory to search for files")
        default_excludes = [".git"]
        parser.add_argument("--excludes", "-e", default=default_excludes, nargs="+", help="paths to exclude")
        return parser

    def generate_parser_files(dir_: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=dir_, type=DirType(), help="directory to search for files")
        default_excludes = [".git", "__pycache__"]
        parser.add_argument("--excludes", "-e", default=default_excludes, nargs="+", help="paths to exclude")
        return parser

    def generate_parser_git_ignored(dir_: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=dir_, type=DirType(), help="directory for git repo")
        return parser

    def generate_parser_git_staged(dir_: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=dir_, type=DirType(), help="directory for git repo")
        return parser

    def generate_parser_git_text(dir_: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=dir_, type=DirType(), help="directory for git repo")
        parser.add_argument("--eol", "-e", choices=["all", "cr", "crlf", "lf"], default="lf", help="end of line format")
        return parser

    def generate_parser_git_tracked(dir_: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=dir_, type=DirType(), help="directory for git repo")
        return parser

    def generate_parser_git_untracked(dir_: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=dir_, type=DirType(), help="directory for git repo")
        parser.add_argument(
            "--show-ignored",
            "--si",
            action="store_true",
            default=False,
            help="show files ignored by .gitignore",
        )
        return parser

    def generate_parser_regex() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--file-mode", "-f", action="store_true", help="Truncate file objs to just their basename.")
        group_regex = parser.add_mutually_exclusive_group(required=True)
        group_regex.add_argument("--regex", "-r", action=RegexAction, help="regex used to filter objects")
        group_regex.add_argument(
            "--regex-has-uppercase",
            "--rhu",
            action="store_const",
            const=re_utils.REGEX_FN_HAS_UPPER,
            dest="regex",
            help="regex used to filter objects containing an uppercase letter",
        )
        group_regex.add_argument(
            "--regex-bad-chars",
            "--rbc",
            action="store_const",
            const=re_utils.REGEX_FN_STRICT_2,
            dest="regex",
            help="regex used to filter objects with bad characters for filenames",
        )
        group_regex.add_argument(
            "--regex-bad-chars-strict",
            "--rbcs",
            action="store_const",
            const=re_utils.REGEX_FN_STRICT_1,
            dest="regex",
            help="regex used to filter objects with bad character for filenames; strictest setting",
        )
        return parser

    #### cmd line args parser
    ## toplevel script parser
    parser = generate_parser()
    args = parser.parse_args(argparse_args)
    validate_args(args)
    ## generate filter specific arg parsers
    parser_apple_junk = generate_parser_apple_junk(args.dir)
    parser_files = generate_parser_files(args.dir)
    parser_git_ignored = generate_parser_git_ignored(args.dir)
    parser_git_staged = generate_parser_git_staged(args.dir)
    parser_git_tracked = generate_parser_git_tracked(args.dir)
    parser_git_untracked = generate_parser_git_untracked(args.dir)
    parser_git_text = generate_parser_git_text(args.dir)
    parser_regex = generate_parser_regex()
    #### construct filter subcommand parser dict
    filter_parsers = {
        "apple_junk": parser_apple_junk,
        "files": parser_files,
        "git_ignored": parser_git_ignored,
        "git_staged": parser_git_staged,
        "git_text": parser_git_text,
        "git_tracked": parser_git_tracked,
        "git_untracked": parser_git_untracked,
        "regex": parser_regex,
    }
    #### construct filter with filter operation/args dict
    filter_lst = []
    for arg in args.ands_ors:
        f_type = arg["args"][0]
        try:
            filter_parser = filter_parsers[f_type]
        except KeyError:
            logger.error_raise(
                ValueError(f"Filter type '{f_type}' must be one of {list(filter_parsers.keys())}."),
                raise_exc=SystemExit(1),
            )
        args_internal = filter_parser.parse_args(arg["args"][1:])
        args_filter = dict(args_internal.__dict__.items())
        filter_lst.append({"filter": f_type, "operation": arg["operation"], "args": args_filter})
    #### return args
    return filter_lst


def _operation_apply(operation: str, lhs: Iterable[Any], rhs: Iterable[Any]) -> Iterable[Any]:
    if operation == "and":
        return set(lhs).intersection(rhs)
    if operation == "or":
        return set(lhs).union(rhs)
    logger.error_raise(ValueError("<operation> not in ['and', 'or']."), raise_exc=SystemExit(1))


def filter_apple_junk(dir_: str, excludes: Iterable[str]) -> Iterable[str]:
    dirs_junk = [".Spotlight-V100", ".Trash", ".Trashes", ".fseventsd", ".TemporaryItems"]
    files_junk = [
        ".com.apple.timemachine.donotpresent",
        ".DS_Store",
        ".apDisk",
        ".VolumeIcon.icns",
        ".fseventsd",
        ".TemporaryItems",
    ]

    objs_out = []
    for root, dirs, files in os.walk(dir_, topdown=True):
        dirs[:] = [d for d in dirs if d not in excludes]
        objs_out += [path_utils.path_clean(os.path.join(root, d)) for d in dirs if d in dirs_junk]
        dirs[:] = [d for d in dirs if d not in dirs_junk]
        for file in files:
            if file not in excludes and file in files_junk:
                objs_out.append(path_utils.path_clean(os.path.join(root, file)))
    return objs_out


def _filter_apple_junk_wrapped(
    objs_in: Iterable[str],
    operation: str,
    dir_: str,
    excludes: Iterable[str],
) -> Iterable[str]:
    objs_out = filter_apple_junk(dir_, excludes)
    return _operation_apply(operation, objs_in, objs_out)


def filter_files(dir_: str, excludes: Iterable[str]) -> Iterable[str]:
    files_out = []
    for root, dirs, files in os.walk(dir_, topdown=True):
        dirs[:] = [d for d in dirs if d not in excludes]
        for file in files:
            if file not in excludes:
                files_out.append(path_utils.path_clean(os.path.join(root, file)))
    return files_out


def _filter_files_wrapped(files_in: Iterable[str], operation: str, dir_: str, excludes: Iterable[str]) -> Iterable[str]:
    files_out = filter_files(dir_, excludes)
    return _operation_apply(operation, files_in, files_out)


def filter_git_ignore(files_in: Iterable[str], dir_: str) -> Iterable[str]:
    #### initialize git var
    g = git.Git(dir_)
    #### accumulate ignored files
    files_out = []
    for f in files_in:
        try:
            git_output = g.check_ignore("--", f)
        except git.exc.GitCommandError:
            continue
        if git_output != "":
            files_out.append(path_utils.path_clean(f))
    #### cleanup files then return
    files_out = [f for f in files_out if os.path.exists(f)]  # TODO: is this needed?
    return files_out


def _filter_git_ignored_wrapped(files_in: Iterable[str], operation: str, dir_: str) -> Iterable[str]:
    #### get git ignore files
    files_out = filter_git_ignore(files_in, dir_)
    #### apply <operation>
    return set(files_out) if operation == "and" else _operation_apply("or", files_in, files_out)


def filter_git_staged(dir_: str):
    #### initialize git var
    g = git.Git(dir_)
    #### accumulate staged files
    files_git_staged = g.diff("-z", "--cached", "--name-only", "--", str(dir_)).strip("\x00").split("\x00")
    #### early return if no git output
    if files_git_staged == [""]:
        return []
    #### get the git top level directory
    dir_git = g.rev_parse("--show-toplevel")
    #### cleanup files then return
    files_out = [path_utils.path_clean(os.path.join(dir_git, f)) for f in files_git_staged]
    files_out = [f for f in files_out if os.path.exists(f)]
    return files_out


def _filter_git_staged_wrapped(files_in: Iterable[str], operation: str, dir_: str) -> Iterable[str]:
    files_out = filter_git_staged(dir_)
    return _operation_apply(operation, files_in, files_out)


def filter_git_text(files_in: Iterable[str], dir_: str, eol: str):
    #### initialize git var
    g = git.Git(dir_)
    #### accumulate git text files
    files_out = []
    for f in files_in:
        try:
            git_output = g.check_attr("-z", "text", str(f)).strip("\x00").split("\x00")
        except git.exc.GitCommandError:
            continue
        #### check if the text attribute for this file is set
        if git_output != "" and len(git_output) > 2 and git_output[2] == "set":
            if eol == "all":
                files_out.append(path_utils.path_clean(f))
                continue
            #### check if the eol attribute is equal to what <eol> is specified as
            try:
                git_output = g.check_attr("-z", "eol", str(f)).strip("\x00").split("\x00")
            except git.exc.GitCommandError:
                continue
            if git_output != "" and len(git_output) > 2 and git_output[2] == eol:
                files_out.append(path_utils.path_clean(f))
    #### cleanup files then return
    files_out = [f for f in files_out if os.path.exists(f)]
    return files_out


def _filter_git_text_wrapped(files_in: Iterable[str], operation: str, dir_: str, eol: str) -> Iterable[str]:
    if operation == "or":
        logger.error_raise(ValueError("For filter 'text' <operation> == 'or' is not allowed."), raise_exc=SystemExit(1))
    #### process files and check which ones are ignored
    files_out = filter_git_text(files_in, dir_, eol)
    return files_out  # type: ignore[no-any-return] # TODO: should this be needed?


def filter_git_tracked(dir_: str) -> Iterable[str]:
    g = git.Git(dir_)
    files_git_tracked = g.ls_files("-z").strip("\x00").split("\x00")
    #### early return if no git output
    if files_git_tracked == [""]:
        return []
    #### cleanup files then return
    files_out = [path_utils.path_clean(os.path.join(dir_, f)) for f in files_git_tracked]
    files_out = [f for f in files_out if os.path.exists(f)]
    return files_out


def _filter_git_tracked_wrapped(files_in: Iterable[str], operation: str, dir_: str) -> Iterable[str]:
    files_out = filter_git_tracked(dir_)
    return _operation_apply(operation, files_in, files_out)


def filter_git_untracked(dir_: str, show_ignored: bool) -> Iterable[str]:
    g = git.Git(dir_)
    params = ["-z", "--others"]
    if not show_ignored:
        params.append("--exclude-standard")
    files_git_untracked = g.ls_files(*params).strip("\x00").split("\x00")
    #### early return if no git output
    if files_git_untracked == [""]:
        return []
    #### cleanup files then return
    files_out = [path_utils.path_clean(os.path.join(dir_, f)) for f in files_git_untracked]
    files_out = [f for f in files_out if os.path.exists(f)]
    return files_out


def _filter_git_untracked_wrapped(
    files_in: Iterable[str],
    operation: str,
    dir_: str,
    show_ignored: bool,
) -> Iterable[str]:
    files_out = filter_git_untracked(dir_, show_ignored)
    return _operation_apply(operation, files_in, files_out)


def filter_regex(objs_in: Iterable[str], regex: Pattern, file_mode: bool = False) -> Iterable[str]:
    if file_mode:
        objs_to_process = [os.path.basename(f) for f in objs_in]
        return [o_in for o_in, o in zip(objs_in, objs_to_process) if re.search(regex, o)]
    return [o for o in objs_in if re.search(regex, o)]


def _filter_regex_wrapped(objs_in: Iterable[str], operation: str, regex: Pattern, file_mode: bool) -> Iterable[str]:
    if operation == "or":
        logger.error_raise(
            ValueError("For filter 'regex' <operation> == 'or' is not allowed."),
            raise_exc=SystemExit(1),
        )
    return filter_regex(objs_in, regex, file_mode)


def filter_run(objs: Iterable[Any], operation: str, filter_: str, args: dict) -> Iterable[Any]:
    logger.error_assert(
        operation in ["and", "or"],
        ValueError("<operation> not in ['and', 'or']."),
        raise_exc=SystemExit(1),
    )
    str_to_func: dict[str, Callable[..., Iterable[Any]]] = {
        "apple_junk": _filter_apple_junk_wrapped,
        "files": _filter_files_wrapped,
        "git_ignored": _filter_git_ignored_wrapped,
        "git_staged": _filter_git_staged_wrapped,
        "git_text": _filter_git_text_wrapped,
        "git_tracked": _filter_git_tracked_wrapped,
        "git_untracked": _filter_git_untracked_wrapped,
        "regex": _filter_regex_wrapped,
    }
    if not filter_ in str_to_func:
        logger.error_raise(ValueError(f"Unexpected filter '{filter_}'."), raise_exc=SystemExit(1))
    # _operation_apply(operation, objs, objs_filtered)
    return str_to_func[filter_](objs, operation, **args)


def main(args: Sequence[str] = None, initial_objs: Iterable | None = None) -> Iterable[Any]:
    initial_objs = set() if initial_objs is None else initial_objs
    filter_list = _parse_input(args)
    filter_final_result = initial_objs
    for filter_ in filter_list:
        filter_final_result = filter_run(filter_final_result, filter_["operation"], filter_["filter"], filter_["args"])
    return filter_final_result


logger = LogManager(__name__)

if __name__ == "__main__":
    objs_main_return = main()
    for obj in objs_main_return:
        print(obj)
