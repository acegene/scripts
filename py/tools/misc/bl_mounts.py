#!/usr/bin/env python3
import argparse
import datetime
import glob
import os
import re
import subprocess
import sys
from collections import OrderedDict

# TODO:
# * parse lsblk by column -> lsblk -p -S --json
# * most recent mountale paths should take priority

if os.geteuid() != 0:
    print("WARNING: need to be sudo, relaunching as sudo")
    # script = sys.argv[0]
    result = subprocess.run(["sudo", "python3", os.path.abspath(__file__)] + sys.argv[1:], check=False)
    sys.exit(result.returncode)


_USER = os.environ.get("SUDO_USER")
assert isinstance(_USER, str)
_LOG_BASE = os.path.splitext(os.path.basename(__file__))[0]
_HEADING = "time,partition,dir_mount,dir_bl,drive_details,lsblk -p -S\n"
_LOG = os.path.join("/home", _USER, ".log", f"{_LOG_BASE}.log")


def _append(file, s):
    with open(file, "r+", encoding="utf-8") as f:
        f.seek(0, 2)
        f.write(s)


def _get_bl_paths():
    bl_paths = []
    pattern = re.compile(r"/media/bl(?:-\d+)?")
    for entry in os.listdir("/media"):
        full_path = os.path.join("/media", entry)
        if os.path.exists(full_path):
            if pattern.match(full_path):
                bl_paths.append(full_path)
    return bl_paths


def _get_mount_paths():
    mount_paths = []
    pattern = re.compile(r"/media/mount(?:-\d+)?")
    for entry in os.listdir("/media"):
        full_path = os.path.join("/media", entry)
        if os.path.exists(full_path):
            if pattern.match(full_path):
                mount_paths.append(full_path)
    return mount_paths


def _make_mount_names_from_index(index):
    return f"/media/mount-{index}", f"/media/bl-{index}"


def _unmount(directory):
    subprocess.run(
        ["sudo", "umount", "-l", directory],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        check=True,
    )


def _unmount_all(directories):
    for d in directories:
        _unmount(d)


def _unmount_if_exists_else_create_dir(directory):
    _unmount(directory)
    os.makedirs(directory, exist_ok=True)


def _create_file(file_path, optional_str=None):
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
        print(f"INFO: created dir={dir_}")
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            print(f"INFO: created file_path={file_path}")
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


def _get_lsblk_info(mount):
    lsblk_output = subprocess.run(["lsblk", "-p", "-S"], stdout=subprocess.PIPE, check=True, text=True).stdout
    for line in lsblk_output.strip().split("\n"):
        if mount in line:
            return line
    return None


def _get_most_recent_dir_mount_and_dir_bl(ls_blk_info_line, log_file):
    ret_value = None
    print(f"INFO: searching log_file={log_file}")
    with open(log_file, encoding="utf-8") as f:
        lines = f.readlines()[::-1]  # Read lines in reverse order
        for line in lines:
            ls_blk_info_line_1_space = " ".join(ls_blk_info_line.split()[2:])
            line_1_space = " ".join(line.split())
            if ls_blk_info_line_1_space in line_1_space:
                print(("ls", ls_blk_info_line_1_space))
                print(("ln", line_1_space))
                parts = line_1_space.strip().split(",")
                ret_value = (parts[2], parts[3])
                break
            print(f"{ls_blk_info_line_1_space} NOT in {line_1_space}")
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
    _unmount_if_exists_else_create_dir(dir_bl)
    _unmount_if_exists_else_create_dir(dir_mount)

    try:
        dislocker_cmd = f"sudo dislocker -V {partition} -u -- {dir_bl}"
        mount_cmd = f"sudo mount -o loop {dir_bl}/dislocker-file {dir_mount}"
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


def main():
    # pylint: disable=[too-many-locals,too-many-branches,too-many-statements]
    parser = argparse.ArgumentParser()
    # parser.add_argument("--no-auto", "--na", action="store_true")
    parser.add_argument("--unmount-all", "--ua", action="store_true")
    args = parser.parse_args()

    if args.unmount_all:
        bl_paths = _get_bl_paths()
        mount_paths = _get_mount_paths()
        _unmount_all(bl_paths)
        _unmount_all(mount_paths)
        print("INFO: unmout all complete")
        sys.exit(0)

    _create_file(_LOG, _HEADING)

    mountable_paths = _get_mountable_paths()
    mountable_paths_to_mount_points = OrderedDict()
    for mounted_name, mounted_partition in mountable_paths:
        if mounted_partition is None:
            print(f"WARNING: paritions do not exist for mounted_name={mounted_name}")
            continue
        ls_blk_info = _get_lsblk_info(mounted_name)
        assert ls_blk_info is not None
        dir_mount_and_dir_bl = _get_most_recent_dir_mount_and_dir_bl(ls_blk_info, _LOG)
        print(f"mounted_name={mounted_name}")
        print(f"  mounted_partition={mounted_partition}")
        print(f"  ls_blk_info={ls_blk_info}")
        if dir_mount_and_dir_bl is not None:
            print(f"  dir_mount={dir_mount_and_dir_bl[0]}")
            print(f"  dir_bl={dir_mount_and_dir_bl[1]}")
        mountable_paths_to_mount_points[mounted_partition] = dir_mount_and_dir_bl

    # need_prompt = False
    no_prompt_mountable_paths_to_mount_points = OrderedDict()
    prompt_mountable_paths = []
    for mountable_path, mount_point in mountable_paths_to_mount_points.items():
        if mount_point is None:
            prompt_mountable_paths.append(mountable_path)
            print(f"WARNING: could not find mount_point for mountable_path={mountable_path}")
            # need_prompt = True
        else:
            no_prompt_mountable_paths_to_mount_points[mountable_path] = mount_point
            print(f"INFO: found mountable_path={mountable_path}; mount_point={mount_point}")

    input_str = input("PROMPT: Accept found mountable paths above? (y/n): ").lower()
    if input_str != "y":
        for i, (path, mount_path) in enumerate(no_prompt_mountable_paths_to_mount_points.items()):
            print(f"{i}: mount path='{path}' to {mount_path}")
        while True:
            change_indices_str = input(
                "PROMPT: Give space delimited integers for for the above indices you wish to change: ",
            )
            try:
                change_indices = tuple(int(s) for s in change_indices_str.split())
                break
            except ValueError:
                print("ERROR: invalid input")

        change_keys = []
        for i, (k, v) in enumerate(no_prompt_mountable_paths_to_mount_points.items()):
            if i in change_indices:
                change_keys.append(k)
        for k in change_keys:
            prompt_mountable_paths.append(k)
            no_prompt_mountable_paths_to_mount_points.pop(k)
            mountable_paths_to_mount_points[k] = None
            # mountable_paths_to_mount_points  # TODO: why is this here?

    if len(prompt_mountable_paths) > 0:
        while True:
            input_str = input(f"PROMPT: Give space delimited integers for mount paths for {prompt_mountable_paths}: ")
            try:
                input_mount_integers = [int(s) for s in input_str.split()]
            except ValueError:
                print("ERROR: invalid input")
                continue
            if len(input_mount_integers) != len(set(input_mount_integers)):
                print("ERROR: cannot repeat integers")
                continue
            if len(input_mount_integers) != len(prompt_mountable_paths):
                print(
                    f"ERROR: len(input_mount_integers) != len(prompt_mountable_paths): {len(input_mount_integers)} != {len(prompt_mountable_paths)}",
                )
                continue
            if any(
                _make_mount_names_from_index(i) in no_prompt_mountable_paths_to_mount_points.values()
                for i in input_mount_integers
            ):
                print("ERROR: cannot propose to mount to same location as found mounts:")
                print(no_prompt_mountable_paths_to_mount_points)
                continue
            break

        for i, mountable_path in enumerate(prompt_mountable_paths):
            assert mountable_paths_to_mount_points[mountable_path] is None
            mountable_paths_to_mount_points[mountable_path] = _make_mount_names_from_index(input_mount_integers[i])

    assert all(v is not None for v in mountable_paths_to_mount_points.values())

    paths_to_mount = []
    for mountable_path, mount_point in mountable_paths_to_mount_points.items():
        if os.path.exists(os.path.join(mount_point[0], "README.md")):
            print(f"INFO: skipping as exists already: mountable_path={mountable_path}; mount_point={mount_point}")
        else:
            print(f"INFO: will attempt mountable_path={mountable_path}; mount_point={mount_point}")
            paths_to_mount.append(mountable_path)

    if len(paths_to_mount) == 0:
        print("INFO: no paths to mount")
        sys.exit(0)

    input_str = input("PROMPT: Continue? (y/n): ").lower()
    if input_str != "y":
        print(f"ERROR: aborted due to input_str={input_str}")
        sys.exit(1)

    for path_to_mount in paths_to_mount:
        dir_mount, dir_bl = mountable_paths_to_mount_points[path_to_mount]
        while True:
            _unmount_if_exists_else_create_dir(dir_mount)
            _unmount_if_exists_else_create_dir(dir_bl)
            bl_mount_ec, bl_mount_result_str = _bl_mount(path_to_mount, dir_mount, dir_bl)
            if bl_mount_ec == 0:
                break
            if bl_mount_ec == 2:
                print("ERROR: seems encrypt passed but the readme could not be read, create one then try again")
                input("PROMPT: press enter when ready to continue")
            else:
                print("ERROR: failed decrypt, try again")
        print(f"INFO: {bl_mount_result_str}")
        _append(_LOG, bl_mount_result_str)


if __name__ == "__main__":
    main()
