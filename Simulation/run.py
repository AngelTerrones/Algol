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
from myhdl import toVerilog
from myhdl import Signal
from myhdl import modbv
from Core.core import CoreHDL


def run_module(args):
    if args.list:
        list_module_test()
    elif args.all:
        pytest.main(['-s', '-v', '-k', 'not test_core'])
    else:
        pytest.main(['-s', '-v', args.file])


def run_simulation(args):
    if args.all:
        assert not int(args.bytes_line) & (int(args.bytes_line) - 1), "Number of bytes por line must be a power of 2"
        if args.vcd:
            print("Ignoring the vcd flag")
        pytest.main(['-v', '--tb=line', 'Simulation/core/test_core.py', '--mem_size', args.mem_size, '--all', '--bytes_line', args.bytes_line])
    else:
        assert not int(args.bytes_line) & (int(args.bytes_line) - 1), "Number of bytes por line must be a power of 2"
        if args.vcd:
            pytest.main(['-v', '--tb=short', 'Simulation/core/test_core.py', '--mem_size', args.mem_size, '--hex_file', args.file, '--bytes_line', args.bytes_line, '--vcd'])
        else:
            pytest.main(['-v', '--tb=short', 'Simulation/core/test_core.py', '--mem_size', args.mem_size, '--hex_file', args.file, '--bytes_line', args.bytes_line])


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


def compile_tests(args):
    make_process = subprocess.Popen("autoconf; ./configure; make -j$(nproc)", stderr=subprocess.STDOUT,
                                    cwd='Simulation/tests', shell=True)
    assert make_process.wait() == 0, 'Unable to compile tests.'


def clean_tests(args):
    make_process = subprocess.Popen("make clean", stderr=subprocess.STDOUT,
                                    cwd='Simulation/tests', shell=True)
    assert make_process.wait() == 0, 'Unable to clean test folder.'


def convert_to_verilog(args):
    clk          = Signal(False)
    rst          = Signal(False)
    imem_addr_o  = Signal(modbv(0)[32:])
    imem_dat_o   = Signal(modbv(0)[32:])
    imem_sel_o   = Signal(modbv(0)[4:])
    imem_cti_o   = Signal(modbv(0)[3:])
    imem_cyc_o   = Signal(False)
    imem_we_o    = Signal(False)
    imem_stb_o   = Signal(False)
    imem_dat_i   = Signal(modbv(0)[32:])
    imem_stall_i = Signal(False)
    imem_ack_i   = Signal(False)
    imem_err_i   = Signal(False)
    dmem_addr_o  = Signal(modbv(0)[32:])
    dmem_dat_o   = Signal(modbv(0)[32:])
    dmem_sel_o   = Signal(modbv(0)[4:])
    dmem_cti_o   = Signal(modbv(0)[3:])
    dmem_cyc_o   = Signal(False)
    dmem_we_o    = Signal(False)
    dmem_stb_o   = Signal(False)
    dmem_dat_i   = Signal(modbv(0)[32:])
    dmem_stall_i = Signal(False)
    dmem_ack_i   = Signal(False)
    dmem_err_i   = Signal(False)
    toHost       = Signal(modbv(0)[32:])

    toVerilog(CoreHDL, clk, rst, toHost, imem_addr_o, imem_dat_o, imem_sel_o, imem_cti_o, imem_cyc_o, imem_we_o,
              imem_stb_o, imem_dat_i, imem_stall_i, imem_ack_i, imem_err_i, dmem_addr_o, dmem_dat_o, dmem_sel_o,
              dmem_cti_o, dmem_cyc_o, dmem_we_o, dmem_stb_o, dmem_dat_i, dmem_stall_i, dmem_ack_i, dmem_err_i)


def main():
    """
    Set arguments, parse, and call the required function
    """
    parser = argparse.ArgumentParser(description='Algol (RISC-V processor). Main simulation script.')
    subparsers = parser.add_subparsers(title='Sub-commands',
                                       description='Available functions',
                                       help='Description')

    # module simulation
    parser_module = subparsers.add_parser('module', help='Run tests for modules')
    group_module = parser_module.add_mutually_exclusive_group(required=True)
    group_module.add_argument('-l', '--list', help='List tests', action='store_true')
    group_module.add_argument('-f', '--file', help='Run a specific test')
    group_module.add_argument('-a', '--all', help='Run all tests', action='store_true')
    parser_module.set_defaults(func=run_module)

    # Core simulation
    parser_core = subparsers.add_parser('core', help='Run assembler tests in the RV32 processor')
    group_core1 = parser_core.add_mutually_exclusive_group(required=True)
    group_core1.add_argument('-f', '--file', help='Run a specific test')
    group_core1.add_argument('-a', '--all', help='Run all tests', action='store_true')
    parser_core.add_argument('mem_size', help='Memory size in bytes')
    parser_core.add_argument('bytes_line', help='Number of bytes per line in the HEX file')
    parser_core.add_argument('--vcd', action='store_true', help='Generate VCD files')
    parser_core.set_defaults(func=run_simulation)

    # Compile tests
    parser_compile = subparsers.add_parser('compile_tests', help='Compile all the RISC-V tests')
    parser_compile.set_defaults(func=compile_tests)

    # Clean tests
    parser_clean = subparsers.add_parser('clean_tests', help='Clean the RISC-V test folder')
    parser_clean.set_defaults(func=clean_tests)

    # Convert to Verilog
    parser_to_verilog = subparsers.add_parser('to_verilog', help='Convert design to Verilog')
    parser_to_verilog.set_defaults(func=convert_to_verilog)

    args = parser.parse_args()
    args.func(args)

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
