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

from memIO import MemPortIO
from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import modbv


class CtrlIO:
    def __init__(self,
                 id_stall:            Signal,
                 full_stall:          Signal,
                 pipeline_kill:       Signal,
                 pc_select:           Signal,
                 id_br_type:          Signal,
                 if_kill:             Signal,
                 id_kill:             Signal,
                 id_op1_select:       Signal,
                 id_op2_select:       Signal,
                 id_alu_funct:        Signal,
                 id_mem_select:       Signal,
                 id_rf_we:            Signal,
                 id_mem_valid:        Signal,
                 id_mem_funct:        Signal,
                 id_mem_type:         Signal,
                 id_csr_cmd:          Signal,
                 mem_exception:       Signal,
                 mem_exception_cause: Signal):
        self.id_stall            = id_stall
        self.full_stall          = full_stall
        self.pc_select           = pc_select
        self.id_br_type          = id_br_type
        self.if_kill             = if_kill
        self.id_kill             = id_kill
        self.id_op1_select       = id_op1_select
        self.id_op2_select       = id_op2_select
        self.id_alu_funct        = id_alu_funct
        self.id_mem_select       = id_mem_select
        self.id_rf_we            = id_rf_we
        self.id_mem_valid        = id_mem_valid
        self.id_mem_funct        = id_mem_funct
        self.id_mem_type         = id_mem_type
        self.id_csr_cmd          = id_csr_cmd
        self.pipeline_kill       = pipeline_kill
        self.mem_exception       = mem_exception
        self.mem_exception_cause = mem_exception_cause


class Ctrlpath:
    def __init__(self):
        pass

    def GetRTL(self):
        pass

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
