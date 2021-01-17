#!/usr/bin/python3
#
# descr: removes various filetypes that mac autogenerates

import os # os.walk, os.path, os.stat, os.path.join, os.path.isdir, os.path.isfile
import argparse # argparse.ArgumentParser
import sys # sys.exit production ready
import shutil # shutil.rmtree
####################################################################################################
####################################################################################################
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    global dir_walk
    ## cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", "-d", default='.')
    args = parser.parse_args()
    ## set variables via cmd line args
    dir_walk = args.dir
    ## check and fix variables
    assert(os.path.isdir(dir_walk))

def get_rm_objs(files_bad, dirs_bad):
    """Return lists of files/dirs that needs to be rm'd based on bad files/dirs parameters"""
    files_rm = []; dirs_rm = []
    for currentpath, folders, files in os.walk(dir_walk):
        for file in files:
            for bf in files_bad:
                if file == bf:
                    files_rm.append(os.path.join(currentpath, file))
            if file.startswith('._'):
                files_rm.append(os.path.join(currentpath, file))
        for dir in folders:
            for bd in dirs_bad:
                if dir == bd:
                    dirs_rm.append(os.path.join(currentpath, dir))
    files_rm = sorted(files_rm, key=lambda x: os.stat(x).st_size)
    dirs_rm = sorted(dirs_rm, key=lambda x: os.stat(x).st_size)
    assert(len(files_rm) + len(dirs_rm) > 0)
    return files_rm, dirs_rm

def print_user_feedback(files_rm, dirs_rm):
    """Print some useful info to the user of what objects are ready for rm"""
    rm_max_sz_width = '{0:>' + str(len(str(max([os.stat(val).st_size for val in dirs_rm + files_rm])))) + '}' # formatting
    print('#### DIRS ####')
    for d_rm in dirs_rm:
        print(rm_max_sz_width.format(str(os.stat(d_rm).st_size)) + ' - ' + d_rm)
    print('#### FILES ####')
    for f_rm in files_rm:
        print(rm_max_sz_width.format(str(os.stat(f_rm).st_size)) + ' - ' + f_rm)

def rm_objs_user_prompt(files_rm, dirs_rm):
    print('enter yes/no on whether to delete the above files')
    choice = input().lower()
    if choice == 'yes' or choice == 'y':
        print('removing...')
        for d_rm in dirs_rm:
            os.chmod(d_rm, 0o777)
            shutil.rmtree(d_rm)
        for f_rm in files_rm:
            os.chmod(f_rm, 0o777)
            os.remove(f_rm)
    elif choice == 'no' or choice == 'n':
        pass
    else:
        print("ERROR: respond with yes/no")
####################################################################################################
####################################################################################################
#### default values
dir_walk = ''
#### checks and overwrites default values using script input
parse_inputs()
#### hardcoded values
files_bad = ['.com.apple.timemachine.donotpresent', '.DS_Store', '.apDisk', '.VolumeIcon.icns', '.fseventsd', '.TemporaryItems']
dirs_bad = ['.Spotlight-V100', '.Trash', '.Trashes', '.fseventsd', '.TemporaryItems']
#### get objects to remove using lists of bad objects
files_rm, dirs_rm = get_rm_objs(files_bad, dirs_bad)
#### print candidates for removal
print_user_feedback(files_rm, dirs_rm)
#### ask for user feedback on whether to remove the listed objects, then delete
rm_objs_user_prompt(files_rm, dirs_rm)