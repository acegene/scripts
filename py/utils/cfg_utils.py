import os
import re
import sys


def expand_env_vars(input_string: str) -> str:
    ## matches ${ENV_VAR:VAR_NAME}
    pattern = r"\${(ENV_VAR):([^}]+)}"

    ## replace matches with expanded env variables
    def replace_env_var(match):
        env_type, var_name = match.groups()
        if env_type == "ENV_VAR":
            expanded_var = os.path.expandvars(f"${var_name}")  # alternative: os.environ.get("VAR")
            return expanded_var
        return match.group(0)  # original match if not ENV_VAR

    # replace all matches in the input string
    result_string = re.sub(pattern, replace_env_var, input_string)
    return result_string


def create_path_from_relative_type(relative_type: str, relatives: dict[str, dict] | None = None) -> str:
    relatives = {} if relatives is None else relatives

    ## if relative_type is in relatives than that overrides below defaults
    relative = relatives.get(relative_type, None)
    if relative is not None:
        return create_path_from_relative_path(relative, relatives)
    ## default relative_types, note that HOME is based on current user
    if relative_type == "ABSOLUTE":
        return ""
    if relative_type == "CWD":
        return os.getcwd()
    if relative_type == "HOME":
        return os.path.expanduser("~")

    print(f"FATAL: unexpected relative_type={relative_type}; relatives={relatives}")
    sys.exit(1)


def create_path_from_relative_path(relative_path: dict, relatives: dict[str, dict] | None = None) -> str:
    path_base = create_path_from_relative_type(relative_path.get("relative_type", "ABSOLUTE"), relatives)
    path_suffix = relative_path["path"]  # TODO: consider OS with dir seps
    return expand_env_vars(f"{path_base}{path_suffix}")
