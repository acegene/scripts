#!/usr/bin/python3
#
# descr: autodetects any multi-file and provides an interactive cli to batch rename the multi-file
#
# usage: python multi-file-rename.py --help
#
#        python multi-file-rename.py --ee --po=-pt1 -x .git third-party --mx 50
#
# warns: race condition during batch renames if another process moves the files, relativel
#
# todos: handle files without extensions better
#        proper cmd args mutual exclusion
#        allow sequences that dont start with 1 or a to be found and specified as the output 

import os # filesystem interactions
import sys
import argparse # cmd line arg parsing
import re # regex
import json # json file i/o
from typing import List
####################################################################################################
#################################################################################################### 
def parse_inputs() -> None:
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    ## global vars
    global dir_in; global dir_out; global part_out
    global excludes; global exts
    global inplace; global maxdepth; global mindepth
    #### local funcs
    def import_json_obj(f:str, key:str) -> List[str]:
        """Returns json object associated with key from file"""
        with open(f, 'r') as json_file:
            data = json.load(json_file)
            assert(key in data)
            return data[key]
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir-in', '-i', default='.', help='directory to search for multifiles')
    parser.add_argument('--dir-out', '-o', help='directory to move renamed multifiles into')
    parser.add_argument('--part-out', '--po', default='-pt1', help='the part format to use for renaming multifiles')
    parser.add_argument('--excludes', '-x', nargs='+', help='directories to exclude from multifile search')
    parser.add_argument('--exts', '-e', nargs='+', help='list of file extensions for multifile search')
    parser.add_argument('--exts-json', '--ej', help='path to json file containing a list of file extensions (at key=\'video_exts\') for multifile search')
    parser.add_argument('--exts-env', '--ee', action='store_true', help='uses hardcoded env var for list of file extensions for multifile search')
    parser.add_argument('--inplace', '--inp', action='store_true', help='toggle renaming operation to inplace replace the part rather than append')
    parser.add_argument('--maxdepth', '--mx', default=1, type=int, help='the recursive directory searches max depth')
    parser.add_argument('--mindepth', '--mn', default=0, type=int, help='the recursive directory searches min depth')
    args = parser.parse_args()
    #### set variables via cmd line args
    dir_in = args.dir_in; dir_out = args.dir_out; part_out = args.part_out
    maxdepth = args.maxdepth; mindepth = args.mindepth
    exts = args.exts; json_exts = args.exts_json; env_exts = args.exts_env; excludes = args.excludes
    #### check and fix variables
    assert(os.path.isdir(dir_in))
    assert(dir_out == None or os.path.isdir(dir_out))
    assert(len([True for x in [exts, env_exts, json_exts] if x != None and x != False]) <= 1)
    if env_exts == True:
        assert('GWSST' in os.environ)
        json_exts = os.path.join(os.environ['GWSST'], 'globals.json')
    if json_exts != None:
        assert(os.path.isfile(json_exts))
        exts = import_json_obj(json_exts, 'video_exts')
    if exts == None:
        exts = '.*'
        inplace = True # TODO: when no file extensions are specified this fixes output
    else:
        exts = '|'.join(['\.' + ext if ext[0] != '.' else ext for ext in exts])

def get_files_regex(directory:str='.', reg:str='.*') -> List[str]:
    """Get files from directory that match the regex pattern reg"""
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return [f for f in files if re.search(reg, f, re.IGNORECASE) != None]

class MultiFile:
    """Allows operation on a contiguous group of similarly named files"""
    prefix_style = r'( - |_|-|| )(0|00|cd|pt|part|| )'
    part_arrs = None
    def __init__(self, num_files:int=0, file_dict=None) -> None:
        self.num_files = num_files
        self.file_dict = file_dict
    def to_list(self, exc_dir:bool=False) -> List[str]:
        """Return this object's files to a list of strings"""
        return [self.get_nth_file(i, exc_dir) for i in range(self.num_files)]
    def get_nth_file(self, n:int, exc_dir:bool=False) -> str:
        """Get this object's n'th file"""
        assert(n <= self.num_files)
        out = ''; out_list = []
        for s in ['base', 'prepart', 'parts', 'postpart', 'ext']:
            out_list += [self.file_dict.get(s, None)]
        out_list[2] = out_list[2][n] # parts array must be indexed
        out = ''.join([str(x) for x in out_list if x is not None])
        if exc_dir != True and self.file_dict['directory'] != None:
            out = os.path.join(self.file_dict['directory'], out)
        return out
    def isfiles(self) -> bool:
        """Ensure this object has at least two valid and contiguous files"""
        files = self.to_list()
        if len(files) <= 1:
            return False
        for f in files:
            if not os.path.isfile(f):
                return False
        else:
            return True
    def mv(self, parts:List[str], dir_out:str=None, inplace:bool=False) -> 'MultiFile':
        """Rename this object's files using the pattern specified by parts"""
        assert(self.isfiles())
        out_dir = dir_out if dir_out != None else self.file_dict['directory']
        out_base = self.file_dict['base']
        out_postpart = self.file_dict['postpart']
        out_ext = self.file_dict['ext']
        while True:
            files_out = []
            if self.num_files > len([p for p in parts if p != None]):
                print("WARNING: too many files (" + str(self.num_files) + ") of form '" + self.get_nth_file(0)  + "' for part-out '" + str(parts[0]) + "', skipping...")
                return self
            for i in range(self.num_files):
                if inplace:
                    tmp = ''.join([str(x) for x in [out_base, parts[i], out_postpart, out_ext] if x is not None])
                else:
                    tmp = ''.join([str(x) for x in [out_base, out_postpart, parts[i], out_ext] if x is not None])
                if out_dir != None:
                    tmp = os.path.join(out_dir, tmp)
                files_out.append(tmp)
            target_exists = False
            for o, n in zip(self.to_list(), files_out):
                if o == n:
                    print("WARNING: target '" + str(n) + "' exists, skipping...")
                    return self
            print('INFO: multi-file ready to be moved, displaying rename cmds')
            for o, n in zip(self.to_list(), files_out):
                print('mv ' + str(o) + ' ' + str(n))
            print('PROMPT: (c)ontinue; (b)ase-rename name; (d)ir-rename name; (e)xt-rename name; (i)nplace; (s)kip; (q)uit; ')
            choice = input()
            if choice == 'continue' or choice == 'c':
                for o, n in zip(self.to_list(), files_out):
                    os.rename(o, n)
                    assert(os.path.isfile(n))
                return MultiFile(len(files_out), {'directory':out_dir, 'base':out_base, 'parts':parts, 'ext':out_ext})
            elif choice == 'inplace' or choice == 'i':
                inplace = not inplace
            elif choice == 'skip' or choice == 's':
                print('INFO: skipping rename of this batch of multifiles')
                break
            elif choice == 'quit' or choice == 'q':
                sys.exit()
            elif choice[:12] == 'base-rename ' or choice[:2] == 'b ':
                out_base = choice.split(' ', 1)[1]
            elif choice[:11] == 'dir-rename ' or choice[:2] == 'd ':
                out_dir = choice.split(' ', 1)[1]
            elif choice[:11] == 'ext-rename ' or choice[:2] == 'e ':
                out_ext = choice.split(' ', 1)[1]
            else:
                print("ERROR: invalid input to prompt")
        return None
    @staticmethod
    def find_multi_files(directory:str, files:List[str]=None) -> List['MultiFile']:
        """Returns a list of MultiFile objects in directory"""
        global times
        #### check and set inputs
        assert(os.path.isdir(directory))
        assert(all([True if os.path.isfile(os.path.join(directory, f)) else False for f in files]))
        #### supports this function recursively calling itself
        if len(files) == 0:
            return []
        #### initializes outputs
        out = None; mfs_out = []
        #### max string length for regex iterating
        max_length = max([len(str(f)) for f in files])
        #### all of the possible combination of parts
        for part_array in MultiFile.get_part_arrs():
            matches_all = []
            for i in range(max_length+1): # TODO: better approach or clever limitations of range for performance
                regex = '^(.{' + str(i) + '})' + '(' + part_array[0] +')(.*)(\..*)$'
                matches = [re.search(regex, f, re.IGNORECASE) for f in files if re.search(regex, f, re.IGNORECASE) != None]
                matches_all.append(matches)
            for matches in matches_all:
                for match in matches:
                    base = match.group(1); prepart = ''; part = match.group(2); postpart = match.group(3); ext = match.group(4)
                    num_files = 0
                    for part in part_array:
                        part_match = ''.join(c for c in part if not c.isdigit()) # TODO: check
                        part = re.sub(part_match, part_match, part, re.IGNORECASE)
                        file_out = base + prepart + part + postpart + ext
                        if not os.path.isfile(os.path.join(directory, file_out)) or file_out not in files:
                            break
                        num_files += 1
                    if num_files > 1:
                        m = re.search(r'^(.*?)' + MultiFile.prefix_style + r'$', base, re.IGNORECASE)
                        base = m.group(1); prepart = m.group(2)
                        mf = MultiFile(num_files, {'directory':directory, 'base':base, 'prepart':prepart, 'parts':[m.group(3) + p for p in part_array], 'postpart':postpart, 'ext':ext})
                        assert(all([True if os.path.isfile(x) else False for x in mf.to_list()]))
                        assert(all([True if x in files else False for x in mf.to_list(exc_dir=True)]))
                        mfs_out.append(mf)
        out = max(mfs_out, default=None, key=lambda mf:mf.num_files)
        if out != None:
            for mf in out.to_list(exc_dir=True):
                files.remove(mf)
            return [out] + MultiFile.find_multi_files(directory=directory, files=files)
        return []
    @staticmethod
    def get_part_arrs() -> List[List[str]]:
        """Get the part arrays for finding contiguous files"""
        if MultiFile.part_arrs == None:
            MultiFile.set_part_arrs()
        return MultiFile.part_arrs
    @staticmethod
    def get_part_arr_out(part_out:str) -> List[str]:
        """Get the part array that will be uses for rename operations"""
        for part_array in MultiFile.get_part_arrs():
            regex = '^' + MultiFile.prefix_style + '(' + part_array[0] +')$'
            result = re.search(regex, part_out)
            if result != None:
                return [result.group(1) + result.group(2) + part for part in part_array if part != None]
        else:
            print("ERROR: --part-out arg of '" + part_out + "' is not recognized")
            sys.exit()
    @staticmethod
    def set_part_arrs(length:int=9999) -> None:
        """Set the part arrays for finding contiguous files"""
        length = max(length, 26); length = min(length, 999999) # TODO: improve handling with larger values
        alpha = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] # namea, nameb, etc.
        nums = [str(i) for i in range(1,length+1)]
        nums_padded = [[n.zfill(i) for n in nums] for i in range(2,len(str(length)))]
        MultiFile.part_arrs = [alpha, nums] + nums_padded
####################################################################################################
####################################################################################################
#### default values
dir_in = None; dir_out = None; part_out = None
excludes = None; exts = None
inplace = None; maxdepth = None; mindepth = None
#### checks and overwrites default values using script input
parse_inputs()
#### recursively find all dirs in dir_in between leveles mindepth and maxdepth
dirs_walk = [d[0] for d in os.walk(dir_in) if os.walk(dir_in) and d[0][len(dir_in):].count(os.sep) <= maxdepth-1 and d[0][len(dir_in):].count(os.sep) >= mindepth-1]
#### removing all excludes from dirs
if excludes != None:
    for exclude in excludes:
        dirs_walk = [d for d in dirs_walk if exclude not in d]
#### rename each multifile
print('INFO: searching for multi-files in ' + str(len(dirs_walk)) + ' directories')
#### search for multifiles in dirs_walk
for mfs in [MultiFile.find_multi_files(d, get_files_regex(d,'^.*(' + exts + ')$')) for d in dirs_walk]:
    for mf in mfs:
        mf.mv(MultiFile.get_part_arr_out(part_out), dir_out, inplace)
