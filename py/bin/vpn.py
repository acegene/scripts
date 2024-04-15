#!/usr/bin/env python3

import argparse
import subprocess
import sys

from collections import OrderedDict

# TODO: make sure not connected when attempting login
# TODO: meshnet

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

_int_to_enabled_status = {
    "0": "disabled",
    "1": "enabled",
}

_PRINTED_SETTING_NAME_TO_PRINTED_VALUE_FORM_FUNC = {
    # "Technology" :"Technology",
    "firewall": lambda *args: _int_to_enabled_status[args[0]],
    # "Firewall Mark": lambda *args: ,
    # "Routing": lambda *args: ,
    "analytics": lambda *args: _int_to_enabled_status[args[0]],
    "killswitch": lambda *args: _int_to_enabled_status[args[0]],
    # "Threat Protection Lite": lambda *args: ,
    "notify": lambda *args: _int_to_enabled_status[args[0]],
    "autoconnect": lambda *args: _int_to_enabled_status[args[0]],
    # "IPv6": lambda *args: ,
    # "Meshnet": lambda *args: ,
    "dns": lambda *args: ", ".join(args),
    "lan-discovery": lambda *args: _int_to_enabled_status[args[0]],
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


def _print_stream_if_unempty(str_hdl, msg):
    if msg != "":
        print(f"  {str_hdl}: {msg}")


def _print_cmd_w_output(cmd, result, is_error=True):
    if is_error:
        print(f"ERROR: failed to execute cmd: {' '.join(cmd)}")
    else:
        print(f"INFO: executed cmd: {' '.join(cmd)}")
    _print_stream_if_unempty("stdout", _strip_nl_and_hyphens(result.stdout))
    _print_stream_if_unempty("stderr", _strip_nl_and_hyphens(result.stderr))


# TODO: it is not understood why this is necessary, i.e. where the excess chars come from
def _strip_nl_and_hyphens(s):
    out_s = s
    startswith = lambda s, delims: any((s.startswith(d) for d in delims))
    endswith = lambda s, delims: any((s.endswith(d) for d in delims))
    while startswith(out_s, ("\n", "-")) or endswith(out_s, ("\n", "-")):
        out_s = out_s.strip()
        out_s = out_s.strip("\n")
        out_s = out_s.strip("-")
    return out_s


def _exec_nordvpn_cmd_w_error_handling(cmd, print_on_succ=False):
    print(f"INFO: executing cmd: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, check=False, text=True)
    if result.returncode == 0:
        if print_on_succ:
            _print_cmd_w_output(cmd, result, True)
        return True
    _print_cmd_w_output(cmd, result)
    return False


def _exec_nordvpn_set_cmd_w_error_handling(cmd, settings, print_on_succ=False):
    assert cmd[1] == "set", cmd
    assert cmd[2] in settings, (cmd, settings)
    cmd_setting_value_as_would_be_printed = _PRINTED_SETTING_NAME_TO_PRINTED_VALUE_FORM_FUNC[cmd[2]](*cmd[3:])
    current_setting_value = settings[cmd[2]]
    if cmd_setting_value_as_would_be_printed == current_setting_value:
        print(f"INFO: skipping cmd: {cmd}; {cmd[2]}: {current_setting_value}")
        return True

    print(f"INFO: executing cmd: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, check=False, text=True)
    if result.returncode == 0:
        if print_on_succ:
            _print_cmd_w_output(cmd, result, True)
        return True
    _print_cmd_w_output(cmd, result)
    return False


def _exec_nordvpn_cmd_w_exit_on_failure(cmd, print_on_succ=False):
    if not _exec_nordvpn_cmd_w_error_handling(cmd, print_on_succ):
        sys.exit(1)


def _exec_nordvpn_set_cmds_w_error_handling(cmds, settings, print_on_succ=False):
    for cmd in cmds:
        if not _exec_nordvpn_set_cmd_w_error_handling(cmd, settings, print_on_succ):
            return False
    return True


def connect(is_connected=False):
    if is_connected:
        print("INFO: skipping connect due to already being connected.")
    else:
        if not _exec_nordvpn_cmd_w_error_handling(_NORDVPN_CONNECT):
            sys.exit(1)


def get_settings():
    cmd = ("nordvpn", "settings")
    result = subprocess.run(cmd, capture_output=True, check=False, text=True)
    settings_to_values = OrderedDict()
    if result.returncode == 0:
        setting_lines = _strip_nl_and_hyphens(result.stdout).split("\n")
        settings_w_value = []
        for line in setting_lines:
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
    _print_cmd_w_output(cmd, result)
    sys.exit(1)


def get_status():
    cmd = _NORDVPN_STATUS
    result = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE)
    if result.returncode == 0:
        print(_strip_nl_and_hyphens(result.stdout))
    else:
        _print_cmd_w_output(cmd, result)
        sys.exit(1)

    if "Status: Connected" in result.stdout:
        return True
    if "Status: Disconnected" in result.stdout:
        return False
    assert False, print(result.stdout)


def login(is_connected=False):
    if is_connected:
        print("INFO: skipping login due to already being connected.")
    else:
        if not _exec_nordvpn_cmd_w_error_handling(_NORDVPN_LOGIN):
            sys.exit(1)


def nordvpn_main(args):
    print("#### STATUS PRE CMD")
    status = get_status()

    print("#### SETTINGS PRE CMD")
    pre_settings = get_settings()
    for setting_name, pre_value in sorted(list((k, v) for k, v in pre_settings.items()), key=lambda t: t[0]):
        print(f"{setting_name}: {pre_value}")
    print("#### CHANGE SETTINGS PRE CMD")
    pre_connect_cmds = _FLAG_TO_PRE_RUN_CMDS[args.flag]
    if not _exec_nordvpn_set_cmds_w_error_handling(pre_connect_cmds, pre_settings):
        sys.exit(1)

    if args.flag == "status":
        return

    print("#### CMD EXECUTION")
    if args.flag == "connect":
        connect(status)
    elif args.flag == "disconnect":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORDVPN_DISCONNECT)
    elif args.flag == "login":
        login(status)
    elif args.flag == "logout":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORDVPN_LOGOUT, True)
    elif args.flag == "reconnect":
        _exec_nordvpn_cmd_w_exit_on_failure(_NORDVPN_DISCONNECT)
        connect(get_status())
    else:
        assert False, args.flag

    print("#### CHANGE SETTINGS POST CMD")
    post_settings = get_settings()
    post_connect_cmds = _FLAG_TO_POST_RUN_CMDS[args.flag]
    if not _exec_nordvpn_set_cmds_w_error_handling(post_connect_cmds, post_settings):
        sys.exit(1)

    final_settings = get_settings()

    print("#### STATUS POST CMD")
    status = get_status()
    print("#### SETTINGS CHANGED")
    for setting_name, pre_value in sorted(list((k, v) for k, v in pre_settings.items()), key=lambda t: t[0]):
        final_value = final_settings[setting_name]
        if pre_value != final_value:
            print(f"INFO: changed '{setting_name}' from '{pre_value}' to '{final_value}'")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vpn-provider", "--vpn", choices=["nordvpn"], default="nordvpn")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--connect", "-c", action="store_const", const="connect", dest="flag")
    group.add_argument("--disconnect", "-d", action="store_const", const="disconnect", dest="flag")
    group.add_argument("--login", "--li", "-l", action="store_const", const="login", dest="flag")
    group.add_argument("--logout", "--lo", action="store_const", const="logout", dest="flag")
    group.add_argument("--reconnect", "-r", action="store_const", const="reconnect", dest="flag")
    group.add_argument("--status", "-s", action="store_const", const="status", dest="flag")
    args = parser.parse_args()

    if args.vpn_provider == "nordvpn":
        nordvpn_main(args)
    else:
        assert False, args.vpn_provider


if __name__ == "__main__":
    main()
