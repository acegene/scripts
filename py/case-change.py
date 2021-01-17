#!/usr/bin/python3
#
# descr: allows a user to recursively change casing of files in '--dir-in'
#
# usage: python case-change.py
#            file name/ext to lower for files found in current dir
#        python case-change.py --dir-in fldr --case upper --part ext
#            file ext to upper for files found in 'fldr'
#
# notes: no renaming will be done without the --force option

import os
import argparse

####################################################################################################
####################################################################################################
def parse_inputs():
    """Parse cmd line inputs; set, check, and fix script's default variables"""
    global dir_in; global namer_tmp; global namer_new; global force
    #### cmd line args parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir-in', '-i', default='.')
    parser.add_argument('--dir-out', '-o')
    # parser.add_argument('--dirs-exclude', '-x', nargs='+')
    parser.add_argument('--case', '-c', choices=['lower', 'upper'], default='lower')
    parser.add_argument('--part', '-p', choices=['all', 'name', 'ext'], default='all')
    parser.add_argument('--force', '-f', action='store_true')
    args = parser.parse_args()
    #### set script vars
    dir_in = args.dir_in; force = args.force
    dir_out = args.dir_out; case = args.case; part = args.part
    #### check script vars
    assert(os.path.isdir(dir_in))
    assert(dir_out == None or os.path.isdir(dir_out))
    #### construct namer lambdas
    if case == 'upper':
        caser_ext = str.upper
        caser_name = str.upper
    else:
        caser_ext = str.lower
        caser_name = str.lower
    if part == 'name':
        caser_ext = str
    if part == 'ext':
        caser_name = str
    tmp_str = '.tmp_file'
    if dir_out == None:
        namer_tmp = lambda dir_in,name,ext: os.path.join(dir_in, name + ext + tmp_str)
        namer_new = lambda dir_in,name,ext: os.path.join(dir_in, caser_name(name) + caser_ext(ext))
    else:
        namer_tmp = lambda dir_in,name,ext: os.path.join(dir_out, name + ext + tmp_str)
        namer_new = lambda dir_in,name,ext: os.path.join(dir_out, caser_name(name) + caser_ext(ext))

def rename_from_lambdas(directory, namer_tmp, namer_new, force):
    for fname in os.listdir(directory):
        orig = os.path.join(directory, fname)

        name, ext = os.path.splitext(fname)
        tmp = namer_tmp(directory, name, ext)
        new = namer_new(directory, name, ext)

        if orig == new:
            continue

        assert(os.path.isfile(orig))
        assert(not os.path.isfile(tmp))
        if force:
            os.rename(orig, tmp)

        assert(not os.path.isfile(new))

        if force:
            os.rename(tmp, new)
        else:
            print('INFO: this is just a test, to perform renames try --force option')

        print('EXEC: mv ' + str(orig) + ' ' + str(new))
####################################################################################################
####################################################################################################
#### default values
dir_in = None; namer_new= None; namer_tmp = None; force = None
#### checks and overwrites default values using script input
parse_inputs()
####
rename_from_lambdas(dir_in, namer_tmp, namer_new, force)