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
import subprocess


def run_module(all=False, file=None, list=False):
    assert all or file or list, "Please, indicate flags: --all, --file or --list"
    if list:
        list_module_test()
    elif all:
        pytest.main(['-s', '-v'])
    else:
        pytest.main(['-s', '-v', file])


def run_simulation(all=False, file=None, list=False, mem_size=4096, hex_file=None, bytes_line=0, vcd=False):
    if list:
        list_core_test()
    elif all:
        assert mem_size, "Memory size is needed"
        assert bytes_line, "Number of bytes por line is needed"
        assert not int(bytes_line) & (int(bytes_line) - 1), "Number of bytes por line must be a power of 2"
        if vcd:
            print("Running all tests with --vcd flag: ignoring.")
        pytest.main(['-v', '--tb=line', '-s', 'Simulation/core/test_core.py', '--mem_size', mem_size, '--all', '--bytes_line', bytes_line])
    else:
        assert mem_size, "Memory size is needed"
        assert hex_file, "Memory image is needed"
        assert bytes_line, "Number of bytes por line is needed"
        assert not int(bytes_line) & (int(bytes_line) - 1), "Number of bytes por line must be a power of 2"
        if vcd:
            pytest.main(['-v', '-s', 'Simulation/core/test_core.py', '--mem_size', mem_size, '--hex_file', hex_file, '--bytes_line', bytes_line, '--vcd'])
        else:
            pytest.main(['-v', '-s', 'Simulation/core/test_core.py', '--mem_size', mem_size, '--hex_file', hex_file, '--bytes_line', bytes_line])


def run_cosimulation(all=False, file=None, list=False, mem_size=None, hex_file=None):
    if list:
        list_core_test()
    else:
        pass


def list_module_test():
    print("List of unit tests for algol:")
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
    print("List of ISA tests (from riscv-test repo):")
    cwd = os.getcwd()
    tests = glob.glob(cwd + "/Simulation/tests/rv32*.hex")
    if len(tests) == 0:
        print("No available tests. Please, compile test first.")
    else:
        print("------------------------------------------------------------")
        for test in tests:
            print(test)
        print("------------------------------------------------------------")


def compile_tests():
    make_process = subprocess.Popen("autoconf; ./configure; make -j$(nproc)", stderr=subprocess.STDOUT,
                                    cwd='Simulation/tests', shell=True)
    assert make_process.wait() == 0, 'Unable to compile tests.'


def clean_tests():
    make_process = subprocess.Popen("make clean", stderr=subprocess.STDOUT,
                                    cwd='Simulation/tests', shell=True)
    assert make_process.wait() == 0, 'Unable to clean test folder.'


def main():
    """
    Set arguments, parse, and call the required function
    """
    choices = ['module', 'sim', 'cosim', 'compile_tests', 'clean_tests']
    functions = [run_module, run_simulation, run_cosimulation, compile_tests, clean_tests]

    parser = argparse.ArgumentParser(description='Algol (RISC-V processor). Main simulation script.')
    parser.add_argument('mode', help='Available commands', choices=choices)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--all', help='Execute all tests', action='store_true')
    group.add_argument('-l', '--list', help='List tests', action='store_true')
    group.add_argument('-f', '--file', help='Indicate a specific test')

    parser.add_argument('--mem_size', help='Memory size in bytes')
    parser.add_argument('--hex_file', help='Memory image in HEX format')
    parser.add_argument('--bytes_line', help='Number of bytes per line in the HEX file')
    parser.add_argument('--vcd', action='store_true', help='Generate VCD files')

    args = parser.parse_args()

    if args.mode == choices[0]:
        functions[choices.index(args.mode)](args.all, args.file, args.list)  # Module
    elif args.mode == choices[3]:
        functions[choices.index(args.mode)]()  # Compile
    elif args.mode == choices[4]:
        functions[choices.index(args.mode)]()  # clean
    else:
        functions[choices.index(args.mode)](args.all, args.file, args.list, args.mem_size, args.hex_file, args.bytes_line, args.vcd)

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
