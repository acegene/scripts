#!/usr/bin/env python3
#
# Manipulate/handle str between str_beg and str_end for a given str/file/pipe; matches work across lines
#
# author: acegene <acegene22@gmail.com>
# usage
#   * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyENDxx"
#       * stdout: "zzOUTxx"
#   * write_btw.py -b BEG -e END -o '' --str "zzBEGyyENDxx"
#       * stdout: "zzxx"
#   * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyENDxxBEGwwENDvv"
#       * stdout: "zzOUTxxOUTvv"
#   * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyBEGxxENDww"
#       * stdout: "zzOUTww"
#   * write_btw.py -b BEG -e END -o OUT --str "zzBEGyyENDxxBEGwwENDvv" --pattern-btw-type greedy
#       * stdout: "zzOUTvv"
#   * write_btw.py -b BEG -e END -o OUT --file FILE_PATH
#       * stdout: "zzOUTxx" # if FILE_PATH content is "zzBEGyyENDxx"
#   * write_btw.py -b BEG -e END -o OUT --file FILE_PATH --file-mode write
#       * if FILE_PATH content is "zzBEGyyENDxx" it will be overwritten by "zzOUTxx"
#   * printf "zzBEGyyENDxx" | write_btw.py -b BEG -e END -o OUT --pipe
#       * stdout: "zzOUTxx"
# notes
#   * use HERE docs with --pipe: https://stackoverflow.com/a/10677233
#   * use HERE docs to assign to vars for input cmd args: https://stackoverflow.com/a/1655389
#   * preserves file newline type ('\n' vs '\r\n'); platform executing script should be irrelevant
#   * this scripts intent is to be robust rather than fast
#   * text encodings for python: https://stackoverflow.com/a/25584253
# warnings
#   * this script has no file locking mechanism
#   * problems could arise with large files (2-3 GB for 32 bit python and 64GB for 64 bit python)
# todos
#   * option for handling overlapping matches
#   * user specified capture groups and related potential behavior
#   * option to match str_beg and end-of-str_in if matching str_end no found; similar for str_end
#   * handle sourcing and calling from another script with regards to logging
#   * pattern matching for str_beg and str_end
#   * add more thorough encoding checks and exception handling
#   * add option to write to stdout as binary (and maybe read from stdin as binary?)
#       * https://stackoverflow.com/a/27185688
#       * https://stackoverflow.com/a/58664856
#   * consider auto encoding detection confidence from chardet (or replacing chardet alltogether?)
#   * carefully consider each usage of newline=""
#   * consider checking if content matches file before writing
import argparse
import enum
import io
import logging
import os
import re
import sys
from collections.abc import Sequence
from typing import Any
from typing import NoReturn

import chardet  # type: ignore[import-untyped]
from utils import path_utils
from utils import re_utils

NAME_THIS = __file__


def assert_unreachable(value: NoReturn) -> NoReturn:
    assert False, f"Unhandled value: {value} ({type(value).__name__})"


class BtwMode(enum.Enum):
    FILE = 0
    STR = 1


class BtwPattern(enum.Enum):
    NONGREEDY = 0
    GREEDY = 1


def setup_logger(logger_name: str) -> logging.Logger:
    #### create logger
    logger_out = logging.getLogger(logger_name)
    logger_out.setLevel(logging.INFO)
    #### create console handler
    console_hdlr = logging.StreamHandler()
    console_hdlr.setLevel(logging.INFO)
    #### create formatter
    formatter = logging.Formatter("%(levelname)s: %(name)s: %(message)s")
    #### add formatter to handlers
    console_hdlr.setFormatter(formatter)
    #### add handlers to logger
    logger_out.addHandler(console_hdlr)
    return logger_out


def parse_inputs(cmd_args: Sequence[str] | None = None) -> dict[str, Any]:
    """Parse cmd line inputs; set, check, and fix script's default vars."""
    # pylint: disable=too-many-statements
    #### cmd args parser
    parser = argparse.ArgumentParser(usage=usage())
    ## str args
    parser.add_argument("--str-beg", "-b", required=True, help="str the found pattern must beg with")
    parser.add_argument("--str-end", "-e", required=True, help="str the found pattern must end with")
    parser.add_argument(
        "--str-out",
        "-o",
        required=True,
        help="str to replace 'str_beg + pattern + str_end' with",
    )
    ## misc args
    parser.add_argument(
        "--indices",
        nargs="+",
        type=check_pos_int,
        help="handle matches[n] where n is specified indices (0=1st)",
    )
    parser.add_argument(
        "--error-no-matches",
        action="store_true",
        default=False,
        help="execute sys.exit(1) if no matches are found",
    )
    ## encoding args
    # parser.add_argument("--encoding-fallback", help='encoding codec to use when one fails')
    parser.add_argument("--encoding-file", help="encoding codec to use for file")
    parser.add_argument(
        "--encoding-stdin",
        default=sys.stdin.encoding,
        help="encoding codec to use for stdin",
    )
    parser.add_argument(
        "--encoding-stdout",
        default=sys.stdin.encoding,
        help="encoding codec for stdout",
    )
    parser.add_argument("--file-mode", choices=["stdout", "write"], default="stdout", help="")
    ## mutually exclusive pattern group
    parser_group_pattern = parser.add_mutually_exclusive_group()
    parser_group_pattern.add_argument("--pattern-btw", type=check_re_pattern, help="pattern to use; NOT recommended")
    parser_group_pattern.add_argument("--pattern-btw-type", choices=["greedy", "nongreedy"], default="nongreedy")
    ## mutually exclusive mode group
    parser_group_mode = parser.add_mutually_exclusive_group(required=True)
    parser_group_mode.add_argument("--file", type=check_file, help="extract str_in from file")
    parser_group_mode.add_argument("--str", help="str to use as str_in")
    parser_group_mode.add_argument(
        "--pipe",
        action="store_true",
        help="extract str to use as str_in from pipe/stdin",
    )
    ## parse cmd args
    args = parser.parse_args(cmd_args)
    #### create output dictionary
    args_parsed = {}
    #### fill output dictionary
    ## fill outputs shared between subcommands
    args_parsed["str_beg"] = args.str_beg
    args_parsed["str_end"] = args.str_end
    args_parsed["str_out"] = args.str_out
    args_parsed["indices"] = args.indices
    args_parsed["error_no_matches"] = args.error_no_matches
    args_parsed["encoding_stdout"] = args.encoding_stdout
    ## fill output pattern_btw
    if args.pattern_btw is not None:
        args_parsed["pattern_btw"] = args.pattern_btw
    else:
        pattern_type = BtwPattern[args.pattern_btw_type.upper()]
        if pattern_type is BtwPattern.GREEDY:
            args_parsed["pattern_btw"] = r"(.*)"
        elif pattern_type is BtwPattern.NONGREEDY:
            args_parsed["pattern_btw"] = r"(.*?)"
        else:
            assert_unreachable(args_parsed["pattern_btw"])
    ## fill mode specific args
    if args.file is not None:
        args_parsed["mode"] = BtwMode.FILE
        args_parsed["file"] = args.file
        args_parsed["file_mode"] = args.file_mode
        if args.encoding_file is not None:
            args_parsed["encoding_file"] = args.encoding_file
        else:
            with open(__file__, "rb") as f:
                args_parsed["encoding_file"] = chardet.detect(f.read())["encoding"]
                logger.info(
                    "for file='%s' using auto detected encodings='%s'.",
                    args_parsed["file"],
                    args_parsed["encoding_file"],
                )
    elif args.str is not None:
        args_parsed["mode"] = BtwMode.STR
        args_parsed["str_in"] = args.str
    elif args.pipe is True:
        args_parsed["mode"] = BtwMode.STR
        stdin_encoded = io.TextIOWrapper(sys.stdin.buffer.raw, encoding=args.encoding_stdin)  # type: ignore[attr-defined]
        args_parsed["str_in"] = stdin_encoded.read()
    else:
        logger.error("could not find any possible value for mode")
        sys.exit(1)

    return args_parsed


def usage() -> str:
    usage_str = ""
    try:
        with path_utils.open_unix_safely(__file__) as f:
            for line in f.readlines():
                if not line.startswith("#"):
                    return usage_str
                usage_str += line
    except OSError as e:
        if e.errno == 2:
            usage_str = "WARNING: could not generate usage."
        else:
            raise OSError from e
    return usage_str


def check_file(value: Any) -> str:
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError(f"{value} is an invalid file path")
    return value  # type: ignore[no-any-return]


def check_pos_int(value: Any) -> int:
    try:
        int_from_value = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value") from None
    if int_from_value < 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return int_from_value


def check_re_pattern(value: str) -> str:
    try:
        re.compile(value)
    except re.error:
        raise argparse.ArgumentTypeError(f"{value} is an invalid regex pattern") from None
    return value


def str_btw_internal(
    str_in: str,
    str_beg: str,
    str_end: str,
    str_out: str,
    pattern_btw: str,
    indices: Sequence[int] | None,
) -> tuple[str, int]:
    pattern = re.escape(str_beg) + pattern_btw + re.escape(str_end)
    return re_utils.re_replace(pattern, str_in, group_replace=[str_out], indices=indices, flags=re.S)


def file_btw(  # pylint: disable=too-many-positional-arguments
    file_: str,
    file_mode: str,
    str_beg: str,
    str_end: str,
    str_out: str,
    pattern_btw: str,
    indices: Sequence[int] | None,
    encoding_file: str,
    encoding_stdout: str,
) -> int:
    # pylint: disable=too-many-arguments
    with path_utils.open_unix_safely(file_, encoding=encoding_file) as f:
        str_in = f.read()
    str_final, num_matches = str_btw_internal(str_in, str_beg, str_end, str_out, pattern_btw, indices)
    if file_mode == "stdout":
        io.TextIOWrapper(sys.stdout.buffer.raw, newline="", encoding=encoding_stdout).write(str_final)  # type: ignore[attr-defined]
    elif file_mode == "write":
        #### prevent unnecessary overwriting of file if no matches were found
        if num_matches != 0:
            with path_utils.open_unix_safely(file_, "w", encoding=encoding_file) as f:
                f.seek(0)
                f.write(str_final)
                f.truncate()
    else:
        logger.error("unexpected file_mode='%s'", file_mode)
        sys.exit(1)
    return num_matches


def str_btw(
    str_in: str,
    str_beg: str,
    str_end: str,
    str_out: str,
    pattern_btw: str,
    indices: Sequence[int] | None,
    encoding_stdout: str,
) -> int:
    str_final, num_matches = str_btw_internal(str_in, str_beg, str_end, str_out, pattern_btw, indices)
    io.TextIOWrapper(sys.stdout.buffer.raw, encoding=encoding_stdout).write(str_final)  # type: ignore[attr-defined]
    return num_matches


def write_btw(cmd_args: Sequence[str] | None = None) -> None:
    #### parse and check cmd line args
    args_parsed = parse_inputs(cmd_args)
    #### select and call func with appropriate args depending on mode
    if args_parsed["mode"] is BtwMode.FILE:
        num_matches = file_btw(
            args_parsed["file"],
            args_parsed["file_mode"],
            args_parsed["str_beg"],
            args_parsed["str_end"],
            args_parsed["str_out"],
            args_parsed["pattern_btw"],
            args_parsed["indices"],
            args_parsed["encoding_file"],
            args_parsed["encoding_stdout"],
        )
    elif args_parsed["mode"] is BtwMode.STR:
        num_matches = str_btw(
            args_parsed["str_in"],
            args_parsed["str_beg"],
            args_parsed["str_end"],
            args_parsed["str_out"],
            args_parsed["pattern_btw"],
            args_parsed["indices"],
            args_parsed["encoding_stdout"],
        )
    else:
        assert_unreachable(args_parsed["mode"])
    if args_parsed["error_no_matches"] and num_matches == 0:
        sys.exit(1)


logger = setup_logger(__name__)

if __name__ == "__main__":
    write_btw()
