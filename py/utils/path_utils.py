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

from typing import Sequence

from utils.lock_manager import LockManager

# https://www.programcreek.com/python/?code=lanbing510%2FGTDWeb%2FGTDWeb-master%2Fdjango%2Fcore%2Ffiles%2Fmove.py

# path_this = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
# dir_this = os.path.dirname(path_this)
# base_this = os.path.basename(path_this)


def generate_tmp_from_path(path: str):
    """Generate and return temporary unique pathname from <path>

    Imports:
        os
        uuid

    Args:
        path (str): Path to generate output tmp path from

    Returns:
        Pathlike: Path that has been added unique content
    """
    #### generate unique ID
    copy_id = uuid.uuid4()
    #### cp <src> <tmp_dst> # cp across filesystems to tmp location
    return f"{path}.{copy_id}.tmp"


def is_filesystem_case_sensitive(dir_: str = ".") -> bool:
    """Check whether <dir_> is part of a case sensitive filesystem

    Requires write access to <dir_>

    https://stackoverflow.com/a/36580834/10630957

    Imports:
        os
        tempfile

    Args:
        dir_ (str): Directory that is being tested for case sensitivity

    Returns:
        bool: True if filesystem for <dir_> is case sensitive
    """
    try:
        return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]  # type: ignore [attr-defined, no-any-return]
    except AttributeError:
        setattr(is_filesystem_case_sensitive, "case_sensitive_dir_dict", {})
    except KeyError:
        pass
    with tempfile.NamedTemporaryFile(prefix="TmP", dir=dir_) as tmp_file:
        is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_] = not os.path.exists(tmp_file.name.lower())  # type: ignore [attr-defined] # pylint: disable=[line-too-long,no-member]
        return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]  # type: ignore [attr-defined, no-any-return] # pylint: disable=[line-too-long,no-member]


def mv(src: str, dst: str, ignore_locks=False) -> None:
    """Atomically move object <src> to <dst> even across filesystems

    Avoids race conditions with programs that utilize advisory locking system (see LockManager)

    https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python/

    TODO:
        directory contents are not locked, only the directory itself

    Imports:
        import errno
        import os
        import shutil
        import uuid

    Import locals:
        from utils import path_utils
        from utils.lock_manager import LockManager

    Args:
        src (str): Object to move
        dst (str): Destination object to move <src> to

    Returns:
        None

    Raises:
        FileNotFoundError: if os.path.exists(<src>)
        FileExistsError: if os.path.exists(<dst>)
        NotADirectoryError: if the directory of <src> or <dst> does not exist
        PermissionError: if a lock could not be secured for <src> or <dst>
    """

    # pylint: disable=[too-many-branches,too-many-statements]
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
                raise FileNotFoundError(f"File or directory '{src}' aka <src> does not exist!")
            raise NotADirectoryError(f"Directory for '{src}' aka <src> does not exist!")
        #### <dst> must not exist
        if os.path.exists(dst_nrm):
            if os.path.samefile(src_nrm, dst_nrm):  # works for dirs too
                if os.path.isfile(dst_nrm):
                    raise FileExistsError(f"Files '{src}' == '{dst}' aka <src> == <dst>")
                raise FileExistsError(f"Directories '{src}' == '{dst}' aka <src> == <dst>")
            if os.path.isfile(dst_nrm):
                raise FileExistsError(f"File '{dst}' aka <dst> should not exist!")
            raise FileExistsError(f"Directory '{dst}' aka <dst> should not exist!")
        if not os.path.exists(os.path.dirname(dst_nrm)):
            raise NotADirectoryError(f"Directory for '{dst}' aka <dst> does not exist!")
    except:
        lock_manager.release_locks()
        raise
    #### continue only if locks were obtained
    if locks_err is not None:
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


def mv_multi(srcs: Sequence[str], dsts: Sequence[str]) -> None:
    """Move objects <srcs> to <dsts> even across filesystems

    Imports:
        errno
        os
        shutil
        from typing import Sequence

    Import locals:
        from utils.lock_manager import LockManager

    Args:
        srcs (Sequence[str]): Objects to move
        dsts (Sequence[str]): Destination objects to move <srcs> to

    Returns:
        None

    Raises:
        FileNotFoundError: if not all([os.path.exists(src) for src in <srcs>])
        FileExistsError: if any([os.path.exists(dst) for dst in <dsts> if os.path.samefile(src, dst) for src in <srcs>])
        PermissionError: if the lock for any file in <srcs> or <dsts> cannot be acquired
        ValueError: if len(<srcs>) != len(<dsts>) or all elements of <srcs> or <dsts> are not unique
    """
    # pylint: disable=[too-many-branches,too-many-statements]
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
            raise NotADirectoryError(f"Directory for '{src}' from <srcs> does not exist!")
        srcs_unique.add(src if is_filesystem_case_sensitive(dir_src) else src.lower())
    #### remove duplicates from <dsts>
    dsts_unique = set()
    for dst in dsts_nrm:
        dir_dst = os.path.dirname(dst)
        if not os.path.isdir(dir_dst):
            raise NotADirectoryError(f"Directory for '{dst}' from <dsts> does not exist!")
        dsts_unique.add(dst if is_filesystem_case_sensitive(dir_dst) else dst.lower())
    #### all of <srcs> and <dsts> must be unique
    if len(srcs_nrm) != len(srcs_unique):
        raise ValueError(f"All <srcs> values should be unique! {srcs}")
    if len(dsts_nrm) != len(dsts_unique):
        raise ValueError(f"All <dsts> values should be unique! {dsts}")
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
                    raise FileNotFoundError(f"File or directory '{src}' from <srcs> does not exist!")
                # redundantly verifying if dir exists
                raise NotADirectoryError(f"Directory '{src}' from <srcs> does not exist!")
        #### all of <dsts> must not exist unless also part of <srcs>
        for dst in dsts_nrm:
            if os.path.exists(dst):
                if not any((os.path.samefile(src, dst) for src in srcs_nrm)):
                    if os.path.isfile(dst):
                        raise FileExistsError(f"File '{dst}' from <dsts> should not exist!")
                    raise FileExistsError(f"Directory '{dst}' from <dsts> should not exist!")
            else:  # redundantly verifying if dir exists
                if not os.path.exists(os.path.dirname(dst)):
                    raise NotADirectoryError(f"Directory '{dst}' from <dsts> does not exist!")
    except:
        lock_manager.release_locks()
        raise
    #### continue only if locks were obtained
    if locks_err is not None:
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


def path_basename_to_lower(path: str, ignore_locks=False) -> str:
    """Rename <path> to a lowercase

    TODO:
        Add persisting lock for the target filename

    Imports:
        os

    Args:
        path (str): Path to rename to lowercase

    Returns:
        str: Newly renamed
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


def is_path_basename_lower(path: str) -> bool:
    path_cleaned = path_clean(path)
    basename = str(os.path.basename(path_cleaned))
    return basename == basename.lower()


def path_clean(path: str) -> str:
    """Clean <path> representation to give deterministic comparable representation

    Imports:
        os

    Args:
        path (str): Path to clean and return

    Returns:
        str: A clean path
    """
    return os.path.abspath(os.path.normpath(path))
