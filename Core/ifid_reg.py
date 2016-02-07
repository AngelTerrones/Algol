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


class IFIDReg:
    def __init__(self,
                 clk:            Signal(False),
                 rst:            Signal(False),
                 id_stall:       Signal(False),
                 full_stall:     Signal(False),
                 if_kill:        Signal(False),
                 pipeline_kill:  Signal(False),
                 if_pc:          Signal(modbv(0)[32:]),
                 if_instruction: Signal(modbv(0)[32:]),
                 id_pc:          Signal(modbv(0)[32:]),
                 id_instruction: Signal(modbv(0)[32:])):
        # inputs
        self.clk            = clk
        self.rst            = rst
        self.id_stall       = id_stall
        self.full_stall     = full_stall
        self.if_kill        = if_kill
        self.pipeline_kill  = pipeline_kill
        self.if_pc          = if_pc
        self.if_instruction = if_instruction
        # outputs
        self.id_pc          = id_pc
        self.id_instruction = id_instruction

    def GetRTL(self):
        @always(self.clk.posedge)
        def rtl():
            if self.rst == 1:
                self.id_pc.next          = 0
                self.id_instruction.next = Consts.BUBBLE
            else:
                self.id_pc.next          = (self.id_pc if self.id_stall or self.full_stall else (self.if_pc))
                self.id_instruction.next = (self.id_instruction if self.id_stall or self.full_stall else
                                            (Consts.BUBBLE if self.pipeline_kill or self.if_kill else
                                             (self.if_instruction)))
        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
