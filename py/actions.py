#!/usr/bin/env python3
#
# Copies files using a json file to describe actions
#
# todos
#   * detect/specify (?) binary files and handle binary file diffs

import argparse
import difflib
import filecmp
import json
import os
import shutil
import sys

from typing import Callable, Dict, List, Optional

from utils import cli_utils
from utils import json_utils
from utils import path_utils


def print_diff(lhs, rhs, lhs_encoding="utf-8", rhs_encoding="utf-8"):
    with path_utils.open_unix_safely(lhs, encoding=lhs_encoding) as lhs_file:
        lhs_lines = lhs_file.readlines()
    with path_utils.open_unix_safely(rhs, encoding=rhs_encoding) as rhs_file:
        rhs_lines = rhs_file.readlines()
    diff = difflib.unified_diff(
        rhs_lines,
        lhs_lines,
        fromfile="original",
        tofile="edited",
    )
    print(f"INFO: showing potential changes from writing '{lhs}' to '{rhs}':")
    print("".join(list(diff)))


def preview_cp(src_path: str, dst_path: str) -> str:
    print(f"INFO: PREVIEW MODE: cp '{src_path}' '{dst_path}'")
    return dst_path


def action_make_symlinks(src, links, options=None, references=None) -> Dict:
    # pylint: disable=unused-argument
    relatives = None if references is None else references.get("relatives", None)

    src_path = json_utils.create_path_from_json_relative_path(src, relatives)
    link_paths = []
    for link in links:
        link_path = json_utils.create_path_from_json_relative_path(link, relatives)
        if os.path.exists(link_path):
            if os.path.islink(link_path):
                print(f"INFO: skipping: make_symlink '{src_path}' '{link_path}'; symlink already exists")
                link_paths.append(link_path)
                continue
            print(f"ERROR: skipping: make_symlink '{src_path}' '{link_path}'; symlink path has non-symlink object")
            return {"error_code": 1, "link_paths": link_paths}
        print(f"INFO: make_symlink '{src_path}' '{link_path}'")
        os.symlink(src_path, link_path)
        link_paths.append(link_path)
    return {"error_code": 0, "link_paths": link_paths}


def get_path_type_from_json_path(obj):
    return obj["path"][-1]["path_type"]


def action_cp_to_dst_directory(src, dst, options=None, relatives=None) -> Dict:
    # pylint: disable=unused-argument
    # for (dirpath, dirnames, filenames) in os.walk(path):
    #     for dirname in dirnames:
    #         print(os.sep.join([dirpath, dirname]))
    assert False


def action_cp_to_dst_file(src, dst, options=None, relatives=None) -> Dict:
    # pylint: disable=[too-many-branches,too-many-return-statements,too-many-statements]
    options = {} if options is None else options

    overwrite_status = options.get("overwite_status", "NO_W_ERROR")
    preview = options.get("preview", True)

    cp_func: Callable[[str, str], str] = preview_cp if preview else shutil.copy2  # type: ignore

    src_path = json_utils.create_path_from_json_relative_path(src, relatives)
    dst_path = json_utils.create_path_from_json_relative_path(dst, relatives)

    if os.path.exists(dst_path):
        if filecmp.cmp(src_path, dst_path):
            print(f"INFO: skipping: cp '{src_path}' '{dst_path}'; contents equal")
            return {"error_code": 0, "dst_path": dst_path}

        if overwrite_status == "NO":
            print(f"INFO: skipping: cp '{src_path}' '{dst_path}'; dst_path='{dst_path}' exists")
        elif overwrite_status == "NO_W_ERROR":
            print(f"ERROR: skipping: cp '{src_path}' '{dst_path}'; dst_path='{dst_path}' exists")
            return {"error_code": 1}
        elif overwrite_status == "YES":
            print(f"INFO: overwriting dst_path='{dst_path}'")
            print(f"INFO: cp '{src_path}' '{dst_path}'")
            cp_func(src_path, dst_path)
        elif overwrite_status == "YES_W_PROMPT":
            if cli_utils.prompt_return_bool(f"PROMPT: overwrite dst_path='{dst_path}'? [Y/y] ", ["y", "Y"]):
                print(f"INFO: overwriting dst_path='{dst_path}'")
                print(f"INFO: cp '{src_path}' '{dst_path}'")
                cp_func(src_path, dst_path)
            else:
                print(f"INFO: skipping: cp '{src_path}' '{dst_path}', due to prompt response")
                return {"error_code": 0, "dst_path": None}
        elif overwrite_status == "YES_W_DIFF_W_PROMPT":
            print_diff(src_path, dst_path)
            if cli_utils.prompt_return_bool(f"PROMPT: overwrite dst_path='{dst_path}'? [Y/y] ", ["y", "Y"]):
                print(f"INFO: overwriting dst_path='{dst_path}'")
                print(f"INFO: cp '{src_path}' '{dst_path}'")
                cp_func(src_path, dst_path)
            else:
                print(f"INFO: skipping: cp '{src_path}' '{dst_path}', due to prompt response")
                return {"error_code": 0, "dst_path": None}
        elif overwrite_status == "YES_W_PROMPT_W_ABORT_ON_NO":
            if cli_utils.prompt_return_bool(f"PROMPT: overwrite dst_path='{dst_path}'? [Y/y] ", ["y", "Y"]):
                print(f"INFO: overwriting dst_path='{dst_path}'")
                print(f"INFO: cp '{src_path}' '{dst_path}'")
                cp_func(src_path, dst_path)
            else:
                print(f"INFO: skipping: cp '{src_path}' '{dst_path}', due to prompt response")
                print("INFO: aborting due to prompt response")
                return {"error_code": 1}
        elif overwrite_status == "YES_W_DIFF_W_PROMPT_W_ABORT_ON_NO":
            if cli_utils.prompt_return_bool(f"PROMPT: overwrite dst_path='{dst_path}'? Y/y", ["y", "Y"]):
                print(f"INFO: overwriting dst_path='{dst_path}'")
                print(f"INFO: cp '{src_path}' '{dst_path}'")
                cp_func(src_path, dst_path)
            else:
                print(f"INFO: skipping: cp '{src_path}' '{dst_path}', due to prompt response")
                print("INFO: aborting due to prompt response")
                return {"error_code": 1}
        else:
            print(f"ERROR: unexpected overwrite_status={overwrite_status}")
            return {"error_code": 1}
    else:
        print(f"INFO: cp '{src_path}' '{dst_path}'")
        cp_func(src_path, dst_path)

    return {"error_code": 0, "dst_path": dst_path}


def action_cp_to_dsts(src, dsts, options=None, references=None) -> Dict:
    relatives = None if references is None else references.get("relatives", None)

    src_path_type = get_path_type_from_json_path(src)

    for dst in dsts:
        dst_path_type = get_path_type_from_json_path(dst)
        if src_path_type != dst_path_type:
            print("ERROR: mismatched path_type; src_path_type != dst_path_type; {src_path_type} != {dst_path_type}")
            return {"error_code": 1, "dst_paths": []}

    action_cp_to_dst: Callable[..., Dict]
    if src_path_type == "DIRECTORY":
        action_cp_to_dst = action_cp_to_dst_directory
    elif src_path_type == "FILE":
        action_cp_to_dst = action_cp_to_dst_file
    else:
        print(f"ERROR: unrecognized src_path_type={src_path_type}")
        return {"error_code": 1, "dst_paths": []}

    dst_paths: List[Optional[Dict]] = []
    for dst in dsts:
        cp_to_dst_result = action_cp_to_dst(src, dst, options=options, relatives=relatives)
        if cp_to_dst_result["error_code"] != 0:
            return {"error_code": cp_to_dst_result["error_code"], "dst_paths": dst_paths}
        dst_paths.append(cp_to_dst_result["dst_path"])

    return {"error_code": 0, "dst_paths": dst_paths}


def handle_action(action, references, prev_ret_val=None) -> Dict:
    prev_ret_val_kwargs = {}
    if action.get("prev_ret_val_to_extract", None) is not None:
        for key, value in action["prev_ret_val_to_extract"].items():
            prev_ret_val_kwargs[value] = prev_ret_val[key]

    if action["action_type"] == "cp":
        return action_cp_to_dsts(references=references, **prev_ret_val_kwargs, **action.get("kwargs", {}))
    if action["action_type"] == "make_symlinks":
        return action_make_symlinks(references=references, **action.get("kwargs", {}))
    print(f"FATAL: unrecognized action['action_type']={action['action_type']}; references={references}")
    sys.exit(1)


def parse_json_and_execute_actions(action_json):
    with path_utils.open_unix_safely(action_json, encoding="utf-8") as f:
        json_data = json.load(f)

    references = json_data.get("references") if "references" in json_data else {}

    prev_ret_val: Dict = {}
    for action in json_data.get("actions"):
        prev_ret_val = handle_action(action, references, prev_ret_val=prev_ret_val)


def parse_inputs() -> Dict:
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="json file specifying actions")
    args = parser.parse_args()

    return {"json_path": args.json}


if __name__ == "__main__":
    inputs = parse_inputs()
    parse_json_and_execute_actions(inputs["json_path"])
