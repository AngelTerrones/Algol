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
from myhdl import always
from Core.consts import Consts


class PCreg:
    def __init__(self,
                 clk:           Signal(False),
                 rst:           Signal(False),
                 id_stall:      Signal(False),
                 full_stall:    Signal(False),
                 pipeline_kill: Signal(False),
                 a_pc:          Signal(modbv(0)[32:]),
                 if_pc:         Signal(modbv(0)[32:])):
        # inputs
        self.clk           = clk
        self.rst           = rst
        self.id_stall      = id_stall
        self.full_stall    = full_stall
        self.pipeline_kill = pipeline_kill
        self.a_pc          = a_pc
        # outputs
        self.if_pc         = if_pc

    def GetRTL(self):
        @always(self.clk.posedge)
        def rtl():
            if self.rst == 1:
                self.if_pc.next = Consts.START_ADDR
            else:
                if (not self.id_stall and not self.full_stall) | self.pipeline_kill:
                    self.if_pc.next = self.a_pc

        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
