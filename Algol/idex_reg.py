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
from consts import Consts
from alu import ALUFunction
from memIO import MemoryOpConstant
from csr import CSRCommand


class IDEXReg:
    def __init__(self,
                 clk:             Signal(False),
                 rst:             Signal(False),
                 id_stall:        Signal(False),
                 full_stall:      Signal(False),
                 id_kill:         Signal(False),
                 pipeline_kill:   Signal(False),
                 id_pc:           Signal(modbv(0)[32:]),
                 id_br_type:      Signal(modbv(0)[2:]),
                 id_op1_data:     Signal,
                 id_op2_data:     Signal,
                 id_alu_funct:    Signal,
                 id_mem_wdata:    Signal,
                 id_mem_type:     Signal,
                 id_mem_funct:    Signal,
                 id_mem_valid:    Signal,
                 id_csr_cmd:      Signal,
                 id_mem_data_sel: Signal,
                 id_wb_addr:      Signal,
                 id_wb_we:        Signal,
                 ex_pc:           Signal,
                 ex_br_type:      Signal,
                 ex_op1_data:     Signal,
                 ex_op2_data:     Signal,
                 ex_alu_funct:    Signal,
                 ex_mem_wdata:    Signal,
                 ex_mem_type:     Signal,
                 ex_mem_funct:    Signal,
                 ex_mem_valid:    Signal,
                 ex_csr_cmd:      Signal,
                 ex_wb_data_sel:  Signal,
                 ex_wb_addr:      Signal,
                 ex_wb_we:        Signal):
        # inputs
        self.clk             = clk
        self.rst             = rst
        self.id_stall        = id_stall
        self.full_stall      = full_stall
        self.id_kill         = id_kill
        self.pipeline_kill   = pipeline_kill
        self.id_pc           = id_pc
        self.id_br_type      = id_br_type
        self.id_op1_data     = id_op1_data
        self.id_op2_data     = id_op2_data
        self.id_alu_funct    = id_alu_funct
        self.id_mem_wdata    = id_mem_wdata
        self.id_mem_type     = id_mem_type
        self.id_mem_funct    = id_mem_funct
        self.id_mem_valid    = id_mem_valid
        self.id_csr_cmd      = id_csr_cmd
        self.id_mem_data_sel = id_mem_data_sel
        self.id_wb_addr      = id_wb_addr
        self.id_wb_we        = id_wb_we
        # outputs
        self.ex_pc           = ex_pc
        self.ex_br_type      = ex_br_type
        self.ex_op1_data     = ex_op1_data
        self.ex_op2_data     = ex_op2_data
        self.ex_alu_funct    = ex_alu_funct
        self.ex_mem_wdata    = ex_mem_wdata
        self.ex_mem_type     = ex_mem_type
        self.ex_mem_funct    = ex_mem_funct
        self.ex_mem_valid    = ex_mem_valid
        self.ex_csr_cmd      = ex_csr_cmd
        self.ex_wb_data_sel  = ex_wb_data_sel
        self.ex_wb_addr      = ex_wb_addr
        self.ex_wb_we        = ex_wb_we

    def GetRTL(self):
        @always(self.clk.posedge)
        def rtl():
            if self.rst == 1:
                self.ex_pc.next          = 0  # ?
                self.ex_branch_type.next = Consts.BR_X
                self.ex_op1_data.next    = 0xDEADF00D
                self.ex_op2_data.next    = 0xDEADF00D
                self.ex_alu_funct.next   = ALUFunction.OP_ADD
                self.ex_mem_wdata.next   = 0x0BADC0DE
                self.ex_mem_type.next    = MemoryOpConstant.MT_X
                self.ex_mem_funct.next   = MemoryOpConstant.M_X
                self.ex_mem_valid.next   = False
                self.ex_csr_cmd.next     = CSRCommand.CSR_IDLE
                self.ex_wb_data_sel.next = Consts.WB_X
                self.ex_wb_addr.next     = 0
                self.ex_wb_we.next       = False
            else:
                # id_stall and full_stall are not related.
                if self.pipeline_kill or self.id_kill or (self.id_stall and not self.full_stall):
                    self.ex_branch_type.next = Consts.BR_X
                    self.ex_mem_valid.next   = False
                    self.ex_mem_funct.next   = MemoryOpConstant.M_X
                    self.ex_csr_cmd.next     = CSRCommand.CSR_IDLE
                    self.ex_wb_addr.next     = 0
                    self.ex_wb_we.next       = False
                elif (not self.id_stall and not self.full_stall):
                    self.ex_pc.next          = self.id_pc
                    self.ex_op1_data.next    = self.id_op1_data
                    self.ex_op2_data.next    = self.id_op2_data
                    self.ex_alu_funct.next   = self.id_alu_funct
                    self.ex_mem_wdata.next   = self.id_op2
                    self.ex_mem_type.next    = self.id_mem_type
                    self.ex_wb_data_sel.next = self.id_wb_select

                    self.ex_branch_type.next = self.id_br_type
                    self.ex_mem_valid.next   = self.id_mem_valid
                    self.ex_mem_funct.next   = self.id_mem_funct
                    self.ex_csr_cmd.next     = self.id_csr_cmd
                    self.ex_wb_addr.next     = self.id_wb_addr
                    self.ex_wb_we.next       = self.id_rf_we

        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
