#!/usr/bin/python3
#
# title: multifile-mv.py
#
# descr: searches for multifiles/mfs and then provides interactive cli for renaming/moving/mv'ing located mfs
#
#      * mf is a group of incrementing files such as mf=[file1.mp4, file2.mp4, file3.mp4]
#
#      * params can be specified at launch via cmdargs and during runtime via interactive cli
#            * cmdargs params can be understood with parse_inputs() below or using the --help cmdargs option
#            * cli is only for the mf mv process and includes params=[dir_out, base, part, ext, range_mv, inplace]
#
#      * given mf=[f-ep-1-720p.mp4,f-ep-2-720p.mp4]; then base=f, prepart=-ep-, part=1, postpart=-720p, ext=.mp4, range=1-3
#
#      * mfs search by default locates mfs with its first file's part in ['a','0','1'] e.g. mf = [f_a,f_b,f_c]
#            * '--range-search 3-4' via cmdargs can locate mf=[f3,f4,f5] or mf=[f4,f5]; note: does not limit length of mf
#
#      * mfs mv default format is base + postpart + part + ext unless inplace=True then format is base + part + postpart + ext
#            * partial mv: '--range-mv 2-3' via cmdargs or 'range_mv 2-3' via cli to allow mf=[f1,f2,f3] to mv only [f2,f3]
#
#      * mf mv is not atomic, but each individual file mv is atomic; see: https://en.wikipedia.org/wiki/Atomicity_(database_systems)
#
# usage: python multifile-mv.py --help
#            * provides help info on scripts cmd line args
#        python multifile-mv.py
#            * uses default params to locate mfs and launch cli
#
# warns: race condition when another process moves files currently being batch mv'd, process is aborted with
#
# notes: version 0.9
#        tested on 'Windows 10 2004' # TODO: testing with OSX and linux
#
# todos: handle files without extensions
#        proper cmd args mutual exclusion
#        performance with high quantities of files
#        allow two mvs for same mf if done partially
#        file input for cmdargs

import argparse
import errno
import itertools
import json
import os
import re
import shutil
import sys
import uuid

from typing import List # declaration of parameter and return types

if sys.version_info < (3,6): # version 3.6.X or newer allows f strings
    raise Exception("ERROR: python version needs to be 3.6.X or newer, instead is: " + '.'.join([str(m) for m in sys.version_info[:3]]))
################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################
# yymmdd: 210101
# generation cmd on the following line:
# python "${GWSPY}/write-btw.py" "-t" "py" "-w" "${GWSPY}/multifile-mv.py" "-x" "mv_atomic" "except_if_not" "parse_range"

def except_if_not(exception:Exception, expression:bool, string_if_except:str=None) -> None:
    """Throw exception if expression is False"""
    if not expression:
        if string_if_except != None:
            print(string_if_except)
        raise exception

def mv_atomic(src:str, dst:str) -> None:
    """Atomically move <src> to <dst> even across filesystems"""
    #### <dst> should be the target name and not the target parent dir
    try:
        os.rename(src, dst)
    except OSError as err:
        if err.errno == errno.EXDEV:
            #### generate unique ID
            copy_id = uuid.uuid4()
            #### cp <src> <tmp_dst> # cp across filesystems to tmp location
            tmp_dst = "%s.%s.tmp" % (dst, copy_id)
            shutil.copyfile(src, tmp_dst)
            #### mv <tmp_dst> <src> # atomic mv
            os.rename(tmp_dst, dst)
            #### rm <src>
            os.unlink(src)
        else:
            raise

def parse_range(range_str:str, throw=True) -> List[int]:
    #### local funcs
    def new_list_elems_removed(elems, lst): return list(filter(lambda x: x not in elems, lst))
    #### set and use error type for param errors
    error = None
    error = TypeError if not error and not isinstance(range_str, str) else error
    error = ValueError if not error and range_str == '' else error
    error = ValueError if not error and not all([c.isdigit() for c in new_list_elems_removed(['-', ','], range_str)]) else error
    error = ValueError if not error and not all([c.isdigit() for c in [range_str[0], range_str[-1]]]) else error
    if error:
        print('ERROR: expect str with only positive ints, commas and hyphens, given ' + range_str)
        if throw:
            raise error
        return None
    result = []
    for section in range_str.split(','):
        x = section.split('-')
        result += [i for i in range(int(x[0]), int(x[-1]) + 1)]
    return sorted(result)
################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################
def alpha_from_int(x:int) -> str:
    return chr(x+96)

def int_from_alpha(string:str) -> int:
    if len(string) != 1:
        return 0
    new = ord(string)
    if 65 <= new <= 90: # uppercase
        return new - 64
    elif 97 <= new <= 122: # lowercase
        return new - 96
    return 0 # unrecognized

def parse_range_alpha(range_str:str, throw=True) -> List[int]:
    #### local funcs
    def newListRemove(element, lst): return list(filter(lambda x: x != element, lst))
    error = None
    error = TypeError if not error and not isinstance(range_str, str) else error
    error = ValueError if not error and range_str == '' else error
    mid = all(x.isdigit() for x in newListRemove('-', newListRemove(',', range_str)))
    if error:
        print(f"ERROR: expect str with only positive ints, commas and hyphens, given '{range_str}'")
        if throw:
            raise error
        return None
    if range_str[0].isalpha():
        range_str = ''.join([str(int_from_alpha(c)) if c.isalpha() else c for c in range_str])
        return list(map(alpha_from_int, parse_range(range_str, throw)))
    else:
        return parse_range(range_str, throw)

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
    parser.add_argument('--dir-out', '-o', help='dir to mv multifiles into')
    parser.add_argument('--part-out', '-p', default='-1', help='first part of multifile mv i.e. pt-1')
    parser.add_argument('--excludes', '-x', default=[], nargs='+', help='dirs to exclude from multifile search')
    parser.add_argument('--exts', '-e', nargs='+', help='file exts filter for multifile search')
    parser.add_argument('--exts-json', '--ej', help='path to json file containing a list of file exts (at key=\'video_exts\') for multifile search')
    parser.add_argument('--exts-env', '--ee', action='store_true', help='use hardcoded env var for list of file exts for multifile search')
    parser.add_argument('--regex', '-r', help='regex for prefiltering files for multifile search')
    parser.add_argument('--inplace', '--inp', action='store_true', default=False, help='toggle mv inplace mode')
    parser.add_argument('--maxdepth', '--mx', default=10, type=int, help='the recursive dir search max depth')
    parser.add_argument('--mindepth', '--mn', default=1, type=int, help='the recursive dir search min depth')
    parser.add_argument('--range-search', '--rs', default=[0,1], type=parse_range_alpha, help='range, inclusive, for multifile search to consider as a first files part i.e. 0-1')
    parser.add_argument('--range-mv', '--rm', default=None, type=parse_range_alpha, help='indices range, inclusive, for multifile mv i.e. 0-4') 
    args = parser.parse_args()
    #### return dict assigned from attributes of argumentparser object
    out = {attr:val for attr, val in args.__dict__.items()}
    #### raise exceptions
    except_if_not(ValueError, os.path.isdir(out['dir_in']))
    except_if_not(ValueError, out['dir_out'] == None or os.path.isdir(out['dir_out']))
    except_if_not(ValueError, len([True for x in [out['regex'], out['exts'], out['exts_env'], out['exts_json']] if x != None and x != False]) <= 1)
    except_if_not(ValueError, out['maxdepth'] >= out['mindepth'] and out['mindepth'] > 0)
    #### convert range search range from alpha to int if given an alpha range
    out['range_search'] = [int_from_alpha(x) if isinstance(x, str) else x for x in out['range_search']]
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

def listdir_dirs(dir_in:str='', mindepth:int=1, maxdepth:int=1, excludes:List[str]=[]) -> List[str]:
    """Get dirs from directory within the recursive depths mindepth-maxdepth and remove excludes"""
    #### recursively find all dirs in dir_in between levels mindepth and maxdepth with excludes removed
    dirs_walk = [d[0] for d in os.walk(dir_in) if os.walk(dir_in) and d[0][len(dir_in):].count(os.sep) <= maxdepth-1 and d[0][len(dir_in):].count(os.sep) >= mindepth-1]
    #### remove all excludes from dirs_walk
    return [d for d in dirs_walk if all([False for e in excludes if e in d])]

def listdir_files(dir_in:str='.', regex:str='.*') -> List[str]:
    """Get files from dir_in that match the regex pattern reg"""
    files = [f for f in os.listdir(dir_in) if os.path.isfile(os.path.join(dir_in, f))]
    return [f for f in files if re.search(regex, f, re.IGNORECASE) != None]

class Multifile:
    """Allows operation on a contiguous group of similarly named files"""
    prefix_style = r'( - |_|-|| )(cd|ep|episode|pt|part|| )( - |_|-|| )'
    part_arrs = None
    def __init__(self, file_dict=None) -> None:
        assert all(True if k in ['dir', 'base', 'prepart', 'parts', 'postpart', 'ext'] else False for k in file_dict.keys())
        self.file_dict = file_dict
    def __getitem__(self, key):
        return self.file_dict[key] if isinstance(key, str) else self.get_nth_file(key)
    #### method to extract filenames from multifile
    def get_nth_file(self, n:int, exc_dir:bool=False, inplace:bool=True) -> str:
        """Get this multifiles n'th file"""
        assert n < self.size(), f"ERROR: DEBUG: {str(n)}:{str(self.file_dict)}"
        out = []
        if not inplace:
            out += [self['base'], self['postpart'], self['prepart'], self['parts'][n], self['ext']]
        else:
            out += [self['base'], self['prepart'], self['parts'][n], self['postpart'], self['ext']]
        if not exc_dir:
            out[0] = os.path.join(self['dir'], out[0])
        return ''.join([str(x) for x in out if x is not None])
    def to_list(self, exc_dir:bool=False, inplace:bool=True) -> List[str]:
        """Return this object's files to a list of strings"""
        return [self.get_nth_file(i, exc_dir, inplace) for i in range(self.size())]
    #### method to test the current state of the multifile
    def isalpha(self) -> bool:
        return self['parts'][0][-1].isalpha()
    def ismultifile(self) -> bool:
        """Ensure this object has at least two valid and contiguous files"""
        return all([os.path.isfile(f) for f in self.to_list()]) and self.size() > 1 
    def size(self) -> int:
        return len(self['parts'])
    #### method that manipulate the state of the multifile or its referenced contents
    def mv(self, parts:List[str], dir_out:str=None, range_mv:List[int]=None, inplace:bool=False) -> 'Multifile':
        """Move this object's files using the pattern specified by parts"""
        #### check if a mv operation is possible
        assert self.ismultifile()
        #### set output multifile dict
        out_dict = {k:v for k, v in self.file_dict.items()}
        out_dict['dir'] = dir_out if dir_out != None else self['dir']
        out_dict['prepart'] = None
        if range_mv == None:
            if len(parts) < self.size():
                print(f"ERROR: selected parts_out not big enough for multifile, choose new part or range\nERROR: partlist: {parts}\nERROR: multifile: {out_dict['parts']}")
            out_dict['parts'] = parts[:self.size()]
        else:
            if str(parts[0][-1]).isalpha() != str(range_mv[0]).isalpha():
                print('ERROR: range and parts input must both be alpha characters or both be ints')
            out_dict['parts'] = parts[:len(range_mv)]
        #### describe the state of the potential mv
        print('INFO: printing potential mv cmds to be executed...')
        while True:
            #### check if mv operations are valid, if not then abort
            if range_mv == None:
                reduced_list = self.to_list()
            else:
                reduced_list = [self.to_list()[i] for i, p in enumerate(self['parts']) if p.lower() in [str(r) for r in range_mv]] # TODO: check all range is applicable
                assert len(reduced_list) == len(range_mv), f"ERROR: portion of range unaccounted for '{len(reduced_list)}' != '{len(range_mv)}'" # TODO:
                if len(reduced_list) != self.size():
                    print(f"INFO: partial mv being proposed for {len(reduced_list)} out of {self.size()} files revert to full mv with input 'r all'")
                    print(f"INFO: indices of partial mv (range): {range_mv}")
            out_dict['parts'] = out_dict['parts'][:len(reduced_list)]
            #### create mf object based on out_dict which is manipulated by user input
            out_mf = Multifile(out_dict)
            out_list = out_mf.to_list(inplace=inplace)
            length = len(reduced_list)
            out_length = len(out_list)
            if length != out_length:
                print(f"ERROR: multifile length mismatch for lhs ({length}) and rhs ({out_length})")
            for i, (old, new) in enumerate(itertools.zip_longest(reduced_list, out_list, fillvalue='NO_EQUIVALENT_VALUE')):
                if old == new:
                    print(f"WARNING: target '{new}' exists")
                    break
                if max(length, out_length) < 10:
                    print(f"  mv {old} {new}")
                else:
                    if i in [0, 1, 2, max(length, out_length)-3, max(length, out_length)-2, max(length, out_length)-1]:
                        print(f"  mv {old} {new}")
                    if i == 3:
                        print(f"  ... {max(length, out_length)} files total")
            print('PROMPT: (c)ontinue; (d)ir str; (b)ase str; (p)art str; (e)xt str; (r)ange_mv str; (i)nplace; (s)kip; (q)uit')
            choice = input()
            if choice == 'continue' or choice == 'c':
                if length != out_length:
                    continue
                if not all([True if old not in out_list else False for old in reduced_list]):
                    if not all([old != new for old, new in zip(reduced_list, out_list)]):
                        print(f"ERROR: src and target have overlap of some/all files:\nERROR: src: {reduced_list}\nERROR: targ: {out_list}")
                        continue
                    # TODO: hack to reverse lists to avoid mf overwriting itself during mv
                    old_char = self['parts'][0][-1]
                    new_char = out_mf['parts'][0][-1]
                    if old_char.isdigit():
                        if int(old_char) < int(new_char):
                            reduced_list.reverse()
                            out_list.reverse()
                    else:
                        if old_char < new_char:
                            reduced_list.reverse()
                            out_list.reverse()
                for old, new in zip(reduced_list, out_list):
                    # TODO: check all the files not in old do not exist
                    assert old != new, f"ERROR: mv '{old}' '{new}'"
                    assert os.path.isfile(old), f"ERROR: mv '{old}' '{new}'"
                    assert not os.path.isfile(new), f"ERROR: mv '{old}' '{new}'"
                    mv_atomic(old, new)
                    assert not os.path.isfile(old), f"ERROR: mv '{old}' '{new}'"
                    assert os.path.isfile(new), f"ERROR: mv '{old}' '{new}'"
                return out_mf
            elif choice[:9] == 'range_mv ' or choice[:2] == 'r ':
                tmp = choice.split(' ', 1)[1]
                if tmp == 'all':
                    range_mv = None
                    out_dict['parts'] = Multifile.get_part_arr_out(out_dict['parts'][0])
                else:
                    tmp_parsed = parse_range(tmp, throw=False)
                    if tmp_parsed:
                        if str(tmp_parsed[0]).isalpha() != self.isalpha():
                            print('ERROR: range and multifile must both be alpha characters or both be ints')
                        else:
                            range_mv = tmp_parsed
                            out_dict['parts'] = Multifile.get_part_arr_out(out_dict['parts'][0])
            elif choice == 'inplace' or choice == 'i':
                inplace = not inplace
            elif choice == 'skip' or choice == 's':
                print('INFO: skipping mv of this batch of multifiles')
                break
            elif choice == 'quit' or choice == 'q':
                sys.exit()
            elif choice[:4] == 'dir ' or choice[:2] == 'd ':
                tmp = choice.split(' ', 1)[1]
                if not os.path.isdir(tmp):
                    print(f"ERROR: the following is not a dir: {tmp}")
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
            print("#######################################################")
        return None
    #### class methods
    @classmethod
    def extract_multifiles(cls, dir_in:str, files:List[str], min_in:int=0, max_in:int=1) -> List['Multifile']:
        """Returns a list of Multifile objects in dir_in"""
        #### check and set inputs
        assert os.path.isdir(dir_in)
        assert all([True if os.path.isfile(os.path.join(dir_in, f)) else False for f in files])
        assert min_in <= max_in
        #### supports this method recursively calling itself
        if len(files) == 0:
            return []
        #### initializes outputs
        out = None; mfs_out = []
        #### max string length for regex iterating
        max_length = max([len(str(f)) for f in files])
        #### all of the possible combination of parts
        file_part_indices_list = []
        for part_array in Multifile.get_part_arrs():
            matches = []
            #### find potential first file matches for every file for each part in part_array
            for i, part in enumerate(part_array[min_in:max_in+1]):
                if part == None:
                    continue
                file_part_indices_list.append([(f, i + min_in, re.finditer(part, f)) for f in files])
            #### generate regex match list for capture groups
            for file_part_indices in file_part_indices_list:
                for (f, part_index, indices) in file_part_indices:
                    for i in indices:
                        regex = '^(.{' + str(i.start()) + '})' + '(' + part_array[part_index] +')(.*)(\..*)$'
                        match = re.search(regex, f, re.IGNORECASE)
                        if match:
                            matches.append((part_index, match))
            for (part_index, match) in matches:
                base = match.group(1); part = match.group(2); postpart = match.group(3); ext = match.group(4)
                num_files = 0
                for i, part in enumerate(part_array[part_index:]):
                    if part == None:
                        continue
                    part_match = ''.join(c for c in part if not c.isdigit()) # TODO: check
                    part = re.sub(part_match, part_match, part, re.IGNORECASE)
                    file_out = base + part + postpart + ext
                    if not os.path.isfile(os.path.join(dir_in, file_out)) or file_out not in files:
                        if i + part_index == 0 and part != 'a': # TODO:
                            continue
                        break
                    num_files += 1
                if num_files > 1:
                    m = re.search(r'^(.*?)' + Multifile.prefix_style + r'$', base, re.IGNORECASE)
                    base = m.group(1)
                    mf = Multifile({'dir':dir_in, 'base':base, 'prepart':m.group(2) + m.group(3) + m.group(4), 'parts':part_array[part_index:part_index+num_files], 'postpart':postpart, 'ext':ext})
                    assert all([True if os.path.isfile(x) else False for x in mf.to_list()]), f"ERROR: {mf.to_list()}"
                    assert all([True if x in files else False for x in mf.to_list(exc_dir=True)]), f"ERROR: {mf.to_list(exc_dir=True)}"
                    mfs_out.append(mf)
        out = max(mfs_out, default=None, key=lambda mf:mf.size())
        if out != None:
            [files.remove(mf) for mf in out.to_list(exc_dir=True)]
            return [out] + Multifile.extract_multifiles(dir_in=dir_in, files=files, min_in=min_in, max_in=max_in)
        return []
    @classmethod
    def get_part_arr_out(cls, part_out:str) -> List[str]:
        """Get the part array that will be uses for mv operations"""
        num = re.sub("[^0-9]", "", part_out)
        num = int(num) if num != '' else int_from_alpha(part_out[-1])
        for part_array in cls.get_part_arrs():
            if part_array[num] == None:
                continue
            regex = '^' + cls.prefix_style + '(' + part_array[num] +')$'
            result = re.search(regex, part_out)
            if result != None:
                return [result.group(1) + result.group(2) + result.group(3) + part for part in part_array[num:] if part != None]
        else:
            print(f"WARNING: could not find parts array for input '{part_out}'")
            return None
    @classmethod
    def get_part_arrs(cls) -> List[List[str]]:
        """Get the part arrays for finding contiguous files"""
        if cls.part_arrs == None:
            cls.set_part_arrs()
        return cls.part_arrs
    @classmethod
    def set_part_arrs(cls, length:int=9999) -> None:
        """Set the static variable part_arrs"""
        length = max(length, 26); length = min(length, 999999) # TODO: improve handling with larger values
        alpha = [None, 'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] # namea, nameb, etc.
        nums = [str(i) for i in range(0,length+1)] # name1, name2, etc.
        #### array of arrays with length and zero padding incrementing based on the number of digits of length
        nums_padded = [[n.zfill(i) for j, n in enumerate(nums) if j < 10**i-1] for i in reversed(range(2,len(str(length))))] # name01, name02, etc.
        #### set static variable part_arrs
        cls.part_arrs = [alpha, nums] + nums_padded
####################################################################################################
####################################################################################################
def main() -> None:
    #### parses script input to populate args dict
    args = parse_inputs()
    #### recursively find all dirs in dir_in between levels mindepth and maxdepth with excludes removed
    dirs_walk = listdir_dirs(args['dir_in'], args['mindepth'], args['maxdepth'], args['excludes'])
    #### print useful info
    print(f"INFO: root dir to search for multifiles: '{args['dir_in']}'")
    if len(dirs_walk) > 1:
        print(f"INFO: searching recursively {args['mindepth']}-{args['maxdepth']} dirs deep... found {len(dirs_walk)} dirs")
    print(f"INFO: regex file filter: '{args['regex']}'")
    #### search for multifiles in dirs_walk
    mfs_list = [Multifile.extract_multifiles(d, listdir_files(d, args['regex']), min_in=args['range_search'][0], max_in=args['range_search'][-1]) for d in dirs_walk]
    print(f"INFO: found {sum(len(mfs) for mfs in mfs_list)} multifile candidates")
    #### mv each multifile
    [mf.mv(args['parts_out'], args['dir_out'], args['range_mv'], args['inplace']) for mfs in mfs_list for mf in mfs]
    print('INFO: SUCCESS')

if __name__ == "__main__":
    main()