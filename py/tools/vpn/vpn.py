#!/usr/bin/env python3

import argparse
import datetime
import json
import math
import os
import subprocess
import sys

from collections import OrderedDict
from typing import Dict, Optional, Sequence

from utils import argparse_utils
from utils import lock_manager
from utils import log_manager

## TODO:
## * meshnet
## * login and logout not working right


_LOGFILE_PATH = f'{os.environ["TEMP"]}/vpn.log' if os.name == "nt" else "/tmp/vpn.log"
_LOGGING_CFG = os.path.join(os.path.dirname(os.path.realpath(__file__)), "vpn-logging-cfg.json")
logger: log_manager.LogManager

_DNS_NORDVPN_IPS = ("103.86.96.100", "103.86.99.100")

_SET_SETTINGS_TO_PRINTED_SETTING_NAME = {
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

_BOOL_STR_TO_ENABLE_STATUS = {
    "0": "disabled",
    "1": "enabled",
}

_PRINTED_SETTING_NAME_TO_PRINTED_VALUE_FORM_FUNC = {
    # "Technology" :"Technology",
    "firewall": lambda *args: _BOOL_STR_TO_ENABLE_STATUS[args[0]],
    # "Firewall Mark": lambda *args: ,
    # "Routing": lambda *args: ,
    "analytics": lambda *args: _BOOL_STR_TO_ENABLE_STATUS[args[0]],
    "killswitch": lambda *args: _BOOL_STR_TO_ENABLE_STATUS[args[0]],
    # "Threat Protection Lite": lambda *args: ,
    "notify": lambda *args: _BOOL_STR_TO_ENABLE_STATUS[args[0]],
    "autoconnect": lambda *args: _BOOL_STR_TO_ENABLE_STATUS[args[0]],
    # "IPv6": lambda *args: ,
    # "Meshnet": lambda *args: ,
    "dns": lambda *args: ", ".join(args),
    "lan-discovery": lambda *args: _BOOL_STR_TO_ENABLE_STATUS[args[0]],
}

_NORDVPN_ANALYTICS_OFF = ("nordvpn", "set", "analytics", "0")
_NORDVPN_AUTOCONNECT_ON = ("nordvpn", "set", "autoconnect", "1")
_NORDVPN_NOTIFY_ON = ("nordvpn", "set", "notify", "1")
_NORDVPN_FIREWALL_ON = ("nordvpn", "set", "firewall", "1")
_NORDVPN_KILLSWITCH_OFF = ("nordvpn", "set", "killswitch", "0")
_NORDVPN_KILLSWITCH_ON = ("nordvpn", "set", "killswitch", "1")
_NORDVPN_LAN_DISCOVERY = ("nordvpn", "set", "lan-discovery", "1")
_NORDVPN_DNS = ("nordvpn", "set", "dns", *_DNS_NORDVPN_IPS)

_NORDVPN_CONNECT = ("nordvpn", "connect")
_NORDVPN_DISCONNECT = ("nordvpn", "disconnect")
_NORDVPN_LOGIN = ("nordvpn", "login")
_NORDVPN_LOGOUT = ("nordvpn", "logout")
_NORDVPN_STATUS = ("nordvpn", "status")

_VPN_PRE_LOGIN_SETTINGS = (
    _NORDVPN_ANALYTICS_OFF,
    _NORDVPN_NOTIFY_ON,
    _NORDVPN_LAN_DISCOVERY,
    _NORDVPN_DNS,
    _NORDVPN_FIREWALL_ON,
)
_VPN_PRE_CONNECT_SETTINGS = (*_VPN_PRE_LOGIN_SETTINGS, _NORDVPN_AUTOCONNECT_ON)

_VPN_POST_CONNECT_SETTINGS = (_NORDVPN_KILLSWITCH_ON,)

_FLAG_TO_PRE_RUN_CMDS = {
    "connect": _VPN_PRE_CONNECT_SETTINGS,
    "disconnect": tuple(),
    "reconnect": _VPN_PRE_CONNECT_SETTINGS,  # TODO: is this right, also post for reconnect
    "status": tuple(),
    "login": tuple(),
    "logout": tuple(),
}

_FLAG_TO_POST_RUN_CMDS = {
    "connect": _VPN_POST_CONNECT_SETTINGS,
    "disconnect": (_NORDVPN_KILLSWITCH_OFF,),
    "reconnect": _VPN_POST_CONNECT_SETTINGS,
    "status": tuple(),
    "login": _VPN_PRE_LOGIN_SETTINGS,
    "logout": tuple(),
}


def _delete_if_exists(file_path: str) -> bool:
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def _print_stream_if_unempty(str_hdl: str, msg: str) -> None:
    if msg != "":
        logger.info(f"  {str_hdl}:\n{msg}")


def _log_cmd_w_output(cmd: Sequence[str], result, is_error: bool = True) -> None:
    if is_error:
        logger.error(f"failed to execute cmd: {' '.join(cmd)}")
    else:
        logger.info(f"executed cmd: {' '.join(cmd)}")
    _print_stream_if_unempty("stdout", _strip_nl_and_hyphens(result.stdout))
    _print_stream_if_unempty("stderr", _strip_nl_and_hyphens(result.stderr))


def subprocess_run_wrapped(cmd):
    return subprocess.run(
        cmd,
        # ["/usr/bin/env", "bash", "-c", " ".join(cmd)], # to force interpreter
        capture_output=True,
        check=False,
        text=True,
    )


# TODO: it is not understood why this is necessary, i.e. where the excess chars come from
def _strip_nl_and_hyphens(s: str) -> str:
    out_s = s
    startswith = lambda s, delims: any((s.startswith(d) for d in delims))
    endswith = lambda s, delims: any((s.endswith(d) for d in delims))
    symbols = ("\n", "-", "/", "\\", "|")
    while startswith(out_s, symbols) or endswith(out_s, ("\n", "-")):
        out_s = out_s.strip()
        out_s = out_s.strip("\n")
        out_s = out_s.strip("-")
    return out_s


def _str_time_duration_to_secs(duration_str: str) -> int:
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


def _get_time_now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _get_time_str_as_datetime_utc(s: str) -> datetime.datetime:
    return datetime.datetime.strptime(s, "%y%m%dT%H%M%SZ").replace(tzinfo=datetime.timezone.utc)


def _get_dict_from_json_file(json_file: str) -> Dict:
    if not os.path.exists(json_file):
        return {}
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore [no-any-return]


def _exec_nordvpn_cmd_w_error_handling(cmd: Sequence[str], print_on_succ: bool = False) -> bool:
    logger.info(f"executing cmd: {' '.join(cmd)}")
    result = subprocess_run_wrapped(cmd)
    if result.returncode == 0:
        if print_on_succ:
            _log_cmd_w_output(cmd, result, True)
        return True
    _log_cmd_w_output(cmd, result)
    return False


def _exec_nordvpn_set_cmd_w_error_handling(cmd: Sequence[str], settings: Dict, print_on_succ: bool = False) -> bool:
    assert cmd[1] == "set", cmd
    assert cmd[2] in settings, (cmd, settings)
    cmd_setting_value_as_would_be_printed = _PRINTED_SETTING_NAME_TO_PRINTED_VALUE_FORM_FUNC[cmd[2]](*cmd[3:])
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
    cmds: Sequence[Sequence[str]], settings: Dict, print_on_succ: bool = False
) -> bool:
    for cmd in cmds:
        if not _exec_nordvpn_set_cmd_w_error_handling(cmd, settings, print_on_succ):
            return False
    return True


def connect(is_connected: bool = False) -> bool:
    if is_connected:
        logger.info("skipping connect due to already being connected.")
        return True
    return _exec_nordvpn_cmd_w_error_handling(_NORDVPN_CONNECT)


def get_settings() -> Dict:
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
            if setting_w_value_colon_split[0] in _SET_SETTINGS_TO_PRINTED_SETTING_NAME:
                settings_to_values[_SET_SETTINGS_TO_PRINTED_SETTING_NAME[setting_w_value_colon_split[0]]] = (
                    setting_w_value_colon_split[1]
                )
        return settings_to_values
    _log_cmd_w_output(cmd, result)
    sys.exit(1)


def get_status() -> bool:
    cmd = _NORDVPN_STATUS
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
        if not _exec_nordvpn_cmd_w_error_handling(_NORDVPN_LOGIN):
            sys.exit(1)


def write_dict_to_file_as_json(json_dict: Dict, filename: str) -> None:
    with open(filename, "w", encoding="utf-8", newline="\n") as f:
        json.dump(json_dict, f)


def nordvpn_main(args: argparse.Namespace, vpn_status: Dict) -> None:
    # pylint: disable=[too-many-branches,too-many-locals,too-many-statements]
    time_now_datetime = _get_time_now_utc()
    time_now_str = time_now_datetime.strftime("%y%m%dT%H%M%SZ")

    logger.info("#### STATUS PRE CMD")
    status = get_status()

    if args.cron_job_pause_duration is not None:
        cron_job_pause_duration = _str_time_duration_to_secs(args.cron_job_pause_duration)
        cron_pause_until_datetime = time_now_datetime + datetime.timedelta(seconds=cron_job_pause_duration)
        cron_pause_until_str = cron_pause_until_datetime.strftime("%y%m%dT%H%M%SZ")
        cron_pause_until_duration = cron_pause_until_datetime - time_now_datetime
        vpn_status["cron_pause_until"] = cron_pause_until_str
        logger.info(
            f"Set cron_pause_until={cron_pause_until_str};"
            f" time_now={time_now_str};"
            f" cron_pause_until_duration={cron_pause_until_duration}"
        )

    if args.cron_job:
        pause_until_str = vpn_status.get("cron_pause_until", None)
        if pause_until_str is not None:
            pause_until_datetime = _get_time_str_as_datetime_utc(pause_until_str)
            if time_now_datetime < pause_until_datetime:
                logger.info(
                    f"Skipping cron job;"
                    f" time_now={time_now_str} < pause_until={pause_until_str};"
                    " setting args.flag=status"
                )
                args.flag = "status"
            else:
                logger.info(f"Executing cron job; time_now={time_now_str} >= pause_until={pause_until_str}")
                vpn_status["cron_pause_until"] = None
        else:
            logger.info(f"Executing cron job; time_now={time_now_str} >= pause_until={pause_until_str}")
            vpn_status["cron_pause_until"] = None

    pre_settings = get_settings()
    settings_str = "\n".join(
        f"  {setting_name}: {pre_value}"
        for setting_name, pre_value in sorted(list((k, v) for k, v in pre_settings.items()), key=lambda t: t[0])
    )
    logger.info(f"#### SETTINGS PRE CMD\n{settings_str}")
    logger.info("#### CHANGE SETTINGS PRE CMD")
    pre_connect_cmds = _FLAG_TO_PRE_RUN_CMDS[args.flag]
    if not _exec_nordvpn_set_cmds_w_error_handling(pre_connect_cmds, pre_settings):
        sys.exit(1)

    if args.flag == "status":
        if status:
            vpn_status["earliest_fail_connect"] = None
        return

    logger.info("#### CMD EXECUTION")
    connect_success = None
    if args.flag == "connect":
        connect_success = connect(status)
    elif args.flag == "disconnect":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORDVPN_DISCONNECT)
    elif args.flag == "login":
        login(status)
    elif args.flag == "logout":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORDVPN_LOGOUT, True)
    elif args.flag == "reconnect":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORDVPN_DISCONNECT)
        connect_success = connect(get_status())
    else:
        assert False, args.flag

    if connect_success is False:
        earliest_fail_connect = vpn_status.get("earliest_fail_connect", None)
        if earliest_fail_connect is None:
            vpn_status["earliest_fail_connect"] = time_now_str
        earliest_fail_connect_datetime = _get_time_str_as_datetime_utc(vpn_status["earliest_fail_connect"])
        if time_now_datetime - earliest_fail_connect_datetime > datetime.timedelta(
            seconds=_str_time_duration_to_secs(args.duration_fail_connect_until_notification)
        ):
            msg = f"vpn disconnected for time > duration_fail_connect_until_notification={args.duration_fail_connect_until_notification}"  # pylint: disable=line-too-long
            logger.error(msg)
            vpn_status["earliest_fail_connect"] = None
            sys.exit(1)

    logger.info("#### CHANGE SETTINGS POST CMD")
    post_settings = get_settings()
    post_connect_cmds = _FLAG_TO_POST_RUN_CMDS[args.flag]
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


def main(argparse_args: Optional[Sequence[str]] = None) -> None:
    # pylint: disable=[too-many-branches,too-many-locals,too-many-statements]
    parser = argparse.ArgumentParser()
    parser.add_argument("--cron-job", action="store_true")
    parser.add_argument("--cron-job-pause-duration", "--pause")
    parser.add_argument("--duration-fail-connect-until-notification", "--dfc", default="5m")
    file_status = f'{os.environ["TEMP"]}/vpn-status.json' if os.name == "nt" else "/tmp/vpn-status.json"
    parser.add_argument("--file-out-vpn-status", default=file_status)
    parser.add_argument("--lock-timeout-duration-rm", default="120s")
    parser.add_argument("--log")
    parser.add_argument("--log-cfg")
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

    global _LOGFILE_PATH, logger  # pylint: disable=global-statement
    _LOGFILE_PATH = _LOGFILE_PATH if args.log is None else args.log
    log_cfg = _LOGGING_CFG if args.log_cfg is None else args.log_cfg

    time_script_start_datetime = _get_time_now_utc()

    files_to_lock = (_LOGFILE_PATH, args.file_out_vpn_status)
    lm = lock_manager.LockManager(*files_to_lock, timeout=10)

    vpn_status = _get_dict_from_json_file(args.file_out_vpn_status)  # write must be atomic or this can get corrupted
    locks_deleted_log_msgs = []
    if vpn_status.get("time_last_lock", None) is None:
        for lock in lm.lock_names:
            if _delete_if_exists(lock):
                locks_deleted_log_msgs.append(f"Deleted lock={lock} as time_last_lock=None")
    else:
        time_last_lock_datetime = _get_time_str_as_datetime_utc(vpn_status["time_last_lock"])
        lock_timeout_duration_rm = datetime.timedelta(seconds=_str_time_duration_to_secs(args.lock_timeout_duration_rm))
        if time_script_start_datetime > (time_last_lock_datetime + lock_timeout_duration_rm):
            time_script_start_str = time_script_start_datetime.strftime("%y%m%dT%H%M%SZ")
            for lock in lm.lock_names:
                if _delete_if_exists(lock):
                    locks_deleted_log_msgs.append(
                        f"Deleted lock={lock} as "
                        f"time_script_start_str={time_script_start_str} > "
                        f"(time_last_lock={vpn_status['time_last_lock']} + "
                        f"lock_timeout_duration_rm={args.lock_timeout_duration_rm})",
                    )

    with lm:
        time_lock_datetime = _get_time_now_utc()
        time_lock_str = time_lock_datetime.strftime("%y%m%dT%H%M%SZ")
        vpn_status["time_last_lock"] = time_lock_str

        logger = log_manager.LogManager(__name__, log_manager.get_cfg_file_as_cfg_dict(log_cfg, globals()))

        logger.debug(f"argparse args:\n{argparse_utils.parsed_args_to_str(args)}")
        for msg in locks_deleted_log_msgs:
            logger.warning(msg)
        logger.debug(f"files_locked={files_to_lock} at time={time_lock_str}")
        if args.cron_job:
            logger.info("Start automated execution by cron job")

        try:
            if args.vpn_provider == "nordvpn":
                nordvpn_main(args, vpn_status)
            else:
                raise ValueError(args.vpn_provider)
        except BaseException as e:
            write_dict_to_file_as_json(vpn_status, args.file_out_vpn_status)
            raise e
        write_dict_to_file_as_json(vpn_status, args.file_out_vpn_status)


if __name__ == "__main__":
    main()
