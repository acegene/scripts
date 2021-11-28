#!/usr/bin/python3
#
# title: test_wrapped_indexable_callable.py
#
# descr: tests wrapped_indexable_callable.py
#
# usage: python test_wrapped_indexable_callable.py
#            * need to have wrapped_indexable_callable.py in $PYTHONPATH or place wrapped_indexable_callable.py in parent directory

import itertools
import unittest
import unittest.mock

try:
    from utils.wrapped_indexable_callable import wrapped_indexable_callable
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.wrapped_indexable_callable import wrapped_indexable_callable
####################################################################################################
####################################################################################################


def zip_equal(*iterables):
    """Zip and raise exception if lengths are not equal.
    http://stackoverflow.com/questions/32954486/zip-iterators-asserting-for-equal-length-in-python

    :param iterables: Iterable objects
    :return: A new iterator outputting tuples where one element comes from each iterable
    """
    sentinel = object()
    for combo in itertools.zip_longest(*iterables, fillvalue=sentinel):
        if any(sentinel is c for c in combo):
            raise ValueError(
                "Iterables have different lengths. Iterable(s) #{} (of 0..{}) ran out first.".format(
                    [i for i, c in enumerate(combo) if c is sentinel], len(combo) - 1
                )
            )
        yield combo


class WrappedIndexableCallableTestCase(unittest.TestCase):
    def indexable_func(self, index):
        if index > 10:
            raise IndexError
        return index

    def assert_containers_equal(self, lhs, rhs, s):
        if len(lhs) != 0:
            if str(lhs) != str(rhs):
                assert False, f"{lhs} != {rhs}"
        for l, r in zip_equal(lhs, rhs):
            assert l == r, f"For {s}: {l} != {r}"
            assert l in rhs, f"For {s}: {l} not in rhs"
        for l, r in zip_equal(reversed(lhs), reversed(rhs)):
            assert l == r, f"For {s}: {l} != {r}"
        length_lhs = len(lhs)
        for i in range(length_lhs):
            assert lhs[i] == rhs[i], f"For {s}: index: {i}: {lhs[i]} != {rhs[i]}"
        for i in range(-1, -length_lhs - 1, -1):
            assert lhs[i] == rhs[i], f"For {s}: index: {i}: {lhs[i]} != {rhs[i]}"

    def test__iterable_from_indexable(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0, 1, 2]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = [start for start in range(-expected_base[-1] - 1, expected_base[-1] + 2)] + [None]
        stops = [stop for stop in range(-expected_base[-1] - 1, expected_base[-1] + 2)] + [None]
        steps = (
            [step for step in range(-expected_base[-1] - 1, 0)]
            + [step for step in range(1, expected_base[-1] + 2)]
            + [None]
        )
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test class
        for s1 in slices:
            actual_func = WrappedIndexableCallable(self.indexable_func, expected_base_length, s1)
            actual_list = WrappedIndexableCallable([0, 1, 2, 3, 4, 5], expected_base_length, s1)
            assert len(expected_base[s1]) == len(actual_func)
            assert len(expected_base[s1]) == len(actual_list)
            self.assert_containers_equal(expected_base[s1], actual_func, s1)
            self.assert_containers_equal(expected_base[s1], actual_list, s1)
            for s2 in slices:
                self.assert_containers_equal(expected_base[s1][s2], actual_func[s2], [s1, s2])
                self.assert_containers_equal(expected_base[s1][s2], actual_list[s2], [s1, s2])
                for s3 in slices:
                    self.assert_containers_equal(expected_base[s1][s2][s3], actual_func[s2][s3], [s1, s2, s3])
                    self.assert_containers_equal(expected_base[s1][s2][s3], actual_list[s2][s3], [s1, s2, s3])


if __name__ == "__main__":
    unittest.main()
