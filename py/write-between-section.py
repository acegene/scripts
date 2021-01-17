import argparse # cmd line arg parsing
import os # filesystem interactions
import sys
import re # regex
# descr: adds line to source src.bash
# usage: cd "${GWS}" && python scripts/py/write-between-section.py -w init/init.bash -r scripts/shell/__supplemental-functions.bash -x __echo __yes_no_prompt __check_if_obj_exists __append_line_to_file_if_not_found
#        cd "${GWS}" && python scripts/py/write-between-section.py -w aliases/init/init.bash -r scripts/shell/__supplemental-functions.bash -x __echo __check_if_obj_exists __append_line_to_file_if_not_found
####################################################################################################
####################################################################################################
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    global files_write; global funcs_write; global file_read; global disp_funcs; global all_read; global empty
    ## cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-write", "-w", nargs='+')
    parser.add_argument("--funcs-write", "-x", nargs='+')
    parser.add_argument("--disp-funcs", "-d", action='store_true')
    parser.add_argument("--file-read", "-r")
    parser.add_argument("--all-read", "-a", action='store_true')
    parser.add_argument("--empty", "-e", action='store_true')
    args = parser.parse_args()
    ## set script vars
    files_write = args.files_write
    funcs_write = args.funcs_write
    disp_funcs = args.disp_funcs
    file_read = args.file_read
    all_read = args.all_read
    empty = args.empty
    ## check values
    assert(len([x for x in [all_read, empty, disp_funcs] if x != False]) <= 1)
    if not empty:
        assert(file_read is not None)
        if not disp_funcs:
            assert(files_write is not None)
            if not all_read:
                assert(funcs_write is not None)
    for f in files_write:
        assert(os.path.isfile(f))
    assert(os.path.isfile(file_read))

def extract_funcs(f):
    funcs = []
    with open(f, 'r') as f:
        f_str = f.read()
        match = re.finditer(r"(__.*?)\(\).*?\n\}", f_str, flags=re.S)
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
## default values
files_write = []; funcs_write = []; file_read = ''; disp_funcs = False; all_read = False; empty = False
## checks and overwrites default values using script input
parse_inputs()
## hardcoded values
beg = '################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################'
end = '################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################'

if disp_funcs:
    funcs = extract_funcs(file_read)
    for f in funcs:
        print(f.group(1))
    print('\n' + beg + '\n' + end)
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
    funcs = extract_funcs(file_read)
    for f in funcs_write:
        assert(f in [func.group(1) for func in funcs])
    funcs_write = [func.group(0) for func in funcs if func.group(1) in funcs_write]
    txt_write = beg + '\n' + '\n\n'.join(funcs_write) +  '\n' + end

write_over_patterns(files_write, r"" + beg + ".*?" + end, txt_write)
