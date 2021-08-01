import fnmatch
import math
import os
import re

from typing import Union

from utils import path_utils

PathLike = Union[str, bytes, os.PathLike]

CR_LINE_ENDING = b"\r"
CRLF_LINE_ENDING = b"\r\n"
LF_LINE_ENDING = b"\n"
LINE_ENDINGS = [CR_LINE_ENDING, CRLF_LINE_ENDING, LF_LINE_ENDING]


def convert_newlines(string: str, line_ending: str = LF_LINE_ENDING) -> str:
    #### https://stackoverflow.com/questions/47178459/replace-crlf-with-lf-in-python-3-6
    #### https://gist.github.com/jonlabelle/dd8c3caa7808cbe4cfe0a47ee4881059
    #### check params
    if line_ending not in LINE_ENDINGS:
        raise ValueError("<line_ending> must be specified as one of %s" % (LINE_ENDINGS))
    #### modify line endings of file's content
    if line_ending == CR_LINE_ENDING:
        string_modified = string.replace(CRLF_LINE_ENDING, LF_LINE_ENDING).replace(LF_LINE_ENDING, CR_LINE_ENDING)
    elif line_ending == CRLF_LINE_ENDING:
        string_modified = (
            string.replace(CRLF_LINE_ENDING, LF_LINE_ENDING)
            .replace(CR_LINE_ENDING, LF_LINE_ENDING)
            .replace(LF_LINE_ENDING, CRLF_LINE_ENDING)
        )
    elif line_ending == LF_LINE_ENDING:
        string_modified = string.replace(CRLF_LINE_ENDING, LF_LINE_ENDING).replace(CR_LINE_ENDING, LF_LINE_ENDING)
    else:
        raise ValueError("Unhandled input")
    #### return whether string was modified and the modified string itself
    return string_modified


def convert_tabs_to_spaces(string: str, num_spaces: int = 4) -> str:
    #### replace tabs with spaces
    string_modified = string.replace(b"\t", b" " * num_spaces)
    #### return whether string was modified and the modified string itself
    return string_modified


def add_trailing_newline(string: str, line_ending: str = LF_LINE_ENDING) -> str:
    #### check params
    if line_ending not in LINE_ENDINGS:
        raise ValueError("<line_ending> must be specified as one of %s" % (LINE_ENDINGS))
    #### TODO: calls to this should check lineending type
    if line_ending == CR_LINE_ENDING or line_ending == LF_LINE_ENDING:
        length = len(string)
        if length == 0:
            return b""
        for i in range(length):
            if string[length - i - 1 : length - i] != line_ending:
                return string[: length - i] + line_ending
        return b""
    elif line_ending == CRLF_LINE_ENDING:
        length = len(string)
        if length == 0:
            return b""
        elif length == 1:
            return string + line_ending
        else:
            for i in range(math.ceil(length / 2)):
                if string[length - (2 * i) - 2 : length - (2 * i)] != line_ending:
                    return string[: length - (2 * i)] + line_ending
        return b"" if (length % 2) == 0 else string + line_ending
    else:
        raise ValueError


def remove_trailing_line_spaces(string: str, line_ending: str = LF_LINE_ENDING) -> str:
    #### check params
    if line_ending not in LINE_ENDINGS:
        raise ValueError("<line_ending> must be specified as one of %s" % (LINE_ENDINGS))
    #### line endings
    if line_ending == CR_LINE_ENDING:
        line_ending = b"\r"
    elif line_ending == CRLF_LINE_ENDING:
        line_ending = b"\r\n"
    elif line_ending == LF_LINE_ENDING:
        line_ending = b"\n"
    else:
        raise ValueError
    ####
    regex = re.compile(b"  *" + line_ending)
    string_modified = re.sub(regex, line_ending, string)
    #### return whether string was modified and the modified string itself
    return string_modified


def format_file(file_path):
    with open(file_path, "rb") as open_file:
        content = open_file.read()
        # newline_converted = convert_newlines(content)[0]
        # tabless = convert_tabs_to_spaces(newline_converted)[0]
        # trailing_spaces_rm = remove_trailing_line_spaces(tabless)[0]
        trailing_newline_add = add_trailing_newline(content, line_ending=CRLF_LINE_ENDING)
        if content != trailing_newline_add:
            print((file_path, "Trying to edit file buddy!"))

    with open(file_path, "wb") as open_file:
        open_file.write(trailing_newline_add)


def format_dir():
    file_paths = []
    for root, dirnames, filenames in os.walk("."):
        for filename in fnmatch.filter(filenames, "*.py"):
            file_paths.append(os.path.join(root, filename))
    for file_path in file_paths:
        format_file(file_path)


def path_basename_to_lower(path: PathLike, ignore_locks=False) -> PathLike:
    return path_utils.path_basename_to_lower(path, ignore_locks)
