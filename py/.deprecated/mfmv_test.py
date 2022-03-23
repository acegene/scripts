#!/usr/bin/python3
#
# title: mfmv_test.py
#
# descr: tests mfmv.py
#
# usage: python mfmv_test.py
#            * need to have mfmv.py in $PYTHONPATH or place mfmv.py in parent directory
#
# notes: version 0.8
#        tested on 'Windows 10 2004' # TODO: testing with OSX and linux
#
# todos: cases with more multifiles and files not part of multifiles
#        refactor creation of params
#        input prompts related to dir such as 'd ..'

import argparse
import copy
import os
import sys
import unittest
import unittest.mock

import parameterized # pip install parameterized

from typing import List # declaration of parameter and return types

import mfmv_test_helper

try:
    import mfmv
    from wrapped_indexable_callable import WrappedIndexableCallable
except:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import mfmv
    from wrapped_indexable_callable import WrappedIndexableCallable
####################################################################################################
#################################################################################################### 
coverage = 'low'
print('INFO: testing with coverage set to: ' + coverage)
if coverage == 'low':
    part_symbols = ['-']
    part_word = ['pt']
    dirs_out = ['.']
    part_out = mfmv.gen_wrapped_indexable_callable()
elif coverage == 'mid':
    part_symbols = ['_']
    part_word = ['pt', '']
    dirs_out = [None, 'test']
    part_out = ['1', 'part_a', 'cd0']
elif coverage == 'high':
    part_symbols = ['_', '-', ' ', '']
    part_word = ['pt', 'part', '']
    dirs_out = [None, '.', '..', 'test', 'test' + os.sep + 'level1']
    part_out = ['a', '1', 'part_a', ' pt0', 'cd 6']
else:
    raise
params = [w for w in dirs_out]
params = [[p, x+y+z] for p in params for x in part_symbols for y in part_word for z in part_symbols]
params = [p + [o] for p in params for o in part_out]
# print(params)

class MultifileMvTestCase(unittest.TestCase):
    def setUp(self):
        default_parser_args = {'dir_in':'.','dir_out':None,'excludes':[],'regex':None,'inplace': False,'maxdepth':5,'mindepth':1,'part_final':'1000','exts':['mp4', 'txt'],'exts_json':None,'exts_env':None,'range_search':[0,1],'range_mv':None}
        self.args = lambda: None # hack to 'forward declare' variable
        self.set_cmd_args(default_parser_args)
        self.base = 'base'; self.ext = '.mp4'
        self.input_side_effect = ['c'] * 200
        self.generate_parts(11)
        self.mvd = []
        self.files_in = []; self.files_out = []

    def set_cmd_args(self, dict_args):
        [setattr(self.args, k, v) for k, v in dict_args.items()]

    def generate_parts(self, length:int) -> List[str]:
        digits = len(str(length))
        self.nums = [str(i) for i in range(0, length+1)]
        self.nums_padded = [n.zfill(digits) for i, n in enumerate(self.nums) if i < 10**digits-1]

    def gen_parts(self, part_out:str, length:int) -> List[str]:
        if part_out.isdigit():
            digits = len(str(length))
            return [str(i) for i in range(int(part_out), int(part_out) + length)]
        else:
            return ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'][:length+1]

    def listdir_side_effect(self, *args, **kwargs):
        return self.files_in if args[0] == self.args.dir_in else []

    def listdir_dirs_side_effect(self, *args, **kwargs):
        return [self.args.dir_in]

    def isfile_side_effect(self, *args, **kwargs):
        for (lhs, rhs) in self.mvd:
            if args[0] == rhs:
                assert args[0] in [os.path.join(self.dir_mv, f) for f in self.files_out], f"{args[0]} not in {[os.path.join(self.dir_mv, f) for f in self.files_out]}"
                return True
        for (lhs, rhs) in self.mvd:
            if args[0] == lhs:
                assert args[0] in [os.path.join(self.args.dir_in, f) for f in self.files_in]
                return False
        return args[0] in [os.path.join(self.args.dir_in, f) for f in self.files_in]

    def isdir_side_effect(self, *args, **kwargs):
        if args[0] == self.args.dir_in:
            return True
        if args[0] == self.args.dir_out:
            return True
        return False

    def multifile_mv_side_effect(self, *args, **kwargs):
        self.mvd.append((args[0], args[1]))

    def part_func_selection_terminal_side_effect(self, *args, **kwargs):
        mfmv.gen_wrapped_indexable_callable()

    def runTest(self, args, files_in, files_out, prepart, part_out):
        self.set_cmd_args(args); self.files_in = copy.deepcopy(files_in); self.files_out = copy.deepcopy(files_out)
        self.dir_mv = self.args.dir_out if self.args.dir_out != None else self.args.dir_in
        mv_pairs =  [(os.path.join(self.args.dir_in, i), os.path.join(self.dir_mv, o)) for i, o in zip(self.files_in, self.files_out)]
        # with unittest.mock.patch('builtins.input', side_effect=self.input_side_effect): # hardcode user input
        with unittest.mock.patch('argparse.ArgumentParser.parse_args', return_value=copy.deepcopy(self.args)): # hardcode user cmd line args
            with unittest.mock.patch('mfmv.listdir_dirs', side_effect=self.listdir_dirs_side_effect):
                    with unittest.mock.patch('os.path.isfile', side_effect=self.isfile_side_effect):
                        with unittest.mock.patch('os.path.isdir', side_effect=self.isdir_side_effect):
                            with unittest.mock.patch('os.listdir', side_effect=self.listdir_side_effect):
                                with unittest.mock.patch('mfmv.mv_atomic', side_effect=self.multifile_mv_side_effect) as mv:
                                    with unittest.mock.patch('mfmv.prepart_selection_terminal', return_value=prepart):
                                        with unittest.mock.patch('mfmv.postpart_selection_terminal', return_value=''):
                                            # with unittest.mock.patch('mfmv.part_func_selection_terminal', return_value=part_out):
                                                # with unittest.mock.patch('builtins.print'): # silence output and speed up test
                                            mfmv.main()
                                            assert len(mv.call_args_list) == len(mv_pairs), f"{len(mv.call_args_list)} != {len(mv_pairs)}"
                                            for (args, kwargs), mv_pair in zip(mv.call_args_list, mv_pairs):
                                                assert args == mv_pair, f"{args} != {mv_pair}"

    @parameterized.parameterized.expand(params)
    def testNo1(self, dir_out, prepart, part_out):
        args = {'dir_out':dir_out, 'part_out':part_out}
        files_in = [self.base + prepart + p + self.ext for p in self.nums]
        if len(part_out) < len(files_in): # TODO:
            return
        files_out = [self.base + prepart  + p + self.ext for p in part_out[0:len(files_in)]]
        if files_in[0] == files_out[0]:
            return
        self.runTest(args, files_in, files_out, prepart, part_out)

    # @parameterized.parameterized.expand(params)
    # def testNo2(self, dir_out, prepart, part_out):
    #     args = {'dir_out':dir_out, 'part_out':part_out}
    #     self.input_side_effect = ['20', 'i', 'b mid', 'i', 'b final', 'e .ext', 'c']
    #     files_in = [self.base + prepart + str(p) + 'fluff' + self.ext for p in self.nums[1:]]
    #     files_out = ['final' + part_out[:-1]  + str(p) + '.ext' for i, p in enumerate(self.gen_parts(part_out[-1], len(files_in))) if i < len(files_in)]
    #     self.runTest(args, files_in, files_out)

    # @parameterized.parameterized.expand(params)
    # def testNo3(self, dir_out, prepart, part_out):
    #     args = {'dir_out':dir_out, 'part_out':part_out, 'range_search':[0,2]}
    #     files_in = [self.base + prepart + str(p) + self.ext for p in self.nums[2:] if prepart + str(self.nums[2]) != part_out]
    #     files_out = [self.base + part_out[:-1] + str(p) + self.ext for i, p in enumerate(self.gen_parts(part_out[-1], len(files_in))) if i < len(files_in)]
    #     self.runTest(args, files_in, files_out)

    def gen_indexable_part_funcs_fixture(self):
        funcs, lengths = zip(*mfmv.gen_indexable_part_funcs())
        wrapped_funcs = [WrappedIndexableCallable(*args) for args in zip(funcs, lengths)]
        return {
            'funcs' : funcs,
            'lengths' : lengths,
            'wrapped_funcs' : wrapped_funcs
        }

    @unittest.mock.patch('builtins.print')
    def test_gen_indexable_part_funcs(self, print):
        dic = self.gen_indexable_part_funcs_fixture()
        for wf, length, expected in zip(dic['wrapped_funcs'], dic['lengths'], mfmv_test_helper.gen_indexable_part_0_99_indices):
            assert len(expected) > 0
            for actual, expected in zip(wf, expected):
                assert actual == expected, str(actual) + ' != ' + str(expected)
            with self.assertRaises(IndexError):
                wf[length]

    @unittest.mock.patch('builtins.print')
    def test_part_func_selection_terminal(self, print):
        dic = self.gen_indexable_part_funcs_fixture()
        with unittest.mock.patch('builtins.input', side_effect=[str(i) for i in reversed(range(1, len(dic['wrapped_funcs'])+1))]):
            for wf in reversed(dic['wrapped_funcs']):
                actual = mfmv.part_func_selection_terminal(dic['wrapped_funcs'])
                assert wf[0] == actual[0], str(wf[0]) + ' != ' + str(actual[0])
                assert wf[-1] == actual[-1], str(wf[-1]) + ' != ' + str(actual[-1])
                assert len(wf) == len(actual), str(len(wf)) + ' != ' + str(len(actual))

    @unittest.mock.patch('builtins.print')
    def test_prepart_selection_terminal(self, print):
        input_side_effect = ['1', 'custom_input1', 'y', '1', 'custom_input2', 'y', '1', 'custom_input3', 'y', '1', 'custom_input4', 'n', 'q']
        expecteds = input_side_effect[slice(1,-3,3)] + [None]
        with unittest.mock.patch('builtins.input', side_effect=input_side_effect):
            for expected in expecteds:
                assert mfmv.prepart_selection_terminal() == expected, str(mfmv.prepart_selection_terminal()) + ' != ' + str(expected)

    @unittest.mock.patch('builtins.print')
    def test_postpart_selection_terminal(self, print):
        input_side_effect = ['1', 'custom_input1', 'y', '1', 'custom_input2', 'y', '1', 'custom_input3', 'y', '1', 'custom_input4', 'n', 'q']
        expecteds = input_side_effect[slice(1,-3,3)] + [None]
        with unittest.mock.patch('builtins.input', side_effect=input_side_effect):
            for expected in expecteds:
                assert mfmv.postpart_selection_terminal() == expected, str(mfmv.postpart_selection_terminal()) + ' != ' + str(expected)

if __name__ == '__main__':
    unittest.main()