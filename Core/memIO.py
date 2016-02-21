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


class MemOp:
    """
    Defines data types and memory functions.
    """
    SZ_MT  = 3
    MT_X   = 0
    MT_B   = 1
    MT_H   = 2
    MT_W   = 3
    MT_BU  = 5
    MT_HU  = 6
    _MT_X  = modbv(0)[SZ_MT:]
    _MT_B  = modbv(1)[SZ_MT:]
    _MT_H  = modbv(2)[SZ_MT:]
    _MT_W  = modbv(3)[SZ_MT:]
    _MT_BU = modbv(5)[SZ_MT:]
    _MT_HU = modbv(6)[SZ_MT:]

    SZ_M   = 1
    M_X    = False
    M_RD   = False
    M_WR   = True


class MemPortIO:
    """
    Defines the memory IO interface.

    :ivar addr:  Memory address
    :ivar wdata: Write data
    :ivar wr:    4-bit mask to indicate bytes to write. Do not care in case of read.
    :ivar fcn:   Type of memory operation: read or write.
    :ivar valid: The current operation is valid.
    :ivar rdata: Read data
    :ivar ready: The transaction has ended and is valid
    :ivar fault: Fault in bus transaction
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.addr  = Signal(modbv(0)[32:])
        self.wdata = Signal(modbv(0)[32:])
        self.wr    = Signal(modbv(0)[4:])
        self.fcn   = Signal(False)
        self.valid = Signal(False)
        self.rdata = Signal(modbv(0)[32:])
        self.ready = Signal(False)
        self.fault = Signal(False)

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
