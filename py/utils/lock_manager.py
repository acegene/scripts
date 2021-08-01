# lock_manager.py
#
# brief:  python module for the class 'LockManager'
#
# usage:  * from utils.lock_manager import LockManager
#         * lock_manager = LockManager(files_to_lock)
#
# author: acegene <acegene22@gmail.com>

import os

from typing import Union

import filelock  # pip install filelock

PathLike = Union[str, bytes, os.PathLike]


class LockManager:
    "Path object advisory locking with rigid behavior to faciliate synchronization of components using this manager"

    def __init__(self, *objects: PathLike):
        self.locks = [filelock.SoftFileLock(f"{obj}.lock") for obj in objects]

    def create_locks(self) -> None:
        """Attempt to obtain each lock in <self.locks>"""
        for lock in self.locks:
            try:
                lock.acquire(timeout=0.1)
            except:
                [lock.release() for lock in self.locks]
                raise PermissionError(f"Could not obtain lock '{lock.lock_file}'")

    def release_locks(self) -> None:
        """Release each lock in <self.locks>"""
        for lock in self.locks:
            lock.release()
