import re

from typing import Callable, Pattern, Sequence, Tuple, Union

#### TODO: consider filename length restriction

#### Regex criteria for filenames; a match typically indicates an erroneous filename
#### Criteria of the same number are mutually exclusive i.e do not use 1a alongside 1b
#### These regexes expect the basename of the file (directory removed)
## 1a) At least one character does not match ['_', '-', '.'] or contain lowercase alphanumeric characters (a-z and 0-9)
REG_STR_FN_1A = r".*[^a-z0-9\-_\.].*"
## 1b) At least one character does not match ['_', '-', '.'] or contain alphanumeric characters (a-z, A-Z, and 0-9)
REG_STR_FN_1B = r".*[^a-zA-Z0-9\-_\.].*"
## 1c) At least one character is a capital alpha character A-Z (capital accented characters such as 'À' are ignored)
REG_STR_FN_1C = r".*[A-Z].*"
## 2a) Leading character is one of ['_', '-']
REG_STR_FN_2A = r"[\-_].*"
## 2b) Leading character is '-'
REG_STR_FN_2B = r"\-.*"
## 2c) Leading character is '_'
REG_STR_FN_2C = r"_.*"
## 3a) Trailing character is '.'
REG_STR_FN_3A = r".*\."
## 4a) All characters are one of ['.', ' ']
REG_STR_FN_4A = r"[\. ]*"


def regex_or_operation(*regexes: str) -> Pattern:
    return re.compile(r"^(" + r"|".join(regexes) + r")$")


#### Precompiled regexes
REGEX_FN_STRICT_1 = regex_or_operation(REG_STR_FN_1A, REG_STR_FN_2A, REG_STR_FN_3A, REG_STR_FN_4A)
REGEX_FN_STRICT_2 = regex_or_operation(REG_STR_FN_1B, REG_STR_FN_2B, REG_STR_FN_3A, REG_STR_FN_4A)
REGEX_FN_HAS_UPPER = re.compile(REG_STR_FN_1C)  # TODO: does this need '^(' or ')$'?

ReplaceType = Union[str, Callable[[str], str], None]


def re_replace(reg: str, str_in: str, group_replace: Sequence[ReplaceType], indices=None, flags=0) -> Tuple[str, int]:
    def __create_replace_str(str_in: str, replace: ReplaceType):
        if replace is None:
            return str_in
        if isinstance(replace, str):
            return replace
        return replace(str_in)

    if re.compile(reg, flags=flags).groups != len(group_replace):
        raise ValueError(
            f"num capture-groups != len(group_replace): {re.compile(reg, flags=flags).groups} != {len(group_replace)}"
        )
    str_out = str_in
    offset = 0
    selected = re_select(reg, str_in, flags)
    for j, match in enumerate(selected):
        if indices is None or j in indices:
            for i, group in enumerate(match):
                str_repl = __create_replace_str(group[0], group_replace[i] if group_replace[i] is not None else None)
                str_out = str_repl.join([str_out[: group[1][0] + offset], str_out[group[1][1] + offset :]])
                offset += len(str_repl) - (group[1][1] - group[1][0])
    return str_out, len(selected)


def re_select(reg: str, str_in: str, flags=0) -> Sequence[Sequence[Tuple[str, Tuple[int, int]]]]:
    return [
        [(group, match.span(i + 1)) for i, group in enumerate(match.groups())]
        for match in re.finditer(reg, str_in, flags=flags)
    ]
