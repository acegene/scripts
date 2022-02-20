#!/usr/bin/env python3
#
# title: write_btw.py
#
# owner: acegene
#
# descr: manipulate/handle str between str_beg and str_end for a given str/file/pipe; matches work across lines
#
# usage: * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyENDxx"
#              stdout: "zzOUTxx"
#        * write_btw.py -b BEG -e END -o '' --str "zzBEGyyENDxx"
#              stdout: "zzxx"
#        * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyENDxxBEGwwENDvv"
#              stdout: "zzOUTxxOUTvv"
#        * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyBEGxxENDww"
#              stdout: "zzOUTww"
#        * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyENDxxBEGwwENDvv" --pattern-btw-type greedy
#              stdout: "zzOUTvv"
#        * write_btw.py -b BEG -e END -o OUT --file-stdout FILE_PATH
#              stdout: "zzOUTxx" # if FILE_PATH content is "zzBEGyyENDxx"
#        * write_btw.py -b BEG -e END -o OUT --file-write FILE_PATH
#              if FILE_PATH content is "zzBEGyyENDxx" it will be overwritten by "zzOUTxx"
#        * printf "zzBEGyyENDxx" | write_btw.py -b BEG -e END -o OUT --pipe
#              stdout: "zzOUTxx"
#
# notes: * compatible with HERE docs if using --pipe: https://stackoverflow.com/a/10677233
#        * newline type of files is preserved ('\n' vs '\r\n'); platform executing script should be irrelevant
#        * this scripts intent is to be robust rather than fast
#
# warns: * this script has no file locking mechanism
#           * problems could arise with large files (2-3 GB for 32 bit python and 64GB for 64 bit python)
#
# todos: * option for handling overlapping matches
#        * user specified capture groups and related potential behavior
#        * option to match str_beg and end-of-str_in if matching str_end no found; similar for str_end
#        * handle sourcing and calling from another script with regards to logging
#        * pattern matching for str_beg and str_end

import argparse
import enum
import logging
import os
import re
import sys

from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union

PathLike = Union[str, bytes, os.PathLike]

NAME_THIS = os.path.basename(__file__)


class MetaEnum(enum.EnumMeta):
    def __is_exaustive(cls, keys: Sequence[Any]) -> bool:
        if len(cls) != len(keys):
            return False
        for key in keys:
            if key not in cls:
                return False
        return True

    def from_str(cls, label: str) -> "MetaEnum":
        try:
            return cls[label]
        except KeyError:
            raise ValueError(f"{cls.__name__}.from_str cannot accept input='{label}'")

    CallableTuple = Tuple[Callable]
    CallableTupleWithArgs = Tuple[Callable, Sequence[Any]]
    CallableTupleWithArgsWithKWArgs = Tuple[Callable, Sequence[Any], Dict[str, Any]]
    CallableTupleWithOrWithoutArgs = Union[CallableTuple, CallableTupleWithArgs, CallableTupleWithArgsWithKWArgs]

    def exaustive_actions(cls, enum_state: "MetaEnum", actions: Dict["MetaEnum", CallableTupleWithOrWithoutArgs]):
        if not cls.__is_exaustive(actions.keys()):
            raise ValueError(f"{cls.__name__}.exaustive_actions requires all enum states are covered by 'actions' arg")
        action = actions[enum_state]
        if len(action) == 1:
            return action[0]()
        if len(action) == 2:
            return action[0](*action[1])
        if len(action) == 3:
            return action[0](*action[1], **action[2])
        raise ValueError(f"{cls.__name__}.exaustive_actions requires len(action) equal to 1-3")

    def exaustive_assigns(cls, enum_state: "MetaEnum", assigns: Dict["MetaEnum", Any]):
        if not cls.__is_exaustive(assigns.keys()):
            raise ValueError(f"{cls.__name__}.exaustive_assigns requires all enum states are covered by 'actions' arg")
        return assigns[enum_state]


class BtwMode(enum.Enum, metaclass=MetaEnum):
    FILE = 0
    STR = 1


class BtwPattern(enum.Enum, metaclass=MetaEnum):
    NONGREEDY = 0
    GREEDY = 1


def setup_logger(logger_name: str) -> logging.Logger:
    #### create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    #### create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    #### create formatter
    formatter = logging.Formatter("%(levelname)s: %(name)s: %(message)s")
    #### add formatter to handlers
    ch.setFormatter(formatter)
    #### add handlers to logger
    logger.addHandler(ch)
    return logger


def parse_inputs(cmd_args: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Parse cmd line inputs; set, check, and fix script's default vars"""
    #### cmd args parser
    parser = argparse.ArgumentParser(cmd_args, usage=usage())
    ## top level parser
    parser.add_argument("--str-beg", "-b", required=True, help="str the found pattern must beg with")
    parser.add_argument("--str-end", "-e", required=True, help="str the found pattern must end with")
    parser.add_argument("--str-out", "-o", required=True, help="str to replace 'str_beg + pattern + str_end' with")
    parser.add_argument(
        "--indices", nargs="+", type=check_pos_int, help="handle matches[n] where n is specified indices (0=1st)"
    )
    parser.add_argument(
        "--error-no-matches", action="store_true", default=False, help="execute sys.exit(1) if no matches are found"
    )
    ## mutually exclusive pattern group
    parser_group_pattern = parser.add_mutually_exclusive_group()
    parser_group_pattern.add_argument("--pattern-btw", type=check_re_pattern, help="pattern to use; NOT recommended")
    parser_group_pattern.add_argument("--pattern-btw-type", choices=["greedy", "nongreedy"], default="nongreedy")
    parser_group_mode = parser.add_mutually_exclusive_group()
    parser_group_mode.add_argument("--file-stdout", type=is_file, help="extract str_in from file; write to stdout")
    parser_group_mode.add_argument("--file-write", type=is_file, help="extract str_in from file; overwrite file")
    parser_group_mode.add_argument("--str", help="str to use as str_in")
    parser_group_mode.add_argument("--pipe", action="store_true", help="extract str to use as str_in from pipe/stdin")
    ## parse cmd args
    args = parser.parse_args()
    #### create output dictionary
    args_parsed = {}
    #### fill output dictionary
    ## fill outputs shared between subcommands
    args_parsed["str_beg"] = args.str_beg
    args_parsed["str_end"] = args.str_end
    args_parsed["str_out"] = args.str_out
    args_parsed["indices"] = args.indices
    args_parsed["error_no_matches"] = args.error_no_matches
    ## fill output pattern_btw
    if args.pattern_btw != None:
        args_parsed["pattern_btw"] = args.pattern_btw
    else:
        args_parsed["pattern_btw"] = BtwPattern.exaustive_assigns(
            BtwPattern.from_str(args.pattern_btw_type.upper()), {BtwPattern.NONGREEDY: r".*?", BtwPattern.GREEDY: r".*"}
        )
    ## fill mode specific args
    if args.file_stdout != None or args.file_write != None:
        args_parsed["mode"] = BtwMode.FILE
        args_parsed["file"] = args.file_stdout if args.file_stdout != None else args.file_write
        args_parsed["file_mode"] = "stdout" if args.file_stdout != None else "write"
    elif args.str != None:
        args_parsed["mode"] = BtwMode.STR
        args_parsed["str_in"] = args.str
    elif args.pipe == True:
        args_parsed["mode"] = BtwMode.STR
        args_parsed["str_in"] = sys.stdin.read()
    else:
        logger.error(f"could not find any possible value for mode")
        sys.exit(1)

    return args_parsed


def usage() -> str:
    usage_str = ""
    with open(__file__, "r") as f:
        for line in f.readlines():
            if not line.startswith("#"):
                return usage_str
            usage_str += line
    return usage_str


def is_file(value: Any) -> PathLike:
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError(f"{value} is an invalid file path")
    return value


def check_pos_int(value: Any) -> int:
    try:
        int_from_value = int(value)
    except (TypeError, ValueError) as e:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    if int_from_value < 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return int_from_value


def check_re_pattern(value: str) -> str:
    try:
        re.compile(value)
    except re.error:
        raise argparse.ArgumentTypeError(f"{value} is an invalid regex pattern")
    return value


def str_replace_range(str_in: str, index_start: int, index_end: int, str_replace: str) -> str:
    return str_in[0:index_start] + str_replace + str_in[index_end:]


def str_btw_internal(
    str_in: str, str_beg: str, str_end: str, str_out: str, pattern_btw: str, indices: Optional[Sequence[int]]
) -> Tuple[int, str]:
    pattern = re.escape(str_beg) + pattern_btw + re.escape(str_end)
    matches = re.finditer(pattern, str_in, flags=re.S)
    str_final = str_in
    offset = 0
    num_matches = 0
    for i, match in enumerate(matches):
        num_matches += 1
        if indices == None or i in indices:
            str_final = str_replace_range(str_final, match.start() + offset, match.end() + offset, str_out)
            offset += len(str_out) - (match.end() - match.start())
    return str_final, num_matches


def file_btw(
    file_: PathLike,
    file_mode: str,
    str_beg: str,
    str_end: str,
    str_out: str,
    pattern_btw: str,
    indices: Optional[Sequence[int]],
) -> int:
    with open(file_, "r", newline="") as f:
        str_in = f.read()
    str_final, num_matches = str_btw_internal(str_in, str_beg, str_end, str_out, pattern_btw, indices)
    if file_mode == "stdout":
        print(str_final, end="")
    elif file_mode == "write":
        #### prevent unnecessary overwriting of file if no matches were found
        if num_matches != 0:
            with open(file_, "w") as f:
                f.seek(0)
                f.write(str_final)
                f.truncate()
    else:
        for symbol, value in locals().items():
            print((symbol, value))
        logger.error(f"unexpected file_mode='{file_mode}'")
        sys.exit(1)
    return num_matches


def str_btw(
    str_in: str, str_beg: str, str_end: str, str_out: str, pattern_btw: str, indices: Optional[Sequence[int]]
) -> int:
    str_final, num_matches = str_btw_internal(str_in, str_beg, str_end, str_out, pattern_btw, indices)
    print(str_final, end="")
    return num_matches


def write_btw(cmd_args: Optional[Sequence[str]] = None) -> None:
    #### parse and check cmd line args
    args_parsed = parse_inputs(cmd_args)
    #### select and call func with appropriate args depending on mode
    num_matches = BtwMode.exaustive_actions(
        args_parsed["mode"],
        {
            BtwMode.FILE: (
                file_btw,
                (
                    args_parsed.get("file", None),
                    args_parsed.get("file_mode", None),
                    args_parsed.get("str_beg", None),
                    args_parsed.get("str_end", None),
                    args_parsed.get("str_out", None),
                    args_parsed.get("pattern_btw", None),
                    args_parsed.get("indices", None),
                ),
            ),
            BtwMode.STR: (
                str_btw,
                (
                    args_parsed.get("str_in", None),
                    args_parsed.get("str_beg", None),
                    args_parsed.get("str_end", None),
                    args_parsed.get("str_out", None),
                    args_parsed.get("pattern_btw", None),
                    args_parsed.get("indices", None),
                ),
            ),
        },
    )
    sys.exit(1 if args_parsed["error_no_matches"] and num_matches == 0 else 0)


if __name__ == "__main__":
    logger = setup_logger(NAME_THIS)
    write_btw()
