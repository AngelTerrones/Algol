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
from myhdl import modbv
from Core.memIO import MemOp
from Core.consts import Consts
from Core.csr import CSRCMD


class EXMEMReg:
    def __init__(self,
                 clk:              Signal(False),
                 rst:              Signal(False),
                 full_stall:       Signal(False),
                 pipeline_kill:    Signal(False),
                 ex_pc:            Signal,
                 ex_alu_out:       Signal,
                 ex_mem_wdata:     Signal,
                 ex_mem_type:      Signal,
                 ex_mem_funct:     Signal,
                 ex_mem_valid:     Signal,
                 ex_mem_data_sel:  Signal,
                 ex_wb_addr:       Signal,
                 ex_wb_we:         Signal,
                 ex_csr_addr:      Signal,
                 ex_csr_wdata:     Signal,
                 ex_csr_cmd:       Signal,
                 mem_pc:           Signal,
                 mem_alu_out:      Signal,
                 mem_mem_wdata:    Signal,
                 mem_mem_type:     Signal,
                 mem_mem_funct:    Signal,
                 mem_mem_valid:    Signal,
                 mem_mem_data_sel: Signal,
                 mem_wb_addr:      Signal,
                 mem_wb_we:        Signal,
                 mem_csr_addr:     Signal,
                 mem_csr_wdata:    Signal,
                 mem_csr_cmd:      Signal):
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
        self.ex_mem_data_sel  = ex_mem_data_sel
        self.ex_wb_addr       = ex_wb_addr
        self.ex_wb_we         = ex_wb_we
        self.ex_csr_addr      = ex_csr_addr
        self.ex_csr_wdata     = ex_csr_wdata
        self.ex_csr_cmd       = ex_csr_cmd
        # outputs
        self.mem_pc           = mem_pc
        self.mem_alu_out      = mem_alu_out
        self.mem_mem_wdata    = mem_mem_wdata
        self.mem_mem_type     = mem_mem_type
        self.mem_mem_funct    = mem_mem_funct
        self.mem_mem_valid    = mem_mem_valid
        self.mem_mem_data_sel = mem_mem_data_sel
        self.mem_wb_addr      = mem_wb_addr
        self.mem_wb_we        = mem_wb_we
        self.mem_csr_addr     = mem_csr_addr
        self.mem_csr_wdata    = mem_csr_wdata
        self.mem_csr_cmd      = mem_csr_cmd

    def GetRTL(self):
        @always(self.clk.posedge)
        def rtl():
            if self.rst == 1:
                self.mem_pc.next           = 0
                self.mem_mem_valid.next    = False
                self.mem_alu_out.next      = 0
                self.mem_mem_wdata.next    = 0
                self.mem_mem_type.next     = MemOp.MT_X
                self.mem_mem_funct.next    = MemOp.M_X
                self.mem_mem_data_sel.next = Consts.WB_X
                self.mem_wb_addr.next      = 0
                self.mem_wb_we.next        = False
                self.mem_csr_addr.next     = 0
                self.mem_csr_wdata.next    = 0
                self.mem_csr_cmd.next      = CSRCMD.CSR_IDLE
            else:
                self.mem_pc.next           = (self.mem_pc if self.full_stall else self.ex_pc)
                self.mem_alu_out.next      = (self.mem_alu_out if self.full_stall else self.ex_alu_out)
                self.mem_mem_wdata.next    = (self.mem_mem_wdata if self.full_stall else self.ex_mem_wdata)
                self.mem_mem_type.next     = (self.mem_mem_type if self.full_stall else self.ex_mem_type)
                self.mem_mem_funct.next    = (self.mem_mem_funct if self.full_stall else self.ex_mem_funct)
                self.mem_mem_data_sel.next = (self.mem_mem_data_sel if self.full_stall else self.ex_mem_data_sel)
                self.mem_wb_addr.next      = (self.mem_wb_addr if self.full_stall else self.ex_wb_addr)
                self.mem_csr_addr.next     = (self.mem_csr_addr if self.full_stall else self.ex_csr_addr)
                self.mem_csr_wdata.next    = (self.mem_csr_wdata if self.full_stall else self.ex_csr_wdata)
                self.mem_mem_valid.next    = (self.mem_mem_valid if self.full_stall else (False if self.pipeline_kill else self.ex_mem_valid))
                self.mem_wb_we.next        = (self.mem_wb_we if self.full_stall else (False if self.pipeline_kill else self.ex_wb_we))
                self.mem_csr_cmd.next      = (self.mem_csr_cmd if (self.full_stall) else (modbv(CSRCMD.CSR_IDLE)[CSRCMD.SZ_CMD:] if self.pipeline_kill else self.ex_csr_cmd))
        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
