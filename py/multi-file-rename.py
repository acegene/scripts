#!/usr/bin/python3
#
# descr: autodetects any multi-file and provides an interactive cli to batch rename the multi-file
#
# usage: python multi-file-rename.py --help
#
#        python multi-file-rename.py -p=-pt1 -n -x .git third-party --mx 6
#
# warns: beta
#
# todos: create --help manpage
#        handle files without extensions better
#        proper cmd args mutual exclusion
#        handle zero padding

import os # filesystem interactions
import sys
from multiprocessing import Pool, freeze_support, Process, Queue
import time
import argparse # cmd line arg parsing
import re # regex
import json # json file i/o
import time # debugging
####################################################################################################
#################################################################################################### 
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    ## global vars
    global dir_in; global dir_out; global part_out
    global exts; global excludes; global multiprocesses
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
    parser.add_argument('--inplace', '--inp', action='store_true')
    parser.add_argument('--multiprocesses', '-m', default=None, type=int)
    parser.add_argument('--maxdepth', '--mx', default=1, type=int)
    parser.add_argument('--mindepth', '--mn', default=0, type=int)
    args = parser.parse_args()
    #### set variables via cmd line args
    dir_in = args.dir_in; dir_out = args.dir_out; part_out = args.part_out
    maxdepth = args.maxdepth; mindepth = args.mindepth; multiprocesses = args.multiprocesses
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
    def get_nth_file(self, n=0):
        assert(n <= self.num_files)
        return ''.join([str(x) for x in [self.base, self.prepart, self.parts[n], self.postpart, self.ext] if x is not None])
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
            if self.num_files > len([p for p in parts if p != None]):
                print("WARNING: too many files (" + str(self.num_files) + ") of form '" + self.get_nth_file(0)  + "' for part-out '" + str(parts[0]) + "', skipping...")
                return self
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
                return MultiFile(len(files_out), directory=out_dir, base=out_base, parts=parts, ext=out_ext)
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
    def get_part_arrs():
        length_arrays = 99; length_arrays = max(26, length_arrays) # HARDCODED
        nones = [None]*(length_arrays-26) if length_arrays >= 26 else []
        part_array_A = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] + nones # vidnameA, vidnameB, etc.
        part_array_B = [str(val) for val in range(1,length_arrays+1)] # vidname1, vidname2, etc.
        part_array_C = ['0' + val for val in part_array_B] # vidname01, vidname02, etc. 
        part_array_D = ['00' + val for val in part_array_B] # vidname001, vidname002, etc.
        part_array_E = ['cd' + val for val in part_array_B] # vidnamecd1, vidnamecd2, etc.
        part_array_F = ['pt' + val for val in part_array_B] # vidnamept1, vidnamept2, etc.
        part_array_G = ['part' + val for val in part_array_B] # vidnamepart1, vidnamepart2, etc.
        part_array_H = ['p' + val for val in part_array_B] # vidnamep1, vidnamep2, etc.
        ## ordering of return value is necessary to allow prioritization of which part_array to match against
        return [list(a) for a in zip(part_array_A,part_array_E,part_array_F,part_array_G,part_array_H,part_array_D,part_array_C,part_array_B)],[part_array_A,part_array_E,part_array_F,part_array_G,part_array_H,part_array_D,part_array_C,part_array_B]
    @staticmethod
    def get_part_arr_out(part):
        part_arrays,part_arrays_inv = MultiFile.get_part_arrs()
        for part_array in part_arrays_inv:
            regex = '^' + MultiFile.part_prefix + '(' + part_array[0] +')$'
            result = re.search(regex, part_out)
            if result != None:
                return [result.group(1) + val if val != None else None for val in part_array]
        else:
            print("ERROR: --part-out arg of '" + part_out + "' is not recognized")
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
    def find_multi_files(directory, exts=None, files=None):
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
                if pt == None:
                    continue
                matches_all = []
                for x in range(max_length+1):
                    regex = '(.{' + str(x) + '})' + MultiFile.part_prefix + '(' + pt +')(.*)(' + exts + ')$'
                    matches = [re.search(regex, f, re.IGNORECASE) for f in files if re.search(regex, f, re.IGNORECASE) != None]
                    matches_all.append(matches)
                for matches in matches_all:
                    for m in matches:
                        base = m.group(1); prepart = m.group(2); part = m.group(3); postpart = m.group(4); ext = m.group(5)
                        match = False
                        num_files = 0
                        for x in part_arrays_inv[j][:len(part_arrays_inv[j])-i]:
                            num_files += 1
                            part_match = ''.join(c for c in part if not c.isdigit()) # TODO: check
                            x = re.sub(part_match, part_match, x, re.IGNORECASE)
                            file_out = base + prepart + x + postpart + ext
                            if not os.path.isfile(os.path.join(directory, file_out)) or file_out not in files:
                                match = False
                                break
                            else:
                                match = True
                        if match == True and num_files > 1:
                            mf = MultiFile(num_files, directory, base, prepart, part_arrays_inv[j], postpart, ext)
                            assert(all([True if os.path.isfile(x) else False for x in mf.to_list()]))
                            assert(all([True if x in files else False for x in mf.to_list(exc_dir=True)]))
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
    @staticmethod
    def find_multi_files_queue(directory, exts=None, queue=None):
        out = []
        for d in directory:
            out = out + MultiFile.find_multi_files(d, exts)
        queue.put(out)
    @staticmethod
    def find_multi_files_multi(directory, exts=None, files=None):
        # print('MULTIPROCESS')
        out = []
        for d, e in zip(directory, exts):
            out = out + MultiFile.find_multi_files(d, e)
        return out
####################################################################################################
####################################################################################################
if __name__ == '__main__':
    times = []
    times.append((time.time(),'t0')) # 0
    #### default values
    dir_in = None; dir_out = None; part_out = None
    inplace = None; maxdepth = None; mindepth = None; multiprocesses = None
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
    print('INFO: searching for multi-files in ' + str(len(dirs_walk)) + ' directories')
    #### when multiprocesses benefits execution time is still being determined...
    times.append((time.time(),' tinputs')) # 1
    mfs = []
    if multiprocesses == None:
        times.append((time.time(),'tpreproc')) # 2
        for dir_walk in dirs_walk:
            mfs += MultiFile.find_multi_files(dir_walk, exts=exts)
        times.append((time.time(),'   tproc')) # 3
        print('SUCCESS: SINGLEPROCESS')
    else:
        freeze_support() # TODO: research ramifications
        dirs_per_pool = 20 # TODO: find appropriate value, improve grouping to be more sophisticated?
        pool_args = [dirs_walk[d * dirs_per_pool:(d + 1) * dirs_per_pool] for d in range((len(dirs_walk) + dirs_per_pool - 1) // dirs_per_pool )]
        if multiprocesses != 0:
            #### break list into list of lists then convert to list of tuples of lists
            pool_args = [(a, [exts] * len(a)) for a in pool_args]
            times.append((time.time(),'tpreproc')) # 2
            with Pool() as pool:
                data = pool.starmap(MultiFile.find_multi_files_multi, pool_args)
            times.append((time.time(),'   tproc')) # 3
            [mfs := mfs + d for d in data]
            print('SUCCESS: MULTIPOOL')
        else:
            processes = []; queues = []; queues_out = []
            times.append((time.time(),'tpreproc')) # 2
            for dir_walk in pool_args:
                q = Queue()
                queues.append(q)
                p = Process(target=MultiFile.find_multi_files_queue,args=(dir_walk,exts,q))
                p.start()
                processes.append(p)
            [(queues_out.append(queues[i].get())) for i, p in enumerate(processes)]
            times.append((time.time(),'   tproc')) # 3
            [mfs := mfs + q for q in queues_out]
            print('SUCCESS: MULTIPROCESSES')
    for mf in mfs:
        print("[" + str(mf.num_files) + "] " + str(mf.to_list()))
        # mf.mv(MultiFile.get_part_arr_out(part_out), dir_out, inplace)
    times.append((time.time(),'  tfinal')) # 4
    for i, t in enumerate(times):
        if i == 0:
            continue
        print('TIMES: '+ str(times[i][1]) + "=" + str(times[i][0]-times[i-1][0]))
    print('TIMES:    total=' + str(times[len(times)-1][0]-times[0][0]))