#!/usr/bin/python3
#
# descr: autodetects any multi-file and provides an interactive cli to batch rename the multi-file
#
# usage: python multi-file-rename.py --help
#
#        python multi-file-rename.py -p=-pt1 -n -x .git third-party --mx 6
#
# todos: create --help manpage
#        handle files without extensions better
#        proper cmd args mutual exclusion

import os # filesystem interactions
import sys
import argparse # cmd line arg parsing
import re # regex
import json # json file i/o
####################################################################################################
#################################################################################################### 
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    ## global vars
    global dir_in; global dir_out; global part_out
    global exts; global excludes
    global inplace; global maxdepth; global mindepth
    #### local funcs
    def import_json_obj(f, key):
        """Returns json object associated with key from file"""
        with open(f, 'r') as json_file:
            data = json.load(json_file)
            assert(key in data)
            return data[key]
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir-in', '-i', default='.')
    parser.add_argument('--dir-out', '-o')
    parser.add_argument('--part-out', '-p', default='-pt1')
    parser.add_argument('--exts', '-e', nargs='+')
    parser.add_argument('--exts-json', '-j')
    parser.add_argument('--exts-env', '-n', action='store_true')
    parser.add_argument('--excludes', '-x', nargs='+')
    parser.add_argument('--inplace', '-c', action='store_true')
    parser.add_argument('--maxdepth', '--mx', default=1, type=int)
    parser.add_argument('--mindepth', '--mn', default=0, type=int)
    args = parser.parse_args()
    #### set variables via cmd line args
    dir_in = args.dir_in; dir_out = args.dir_out; part_out = args.part_out
    maxdepth = args.maxdepth; mindepth = args.mindepth
    exts = args.exts; json_exts = args.exts_json; env_exts = args.exts_env; excludes = args.excludes
    #### check and fix variables
    assert(os.path.isdir(dir_in))
    assert(dir_out == None or os.path.isdir(dir_out))
    assert(part_out != None and part_out != '')
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
        exts = '|'.join(['\.' + val if val[0] != '.' else val for val in exts])

class MultiFile:
    part_prefix = '( - |_|-|| )'
    def __init__(self, num_files=0, directory=None, base=None, prepart=None, parts=None, postpart=None, ext=None):
        self.num_files = num_files
        self.directory = directory
        self.base = base
        self.prepart = prepart
        self.parts = parts
        self.postpart = postpart
        self.ext = ext
    def to_list(self, exc_dir=False):
        out = []
        for i in range(0, self.num_files):
            path = ''.join([str(x) for x in [self.base, self.prepart, self.parts[i], self.postpart, self.ext] if x is not None])
            if exc_dir == False and self.directory != None:
                path = os.path.join(self.directory, path)
            out.append(path)
        return out
    def isfiles(self):
        files = self.to_list()
        if len(files) <= 1:
            return False
        for f in files:
            if not os.path.isfile(f):
                return False
        else:
            return True
    def mv(self, parts, dir_out=None, inplace=False):
        out_dir = dir_out if dir_out != None else self.directory
        out_base = self.base
        out_postpart = self.postpart
        out_ext = self.ext
        assert(self.isfiles())
        while True:
            files_out = []
            for i in range(0, self.num_files):
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
            print('NOTE: multi-file ready to be moved, displaying rename cmds')
            for o, n in zip(self.to_list(), files_out):
                print('mv ' + str(o) + ' ' + str(n))
            print('PROMPT: (c)ontinue; (b)ase-rename name; (d)ir-rename name; (e)xt-rename name; (i)nplace; (s)kip; (q)uit; ')
            choice = input()
            if choice == 'continue' or choice == 'c':
                for o, n in zip(self.to_list(), files_out):
                    os.rename(o, n)
                    assert(os.path.isfile(n))
                return MultiFile(len(files_out), directory=out_dir, base=out_base, parts=parts, ext=out_ext)
            elif choice == 'inplace' or choice == 'i':
                inplace = not inplace
            elif choice == 'skip' or choice == 's':
                print('NOTE: skipping rename of this batch of multifiles')
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
    def get_part_arrs():
        part_array_A = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'] # vidnameA, vidnameB, etc.
        part_array_B = [str(val) for val in range(1,27)] # vidname1, vidname2, etc.
        part_array_C = ['0' + val for val in part_array_B] # vidname01, vidname02, etc. 
        part_array_D = ['00' + val for val in part_array_B] # vidname001, vidname002, etc.
        part_array_E = ['cd' + val for val in part_array_B] # vidnamecd1, vidnamecd2, etc.
        part_array_F = ['pt' + val for val in part_array_B] # vidnamept1, vidnamept2, etc.
        part_array_G = ['part' + val for val in part_array_B] # vidnamepart1, vidnamepart2, etc.
        part_array_H = ['p' + val for val in part_array_B] # vidnamep1, vidnamep2, etc.
        ## ordering of return value is necessary to allow prioritization of which part_array to match against
        return [list(a) for a in zip(part_array_A,part_array_E,part_array_F,part_array_G,part_array_H,part_array_D,part_array_C,part_array_B)],[part_array_A,part_array_E,part_array_F,part_array_G,part_array_H,part_array_D,part_array_C,part_array_B]
        # return [part_array_A,part_array_E,part_array_F,part_array_G,part_array_H,part_array_D,part_array_C,part_array_B]
    @staticmethod
    def get_part_arr_out(part):
        part_arrays,part_arrays_inv = MultiFile.get_part_arrs()
        for part_array in part_arrays_inv:
            regex = '^' + MultiFile.part_prefix + '(' + part_array[0] +')$'
            result = re.search(regex, part_out)
            if result != None:
                return [result.group(1) + val for val in part_array]
        else:
            print('ERROR: --part-out arg of \'' + part_out + '\' is not recognized')
            sys.exit()
    @staticmethod
    def multi_files_files_equal(lhs, rhs):
        lhs_list = lhs.to_list()
        rhs_list = rhs.to_list()
        if len(lhs_list) != len(rhs_list):
            return False
        for l, r in zip(lhs_list, rhs_list):
            if l != r:
                return False
        return True
    @staticmethod
    def find_multi_files(directory, files=None, exts=None):
        """Returns a list of MultiFile objects in directory"""
        #### check and set inputs
        assert(os.path.isdir(directory))
        if files == None:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        else:
            assert(all([True if os.path.isfile(os.path.join(directory, f)) else False for f in files]))
        files = [f for f in files if re.search('^.*(' + exts + ')$', f, re.IGNORECASE) != None]
        #### supports this function recursively calling itself
        if len(files) == 0:
            return []
        #### initializes outputs
        out = None; mfs_out = []; list_mfs_out = []
        #### max string length for regex iterating
        max_length = max([len(str(f)) for f in files])
        #### all of the possible combination of parts
        part_arrays,part_arrays_inv = MultiFile.get_part_arrs()
        #### TODO: explain iteration direction
        for i, part_array in enumerate(reversed(part_arrays)):
            for j, pt in enumerate(part_array):
                matches_all = []
                for x in range(max_length):
                    regex = '(.{' + str(x) + '})' + MultiFile.part_prefix + '(' + pt +')(.*)(' + exts + ')$'
                    matches = [re.search(regex, f, re.IGNORECASE) for f in files if re.search(regex, f, re.IGNORECASE) != None]
                    matches_all.append(matches)
                for matched_files in matches_all:
                    for f in matched_files:
                        base = f.group(1); prepart = f.group(2); part = f.group(3); postpart = f.group(4); ext = f.group(5)
                        match = False
                        num_files = 0
                        for x in part_arrays_inv[j][:-i]:
                            num_files += 1
                            part_match = ''.join(c for c in part if not c.isdigit()) # TODO: check
                            x = re.sub(part_match, part_match, x, re.IGNORECASE)
                            file_out = os.path.join(directory, str(base) + str(prepart) + str(x) + str(postpart) + str(ext))
                            if not os.path.isfile(file_out):
                                match = False
                                break
                            else:
                                match = True
                        if match == True and num_files > 1:
                            mf = MultiFile(num_files, directory, base, prepart, part_arrays_inv[j], postpart, ext)
                            assert(all([True for x in mf.to_list() if os.path.isfile(x)]))
                            assert(all([True for x in mf.to_list(exc_dir=True) if x in files]))
                            mfs_out.append(mf)
                    list_mfs_out.append(mfs_out)
                max_mf_size = 0
                for mfs in list_mfs_out:
                    for mf in mfs: 
                        assert(mf.num_files > 1)
                        if mf.num_files > max_mf_size:
                            max_mf_size = mf.num_files
                            out = mf
                if out != None:
                    for mf in out.to_list(exc_dir=True):
                        files.remove(mf)
                    return [out] + MultiFile.find_multi_files(directory=directory, files=files, exts=exts)
        return mfs_out
####################################################################################################
####################################################################################################
#### default values
dir_in = None; dir_out = None; part_out = None
inplace = None; maxdepth = None; mindepth = None 
exts = None; json_exts = None; excludes = None
#### checks and overwrites default values using script input
parse_inputs()
#### recursively find all dirs in dir_in between leveles mindepth and maxdepth
dirs_walk = [val[0] for val in os.walk(dir_in) if os.walk(dir_in) and val[0][len(dir_in):].count(os.sep) <= maxdepth-1 and val[0][len(dir_in):].count(os.sep) >= mindepth-1]
#### removing all excludes from dirs
if excludes != None:
    for exclude in excludes:
        dirs_walk = [val for val in dirs_walk if exclude.lower() not in val.lower()]
#### rename each multifile
for dir_walk in dirs_walk:
    # print('NOTE: searching for multi-files in: ' + str(dir_walk))
    for mf in MultiFile.find_multi_files(dir_walk, exts=exts):
        mf.mv(MultiFile.get_part_arr_out(part_out), dir_out, inplace)