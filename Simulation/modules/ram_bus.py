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

from Core.consts import Consts
from Core.wishbone import WishboneMaster
from Core.wishbone import WishboneIntercon
from myhdl import always
from myhdl import delay
from myhdl import Signal


class RamBus:
    def __init__(self, memory_size):
        ns                 = memory_size  # in words
        self.depth         = ns
        self.clka          = Signal(False)
        self.clkb          = Signal(False)
        self.imem_intercon = WishboneIntercon()
        self.dmem_intercon = WishboneIntercon()
        self.imem          = WishboneMaster(self.imem_intercon)
        self.dmem          = WishboneMaster(self.dmem_intercon)

        self.mirror_mem = [None for _ in range(ns)]

    def gen_clocks(self):
        @always(delay(5))
        def rambusclk():
            self.clka.next = not self.clka
            self.clkb.next = not self.clkb

        return rambusclk

    def write(self, addr, data):
        yield self.clkb.posedge
        self.dmem.addr_o.next      = addr
        self.dmem.dat_o.next       = data
        self.dmem.sel_o.next       = 0b1111
        self.dmem.we_o.next        = Consts.M_WR
        self.dmem.cyc_o.next       = True
        self.dmem.stb_o.next       = True
        self.dmem.cti_o.next       = 0
        self.mirror_mem[addr >> 2] = data
        # insert a delay waiting for stable signals.
        # Also, insert a loop to check for a stable signal,
        # and ignore glitches.
        yield delay(1)
        while not self.dmem.ack_i:
            yield self.dmem.ack_i.posedge
            yield self.clkb.negedge
        yield self.clkb.posedge
        self.dmem.we_o.next        = Consts.M_RD
        self.dmem.cyc_o.next       = False
        self.dmem.stb_o.next       = False

    def read(self, addr):
        yield self.clkb.posedge
        self.dmem.addr_o.next = addr
        self.dmem.sel_o.next  = 0b0000
        self.dmem.we_o.next   = Consts.M_RD
        self.dmem.cyc_o.next  = True
        self.dmem.stb_o.next  = True
        self.dmem.cti_o.next  = 0
        # insert a delay waiting for stable signals.
        # Also, insert a loop to check for a stable signal,
        # and ignore glitches.
        yield delay(1)
        while not self.dmem.ack_i:
            yield self.dmem.ack_i.posedge
            yield self.clkb.negedge
        yield self.clkb.posedge
        self.dmem.cyc_o.next  = False
        self.dmem.stb_o.next  = False

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
