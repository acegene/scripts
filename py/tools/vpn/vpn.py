#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import functools
import json
import math
import os
import subprocess
import sys
from collections import OrderedDict
from collections.abc import Sequence

from utils import argparse_utils
from utils import lock_manager
from utils import log_manager
from utils import path_utils

## TODO:
## * meshnet
## * login and logout not working right

_LOG_BASE = os.path.splitext(os.path.basename(__file__))[0]
_LOG_FILE_PATH = f'{os.environ["TEMP"]}/{_LOG_BASE}.log' if os.name == "nt" else f"/tmp/{_LOG_BASE}.log"
_LOGGING_CFG_DEFAULT = os.path.join(os.path.dirname(os.path.realpath(__file__)), f"{_LOG_BASE}_logging_cfg.json")
logger = log_manager.LogManager()

_NORD_DNS_IPS = ("103.86.96.100", "103.86.99.100")

_NORD_CMDS = {
    ## settings
    "analytics_off": ("nordvpn", "set", "analytics", "0"),
    "autoconnect_on": ("nordvpn", "set", "autoconnect", "1"),
    "notify_on": ("nordvpn", "set", "notify", "1"),
    "firewall_on": ("nordvpn", "set", "firewall", "1"),
    "killswitch_off": ("nordvpn", "set", "killswitch", "0"),
    "killswitch_on": ("nordvpn", "set", "killswitch", "1"),
    "lan_discovery": ("nordvpn", "set", "lan-discovery", "1"),
    "dns": ("nordvpn", "set", "dns", *_NORD_DNS_IPS),
    ## cmds
    "connect": ("nordvpn", "connect"),
    "disconnect": ("nordvpn", "disconnect"),
    "login": ("nordvpn", "login"),
    "logout": ("nordvpn", "logout"),
    "status": ("nordvpn", "status"),
}

_NORD_PRE_LOGIN_SETTINGS = (
    _NORD_CMDS["analytics_off"],
    _NORD_CMDS["notify_on"],
    _NORD_CMDS["lan_discovery"],
    _NORD_CMDS["dns"],
    _NORD_CMDS["firewall_on"],
)
_NORD_PRE_CONNECT_SETTINGS = (*_NORD_PRE_LOGIN_SETTINGS, _NORD_CMDS["autoconnect_on"])

_NORD_POST_CONNECT_SETTINGS = (_NORD_CMDS["killswitch_on"],)

_NORD_FLAG_TO_PRE_RUN_CMDS = {
    "connect": _NORD_PRE_CONNECT_SETTINGS,
    "disconnect": (),
    "reconnect": _NORD_PRE_CONNECT_SETTINGS,  # TODO: is this right, also post for reconnect
    "status": (),
    "login": (),
    "logout": (),
}

_NORD_FLAG_TO_POST_RUN_CMDS = {
    "connect": _NORD_POST_CONNECT_SETTINGS,
    "disconnect": (_NORD_CMDS["killswitch_off"],),
    "reconnect": _NORD_POST_CONNECT_SETTINGS,
    "status": (),
    "login": _NORD_PRE_LOGIN_SETTINGS,
    "logout": (),
}

_NORD_SET_SETTING_NAME_TO_PRINTED = {
    # "Technology": "Technology",
    "Firewall": "firewall",
    # "Firewall Mark": "Firewall Mark",
    # "Routing": "Routing",
    "Analytics": "analytics",
    "Kill Switch": "killswitch",
    # "Threat Protection Lite": "Threat Protection Lite",
    "Notify": "notify",
    "Auto-connect": "autoconnect",
    # "IPv6": "IPv6",
    # "Meshnet": "Meshnet",
    "DNS": "dns",
    "LAN Discovery": "lan-discovery",
}

_NORD_BOOL_STR_TO_ENABLE_STATUS = {
    "0": "disabled",
    "1": "enabled",
}

_NORD_PRINTED_SETTING_NAME_TO_PRINTED_VALUE_FORM_FUNC = {
    # "Technology" :"Technology",
    "firewall": lambda *args: _NORD_BOOL_STR_TO_ENABLE_STATUS[args[0]],
    # "Firewall Mark": lambda *args: ,
    # "Routing": lambda *args: ,
    "analytics": lambda *args: _NORD_BOOL_STR_TO_ENABLE_STATUS[args[0]],
    "killswitch": lambda *args: _NORD_BOOL_STR_TO_ENABLE_STATUS[args[0]],
    # "Threat Protection Lite": lambda *args: ,
    "notify": lambda *args: _NORD_BOOL_STR_TO_ENABLE_STATUS[args[0]],
    "autoconnect": lambda *args: _NORD_BOOL_STR_TO_ENABLE_STATUS[args[0]],
    # "IPv6": lambda *args: ,
    # "Meshnet": lambda *args: ,
    "dns": lambda *args: ", ".join(args),
    "lan-discovery": lambda *args: _NORD_BOOL_STR_TO_ENABLE_STATUS[args[0]],
}


@functools.total_ordering
class DateTimeUTC:
    def __init__(self, datetime_: datetime.datetime | str | None = None, str_format: str = "%y%m%dT%H%M%SZ"):
        if datetime_ is None:
            self.datetime = datetime.datetime.now(datetime.timezone.utc)
        elif isinstance(datetime_, datetime.datetime):
            self.datetime = datetime_.replace(tzinfo=datetime.timezone.utc)
        elif isinstance(datetime_, str):
            self.datetime = datetime.datetime.strptime(datetime_, str_format).replace(tzinfo=datetime.timezone.utc)
        else:
            raise TypeError
        self.str_format = str_format
        self.str = self.datetime.strftime(self.str_format)

    def __add__(self, other: datetime.timedelta | float | int | str) -> DateTimeUTC:
        if isinstance(other, datetime.timedelta):
            return DateTimeUTC(self.datetime + other)
        if isinstance(other, float):
            return DateTimeUTC(self.datetime + datetime.timedelta(seconds=other))
        if isinstance(other, int):
            return DateTimeUTC(self.datetime + datetime.timedelta(seconds=other))
        if isinstance(other, str):
            return DateTimeUTC(self.datetime + datetime.timedelta(seconds=DateTimeUTC.str_time_duration_to_secs(other)))
        raise TypeError(f"Unexpected type(other)={type(other)}; other={other}")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DateTimeUTC):
            return self.datetime == other.datetime
        if isinstance(other, datetime.datetime):
            return self.datetime == other
        return False

    def __lt__(self, other: DateTimeUTC | datetime.datetime) -> bool:
        if isinstance(other, DateTimeUTC):
            return self.datetime < other.datetime
        if isinstance(other, datetime.datetime):
            return self.datetime < other
        raise TypeError(f"Unexpected type(other)={type(other)}; other={other}")

    def __sub__(
        self,
        other: DateTimeUTC | datetime.datetime | datetime.timedelta | float | int | str,
    ) -> DateTimeUTC | datetime.timedelta:
        if isinstance(other, DateTimeUTC):
            return self.datetime - other.datetime
        if isinstance(other, datetime.datetime):
            return self.datetime - other
        if isinstance(other, datetime.timedelta):
            return DateTimeUTC(self.datetime - other)
        if isinstance(other, float):
            return DateTimeUTC(self.datetime - datetime.timedelta(seconds=other))
        if isinstance(other, int):
            return DateTimeUTC(self.datetime - datetime.timedelta(seconds=other))
        if isinstance(other, str):
            return DateTimeUTC(self.datetime - datetime.timedelta(seconds=DateTimeUTC.str_time_duration_to_secs(other)))
        raise TypeError(f"Unexpected type(other)={type(other)}; other={other}")

    def __str__(self):
        return self.str

    @staticmethod
    def from_utc_time_str(s: str, str_format: str = "%y%m%dT%H%M%SZ") -> DateTimeUTC:
        return DateTimeUTC(datetime.datetime.strptime(s, str_format).replace(tzinfo=datetime.timezone.utc))

    @staticmethod
    def str_time_duration_to_secs(duration_str: str) -> int:
        try:
            if duration_str.endswith("h"):
                hours = float(duration_str[:-1])
                return int(math.ceil(hours * 3600))  # Convert hours to seconds, rounding up
            if duration_str.endswith("m"):
                mins = float(duration_str[:-1])
                return int(math.ceil(mins * 60))  # Convert mins to seconds, rounding up
            if duration_str.endswith("s"):
                return int(duration_str[:-1])
            return int(duration_str)
        except ValueError as e:
            logger.error(f"Invalid value for duration_str={duration_str}")
            raise e


def _delete_if_exists(file_path: str) -> bool:
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def _delete_locks_if_timed_out(locks, time_script_start, time_last_lock_str, lock_timeout_duration_rm):
    locks_deleted_log_msgs = []
    if time_last_lock_str is None:
        for lock in locks:
            if _delete_if_exists(lock):
                locks_deleted_log_msgs.append(f"Deleted lock={lock} as time_last_lock=None")
    else:
        time_last_lock = DateTimeUTC(time_last_lock_str)
        if (time_last_lock + lock_timeout_duration_rm) < time_script_start:
            for lock in locks:
                if _delete_if_exists(lock):
                    locks_deleted_log_msgs.append(
                        f"Deleted lock={lock} as time_script_start={time_script_start} > "
                        f"(time_last_lock={time_last_lock} + "
                        f"lock_timeout_duration_rm={lock_timeout_duration_rm})",
                    )
    return locks_deleted_log_msgs


def _log_stream_if_unempty(str_hdl: str, msg: str) -> None:
    if msg != "":
        logger.info(f"  {str_hdl}:\n{msg}")


def _log_cmd_w_output(cmd: Sequence[str], result, is_error: bool = True) -> None:
    if is_error:
        logger.error(f"failed to execute cmd: {' '.join(cmd)}")
    else:
        logger.info(f"executed cmd: {' '.join(cmd)}")
    _log_stream_if_unempty("stdout", _strip_nl_and_hyphens(result.stdout))
    _log_stream_if_unempty("stderr", _strip_nl_and_hyphens(result.stderr))


def subprocess_run_wrapped(cmd: Sequence[str], timeout: int = 20) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            # ["/usr/bin/env", "bash", "-c", " ".join(cmd)], # to force interpreter
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.error("failed to execute cmd=%s within timeout=%s", cmd, timeout)
        raise


# TODO: it is not understood why this is necessary, i.e. where the excess chars come from
def _strip_nl_and_hyphens(s: str) -> str:
    out_s = s
    startswith = lambda s, delims: any(s.startswith(d) for d in delims)
    endswith = lambda s, delims: any(s.endswith(d) for d in delims)
    symbols = ("\n", "-", "/", "\\", "|")
    while startswith(out_s, symbols) or endswith(out_s, ("\n", "-")):
        out_s = out_s.strip()
        out_s = out_s.strip("\n")
        out_s = out_s.strip("-")
    return out_s


def _get_dict_from_json_file(json_file: str) -> dict:
    if not os.path.exists(json_file):
        return {}
    with path_utils.open_unix_safely(json_file) as f:
        return json.load(f)  # type: ignore[no-any-return]


def _exec_nordvpn_cmd_w_error_handling(cmd: Sequence[str], print_on_succ: bool = False) -> bool:
    logger.info(f"executing cmd: {' '.join(cmd)}")
    result = subprocess_run_wrapped(cmd)
    if result.returncode == 0:
        if print_on_succ:
            _log_cmd_w_output(cmd, result, True)
        return True
    _log_cmd_w_output(cmd, result)
    return False


def _exec_nordvpn_set_cmd_w_error_handling(cmd: Sequence[str], settings: dict, print_on_succ: bool = False) -> bool:
    assert cmd[1] == "set", cmd
    assert cmd[2] in settings, (cmd, settings)
    cmd_setting_value_as_would_be_printed = _NORD_PRINTED_SETTING_NAME_TO_PRINTED_VALUE_FORM_FUNC[cmd[2]](*cmd[3:])
    current_setting_value = settings[cmd[2]]
    if cmd_setting_value_as_would_be_printed == current_setting_value:
        logger.info(f"skipping cmd: {cmd}; {cmd[2]}: {current_setting_value}")
        return True

    logger.info(f"executing cmd: {' '.join(cmd)}")
    result = subprocess_run_wrapped(cmd)
    if result.returncode == 0:
        if print_on_succ:
            _log_cmd_w_output(cmd, result, True)
        return True
    _log_cmd_w_output(cmd, result)
    return False


def _exec_nordvpn_cmd_w_exit_on_failure(cmd: Sequence[str], print_on_succ: bool = False) -> None:
    if not _exec_nordvpn_cmd_w_error_handling(cmd, print_on_succ):
        sys.exit(1)


def _exec_nordvpn_set_cmds_w_error_handling(
    cmds: Sequence[Sequence[str]],
    settings: dict,
    print_on_succ: bool = False,
) -> bool:
    for cmd in cmds:
        if not _exec_nordvpn_set_cmd_w_error_handling(cmd, settings, print_on_succ):
            return False
    return True


def connect(is_connected: bool = False) -> bool:
    if is_connected:
        logger.info("skipping connect due to already being connected.")
        return True
    return _exec_nordvpn_cmd_w_error_handling(_NORD_CMDS["connect"])


def get_settings() -> dict:
    cmd = ("nordvpn", "settings")
    result = subprocess_run_wrapped(cmd)
    settings_to_values = OrderedDict()
    if result.returncode == 0:
        setting_lines = _strip_nl_and_hyphens(result.stdout).split("\n")
        settings_w_value = []
        for line in setting_lines:
            ## accumulate multiline settings into single key
            if ": " in line or line.endswith(":"):
                settings_w_value.append(line)
            else:
                settings_w_value[-1] += f"\n{line}"
        for setting_w_value in settings_w_value:
            setting_w_value_colon_split = [e.strip() for e in setting_w_value.split(":")]
            assert len(setting_w_value_colon_split) == 2, (setting_w_value, setting_w_value_colon_split)
            if setting_w_value_colon_split[0] in _NORD_SET_SETTING_NAME_TO_PRINTED:
                settings_to_values[_NORD_SET_SETTING_NAME_TO_PRINTED[setting_w_value_colon_split[0]]] = (
                    setting_w_value_colon_split[1]
                )
        return settings_to_values
    _log_cmd_w_output(cmd, result)
    sys.exit(1)


def get_status() -> bool:
    cmd = _NORD_CMDS["status"]
    result = subprocess_run_wrapped(cmd)
    if result.returncode == 0:
        logger.info(_strip_nl_and_hyphens(result.stdout))
    else:
        _log_cmd_w_output(cmd, result)
        sys.exit(1)

    if "Status: Connected" in result.stdout:
        return True
    if "Status: Disconnected" in result.stdout:
        return False
    logger.fatal(f"unexpected stdout:\n{result.stdout}")
    assert False, result.stdout


def login(is_connected: bool = False) -> None:
    if is_connected:
        logger.info("skipping login due to already being connected.")
    else:
        if not _exec_nordvpn_cmd_w_error_handling(_NORD_CMDS["login"]):
            sys.exit(1)


def write_dict_to_file_as_json(json_dict: dict, filename: str) -> None:
    with path_utils.open_unix_safely(filename, "w") as f:
        json.dump(json_dict, f)


def nordvpn_cmd_execution(flag, vpn_status, status, duration_fail_connect_until_notification, time_now):
    connect_success = None
    if flag == "connect":
        connect_success = connect(status)
    elif flag == "disconnect":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORD_CMDS["disconnect"])
    elif flag == "login":
        login(status)
    elif flag == "logout":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORD_CMDS["logout"], True)
    elif flag == "reconnect":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORD_CMDS["disconnect"])
        connect_success = connect(get_status())
    else:
        assert False, flag

    if connect_success is False:
        vpn_status["earliest_fail_connect"] = (
            time_now.str
            if vpn_status.get("earliest_fail_connect", None) is None
            else vpn_status["earliest_fail_connect"]
        )
        earliest_fail_connect = DateTimeUTC.from_utc_time_str(vpn_status["earliest_fail_connect"])
        if time_now - earliest_fail_connect > duration_fail_connect_until_notification:
            msg = f"vpn disconnected for time > duration_fail_connect_until_notification={duration_fail_connect_until_notification}"
            logger.error(msg)
            vpn_status["earliest_fail_connect"] = None
            sys.exit(1)


def nordvpn_main(args: argparse.Namespace, vpn_status: dict) -> None:
    time_now = DateTimeUTC()

    logger.info("#### STATUS PRE CMD")
    status = get_status()

    if args.cron_job_pause_duration is not None:
        cron_pause_until = time_now + args.cron_job_pause_duration
        vpn_status["cron_pause_until"] = cron_pause_until.str
        logger.info(
            f"Set cron_pause_until={cron_pause_until};"
            f" time_now={time_now};"
            f" cron_pause_until_duration={args.cron_job_pause_duration}",
        )

    if args.cron_job:
        pause_until = vpn_status.get("cron_pause_until", None)
        if pause_until is not None:
            if time_now < DateTimeUTC(pause_until):
                logger.info(
                    f"Skipping cron job;"
                    f" time_now={time_now} < pause_until={pause_until};"
                    " setting args.flag=status",
                )
                args.flag = "status"
            else:
                logger.info(f"Executing cron job; time_now={time_now} >= pause_until={pause_until}")
                vpn_status["cron_pause_until"] = None
        else:
            logger.info(f"Executing cron job; time_now={time_now} >= pause_until={pause_until}")
            vpn_status["cron_pause_until"] = None

    pre_settings = get_settings()
    logger.info(
        "#### SETTINGS PRE CMD\n%s",
        "\n".join(
            f"  {setting_name}: {pre_value}"
            for setting_name, pre_value in sorted(list((k, v) for k, v in pre_settings.items()), key=lambda t: t[0])
        ),
    )
    logger.info("#### CHANGE SETTINGS PRE CMD")
    pre_connect_cmds = _NORD_FLAG_TO_PRE_RUN_CMDS[args.flag]
    if not _exec_nordvpn_set_cmds_w_error_handling(pre_connect_cmds, pre_settings):
        sys.exit(1)

    if args.flag == "status":
        if status:
            vpn_status["earliest_fail_connect"] = None
        return

    logger.info("#### CMD EXECUTION")
    nordvpn_cmd_execution(args.flag, vpn_status, status, args.duration_fail_connect_until_notification, time_now)

    logger.info("#### CHANGE SETTINGS POST CMD")
    post_settings = get_settings()
    post_connect_cmds = _NORD_FLAG_TO_POST_RUN_CMDS[args.flag]
    if not _exec_nordvpn_set_cmds_w_error_handling(post_connect_cmds, post_settings):
        sys.exit(1)

    final_settings = get_settings()

    logger.info("#### STATUS POST CMD")
    status = get_status()
    logger.info("#### SETTINGS CHANGED")
    for setting_name, pre_value in sorted(list((k, v) for k, v in pre_settings.items()), key=lambda t: t[0]):
        final_value = final_settings[setting_name]
        if pre_value != final_value:
            logger.info(f"changed '{setting_name}' from '{pre_value}' to '{final_value}'")


def main(argparse_args: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cron-job", action="store_true")
    parser.add_argument("--cron-job-pause-duration", "--pause")
    parser.add_argument("--duration-fail-connect-until-notification", "--dfc", default="5m")
    file_status = f'{os.environ["TEMP"]}/vpn-status.json' if os.name == "nt" else "/tmp/vpn-status.json"
    parser.add_argument("--file-out-vpn-status", default=file_status)
    parser.add_argument("--lock-timeout-duration-rm", default="120s")
    parser.add_argument("--log")
    parser.add_argument("--log-cfg", help="Logging cfg, empty str uses LogManager default cfg")
    parser.add_argument("--vpn-provider", "--vpn", choices=["nordvpn"], default="nordvpn")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--connect", "-c", action="store_const", const="connect", dest="flag")
    group.add_argument("--disconnect", "-d", action="store_const", const="disconnect", dest="flag")
    group.add_argument("--login", "--li", "-l", action="store_const", const="login", dest="flag")
    group.add_argument("--logout", "--lo", action="store_const", const="logout", dest="flag")
    group.add_argument("--reconnect", "-r", action="store_const", const="reconnect", dest="flag")
    group.add_argument("--status", "-s", action="store_const", const="status", dest="flag")
    args = parser.parse_args(argparse_args)

    if args.flag is None:
        args.flag = "status"

    log_cfg = _LOGGING_CFG_DEFAULT if args.log_cfg is None else (None if args.log_cfg == "" else args.log_cfg)
    log_manager.LogManager.setup_logger(globals(), log_cfg=log_cfg, log_file=args.log)

    time_script_start = DateTimeUTC()

    files_to_lock = (_LOG_FILE_PATH, args.file_out_vpn_status)
    lm = lock_manager.LockManager(*files_to_lock, timeout=10)

    vpn_status = _get_dict_from_json_file(args.file_out_vpn_status)  # write must be atomic or this can get corrupted

    locks_deleted_log_msgs = _delete_locks_if_timed_out(
        lm.lock_names,
        time_script_start,
        vpn_status.get("time_last_lock", None),
        args.lock_timeout_duration_rm,
    )

    with lm:
        time_lock = DateTimeUTC()
        vpn_status["time_last_lock"] = time_lock.str

        logger.debug(f"argparse args:\n{argparse_utils.parsed_args_to_str(args)}")
        for msg in locks_deleted_log_msgs:
            logger.warning(msg)
        logger.debug(f"files_locked={files_to_lock} at time={time_lock}")
        if args.cron_job:
            logger.info("Start automated execution by cron job")

        try:
            if args.vpn_provider == "nordvpn":
                nordvpn_main(args, vpn_status)
            else:
                raise ValueError(args.vpn_provider)
        finally:
            write_dict_to_file_as_json(vpn_status, args.file_out_vpn_status)


if __name__ == "__main__":
    main()
