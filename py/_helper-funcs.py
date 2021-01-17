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

def safe_execute(default, exception, func, *args):
    try:
        return function(*args)
    except exception:
        return default

def except_if_not(exception:Type[Exception], expression:bool, string_if_except:str=None) -> None:
    """Throw exception if expression is False"""
    if not expression:
        if string_if_except != None:
            print(string_if_except)
        raise exception

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


def ifnone(obj:Any, default:Any) -> Any:
    """Return <default> if <obj> == None"""
    return default if obj == None else obj

