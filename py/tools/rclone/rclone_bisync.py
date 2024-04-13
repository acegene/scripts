#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import subprocess

from typing import Dict, List, Optional

from utils import json_utils


_JSON_CFG_DEFAULT = os.path.join(os.path.expanduser("~"), ".config", "cfg-gws.json")


def run_rclone_bisync(rclone, rclone_bk_details: Dict, force: bool) -> int:
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

        quoted_space = "' '"
        print(f"INFO: EXEC: '{rclone}' '{quoted_space.join(bisync_params)}'")
        bisync_result = subprocess.run([rclone] + bisync_params, check=False, capture_output=False)
        if bisync_result.returncode != 0:
            print(f"ERROR: '{rclone}' '{quoted_space.join(bisync_params)}'; bisync_result.returncode={bisync_result.returncode}")
            return bisync_result.returncode
    return 0


def main(argparse_args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run rclone bisync with details extracted from json.")
    parser.add_argument("--force", action="store_true", help="Run in situations like too many deletes.")
    parser.add_argument("--json-cfg", default=_JSON_CFG_DEFAULT, help="Json cfg file to extract bisync backup settings")
    parser.add_argument("--rclone", default="rclone", help="The rclone version to use")
    args = parser.parse_args(argparse_args)

    with open(args.json_cfg, "r", encoding="utf-8") as file:
        rclone_bk_details = json.load(file)["rclone_bk_details"]

    return run_rclone_bisync(args.rclone, rclone_bk_details, args.force)


if __name__ == "__main__":
    main()
