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

from myhdl import Signal
from myhdl import modbv


class MemoryOpConstant:
    SZ_MT = 3
    MT_X  = 0
    MT_B  = 1
    MT_H  = 2
    MT_W  = 3
    MT_BU = 4
    MT_HU = 5

    SZ_M = 1
    M_X  = 0
    M_RD = 0
    M_WR = 1


class MemPortIO:
    def __init__(self):
        self.req  = MemReq()
        self.resp = MemResp()


class MemReq:
    def __init__(self):
        self.addr  = Signal(modbv(0)[32:])
        self.data  = Signal(modbv(0)[32:])
        self.fcn   = Signal(modbv(0)[3:])
        self.typ   = Signal(False)
        self.valid = Signal(False)


class MemResp:
    def __init__(self):
        self.data  = Signal(modbv(0)[32:])
        self.valid = Signal(False)

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
