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
from memIO import MemPortIO
from dpath import Datapath
from cpath import Ctrlpath
from cpath import CtrlIO


class Core:
    def __init__(self,
                 clk: Signal,
                 rst: Signal,
                 imem: MemPortIO,
                 dmem: MemPortIO):
        self.clk = clk
        self.rst = rst
        self.imem = imem
        self.dmem = dmem

    def GetRTL(self):
        ctrl_dpath = CtrlIO()

        dpath = Datapath(self.clk,
                         self.rst,
                         ctrl_dpath)
        cpath = Ctrlpath(self.clk,
                         self.rst,
                         ctrl_dpath,
                         self.imem,
                         self.dmem)

        return dpath, cpath

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
