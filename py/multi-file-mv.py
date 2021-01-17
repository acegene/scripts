import os # filesystem interactions
import argparse # cmd line arg parsing
import json # json file i/o
import re # regex
####################################################################################################
####################################################################################################
## files for import
if 'GWSSTOR' in os.environ:
    json_globals_file = os.path.join(os.environ['GWSSTOR'], 'globals.json')
else:
    print('WARNING: could not find GWSSTOR environment var')
    json_globals_file = None
####################################################################################################
#################################################################################################### 
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    global dir_walk; global dir_out; global part_out; global exts; global excludes
    ## cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--part-out", "-p", default='-pt1')
    parser.add_argument("--dir", "-d", default='.')
    parser.add_argument("--dir-out", "-o")
    parser.add_argument("--exts", "-e", nargs='+')
    parser.add_argument("--excludes", "-x", nargs='+')
    args = parser.parse_args()
    ## set variables via cmd line args
    dir_walk = args.dir
    dir_out = args.dir_out
    part_out = args.part_out
    exts = args.exts
    excludes = args.excludes
    ## check and fix variables
    if exts == None:
        if json_globals_file != None:
            exts = '|'.join(['.' + val for val in import_vid_exts()])
        else:
            print('ERROR: extensions must be specified')
            exit()
    else:
        exts = '|'.join(exts)
    if not os.path.isdir(dir_walk):
        print('ERROR: the following directory seems to not exist: ' + dir_orig)
        exit()
    if dir_out != None:
        if not os.path.isdir(dir_out):
            print('ERROR: the following directory seems to not exist: ' + dir_out)
            exit()
def import_vid_exts(f=json_globals_file):
    """Returns extensions from global file f"""
    with open(f, 'r') as json_file:
        data = json.load(json_file)
        return data['globals']['video_extensions']
def gen_default_part_arrs():
    part_array_A = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'] # vidnameA, vidnameB, etc.
    part_array_B = [str(val) for val in range(1,27)] # vidname1, vidname2, etc.
    part_array_C = ['0' + val for val in part_array_B] # vidname01, vidname02, etc. 
    part_array_D = ['00' + val for val in part_array_B] # vidname001, vidname002, etc.
    part_array_E = ['cd' + val for val in part_array_B] # vidnamecd1, vidnamecd2, etc.
    part_array_F = ['pt' + val for val in part_array_B] # vidnamept1, vidnamept2, etc.
    part_array_G = ['part' + val for val in part_array_B] # vidnamepart1, vidnamepart2, etc.
    ## ordering of return value is necessary to allow prioritization of which part_array to match against
    return [part_array_A,part_array_E,part_array_F,part_array_G,part_array_B,part_array_C,part_array_D]
def get_part_array_out(part_arrays, part_out):
    for part_array in part_arrays:
        regex = '^' + part_prefix + '(' + part_array[0] +')$'
        result = re.search(regex, part_out)
        if result != None:
            return [result.group(1) + val for val in part_array]
    else:
        print('ERROR: --part-out arg of \'' + part_out + '\' is not recognized')
        exit()
def get_rename_arrays(files, dir, part_arrays, part_array_out):
    for f in files:
        for part_array in part_arrays:
            regex = '^(.*?)' + part_prefix + '(' + part_array[0] +')(' + exts + ')$'
            result = re.search(regex, f, re.IGNORECASE)
            regex_out = '^(.*?)' + part_prefix + '(' + part_array_out[0] +')(' + exts + ')$'
            result_out = re.search(regex_out, f, re.IGNORECASE)
            if result != None:
                if result_out == None: #  or len(result.group(0)) > len(result_out.group(0)):
                    file_base = result.group(1); file_prepart = result.group(2); file_part = result.group(3); file_ext = result.group(4)
                    if file_part == part_array[0]:
                        files_out = [file_base + file_prepart + part_array[0] + file_ext]
                        files_out_renamed = [file_base + part_array_out[0] + file_ext]
                        for i, (part, part_out) in enumerate(zip(part_array[1:], part_array_out[1:])): # TODO: handle more than 26
                            if os.path.isfile(os.path.join(dir, file_base + file_prepart + part + file_ext)):
                                files_out.append(file_base + file_prepart + part + file_ext)
                                files_out_renamed.append(file_base + part_out + file_ext)
                            else:
                                break
                        if len(files_out) != 1:
                            return files_out, files_out_renamed
                else:
                    return [], []
    return [], []
def mv_using_arrays(arr_orig, arr_out, dir_orig, dir_out=None):
    if dir_out == None:
        dir_out = dir_orig
    arr_orig_full = [os.path.join(dir_orig, val) for val in arr_orig]
    arr_out_full = [os.path.join(dir_out, val) for val in arr_out]
    for orig, out in zip(arr_orig_full, arr_out_full):
        print('mv of ' + orig + ' to ' + out)
    print('enter yes/no/quit on whether to perform the above moves')
    while True:
        choice = input().lower()
        if choice == 'yes' or choice == 'y':
            print('moving...')
            for orig, out in zip(arr_orig_full, arr_out_full):
                os.rename(orig, out) 
            break
        elif choice == 'no' or choice == 'n':
            break
        elif choice == 'quit' or choice == 'q':
            exit()
        else:
            print("ERROR: respond with yes/no/quit")
####################################################################################################
####################################################################################################
## default values
dir_walk = []; dir_out = []; part_out = ''; exts = ''; excludes = []
## checks and overwrites default values using script input
parse_inputs()
## hardcoded
part_prefix = '( - |_|-|| )'
part_arrays = gen_default_part_arrs()
## find the appropriate part suffix for the output of mv
part_array_out = get_part_array_out(part_arrays, part_out)
## recursively find all dirs in dir_walk then removing all directories in excludes
dirs_walk = [val[0] for val in os.walk(dir_walk) if os.walk(dir_walk)]
if excludes != None:
    for exclude in excludes:
        dirs_walk = [val for val in dirs_walk if exclude.lower() not in val.lower()]
## get os.rename lists one by one and prompt user for mv confirmation until they choose to quit
for dir_orig in dirs_walk:
    while True:
        files = [f for f in os.listdir(dir_orig) if os.path.isfile(os.path.join(dir_orig, f))]
        files_out, files_out_renamed = get_rename_arrays(files, dir_orig, part_arrays, part_array_out)
        if len(files_out) == 0:
            # print('no applicable files in directory: ' + dir_orig)
            break
        if dir_out != None:
            mv_using_arrays(files_out, files_out_renamed, dir_orig, dir_out)
        else:
            mv_using_arrays(files_out, files_out_renamed, dir_orig, dir_orig)