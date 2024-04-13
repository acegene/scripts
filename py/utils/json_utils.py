import os
import sys

from typing import Dict, Optional, Sequence


def create_path_from_json_path(json_path: Sequence[Dict[str, str]]) -> str:
    path = ""
    for path_piece in json_path:
        if path_piece["path_type"] == "DIRECTORY":
            path += path_piece["value"]
        elif path_piece["path_type"] == "DIRECTORY_SEPARATOR":
            path += os.sep
        elif path_piece["path_type"] == "ENV_VAR":
            path += os.path.expandvars(f"${path_piece['value']}")  # alternative: os.environ.get("VAR")
        elif path_piece["path_type"] == "FILE":
            path += path_piece["value"]
        else:
            print(f"FATAL: unexpected path_piece['path_type']={path_piece['path_type']}")
            sys.exit(1)
    return path


def create_path_from_json_relative_path(json_relative_path: Dict, relatives: Optional[Dict[str, Dict]] = None) -> str:
    path_base = create_path_from_relative_type(json_relative_path["relative_type"], relatives)
    if "path" in json_relative_path:
        path_suffix = create_path_from_json_path(json_relative_path["path"])
    elif "path_array" in json_relative_path:
        path_suffix = "".join([f"{os.sep}{path}" for path in json_relative_path["path_array"]])
    else:
        assert False, "ERROR: expected one of 'path' or 'path_array' key"
    return f"{path_base}{path_suffix}"


def create_path_from_relative_type(relative_type: str, relatives: Optional[Dict[str, Dict]] = None) -> str:
    relatives = {} if relatives is None else relatives

    relative = relatives.get(relative_type, None)
    if relative is not None:
        return create_path_from_json_relative_path(relative, relatives)
    if relative_type == "ABSOLUTE":
        return ""
    if relative_type == "CWD":
        return os.getcwd()
    if relative_type == "HOME":
        return os.path.expanduser("~")

    print(f"FATAL: unexpected relative_type={relative_type}; relatives={relatives}")
    sys.exit(1)
