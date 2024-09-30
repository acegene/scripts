import errno
import os
import tempfile
import unittest.mock

import filelock
import pyfakefs.fake_filesystem_unittest  # python3 -m pip install pyfakefs
from parameterized import parameterized  # type: ignore[import-untyped]
from utils import path_utils


class TestFileAsEolLf(unittest.TestCase):
    @parameterized.expand(
        [
            # fmt: off
            (b"", b""),
            (b"Hello World", b"Hello World"),
            (b"Hello World\r", b"Hello World\n"),
            (b"Hello World\r\n", b"Hello World\n"),
            (b"Hello World\n", b"Hello World\n"),
            (b"Hello\r\nWorld\r\n", b"Hello\nWorld\n"),
            (b"\n".join([b"Line" + bytes(str(i), 'utf-8') for i in range(10000)]), b"\n".join([b"Line" + bytes(str(i), 'utf-8') for i in range(10000)])),
            (b"Unicode \xe2\x98\x83\r\n", b"Unicode \xe2\x98\x83\n"),
            (b"\r\n\r\r\n\nHello\r\n\r\r\n\nWorld\r\n\r\r\n\n", b"\n\n\n\nHello\n\n\n\nWorld\n\n\n\n"),
            ((b"a" * (4096 - 1) + b"\r") + (b"\n" + b"b" * (4096 - 1)), b"a" * (4096 - 1) + b"\n" + b"b" * (4096 - 1)),
            ((b"Hello\r\n" * 2048) + b"World", (b"Hello\n" * 2048) + b"World"),
            (b"Random\xe2\x98\x83DataWith\xc3\xa9Breaks\rMixedIn\n", b"Random\xe2\x98\x83DataWith\xc3\xa9Breaks\nMixedIn\n"),
            # fmt: on
        ],
    )
    def test_file_as_eol_lf(self, src_str_bin: bytes, expected_tgt_str_bin: bytes, chunk_max_size: int = 4096) -> None:
        chunk_size = chunk_max_size
        while chunk_size > 0:
            with tempfile.TemporaryDirectory() as tmp_dir:
                src_path = os.path.join(tmp_dir, "src.txt")
                dst_path = os.path.join(tmp_dir, "dst.txt")

                with open(src_path, "wb") as f:
                    f.write(src_str_bin)

                path_utils.file_as_eol_lf(src_path, dst_path, chunk_size)

                with open(dst_path, "rb") as f:
                    content = f.read()
                    self.assertEqual(expected_tgt_str_bin, content)

            with tempfile.TemporaryDirectory() as tmp_dir:
                src_path = os.path.join(tmp_dir, "src.txt")

                with open(src_path, "wb") as f:
                    f.write(src_str_bin)

                path_utils.file_as_eol_lf(src_path, chunk_size=chunk_size)

                with open(src_path, "rb") as f:
                    content = f.read()
                    self.assertEqual(expected_tgt_str_bin, content)
            chunk_size -= 1


class TestOpenUnixTxtSafely(unittest.TestCase):
    @parameterized.expand(
        [
            # fmt: off
            (b"", b""),
            (b"Hello World", b"Hello World"),
            (b"Hello World\r", b"Hello World\n", ValueError),
            (b"Hello World\r\n", b"Hello World\n", ValueError),
            (b"Hello World\n", b"Hello World\n"),
            (b"Hello\r\nWorld\r\n", b"Hello\nWorld\n", ValueError),
            (b"\n".join([b"Line" + bytes(str(i), 'utf-8') for i in range(10000)]), b"\n".join([b"Line" + bytes(str(i), 'utf-8') for i in range(10000)])),
            (b"Unicode \xe2\x98\x83\r\n", b"Unicode \xe2\x98\x83\n", ValueError),
            (b"\r\n\r\r\n\nHello\r\n\r\r\n\nWorld\r\n\r\r\n\n", b"\n\n\n\nHello\n\n\n\nWorld\n\n\n\n", ValueError),
            ((b"a" * (4096 - 1) + b"\r") + (b"\n" + b"b" * (4096 - 1)), b"a" * (4096 - 1) + b"\n" + b"b" * (4096 - 1), ValueError),
            ((b"Hello\r\n" * 2048) + b"World", (b"Hello\n" * 2048) + b"World", ValueError),
            (b"Random\xe2\x98\x83DataWith\xc3\xa9Breaks\rMixedIn\n", b"Random\xe2\x98\x83DataWith\xc3\xa9Breaks\nMixedIn\n", ValueError),
            # fmt: on
        ],
    )
    def test_open_unix_txt_safely(
        self,
        src_str_bin: bytes,
        expected_tgt_str_bin: bytes,
        raises: Exception | None = None,
    ) -> None:
        chunk_size: int = 4096
        encoding = "utf-8"
        expected_tgt_str = expected_tgt_str_bin.decode(encoding=encoding)
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "src.txt")
            path_out = os.path.join(tmp_dir, "dst.txt")

            with open(path, "wb") as f:
                f.write(src_str_bin)

            content = None
            if raises is None:
                with path_utils.open_unix_safely(path, encoding=encoding, chunk_size=chunk_size) as f:
                    content = f.read()
            else:
                with self.assertRaises(ValueError):
                    with path_utils.open_unix_safely(path, encoding=encoding, chunk_size=chunk_size) as f:
                        content = f.read()

            if raises is None:
                self.assertEqual(expected_tgt_str, content)
                with path_utils.open_unix_safely(path_out, "w", encoding=encoding, chunk_size=chunk_size) as f:
                    f.write(content)  # type: ignore[arg-type]
                with open(path_out, "rb") as f:
                    content_out = f.read()
                self.assertEqual(expected_tgt_str_bin, content_out)
            else:
                self.assertIsNone(content)

            with path_utils.open_unix_safely(path, correct_eol=True) as f:
                content = f.read()

            self.assertEqual(expected_tgt_str, content)


unmocked_os_rename = path_utils.os.rename


class MockOSRenameFailOnce:
    # pylint: disable=[too-few-public-methods]
    num_os_rename_calls = 0
    num_os_rename_raises = 0

    def __init__(self):
        pass

    def __call__(self, old, new):
        self.num_os_rename_calls += 1
        if self.num_os_rename_raises >= self.num_os_rename_calls:
            raise OSError(errno.EXDEV, "")
        unmocked_os_rename(old, new)


class TestMv(pyfakefs.fake_filesystem_unittest.TestCase):
    # pylint: disable=[too-many-public-methods]
    def setUp(self):
        setattr(MockOSRenameFailOnce, "num_os_rename_calls", 0)
        setattr(MockOSRenameFailOnce, "num_os_rename_raises", 0)
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
        for _base, dirs, files in os.walk(self.dir):
            counted_files += len(files)
            counted_dirs += len(dirs)
        self.assertTrue(counted_files == num_files, f"{counted_files} != {num_files}")
        self.assertTrue(counted_dirs == num_dirs, f"{counted_dirs} != {num_dirs}")
        for obj in objects[:counted_files]:
            self.assertTrue(os.path.isfile(obj), f"File '{obj}' should exist!")
        for obj in objects[counted_files:]:
            self.assertTrue(os.path.isdir(obj), f"Dir '{obj}' should exist!")
        self.assertTrue((num_files + num_dirs) == len(objects), f"({num_files} + {num_dirs}) != len({objects})")

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
        self.assertRaises(filelock.Timeout, path_utils.mv, self.old, self.new)
        self.assert_exists(2, 0, self.old, old_lock)

    def test__mv__file_new_lock_exists__raise_permission(self):
        new_lock = self.new + ".lock"
        self.create_files(self.old, new_lock)
        self.assertRaises(filelock.Timeout, path_utils.mv, self.old, self.new)
        self.assert_exists(2, 0, self.old, new_lock)

    def test__mv__old_lock_exists_new_lock_exists__raise_permission(self):
        old_lock = self.old + ".lock"
        new_lock = self.new + ".lock"
        self.create_files(self.old, old_lock, new_lock)
        self.assertRaises(filelock.Timeout, path_utils.mv, self.old, self.new)
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

    @unittest.mock.patch("utils.path_utils.os.rename", side_effect=MockOSRenameFailOnce())
    def test__mv__file_across_fs__success(self, _mock_os_rename_):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.create_dirs(dir_1, dir_2)
        self.old = dir_1 + "old.txt"
        self.new = dir_2 + "new.txt"
        self.create_files(self.old)
        setattr(MockOSRenameFailOnce, "num_os_rename_raises", 1)
        path_utils.mv(self.old, self.new)
        self.assert_exists(1, 2, self.new, dir_1, dir_2)

    @unittest.mock.patch("utils.path_utils.os.rename", side_effect=MockOSRenameFailOnce())
    def test__mv__dir_across_fs__success(self, _mock_os_rename_):
        dir_1 = self.dir + "dir_1/"
        dir_2 = self.dir + "dir_2/"
        self.old = dir_1 + "old_dir/"
        self.new = dir_2 + "new_dir/"
        self.create_dirs(dir_1, dir_2, self.old)
        old_files = [self.old + "file_" + str(i) for i in range(11)]
        new_files = [self.new + "file_" + str(i) for i in range(11)]
        self.create_files(*old_files)
        setattr(MockOSRenameFailOnce, "num_os_rename_raises", 1)
        path_utils.mv(self.old, self.new)
        self.assert_exists(11, 3, *new_files, dir_1, dir_2, self.new)


class TestMvMulti(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        setattr(MockOSRenameFailOnce, "num_os_rename_calls", 0)
        setattr(MockOSRenameFailOnce, "num_os_rename_raises", 0)
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
        for _base, dirs, files in os.walk(self.dir):
            counted_files += len(files)
            counted_dirs += len(dirs)
        self.assertTrue(counted_files == num_files, f"{counted_files} != {num_files}")
        self.assertTrue(counted_dirs == num_dirs, f"{counted_dirs} != {num_dirs}")
        for obj in objects[:counted_files]:
            self.assertTrue(os.path.isfile(obj), f"File '{obj}' should exist!")
        for obj in objects[counted_files:]:
            self.assertTrue(os.path.isdir(obj), f"Dir '{obj}' should exist!")
        self.assertTrue((num_files + num_dirs) == len(objects), f"({num_files} + {num_dirs}) != len({objects})")

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
        self.assertRaises(filelock.Timeout, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(12, 0, *self.old, old_lock)

    def test__mv_multi__files_new_lock_exists__raise_permission(self):
        new_lock = self.new[-1] + ".lock"
        self.create_files(*self.old, new_lock)
        self.assertRaises(filelock.Timeout, path_utils.mv_multi, self.old, self.new)
        self.assert_exists(12, 0, *self.old, new_lock)

    def test__mv_multi__files_old_lock_exists_new_lock_exists__raise_permission(self):
        old_lock = self.old[-1] + ".lock"
        new_lock = self.new[-1] + ".lock"
        self.create_files(*self.old, old_lock, new_lock)
        self.assertRaises(filelock.Timeout, path_utils.mv_multi, self.old, self.new)
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
