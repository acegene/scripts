#!/usr/bin/env python3
import argparse
import datetime
import os
import subprocess
import sys
from collections.abc import Sequence

import yaml  # type: ignore[import-untyped]
from utils import cfg_utils
from utils import log_manager
from utils import path_utils

## TODO:
## - cannot specify force via prompt or per bisync execution
## - dry run with summary of expected changes
## - does not create local dir if does not exist
## - specify remotes
## - in case of conflicts, a diff should be shown prior to making changes

_LOG_FILE_PATH, _LOG_CFG_DEFAULT = log_manager.get_default_log_paths(__file__)
logger = log_manager.LogManager()

_CFG_DEFAULT = os.path.join(os.path.expanduser("~"), ".config", "cfg-gws.yaml")
_RCLONE_TEST = "RCLONE_TEST"


def find_cfg_file(dir_: str) -> str | None:
    for root, _, files in os.walk(dir_):
        for file in files:
            if file == "cfg-gws.yaml":
                return os.path.abspath(os.path.join(root, file))
    return None


def _init_rclone_bisync(rclone, rclone_bk_details: dict, relatives: dict[str, dict]) -> int:
    # pylint: disable=too-many-locals
    found_cfg = _CFG_DEFAULT if os.path.exists(_CFG_DEFAULT) else None

    listremotes_result = subprocess.run([rclone] + ["listremotes"], check=True, capture_output=True)
    remotes = tuple(r.decode().rstrip(":") for r in listremotes_result.stdout.split())

    if len(remotes) == 0:
        logger.error("no remotes have been configured!")
        return 1

    for rclone_bk_detail in rclone_bk_details:
        local = cfg_utils.create_path_from_relative_path(rclone_bk_detail["loc"], relatives)
        bk_local = cfg_utils.create_path_from_relative_path(rclone_bk_detail["bk_loc"], relatives)
        remote = rclone_bk_detail["rem"]

        remote_base = remote.split(":")[0]
        if remote_base not in remotes:
            logger.info(f"remote={remote_base} will be skipped as it is not configured")
            continue

        if not os.path.exists(local):
            os.makedirs(local, exist_ok=True)
        if not os.path.exists(bk_local):
            os.makedirs(bk_local, exist_ok=True)

        rclone_test_path = os.path.join(local, _RCLONE_TEST)
        if not os.path.exists(rclone_test_path):
            if len(os.listdir(local)) != 0:
                logger.error(f"expected local={local} to be empty")
                sys.exit(1)
            rclone_test_cp_params = ["copyto", f"{remote}/RCLONE_TEST", rclone_test_path]
            rclone_test_cp_params_str = "' '".join(rclone_test_cp_params)
            cmd_str = f"'{rclone}' '{rclone_test_cp_params_str}'"
            logger.info(f"EXEC: {cmd_str}")
            rclone_result = subprocess.run([rclone] + rclone_test_cp_params, check=False, capture_output=False)
            if rclone_result.returncode != 0:
                logger.error(f"{cmd_str}; rclone_result.returncode={rclone_result.returncode}")
                return rclone_result.returncode

            resync_params = ["bisync", "--resync", local, remote, "--check-access", "-v"]
            resync_params_str = "' '".join(resync_params)
            cmd_str = f"'{rclone}' '{resync_params_str}'"
            resync_result = subprocess.run([rclone] + resync_params, check=False, capture_output=False)
            if resync_result.returncode != 0:
                logger.error(f"{cmd_str}; resync_result.returncode={resync_result.returncode}")
                return resync_result.returncode
        if found_cfg is None:
            found_cfg = find_cfg_file(local)

    if not os.path.exists(_CFG_DEFAULT):
        assert found_cfg is not None
        parent_dir = os.path.dirname(_CFG_DEFAULT)
        os.makedirs(parent_dir, exist_ok=True)
        found_cfg_abs = os.path.abspath(found_cfg)
        os.symlink(found_cfg_abs, _CFG_DEFAULT)
        logger.info(f"created symlink '{found_cfg_abs}' -> '{_CFG_DEFAULT}'")

    return 0


def _run_rclone_bk_clean(
    rclone,
    rclone_bk_details: dict,
    /,
    dry_run: bool,
    force: bool,
) -> int:
    listremotes_result = subprocess.run([rclone] + ["listremotes"], check=True, capture_output=True)
    remotes = tuple(r.decode().rstrip(":") for r in listremotes_result.stdout.split())

    if len(remotes) == 0:
        logger.error("no remotes have been configured!")
        return 1

    for rclone_bk_detail in rclone_bk_details:
        bk_remote = rclone_bk_detail["bk_rem"]
        bk_clean_args = rclone_bk_detail.get("bk_clean_args", tuple())

        remote_base = bk_remote.split(":")[0]
        if remote_base not in remotes:
            logger.info(f"remote={remote_base} will be skipped as it is not configured")
            continue

        bisync_params = [
            "delete",
            bk_remote,
            *bk_clean_args,
            "-v",
        ]

        if dry_run:
            bisync_params.append("--dry-run")
        if force:
            bisync_params.append("--force")

        bisync_params_str = "' '".join(bisync_params)
        cmd_str = f"'{rclone}' '{bisync_params_str}'"
        logger.info(f"EXEC: {cmd_str}")
        bisync_result = subprocess.run([rclone] + bisync_params, check=False, capture_output=False)
        if bisync_result.returncode != 0:
            logger.error(f"{cmd_str}; bisync_result.returncode={bisync_result.returncode}")
            return bisync_result.returncode
    return 0


def _run_rclone_bisync(
    rclone,
    rclone_bk_details: dict,
    relatives: dict[str, dict],
    /,
    dry_run: bool,
    force: bool,
) -> int:
    # pylint: disable=too-many-locals
    listremotes_result = subprocess.run([rclone] + ["listremotes"], check=True, capture_output=True)
    remotes = tuple(r.decode().rstrip(":") for r in listremotes_result.stdout.split())

    if len(remotes) == 0:
        logger.error("no remotes have been configured!")
        return 1

    for rclone_bk_detail in rclone_bk_details:
        local = cfg_utils.create_path_from_relative_path(rclone_bk_detail["loc"], relatives)
        bk_local = cfg_utils.create_path_from_relative_path(rclone_bk_detail["bk_loc"], relatives)
        remote = rclone_bk_detail["rem"]
        bk_remote = rclone_bk_detail["bk_rem"]

        remote_base = remote.split(":")[0]
        if remote_base not in remotes:
            logger.info(f"remote={remote_base} will be skipped as it is not configured")
            continue

        formatted_utc_time = datetime.datetime.utcnow().strftime("%y%m%dt%H%M%Sz")

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
            f"{formatted_utc_time}-loc,{formatted_utc_time}-rem",
            "--suffix",
            f".{formatted_utc_time}-bk",
            "--suffix-keep-extension",
            "--check-access",
            "--resilient",
            "-v",
        ]

        if dry_run:
            bisync_params.append("--dry-run")
        if force:
            bisync_params.append("--force")

        bisync_params_str = "' '".join(bisync_params)
        cmd_str = f"'{rclone}' '{bisync_params_str}'"
        logger.info(f"EXEC: {cmd_str}")
        bisync_result = subprocess.run([rclone] + bisync_params, check=False, capture_output=False)
        if bisync_result.returncode != 0:
            logger.error(f"{cmd_str}; bisync_result.returncode={bisync_result.returncode}")
            return bisync_result.returncode
    return 0


def main(argparse_args: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run rclone bisync with details extracted from json.")
    parser.add_argument("--log")
    parser.add_argument("--log-cfg", default=_LOG_CFG_DEFAULT, help="Log cfg; empty str uses LogManager default cfg")

    parser.add_argument("--cfg", default=_CFG_DEFAULT, help="Json cfg file to extract bisync backup settings")
    parser.add_argument("--dry-run", "--dry", action="store_true", help="Prevent modifications, show changes preview")
    parser.add_argument("--force", action="store_true", help="Run even in situations like too many deletes")
    parser.add_argument("--rclone", default="rclone", help="The rclone version to use")

    flag_group = parser.add_mutually_exclusive_group()
    parser.set_defaults(flag="sync")
    flag_group.add_argument("--bk-clean", action="store_const", const="bk_clean", dest="flag")
    flag_group.add_argument("--init", action="store_const", const="init", dest="flag")
    flag_group.add_argument("--sync", "--bisync", action="store_const", const="sync", dest="flag")

    args = parser.parse_args(argparse_args)

    log_manager.LogManager.setup_logger(globals(), log_cfg=args.log_cfg, log_file=args.log)

    with path_utils.open_unix_safely(args.cfg, encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)

    rclone_bk_details = yaml_data["rclone_bk_details"]
    references = yaml_data.get("references", {})

    match args.flag:
        case "init":
            return _init_rclone_bisync(args.rclone, rclone_bk_details, references)
        case "bk_clean":
            return _run_rclone_bk_clean(args.rclone, rclone_bk_details, dry_run=args.dry_run, force=args.force)
        case "sync":
            return _run_rclone_bisync(
                args.rclone,
                rclone_bk_details,
                references,
                dry_run=args.dry_run,
                force=args.force,
            )
        case _:
            assert False, args.flag


if __name__ == "__main__":
    sys.exit(main())
