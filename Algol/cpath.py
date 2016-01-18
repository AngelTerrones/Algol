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
                 id_fwd1_select:     Signal,
                 id_fwd2_select:     Signal,
                 id_rs1_addr:        Signal,
                 id_rs2_addr:        Signal,
                 id_op1:             Signal,
                 id_op2:             Signal,
                 ex_wb_addr:         Signal,
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
        self.id_fwd1_select     = id_fwd1_select
        self.id_fwd2_select     = id_fwd2_select
        self.id_rs1_addr        = id_rs1_addr
        self.id_rs2_addr        = id_rs2_addr
        self.ex_wb_addr         = ex_wb_addr
        self.ex_wb_we           = ex_wb_we
        self.mem_wb_addr        = mem_wb_addr
        self.mem_wb_we          = mem_wb_we
        self.wb_wb_addr         = wb_wb_addr
        self.wb_wb_we           = wb_wb_we

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

        self.id_br_type         = Signal(modbv(0)[Consts.SZ_BR])
        self.id_eq              = Signal(False)
        self.id_lt              = Signal(False)
        self.id_ltu             = Signal(False)

        self.id_if_misalign     = Signal(False)
        self.id_if_fault        = Signal(False)
        self.id_illegal_inst    = Signal(False)
        self.id_softwate_int    = Signal(False)
        self.id_timer_int       = Signal(False)
        self.id_eret            = Signal(False)

        self.ex_exception       = Signal(False)
        self.ex_eret            = Signal(False)
        self.ex_csr_cmd         = Signal(modbv(0)[CSRCommand.SZ_CMD])
        self.ex_exception_code  = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE])

        self.mem_prev_exc       = Signal(False)

        self.mem_exception      = Signal(False)
        self.mem_exception_code = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE])

    def CheckInvalidAddress(addr, mem_type):
        return (addr[0] if mem_type == MemoryOpConstant.MT_H or mem_type == MemoryOpConstant.MT_HU else
                (addr[0] or addr[1] if mem_type == MemoryOpConstant.MT_W else
                 (False)))

    def GetRTL(self):
        control   = Signal(modbv(0)[26:])

        @always_comb
        def _ctrl_assignment():
            control.next = 0

        @always_comb
        def _assignments():
            self.id_br_type.next      = control[2:0]
            self.id_op1_select.next   = control[4:2]
            self.id_op2_select.next   = control[6:4]
            self.id_sel_imm.next      = control[9:6]
            self.id_alu_funct.next    = control[13:9]
            self.id_mem_type.next     = control[16:13]
            self.id_mem_funct.next    = control[16]
            self.id_mem_valid.next    = control[17]
            self.id_csr_cmd.next      = control[21:18]
            self.id_mem_data_sel.next = control[23:21]
            self.id_wb_we.next        = control[23]
            self.id_eret.next         = control[24]
            self.id_illegal_inst.next = control[25]

            self.retire.next = not self.full_stall and not self.csr_exception

        @always(self.clk.posedge)
        def _ifid_register():
            if self.rst:
                self.id_if_misalign.next = False
            else:
                if self.pipeline_kill or self.if_kill:
                    self.id_if_misalign.next = False
                elif not self.id_stall and not self.full_stall:
                    self.id_if_misalign.next = self.CheckInvalidAddress(self.imem.req.addr,
                                                                         self.imem.req.typ)

        @always(self.clk.posedge)
        def _idex_register():
            if self.rst:
                self.ex_eret.next      = False
                self.ex_csr_cmd.next   = CSRCommand.CSR_IDLE
                self.ex_exception.next = False
                self.ex_exception_code.next = CSRExceptionCode.E_ILLEGAL_INST
            else:
                if self.pipeline_kill or self.id_kill or (self.id_stall and not self.full_stall):
                    self.ex_eret.next      = False
                    self.ex_csr_cmd.next   = CSRCommand.CSR_IDLE
                    self.ex_exception.next = False
                    self.ex_exception_code.next = CSRExceptionCode.E_ILLEGAL_INST
                elif not self.id_stall and not self.full_stall:
                    self.ex_eret.next      = self.id_eret
                    self.ex_csr_cmd.next   = self.id_csr_cmd
                    self.ex_exception.next = self.id_if_misalign or self.id_illegal_inst
                    self.ex_exception_code.next = (CSRExceptionCode.E_INST_ADDR_MISALIGNED if self.id_if_misalign else
                                                   (CSRExceptionCode.E_INST_ACCESS_FAULT if self.id_if_fault else
                                                    (CSRExceptionCode.I_TIMER if self.id_interrupt else
                                                     (CSRExceptionCode.E_ILLEGAL_INST))))

        @always(self.clk.posedge)
        def _exmem_register():
            if self.rst:
                self.csr_eret.next = False
            else:
                if self.pipeline_kill:
                    self.csr_eret.next = False
                elif not self.full_stall:
                    self.csr_eret.next = self.ex_eret

        @always_comb
        def _branch_detect():
            self.id_eq.next  = self.id_op1 == self.id_op2
            self.id_lt.next  = self.id_op1.signed() < self.id_op2.signed()
            self.id_ltu.next = self.id_op1 < self.id_op2

        @always_comb
        def _pc_select():
            self.pc_select.next = (Consts.PC_EXC if self.csr_exception else
                                   (Consts.PC_BRJMP if ((self.id_br_type == Consts.BR_NE and not self.id_eq) or
                                                        (self.id_br_type == Consts.BR_EQ and self.id_eq) or
                                                        (self.id_br_type == Consts.BR_LT and self.id_lt) or
                                                        (self.id_br_type == Consts.BR_LTU and self.id_ltu) or
                                                        (self.id_br_type == Consts.BR_GE and not self.id_lt) or
                                                        (self.id_br_type == Consts.BR_GEU and not self.id_ltu)) else
                                    (Consts.PC_JALR if self.id_br_type == Consts.BR_J else
                                     (Consts.PC_4))))

        @always_comb
        def _fwd_ctrl():
            self.id_fwd1_select.next = (Consts.FWD_EX if self.id_rs1_addr == self.ex_wb_addr and self.ex_wb_we else
                                        (Consts.FWD_MEM if self.id_rs1_addr == self.mem_wb_addr and self.mem_wb_we else
                                         (Consts.FWD_WB if self.id_rs1_addr == self.wb_wb_addr and self.wb_wb_we else
                                          Consts.FWD_N)))
            self.id_fwd2_select.next = (Consts.FWD_EX if self.id_rs2_addr == self.ex_wb_addr and self.ex_wb_we else
                                        (Consts.FWD_MEM if self.id_rs2_addr == self.mem_wb_addr and self.mem_wb_we else
                                         (Consts.FWD_WB if self.id_rs2_addr == self.wb_wb_addr and self.wb_wb_we else
                                          (Consts.FWD_N))))

        @always_comb
        def _ctrl_pipeline():
            self.if_kill.next       = self.pc_select != Consts.PC_4
            self.id_stall.next      = self.id_fwd1_select == Consts.FWD_EX and (self.ex_csr_cmd != CSRCommand.CSR_IDLE or
                                                                                self.ex_mem_funct == MemoryOpConstant.M_WR)
            self.id_kill.next       = False
            self.full_stall.next    = (not self.imem.resp.valid and self.imem.req.valid) or (not self.dmem.resp.valid and self.dmem.req.valid)
            self.pipeline_kill.next = self.csr_exception

        @always_comb
        def _exc_detect():
            self.csr_exception.next = self.mem_exception or self.illegal_access
            self.csr_exception_code.next = self.mem_exception_code

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
# flycheck-flake8-maximum-line-length: 160
# flycheck-flake8rc: ".flake8rc"
# End:
