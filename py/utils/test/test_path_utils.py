# type: ignore # TODO

import errno
import os
import sys
import unittest
import unittest.mock

from pyfakefs.fake_filesystem_unittest import TestCase  # pip install pyfakefs

try:
    from utils import path_utils
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils import path_utils

# TODO: allow to be ran from any dir

unmocked_os_rename = path_utils.os.rename


class mock_os_rename_fail_once:
    num_os_rename_calls = 0
    num_os_rename_raises = 0

    def __init__(self):
        pass

    def __call__(self, old, new):
        self.num_os_rename_calls += 1
        if self.num_os_rename_raises >= self.num_os_rename_calls:
            raise OSError(errno.EXDEV, "")
        else:
            unmocked_os_rename(old, new)


class TestMv(TestCase):
    def setUp(self):
        setattr(mock_os_rename_fail_once, "num_os_rename_calls", 0)
        setattr(mock_os_rename_fail_once, "num_os_rename_raises", 0)
        self.setUpPyfakefs()
        self.dir = "/test/"
        self.create_dirs(self.dir)
        self.old = self.dir + "old.txt"
        self.new = self.dir + "new.txt"

    def create_dirs(self, *dirs):
        for d in dirs:
            self.assertFalse(os.path.exists(d))
            self.fs.create_dir(d)
            self.assertTrue(os.path.exists(d))

    def create_files(self, *files):
        for f in files:
            self.assertFalse(os.path.exists(f))
            self.fs.create_file(f)
            self.assertTrue(os.path.exists(f))

    def assert_exists(self, num_files, num_dirs, *objects):
        counted_files = 0
        counted_dirs = 0
        for base, dirs, files in os.walk(self.dir):
            for fs in files:
                counted_files += 1
            for ds in dirs:
                counted_dirs += 1
        self.assertTrue(counted_files == num_files, "%s != %s" % (counted_files, num_files))
        self.assertTrue(counted_dirs == num_dirs, "%s != %s" % (counted_dirs, num_dirs))
        for obj in objects[:counted_files]:
            self.assertTrue(os.path.isfile(obj), "File '%s' should exist!" % (obj))
        for obj in objects[counted_files:]:
            self.assertTrue(os.path.isdir(obj), "Dir '%s' should exist!" % (obj))
        self.assertTrue((num_files + num_dirs) == len(objects), "(%s + %s) != len(%s)" % (num_files, num_dirs, objects))

    def test__mv__file_base_case__success(self):
        self.create_files(self.old)
        path_utils.mv(self.old, self.new)
        self.assert_exists(1, 0, self.new)

    def test__mv__file_old_relative__success(self):
        os.chdir(self.dir)
        self.old = "old.txt"
        self.create_files(self.old)
        path_utils.mv(self.old, self.new)
        self.assert_exists(1, 0, self.new)

    def test__mv__file_new_relative__success(self):
        os.chdir(self.dir)
        self.new = "new.txt"
        self.create_files(self.old)
        path_utils.mv(self.old, self.new)
        self.assert_exists(1, 0, self.new)

    def test__mv__file_new_is_relative_old__raise_file_exists(self):
        os.chdir(self.dir)
        self.new = "old.txt"
        self.create_files(self.old)
        self.assertRaises(FileExistsError, path_utils.mv, self.old, self.new)
        self.assert_exists(1, 0, self.old)

    def test__mv__file_old_lock_exists__raise_permission(self):
        old_lock = self.old + ".lock"
        self.create_files(self.old, old_lock)
        self.assertRaises(PermissionError, path_utils.mv, self.old, self.new)
        self.assert_exists(2, 0, self.old, old_lock)

    def test__mv__file_new_lock_exists__raise_permission(self):
        new_lock = self.new + ".lock"
        self.create_files(self.old, new_lock)
        self.assertRaises(PermissionError, path_utils.mv, self.old, self.new)
        self.assert_exists(2, 0, self.old, new_lock)

    def test__mv__old_lock_exists_new_lock_exists__raise_permission(self):
        old_lock = self.old + ".lock"
        new_lock = self.new + ".lock"
        self.create_files(self.old, old_lock, new_lock)
        self.assertRaises(PermissionError, path_utils.mv, self.old, self.new)
        self.assert_exists(3, 0, self.old, old_lock, new_lock)

    def test__mv__file_ignore_locks_old_lock_exists__success(self):
        old_lock = self.old + ".lock"
        self.create_files(self.old, old_lock)
        path_utils.mv(self.old, self.new, ignore_locks=True)
        self.assert_exists(2, 0, self.new, old_lock)

    def test__mv__file_ignore_locks_new_lock_exists__success(self):
        new_lock = self.new + ".lock"
        self.create_files(self.old, new_lock)
        path_utils.mv(self.old, self.new, ignore_locks=True)
        self.assert_exists(2, 0, self.new, new_lock)

    def test__mv__file_old_not_exists__raise_file_not_found(self):
        self.assertRaises(FileNotFoundError, path_utils.mv, self.old, self.new)
        self.assert_exists(0, 0)

    def test__mv__file_new_exists__raise_file_exists(self):
        self.create_files(self.old, self.new)
        self.assertRaises(FileExistsError, path_utils.mv, self.old, self.new)
        self.assert_exists(2, 0, self.old, self.new)

    def test__mv__file_old_not_exist_new_exists__raise_file_exists(self):
        self.create_files(self.new)
        self.assertRaises(FileNotFoundError, path_utils.mv, self.old, self.new)
        self.assert_exists(1, 0, self.new)

    def test__mv__file_new_is_old__raise_file_exists(self):
        self.new = self.old
        self.create_files(self.old)
        self.assertRaises(FileExistsError, path_utils.mv, self.old, self.new)
        self.assert_exists(1, 0, self.old)

    def test__mv__file_old_dir_not_exists__raise_not_a_directory(self):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.create_dirs(dir_2)
        self.old = dir_1 + "old.txt"
        self.new = dir_2 + "new.txt"
        self.assertRaises(NotADirectoryError, path_utils.mv, self.old, self.new)
        self.assert_exists(0, 1, dir_2)

    def test__mv__file_new_dir_not_exists__raise_not_a_directory(self):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.create_dirs(dir_1)
        self.old = dir_1 + "old.txt"
        self.new = dir_2 + "new.txt"
        self.create_files(self.old)
        self.assertRaises(NotADirectoryError, path_utils.mv, self.old, self.new)
        self.assert_exists(1, 1, self.old, dir_1)

    def test__mv__file_old_dir_not_exists_new_dir_not_exists__raise_not_a_directory(self):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.old = dir_1 + "old.txt"
        self.new = dir_2 + "new.txt"
        self.assertRaises(NotADirectoryError, path_utils.mv, self.old, self.new)
        self.assert_exists(0, 0)

    def test__mv__dir_base_case__success(self):
        self.old = self.dir + "old_dir/"
        self.new = self.dir + "new_dir/"
        old_files = [self.old + "file_" + str(i) for i in range(11)]
        new_files = [self.new + "file_" + str(i) for i in range(11)]
        self.create_dirs(self.old)
        self.create_files(*old_files)
        path_utils.mv(self.old, self.new)
        self.assert_exists(11, 1, *new_files, self.new)

    def test__mv__dir_new_exist__raise_file_exists(self):
        self.old = self.dir + "old_dir/"
        self.new = self.dir + "new_dir/"
        self.create_dirs(self.old, self.new)
        self.assertRaises(FileExistsError, path_utils.mv, self.old, self.new)
        self.assert_exists(0, 2, self.old, self.new)

    def test__mv__dir_new_file_exists__raise_file_exists(self):
        self.old = self.dir + "old_dir/"
        self.new = self.dir + "new.txt"
        self.create_dirs(self.old)
        self.create_files(self.new)
        self.assertRaises(FileExistsError, path_utils.mv, self.old, self.new)
        self.assert_exists(1, 1, self.new, self.old)

    def test__mv__dir_empty__success(self):
        self.old = self.dir + "old_dir/"
        self.new = self.dir + "new_dir/"
        self.create_dirs(self.old)
        path_utils.mv(self.old, self.new)
        self.assert_exists(0, 1, self.new)

    def test__mv__dir_new_dir_not_exist__raise_not_a_directory(self):
        self.old = self.dir + "old_dir/"
        dir_out = self.dir + "dir_out/"
        self.new = dir_out + "new_dir"
        self.create_dirs(self.old)
        self.assertRaises(NotADirectoryError, path_utils.mv, self.old, self.new)
        self.assert_exists(0, 1, self.old)

    @unittest.mock.patch("utils.path_utils.os.rename", side_effect=mock_os_rename_fail_once())
    def test__mv__file_across_fs__success(self, mock_os_rename_):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.create_dirs(dir_1, dir_2)
        self.old = dir_1 + "old.txt"
        self.new = dir_2 + "new.txt"
        self.create_files(self.old)
        setattr(mock_os_rename_fail_once, "num_os_rename_raises", 1)
        path_utils.mv(self.old, self.new)
        self.assert_exists(1, 2, self.new, dir_1, dir_2)

    @unittest.mock.patch("utils.path_utils.os.rename", side_effect=mock_os_rename_fail_once())
    def test__mv__dir_across_fs__success(self, mock_os_rename_):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.old = dir_1 + "old_dir/"
        self.new = dir_2 + "new_dir/"
        self.create_dirs(dir_1, dir_2, self.old)
        old_files = [self.old + "file_" + str(i) for i in range(11)]
        new_files = [self.new + "file_" + str(i) for i in range(11)]
        self.create_files(*old_files)
        setattr(mock_os_rename_fail_once, "num_os_rename_raises", 1)
        path_utils.mv(self.old, self.new)
        self.assert_exists(11, 3, *new_files, dir_1, dir_2, self.new)


class TestMvMulti(TestCase):
    def setUp(self):
        setattr(mock_os_rename_fail_once, "num_os_rename_calls", 0)
        setattr(mock_os_rename_fail_once, "num_os_rename_raises", 0)
        self.setUpPyfakefs()
        self.dir = "/test/"
        self.create_dirs(self.dir)
        self.old = [self.dir + "old_" + str(i) + ".txt" for i in range(11)]
        self.new = [self.dir + "new_" + str(i) + ".txt" for i in range(11)]

    def create_dirs(self, *dirs):
        for d in dirs:
            self.assertFalse(os.path.exists(d))
            self.fs.create_dir(d)
            self.assertTrue(os.path.exists(d))

    def create_files(self, *files):
        for f in files:
            self.assertFalse(os.path.exists(f))
            self.fs.create_file(f)
            self.assertTrue(os.path.exists(f))

    def assert_exists(self, num_files, num_dirs, *objects):
        counted_files = 0
        counted_dirs = 0
        for base, dirs, files in os.walk(self.dir):
            for fs in files:
                counted_files += 1
            for ds in dirs:
                counted_dirs += 1
        self.assertTrue(counted_files == num_files, "%s != %s" % (counted_files, num_files))
        self.assertTrue(counted_dirs == num_dirs, "%s != %s" % (counted_dirs, num_dirs))
        for obj in objects[:counted_files]:
            self.assertTrue(os.path.isfile(obj), "File '%s' should exist!" % (obj))
        for obj in objects[counted_files:]:
            self.assertTrue(os.path.isdir(obj), "Dir '%s' should exist!" % (obj))
        self.assertTrue((num_files + num_dirs) == len(objects), "(%s + %s) != len(%s)" % (num_files, num_dirs, objects))

    def test__mv_multi__files_base_case__success(self):
        self.create_files(*self.old)
        path_utils.mv_multi(self.old, self.new)
        self.assert_exists(11, 0, *self.new)

    def test__mv_multi__files_old_relative__success(self):
        os.chdir(self.dir)
        self.old = ["old_" + str(i) + ".txt" for i in range(11)]
        self.create_files(*self.old)
        path_utils.mv_multi(self.old, self.new)
        self.assert_exists(11, 0, *self.new)

    def test__mv_multi__files_new_relative__success(self):
        os.chdir(self.dir)
        self.new = ["new_" + str(i) + ".txt" for i in range(11)]
        self.create_files(*self.old)
        path_utils.mv_multi(self.old, self.new)
        self.assert_exists(11, 0, *self.new)

    def test__mv_multi__files_new_is_relative_old__success(self):
        os.chdir(self.dir)
        self.new = ["old_" + str(i) + ".txt" for i in range(11)]
        self.create_files(*self.old)
        path_utils.mv_multi(self.old, self.new)
        self.assert_exists(11, 0, *self.old)

    def test__mv_multi__files_old_lock_exists__raise_permission(self):
        old_lock = self.old[-1] + ".lock"
        self.create_files(*self.old, old_lock)
        self.assertRaises(PermissionError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(12, 0, *self.old, old_lock)

    def test__mv_multi__files_new_lock_exists__raise_permission(self):
        new_lock = self.new[-1] + ".lock"
        self.create_files(*self.old, new_lock)
        self.assertRaises(PermissionError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(12, 0, *self.old, new_lock)

    def test__mv_multi__files_old_lock_exists_new_lock_exists__raise_permission(self):
        old_lock = self.old[-1] + ".lock"
        new_lock = self.new[-1] + ".lock"
        self.create_files(*self.old, old_lock, new_lock)
        self.assertRaises(PermissionError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(13, 0, *self.old, old_lock, new_lock)

    def test__mv_multi__files_old_not_exists__raise_file_not_found(self):
        self.create_files(*self.old[:-1])
        self.assertRaises(FileNotFoundError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(10, 0, *self.old[:-1])

    def test__mv_multi__files_new_exists__raise_file_exists(self):
        self.create_files(*self.old, self.new[0])
        self.assertRaises(FileExistsError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(12, 0, *self.old, self.new[0])

    def test__mv_multi__files_old_not_exists_new_exists__raise_file_exists(self):
        self.create_files(self.new[0])
        self.assertRaises(FileNotFoundError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(1, 0, self.new[0])

    def test__mv_multi__files_new_relative_path_old__success(self):
        os.chdir(self.dir)
        self.new = ["old_" + str(i) + ".txt" for i in range(11)]
        self.create_files(*self.old)
        path_utils.mv_multi(self.old, self.new)
        self.assert_exists(11, 0, *self.old)

    def test__mv_multi__files_old_dir_not_exists__raise_not_a_directory(self):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.create_dirs(dir_2)
        self.old = [dir_1 + "old_" + str(i) + ".txt" for i in range(11)]
        self.new = [dir_2 + "new_" + str(i) + ".txt" for i in range(11)]
        self.assertRaises(NotADirectoryError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(0, 1, dir_2)

    def test__mv_multi__files_new_dir_not_exists__raise_not_a_directory(self):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.create_dirs(dir_1)
        self.old = [dir_1 + "old_" + str(i) + ".txt" for i in range(11)]
        self.new = [dir_2 + "new_" + str(i) + ".txt" for i in range(11)]
        self.create_files(*self.old)
        self.assertRaises(NotADirectoryError, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(11, 1, *self.old, dir_1)

    def test__mv_multi__files_old_not_unique__raise_value(self):
        self.create_files(*self.old)
        self.assertRaises(ValueError, path_utils.mv_multi, self.old + [self.old[0]], self.new)
        self.assert_exists(11, 0, *self.old)

    def test__mv_multi__files_new_not_unique__raise_value(self):
        self.create_files(*self.old)
        self.assertRaises(ValueError, path_utils.mv_multi, self.old, self.new + [self.new[0]])
        self.assert_exists(11, 0, *self.old)

    def test__mv_multi__files_switch_old_and_new__success(self):
        self.old = [self.dir + str(i) + ".txt" for i in [1, 2, 3]]
        self.new = [self.dir + str(i) + ".txt" for i in [3, 2, 1]]
        self.create_files(*self.old)
        path_utils.mv_multi(self.old, self.new)
        self.assert_exists(3, 0, *self.new)


if __name__ == "__main__":
    unittest.main()
