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
from csr import CSRCommand
from memIO import MemoryOpConstant
from consts import Consts


class EXMEMReg:
    def __init__(self,
                 clk:             Signal(False),
                 rst:             Signal(False),
                 full_stall:      Signal(False),
                 pipeline_kill:   Signal(False),
                 ex_pc:           Signal,
                 ex_alu_out:      Signal,
                 ex_mem_wdata:    Signal,
                 ex_mem_type:     Signal,
                 ex_mem_funct:    Signal,
                 ex_mem_valid:    Signal,
                 ex_csr_cmd:      Signal,
                 ex_mem_data_sel:  Signal,
                 ex_wb_addr:      Signal,
                 ex_wb_we:        Signal,
                 mem_pc:          Signal,
                 mem_alu_out:     Signal,
                 mem_mem_wdata:   Signal,
                 mem_mem_type:    Signal,
                 mem_mem_funct:   Signal,
                 mem_mem_valid:   Signal,
                 mem_csr_cmd:     Signal,
                 mem_mem_data_sel: Signal,
                 mem_wb_addr:     Signal,
                 mem_wb_we:       Signal):
        # inputs
        self.clk              = clk
        self.rst              = rst
        self.full_stall       = full_stall
        self.pipeline_kill    = pipeline_kill
        self.ex_pc            = ex_pc
        self.ex_alu_out       = ex_alu_out
        self.ex_mem_wdata     = ex_mem_wdata
        self.ex_mem_type      = ex_mem_type
        self.ex_mem_funct     = ex_mem_funct
        self.ex_mem_valid     = ex_mem_valid
        self.ex_csr_cmd       = ex_csr_cmd
        self.ex_mem_data_sel  = ex_mem_data_sel
        self.ex_wb_addr       = ex_wb_addr
        self.ex_wb_we         = ex_wb_we
        # outputs
        self.mem_pc           = mem_pc
        self.mem_alu_out      = mem_alu_out
        self.mem_mem_wdata    = mem_mem_wdata
        self.mem_mem_type     = mem_mem_type
        self.mem_mem_funct    = mem_mem_funct
        self.mem_mem_valid    = mem_mem_valid
        self.mem_csr_cmd      = mem_csr_cmd
        self.mem_mem_data_sel = mem_mem_data_sel
        self.mem_wb_addr      = mem_wb_addr
        self.mem_wb_we        = mem_wb_we

    def GetRTL(self):
        @always(self.clk.posedge)
        def rtl():
            if self.rst == 1:
                self.mem_pc          = 0
                self.mem_mem_valid   = False
                self.mem_csr_cmd     = CSRCommand.CSR_IDLE
                self.mem_wb_we       = False
                self.mem_alu_out     = 0
                self.mem_mem_wdata   = 0
                self.mem_mem_type    = MemoryOpConstant.MT_X
                self.mem_mem_funct   = MemoryOpConstant.M_X
                self.mem_mem_data_sel = Consts.WB_X
                self.mem_wb_addr     = 0
            else:
                if self.pipeline_kill:
                    self.mem_pc        = 0
                    self.mem_mem_valid = False
                    self.mem_csr_cmd   = CSRCommand.CSR_IDLE
                    self.mem_wb_we     = False
                elif not self.full_stall:
                    self.mem_pc          = self.ex_pc
                    self.mem_alu_out     = self.ex_alu_out
                    self.mem_mem_wdata   = self.ex_mem_wdata
                    self.mem_mem_type    = self.ex_mem_type
                    self.mem_mem_funct   = self.ex_mem_funct
                    self.mem_mem_valid   = self.ex_mem_valid
                    self.mem_csr_cmd     = self.ex_csr_cmd
                    self.mem_mem_data_sel = self.ex_mem_data_sel
                    self.mem_wb_addr     = self.ex_wb_addr
                    self.mem_wb_we       = self.ex_wb_we

        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
