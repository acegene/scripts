#!/usr/bin/python3
#
# title: _helper-funcs.py
#
# descr: collection of useful python3 funcs, with minimized external dependencies
#
#      * this file and its funcs need to have special formatting
#          * func first line should comply with regex '^def .*:$'
#          * adjacent newline characters mark the end of the func
#          * file must end with two newline characters
#      * formatting compliance enables write-btw.py to parse this files funcs

#### from typing import Type
def except_if_false(exception:Type[Exception], expression:bool, string_if_except:str=None) -> None:
    """Throw <exception> if <expression> == False"""
    if not expression:
        if string_if_except != None:
            print(string_if_except)
        raise exception

#### from typing import Any, Callable, Sequence, Type, Union
def try_or(exceptions:Union[Type[Exception], Sequence[Type[Exception]]], call:Callable, *args, default:Any=None, **kargs) -> Any:
    """Returns result from calling <call> with <*args> <**kargs>; if an exception in <exceptions> occurs return default"""
    try:
        return call(*args, **kargs)
    except (exceptions):
        return default

#### from typing import Any
def get_with_default(obj:Any, default:Any) -> Any:
    """Return <default> if <obj> == None"""
    return default if obj == None else obj

#### import errno, os, shutil, uuid
#### os: 'Windows 10 2004'
#### https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python/
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

#### from typing import Optional, Type
#### https://stackoverflow.com/questions/4726168/parsing-command-line-input-for-numbers
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

##### https://stackoverflow.com/questions/19257498/combining-two-slicing-operations
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
        assert length_out >= 0 and length_out <= length
        #### return combined_slice, length slice
        return slice(start, stop, step), length_out
    out, _ = functools.reduce(lambda x, y: slice_merge(x[0], y, x[1]), slices, (slice(0, None, 1), length))
    return out

#### import sys
#### https://stackoverflow.com/questions/3160699/python-progress-bar
def progressbar(it, prefix='', size=60, file=sys.stderr):
    count = len(it)
    def show(j):
        x = int(size*j/count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), j, count))
        file.flush()
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    file.write("\n")
    file.flush()

