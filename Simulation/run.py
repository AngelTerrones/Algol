#!/usr/bin/env python
# Copyright (c) 2015 Angel Terrones (<angelterrones@gmail.com>)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import argparse
import pytest
import os
import glob


def run_module(all=False, file=None, list=False):
    if list:
        list_module_test()
    elif all:
        pytest.main('-v')
    else:
        pytest.main(['-v', file])


def run_simulation(all=False, file=None, list=False):
    if list:
        list_core_test()
    else:
        pass


def run_cosimulation(all=False, file=None, list=False):
    if list:
        list_core_test()
    else:
        pass


def list_module_test():
    print("List of unit tests:")
    cwd = os.getcwd()
    tests = glob.glob(cwd + "/Simulation/modules/test*.py")
    if len(tests) == 0:
        print("No available tests: {0}".format(cwd))
    else:
        print("------------------------------------------------------------")
        for test in tests:
            print(test)
        print("------------------------------------------------------------")


def list_core_test():
    print("List of core tests (ASM/C):")
    cwd = os.getcwd()
    tests = glob.glob(cwd + "/Simulation/tests/*")
    if len(tests) == 0:
        print("No available tests.")
    else:
        print("------------------------------------------------------------")
        for test in tests:
            print(test)
        print("------------------------------------------------------------")


def main():
    """
    Set arguments, parse, and call the required function
    """
    choices = ['module', 'sim', 'cosim']
    functions = [run_module, run_simulation, run_cosimulation]

    parser = argparse.ArgumentParser(description='Simulation script.')
    parser.add_argument('mode', help='Type of simulation', choices=choices)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--all', help='Execute all tests', action='store_true')
    group.add_argument('-l', '--list', help='List tests', action='store_true')
    group.add_argument('-f', '--file', help='Indicate a specific test')

    args = parser.parse_args()

    functions[choices.index(args.mode)](args.all, args.file, args.list)

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End: