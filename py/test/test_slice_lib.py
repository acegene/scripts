#!/usr/bin/python3
#
# title: test_slice_lib.py
#
# descr: tests slice_lib.py
#
# usage: python test_slice_lib.py
#            * need to have slice_lib.py in $PYTHONPATH or place slice_lib.py in parent directory

import itertools
import unittest
import unittest.mock

try:
    import slice_lib
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import slice_lib
####################################################################################################
####################################################################################################

class SliceLibTest(unittest.TestCase):
    def test__in_slice(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0,1,2,3,4,5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = [start for start in expected_base] + [-start - 1 for start in expected_base] + [None] + [expected_base[-1] + 1, -expected_base[-1] - 2]
        stops = [stop for stop in expected_base] + [-stop - 1 for stop in expected_base] + [None] + [expected_base[-1] + 1, -expected_base[-1] - 2]
        steps = [step for step in expected_base[1:]] + [-step for step in expected_base[1:]] + [None] + [expected_base[-1] + 1, -expected_base[-1] - 1]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            for i in range(expected_base_length):
                assert slice_lib.in_slice(i, s, expected_base_length) == (i in expected_base[s]), 'Index=' + str(i) + ' not found in expected_base[' + str(s) + ']=' + str(expected_base[s])
            for i in range(-1, -expected_base_length-1, -1):
                assert slice_lib.in_slice(i, s, expected_base_length) == (i+expected_base_length in expected_base[s]), 'Index=' + str(i) + ' not found in expected_base[' + str(s) + ']=' + str(expected_base[s])

    def test__is_slice_empty(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0,1,2,3,4,5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = [start for start in range(-expected_base[-1]-3,expected_base[-1]+3)] + [None]
        stops = [stop for stop in range(-expected_base[-1]-3,expected_base[-1]+3)] + [None]
        steps = [step for step in range(-expected_base[-1]-3,0)] + [step for step in range(1,expected_base[-1]+3)] + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            assert slice_lib.is_slice_empty(s, expected_base_length) == (len(expected_base[s]) == 0), 'slice_lib.is_slice_empty(' + str(s) + ', ' + str(expected_base_length) + ')=' + str(slice_lib.is_slice_empty(s, expected_base_length)) + ' != (len(expected_base[' + str(s) + ']) == 0)=' + str(len(expected_base[s]) == 0)

    def test__slice_clean(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0,1,2,3,4,5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = [start for start in range(-expected_base[-1]-3,expected_base[-1]+3)] + [None]
        stops = [stop for stop in range(-expected_base[-1]-3,expected_base[-1]+3)] + [None]
        steps = [step for step in range(-expected_base[-1]-3,0)] + [step for step in range(1,expected_base[-1]+3)] + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            s_cleaned_neg = slice_lib.slice_clean(s, expected_base_length, False)
            assert expected_base[s] == expected_base[s_cleaned_neg], str(s) + ' != ' + str(s_cleaned_neg) + ' so '  + str(expected_base[s]) + ' != ' + str(expected_base[s_cleaned_neg])
            assert s_cleaned_neg.start >= 0, 'Cleaned slice=' + str(s_cleaned_neg) + ' has invalid start value'
            assert s_cleaned_neg.stop >= 0 or s_cleaned_neg.stop == -expected_base_length - 1, 'Cleaned slice=' + str(s_cleaned_neg) + ' has invalid stop value'
            assert s_cleaned_neg.step != None, 'Cleaned slice=' + str(s_cleaned_neg) + ' has invalid step value'
            s_cleaned = slice_lib.slice_clean(s, expected_base_length, True)
            assert expected_base[s] == expected_base[s_cleaned], str(s) + ' != ' + str(s_cleaned) + ' so '  + str(expected_base[s]) + ' != ' + str(expected_base[s_cleaned])
            assert s_cleaned.start >= 0, 'Cleaned slice=' + str(s_cleaned) + ' has invalid start value'
            assert s_cleaned.stop == None or s_cleaned.stop >= 0, 'Cleaned slice=' + str(s_cleaned) + ' has invalid stop value'
            assert s_cleaned.step != None, 'Cleaned slice=' + str(s_cleaned) + ' has invalid step value'

    def test__slice_index(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0,1,2,3,4,5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = [start for start in expected_base] + [-start - 1 for start in expected_base] + [None] + [expected_base[-1] + 1, -expected_base[-1] - 2]
        stops = [stop for stop in expected_base] + [-stop - 1 for stop in expected_base] + [None] + [expected_base[-1] + 1, -expected_base[-1] - 2]
        steps = [step for step in expected_base[1:]] + [-step for step in expected_base[1:]] + [None] + [expected_base[-1] + 1, -expected_base[-1] - 1]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            for i in range(expected_base_length+1):
                try:
                    test_index = slice_lib.slice_index(i, s, expected_base_length)
                except IndexError:
                    assert i >= len(expected_base[s])
                    continue
                assert expected_base[test_index] == expected_base[s][i]
            for i in range(-1, -expected_base_length-2, -1):
                try:
                    test_index = slice_lib.slice_index(i, s, expected_base_length)
                except IndexError:
                    length_slice = len(expected_base[s])
                    assert i >= length_slice or i + length_slice < 0, str(s) + ': ' + str(i) + ' is not in ' + str(expected_base[s])
                    continue
                assert expected_base[test_index] == expected_base[s][i]

    def test__slice_length(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0,1,2,3,4,5]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = [start for start in range(-expected_base[-1]-3,expected_base[-1]+3)] + [None]
        stops = [stop for stop in range(-expected_base[-1]-3,expected_base[-1]+3)] + [None]
        steps = [step for step in range(-expected_base[-1]-3,0)] + [step for step in range(1,expected_base[-1]+3)] + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s in slices:
            actual_length = slice_lib.slice_length(s, expected_base_length)
            assert actual_length == len(expected_base[s])

    def test__slice_merge(self):
        #### set expected base list to slice and compare with actual
        expected_base = [0,1,2]
        expected_base_length = len(expected_base)
        #### generate slices to use for testing
        starts = [start for start in range(-expected_base[-1]-2,expected_base[-1]+2)] + [None]
        stops = [stop for stop in range(-expected_base[-1]-2,expected_base[-1]+2)] + [None]
        steps = [step for step in range(-expected_base[-1],0)] + [step for step in range(1,expected_base[-1]+1)] + [None]
        slices = [slice(start, stop, step) for start in starts for stop in stops for step in steps]
        #### iterate over slices and test function
        for s1 in slices:
            for s2 in slices:
                s_merged = slice_lib.slice_merge([s1, s2], expected_base_length)
                assert expected_base[s1][s2] == expected_base[s_merged], str([s1, s2]) + ' != ' + str(s_merged) + ' so '  + str(expected_base[s1][s2]) + ' != ' + str(expected_base[s_merged])
                s_merged = slice_lib.slice_merge([s1, s2], expected_base_length, False)
                assert expected_base[s1][s2] == expected_base[s_merged], str([s1, s2]) + ' != ' + str(s_merged) + ' so '  + str(expected_base[s1][s2]) + ' != ' + str(expected_base[s_merged])
                for s3 in slices:
                    s_merged = slice_lib.slice_merge([s1, s2, s3], expected_base_length)
                    assert expected_base[s1][s2][s3] == expected_base[s_merged], str([s1, s2, s3]) + ' != ' + str(s_merged) + ' so '  + str(expected_base[s1][s2][s3]) + ' != ' + str(expected_base[s_merged])
                    s_merged = slice_lib.slice_merge([s1, s2, s3], expected_base_length, False)
                    assert expected_base[s1][s2][s3] == expected_base[s_merged], str([s1, s2, s3]) + ' != ' + str(s_merged) + ' so '  + str(expected_base[s1][s2][s3]) + ' != ' + str(expected_base[s_merged_neg])

if __name__ == '__main__':
    unittest.main()
