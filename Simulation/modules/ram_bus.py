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

from Core.memIO import MemOp
from Core.memIO import MemPortIO
from myhdl import always
from myhdl import Signal
from myhdl import delay


class RamBus:
    def __init__(self, memory_size):
        ns = memory_size  # in words
        self.depth = ns
        self.clk = Signal(False)
        self.rst = Signal(False)
        self.imem = MemPortIO()
        self.dmem = MemPortIO()

        self.mirror_mem = [None for _ in range(ns)]

    def gen_clocks(self):
        @always(delay(3))
        def rambusclk():
            self.clk.next = not self.clk

        return rambusclk

    def write(self, addr, data):
        yield self.clk.posedge
        self.dmem.addr.next = addr
        self.dmem.wdata.next = data
        self.dmem.wr.next = 0b1111
        self.dmem.fcn.next = MemOp.M_WR
        self.dmem.valid.next = True
        self.mirror_mem[addr >> 2] = data
        yield self.dmem.ready.posedge
        yield self.clk.negedge
        self.dmem.valid.next = False

    def read(self, addr):
        yield self.clk.posedge
        self.dmem.addr.next = addr
        self.dmem.wr.next = 0b0000
        self.dmem.fcn.next = MemOp.M_RD
        self.dmem.valid.next = True
        # insert a delay waiting for stable signals.
        # Also, insert a loop to check for a stable signal,
        # and ignore glitches.
        yield delay(1)
        while not self.dmem.ready:
            yield self.dmem.ready.posedge
            yield self.clk.negedge
        self.dmem.valid.next = False


# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
