import math
import os
import re

from typing import Union

from utils import path_utils

PathLike = Union[str, bytes, os.PathLike]

LE_CR = b"\r"
LE_CRLF = b"\r\n"
LE_LF = b"\n"
LINE_ENDINGS = [LE_CR, LE_CRLF, LE_LF]


def _eol_str_to_bin_str(str_in: str) -> str:
    if str_in in LINE_ENDINGS:
        return str_in
    if str_in == "cr":
        return LE_CR
    if str_in == "crlf":
        return LE_CRLF
    if str_in == "lf":
        return LE_LF
    raise ValueError(f"<eol> must be specified as one of {['lf', 'crlf', 'cr']}.")


def convert_newlines(string: str, eol: str = LE_LF) -> str:
    #### https://stackoverflow.com/questions/47178459/replace-crlf-with-lf-in-python-3-6
    #### https://gist.github.com/jonlabelle/dd8c3caa7808cbe4cfe0a47ee4881059
    #### check eol
    eol_nrm = _eol_str_to_bin_str(eol)
    #### modify line endings of file's content
    if eol_nrm == LE_CR:
        string_modified = string.replace(LE_CRLF, LE_LF).replace(LE_LF, LE_CR)
    elif eol_nrm == LE_CRLF:
        string_modified = string.replace(LE_CRLF, LE_LF).replace(LE_CR, LE_LF).replace(LE_LF, LE_CRLF)
    elif eol_nrm == LE_LF:
        string_modified = string.replace(LE_CRLF, LE_LF).replace(LE_CR, LE_LF)
    else:
        raise ValueError(f"Unhandled input '{eol_nrm}'.")
    #### return modified string
    return string_modified


def convert_tabs_to_spaces(string: str, num_spaces: int = 4) -> str:
    #### replace tabs with spaces
    string_modified = string.replace(b"\t", b" " * num_spaces)
    #### return modified string
    return string_modified


def one_trailing_newline(string: str, eol: str = LE_LF) -> str:
    #### check eol
    eol_nrm = _eol_str_to_bin_str(eol)
    #### different behavior depending on eol
    if eol_nrm == LE_CR or eol_nrm == LE_LF:
        length = len(string)
        if length == 0:
            return b""
        for i in range(length):
            if string[length - i - 1 : length - i] != eol_nrm:
                return string[: length - i] + eol_nrm
        return b""
    if eol_nrm == LE_CRLF:
        length = len(string)
        if length == 0:
            return b""
        elif length == 1:
            return string + eol_nrm
        else:
            for i in range(math.ceil(length / 2)):
                if string[length - (2 * i) - 2 : length - (2 * i)] != eol_nrm:
                    return string[: length - (2 * i)] + eol_nrm
        return b"" if (length % 2) == 0 else string + eol_nrm
    raise ValueError(f"Unhandled input '{eol_nrm}'.")


def path_basename_to_lower(path: PathLike, ignore_locks=False) -> PathLike:
    return path_utils.path_basename_to_lower(path, ignore_locks)


def remove_trailing_line_spaces(string: str, eol: str = LE_LF) -> str:
    #### check eol
    eol_nrm = _eol_str_to_bin_str(eol)
    #### use regex to delete spaces before newlines
    regex = re.compile(b"  *" + eol_nrm)
    string_modified = re.sub(regex, eol_nrm, string)
    #### return modified string
    return string_modified
