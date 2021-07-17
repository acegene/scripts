import errno
import os
import shutil
import uuid

from typing import Sequence

from gen_utils import is_filesystem_case_sensitive
from locks_manager import LocksManager

# https://www.programcreek.com/python/?code=lanbing510%2FGTDWeb%2FGTDWeb-master%2Fdjango%2Fcore%2Ffiles%2Fmove.py

def mv(src:str, dst:str, ignore_locks=False) -> None:
    """Atomically move object <src> to <dst> even across filesystems

    Avoids race conditions with programs that utilize advisory locking system (see LocksManager)

    https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python/

    TODO:
        directory contents are not locked, only the directory itself

    Imports:
        errno
        gen_utils.is_filesystem_case_sensitive # local import
        locks_manager.LocksManager # local import
        os
        shutil
        uuid

    Args:
        src (str): object to move
        dst (str): destination object to move <src> to

    Returns:
        None

    Raises:
        FileNotFoundError: if os.path.exists(<src>)
        FileExistsError: if os.path.exists(<dst>)
        NotADirectoryError: if the directory of <src> or <dst> does not exist
        PermissionError: if a lock could not be secured for <src> or <dst>
    """

    #### normalize inputs
    src_nrm = os.path.abspath(os.path.normpath(src))
    dst_nrm = os.path.abspath(os.path.normpath(dst))
    #### lock <src> and <dst> prior to interacting with them to avoid race condition
    locks_err = None
    try:
        if not ignore_locks:
            locks_manager = LocksManager(src_nrm, dst_nrm)
            locks_manager.create_locks()
    except PermissionError as err:
        locks_err = err
    except:
        locks_manager.release_locks()
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
            if os.path.samefile(src_nrm, dst_nrm): # works for dirs too
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
        locks_manager.release_locks()
        raise
    #### continue only if locks were obtained
    if locks_err != None:
        locks_manager.release_locks()
        raise locks_err
    #### execute mv
    try:
        try:
            os.rename(src_nrm, dst_nrm)
        except OSError as err:
            if err.errno == errno.EXDEV:
                #### generate unique ID
                copy_id = uuid.uuid4()
                #### cp <src> <tmp_dst> # cp across filesystems to tmp location
                tmp_dst = "%s.%s.tmp" % (dst_nrm, copy_id)
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
            locks_manager.release_locks()
        raise

def mv_multi(srcs:Sequence[str], dsts:Sequence[str]) -> None:
    """Move objects <srcs> to <dsts> even across filesystems

    Imports:
        errno
        locks_manager.LocksManager # local import
        os
        shutil
        uuid

    Args:
        srcs (Sequence[str]): objects to move
        dsts (Sequence[str]): destination objects to move <srcs> to

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
        raise ValueError('Inputs <srcs> and <dsts> should have the same length!')
    #### normalize inputs
    srcs_nrm = [str(os.path.abspath(os.path.normpath(src))) for src in srcs]
    dsts_nrm = [str(os.path.abspath(os.path.normpath(dst))) for dst in dsts]
    #### remove duplicates from <srcs> # TODO: handle when dirname does not exist
    srcs_unique = set()
    for src in srcs_nrm:
        dir_src = str(os.path.dirname(src))
        if not os.path.isdir(dir_src):
            raise NotADirectoryError("Directory for '%s' from <srcs> does not exist!" % (src))
        srcs_unique.add(src if is_filesystem_case_sensitive(dir_src) else src.lower())
    #### remove duplicates from <dsts>
    dsts_unique = set()
    for dst in dsts_nrm:
        dir_dst = str(os.path.dirname(dst))
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
        locks_manager = LocksManager(*set.union(srcs_unique, dsts_unique))
        locks_manager.create_locks()
    except PermissionError as err:
        locks_err = err
    except:
        locks_manager.release_locks()
        raise
    #### check that a mv_multi <srcs> to <dsts> is possible
    try:
        #### all of <srcs> must exist
        for src in srcs_nrm:
            if not os.path.exists(src):
                if os.path.exists(os.path.dirname(src)):
                    raise FileNotFoundError("File or directory '%s' from <srcs> does not exist!" % (src))
                else: # redundantly verifying if dir exists
                    raise NotADirectoryError("Directory '%s' from <srcs> does not exist!" % (src))
        #### all of <dsts> must not exist unless also part of <srcs>
        for dst in dsts_nrm:
            if os.path.exists(dst):
                if not any((os.path.samefile(src, dst) for src in srcs_nrm)):
                    if os.path.isfile(dst):
                        raise FileExistsError("File '%s' from <dsts> should not exist!" % (dst))
                    else:
                        raise FileExistsError("Directory '%s' from <dsts> should not exist!" % (dst))
            else: # redundantly verifying if dir exists
                if not os.path.exists(os.path.dirname(dst)):
                    raise NotADirectoryError("Directory '%s' from <dsts> does not exist!" % (dst))
    except:
        locks_manager.release_locks()
        raise
    #### continue only if locks were obtained
    if locks_err != None:
        raise locks_err
    #### execute mv_multi
    try:
        #### generate unique ID and create <tmp_dsts> from <dsts> and ID
        copy_id = uuid.uuid4()
        tmp_dsts = ["%s.%s.tmp" % (dst, copy_id) for dst in dsts_nrm]
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
        locks_manager.release_locks()
        raise
