# Python module for tools related to path objects
#
# usage
#   * from utils import path_utils
#       * adding this to a python file allows usage of functions as path_utils.func()
#
# author: acegene <acegene22@gmail.com>

import errno
import os
import shutil
import tempfile
import uuid

from typing import Sequence, Union

from utils.lock_manager import LockManager

# https://www.programcreek.com/python/?code=lanbing510%2FGTDWeb%2FGTDWeb-master%2Fdjango%2Fcore%2Ffiles%2Fmove.py

# path_this = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
# dir_this = os.path.dirname(path_this)
# base_this = os.path.basename(path_this)

PathLike = Union[str, bytes, os.PathLike]


def generate_tmp_from_path(path: PathLike):
    """Generate and return temporary unique pathname from <path>

    Prereq cmds:
        PathLike = Union[str, bytes, os.PathLike]

    Imports:
        os
        uuid

    Args:
        path (PathLike): Path to generate output tmp path from

    Returns:
        Pathlike: Path that has been added unique content
    """
    #### generate unique ID
    copy_id = uuid.uuid4()
    #### cp <src> <tmp_dst> # cp across filesystems to tmp location
    return f"{path}.{copy_id}.tmp"


def is_filesystem_case_sensitive(dir_: PathLike = ".") -> bool:
    """Check whether <dir_> is part of a case sensitive filesystem

    Requires write access to <dir_>

    https://stackoverflow.com/a/36580834/10630957

    Prereq cmds:
        PathLike = Union[str, bytes, os.PathLike]

    Imports:
        os
        tempfile

    Args:
        dir_ (PathLike): Directory that is being tested for case sensitivity

    Returns:
        bool: True if filesystem for <dir_> is case sensitive
    """
    try:
        return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]
    except AttributeError:
        setattr(is_filesystem_case_sensitive, "case_sensitive_dir_dict", {})
    finally:
        with tempfile.NamedTemporaryFile(prefix="TmP", dir=dir_) as tmp_file:
            is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_] = not os.path.exists(tmp_file.name.lower())
            return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]


def mv(src: PathLike, dst: PathLike, ignore_locks=False) -> None:
    """Atomically move object <src> to <dst> even across filesystems

    Avoids race conditions with programs that utilize advisory locking system (see LockManager)

    https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python/

    TODO:
        directory contents are not locked, only the directory itself

    Prereq cmds:
        PathLike = Union[str, bytes, os.PathLike]

    Imports:
        import errno
        import os
        import shutil
        import uuid

    Import locals:
        from utils import path_utils
        from utils.lock_manager import LockManager

    Args:
        src (PathLike): Object to move
        dst (PathLike): Destination object to move <src> to

    Returns:
        None

    Raises:
        FileNotFoundError: if os.path.exists(<src>)
        FileExistsError: if os.path.exists(<dst>)
        NotADirectoryError: if the directory of <src> or <dst> does not exist
        PermissionError: if a lock could not be secured for <src> or <dst>
    """
    #### normalize inputs
    src_nrm = path_clean(src)
    dst_nrm = path_clean(dst)
    #### lock <src> and <dst> prior to interacting with them to avoid race condition
    locks_err = None
    try:
        if not ignore_locks:
            lock_manager = LockManager(src_nrm, dst_nrm)
            lock_manager.create_locks()
    except PermissionError as err:
        locks_err = err
    except:
        lock_manager.release_locks()
        raise
    #### check that a mv <src> to <dst> is possible
    try:
        #### <src> must exist
        if not os.path.exists(src_nrm):
            if os.path.exists(os.path.dirname(src_nrm)):
                raise FileNotFoundError("File or directory '%s' aka <src> does not exist!" % (src))
            else:
                raise NotADirectoryError("Directory for '%s' aka <src> does not exist!" % (src))
        #### <dst> must not exist
        if os.path.exists(dst_nrm):
            if os.path.samefile(src_nrm, dst_nrm):  # works for dirs too
                if os.path.isfile(dst_nrm):
                    raise FileExistsError("Files '%s' == '%s' aka <src> == <dst>" % (src, dst))
                else:
                    raise FileExistsError("Directories '%s' == '%s' aka <src> == <dst>" % (src, dst))
            else:
                if os.path.isfile(dst_nrm):
                    raise FileExistsError("File '%s' aka <dst> should not exist!" % (dst))
                else:
                    raise FileExistsError("Directory '%s' aka <dst> should not exist!" % (dst))
        else:
            if not os.path.exists(os.path.dirname(dst_nrm)):
                raise NotADirectoryError("Directory for '%s' aka <dst> does not exist!" % (dst))
    except:
        lock_manager.release_locks()
        raise
    #### continue only if locks were obtained
    if locks_err != None:
        lock_manager.release_locks()
        raise locks_err
    #### execute mv
    try:
        try:
            os.rename(src_nrm, dst_nrm)
        except OSError as err:
            if err.errno == errno.EXDEV:
                #### generate unique ID for <dst_nrm> and assign to <tmp_dst>
                tmp_dst = generate_tmp_from_path(dst_nrm)
                #### mv <tmp_dst> <src> # atomic mv, handled differently for files and dirs
                if os.path.isfile(src):
                    shutil.copyfile(src_nrm, tmp_dst)
                    os.rename(tmp_dst, dst_nrm)
                    os.unlink(src_nrm)
                else:
                    shutil.copytree(src_nrm, tmp_dst)
                    os.rename(tmp_dst, dst_nrm)
                    shutil.rmtree(src_nrm)
            else:
                raise
    except:
        if not ignore_locks:
            lock_manager.release_locks()
        raise


def mv_multi(srcs: Sequence[PathLike], dsts: Sequence[PathLike]) -> None:
    """Move objects <srcs> to <dsts> even across filesystems

    Prereq cmds:
        PathLike = Union[str, bytes, os.PathLike]

    Imports:
        errno
        os
        shutil
        from typing import Sequence

    Import locals:
        from utils.lock_manager import LockManager

    Args:
        srcs (Sequence[PathLike]): Objects to move
        dsts (Sequence[PathLike]): Destination objects to move <srcs> to

    Returns:
        None

    Raises:
        FileNotFoundError: if not all([os.path.exists(src) for src in <srcs>])
        FileExistsError: if any([os.path.exists(dst) for dst in <dsts> if os.path.samefile(src, dst) for src in <srcs>])
        PermissionError: if the lock for any file in <srcs> or <dsts> cannot be acquired
        ValueError: if len(<srcs>) != len(<dsts>) or all elements of <srcs> or <dsts> are not unique
    """
    #### ensure <srcs> and <dsts> are the same length
    if len(srcs) != len(dsts):
        raise ValueError("Inputs <srcs> and <dsts> should have the same length!")
    #### normalize inputs
    srcs_nrm = [path_clean(src) for src in srcs]
    dsts_nrm = [path_clean(dst) for dst in dsts]
    #### remove duplicates from <srcs> # TODO: handle when dirname does not exist
    srcs_unique = set()
    for src in srcs_nrm:
        dir_src = os.path.dirname(src)
        if not os.path.isdir(dir_src):
            raise NotADirectoryError("Directory for '%s' from <srcs> does not exist!" % (src))
        srcs_unique.add(src if is_filesystem_case_sensitive(dir_src) else src.lower())
    #### remove duplicates from <dsts>
    dsts_unique = set()
    for dst in dsts_nrm:
        dir_dst = os.path.dirname(dst)
        if not os.path.isdir(dir_dst):
            raise NotADirectoryError("Directory for '%s' from <dsts> does not exist!" % (dst))
        dsts_unique.add(dst if is_filesystem_case_sensitive(dir_dst) else dst.lower())
    #### all of <srcs> and <dsts> must be unique
    if len(srcs_nrm) != len(srcs_unique):
        raise ValueError("All <srcs> values should be unique! %s" % (srcs))
    if len(dsts_nrm) != len(dsts_unique):
        raise ValueError("All <dsts> values should be unique! %s" % (dsts))
    #### lock <srcs> and <dsts> prior to interacting with them to avoid race condition
    locks_err = None
    try:
        lock_manager = LockManager(*set.union(srcs_unique, dsts_unique))
        lock_manager.create_locks()
    except PermissionError as err:
        locks_err = err
    except:
        lock_manager.release_locks()
        raise
    #### check that a mv_multi <srcs> to <dsts> is possible
    try:
        #### all of <srcs> must exist
        for src in srcs_nrm:
            if not os.path.exists(src):
                if os.path.exists(os.path.dirname(src)):
                    raise FileNotFoundError("File or directory '%s' from <srcs> does not exist!" % (src))
                else:  # redundantly verifying if dir exists
                    raise NotADirectoryError("Directory '%s' from <srcs> does not exist!" % (src))
        #### all of <dsts> must not exist unless also part of <srcs>
        for dst in dsts_nrm:
            if os.path.exists(dst):
                if not any((os.path.samefile(src, dst) for src in srcs_nrm)):
                    if os.path.isfile(dst):
                        raise FileExistsError("File '%s' from <dsts> should not exist!" % (dst))
                    else:
                        raise FileExistsError("Directory '%s' from <dsts> should not exist!" % (dst))
            else:  # redundantly verifying if dir exists
                if not os.path.exists(os.path.dirname(dst)):
                    raise NotADirectoryError("Directory '%s' from <dsts> does not exist!" % (dst))
    except:
        lock_manager.release_locks()
        raise
    #### continue only if locks were obtained
    if locks_err != None:
        raise locks_err
    #### execute mv_multi
    try:
        #### generate <tmp_dsts> from <dsts_nrm>
        tmp_dsts = [generate_tmp_from_path(dst) for dst in dsts_nrm]
        #### perform mv(srcs, tmp_dsts)
        for src, tmp_dst, dst in zip(srcs_nrm, tmp_dsts, dsts_nrm):
            if os.path.exists(dst):
                continue
            mv(src, tmp_dst, ignore_locks=True)
        #### perform mv(tmp_dsts, dsts)
        for src, tmp_dst, dst in zip(srcs_nrm, tmp_dsts, dsts_nrm):
            if os.path.exists(dst):
                continue
            mv(tmp_dst, dst, ignore_locks=True)
    except:
        lock_manager.release_locks()
        raise


def path_basename_to_lower(path: PathLike, ignore_locks=False) -> PathLike:
    """Rename <path> to a lowercase

    TODO:
        Add persisting lock for the target filename

    Prereq cmds:
        PathLike = Union[str, bytes, os.PathLike]

    Imports:
        os

    Args:
        path (PathLike): Path to rename to lowercase

    Returns:
        PathLike: Newly renamed
    """
    path_cleaned = path_clean(path)
    basename_lower = str(os.path.basename(path_cleaned)).lower()
    path_lower = os.path.join(os.path.dirname(path_cleaned), basename_lower)
    if is_filesystem_case_sensitive(os.path.dirname(path_cleaned)):
        mv(path, path_lower, ignore_locks)
    else:
        path_lower_tmp = generate_tmp_from_path(path_lower)
        mv(path, path_lower_tmp, ignore_locks)
        mv(path_lower_tmp, path_lower, ignore_locks)
    return path_clean(path_lower)


def is_path_basename_lower(path: PathLike) -> PathLike:
    path_cleaned = path_clean(path)
    basename = str(os.path.basename(path_cleaned))
    return basename == basename.lower()


def path_clean(path: PathLike) -> PathLike:
    """Clean <path> representation to give deterministic comparable representation

    Prereq cmds:
        PathLike = Union[str, bytes, os.PathLike]

    Imports:
        os

    Args:
        path (PathLike): Path to clean and return

    Returns:
        PathLike: A clean path
    """
    return os.path.abspath(os.path.normpath(path))
