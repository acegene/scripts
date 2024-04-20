#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import subprocess
import sys

from typing import Dict, Optional, Sequence

from utils import json_utils

## TODO:
## - cannot specify force via prompt or per bisync execution


_JSON_CFG_DEFAULT = os.path.join(os.path.expanduser("~"), ".config", "cfg-gws.json")
_RCLONE_TEST = "RCLONE_TEST"


def find_cfg_file(dir_: str) -> Optional[str]:
    for root, _, files in os.walk(dir_):
        for file in files:
            if file == "cfg-gws.json":
                return os.path.abspath(os.path.join(root, file))
    return None


def _init_rclone_bisync(rclone, rclone_bk_details: Dict, json_cfg: str) -> int:
    found_cfg = _JSON_CFG_DEFAULT if os.path.exists(_JSON_CFG_DEFAULT) else None
    for rclone_bk_detail in rclone_bk_details:
        local = json_utils.create_path_from_json_relative_path(rclone_bk_detail["loc"])
        bk_local = json_utils.create_path_from_json_relative_path(rclone_bk_detail["bk_loc"])
        remote = os.path.expandvars(rclone_bk_detail["rem"])

        if not os.path.exists(local):
            os.makedirs(local, exist_ok=True)
        if not os.path.exists(bk_local):
            os.makedirs(bk_local, exist_ok=True)

        rclone_test_path = os.path.join(local, _RCLONE_TEST)
        if not os.path.exists(rclone_test_path):
            if len(os.listdir(local)) != 0:
                print(f"ERROR: expected local={local} to be empty")
                sys.exit(1)
            rclone_test_cp_params = ["copyto", f"{remote}/RCLONE_TEST", rclone_test_path]
            rclone_test_cp_params_str = "' '".join(rclone_test_cp_params)
            cmd_str = f"'{rclone}' '{rclone_test_cp_params_str}'"
            print(f"INFO: EXEC: {cmd_str}")
            rclone_result = subprocess.run([rclone] + rclone_test_cp_params, check=False, capture_output=False)
            if rclone_result.returncode != 0:
                print(f"ERROR: {cmd_str}; rclone_result.returncode={rclone_result.returncode}")
                return rclone_result.returncode

            resync_params = ["bisync", "--resync", local, remote, "--check-access", "--verbose"]
            resync_params_str = "' '".join(resync_params)
            cmd_str = f"'{rclone}' '{resync_params_str}'"
            resync_result = subprocess.run([rclone] + resync_params, check=False, capture_output=False)
            if resync_result.returncode != 0:
                print(f"ERROR: {cmd_str}; resync_result.returncode={resync_result.returncode}")
                return resync_result.returncode
        if found_cfg is None:
            found_cfg = find_cfg_file(local)

    if not os.path.exists(_JSON_CFG_DEFAULT):
        assert found_cfg is not None
        parent_dir = os.path.dirname(_JSON_CFG_DEFAULT)
        os.makedirs(parent_dir, exist_ok=True)
        found_cfg_abs = os.path.abspath(found_cfg)
        os.symlink(found_cfg_abs, _JSON_CFG_DEFAULT)
        print(f"INFO: created symlink '{found_cfg_abs}' -> '{_JSON_CFG_DEFAULT}'")

    return 0


def _run_rclone_bisync(rclone, rclone_bk_details: Dict, force: bool) -> int:
    for rclone_bk_detail in rclone_bk_details:
        local = json_utils.create_path_from_json_relative_path(rclone_bk_detail["loc"])
        bk_local = json_utils.create_path_from_json_relative_path(rclone_bk_detail["bk_loc"])
        remote = os.path.expandvars(rclone_bk_detail["rem"])
        bk_remote = os.path.expandvars(rclone_bk_detail["bk_rem"])

        current_utc_time = datetime.datetime.utcnow()
        formatted_time = current_utc_time.strftime("%y%m%dt%H%M%Sz")

        bisync_params = [
            "bisync",
            local,
            remote,
            "--backup-dir1",
            bk_local,
            "--backup-dir2",
            bk_remote,
            "--conflict-resolve",
            "newer",
            "--conflict-loser",
            "pathname",
            "--conflict-suffix",
            f"-{formatted_time}-loc,-{formatted_time}-rem",
            "--suffix",
            f"-{formatted_time}-bk",
            "--suffix-keep-extension",
            "--check-access",
            "--resilient",
            "--verbose",
        ]

        if force:
            bisync_params.append("--force")

        bisync_params_str = "' '".join(bisync_params)
        cmd_str = f"'{rclone}' '{bisync_params_str}'"
        print(f"INFO: EXEC: {cmd_str}")
        bisync_result = subprocess.run([rclone] + bisync_params, check=False, capture_output=False)
        if bisync_result.returncode != 0:
            print(f"ERROR: {cmd_str}; bisync_result.returncode={bisync_result.returncode}")
            return bisync_result.returncode
    return 0


def main(argparse_args: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run rclone bisync with details extracted from json.")
    parser.add_argument("--init", action="store_true", help="TODO")
    parser.add_argument("--force", action="store_true", help="Run in situations like too many deletes.")
    parser.add_argument("--json-cfg", default=_JSON_CFG_DEFAULT, help="Json cfg file to extract bisync backup settings")
    parser.add_argument("--rclone", default="rclone", help="The rclone version to use")
    args = parser.parse_args(argparse_args)

    with open(args.json_cfg, "r", encoding="utf-8") as file:
        rclone_bk_details = json.load(file)["rclone_bk_details"]

    if args.init:
        return _init_rclone_bisync(args.rclone, rclone_bk_details, args.json_cfg)

    return _run_rclone_bisync(args.rclone, rclone_bk_details, args.force)


if __name__ == "__main__":
    sys.exit(main())
