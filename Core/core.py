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
from Core.memIO import MemPortIO
from Core.dpath import Datapath
from Core.cpath import Ctrlpath
from Core.cpath import CtrlIO


class Core:
    """
    Core top module.
    """
    def __init__(self,
                 clk:    Signal,
                 rst:    Signal,
                 imem:   MemPortIO,
                 dmem:   MemPortIO,
                 toHost: Signal):
        """
        Initializes the IO ports.
        :param clk:    System clock
        :param rst:    System reset
        :param imem:   Instruction memory port
        :paran dmem:   Data memory port
        :param toHost: CSR's mtohost register. For simulation purposes.
        """
        self.clk    = clk
        self.rst    = rst
        self.imem   = imem
        self.dmem   = dmem
        self.toHost = toHost

    def GetRTL(self):
        """
        Behavioral description.
        """
        ctrl_dpath = CtrlIO()

        dpath = Datapath(self.clk,
                         self.rst,
                         ctrl_dpath,
                         self.toHost).GetRTL()
        cpath = Ctrlpath(self.clk,
                         self.rst,
                         ctrl_dpath,
                         self.imem,
                         self.dmem).GetRTL()

        return dpath, cpath

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
