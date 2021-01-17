#!/usr/bin/python3
#
# title: mfmv.py
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
#      * mfs search by default locates mfs with their first file's part in ['a','0','1'] e.g. mf = [f_a,f_b,f_c]
#            * '--range-search 3-4' via cmdargs can locate mf=[f3,f4,f5] or mf=[f4,f5]; note: does not limit length of mf
#
#      * mfs mv default format is base + postpart + part + ext unless inplace=True then format is base + part + postpart + ext
#            * partial mv: '--range-mv 2-3' via cmdargs or 'range_mv 2-3' via cli to allow mf=[f1,f2,f3] to mv only [f2,f3]
#
#      * mf mv is not atomic, but each individual file mv is atomic; see: https://en.wikipedia.org/wiki/Atomicity_(database_systems)
#
# usage: python mfmv.py --help
#            * provides help info on scripts cmd line args
#        python mfmv.py
#            * uses default params to locate mfs and launch cli
#
# warns: race condition when an external process moves files currently being batch mv'd
#            * each file is safe, but in the worst case an abort occurs and only a portion of the mf's files will mv
#
# notes: version 1.0
#        tested on 'Windows 10 2004' # TODO: testing with OSX and linux
#
# todos: handle files without extensions
#        proper cmd args mutual exclusion
#        performance with high quantities of files
#        allow two mvs for same mf if done partially
#        file input for cmdargs
#        allow custom user input auto filename formatter

import argparse
import collections
import errno
import functools
import itertools
import json
import os
import re
import shutil
import sys
import uuid

from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence, Type, Union

if sys.version_info < (3,6): # version 3.6.X or newer allows f strings
    raise Exception("ERROR: python version needs to be 3.6.X or newer, instead is: " + '.'.join([str(m) for m in sys.version_info[:3]]))
################&&!%@@%!&&################ AUTO GENERATED CODE BELOW THIS LINE ################&&!%@@%!&&################
# yymmdd: 210116
# generation cmd on the following line:
# python "${GWSPY}/write-btw.py" "-t" "py" "-w" "${GWSPY}/mfmv.py" "-x" "mv_atomic" "except_if_false" "try_or" "parse_range" "get_with_default" "slice_clean" "slice_is_negative" "slice_length" "slice_lst_merge"

def except_if_false(exception:Type[Exception], expression:bool, string_if_except:str=None) -> None:
    """Throw <exception> if <expression> == False"""
    if not expression:
        if string_if_except != None:
            print(string_if_except)
        raise exception

def try_or(exceptions:Union[Type[Exception], Sequence[Type[Exception]]], call:Callable, *args, default:Any=None, **kargs) -> Any:
    """Returns result from calling <call> with <*args> <**kargs>; if an exception in <exceptions> occurs return default"""
    try:
        return call(*args, **kargs)
    except (exceptions):
        return default

def get_with_default(obj:Any, default:Any) -> Any:
    """Return <default> if <obj> == None"""
    return default if obj == None else obj

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

def parse_range(range_str:str, throw:bool=True) -> Optional[List[int]]:
    """Generate a list from <range_str>"""
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

def slice_clean(slice_:slice, length:int) -> slice: # TODO: slice(None, None, -1)
    """Get rid of None's, overly large indices, and negative indices"""
    #### (except -1 for backward slices that go down to first element) # TODO:
    start, stop, step = slice_.indices(length)
    # get number of steps & remaining
    n, r = divmod(stop - start, step)
    if n < 0 or (n==0 and r==0):
        return slice(0,0,1)
    if r != 0: # its a "stop" index, not an last index
        n += 1
    if step < 0:
        start, stop, step = start+(n-1)*step, start-step, -step
    else: # step > 0, step == 0 is not allowed
        stop = start+n*step
    stop = min(stop, length)
    return slice(start, stop, step)

def slice_is_negative(slice_:slice) -> bool:
    return get_with_default(slice_.start, 0) < 0 or get_with_default(slice_.stop, 0) < 0

def slice_length(slice_:slice) -> int:
    assert slice_.stop != None
    start = get_with_default(slice_.start, 0)
    step = get_with_default(slice_.step, 1)
    return max((slice_.stop - start) // step, 1)

def slice_lst_merge(slices:Sequence[slice], length:int) -> slice:
    """ returns a slice that is a combination of all slices.
    given <slices> = [slice1, slice2] then the following is True
    x[slice1][slice2] == x[slice_lst_merge(slice1, slice2, len(x))]
    :param slices: list of slices
    :param length: length of the first dimension of data being sliced e.g. len(x)
    """
    def slice_merge(lhs:slice, rhs:slice, length:int) -> slice:
        #### get step sizes
        lhs_step = (lhs.step if lhs.step is not None else 1)
        rhs_step = (rhs.step if rhs.step is not None else 1)
        step = lhs_step * rhs_step
        #### get indices from slicing with <lhs> assuming length=<length>
        lhs_indices = lhs.indices(length)
        #### length of slice using <lhs>
        lhs_length = (abs(lhs_indices[1] - lhs_indices[0]) - 1) // abs(lhs_indices[2])
        #### deterimine there is at least one datapoint when stepping from start to stop with <lhs>
        if (lhs_indices[1] - lhs_indices[0]) * lhs_step > 0:
            lhs_length += 1
        else:
            return slice(0, 0, step) # slice of zero length
        #### get indices from slicing with <lhs> assuming length=<lhs_length>
        rhs_indices = rhs.indices(lhs_length)
        #### return empty slice if the resulting range is 0
        if not (rhs_indices[1] - rhs_indices[0]) * rhs_step > 0:
            return slice(0, 0, step)
        #### transform <rhs_indices> using <lhs_indices[0]> and <lhs_step>
        start = lhs_indices[0] + rhs_indices[0] * lhs_step
        stop = lhs_indices[0] + rhs_indices[1] * lhs_step
        #### if stop == -1: stop = None
        if start > stop:
            if stop < 0:
                stop = None
                length_out = length
            else:
                length_out = start
        else:
            length_out = stop
        assert length_out >= 0 and length_out <= length, "length_out=%s length=%s" % (length_out, length) # TODO: check
        #### return combined_slice, length slice
        return slice(start, stop, step), length_out
    out, _ = functools.reduce(lambda x, y: slice_merge(x[0], y, x[1]), slices, (slice(0, None, 1), length))
    return out
################&&!%@@%!&&################ AUTO GENERATED CODE ABOVE THIS LINE ################&&!%@@%!&&################
def alpha_from_int(x:int) -> str:
    """Return the alpha lowercase char associated with <x>"""
    return chr(x+96)

def int_from_alpha(string:str) -> int:
    """Return the int associated with <string>"""
    if len(string) != 1:
        return 0
    new = ord(string)
    if 65 <= new <= 90: # uppercase
        return new - 64
    elif 97 <= new <= 122: # lowercase
        return new - 96
    return 0 # unrecognized

def parse_range_alpha(range_str:str, throw=True) -> Union[List[int], List[str], None]:
    """Generate a list from <range_str>"""
    #### local funcs
    def newListRemove(element, lst): return list(filter(lambda x: x != element, lst))
    error = None
    error = TypeError if not error and not isinstance(range_str, str) else error
    error = ValueError if not error and range_str == '' else error
    if error:
        print(f"ERROR: expect str with only positive ints, commas and hyphens, given '{range_str}'")
        if throw:
            raise error
        return None
    if range_str[0].isalpha():
        range_lst = parse_range(''.join([str(int_from_alpha(c)) if c.isalpha() else c for c in range_str]), throw)
        if range_lst == None:
            return None
        return [alpha_from_int(x) for x in range_lst] if range_lst != None else None
    else:
        return parse_range(range_str, throw)

def parse_inputs() -> dict:
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    #### local funcs
    def import_json_obj(f:str, key:str) -> List[str]:
        """Returns json object associated with key from file"""
        with open(f, 'r') as json_file:
            data = json.load(json_file)
            except_if_false(ValueError, key in data)
            return data[key]
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir-in', '-i', default='.', help='dir to search for multifiles')
    parser.add_argument('--dir-out', '-o', help='dir to mv multifiles into')
    parser.add_argument('--part-out', '--po', '-p', default='-1', help='first part of multifile mv i.e. pt-1')
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
    except_if_false(ValueError, os.path.isdir(out['dir_in']))
    except_if_false(ValueError, out['dir_out'] == None or os.path.isdir(out['dir_out']))
    except_if_false(ValueError, len([True for x in [out['regex'], out['exts'], out['exts_env'], out['exts_json']] if x != None and x != False]) <= 1)
    except_if_false(ValueError, out['maxdepth'] >= out['mindepth'] and out['mindepth'] > 0)
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
    out['parts_out'] = Multifile.get_parts_out_list(out['part_out'])
    assert out['parts_out'] is not None
    except_if_false(ValueError, out['parts_out'] != None, "ERROR: part_out arg of '" + str(out['part_out']) + "' is unrecognized")
    #### remove entries from returned dict that are unused by the surrounding scope
    [out.pop(k, None) for k in ['exts_env', 'exts_json', 'exts', 'part_out']]
    #### return dictionary of modified cmd args
    return out

def listdir_dirs(dir_in:str='', mindepth:int=1, maxdepth:int=1, excludes:Sequence[str]=[]) -> List[str]:
    """Get dirs from directory within the recursive depths mindepth-maxdepth and remove excludes"""
    #### recursively find all dirs in dir_in between levels mindepth and maxdepth with excludes removed
    dirs_walk = [d[0] for d in os.walk(dir_in) if os.walk(dir_in) and d[0][len(dir_in):].count(os.sep) <= maxdepth-1 and d[0][len(dir_in):].count(os.sep) >= mindepth-1]
    #### remove all excludes from dirs_walk
    return [d for d in dirs_walk if all([False for e in excludes if e in d])]

def listdir_files(dir_in:str='.', regex:str='.*') -> List[str]:
    """Get files from dir_in that match the regex pattern reg"""
    files = [f for f in os.listdir(dir_in) if os.path.isfile(os.path.join(dir_in, f))]
    return [f for f in files if re.search(regex, f, re.IGNORECASE) != None]

class SequenceWrappedGeneratorFunction(collections.abc.Sequence):
    """Wrapper for allowing access of <gen_func>() as if it were an immutable sequence"""
    def __init__(self, gen_func:Callable[..., Iterable], args:Sequence[Any]=[], kargs:Mapping={}, size_internal:Optional[int]=None, slices:Sequence[slice]=[], gen_func_sliceable=False):
        assert isinstance(args, collections.abc.Sequence)
        assert isinstance(slices, collections.abc.Sequence)
        #### private attributes
        self.__sliceable_gen_func = gen_func if gen_func_sliceable else self.__wrap_sliceable(gen_func)
        self.__args = tuple(*args)
        self.__kargs = dict(**kargs)
        self.__size_internal = size_internal
        self.__slices = slices
    #### magic methods
    def __contains__(self, val:Any) -> bool:
        return val in self.__iter__()
    def __getitem__(self, i: Union[int, slice, Sequence[slice]]) -> Any:
        if isinstance(i, slice):
            return SequenceWrappedGeneratorFunction(self.__sliceable_gen_func, self.__args, self.__kargs, self.__size_internal, self.__slices + [i], True)
        elif isinstance(i, Sequence):
            assert all([isinstance(s, slice) for s in i])
            return SequenceWrappedGeneratorFunction(self.__sliceable_gen_func, self.__args, self.__kargs, self.__size_internal, self.__slices + i, True)
        else: # TODO: assert
            return next(self.__iter_internal(self.__slices + [slice(i, i+1, 1)]))
    def __iter__(self) -> Iterable:
        return self.__iter_internal(self.__slices)
    def __len__(self) -> int:
        if self.__size_internal != None:
            if len(self.__slices) == 0:
                slice_ = slice(0, None, 1)
            elif len(self.__slices) == 1:
                slice_ = self.__slices[0] if not slice_is_negative(self.__slices[0]) else slice_clean(self.__slices[0], self.__size_internal)
            else:
                slice_ = slice_clean(slice_lst_merge(self.__slices, self.__size_internal), self.__size_internal)
            slice_ = slice_clean(slice_lst_merge([slice(self.__size_internal), slice_], self.__size_internal), self.__size_internal)
            assert slice_.stop != None, "ERROR: slice: " + str(slice_) + ": " + str(self.__slices)
            return slice_length(slice_)
        return functools.reduce(lambda x, y: x + 1, self.__iter__(), 0) # TODO: rework maybe
    def __repr__(self) -> str:
        return '[' + ', '.join([str(x) for x in self.__sliceable_gen_func(self.__slices, *self.__args, **self.__kargs)]) + ']'
    def __reversed__(self) -> Iterable:
        return self.__iter_internal(self.__slices + [slice(None, None, -1)])
    def __str__(self) -> str:
        return self.__repr__()
    #### public methods
    def count(self, val:Any) -> int:
        count = 0
        for i, x in enumerate(self.__iter__()):
            if x == val:
                count += 1
        return count
    def index(self, val:Any) -> int:
        for i, x in enumerate(self.__iter__()):
            if x == val:
                return i
        raise ValueError("'" + str(val) + "' not in sequence")
    #### private methods
    def __iter_internal(self, slices:Sequence[slice]=[]) -> Iterable:
        return self.__sliceable_gen_func(slices, *self.__args, **self.__kargs)
    def __len_internal(self) -> int:
        if self.__size_internal == None:
            self.__size_internal = functools.reduce(lambda x, y: x + 1, self.__iter_internal(), 0)
        return self.__size_internal
    def __wrap_sliceable(self, gen_func:Callable[..., Iterable]) -> Callable[..., Iterable]: # TODO:
        """returns a generator function wrapped to take a slice list"""
        def __sliceable_gen_func(gen_func, size_callable, slices, *args):
            if len(slices) == 0:
                slice_ = slice(0, None, 1)
            elif len(slices) == 1:
                slice_ = slices[0] if not slice_is_negative(slices[0]) else slice_clean(slices[0], size_callable())
            else:
                for s in slices:
                    if slice_is_negative(s):
                        size = size_callable()
                        slice_ = slice_clean(slice_lst_merge(slices, size), size)
                        break
                else:
                    slice_ = slice_lst_merge(slices, sys.maxsize)
            for n in itertools.islice(gen_func(*args),slice_.start,slice_.stop,slice_.step):
                yield n
        return functools.partial(__sliceable_gen_func, gen_func, self.__len_internal)

class Multifile():
    """Allows operation on a contiguous group of similarly named files"""
    #### private class attributes
    __prefix_style:str = r'( - |_|-|| )(cd|ep|episode|pt|part|| )( - |_|-|| )'
    _parts_lists:Optional[List[Sequence]] = None # set via __set_parts_lists implicitly
    #### magic methods
    def __init__(self, file_dict:dict) -> None:
        assert all(True if k in ['dir', 'base', 'prepart', 'parts', 'postpart', 'ext'] else False for k in file_dict.keys())
        #### object attributes
        self.file_dict:dict = file_dict
    def __getitem__(self, key:Union[str,int]) -> Any:
        return self.file_dict[key] if isinstance(key, str) else self.__get_nth_file(key)
    #### public methods
    ## methods that manipulate the state of the multifile or its referenced contents
    def mv(self, parts_lst:Sequence, dir_out:Optional[str]=None, range_mv:Optional[Sequence[int]]=None, inplace:bool=False) -> Optional['Multifile']:
        """Move this object's files using the pattern specified by parts"""
        #### asserts
        assert self.ismultifile()
        #### set output multifile dict
        out_dict = {k:v for k, v in self.file_dict.items()}
        out_dict['dir'] = dir_out if dir_out != None else self['dir']
        out_dict['prepart'] = None
        if range_mv == None:
            # if len(parts_lst) < self.size():
            #     print(f"ERROR: selected parts_out not big enough for multifile, choose new part or range\nERROR: partlist: {parts}\nERROR: multifile: {out_dict['parts']}")
            parts_lst = parts_lst[:self.size()]
        else:
            if str(parts_lst[0][-1]).isalpha() != str(range_mv[0]).isalpha():
                print(f"WARNING: parts input ({str(parts_lst[0][-1])}) and range ({str(range_mv[0])}) should both be alpha characters or both be ints")
            parts_lst = parts_lst[:len(range_mv)]
        #### describe the state of the potential mv
        print('INFO: printing potential mv cmds to be executed...')
        while True:
            #### check if mv operations are valid, if not then abort
            if range_mv == None:
                reduced_list = self.to_list()
            else:
                reduced_list = [self.__get_nth_file(i) for i, p in enumerate(self['parts']) if p.lower() in [str(r) for r in range_mv]] # TODO: self.to_list()[i] wont work
                assert len(reduced_list) == len(range_mv), f"ERROR: portion of range unaccounted for '{len(reduced_list)}' != '{len(range_mv)}'" # TODO:
                if len(reduced_list) != self.size():
                    print(f"INFO: partial mv being proposed for {len(reduced_list)} out of {self.size()} files revert to full mv with input 'r all'")
                    print(f"INFO: indices of partial mv (range): {range_mv}")
            out_dict['parts'] = parts_lst[:len(reduced_list)]
            #### create mf object based on out_dict which is manipulated by user input
            out_mf = Multifile(out_dict)
            new_list = out_mf.to_list(inplace=inplace)
            length = len(reduced_list)
            new_length = len(new_list)
            if length != new_length:
                print(f"ERROR: multifile length mismatch for lhs ({length}) and rhs ({new_length})")
            for i, (old, new) in enumerate(itertools.zip_longest(reduced_list, new_list, fillvalue='NO_EQUIVALENT_VALUE')):
                if old == new:
                    print(f"WARNING: target '{new}' exists")
                    break
                if max(length, new_length) < 10:
                    print(f"  mv {old} {new}")
                else:
                    if i in [0, 1, 2, max(length, new_length)-3, max(length, new_length)-2, max(length, new_length)-1]:
                        print(f"  mv {old} {new}")
                    if i == 3:
                        print(f"  ... {max(length, new_length)} files total")
            print('PROMPT: (c)ontinue; (d)ir str; (b)ase str; (p)art str; (e)xt str; (r)ange_mv str; (i)nplace; (s)kip; (q)uit')
            choice = input()
            if choice == 'continue' or choice == 'c':
                if length != new_length:
                    continue
                if not all([True if old not in new_list else False for old in reduced_list]):
                    if not all([old != new for old, new in zip(reduced_list, new_list)]):
                        print(f"ERROR: src and target have overlap of some/all files:\nERROR: src: {reduced_list}\nERROR: targ: {new_list}")
                        continue
                    # TODO: hack to reverse lists to avoid mf overwriting itself during mv
                    old_char = self['parts'][0][-1]
                    new_char = out_mf['parts'][0][-1]
                    if old_char.isdigit():
                        if int(old_char) < int(new_char):
                            reduced_list.reverse()
                            new_list.reverse()
                    else:
                        if old_char < new_char:
                            reduced_list.reverse()
                            new_list.reverse()
                assert self.ismultifile()
                #### simulate mv and perform preliminary checks to avoid unwanted partial mvs
                sim_failed = False
                out_exists = [f for f in new_list if os.path.isfile(f)]
                for old, new in zip(reduced_list, new_list):
                    if old == new:
                        print(f"ERROR: mv sim error: old==new: mv '{old}' '{new}'")
                        sim_failed = True; break
                    if not os.path.isfile(old):
                        print(f"ERROR: mv sim error: os.path.isfile(old)==False: mv '{old}' '{new}'")
                        sim_failed = True; break
                    if new in out_exists:
                        print(f"ERROR: mv sim error: os.path.isfile(new)==True: mv '{old}' '{new}'")
                        sim_failed = True; break
                    try_or(ValueError, out_exists.remove, old)
                    out_exists.append(new)
                if sim_failed:
                    continue
                if not all([True if ol in out_exists else False for ol in new_list]):
                    print(f"ERROR: mv sim error: new_list != out_list\nERROR: new_list: {new_list}\nERROR: out_exists: {out_exists}")
                    continue
                #### mv the files, they are assumed
                for old, new in zip(reduced_list, new_list):
                    #### asserts to prepare for mv
                    assert not os.path.isfile(new), f"ERROR: mv '{old}' '{new}'"
                    #### basic mv operation on single file
                    mv_atomic(old, new)
                    #### asserts to prepare for mv
                    assert not os.path.isfile(old), f"ERROR: mv '{old}' '{new}'"
                    assert os.path.isfile(new), f"ERROR: mv '{old}' '{new}'"
                self = out_mf
                return self
            elif choice[:9] == 'range_mv ' or choice[:2] == 'r ':
                tmp_range = choice.split(' ', 1)[1]
                if tmp_range == 'all':
                    range_mv = None
                else:
                    tmp_parsed = parse_range(tmp_range, throw=False)
                    if tmp_parsed:
                        if str(tmp_parsed[0]).isalpha() != self.__isalpha():
                            print('ERROR: range and multifile must both be alpha characters or both be ints')
                        else:
                            range_mv = tmp_parsed
            elif choice == 'inplace' or choice == 'i':
                inplace = not inplace
            elif choice == 'skip' or choice == 's':
                print('INFO: skipping mv of this batch of multifiles')
                break
            elif choice == 'quit' or choice == 'q':
                sys.exit()
            elif choice[:4] == 'dir ' or choice[:2] == 'd ':
                tmp_dir = choice.split(' ', 1)[1]
                if not os.path.isdir(tmp_dir):
                    print(f"ERROR: the following is not a dir: {tmp_dir}")
                else:
                    out_dict['dir'] = tmp_dir
            elif choice[:5] == 'base ' or choice[:2] == 'b ':
                out_dict['base'] = choice.split(' ', 1)[1]
                if not inplace:
                    out_dict['postpart'] = None
            elif choice[:5] == 'part ' or choice[:2] == 'p ':
                tmp_lst = Multifile.get_parts_out_list(choice.split(' ', 1)[1])
                parts_lst = tmp_lst if tmp_lst != None else parts_lst
            elif choice[:4] == 'ext ' or choice[:2] == 'e ':
                out_dict['ext'] = choice.split(' ', 1)[1]
            else:
                print("ERROR: invalid input for prompt")
            print("#######################################################")
        return None
    ## methods that examine the state of the multifile or its referenced contents
    def ismultifile(self) -> bool:
        """Ensure this object has at least two valid and contiguous files"""
        return all([os.path.isfile(f) for f in self.to_list()]) and self.size() > 1 
    def size(self) -> int:
        return len(self['parts'])
    def to_list(self, exc_dir:bool=False, inplace:bool=True) -> List[str]:
        """Return this object's files to a list of strings"""
        return [self.__get_nth_file(i, exc_dir, inplace) for i in range(self.size())] #TODO: size() slow
    #### private methods
    def __get_nth_file(self, n:int, exc_dir:bool=False, inplace:bool=True) -> str:
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
    def __isalpha(self) -> bool:
        return self['parts'][0][-1].isalpha()
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
        for parts_lst in cls.__get_parts_lists():
            matches = []
            #### find potential first file matches for every file for each part in parts_lst
            for i, part in enumerate(parts_lst[min_in:max_in+1]):
                if part == None:
                    continue
                file_part_indices_list.append([(f, i + min_in, re.finditer(part, f)) for f in files])
            #### generate regex match list for capture groups
            for file_part_indices in file_part_indices_list:
                for (f, part_index, indices) in file_part_indices:
                    for index in indices:
                        regex = '^(.{' + str(index.start()) + '})' + '(' + parts_lst[part_index] +')(.*)(\..*)$'
                        match = re.search(regex, f, re.IGNORECASE)
                        if match:
                            matches.append((part_index, match))
            for (part_index, match) in matches:
                base = match.group(1); part = match.group(2); postpart = match.group(3); ext = match.group(4)
                num_files = 0
                for i, part in enumerate(parts_lst[part_index:]):
                    if part == None:
                        continue
                    part_match = ''.join(c for c in part if not c.isdigit()) # TODO: check
                    part = re.sub(part_match, part_match, part, re.IGNORECASE)
                    file_out = base + part + postpart + ext
                    if not os.path.isfile(os.path.join(dir_in, file_out)) or file_out not in files:
                        break
                    num_files += 1
                if num_files > 1:
                    m = re.search(r'^(.*?)' + cls.__prefix_style + r'$', base, re.IGNORECASE)
                    base = m.group(1)
                    mf = cls({'dir':dir_in, 'base':base, 'prepart':m.group(2) + m.group(3) + m.group(4), 'parts':parts_lst[part_index:part_index+num_files], 'postpart':postpart, 'ext':ext})
                    assert all([True if os.path.isfile(x) else False for x in mf.to_list()]), f"ERROR: {mf.to_list()}"
                    assert all([True if x in files else False for x in mf.to_list(exc_dir=True)]), f"ERROR: {mf.to_list(exc_dir=True)}"
                    mfs_out.append(mf)
        out = max(mfs_out, default=None, key=lambda mf:mf.size())
        if out != None:
            [files.remove(mf) for mf in out.to_list(exc_dir=True)]
            return [out] + cls.extract_multifiles(dir_in=dir_in, files=files, min_in=min_in, max_in=max_in)
        return []
    @classmethod
    def get_parts_out_list(cls, part_out:str) -> Optional[Sequence]:
        """Get the parts generator that will become the rhs for mv operations"""
        match = re.sub("[^0-9]", "", part_out)
        num = int(match) if match != '' else int_from_alpha(part_out[-1])
        for parts_lst in cls.__get_parts_lists():
            try:
                if parts_lst[num] == None:
                    continue
            except StopIteration:
                continue
            regex = '^' + cls.__prefix_style + '(' + parts_lst[num] +')$'
            result = re.search(regex, part_out)
            if result != None:
                def make_parts_out_gen(prepend, slice_):
                    def parts_out_gen(slice_, slices):
                        for part in parts_lst[[slice_] + slices]:
                            if part != None:
                                yield prepend + part
                            else:
                                yield None
                    return functools.partial(parts_out_gen, slice_)
                return SequenceWrappedGeneratorFunction(make_parts_out_gen(result.group(1) + result.group(2) + result.group(3), slice_=slice(num, None, None)), gen_func_sliceable=True)
        else:
            print(f"WARNING: could not find parts array for input '{part_out}'")
            return None
    @classmethod
    def __get_parts_lists(cls) -> List[Sequence]:
        """Get the parts generators for finding contiguous files"""
        if cls._parts_lists == None:
            cls.__set_parts_lists()
        assert cls._parts_lists != None
        return cls._parts_lists
    @classmethod
    def __set_parts_lists(cls) -> None:
        """Set the static variable _parts_lists"""
        length = 999999999 # arbitrarily set to max of 1 billion - 1
        length = max(length, 26); length = min(length, 999999999)
        #### function generators for numbers and lowercase letters
        def nums(slices):
            slice_ = slice_lst_merge(slices, length+1)
            for n in range(*slice_.indices(length+1)):
                yield str(n)
        def alphas(slices):
            lst = [None, 'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
            slice_ = slice_lst_merge(slices, len(lst))
            for n in range(*slice_.indices(length)):
                yield lst[n]
        #### function generators for numbers padded with zeros
        def make_padded_nums(digits):
            def padded_nums(slices):
                for i, part in enumerate((nums(slices))):
                    if i >= 10**int(digits):
                        return
                    yield part.zfill(digits)
            return padded_nums
        #### set static variable _parts_lists
        cls._parts_lists = [SequenceWrappedGeneratorFunction(gf, gen_func_sliceable=True) for gf in [nums, alphas] + [make_padded_nums(i) for i in reversed(range(2,len(str(length))+1))]]
        assert all([isinstance(s, Sequence) for s in cls._parts_lists])
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