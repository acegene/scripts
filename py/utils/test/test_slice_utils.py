#!/usr/bin/python3
#
# Tests slice_utils.py
#
# usage
#   * python test_slice_utils.py
#       * need to have slice_utils.py in $PYTHONPATH or place slice_utils.py in parent directory
import unittest.mock

try:
    from utils import slice_utils
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils import slice_utils
####################################################################################################
####################################################################################################


class SliceLibTest(unittest.TestCase):
    def test__in_slice(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0, 1, 2, 3, 4, 5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = (
            list(expected_base)
            + [-start - 1 for start in expected_base]
            + [None]
            + [expected_base[-1] + 1, -expected_base[-1] - 2]
        )
        stops = (
            list(expected_base)
            + [-stop - 1 for stop in expected_base]
            + [None]
            + [expected_base[-1] + 1, -expected_base[-1] - 2]
        )
        steps = (
            list(expected_base[1:])
            + [-step for step in expected_base[1:]]
            + [None]
            + [expected_base[-1] + 1, -expected_base[-1] - 1]
        )
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            for i in range(expected_base_length):
                assert slice_utils.in_slice(i, s, expected_base_length) == (
                    i in expected_base[s]
                ), f"Index={i} not found in expected_base[{s}]={expected_base[s]}"
            for i in range(-1, -expected_base_length - 1, -1):
                assert slice_utils.in_slice(i, s, expected_base_length) == (
                    i + expected_base_length in expected_base[s]
                ), f"Index={i} not found in expected_base[{s}]={expected_base[s]}"

    def test__is_slice_empty(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0, 1, 2, 3, 4, 5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = list(range(-expected_base[-1] - 3, expected_base[-1] + 3)) + [None]
        stops = list(range(-expected_base[-1] - 3, expected_base[-1] + 3)) + [None]
        steps = list(range(-expected_base[-1] - 3, 0)) + list(range(1, expected_base[-1] + 3)) + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            assert slice_utils.is_slice_empty(s, expected_base_length) == (
                len(expected_base[s]) == 0
            ), f"slice_utils.is_slice_empty({s}, {expected_base_length})={slice_utils.is_slice_empty(s, expected_base_length)} != (len(expected_base[{s}]) == 0)={len(expected_base[s]) == 0})"

    def test__slice_clean(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0, 1, 2, 3, 4, 5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = list(range(-expected_base[-1] - 3, expected_base[-1] + 3)) + [None]
        stops = list(range(-expected_base[-1] - 3, expected_base[-1] + 3)) + [None]
        steps = list(range(-expected_base[-1] - 3, 0)) + list(range(1, expected_base[-1] + 3)) + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            s_cleaned_neg = slice_utils.slice_clean(s, expected_base_length, False)
            assert (
                expected_base[s] == expected_base[s_cleaned_neg]
            ), f"{s} != {s_cleaned_neg} so {expected_base[s]} != {expected_base[s_cleaned_neg]}"
            assert s_cleaned_neg.start >= 0, f"Cleaned slice={s_cleaned_neg} has invalid start value"
            assert (
                s_cleaned_neg.stop >= 0 or s_cleaned_neg.stop == -expected_base_length - 1
            ), f"Cleaned slice={s_cleaned_neg} has invalid stop value"
            assert s_cleaned_neg.step is not None, f"Cleaned slice={s_cleaned_neg} has invalid step value"
            s_cleaned = slice_utils.slice_clean(s, expected_base_length, True)
            assert (
                expected_base[s] == expected_base[s_cleaned]
            ), f"{s} != {s_cleaned} so {expected_base[s]} != {expected_base[s_cleaned]}"
            assert s_cleaned.start >= 0, f"Cleaned slice={s_cleaned} has invalid start value"
            assert s_cleaned.stop is None or s_cleaned.stop >= 0, f"Cleaned slice={s_cleaned} has invalid stop value"
            assert s_cleaned.step is not None, f"Cleaned slice={s_cleaned} has invalid step value"

    def test__slice_index(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0, 1, 2, 3, 4, 5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = (
            list(expected_base)
            + [-start - 1 for start in expected_base]
            + [None]
            + [expected_base[-1] + 1, -expected_base[-1] - 2]
        )
        stops = (
            list(expected_base)
            + [-stop - 1 for stop in expected_base]
            + [None]
            + [expected_base[-1] + 1, -expected_base[-1] - 2]
        )
        steps = (
            list(expected_base[1:])
            + [-step for step in expected_base[1:]]
            + [None]
            + [expected_base[-1] + 1, -expected_base[-1] - 1]
        )
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            for i in range(expected_base_length + 1):
                try:
                    test_index = slice_utils.slice_index(i, s, expected_base_length)
                except IndexError:
                    assert i >= len(expected_base[s])
                    continue
                assert expected_base[test_index] == expected_base[s][i]
            for i in range(-1, -expected_base_length - 2, -1):
                try:
                    test_index = slice_utils.slice_index(i, s, expected_base_length)
                except IndexError:
                    length_slice = len(expected_base[s])
                    assert i >= length_slice or i + length_slice < 0, f"{s}: {i} is not in {expected_base[s]}"
                    continue
                assert expected_base[test_index] == expected_base[s][i]

    def test__slice_length(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0, 1, 2, 3, 4, 5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = list(range(-expected_base[-1] - 3, expected_base[-1] + 3)) + [None]
        stops = list(range(-expected_base[-1] - 3, expected_base[-1] + 3)) + [None]
        steps = list(range(-expected_base[-1] - 3, 0)) + list(range(1, expected_base[-1] + 3)) + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            actual_length = slice_utils.slice_length(s, expected_base_length)
            assert actual_length == len(expected_base[s])

    def test__slice_merge(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0, 1, 2]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = list(range(-expected_base[-1] - 2, expected_base[-1] + 2)) + [None]
        stops = list(range(-expected_base[-1] - 2, expected_base[-1] + 2)) + [None]
        steps = list(range(-expected_base[-1], 0)) + list(range(1, expected_base[-1] + 1)) + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s1 in slices:
            for s2 in slices:
                s_merged = slice_utils.slice_merge([s1, s2], expected_base_length)
                assert (
                    expected_base[s1][s2] == expected_base[s_merged]
                ), f"{[s1, s2]} != {s_merged} so {expected_base[s1][s2]} != {expected_base[s_merged]}"
                s_merged = slice_utils.slice_merge([s1, s2], expected_base_length, False)
                assert (
                    expected_base[s1][s2] == expected_base[s_merged]
                ), f"{[s1, s2]} != {s_merged} so {expected_base[s1][s2]} != {expected_base[s_merged]}"
                for s3 in slices:
                    s_merged = slice_utils.slice_merge([s1, s2, s3], expected_base_length)
                    assert (
                        expected_base[s1][s2][s3] == expected_base[s_merged]
                    ), f"{[s1, s2, s3]} != {s_merged} so {expected_base[s1][s2][s3]} != {expected_base[s_merged]}"
                    s_merged = slice_utils.slice_merge([s1, s2, s3], expected_base_length, False)
                    assert (
                        expected_base[s1][s2][s3] == expected_base[s_merged]
                    ), f"{[s1, s2, s3]} != {s_merged} so {expected_base[s1][s2][s3]} != {expected_base[s_merged]}"


if __name__ == "__main__":
    unittest.main()
