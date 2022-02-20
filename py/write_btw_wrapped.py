#!/usr/bin/python3
#
# title: write_btw.py
#
# descr: read from file, filter and process content using user input, write output by inserting between section markers
#
# usage: see example_cmds below
#
# todos: take input file from pipe
#        python properly extract oy functions even if they have extra newlines

import argparse  # cmd line arg parsing
import os  # filesystem interactions
import re  # regex
import sys

from datetime import date

####################################################################################################
####################################################################################################
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    global args_raw
    global files_write
    global funcs_write
    global funcs_type
    global disp
    global file_read
    global all_read
    global empty
    global pattern
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-write", "-w", nargs="+")
    parser.add_argument("--funcs-write", "-x", nargs="+")
    parser.add_argument("--funcs-type", "-t")
    parser.add_argument("--disp", "-d", action="store_true")
    parser.add_argument("--file-read", "-r")
    parser.add_argument("--all-read", "-a", action="store_true")
    parser.add_argument("--empty", "-e", action="store_true")
    args = parser.parse_args()
    args_raw = argparse._sys.argv
    #### set script vars
    files_write = args.files_write
    funcs_write = args.funcs_write
    funcs_type = args.funcs_type
    disp = args.disp
    file_read = args.file_read
    all_read = args.all_read
    empty = args.empty
    #### check script vars
    assert len([x for x in [all_read, empty] if x != False]) <= 1
    if not empty:
        if not disp and not all_read:
            assert funcs_write != None
    if not disp:
        assert files_write != None
        for f in files_write:
            assert os.path.isfile(f)
    ## set pattern
    if not all_read:
        if not empty:
            assert funcs_type in ["bash", "ps1", "py"]
            if file_read != None:
                assert os.path.isfile(file_read)
            if funcs_type == "bash":
                file_read = (
                    os.environ["GWSSH"] + os.sep + "_helper-funcs.bash"
                    if file_read == None and "GWSSH" in os.environ
                    else file_read
                )
                pattern = r"(__[^\n]*?)\(\).*?\n\}"
            elif funcs_type == "ps1":
                file_read = (
                    os.environ["GWSPS"] + os.sep + "_helper-funcs.ps1"
                    if file_read == None and "GWSPS" in os.environ
                    else file_read
                )
                pattern = r"function *([^\n]*?) *\{\n.*?\n\}"
            elif funcs_type == "py":  # cannot have multiple newline in func
                file_read = (
                    os.environ["GWSPY"] + os.sep + "_helper-funcs.py"
                    if file_read == None and "GWSPY" in os.environ
                    else file_read
                )
                pattern = r"\ndef *([^\n]*?)\([^\n]*\n.*?(?=\n\n)"
            else:  # TODO: clean
                assert False
            assert file_read != None
        else:
            pattern = r"(pleasse doo not matcch)"  # TODO:
    else:
        pattern = r"(.*)"


def extract_funcs(f, pattern):
    funcs = []
    with open(f, "r") as f:
        f_str = f.read()
        match = re.finditer(pattern, f_str, flags=re.S)
        assert match
        for m in match:
            funcs.append(m)
        return funcs


def write_over_patterns(fs, pattern, string):
    for f in fs:
        with open(f, "r+") as f:
            f_str = f.read()
            match = re.search(pattern, f_str, flags=re.S)
            assert match  # TODO: means no patterns in file
            f.seek(0)
            f.write(f_str.replace(match.group(0), string))
            f.truncate()
            print("INFO: wrote to file: " + str(f.name))


####################################################################################################
####################################################################################################
#### default values
files_write = []
funcs_write = []
funcs_type = ""
file_read = ""
disp = False
all_read = False
empty = False
pattern = None
#### checks and overwrites default values using script input
parse_inputs()
#### hardcoded values
beg = "################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################"
end = "################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################"
## disclaimer generation
for i, arg_raw in enumerate(args_raw):
    for env_var in ["GWSPY", "GWSSH", "GWSPS", "GWSA", "GWSS", "GWS"]:
        if env_var in os.environ:
            if os.environ[env_var] in arg_raw:
                args_raw[i] = arg_raw.replace(os.environ[env_var], r"${" + env_var + r"}")
                break
_disclaimers = [
    f"# yymmdd: {date.today().strftime('%y%m%d')}",
    "# generation cmd on the following line:",
    f'# python "{" ".join(args_raw)}"',
]
disclaimer = "\n".join(_disclaimers)
## cmds
example_cmds = [
    "## The below cmds display the available funcs for bash and ps1 scripts",
    'python "${GWSPY}/write_btw.py" -t bash -d',
    'python "${GWSPY}/write_btw.py" -t ps1 -d',
    'python "${GWSPY}/write_btw.py" -t py -d',
    "## The below cmds write to specific files and can/should be ran regularly",
    'python "${GWSPY}/write_btw.py" -t py -w "${GWSPY}/mfmv" -x except_if_not mv_atomic',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWS}/init/init.bash" -x __echo __yes_no_prompt __check_if_objs_exist __append_line_to_file_if_not_found',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWSA}/init/init.bash" -x __echo __check_if_objs_exist __append_line_to_file_if_not_found',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWSM}/init/init.bash" -x __echo __check_if_objs_exist __append_line_to_file_if_not_found',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWSS}/init/init.bash" -x __echo __check_if_objs_exist __append_line_to_file_if_not_found',
    'python "${GWSPY}/write_btw.py" -t ps1 -w "${GWS}/init/init.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write_btw.py" -t ps1 -w "${GWSA}/init/init.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write_btw.py" -t ps1 -w "${GWSM}/init/init.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write_btw.py" -t ps1 -w "${GWSS}/init/init.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWS}/.git-hooks/gitignore/gitignore-gen.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __check_if_objs_exist',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWSA}/.git-hooks/gitignore/gitignore-gen.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __check_if_objs_exist',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWSM}/.git-hooks/gitignore/gitignore-gen.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __check_if_objs_exist',
    'python "${GWSPY}/write_btw.py" -t bash -w "${GWSS}/.git-hooks/gitignore/gitignore-gen.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __check_if_objs_exist',
]

if disp:
    funcs = extract_funcs(file_read, pattern)
    if not empty:
        assert len(funcs) > 0
    print(beg)
    print(disclaimer)
    for f in funcs:
        print(f.group(1))
    print(end)
    for c in example_cmds:
        print(c)
    sys.exit()

if empty:
    print("INFO: mode is empty")
    txt_write = f"{beg}\n{end}"
elif all_read:
    print("INFO: mode is all_read")
    with open(file_read, "r") as f:
        txt_write = f"{beg}\n{f.read()}\n{end}"
else:
    print("INFO: mode is funcs")
    funcs = extract_funcs(file_read, pattern)
    for f in funcs_write:
        assert f in [func.group(1) for func in funcs]
    funcs_write = [func.group(0).strip(" \t\n") for func in funcs if func.group(1) in funcs_write]
    txt_write = f"{beg}\n{disclaimer}\n\n{'\n\n'.join(funcs_write)}\n{end}"

write_over_patterns(files_write, r"" + beg + ".*?" + end, txt_write)
