# Python module for the class 'LockManager'
#
# usage
#   * from utils.lock_manager import LockManager
#   * lock_manager = LockManager(files_to_lock)
#
# author: acegene <acegene22@gmail.com>
import logging

import filelock  # python3 -m pip install filelock


class LockManager:
    "Path object advisory locking with rigid behavior to faciliate synchronization of components using this manager"

    def __init__(self, /, *objects: str, timeout: float = 0.1, log_lvl: str = "INFO"):
        # TODO: multiple modules importing this lib (or even multiple instantiations) can overwrite eachothers log_lvl?
        logging.getLogger("filelock").setLevel(getattr(logging, log_lvl))
        self.lock_names = LockManager.get_lock_file_names(*objects)
        self.locks = tuple(filelock.SoftFileLock(lock_name) for lock_name in self.lock_names)
        self.timeout = timeout

    def __enter__(self, timeout=None):
        if timeout is None:
            timeout = self.timeout
        for context in self.locks:
            context.acquire(timeout=timeout)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for context in reversed(self.locks):
            context.__exit__(exc_type, exc_value, traceback)

    @staticmethod
    def get_lock_file_names(*objects):
        return tuple(f"{obj}.lock" for obj in objects)

    def create_locks(self, timeout=None) -> None:
        """Attempt to obtain each lock in <self.locks>"""
        if timeout is None:
            timeout = self.timeout
        for lock in self.locks:
            try:
                lock.acquire(timeout=timeout)
            except Exception:
                self.release_locks()
                raise

    def release_locks(self) -> None:
        """Release each lock in <self.locks>"""
        for lock in self.locks:
            lock.release()
