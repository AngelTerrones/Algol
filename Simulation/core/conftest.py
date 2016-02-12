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
import os
import glob


def auto_int(value):
    return int(value, 0)


def pytest_addoption(parser):
    parser.addoption('--mem_size', type=auto_int, action='append', default=[],
                     help='Memory size in bytes')
    parser.addoption('--hex_file', type=str, action='append', default=[],
                     help='Memory image in HEX format')
    parser.addoption('--bytes_line', type=auto_int, action='append', default=[],
                     help='Number of bytes por line in the HEX file')
    parser.addoption('--all', action='store_true', default=False, help='Run all RV32 tests')
    parser.addoption('--vcd', action='store_true', default=False, help='Generate VCD files')


def pytest_generate_tests(metafunc):
    if 'mem_size' in metafunc.fixturenames:
        metafunc.parametrize('mem_size', metafunc.config.option.mem_size)
    if 'hex_file' in metafunc.fixturenames:
        if metafunc.config.option.all:
            list_hex = glob.glob(os.getcwd() + "/Simulation/tests/rv32ui-*.hex")
            metafunc.parametrize('hex_file', list_hex)
        else:
            metafunc.parametrize('hex_file', metafunc.config.option.hex_file)
    if 'bytes_line' in metafunc.fixturenames:
        metafunc.parametrize('bytes_line', metafunc.config.option.bytes_line)
    if 'vcd' in metafunc.fixturenames:
        metafunc.parametrize('vcd', [metafunc.config.option.vcd])

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
