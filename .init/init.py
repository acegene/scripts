#!/usr/bin/env python3
# pylint: disable=wrong-import-position
import argparse
import os
import sys
from collections.abc import Sequence

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts", "py"),
)

from utils import argparse_utils
from utils import cli_utils
from utils import log_manager
from utils import python_utils

_LOG_FILE_PATH, _LOG_CFG_DEFAULT = log_manager.get_default_log_paths(__file__)
logger = log_manager.LogManager()


def install_terminal_cfg(dir_repo):
    path_terminal_settings_symlink = os.path.expanduser(
        "~/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json",
    )
    path_terminal_settings = os.path.join(dir_repo, "win/cfg/terminal-cfg/settings.json")

    if not os.path.exists(path_terminal_settings):
        logger.error(f"cannot find: {path_terminal_settings}, aborting terminal cfg setup")
        return False

    if not os.path.exists(path_terminal_settings_symlink):
        os.symlink(path_terminal_settings, path_terminal_settings_symlink)
        logger.info(f"symlink created: {path_terminal_settings} -> {path_terminal_settings_symlink}")
        return True

    if not os.path.islink(path_terminal_settings_symlink):
        logger.info(f"terminal cfg orig: {path_terminal_settings_symlink}")
        logger.info(f"terminal cfg link: {path_terminal_settings}")
        if cli_utils.prompt("PROMPT: replace above orig with link? y/n: "):
            os.remove(path_terminal_settings_symlink)
            os.symlink(path_terminal_settings, path_terminal_settings_symlink)
            logger.info(f"symlink created: {path_terminal_settings} -> {path_terminal_settings_symlink}")
            return True
        logger.error("user aborted terminal cfg setup")
        return False

    logger.info("seems like terminal cfg is already installed")
    return True


def main(argparse_args: Sequence[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=_LOG_FILE_PATH)
    parser.add_argument("--log-cfg", default=_LOG_CFG_DEFAULT, help="Log cfg; empty str uses LogManager default cfg")
    args = parser.parse_args(argparse_args)

    log_manager.LogManager.setup_logger(globals(), log_cfg=args.log_cfg, log_file=args.log)

    logger.debug(f"argparse args:\n{argparse_utils.parsed_args_to_str(args)}")

    dir_this = os.path.dirname(os.path.abspath(__file__))
    dir_repo = os.path.dirname(dir_this)
    assert os.path.basename(dir_repo) == "scripts"

    if python_utils.is_os_windows():
        install_terminal_cfg(dir_repo)


if __name__ == "__main__":
    main()
