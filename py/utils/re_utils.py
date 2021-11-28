import re

from typing import Pattern

# TODO: consider filename length restriction

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
REGEX_FN_HAS_UPPER = re.compile(REG_STR_FN_1C)
