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


class MEMWBReg:
    def __init__(self,
                 clk:           Signal(False),
                 rst:           Signal(False),
                 full_stall:    Signal(False),
                 pipeline_kill: Signal(False),
                 mem_pc:        Signal,
                 mem_wb_addr:   Signal,
                 mem_wb_wdata:  Signal,
                 mem_wb_we:     Signal,
                 wb_pc:         Signal,
                 wb_wb_addr:    Signal,
                 wb_wb_wdata:   Signal,
                 wb_wb_we:      Signal):
        # inputs
        self.clk           = clk
        self.rst           = rst
        self.full_stall    = full_stall
        self.pipeline_kill = pipeline_kill
        self.mem_pc        = mem_pc
        self.mem_wb_addr   = mem_wb_addr
        self.mem_wb_wdata  = mem_wb_wdata
        self.mem_wb_we     = mem_wb_we
        # outputs
        self.wb_pc         = wb_pc
        self.wb_wb_addr    = wb_wb_addr
        self.wb_wb_wdata   = wb_wb_wdata
        self.wb_wb_we      = wb_wb_we

    def GetRTL(self):
        @always(self.clk.posedge)
        def rtl():
            if self.rst == 1:
                self.wb_pc.next       = 0
                self.wb_wb_addr.next  = 0
                self.wb_wb_wdata.next = 0
                self.wb_wb_we.next    = False
            else:
                self.wb_pc.next       = (self.wb_pc if self.full_stall else self.mem_pc)
                self.wb_wb_addr.next  = (self.wb_wb_addr if self.full_stall else self.mem_wb_addr)
                self.wb_wb_wdata.next = (self.wb_wb_wdata if self.full_stall else self.mem_wb_wdata)
                self.wb_wb_we.next    = (self.wb_wb_we if self.full_stall else (False if self.pipeline_kill else self.mem_pc))
        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
