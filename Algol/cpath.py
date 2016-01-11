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

from consts import Consts
from alu import ALUFunction
from memIO import MemPortIO
from memIO import MemoryOpConstant
from csr import CSRCommand
from csr import CSRExceptionCode
from csr import CSRAddressMap
from csr import CSRModes
from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import modbv
from myhdl import instances


class Ctrlpath:
    def __init__(self,
                 clk:                Signal,
                 rst:                Signal,
                 if_kill:            Signal,
                 id_stall:           Signal,
                 id_kill:            Signal,
                 full_stall:         Signal,
                 pipeline_kill:      Signal,
                 pc_select:          Signal,
                 id_br_type:         Signal,
                 id_op1_select:      Signal,
                 id_op2_select:      Signal,
                 id_sel_imm:         Signal,
                 id_alu_funct:       Signal,
                 id_mem_type:        Signal,
                 id_mem_funct:       Signal,
                 id_mem_valid:       Signal,
                 id_csr_cmd:         Signal,
                 id_mem_data_sel:    Signal,
                 id_wb_we:           Signal,
                 ex_fwd1_select:     Signal,
                 ex_fwd2_select:     Signal,
                 ex_rs1_addr:        Signal,
                 ex_rs2_addr:        Signal,
                 ex_wb_we:           Signal,
                 mem_wb_addr:        Signal,
                 mem_wb_we:          Signal,
                 wb_wb_addr:         Signal,
                 wb_wb_we:           Signal,
                 csr_exception:      Signal,
                 csr_exception_code: Signal,
                 csr_eret:           Signal,
                 csr_retire:         Signal,
                 csr_prv:            Signal,
                 csr_illegal_access: Signal,
                 imem_pipeline:      MemPortIO,
                 dmem_pipeline:      MemPortIO,
                 imem:               MemPortIO,
                 dmem:               MemPortIO):
        self.clk                = clk
        self.rst                = rst
        self.if_kill            = if_kill
        self.id_stall           = id_stall
        self.id_kill            = id_kill
        self.full_stall         = full_stall
        self.pipeline_kill      = pipeline_kill
        self.pc_select          = pc_select
        self.id_br_type         = id_br_type
        self.id_op1_select      = id_op1_select
        self.id_op2_select      = id_op2_select
        self.id_sel_imm         = id_sel_imm
        self.id_alu_funct       = id_alu_funct
        self.id_mem_type        = id_mem_type
        self.id_mem_funct       = id_mem_funct
        self.id_mem_valid       = id_mem_valid
        self.id_csr_cmd         = id_csr_cmd
        self.id_mem_data_sel    = id_mem_data_sel
        self.id_wb_we           = id_wb_we
        self.ex_fwd1_select     = ex_fwd1_select
        self.ex_fwd2_select     = ex_fwd2_select
        self.ex_rs1_addr        = ex_rs1_addr
        self.ex_rs2_addr        = ex_rs2_addr
        self.mem_wb_addr        = mem_wb_addr
        self.wb_wb_addr         = wb_wb_addr

        self.csr_exception      = csr_exception
        self.csr_exception_code = csr_exception_code
        self.csr_eret           = csr_eret
        self.csr_retire         = csr_retire
        self.csr_prv            = csr_prv
        self.csr_illegal_access = csr_illegal_access
        self.imem_pipeline      = imem_pipeline
        self.dmem_pipeline      = dmem_pipeline
        self.imem               = imem
        self.dmem               = dmem

    def GetRTL(self):
        control   = Signal(modbv(0)[32:])

        @always_comb
        def _assignments():
            self.pc_select.next       = control[2:0]
            self.id_br_type.next      = control[6:2]
            self.id_op1_select.next   = control[8:6]
            self.id_op2_select.next   = control[10:8]
            self.id_sel_imm.next      = control[13:10]
            self.id_alu_funct.next    = control[17:13]
            self.id_mem_type.next     = control[20:17]
            self.id_mem_funct.next    = control[20]
            self.id_mem_valid.next    = control[21]
            self.id_csr_cmd.next      = control[25:22]
            self.id_mem_data_sel.next = control[27:25]
            self.id_wb_we.next        = control[27]
            self.ex_fwd1_select.next  = control[30:28]
            self.ex_fwd2_select.next  = control[32:30]

        @always_comb
        def _ctrl_assignment():
            control.next = 0

        @always_comb
        def _fwd_ctrl():
            self.ex_fwd1_select.next = Consts.FWD_X
            self.ex_fwd2_select.next = Consts.FWD_X

        @always_comb
        def _ctrl_pipeline():
            pass

        @always_comb
        def _exc_detect():
            pass

        @always_comb
        def _imem_assignment():
            self.imem.req.addr.next           = self.imem_pipeline.req.addr
            self.imem.req.data.next           = self.imem_pipeline.req.data
            self.imem.req.fcn.next            = self.imem_pipeline.req.fcn
            self.imem.req.typ.next            = self.imem_pipeline.req.typ
            self.imem_pipeline.resp.data.next = self.imem.resp.data

        @always_comb
        def _imem_control():
            self.imem.req.valid.next = self.imem_pipeline.req.valid and (not self.imem.resp.valid)

        @always_comb
        def _dmem_assignment():
            global self
            self.dmem.req.addr.next           = self.dmem_pipeline.req.addr
            self.dmem.req.data.next           = self.dmem_pipeline.req.data
            self.dmem.req.fcn.next            = self.dmem_pipeline.req.fcn
            self.dmem.req.typ.next            = self.dmem_pipeline.req.typ
            self.dmem_pipeline.resp.data.next = self.dmem.resp.data

        @always_comb
        def _dmem_control():
            self.dmem.req.valid.next = self.dmem_pipeline.req.valid and (not self.dmem.resp.valid)

        return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
