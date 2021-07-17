import filelock # pip install filelock

class LocksManager():
    def __init__(self, *objects):
        self.locks = [filelock.SoftFileLock(obj + '.lock') for obj in objects]

    def create_locks(self):
        #### attempt to create <self.locks>
        for lock in self.locks:
            try:
                lock.acquire(timeout=0.1)
            except:
                [lock.release() for lock in self.locks]
                raise PermissionError("Could not obtain lock '%s'" % (lock.lock_file))

    def release_locks(self):
        #### attempt to release <self.locks>
        for lock in self.locks:
            lock.release()
