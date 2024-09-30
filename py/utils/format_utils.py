# TODO: need to revisit the binary needs of this file
import math
import re

from utils import path_utils

LE_CR = b"\r"
LE_CRLF = b"\r\n"
LE_LF = b"\n"
LINE_ENDINGS = [LE_CR, LE_CRLF, LE_LF]


def _eol_str_to_bin_str(str_in: str | bytes) -> bytes:
    if str_in in LINE_ENDINGS:
        return str_in  # type: ignore[return-value]
    if str_in == "cr":
        return LE_CR
    if str_in == "crlf":
        return LE_CRLF
    if str_in == "lf":
        return LE_LF
    raise ValueError(f"<eol> must be specified as one of {['lf', 'crlf', 'cr']}.")


def convert_newlines(string: str, eol: str | bytes = LE_LF) -> str:
    #### https://stackoverflow.com/questions/47178459/replace-crlf-with-lf-in-python-3-6
    #### https://gist.github.com/jonlabelle/dd8c3caa7808cbe4cfe0a47ee4881059
    #### check eol
    eol_nrm = _eol_str_to_bin_str(eol)
    #### modify line endings of file's content
    if eol_nrm == LE_CR:
        string_modified = string.replace(LE_CRLF, LE_LF).replace(LE_LF, LE_CR)  # type: ignore[arg-type] # TODO
    elif eol_nrm == LE_CRLF:
        string_modified = string.replace(LE_CRLF, LE_LF).replace(LE_CR, LE_LF).replace(LE_LF, LE_CRLF)  # type: ignore[arg-type] # TODO
    elif eol_nrm == LE_LF:
        string_modified = string.replace(LE_CRLF, LE_LF).replace(LE_CR, LE_LF)  # type: ignore[arg-type] # TODO
    else:
        raise ValueError(f"Unhandled input '{eol_nrm!r}'.")
    #### return modified string
    return string_modified


def convert_tabs_to_spaces(string: str, num_spaces: int = 4) -> str:
    #### replace tabs with spaces
    string_modified = string.replace(b"\t", b" " * num_spaces)  # type: ignore[arg-type] # TODO
    #### return modified string
    return string_modified


def one_trailing_newline(string: str, eol: str | bytes = LE_LF) -> str:  # pylint: disable=too-many-return-statements
    #### check eol
    eol_nrm = _eol_str_to_bin_str(eol)
    #### different behavior depending on eol
    if eol_nrm in (LE_CR, LE_LF):
        length = len(string)
        if length == 0:
            return b""  # type: ignore[return-value] # TODO
        for i in range(length):
            if string[length - i - 1 : length - i] != eol_nrm:
                return string[: length - i] + eol_nrm  # type: ignore[operator] # TODO
        return b""  # type: ignore[return-value] # TODO
    if eol_nrm == LE_CRLF:
        length = len(string)
        if length == 0:
            return b""  # type: ignore[return-value] # TODO
        if length == 1:
            return string + eol_nrm  # type: ignore[operator] # TODO
        for i in range(math.ceil(length / 2)):
            if string[length - (2 * i) - 2 : length - (2 * i)] != eol_nrm:
                return string[: length - (2 * i)] + eol_nrm  # type: ignore[operator] # TODO
        return b"" if (length % 2) == 0 else string + eol_nrm  # type: ignore[operator, return-value] # TODO
    raise ValueError(f"Unhandled input '{eol_nrm!r}'.")


def path_basename_to_lower(path: str, ignore_locks=False) -> str:
    return path_utils.path_basename_to_lower(path, ignore_locks)


def remove_trailing_line_spaces(string: str, eol: str | bytes = LE_LF) -> str:
    #### check eol
    eol_nrm = _eol_str_to_bin_str(eol)
    #### use regex to delete spaces before newlines
    regex = re.compile(b"  *" + eol_nrm)
    string_modified = re.sub(regex, eol_nrm, string)  # type: ignore[call-overload] # TODO
    #### return modified string
    return string_modified  # type: ignore[no-any-return] # TODO
