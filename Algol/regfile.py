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
from myhdl import always
from myhdl import always_comb
from myhdl import modbv


class RFReadPort:
    def __init__(self):
        self.ra = Signal(modbv(0)[5:])
        self.rd = Signal(modbv(0)[32:])


class RFWritePort:
    def __init__(self):
        self.wa = Signal(modbv(0)[5:])
        self.we = Signal(False)
        self.wd = Signal(modbv(0)[32:])


class RegisterFile:
    def __init__(self, clk: Signal,
                 portA: RFReadPort,
                 portB: RFReadPort,
                 writePort: RFWritePort):
        self.clk = clk
        self.portA = portA
        self.portB = portB
        self.writePort = writePort
        self._registers = [Signal(modbv(0)[32:]) for ii in range(0, 32)]

    def GetRTL(self):
        clk = self.clk
        portA = self.portA
        portB = self.portB
        writePort = self.writePort

        @always_comb
        def read():
            portA.rd.next = self._registers[portA.ra] if portA.ra != 0 else 0
            portB.rd.next = self._registers[portB.ra] if portB.ra != 0 else 0

        @always(clk.posedge)
        def write():
            if writePort.wa != 0 and writePort.we == 1:
                self._registers[writePort.wa].next = writePort.wd

        return read, write

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
