# Python module for tools related to path objects
#
# usage
#   * from utils import path_utils
#       * adding this to a python file allows usage of functions as path_utils.func()
#
# author: acegene <acegene22@gmail.com>
import errno
import logging
import os
import pathlib
import shutil
import tempfile
import uuid
from collections.abc import Sequence
from typing import Any
from typing import BinaryIO
from typing import TextIO

from utils import python_utils
from utils.lock_manager import LockManager

# https://www.programcreek.com/python/?code=lanbing510%2FGTDWeb%2FGTDWeb-master%2Fdjango%2Fcore%2Ffiles%2Fmove.py

# path_this = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
# dir_this = os.path.dirname(path_this)
# base_this = os.path.basename(path_this)


logger = logging.getLogger(__name__)


def generate_tmp_from_path(path: str):
    """Generate and return temporary unique pathname from <path>

    Args:
        path: Path to generate output tmp path from

    Returns:
        Path that has been added unique content
    """
    #### generate unique ID
    copy_id = uuid.uuid4()
    #### cp <src> <tmp_dst> # cp across filesystems to tmp location
    return f"{path}.{copy_id}.tmp"


def is_filesystem_case_sensitive(dir_: str = ".") -> bool:
    """Check whether <dir_> is part of a case sensitive filesystem.

    Args:
        dir_: Directory that is being tested for case sensitivity

    Returns:
        True if filesystem for <dir_> is case sensitive

    See Also:
        https://stackoverflow.com/a/36580834/10630957

    Warnings:
        Requires write access to <dir_>
    """
    try:
        return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]  # type: ignore[attr-defined, no-any-return]
    except AttributeError:
        setattr(is_filesystem_case_sensitive, "case_sensitive_dir_dict", {})
    except KeyError:
        pass
    with tempfile.NamedTemporaryFile(prefix="TmP", dir=dir_) as tmp_file:
        is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_] = not os.path.exists(tmp_file.name.lower())  # type: ignore[attr-defined] # pylint: disable=[no-member]
        return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]  # type: ignore[attr-defined, no-any-return] # pylint: disable=[no-member]


def _mv_raise_if_paths_not_correct_status(src: str, dst: str, overwrite: bool = False) -> None:
    if not os.path.exists(src):
        if os.path.exists(os.path.dirname(src)):
            raise FileNotFoundError(f"File or directory '{src}' aka <src> does not exist!")
        raise NotADirectoryError(f"Directory for '{src}' aka <src> does not exist!")
    #### <dst> must not exist if not <overwrite>
    if not overwrite and os.path.exists(dst):
        if os.path.samefile(src, dst):  # works for dirs too
            if os.path.isfile(dst):
                raise FileExistsError(f"Files '{src}' == '{dst}' aka <src> == <dst>")
            raise FileExistsError(f"Directories '{src}' == '{dst}' aka <src> == <dst>")
        if os.path.isfile(dst):
            raise FileExistsError(f"File '{dst}' aka <dst> should not exist!")
        raise FileExistsError(f"Directory '{dst}' aka <dst> should not exist!")
    dir_dst = os.path.dirname(dst)
    if not os.path.exists(dir_dst):
        raise NotADirectoryError(f"Directory '{dir_dst}' for '{dst}' aka <dst> does not exist!")


def mv(src: str, dst: str, /, ignore_locks: bool = False, overwrite: bool = False) -> None:
    """Atomically move object <src> to <dst> even across filesystems.

    Avoids race conditions with programs that utilize advisory locking system (see LockManager)

    Args:
        src: Object to move
        dst: Destination object to move <src> to
        ignore_locks: Useful if locks are managed external to this function

    Returns:
        None

    Raises:
        FileNotFoundError: if os.path.exists(<src>)
        FileExistsError: if os.path.exists(<dst>)
        NotADirectoryError: if the directory of <src> or <dst> does not exist
        PermissionError: if a lock could not be secured for <src> or <dst>

    See Also:
        https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python/

    TODO:
        - directory contents are not locked, only the directory itself
        - how to handle overwrite when src is file but dst is dir
    """

    # pylint: disable=[too-many-branches,too-many-statements]
    #### normalize inputs
    src_nrm = path_clean(src)
    dst_nrm = path_clean(dst)
    files_nrm = {dst_nrm, src_nrm}
    ### check that a mv <src> to <dst> is possible
    _mv_raise_if_paths_not_correct_status(src_nrm, dst_nrm, overwrite=overwrite)
    #### lock <src> and <dst> prior to interacting with them to avoid race condition
    lock_files = () if ignore_locks else files_nrm
    with LockManager(*lock_files):
        ### check that a mv <src> to <dst> is possible, redundantly now that locks obtained
        _mv_raise_if_paths_not_correct_status(src_nrm, dst_nrm, overwrite=overwrite)
        #### execute mv
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


def mv_multi(srcs: Sequence[str], dsts: Sequence[str]) -> None:
    """Move objects <srcs> to <dsts> even across filesystems.

    Args:
        srcs: Objects to move
        dsts: Destination objects to move <srcs> to

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
    srcs_nrm = tuple(path_clean(src) for src in srcs)
    dsts_nrm = tuple(path_clean(dst) for dst in dsts)
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
    with LockManager(*set.union(set(srcs_nrm), set(dsts_nrm))):
        #### check that a mv_multi <srcs> to <dsts> is possible
        ## all of <srcs> must exist
        for src in srcs_nrm:
            if not os.path.exists(src):
                if os.path.exists(os.path.dirname(src)):
                    raise FileNotFoundError(f"File or directory '{src}' from <srcs> does not exist!")
                # redundantly verifying if dir exists
                raise NotADirectoryError(f"Directory '{src}' from <srcs> does not exist!")
        ## all of <dsts> must not exist unless also part of <srcs>
        for dst in dsts_nrm:
            if os.path.exists(dst):
                if not any(os.path.samefile(src, dst) for src in srcs_nrm):
                    if os.path.isfile(dst):
                        raise FileExistsError(f"File '{dst}' from <dsts> should not exist!")
                    raise FileExistsError(f"Directory '{dst}' from <dsts> should not exist!")
            else:  # redundantly verifying if dir exists
                if not os.path.exists(os.path.dirname(dst)):
                    raise NotADirectoryError(f"Directory '{dst}' from <dsts> does not exist!")
        #### execute mv_multi
        ## generate <tmp_dsts> from <dsts_nrm>
        tmp_dsts = [generate_tmp_from_path(dst) for dst in dsts_nrm]
        ## perform mv(srcs, tmp_dsts)
        for src, tmp_dst, dst in zip(srcs_nrm, tmp_dsts, dsts_nrm):
            if os.path.exists(dst):
                continue  # TODO: should this happen?
            mv(src, tmp_dst, ignore_locks=True)
        ## perform mv(tmp_dsts, dsts)
        for src, tmp_dst, dst in zip(srcs_nrm, tmp_dsts, dsts_nrm):
            if os.path.exists(dst):
                continue  # TODO: should this happen?
            mv(tmp_dst, dst, ignore_locks=True)


def path_basename_to_lower(path: str, ignore_locks: bool = False) -> str:
    """Rename <path> to lowercase.

    Args:
        path: Path to rename to lowercase

    Returns:
        <path> to rename wioth basename as lowercase

    TODO:
        Add persisting lock for the target filename
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
    """Clean <path> representation to give deterministic comparable representation.

    Args:
        path: Path to clean and return

    Returns:
        Cleaned path

    TODO:
        Consider how normpath does not resolve symlinks
    """
    # return os.path.abspath(os.path.normpath(path))
    return str(pathlib.Path(path).resolve(strict=False))


def path_as_posix_if_windows(path):
    return path_windows_to_posix(path) if python_utils.is_os_windows() else path


def path_posix_to_windows(path):
    return pathlib.PureWindowsPath(pathlib.PurePosixPath(path))


def path_windows_to_posix(path):
    return path.replace("\\", "/")


#### File content interactions

LE_CR_B = b"\r"
LE_CRLF_B = b"\r\n"
LE_LF_B = b"\n"
LINE_ENDINGS_B = (LE_CR_B, LE_CRLF_B, LE_LF_B)


def append_missing_lines_to_file(file, lines, is_windows=False, check_only: bool = False):
    if not os.path.exists(file):
        if check_only:
            logger.info(f"file does not exist: {file}")
            return False
        if is_windows:
            open(file, "a", encoding="utf-8").close()  # pylint: disable=consider-using-with
        else:
            open_unix_safely(file, "a").close()
        logger.info(f"created {file}")

    missing_line = False
    open_wrapper = lambda is_windows: (
        open(file, "r+", encoding="utf-8")  # pylint: disable=consider-using-with
        if is_windows
        else open_unix_safely(file, "r+")
    )
    with open_wrapper(is_windows) as f:
        content = f.read()
        prepend_nl_necessary = content and not content.endswith("\n")
        for line in lines:
            if line not in content:
                if check_only:
                    logger.info(f"file={file} is missing line={line}")
                    missing_line = True
                else:
                    if prepend_nl_necessary:
                        prepend_nl_necessary = False
                        f.write("\n")
                    f.write(line + "\n")
                    logger.info(f"wrote to file={file} line={line}")
    return not missing_line


def cp_with_replace(src: str, dst: str, replacements: Sequence[tuple[str, str]], check_only: bool = False) -> bool:
    if check_only is True and not os.path.exists(dst):
        logger.info(f"file={dst} does not exist")
        return False

    with open_unix_safely(src, "r") as f:
        content = f.read()

    for orig_str, repl_str in replacements:
        content = content.replace(orig_str, repl_str)

    if check_only:
        with open_unix_safely(dst, "r") as f:
            dst_content = f.read()
            if content != dst_content:
                logger.info(f"src={src} does not match dst={dst}")
                return False
    else:
        with open_unix_safely(dst, "w") as f:
            f.write(content)
    return True


def eol_str_to_bin_str(str_in: bytes | str) -> bytes:
    if str_in in LINE_ENDINGS_B:
        return str_in  # type: ignore[return-value]
    if str_in == "cr":
        return LE_CR_B
    if str_in == "crlf":
        return LE_CRLF_B
    if str_in == "lf":
        return LE_LF_B
    raise ValueError("<eol> must be specified as one of ['cr', 'crlf', 'lf'].")


def file_as_eol_lf(src_file, dst_file=None, /, chunk_size=4096):
    """Converts all types of eol (CRLF, CR) to LF. If <dst_file> is not provided, overwrite <src_file> in place.

    :param src_file: Path to the file which may contain mixed eol.
    :param dst_file: Optional; Path to the write file with LF only line endings.
    """
    if dst_file is None:
        temp_fd, temp_path = tempfile.mkstemp()
        try:
            with open(src_file, "rb") as src, os.fdopen(temp_fd, "wb") as tgt:
                write_src_to_tgt_as_eol_lf_using_chunks(src, tgt, chunk_size)
            os.replace(temp_path, src_file)
        except Exception as e:
            os.remove(temp_path)
            raise e
    else:
        with open(src_file, "rb") as src, open(dst_file, "wb") as tgt:
            write_src_to_tgt_as_eol_lf_using_chunks(src, tgt, chunk_size)


def is_file_content_equal(lhs, rhs, chunk_size=4096):
    """Compare two files in a binary mode chunk by chunk.

    Args:
        lhs: Path to the first file.
        rhs: Path to the second file.
        chunk_size: The size of each chunk to read, default 4096 bytes.

    Returns:
        True if file content is the same
    """
    with open(lhs, "rb") as lhs_f, open(rhs, "rb") as rhs_f:
        while True:
            lhs_chunk = lhs_f.read(chunk_size)
            rhs_chunk = rhs_f.read(chunk_size)
            if lhs_chunk != rhs_chunk:
                return False
            if not lhs_chunk and not rhs_chunk:
                return True


def open_unix_safely(
    path: str,
    mode: str = "r",
    buffering: int = -1,
    encoding: str | None = "utf-8",
    correct_eol: bool = False,
    chunk_size=4096,
    **kwargs: Any,
) -> TextIO:
    """Open a file with UTF-8 encoding and a specified newline character, allowing overrides.

    Args:
        path: Path to the file.
        mode: The mode in which the file is opened.
        buffering: Buffering policy (-1 to use default buffering).
        encoding: Encoding for the file.
        **kwargs: Additional arguments to pass to the built-in open function.

    Returns:
        The file object.
    """
    # pylint: disable=[too-many-arguments]
    if os.path.exists(path):
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                file_as_eol_lf(path, tmp_file.name, chunk_size)
                if not is_file_content_equal(path, tmp_file.name, chunk_size):
                    if correct_eol:
                        mv(tmp_file.name, path, overwrite=True)
                        logger.warning("Newlines needed adjusting to lf for path=%s", path)
                    else:
                        raise ValueError(f"Unexpected newlines in path={path}")
        finally:
            if tmp_file and os.path.exists(str(tmp_file)):
                os.unlink(str(tmp_file))
    assert "b" not in mode, mode
    forbidden_keywords = {"closefd", "errors", "newline"}
    assert not any(key in kwargs for key in forbidden_keywords), kwargs
    return open(path, mode=mode, buffering=buffering, encoding=encoding, errors="strict", newline="\n", **kwargs)  # type: ignore[return-value]


def replace_eol_bin(bin_str: bytes, eol: bytes | str = LE_LF_B) -> bytes:
    #### https://stackoverflow.com/questions/47178459/replace-crlf-with-lf-in-python-3-6
    #### https://gist.github.com/jonlabelle/dd8c3caa7808cbe4cfe0a47ee4881059
    #### check eol
    eol_nrm = eol_str_to_bin_str(eol)
    #### modify line endings of file's content
    if eol_nrm == LE_CR_B:
        bin_str_out = bin_str.replace(LE_CRLF_B, LE_LF_B).replace(LE_LF_B, LE_CR_B)
    elif eol_nrm == LE_CRLF_B:
        bin_str_out = bin_str.replace(LE_CRLF_B, LE_LF_B).replace(LE_CR_B, LE_LF_B).replace(LE_LF_B, LE_CRLF_B)
    elif eol_nrm == LE_LF_B:
        bin_str_out = bin_str.replace(LE_CRLF_B, LE_LF_B).replace(LE_CR_B, LE_LF_B)
    else:
        raise ValueError(f"Unhandled input '{eol_nrm!r}'.")
    #### return modified string
    return bin_str_out


def write_src_to_tgt_as_eol_lf_using_chunks(src: BinaryIO, tgt: BinaryIO, chunk_size=4096) -> None:
    """Read from src and write to tgt and force all eol to lf. Handles large files and chunk boundary edge cases.

    :param src: Source file object opened in binary mode for reading.
    :param tgt: Target file object opened in binary mode for writing.
    """
    previous_end_cr = False  # To handle '\r' at the end of a chunk

    while True:
        chunk = src.read(chunk_size)
        if not chunk:
            break
        # handle CRLF spread across chunk boundaries
        if previous_end_cr and chunk.startswith(LE_LF_B):
            chunk = chunk[1:]
        previous_end_cr = chunk.endswith(LE_CR_B)
        chunk = replace_eol_bin(chunk, LE_LF_B)
        tgt.write(chunk)
