#!/usr/bin/env python3
#
# Searches for multifiles/mfs and then provides interactive cli for renaming/moving/mv'ing located mfs
#   * mf is a group of incrementing files such as mf=[file1.mp4, file2.mp4, file3.mp4]
#   * params can be specified at launch via cmdargs and during runtime via interactive cli
#       * cmdargs params can be understood with parse_inputs() below or using the --help cmdargs option
#       * cli is only for the mf mv process and includes params=[dir_out, base, part, ext, range_mv, inplace]
#   * given mf=[f-ep-1-720p.mp4,f-ep-2-720p.mp4]; then base=f, prepart=-ep-, part=1, postpart=-720p, ext=.mp4, range=1-3
#   * mfs search by default locates mfs with their first file's part in ['a','0','1'] e.g. mf = [f_a,f_b,f_c]
#       * '--range-search 3-4' via cmdargs can locate mf=[f3,f4,f5] or mf=[f4,f5]; note: does not limit length of mf
#   * mfs mv default format is base + postpart + part + ext unless inplace=True then format is base + part + postpart + ext
#       * partial mv: '--range-mv 2-3' via cmdargs or 'range_mv 2-3' via cli to allow mf=[f1,f2,f3] to mv only [f2,f3]
#   * mf mv is not atomic, but each individual file mv is atomic; see: https://en.wikipedia.org/wiki/Atomicity_(database_systems)
#
# usage
#   * python mfmv.py --help
#       * provides help info on scripts cmd line args
#   * python mfmv.py
#       * uses default params to locate mfs and launch cli
# warnings
#   * race condition when an external process moves files currently being batch mv'd
#       * each file is safe, but in the worst case an abort occurs and only a portion of the mf's files will mv
# version 1.0
# notes
#   * tested on 'Windows 10 2004' # TODO: testing with OSX and linux
# todos
#   * handle files without extensions
#   * proper cmd args mutual exclusion
#   * performance with high quantities of files
#   * allow two mvs for same mf if done partially
#   * file input for cmdargs
#       * allow custom user input auto filename formatter
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import re
import sys
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any

from utils import path_utils
from utils.wrapped_indexable_callable import WrappedIndexableCallable

################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################
# yymmdd: 210116
# generation cmd on the following line:
# python "${GWSPY}/write_btw.py" "-t" "py" "-w" "${GWSPY}/mfmv.py" "-x" "mv" "raise_if_false" "try_or" "parse_range"


def raise_if_false(exception: type[Exception], expression: bool, string_if_except: str = None) -> None:
    """Throw <exception> if <expression> == False."""
    if not expression:
        if string_if_except is not None:
            print(string_if_except)
        raise exception


def try_or(
    exceptions: type[BaseException] | tuple[type[BaseException]],
    call: Callable,
    *args,
    default: Any = None,
    **kargs,
) -> Any:
    """Returns result from calling <call> with <*args> <**kargs>; if an exception in <exceptions> occurs return
    default."""
    try:
        return call(*args, **kargs)
    except exceptions:
        return default


def parse_range(range_str: str, throw: bool = True) -> list[int] | None:
    """Generate a list from <range_str>"""

    #### local funcs
    def new_list_elems_removed(elems, lst):
        return list(filter(lambda x: x not in elems, lst))

    #### set and use error type for param errors
    error = None
    error = TypeError if not error and not isinstance(range_str, str) else error
    error = ValueError if not error and range_str == "" else error
    error = (
        ValueError
        if not error and not all(c.isdigit() for c in new_list_elems_removed(("-", ","), range_str))
        else error
    )
    error = ValueError if not error and not all(c.isdigit() for c in (range_str[0], range_str[-1])) else error
    if error:
        print(f"ERROR: expect str with only positive ints, commas and hyphens, given {range_str}.")
        if throw:
            raise error
        return None
    result = []
    for section in range_str.split(","):
        x = section.split("-")
        result += list(range(int(x[0]), int(x[-1]) + 1))
    return sorted(result)


def num_digits(num: int, base: int = 10, exception_if_neg: bool = False) -> int:
    if num > 0:
        return int(math.log(num, base)) + 1
    if num == 0:
        return 1
    if exception_if_neg:
        raise ValueError("If <exception_if_neg> is True then <num> must be positive")
    return int(math.log10(-num)) + 1  # +1 if you don't count the '-'


def num_convert_base(num: int, base: int) -> Sequence[int]:
    assert num >= 0
    if num == 0:
        return [0]
    digits = []
    while num:
        digits.append(int(num % base))
        num //= base
    return digits[::-1]


################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################
def alpha_from_int(x: int) -> str:
    """Return the alpha lowercase char associated with <x>"""
    return chr(x + 96)


def int_from_alpha(string: str) -> int:
    """Return the int associated with <string>"""
    if len(string) != 1:
        return 0
    new = ord(string)
    if 65 <= new <= 90:  # uppercase
        return new - 64
    if 97 <= new <= 122:  # lowercase
        return new - 96
    return 0  # unrecognized


def parse_range_alpha(range_str: str, throw=True) -> list[int] | list[str] | None:
    """Generate a list from <range_str>"""

    error = None
    error = TypeError if not error and not isinstance(range_str, str) else error
    error = ValueError if not error and range_str == "" else error
    if error:  # TODO: check if valid
        print(f"ERROR: expect str with only positive ints, commas and hyphens, given '{range_str}'")
        if throw:
            raise error
        return None
    if range_str[0].isalpha():
        range_lst = parse_range("".join([str(int_from_alpha(c)) if c.isalpha() else c for c in range_str]), throw)
        if range_lst is None:
            return None
        return [alpha_from_int(x) for x in range_lst] if range_lst is not None else None
    return parse_range(range_str, throw)


def parse_inputs(argparse_args: Sequence[str] | None = None) -> dict:
    """Parse cmd line inputs; set, check, and fix script's default variables."""

    #### local funcs
    def import_json_obj(f: str, key: str) -> list[str]:
        """Returns json object associated with key from file."""
        with path_utils.open_unix_safely(f) as json_file:
            data = json.load(json_file)
            raise_if_false(ValueError, key in data)
            return data[key]  # type: ignore[no-any-return]

    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir-in", "-i", default=".", help="dir to search for multifiles")
    parser.add_argument("--dir-out", "-o", help="dir to mv multifiles into")
    # parser.add_argument('--part-out', '--po', '-p', default='-1', help='first part of multifile mv i.e. pt-1')
    parser.add_argument("--excludes", "-x", default=[], nargs="+", help="dirs to exclude from multifile search")
    parser.add_argument("--exts", "-e", nargs="+", help="file exts filter for multifile search")
    parser.add_argument(
        "--exts-json",
        "--ej",
        help="path to json file containing a list of file exts (at key='video_exts') for multifile search",
    )
    parser.add_argument(
        "--exts-env",
        "--ee",
        action="store_true",
        help="use hardcoded env var for list of file exts for multifile search",
    )
    parser.add_argument("--regex", "-r", help="regex for prefiltering files for multifile search")
    parser.add_argument("--inplace", "--inp", action="store_true", default=False, help="toggle mv inplace mode")
    parser.add_argument("--maxdepth", "--mx", default=10, type=int, help="the recursive dir search max depth")
    parser.add_argument("--mindepth", "--mn", default=1, type=int, help="the recursive dir search min depth")
    parser.add_argument(
        "--range-search",
        "--rs",
        default=[0, 1],
        type=parse_range_alpha,
        help="range, inclusive, for multifile search to consider as a first files part i.e. 0-1",
    )  # TODO:
    parser.add_argument(
        "--range-mv",
        "--rm",
        default=None,
        type=parse_range_alpha,
        help="indices range, inclusive, for multifile mv i.e. 0-4",
    )  # TODO:
    args = parser.parse_args(argparse_args)
    #### return dict assigned from attributes of argumentparser object
    out = dict(args.__dict__.items())
    #### raise exceptions
    raise_if_false(ValueError, os.path.isdir(out["dir_in"]))
    raise_if_false(ValueError, out["dir_out"] is None or os.path.isdir(out["dir_out"]))
    raise_if_false(
        ValueError,
        len(
            [
                True
                for x in [out["regex"], out["exts"], out["exts_env"], out["exts_json"]]
                if x is not None and x is True
            ],
        )
        <= 1,
    )
    raise_if_false(ValueError, out["maxdepth"] >= out["mindepth"] and out["mindepth"] > 0)
    #### convert range search range from alpha to int if given an alpha range
    out["range_search"] = [int_from_alpha(x) if isinstance(x, str) else x for x in out["range_search"]]
    #### when regex is None then its set using exts related args
    if out["regex"] is None:
        if out["exts_env"] is True:
            assert "GWSST" in os.environ
            out["exts_json"] = os.path.join(os.environ["GWSST"], "globals.json")
        if out["exts_json"] is not None:
            assert os.path.isfile(out["exts_json"])
            out["exts"] = import_json_obj(out["exts_json"], "video_exts")
        if out["exts"] is None:
            out["exts"] = ["mp4", "m4p", "mkv", "mpeg", "mpg", "avi", "wmv", "mov", "qt", "iso", "m4v", "flv"]
        assert out["exts"] is not None
        out["exts"] = "|".join([r"\." + ext if ext[0] != "." else ext for ext in out["exts"]])
        out["regex"] = "^.*(" + out["exts"] + ")$"
    #### get user specified part formatting for renaming multifiles
    out["parts_out"] = part_func_selection_terminal(gen_wrapped_indexable_callable())
    assert out["parts_out"] is not None
    out["prepart"] = prepart_selection_terminal()
    assert out["prepart"] is not None
    out["postpart"] = postpart_selection_terminal()
    assert out["postpart"] is not None
    #### remove entries from returned dict that are unused by the surrounding scope
    for k in ("exts_env", "exts_json", "exts", "part_out"):
        out.pop(k, None)
    #### return dictionary of modified cmd args
    return out


def listdir_dirs(
    dir_in: str = "",
    mindepth: int = 1,
    maxdepth: int = 1,
    excludes: Sequence[str] | None = None,
) -> list[str]:
    """Get dirs from directory within the recursive depths mindepth-maxdepth and remove excludes."""
    #### recursively find all dirs in dir_in between levels mindepth and maxdepth with excludes removed
    excludes = [] if excludes is None else excludes
    dirs_walk = [
        d[0]
        for d in os.walk(dir_in)
        if os.walk(dir_in)
        and d[0][len(dir_in) :].count(os.sep) <= maxdepth - 1
        and d[0][len(dir_in) :].count(os.sep) >= mindepth - 1
    ]
    #### remove all excludes from dirs_walk
    return [d for d in dirs_walk if all(False for e in excludes if e in d)]


def listdir_files(dir_in: str = ".", regex: str = ".*") -> list[str]:
    """Get files from dir_in that match the regex pattern reg."""
    files = [f for f in os.listdir(dir_in) if os.path.isfile(os.path.join(dir_in, f))]
    return [f for f in files if re.search(regex, f, re.IGNORECASE) is not None]


def gen_indexable_part_funcs() -> Sequence[tuple[Callable, int]]:
    """Set the static variable _parts_lists."""
    max_digits = 9
    max_length = 10 ** (max_digits - 1)  # arbitrarily set to max of 1 billion - 1
    length = max_length
    assert length <= max_length
    assert length >= 26  # not strictly necessary but helps num to alpha conversions

    #### indexable functions numbers and lowercase letters
    def nums(index):
        return str(index)

    def nums_one(index):
        return str(index + 1)

    # fmt: off
    alpha_lst = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    # fmt: on

    def alphas(index, lst=None):
        lst = alpha_lst
        # index_base26_lst = num_convert_base(index, 26)  # TODO:
        return "".join([lst[n] for n in num_convert_base(index, 26)])

    #### function generators for numbers padded with zeros
    def make_padded_nums(digits):
        def padded_nums(index):
            if num_digits(index) > digits:
                raise IndexError
            return str(index).zfill(digits)

        return padded_nums

    def make_padded_nums_one(digits):
        def padded_nums_one(index):
            if num_digits(index) > digits:
                raise IndexError
            return str(index + 1).zfill(digits)

        return padded_nums_one

    def make_padded_alphas(digits, lst=None):
        lst = alpha_lst if lst is None else lst

        def padded_alphas(index, lst=None):
            lst = alpha_lst if lst is None else lst
            if num_digits(index, 26) > digits:
                raise IndexError
            # index_base26_lst = num_convert_base(index, 26)  # TODO:
            alpha_str = "".join([lst[n] for n in num_convert_base(index, 26)])
            return alpha_str.rjust(digits, "a")

        return padded_alphas

    #### generate return var
    part_funcs = []
    part_funcs += [(make_padded_nums(i), 10**i) for i in reversed(range(1, max_digits + 1))]
    part_funcs += [(nums, length)]
    part_funcs += [(make_padded_nums_one(i), (10**i) - 1) for i in reversed(range(1, max_digits + 1))]
    part_funcs += [(nums_one, length)]
    part_funcs += [(make_padded_alphas(i), 26**i) for i in reversed(range(1, max_digits + 1))]
    part_funcs += [(alphas, 26**max_digits)]
    return part_funcs


def gen_wrapped_indexable_callable() -> Sequence[WrappedIndexableCallable]:
    return tuple(WrappedIndexableCallable(func, length) for func, length in gen_indexable_part_funcs())


def part_func_selection_terminal(part_funcs) -> WrappedIndexableCallable | None:
    print("##########################################")
    for i, func in enumerate(part_funcs):
        print(f"{i + 1}: {func[0]}, {func[1]} ... {func[-2]}, {func[-1]}")
    while True:
        choice = input("PROMPT: (q)uit; or select the naming increment style you prefer using a given index above: ")
        if choice in ("q", "quit"):
            print("INFO: aborting without selection")
            return None
        try:
            part_choice_int = int(choice) - 1
        except ValueError:
            print(
                f"WARNING: invalid input of '{choice}', expecting a positive integer between 1 and {len(part_funcs)}.",
            )
            continue
        if part_choice_int in range(0, len(part_funcs)):
            break
        print(f"WARNING: invalid input of '{choice}', expecting a positive integer between 1 and {len(part_funcs)}.")
    return part_funcs[part_choice_int]  # type: ignore[no-any-return] # TODO


def prepart_selection_terminal():
    recommended_preparts = ["", "-", "-part", "-pt", "-ep"]
    return pre_or_post_part_selection_terminal(recommended_preparts, "pre")


def postpart_selection_terminal():
    recommended_postparts = ["", "-", "-pt", "-ep"]
    return pre_or_post_part_selection_terminal(recommended_postparts, "post")


def pre_or_post_part_selection_terminal(recommended: list[str], pre_or_post_str: str):
    while True:
        print("##########################################")
        for i, prepart in enumerate(["prompt user to type a custom " + pre_or_post_str + "part"] + recommended):
            print(f"{i + 1}: '{prepart}'")
        choice = input(
            f"PROMPT: (q)uit; or select the naming {pre_or_post_str}part style you prefer using a given index above: ",
        )
        if choice in ("q", "quit"):
            print("INFO: aborting without selection")
            return None
        try:
            part_choice_int = int(choice) - 1
        except ValueError:
            print(
                f"WARNING: invalid input of '{choice}', expecting a positive integer between 1 and {len(recommended) + 1}.",
            )
            continue
        if part_choice_int == 0:
            choice_out = input(f"PROMPT: type a custom {pre_or_post_str}part style: ")
        elif part_choice_int in range(2, len(recommended) + 1):
            choice_out = recommended[part_choice_int - 1]
        else:
            print(f"WARNING: invalid input of '{choice}'.")
            continue
        while True:
            confirmation = input(f"PROMPT: use the naming scheme '{choice_out}'? (y)es; (n)o ")
            if confirmation in ("y", "yes"):
                print(f"INFO: using {pre_or_post_str}part naming scheme '{choice_out}'.")
                return choice_out
            if confirmation in ("n", "no"):
                print(f"INFO: rejecting {pre_or_post_str}part naming scheme '{choice_out}'.")
                break
            print(f"ERROR: unrecognized confirmation '{confirmation}'.")


class Multifile:
    """Allows operation on a contiguous group of similarly named files."""

    __prefix_style: str = r"( - |_|-|| )(cd|ep|episode|pt|part|| )( - |_|-|| )"
    _parts_lists: Sequence[WrappedIndexableCallable] | None = None

    def __init__(self, file_dict: dict) -> None:
        assert all(k in ["dir", "base", "prepart", "parts", "postpart", "ext"] for k in file_dict.keys())
        #### object attributes
        self.file_dict: dict = file_dict

    def __getitem__(self, key: str | int) -> Any:
        return self.file_dict[key] if isinstance(key, str) else self.__get_nth_file(key)

    ## methods that manipulate the state of the multifile or its referenced contents
    def mv(  # pylint: disable=[too-many-branches,too-many-locals,too-many-statements]
        self,
        prepart: str,
        parts_lst: Sequence,
        dir_out: str | None = None,
        range_mv: Sequence[int] | None = None,
        inplace: bool = False,
    ) -> Multifile | None:
        """Move this object's files using the pattern specified by parts."""
        #### asserts
        assert self.ismultifile(), self.to_list()
        #### set output multifile dict
        out_dict = dict(self.file_dict.items())
        out_dict["dir"] = dir_out if dir_out is not None else self["dir"]
        out_dict["prepart"] = prepart
        if range_mv is None:
            # if len(parts_lst) < self.size():
            #     print(f"ERROR: selected parts_out not big enough for multifile, choose new part or range\nERROR: partlist: {parts}\nERROR: multifile: {out_dict['parts']}")
            parts_lst = parts_lst[: self.size()]
        else:
            if str(parts_lst[0][-1]).isalpha() != str(range_mv[0]).isalpha():
                print(
                    f"WARNING: parts input ({parts_lst[0][-1]}) and range ({range_mv[0]}) should both be alpha characters or both be ints",
                )
            parts_lst = parts_lst[: len(range_mv)]
        #### describe the state of the potential mv
        print("INFO: printing potential mv cmds to be executed...")
        while True:
            #### check if mv operations are valid, if not then abort
            if range_mv is None:
                reduced_list = self.to_list()
            else:
                reduced_list = [
                    self.__get_nth_file(i)
                    for i, p in enumerate(self["parts"])
                    if p.lower() in [str(r) for r in range_mv]
                ]  # TODO: self.to_list()[i] wont work
                assert len(reduced_list) == len(
                    range_mv,
                ), f"ERROR: portion of range unaccounted for '{len(reduced_list)}' != '{len(range_mv)}'"  # TODO:
                if len(reduced_list) != self.size():
                    print(
                        f"INFO: partial mv being proposed for {len(reduced_list)} out of {self.size()} files revert to full mv with input 'r all'",
                    )
                    print(f"INFO: indices of partial mv (range): {range_mv}")
            out_dict["parts"] = parts_lst[: len(reduced_list)]
            #### create mf object based on out_dict which is manipulated by user input
            out_mf = Multifile(out_dict)
            new_list = out_mf.to_list(inplace=inplace)
            length = len(reduced_list)
            new_length = len(new_list)
            if length != new_length:
                print(f"ERROR: multifile length mismatch for lhs ({length}) and rhs ({new_length})")
            for i, (old, new) in enumerate(
                itertools.zip_longest(reduced_list, new_list, fillvalue="NO_EQUIVALENT_VALUE"),
            ):
                max_length = max(length, new_length)
                if max_length < 10:
                    print(f"  mv {old} {new}")
                else:
                    if i in [0, 1, 2, max_length - 3, max_length - 2, max_length - 1]:
                        print(f"  mv {old} {new}")
                    if i == 3:
                        print(f"  ... {max_length} files total")
            print(
                "PROMPT: (c)ontinue; (d)ir str; (b)ase str; (p)art str; (e)xt str; (r)ange_mv str; (i)nplace; (s)kip; (q)uit",
            )
            choice = input()
            if choice in ("c", "continue"):
                if length != new_length:
                    continue
                if not all(old not in new_list for old in reduced_list):
                    if all(old == new for old, new in zip(reduced_list, new_list)):
                        print("ERROR: src and target are the same")
                        continue
                    # TODO: hack to reverse lists to avoid mf overwriting itself during mv
                    old_char = self["parts"][0][-1]
                    new_char = out_mf["parts"][0][-1]
                    if old_char.isdigit():
                        if int(old_char) < int(new_char):
                            reduced_list.reverse()
                            new_list.reverse()
                    else:
                        if old_char < new_char:
                            reduced_list.reverse()
                            new_list.reverse()
                assert self.ismultifile()
                #### simulate mv and perform preliminary checks to avoid unwanted partial mvs
                sim_failed = False
                out_exists = [f for f in new_list if os.path.isfile(f)]
                for old, new in zip(reduced_list, new_list):
                    if old == new:
                        continue
                        # print(f"ERROR: mv sim error: old==new: mv '{old}' '{new}'")
                        # sim_failed = True; break
                    if not os.path.isfile(old):
                        print(f"ERROR: mv sim error: os.path.isfile(old) == False: mv '{old}' '{new}'")
                        sim_failed = True
                        break
                    if new in out_exists:
                        print(f"ERROR: mv sim error: os.path.isfile(new) is True: mv '{old}' '{new}'")
                        sim_failed = True
                        break
                    try_or(ValueError, out_exists.remove, old)
                    out_exists.append(new)
                if sim_failed:
                    continue
                if not all(ol in out_exists for ol in new_list):
                    print(
                        f"ERROR: mv sim error: new_list != out_list\nERROR: new_list: {new_list}\nERROR: out_exists: {out_exists}",
                    )
                    continue
                #### mv the files, they are assumed
                for old, new in zip(reduced_list, new_list):
                    if old != new:
                        #### asserts to prepare for mv
                        assert not os.path.isfile(new), f"ERROR: mv '{old}' '{new}'"
                        #### basic mv operation on single file
                        path_utils.mv(old, new)
                        #### asserts to prepare for mv
                        assert not os.path.isfile(old), f"ERROR: mv '{old}' '{new}'"
                    else:
                        #### basic mv operation on single file
                        path_utils.mv(old, new)
                    assert os.path.isfile(new), f"ERROR: mv '{old}' '{new}'"
                # self = out_mf # TODO: this has no effect, was this actually necessary?
                return out_mf
            assert choice not in ("c", "continue")
            if choice[:9] == "range_mv " or choice[:2] == "r ":
                tmp_range = choice.split(" ", 1)[1]
                if tmp_range == "all":
                    range_mv = None
                else:
                    tmp_parsed = parse_range(tmp_range, throw=False)
                    if tmp_parsed:
                        if str(tmp_parsed[0]).isalpha() != self.__isalpha():
                            print("ERROR: range and multifile must both be alpha characters or both be ints")
                        else:
                            range_mv = tmp_parsed
            elif choice in ("inplace", "i"):
                inplace = not inplace
            elif choice in ("skip", "s"):
                print("INFO: skipping mv of this batch of multifiles")
                break
            elif choice in ("quit", "q"):
                sys.exit()
            elif choice[:4] == "dir " or choice[:2] == "d ":
                tmp_dir = choice.split(" ", 1)[1]
                if not os.path.isdir(tmp_dir):
                    print(f"ERROR: the following is not a dir: {tmp_dir}")
                else:
                    out_dict["dir"] = tmp_dir
            elif choice[:5] == "base " or choice[:2] == "b ":
                out_dict["base"] = choice.split(" ", 1)[1]  # TODO: should this be [1:]?
                if not inplace:
                    out_dict["postpart"] = None
            elif choice[:5] == "part " or choice[:2] == "p ":
                tmp_lst = part_func_selection_terminal(gen_wrapped_indexable_callable())
                parts_lst = tmp_lst if tmp_lst is not None else parts_lst  # type: ignore[assignment] # TODO
            elif choice[:4] == "ext " or choice[:2] == "e ":
                out_dict["ext"] = choice.split(" ", 1)[1]
            else:
                print("ERROR: invalid input for prompt")
            print("#######################################################")
        return None

    ## methods that examine the state of the multifile or its referenced contents
    def ismultifile(self) -> bool:
        """Ensure this object has at least two valid and contiguous files."""
        return all(os.path.isfile(f) for f in self.to_list()) and self.size() > 1

    def size(self) -> int:
        return len(self["parts"])

    def to_list(self, exc_dir: bool = False, inplace: bool = True) -> list[str]:
        """Return this object's files to a list of strings."""
        return [self.__get_nth_file(i, exc_dir, inplace) for i in range(self.size())]  # TODO: size() slow

    #### private methods
    def __get_nth_file(self, n: int, exc_dir: bool = False, inplace: bool = True) -> str:
        """Get this multifiles n'th file."""
        assert n < self.size(), f"ERROR: DEBUG: {str(n)}:{str(self.file_dict)}"
        out = []
        if not inplace:
            out += [self["base"], self["postpart"], self["prepart"], self["parts"][n], self["ext"]]
        else:
            out += [self["base"], self["prepart"], self["parts"][n], self["postpart"], self["ext"]]
        if not exc_dir:
            out[0] = os.path.join(self["dir"], out[0])
        return "".join([str(x) for x in out if x is not None])

    def __isalpha(self) -> bool:
        return self["parts"][0][-1].isalpha()  # type: ignore[no-any-return]

    @classmethod
    def extract_mfs(
        cls,
        file_strs: Sequence[str],
        min_in: int = 0,
        max_in: int = 1,
    ):  # pylint: disable=[too-many-branches,too-many-locals]
        assert min_in <= max_in, (min_in, max_in)
        file_strs_use = list(file_strs)
        #### max string length for regex iterating
        # max_length = max(len(str(f)) for f in files)  # TODO: how was this expected to be used?
        #### all of the possible combination of parts
        mf_details = []
        for parts_lst in cls.__get_parts_lists():  # pylint: disable=[not-an-iterable]
            matches = []
            ### find potential first file matches for every file for each part in parts_lst
            for i, part in enumerate(parts_lst[min_in : max_in + 1]):
                part_index = i + min_in
                if part is None:
                    break  # TODO: this was originally a continue?
                for f in file_strs_use:
                    for index in re.finditer(part, f):
                        regex = "^(.{" + str(index.start()) + "})" + f"({parts_lst[part_index]}" + r")(.*)(\..*)$"
                        match = re.search(regex, f, re.IGNORECASE)
                        if match:
                            matches.append((part_index, match))
            for part_index, match in matches:
                base = match.group(1)
                part = match.group(2)
                postpart = match.group(3)
                ext = match.group(4)
                num_files = 0
                for i, part in enumerate(parts_lst[part_index:]):
                    if part is None:
                        continue
                    part_match = "".join(c for c in part if not c.isdigit())  # TODO: check
                    # TODO: should this be ignore case?
                    part = re.sub(part_match, part_match, part, re.IGNORECASE)
                    file_out = base + part + postpart + ext
                    if file_out not in file_strs_use:
                        break
                    num_files += 1
                if num_files > 1:
                    # TODO: should this be ignore case?
                    m = re.search(r"^(.*?)" + cls.__prefix_style + r"$", base, re.IGNORECASE)
                    assert m is not None
                    base = m.group(1)
                    mf_detail = {
                        "base": base,
                        "prepart": m.group(2) + m.group(3) + m.group(4),
                        "parts": parts_lst[part_index : part_index + num_files],
                        "postpart": postpart,
                        "ext": ext,
                    }
                    files_gen = tuple(
                        f"{mf_detail['base']}{mf_detail['prepart']}{p}{mf_detail['postpart']}{mf_detail['ext']}"
                        for p in mf_detail["parts"]
                    )
                    assert all(f in file_strs_use for f in files_gen), (file_strs_use, files_gen)
                    mf_details.append(mf_detail)

        out = max(mf_details, default=None, key=lambda mf: len(mf["parts"]))
        if out is not None:
            for p in out["parts"]:
                f_out = f"{out['base']}{out['prepart']}{p}{out['postpart']}{out['ext']}"
                file_strs_use.remove(f_out)
            return [out] + cls.extract_mfs(file_strs=file_strs_use, min_in=min_in, max_in=max_in)
        return []

    #### class methods
    @classmethod
    def extract_multifiles(
        cls,
        dir_in: str,
        files: list[str],
        min_in: int = 0,
        max_in: int = 1,
    ) -> tuple[Multifile, ...]:
        """Returns a list of Multifile objects in dir_in."""
        #### check and set inputs
        assert os.path.isdir(dir_in), dir_in
        assert all(os.path.isfile(os.path.join(dir_in, f)) for f in files), (dir_in, files)
        assert min_in <= max_in, (min_in, max_in)
        #### initializes outputs
        return tuple(cls({"dir": dir_in, **mf_detail}) for mf_detail in cls.extract_mfs(files, min_in, max_in))

    @classmethod
    def __get_parts_lists(cls) -> Sequence[WrappedIndexableCallable]:
        """Get the parts generators for finding contiguous files."""
        if cls._parts_lists is None:
            cls._parts_lists = gen_wrapped_indexable_callable()
        assert cls._parts_lists is not None
        assert isinstance(cls._parts_lists, Sequence)
        return cls._parts_lists


####################################################################################################
####################################################################################################
def main(argparse_args: Sequence[str] | None = None) -> None:
    #### parses script input to populate args dict
    args = parse_inputs(argparse_args)
    #### recursively find all dirs in dir_in between levels mindepth and maxdepth with excludes removed
    dirs_walk = listdir_dirs(args["dir_in"], args["mindepth"], args["maxdepth"], args["excludes"])
    #### print useful info
    print(f"INFO: root dir to search for multifiles: '{args['dir_in']}'")
    if len(dirs_walk) > 1:
        print(
            f"INFO: searching recursively {args['mindepth']}-{args['maxdepth']} dirs deep... found {len(dirs_walk)} dirs",
        )
    print(f"INFO: regex file filter: '{args['regex']}'")
    #### search for multifiles in dirs_walk
    # print(f"dirs_walk={dirs_walk}")
    mfs_list = [
        Multifile.extract_multifiles(
            d,
            listdir_files(d, args["regex"]),
            min_in=args["range_search"][0],
            max_in=args["range_search"][-1],
        )
        for d in dirs_walk
    ]
    print(f"INFO: found {sum(len(mfs) for mfs in mfs_list)} multifile candidates")
    #### mv each multifile
    for mfs in mfs_list:
        for mf in mfs:
            mf.mv(args["prepart"], args["parts_out"], args["dir_out"], args["range_mv"], args["inplace"])
    print("INFO: SUCCESS")


if __name__ == "__main__":
    main()
