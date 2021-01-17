#!/usr/bin/python3
#
# title: multifile-rename.py
#
# descr: searches for multifiles via interactive cli to enable batch file renaming
#
#      * a multifile is a group of files from a series e.g. file-ep-1-1080p.mp4 file-ep-2-1080p.mp4 file-ep-3-1080p.mp4
#      * given file=file-ep-1-1080p.mp4; base=file part=-ep-1 postpart=-1080p ext=.mp4
#      * user can specify outputs (base, part, ext) at runtime via interactive cli
#      * if inplace==False (default) then out_format = base + part + postpart + ext else out_format = base + postpart + part + ext
#
# usage: python multifile-rename.py --help
#
#        python multifile-rename.py --po=-pt_1 -x .git third-party
#
# warns: race condition when another process moves files currently being batch renamed, process is aborted with
#
# notes: version 0.8
#        tested on 'Windows 10 2004' # TODO: testing with OSX and linux
#
# todos: handle files without extensions
#        proper cmd args mutual exclusion
#        allow sequences that dont start with 1 or a to be found and specified as the output
#        performance with high quantities of files

import argparse # cmd line arg parsing
import copy # deepcopy()
import json # json file i/o
import os # filesystem interactions
import re # regex
import sys # exit()

from typing import List # declaration of parameter and return types
####################################################################################################
#################################################################################################### 
def except_if_not(exception:Exception, expression:bool, string_if_except:str=None) -> None:
    """Throw exception if expression is False"""
    if not expression:
        if string_if_except != None:
            print(string_if_except)
        raise exception

def parse_inputs() -> None:
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    #### local funcs
    def import_json_obj(f:str, key:str) -> List[str]:
        """Returns json object associated with key from file"""
        with open(f, 'r') as json_file:
            data = json.load(json_file)
            except_if_not(ValueError, key in data)
            return data[key]
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir-in', '-i', default='.', help='dir to search for multifiles')
    parser.add_argument('--dir-out', '-o', help='dir to move renamed multifiles into')
    parser.add_argument('--part-out', '--po', default='-pt1', help='the part format to use for renaming multifiles')
    parser.add_argument('--excludes', '-x', default=[], nargs='+', help='dir to exclude from multifile search')
    parser.add_argument('--exts', '-e', nargs='+', help='list of file exts for multifile search')
    parser.add_argument('--exts-json', '--ej', help='path to json file containing a list of file exts (at key=\'video_exts\') for multifile search')
    parser.add_argument('--exts-env', '--ee', action='store_true', help='uses hardcoded env var for list of file exts for multifile search')
    parser.add_argument('--regex', '-r', help='regex to use to prefilter files for multifile search')
    parser.add_argument('--inplace', '--inp', action='store_true', default=False, help='toggle renaming operation to inplace replace the part rather than append')
    parser.add_argument('--maxdepth', '--mx', default=10, type=int, help='the recursive dir searches max depth')
    parser.add_argument('--mindepth', '--mn', default=1, type=int, help='the recursive dir searches min depth')
    args = parser.parse_args()
    #### return dict assigned from attributes of argumentparser object
    out = {attr:val for attr, val in args.__dict__.items()}
    #### raise exceptions
    except_if_not(ValueError, os.path.isdir(out['dir_in']))
    except_if_not(ValueError, out['dir_out'] == None or os.path.isdir(out['dir_out']))
    except_if_not(ValueError, len([True for x in [out['regex'], out['exts'], out['exts_env'], out['exts_json']] if x != None and x != False]) <= 1)
    except_if_not(ValueError, out['maxdepth'] >= out['mindepth'] and out['mindepth'] > 0)
    #### when regex is None then its set using exts related args
    if out['regex'] == None:
        if out['exts_env'] == True:
            assert 'GWSST' in os.environ 
            out['exts_json'] = os.path.join(os.environ['GWSST'], 'globals.json')
        if out['exts_json'] != None:
            assert os.path.isfile(out['exts_json'])
            out['exts'] = import_json_obj(out['exts_json'], 'video_exts')
        if out['exts'] == None:
            out['exts'] = ['mp4', 'm4p', 'mkv', 'mpeg', 'mpg', 'avi', 'wmv', 'mov', 'qt', 'iso', 'm4v', 'flv']
        out['exts'] = '|'.join(['\.' + ext if ext[0] != '.' else ext for ext in out['exts']])
        out['regex'] = '^.*(' + out['exts'] + ')$'
    #### get user specified part formatting for renaming multifiles
    out['parts_out'] = Multifile.get_part_arr_out(out['part_out'])
    except_if_not(ValueError, out['parts_out'] != None, "ERROR: part_out arg of '" + str(out['part_out']) + "' is unrecognized")
    #### remove entries from returned dict that are unused by the surrounding scope
    [out.pop(k, None) for k in ['exts_env', 'exts_json', 'exts', 'part_out']]
    #### return dictionary of modified cmd args
    return out

def listdir_dirs_recursive(dir_in:str='', mindepth:int=1, maxdepth:int=1, excludes:List[str]=[]) -> List[str]:
    """Get dirs from directory within the recrusive depths mindepth-maxdepth and remove excludes"""
    #### recursively find all dirs in dir_in between levels mindepth and maxdepth with excludes removed
    dirs_walk = [d[0] for d in os.walk(dir_in) if os.walk(dir_in) and d[0][len(dir_in):].count(os.sep) <= maxdepth-1 and d[0][len(dir_in):].count(os.sep) >= mindepth-1]
    #### remove all excludes from dirs_walk
    return [d for d in dirs_walk if all([False for e in excludes if e in d])]

def list_regex_filtered_files(directory:str='.', reg:str='.*') -> List[str]:
    """Get files from directory that match the regex pattern reg"""
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return [f for f in files if re.search(reg, f, re.IGNORECASE) != None]

class Multifile:
    """Allows operation on a contiguous group of similarly named files"""
    prefix_style = r'( - |_|-|| )(cd|ep|episode|pt|part|| )( - |_|-|| )'
    part_arrs = None
    def __init__(self, num_files:int=0, file_dict=None) -> None:
        assert all(True if k in ['dir', 'base', 'parts', 'postpart', 'ext'] else False for k in file_dict.keys())
        self.num_files = num_files
        self.file_dict = file_dict
    def to_list(self, exc_dir:bool=False, inplace:bool=True) -> List[str]:
        """Return this object's files to a list of strings"""
        return [self.get_nth_file(i, exc_dir, inplace) for i in range(self.num_files)]
    def get_nth_file(self, n:int, exc_dir:bool=False, inplace:bool=True) -> str:
        """Get this object's n'th file"""
        assert n <= self.num_files
        out = ''; out_list = []
        for s in ['base', 'parts', 'postpart', 'ext']:
            out_list += [self.file_dict.get(s, None)]
        except_if_not(AssertionError, n < len(out_list[1]), "ERROR: debug... " + str(out_list[1]) + '#' + str(n) + '#' + str(self.file_dict))
        out_list[1] = out_list[1][n] # parts array must be indexed
        if inplace == False:
            out_list[0] = ''.join([x for x in [out_list[0], out_list[2]] if x != None])
            out_list[2] = None
        out = ''.join([str(x) for x in out_list if x is not None])
        if exc_dir == False and self.file_dict['dir'] != None:
            out = os.path.join(self.file_dict['dir'], out)
        return out
    def ismultifile(self) -> bool:
        """Ensure this object has at least two valid and contiguous files"""
        return all([os.path.isfile(f) for f in self.to_list()]) and self.num_files > 1
    def nofiles(self) -> bool:
        """Ensure this object has no valid files"""
        return all([not os.path.isfile(f) for f in self.to_list()])
    def mv(self, parts:List[str], dir_out:str=None, inplace:bool=False) -> 'Multifile':
        """Rename this object's files using the pattern specified by parts"""
        #### check if a mv operation is possible
        assert self.ismultifile()
        if self.num_files > len([p for p in parts if p != None]):
            print("WARNING: too many files (" + str(self.num_files) + ") of form '" + self.get_nth_file(0)  + "' for part-out '" + str(parts[0]) + "', skipping...")
            return None
        #### set output multifile dict
        out_dict = copy.deepcopy(self.file_dict)
        out_dict['dir'] = dir_out if dir_out != None else out_dict['dir']
        out_dict['parts'] = parts
        while True:
            #### create mf object based on out_dict which is manipulated by user input
            out_mf = Multifile(self.num_files, out_dict)
            #### check if mv operations are valid, if not then abort
            print('INFO: printing potential rename cmds to be executed...')
            for i, (old, new) in enumerate(zip(self.to_list(), out_mf.to_list(inplace=inplace))):
                if old == new:
                    print("WARNING: target '" + str(new) + "' exists")
                    break
                if self.num_files < 10:
                    print('  mv ' + str(old) + ' ' + str(new))
                else:
                    if i in [0, 1, self.num_files-2, self.num_files-1]:
                        print('  mv ' + str(old) + ' ' + str(new))
                    if i == 2:
                        print('  ... ' + str(self.num_files) + ' files total')
            if out_mf.nofiles == False:
                print('WARNING: target multifile has existing files')
                return None
            print('PROMPT: (c)ontinue; (d)ir str; (b)ase str; (p)art str; (e)xt str; (i)nplace; (s)kip; (q)uit')
            choice = input()
            if choice == 'continue' or choice == 'c':
                for old, new in zip(self.to_list(), out_mf.to_list(inplace=inplace)):
                    if old == new:
                        print("ERROR: target '" + str(new) + "' exists, aborting...")
                        continue
                for old, new in zip(self.to_list(), out_mf.to_list(inplace=inplace)):
                    assert old != new, "ERROR: target '%s' exists already" % old
                    os.rename(old, new)
                    assert not os.path.isfile(old), "ERROR: old file '%s' not removed" % old
                    assert os.path.isfile(new), "ERROR: target '%s' not created" % old
                print('INFO: SUCCESS with multifile rename of ' + str(out_mf.num_files) + ' files')
                return out_mf
            elif choice == 'inplace' or choice == 'i':
                inplace = not inplace
            elif choice == 'skip' or choice == 's':
                print('INFO: skipping rename of this batch of multifiles')
                break
            elif choice == 'quit' or choice == 'q':
                sys.exit()
            elif choice[:4] == 'dir ' or choice[:2] == 'd ':
                tmp = choice.split(' ', 1)[1]
                if not os.path.isdir(tmp):
                    print('ERROR: the following is not a dir: ' + str(tmp))
                else:
                    out_dict['dir'] = tmp
            elif choice[:5] == 'base ' or choice[:2] == 'b ':
                out_dict['base'] = choice.split(' ', 1)[1]
                if not inplace:
                    out_dict['postpart'] = None
            elif choice[:5] == 'part ' or choice[:2] == 'p ':
                tmp = Multifile.get_part_arr_out(choice.split(' ', 1)[1])
                out_dict['parts'] = tmp if tmp != None else out_dict['parts']
            elif choice[:4] == 'ext ' or choice[:2] == 'e ':
                out_dict['ext'] = choice.split(' ', 1)[1]
            else:
                print("ERROR: invalid input for prompt")
        return None
    @staticmethod
    def find_multifiles(directory:str, files:List[str]) -> List['Multifile']:
        """Returns a list of Multifile objects in directory"""
        #### check and set inputs
        assert os.path.isdir(directory)
        assert all([True if os.path.isfile(os.path.join(directory, f)) else False for f in files])
        #### supports this function recursively calling itself
        if len(files) == 0:
            return []
        #### initializes outputs
        out = None; mfs_out = []
        #### max string length for regex iterating
        max_length = max([len(str(f)) for f in files])
        #### all of the possible combination of parts
        for part_array in Multifile.get_part_arrs():
            matches_all = []
            for i in range(max_length+1): # TODO: better approach or clever limitations of range for performance
                regex = '^(.{' + str(i) + '})' + '(' + part_array[0] +')(.*)(\..*)$'
                matches_all.append([re.search(regex, f, re.IGNORECASE) for f in files if re.search(regex, f, re.IGNORECASE) != None])
            for matches in matches_all:
                for match in matches:
                    base = match.group(1); part = match.group(2); postpart = match.group(3); ext = match.group(4)
                    num_files = 0
                    for part in part_array:
                        part_match = ''.join(c for c in part if not c.isdigit()) # TODO: check
                        part = re.sub(part_match, part_match, part, re.IGNORECASE)
                        file_out = base + part + postpart + ext
                        if not os.path.isfile(os.path.join(directory, file_out)) or file_out not in files:
                            break
                        num_files += 1
                    if num_files > 1:
                        m = re.search(r'^(.*?)' + Multifile.prefix_style + r'$', base, re.IGNORECASE)
                        base = m.group(1)
                        mf = Multifile(num_files, {'dir':directory, 'base':base, 'parts':[m.group(2) + m.group(3) + m.group(4) + p for p in part_array], 'postpart':postpart, 'ext':ext})
                        assert all([True if os.path.isfile(x) else False for x in mf.to_list()])
                        assert all([True if x in files else False for x in mf.to_list(exc_dir=True)])
                        mfs_out.append(mf)
        out = max(mfs_out, default=None, key=lambda mf:mf.num_files)
        if out != None:
            [files.remove(mf) for mf in out.to_list(exc_dir=True)]
            return [out] + Multifile.find_multifiles(directory=directory, files=files)
        return []
    @staticmethod
    def get_part_arrs() -> List[List[str]]:
        """Get the part arrays for finding contiguous files"""
        if Multifile.part_arrs == None:
            Multifile.set_part_arrs()
        return Multifile.part_arrs
    @staticmethod
    def get_part_arr_out(part_out:str) -> List[str]:
        """Get the part array that will be uses for rename operations"""
        for part_array in Multifile.get_part_arrs():
            regex = '^' + Multifile.prefix_style + '(' + part_array[0] +')$'
            result = re.search(regex, part_out)
            if result != None:
                return [result.group(1) + result.group(2) + result.group(3) + part for part in part_array if part != None]
        else:
            print("WARNING: could not find parts array for input '" + part_out + "'")
            return None
    @staticmethod
    def set_part_arrs(length:int=9999) -> None:
        """Set the static variable part_arrs"""
        length = max(length, 26); length = min(length, 999999) # TODO: improve handling with larger values
        alpha = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] # namea, nameb, etc.
        nums = [str(i) for i in range(1,length+1)] # name1, name2, etc.
        #### array of arrays with length and zero padding incrementing based on the number of digits of length
        nums_padded = [[n.zfill(i) for j, n in enumerate(nums) if j < 10**i-1] for i in reversed(range(2,len(str(length))))] # name01, name02, etc.
        #### set static variable part_arrs
        Multifile.part_arrs = [alpha, nums] + nums_padded
####################################################################################################
####################################################################################################
def main() -> None:
    #### parses script input to populate args dict
    args = parse_inputs()
    #### recursively find all dirs in dir_in between levels mindepth and maxdepth with excludes removed
    dirs_walk = listdir_dirs_recursive(args['dir_in'], args['mindepth'], args['maxdepth'], args['excludes'])
    #### print useful info
    print('INFO: root dir to search for multifiles: ' + args['dir_in'])
    if len(dirs_walk) > 1:
        print('INFO: searching recursively ' + str(args['mindepth']) + '-' + str(args['maxdepth']) + ' dirs deep... found ' + str(len(dirs_walk)) + ' dirs')
    print("INFO: regex file filter: '" + str(args['regex']) + "'")
    #### search for multifiles in dirs_walk
    mfs_list = [Multifile.find_multifiles(d, list_regex_filtered_files(d, args['regex'])) for d in dirs_walk]
    print('INFO: found ' + str(sum(len(row) for row in mfs_list)) + ' multifile candidates')
    #### rename each multifile
    [mf.mv(args['parts_out'], args['dir_out'], args['inplace']) for mfs in mfs_list for mf in mfs]
    print('INFO: SUCCESS')

if __name__ == "__main__":
    main()