#!/usr/bin/env python3
import argparse
import datetime
import glob
import os
import re
import subprocess
import sys
from collections import OrderedDict
from collections.abc import Sequence

from utils import argparse_utils
from utils import cli_utils
from utils import log_manager
from utils import path_utils

_LOG_FILE_PATH, _LOG_CFG_DEFAULT = log_manager.get_default_log_paths(__file__)
logger = log_manager.LogManager()

# TODO:
# * parse lsblk by column -> lsblk -p -S --json
# * most recent mountale paths should take priority


def run_as_sudo() -> int:
    logger.warning("need to be sudo, relaunching as sudo")
    pythonpath = os.environ.get("PYTHONPATH", "")
    result = subprocess.run(
        ["sudo", f"PYTHONPATH={pythonpath}", "python3", os.path.abspath(__file__)] + sys.argv[1:],
        check=False,
    )
    return result.returncode


if os.geteuid() != 0:
    sys.exit(run_as_sudo())

_USER = os.environ.get("SUDO_USER")
assert isinstance(_USER, str)

_LOG_CACHE_BASE = os.path.splitext(os.path.basename(__file__))[0]
_LOG_CACHE = os.path.join("/home", _USER, ".log", f"{_LOG_CACHE_BASE}.log")
_HEADING = "time,partition,dir_mount,dir_bl,drive_details,lsblk -p -S\n"


def _append(file: str, s: str) -> None:
    with path_utils.open_unix_safely(file, "r+") as f:
        f.seek(0, 2)
        f.write(s)


def _get_bl_paths() -> list[str]:
    bl_paths = []
    pattern = re.compile(r"/media/bl(?:-\d+)?")
    for entry in os.listdir("/media"):
        full_path = os.path.join("/media", entry)
        if os.path.exists(full_path):
            if pattern.match(full_path):
                bl_paths.append(full_path)
    return bl_paths


def _get_mounted_paths() -> list[str]:
    mount_paths = []
    pattern = re.compile(r"/media/mount(?:-\d+)?")
    for entry in os.listdir("/media"):
        full_path = os.path.join("/media", entry)
        if os.path.exists(full_path):
            if pattern.match(full_path):
                mount_paths.append(full_path)
    return mount_paths


def _get_aligned_bl_and_mount_paths() -> list[tuple[str, str]]:
    bl_paths = _get_bl_paths()
    mounted_paths = _get_mounted_paths()
    if len(bl_paths) != len(mounted_paths):
        logger.error(f"bl_paths={bl_paths}\nmounted_paths={mounted_paths}")
        sys.exit(1)

    aligned_bl_and_mount_paths = []
    for mounted_path in mounted_paths:
        mounted_path_index = int(mounted_path[13:])
        for bl_path in bl_paths:
            if mounted_path_index == int(bl_path[10:]):
                aligned_bl_and_mount_paths.append((bl_path, mounted_path))
                break

    if len(aligned_bl_and_mount_paths) != len(mounted_paths):
        logger.error(
            f"bl_paths={bl_paths}\nmounted_paths={mounted_paths}\naligned_bl_and_mount_paths={aligned_bl_and_mount_paths}",
        )
        sys.exit(1)

    return aligned_bl_and_mount_paths


def _make_mount_names_from_index(index: int) -> tuple[str, str]:
    return f"/media/mount-{index}", f"/media/bl-{index}"


def _unmount_and_rm_dir(directory: str) -> None:
    if not os.path.exists(directory):
        return

    findmnt_result = subprocess.run(
        ("findmnt", "-M", directory),
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        check=False,
    )

    if findmnt_result.returncode == 0:
        cmd = ("sudo", "umount", directory)  # TODO: -l option was used but seems incorrect
        logger.info(f"EXEC: {cmd}")
        subprocess.run(
            cmd,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            check=True,
        )

    assert len(os.listdir(directory)) == 0, directory
    logger.info(f"INFO: rm'ing directory={directory}")
    os.rmdir(directory)


def _unmount_and_rm_dir_then_create_dir(directory: str) -> None:
    _unmount_and_rm_dir(directory)
    os.makedirs(directory, exist_ok=True)


def _create_file(file_path, optional_str: str | None = None) -> None:
    dir_ = os.path.dirname(file_path)
    if not os.path.exists(dir_):
        # original_user = os.environ.get("SUDO_USER")
        sudo_uid = os.environ.get("SUDO_UID")
        sudo_gid = os.environ.get("SUDO_GID")
        assert isinstance(sudo_uid, str)
        assert isinstance(sudo_gid, str)
        uid = int(sudo_uid)
        gid = int(sudo_gid)
        os.makedirs(dir_)
        os.chown(dir_, uid, gid)
        logger.info(f"created dir={dir_}")
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            logger.info(f"created file_path={file_path}")
            if optional_str is not None:
                f.write(optional_str)
        # original_user = os.environ.get("SUDO_USER")
        sudo_uid = os.environ.get("SUDO_UID")
        sudo_gid = os.environ.get("SUDO_GID")
        assert isinstance(sudo_uid, str)
        assert isinstance(sudo_gid, str)
        uid = int(sudo_uid)
        gid = int(sudo_gid)
        os.chown(file_path, uid, gid)


def _get_lsblk_info(mount) -> str | None:
    lsblk_output = subprocess.run(["lsblk", "-p", "-S"], stdout=subprocess.PIPE, check=True, text=True).stdout
    for line in lsblk_output.strip().split("\n"):
        if mount in line:
            return line
    return None


def _get_most_recent_dir_mount_and_dir_bl(ls_blk_info_line: str, log_file: str) -> tuple[str, str] | None:
    ret_value = None
    logger.info(f"searching log_file={log_file}")

    log_str = ""
    with open(log_file, encoding="utf-8") as f:
        lines = f.readlines()[::-1]  # Read lines in reverse order
        for line in lines:
            ls_blk_info_line_1_space = " ".join(ls_blk_info_line.split()[2:])
            line_1_space = " ".join(line.split())
            if ls_blk_info_line_1_space in line_1_space:
                log_str += f"  ls {ls_blk_info_line_1_space}\n"
                log_str += f"  ln {line_1_space}\n"
                parts = line_1_space.strip().split(",")
                ret_value = (parts[2], parts[3])
                break
            log_str += f"  {ls_blk_info_line_1_space} NOT in {line_1_space}\n"
    log_str = log_str[:-1] if log_str.endswith("\n") else log_str
    logger.info(f"log_file={log_file} contents:\n{log_str}")
    return ret_value


def _get_largest_integer_partition(path):
    largest_integer = 1
    path_exists = False
    while True:
        file_path = f"{path}{largest_integer}"
        if os.path.exists(file_path):
            largest_integer += 1
            path_exists = True
        else:
            break
    return largest_integer - 1 if path_exists else None


def _get_mountable_paths():
    sd_files = glob.glob("/dev/sd[a-z]")
    mountable_paths = []
    for f in sd_files:
        largest_partition = _get_largest_integer_partition(f)
        mountable_paths.append((f, None if largest_partition is None else f"{f}{largest_partition}"))
    return mountable_paths
    # return [(f, f"{f}{_get_largest_integer_partition(f)}") for f in sd_files]


def _bl_mount(partition, dir_mount, dir_bl):
    _unmount_and_rm_dir_then_create_dir(dir_mount)
    _unmount_and_rm_dir_then_create_dir(dir_bl)

    try:
        dislocker_cmd = f"sudo dislocker -V {partition} -u -- {dir_bl}"
        mount_cmd = f"sudo mount -o loop {dir_bl}/dislocker-file {dir_mount}"
        ## TODO: check if shell=True can be rm'd
        subprocess.run(dislocker_cmd, shell=True, check=True, stderr=subprocess.PIPE)
        subprocess.run(mount_cmd, shell=True, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"ERROR: {e.stderr.decode()}")
        return 1, None

    lsblk_details_str = subprocess.run(["lsblk", "-p", "-S"], stdout=subprocess.PIPE, check=True, text=True).stdout

    lsblk_name = partition[:8]
    lsblk_detail_name = [line for line in lsblk_details_str.split("\n") if lsblk_name in line]
    assert len(lsblk_detail_name) == 1, (lsblk_detail_name, lsblk_name)

    current_time_utc = datetime.datetime.utcnow()
    formatted_time = current_time_utc.strftime("%y%m%dt%H%M%Sz")

    try:
        with open(f"{dir_mount}/README.md", encoding="utf-8") as f:
            drive_details = f.read().strip("\n")
    except FileNotFoundError:
        drive_details = None

    ret_code = 2 if drive_details is None else 0
    return ret_code, f"{formatted_time},{partition},{dir_mount},{dir_bl},{drive_details},'{lsblk_detail_name[0]}'\n"


def main(argparse_args: Sequence[str] | None = None):
    # pylint: disable=[too-many-locals,too-many-branches,too-many-statements]
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=_LOG_FILE_PATH)
    parser.add_argument("--log-cfg", default=_LOG_CFG_DEFAULT, help="Log cfg; empty str uses LogManager default cfg")
    # parser.add_argument("--no-auto", "--na", action="store_true")
    parser.add_argument("--unmount-all", "--ua", action="store_true")
    args = parser.parse_args(argparse_args)

    log_manager.LogManager.setup_logger(globals(), log_cfg=args.log_cfg, log_file=args.log)

    logger.debug(f"argparse args:\n{argparse_utils.parsed_args_to_str(args)}")

    bl_and_mounted_paths = _get_aligned_bl_and_mount_paths()

    ## ask user whether to unmount
    if len(bl_and_mounted_paths) > 0:
        logger.info(
            "There are %s mounted_paths:\n  %s",
            len(bl_and_mounted_paths),
            "\n  ".join(
                f"index={i}: mounted_path={mounted_path}"
                for i, (_bl_path, mounted_path) in enumerate(bl_and_mounted_paths)
            ),
        )
        while True:
            input_str = input("PROMPT: Give space delimited indices to unmount: ")
            try:
                unmount_indices = tuple(int(s) for s in input_str.split())
            except ValueError:
                logger.error("invalid prompt input; could not convert to ints")
                continue
            if len(unmount_indices) != len(set(unmount_indices)):
                logger.error("invalid prompt input; cannot repeat ints")
                continue
            if not all(0 <= unmount_index < len(bl_and_mounted_paths) for unmount_index in unmount_indices):
                logger.error(f"invalid prompt input; all ints must be within [0, {len(bl_and_mounted_paths)}) ")
                continue

            for i in unmount_indices:
                for path in bl_and_mounted_paths[i]:
                    _unmount_and_rm_dir(path)
            break

    ## get mounted paths following unmounts
    bl_and_mounted_paths = _get_aligned_bl_and_mount_paths()
    logger.info(
        "There are %s mounted_paths:%s%s",
        len(bl_and_mounted_paths),
        "" if len(bl_and_mounted_paths) == 0 else "\n",
        "\n  ".join(f"mounted_path={mounted_path}" for _bl_path, mounted_path in bl_and_mounted_paths),
    )

    _create_file(_LOG_CACHE, _HEADING)

    mountable_paths = _get_mountable_paths()
    mountable_paths_to_mount_points = OrderedDict()
    for mounted_name, mounted_partition in mountable_paths:
        if mounted_partition is None:
            logger.warning(f"partitions do not exist for mounted_name={mounted_name}")
            continue
        ls_blk_info = _get_lsblk_info(mounted_name)
        assert ls_blk_info is not None
        dir_mount_and_dir_bl = _get_most_recent_dir_mount_and_dir_bl(ls_blk_info, _LOG_CACHE)
        log_str = f"mounted_name={mounted_name}\n  mounted_partition={mounted_partition}\n  ls_blk_info={ls_blk_info}"
        if dir_mount_and_dir_bl is not None:
            log_str += f"  dir_mount={dir_mount_and_dir_bl[0]}\n  dir_bl={dir_mount_and_dir_bl[1]}"
        logger.info(log_str)
        mountable_paths_to_mount_points[mounted_partition] = dir_mount_and_dir_bl

    no_prompt_mountable_paths_to_mount_points = OrderedDict()
    prompt_mountable_paths = []
    for i, (mountable_path, mount_point) in enumerate(mountable_paths_to_mount_points.items()):
        if mount_point is None:
            prompt_mountable_paths.append(mountable_path)
            logger.warning(f"index={i}; could not find mount_point for mountable_path={mountable_path}")
        else:
            no_prompt_mountable_paths_to_mount_points[mountable_path] = mount_point
            logger.info(f"index={i}; found mountable_path={mountable_path}; mount_point={mount_point}")

    ## prompt user for cached mountable paths they wish to change
    if len(no_prompt_mountable_paths_to_mount_points) > 0:
        logger.info(
            "no_prompt_mountable_paths_to_mount_points:\n  %s",
            "\n  ".join(
                f"  index={i}: mount path='{path}' to {mount_path}"
                for i, (path, mount_path) in enumerate(no_prompt_mountable_paths_to_mount_points.items())
            ),
        )
        while True:
            prompt_msg = "PROMPT: Give space delimited ints for above cached mountable paths you wish to change: "
            change_indices_str = input(prompt_msg)
            logger.debug(f"PROMPT: prompt_msg='{prompt_msg}' prompt_input='{change_indices_str}'")
            try:
                change_indices = tuple(int(s) for s in change_indices_str.split())
            except ValueError:
                logger.error("invalid prompt input; could not convert to ints")
            if len(change_indices) != len(set(change_indices)):
                logger.error("invalid prompt input; cannot repeat ints")
                continue
            if not all(
                0 <= change_index < len(no_prompt_mountable_paths_to_mount_points) for change_index in change_indices
            ):
                logger.error(
                    f"invalid prompt input; all ints must be within [0, {len(no_prompt_mountable_paths_to_mount_points)}) ",
                )
                continue
            break

        change_keys = []
        for i, (k, _v) in enumerate(no_prompt_mountable_paths_to_mount_points.items()):
            if i in change_indices:
                change_keys.append(k)
        for k in change_keys:
            prompt_mountable_paths.append(k)
            no_prompt_mountable_paths_to_mount_points.pop(k)
            mountable_paths_to_mount_points[k] = None

    if len(prompt_mountable_paths) > 0:
        while True:
            prompt_msg = f"PROMPT: Give space delimited ints for mount paths for {prompt_mountable_paths} (-1 means do not mount): "
            input_str = input(prompt_msg)
            logger.debug(f"PROMPT: prompt_msg='{prompt_msg}' prompt_input='{input_str}'")
            try:
                input_mount_integers = [int(s) for s in input_str.split()]
            except ValueError:
                logger.error("invalid prompt input")
                continue
            if len([i for i in input_mount_integers if i != -1]) != len(
                {i for i in input_mount_integers if i != -1},
            ):
                logger.error("cannot repeat ints")
                continue
            if len(input_mount_integers) != len(prompt_mountable_paths):
                logger.error(
                    f"len(input_mount_integers) != len(prompt_mountable_paths): {len(input_mount_integers)} != {len(prompt_mountable_paths)}",
                )
                continue
            if any(input_mount_index < -1 for input_mount_index in input_mount_integers):
                logger.error("invalid prompt input; all ints must be within [-1, inf)")
                continue
            if any(
                _make_mount_names_from_index(i) in no_prompt_mountable_paths_to_mount_points.values()
                for i in input_mount_integers
            ):
                logger.error(
                    f"cannot propose to mount to same location as found mounts:\n{no_prompt_mountable_paths_to_mount_points}",
                )
                continue
            break

        for i, mountable_path in enumerate(prompt_mountable_paths):
            assert mountable_paths_to_mount_points[mountable_path] is None
            if input_mount_integers[i] == -1:
                del mountable_paths_to_mount_points[mountable_path]
            else:
                mountable_paths_to_mount_points[mountable_path] = _make_mount_names_from_index(input_mount_integers[i])

    assert all(v is not None for v in mountable_paths_to_mount_points.values())

    paths_to_mount = []
    for mountable_path, mount_point in mountable_paths_to_mount_points.items():
        assert mount_point is not None, mountable_paths_to_mount_points
        if os.path.exists(os.path.join(mount_point[0], "README.md")):
            logger.info(
                f"skipping as README.md exists already: mountable_path={mountable_path}; mount_point={mount_point}",
            )
        else:
            logger.info(f"will attempt mountable_path={mountable_path}; mount_point={mount_point}")
            paths_to_mount.append(mountable_path)

    if len(paths_to_mount) == 0:
        logger.info("no paths to mount")
        sys.exit(0)

    if not cli_utils.prompt_once("PROMPT: Continue? (y/n): "):
        logger.info("aborted due to prompt input")
        sys.exit(0)

    for path_to_mount in paths_to_mount:
        mount_point = mountable_paths_to_mount_points[path_to_mount]
        assert mount_point is not None, (mountable_paths_to_mount_points, path_to_mount)
        dir_mount, dir_bl = mount_point
        while True:
            _unmount_and_rm_dir_then_create_dir(dir_mount)
            _unmount_and_rm_dir_then_create_dir(dir_bl)
            bl_mount_ec, bl_mount_result_str = _bl_mount(path_to_mount, dir_mount, dir_bl)
            if bl_mount_ec == 0:
                break
            if bl_mount_ec == 2:
                logger.error("seems encrypt passed but the readme could not be read, create one then try again")
                input("PROMPT: press enter when ready to continue")
                logger.debug("PROMPT: press enter when ready to continue")
            else:
                logger.error("failed decrypt, try again")
        logger.info(f"{bl_mount_result_str}")
        _append(_LOG_CACHE, bl_mount_result_str)


if __name__ == "__main__":
    main()
