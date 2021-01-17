# descr: read from file, filter and process content using user input, write output by inserting between section markers
#
# usage: see example_cmds variable below
#
# todos: take input file from pipe

import argparse # cmd line arg parsing
import os # filesystem interactions
import sys
import re # regex
from datetime import date
####################################################################################################
####################################################################################################
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    global args_raw; global files_write; global funcs_write; global funcs_type; global disp; global file_read; global all_read; global empty; global pattern
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-write", "-w", nargs='+')
    parser.add_argument("--funcs-write", "-x", nargs='+')
    parser.add_argument("--funcs-type", "-t")
    parser.add_argument("--disp", "-d", action='store_true')
    parser.add_argument("--file-read", "-r")
    parser.add_argument("--all-read", "-a", action='store_true')
    parser.add_argument("--empty", "-e", action='store_true')
    args = parser.parse_args()
    args_raw = argparse._sys.argv
    #### set script vars
    files_write = args.files_write; funcs_write = args.funcs_write; funcs_type = args.funcs_type; disp = args.disp
    file_read = args.file_read; all_read = args.all_read; empty = args.empty
    #### check script vars
    assert(len([x for x in [all_read, empty] if x != False]) <= 1)
    if not empty:
        assert(file_read is not None and os.path.isfile(file_read))
        if not disp and not all_read:
            assert(funcs_write is not None)
    if not disp:
        assert(files_write is not None)
        for f in files_write:
            assert(os.path.isfile(f))
    ## set pattern
    if not all_read:
        if not empty:
            assert(funcs_type in ["bash", "ps1"])
            if funcs_type == 'bash':
                pattern = r"(__.*?)\(\).*?\n\}"
            elif funcs_type == 'ps1':
                pattern = r"function (.*?) *\{.*?\n\}"
            else: # TODO: clean
                assert(False)
        else:
            pattern = r"(pleasse doo not matcch)" # TODO:
    else:
        pattern = r"(.*)"

def extract_funcs(f, pattern):
    funcs = []
    with open(f, 'r') as f:
        f_str = f.read()
        match = re.finditer(pattern, f_str, flags=re.S)
        assert(match)
        for m in match:
            funcs.append(m)
        return funcs

def write_over_patterns(fs, pattern, string):
    for f in fs:
        with open(f, 'r+') as f:
            f_str = f.read()
            match = re.search(pattern, f_str, flags=re.S)
            assert(match)
            f.seek(0)
            f.write(f_str.replace(match.group(0), string))
            f.truncate()
            print('NOTE: wrote to file: ' + str(f.name))
####################################################################################################
####################################################################################################
#### default values
files_write = []; funcs_write = []; funcs_type = ''; file_read = ''; disp = False; all_read = False; empty = False
pattern = None
#### checks and overwrites default values using script input
parse_inputs()
#### hardcoded values
beg = '################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################'
end = '################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################'
## disclaimer generation
for i, arg_raw in enumerate(args_raw):
    for env_var in ['GWSPY', 'GWSSH', 'GWSPS', 'GWSA', 'GWSS', 'GWS']:
        if env_var in os.environ:
            if os.environ[env_var] in arg_raw:
                args_raw[i] = arg_raw.replace(os.environ[env_var], r'${' + env_var + r'}')
                break

_disclaimers = [
    '# date of generation: ' + date.today().strftime("%y%m%d") ,
    '# generation cmd on the following line:',
    '# python "' +  '" "'.join(args_raw) + '"'
]
disclaimer = '\n'.join(_disclaimers)
## as an fyi
example_cmds = [
    '## The below cmds display the available funcs for bash and ps1 scripts',
    'python "${GWSPY}/write-btw.py" -t bash -r "${GWSSH}/_helper-funcs.bash" -d',
    'python "${GWSPY}/write-btw.py" -t ps1 -r "${GWSPS}/_helper-funcs.ps1" -d',
    '## The below cmds write to specific files and can/should be ran regularly',
    'python "${GWSPY}/write-btw.py" -t bash -w "${GWS}/init/init.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __yes_no_prompt __check_if_obj_exists __append_line_to_file_if_not_found',
    'python "${GWSPY}/write-btw.py" -t bash -w "${GWSA}/init/init.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __check_if_obj_exists __append_line_to_file_if_not_found',
    'python "${GWSPY}/write-btw.py" -t bash -w "${GWSS}/init/init.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __check_if_obj_exists __append_line_to_file_if_not_found',
    'python "${GWSPY}/write-btw.py" -t ps1 -w "${GWS}/init/init.ps1" -r "${GWSPS}/_helper-funcs.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write-btw.py" -t ps1 -w "${GWSA}/init/init.ps1" -r "${GWSPS}/_helper-funcs.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write-btw.py" -t ps1 -w "${GWSS}/init/init.ps1" -r "${GWSPS}/_helper-funcs.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write-btw.py" -t ps1 -w "${LEW}/init/init.ps1" -r "${GWSPS}/_helper-funcs.ps1" -x Group-Unspecified-Args',
    'python "${GWSPY}/write-btw.py" -t bash -w "${LEW}/init/init.bash" -r "${GWSSH}/_helper-funcs.bash" -x __echo __check_if_obj_exists __append_line_to_file_if_not_found',
]

if disp:
    funcs = extract_funcs(file_read, pattern)
    if not empty:
        assert(len(funcs) > 0)
    print(beg)
    print(disclaimer)
    for f in funcs:
        print(f.group(1))
    print(end)
    for c in example_cmds:
        print(c)
    sys.exit()

if empty:
    print('NOTE: mode is empty')
    txt_write = beg + '\n' + end
elif all_read:
    print('NOTE: mode is all_read')
    with open(file_read, 'r') as f:
        txt_write = beg + '\n' + f.read() + '\n' + end
else:
    print('NOTE: mode is funcs')
    funcs = extract_funcs(file_read, pattern)
    for f in funcs_write:
        assert(f in [func.group(1) for func in funcs])
    funcs_write = [func.group(0) for func in funcs if func.group(1) in funcs_write]
    txt_write = beg + '\n' + disclaimer + '\n\n' + '\n\n'.join(funcs_write) +  '\n' + end

write_over_patterns(files_write, r"" + beg + ".*?" + end, txt_write)
