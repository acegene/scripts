
#!/usr/bin/python3
#
# title: multifile-rename-test.py
#
# descr: tests multifile-rename.py
#
# usage: python multifile-rename-test.py
#
# notes: version 0.8
#        tested on 'Windows 10 2004' # TODO: testing with OSX and linux
#
# todos: cases with more multifiles and files not part of multifiles
#        refactor creation of params
#        input prompts related to dir such as 'd ..'

import argparse
import copy
import importlib
import os
import unittest

from parameterized import parameterized # pip install parameterized
from typing import List # declaration of parameter and return types
from unittest.mock import patch

multifile_rename = importlib.import_module("multifile-rename")
####################################################################################################
#################################################################################################### 
coverage = 'mid'
print('INFO: testing with coverage set to: ' + coverage)
if coverage == 'low':
    part_symbols = ['-']
    part_word = ['pt']
    dirs_out = ['.']
    part_out = ['a', 'part_1']
elif coverage == 'mid':
    part_symbols = ['_']
    part_word = ['pt', '']
    dirs_out = [None, 'test']
    part_out = ['1', 'part_a', 'cd0']
elif coverage == 'high':
    part_symbols = ['_', '-', ' ', '']
    part_word = ['pt', 'part', '']
    dirs_out = [None, '.', '..', 'test', 'test' + os.sep + 'level1']
    part_out = ['a', '1', 'part_a', ' pt0']
else:
    raise
params = [w for w in dirs_out]
params = [[p, x+y+z] for p in params for x in part_symbols for y in part_word for z in part_symbols]
params = [p + [o] for p in params for o in part_out]

class MultifileRenameTestCase(unittest.TestCase):
    def setUp(self):
        default_parser_args = {'dir_in':'.','dir_out':None,'excludes':[],'regex':None,'inplace': False,'maxdepth':5,'mindepth':1,'part_out':'1','part_final':'1000','exts':['mp4', 'txt'],'exts_json':None,'exts_env':None}
        self.args = lambda: None # hack to 'forward declare' variable
        self.setCmdArgs(default_parser_args)
        self.base = 'base'; self.ext = '.mp4'
        self.input_side_effect = ['c'] * 10
        self.generate_parts(11)
        self.mvd = []
        self.files_in = []; self.files_out = []

    def setCmdArgs(self, dict_args):
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

    def rename_side_effect(self, *args, **kwargs):
        self.mvd.append((args[0], args[1]))

    def runTest(self, args, files_in, files_out):
        self.setCmdArgs(args); self.files_in = copy.deepcopy(files_in); self.files_out = copy.deepcopy(files_out)
        self.dir_mv = self.args.dir_out if self.args.dir_out != None else self.args.dir_in
        mv_pairs =  [(os.path.join(self.args.dir_in, i), os.path.join(self.dir_mv, o)) for i, o in zip(self.files_in, self.files_out)]
        with patch('argparse.ArgumentParser.parse_args', return_value=copy.deepcopy(self.args)): # hardcode user cmd line args
            with patch('multifile-rename.listdir_dirs', side_effect=self.listdir_dirs_side_effect):
                with patch('builtins.input', side_effect=self.input_side_effect): # hardcode user input
                    with patch('os.path.isfile', side_effect=self.isfile_side_effect):
                        with patch('os.path.isdir', side_effect=self.isdir_side_effect):
                            with patch('os.listdir', side_effect=self.listdir_side_effect):
                                with patch('multifile-rename.mv_atomic', side_effect=self.rename_side_effect) as rename:
                                    # with patch('builtins.print'): # silence output and speed up test
                                    multifile_rename.main()
                                    assert len(rename.call_args_list) == len(mv_pairs), f"{len(rename.call_args_list)} != {len(mv_pairs)}"
                                    for (args, kwargs), mv_pair in zip(rename.call_args_list, mv_pairs):
                                        assert args == mv_pair, f"{args} != {mv_pair}"

    @parameterized.expand(params)
    def testNo1(self, dir_out, prepart, part_out):
        args = {'dir_out':dir_out, 'part_out':part_out}
        files_in = [self.base + prepart + str(p) + self.ext for p in self.nums[1:] if prepart + str(self.nums[1]) != part_out]
        files_out = [self.base + part_out[:-1]  + str(p) + self.ext for i, p in enumerate(self.gen_parts(part_out[-1], len(files_in))) if i < len(files_in)]
        self.runTest(args, files_in, files_out)
    @parameterized.expand(params)
    def testNo2(self, dir_out, prepart, part_out):
        args = {'dir_out':dir_out, 'part_out':part_out}
        self.input_side_effect = ['i', 'b mid', 'i', 'b final', 'e .ext', 'c']
        files_in = [self.base + prepart + str(p) + 'fluff' + self.ext for p in self.nums[1:]]
        files_out = ['final' + part_out[:-1]  + str(p) + '.ext' for i, p in enumerate(self.gen_parts(part_out[-1], len(files_in))) if i < len(files_in)]
        self.runTest(args, files_in, files_out)
    @parameterized.expand(params)
    def testNo3(self, dir_out, prepart, part_out):
        args = {'dir_out':dir_out, 'part_out':part_out}
        files_in = [self.base + prepart + str(p) + self.ext for p in self.nums[2:] if prepart + str(self.nums[2]) != part_out]
        files_out = [self.base + part_out[:-1]  + str(p) + self.ext for i, p in enumerate(self.gen_parts(part_out[-1], len(files_in))) if i < len(files_in)]
        print(files_in)
        print(files_out)
        self.runTest(args, files_in, files_out)

if __name__ == '__main__':
    unittest.main()