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
from myhdl import always_comb
from myhdl import modbv
from consts import Consts
from memIO import MemPortIO
from memIO import MemoryOpConstant
from cpath import Ctrlpath
from regfile import RegisterFile
from regfile import RFReadPort
from regfile import RFWritePort
from alu import ALU
from alu import ALUFunction
from alu import ALUPortIO
from csr import CSR
from csr import CSRFileRWIO
from csr import CSRExceptionIO
from csr import CSRCommand
from csr import CSRExceptionCode
from csr import CSRAddressMap
from csr import CSRModes
from imm_gen import IMMGen
from common.mux import Mux4
from pc_reg import PCreg
from ifid_reg import IFIDReg
from idex_reg import IDEXReg
from exmem_reg import EXMEMReg
from memwb_reg import MEMWBReg


class Datapath:
    def __init__(self,
                 clk:  Signal(False),
                 rst:  Signal(False),
                 imem: MemPortIO,
                 dmem: MemPortIO):
        self.clk  = clk
        self.rst  = rst
        self.imem = imem
        self.dmem = dmem

    def GetRTL(self):
        imem_pipeline      = MemPortIO()
        dmem_pipeline      = MemPortIO()
        # Signals
        id_stall           = Signal(False)
        if_kill            = Signal(False)
        id_kill            = Signal(False)
        full_stall         = Signal(False)
        pipeline_kill      = Signal(False)
        # A stage
        pc_select          = Signal(modbv(0)[2:])
        a_pc               = Signal(modbv(0)[32:])
        # IF stage
        if_pc              = Signal(modbv(0)[32:])
        if_instruction     = Signal(modbv(0)[32:])
        if_pc_next         = Signal(modbv(0 [32:]))
        # ID stage
        id_pc              = Signal(modbv(0)[32:])
        id_instruction     = Signal(modbv(0)[32:])

        id_rf_portA        = RFReadPort()
        id_rf_portB        = RFReadPort()
        id_wb_addr         = Signal(modbv(0)[5:])
        id_br_type         = Signal(modbv(0)[Consts.SZ_BR:])
        id_rs1_data        = Signal(modbv(0)[32:])
        id_rs2_data        = Signal(modbv(0)[32:])
        id_rs1_addr        = Signal(modbv(0)[5:])
        id_rs2_addr        = Signal(modbv(0)[5:])
        id_op1_select      = Signal(modbv(0)[Consts.SZ_OP1])
        id_op2_select      = Signal(modbv(0)[Consts.SZ_OP2])
        id_sel_imm         = Signal(modbv(0)[Consts.SZ_IMM:])
        id_alu_funct       = Signal(modbv(0)[ALUFunction.SZ_OP:])
        id_mem_type        = Signal(modbv(0)[MemoryOpConstant.SZ_MT:])
        id_mem_funct       = Signal(False)
        id_mem_valid       = Signal(False)
        id_csr_addr        = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])
        id_csr_cmd         = Signal(modbv(0)[CSRCommand.SZ_CMD:])
        id_mem_data_sel    = Signal(modbv(0)[Consts.SZ_WB:])
        id_wb_we           = Signal(False)
        # EX stage
        ex_pc              = Signal(modbv(0)[32:])
        ex_instruction     = Signal(modbv(0)[32:])
        ex_br_type         = Signal(modbv(0)[Consts.SZ_BR:])
        ex_rs1_data        = Signal(modbv(0)[32:])
        ex_rs2_data        = Signal(modbv(0)[32:])
        ex_sel_imm         = Signal(modbv(0)[Consts.SZ_IMM:])
        ex_rs1_addr        = Signal(modbv(0)[5:])
        ex_rs2_addr        = Signal(modbv(0)[5:])
        ex_alu_out         = Signal(modbv(0)[32:])
        ex_alu_funct       = Signal(modbv(0)[ALUFunction.SZ_OP:])
        ex_mem_wdata       = Signal(modbv(0)[32:])
        ex_mem_type        = Signal(modbv(0)[MemoryOpConstant.SZ_MT:])
        ex_mem_funct       = Signal(False)
        ex_mem_valid       = Signal(False)
        ex_csr_addr        = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])
        ex_csr_cmd         = Signal(modbv(0)[CSRCommand.SZ_CMD:])
        ex_mem_data_sel    = Signal(modbv(0)[Consts.SZ_WB:])
        ex_wb_addr         = Signal(modbv(0)[5:])
        ex_wb_we           = Signal(False)

        ex_op1_select      = Signal(modbv(0)[Consts.SZ_OP1:])
        ex_op2_select      = Signal(modbv(0)[Consts.SZ_OP2:])
        ex_fwd1_select     = Signal(modbv(0)[Consts.SZ_FWD:])
        ex_fwd2_select     = Signal(modbv(0)[Consts.SZ_FWD:])
        ex_imm             = Signal(modbv(0)[32:])
        ex_op1             = Signal(modbv(0)[32:])
        ex_op2             = Signal(modbv(0)[32:])
        ex_op1_data        = Signal(modbv(0)[32:])
        ex_op2_data        = Signal(modbv(0)[32:])
        aluIO              = ALUPortIO()

        ex_pc_brjmp        = Signal(modbv(0)[32:])
        ex_pc_jalr         = Signal(modbv(0)[32:])
        # MEM stage
        exc_pc             = Signal(modbv(0)[32:])
        mem_pc             = Signal(modbv(0)[32:])
        mem_alu_out        = Signal(modbv(0)[32:])
        mem_mem_wdata      = Signal(modbv(0)[32:])
        mem_mem_type       = Signal(modbv(0)[MemoryOpConstant.SZ_MT:])
        mem_mem_funct      = Signal(False)
        mem_mem_valid      = Signal(False)
        mem_csr_addr       = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])
        mem_csr_cmd        = Signal(modbv(0)[CSRCommand.SZ_CMD:])
        mem_mem_data_sel   = Signal(modbv(0)[Consts.SZ_WB:])
        mem_wb_addr        = Signal(modbv(0)[5:])
        mem_wb_we          = Signal(False)

        csr_rw             = CSRFileRWIO()
        csr_exc_io         = CSRExceptionIO()
        retire             = Signal(False)
        prv                = Signal(modbv(0)[CSRModes.SZ_MODE:])
        illegal_access     = Signal(False)
        csr_exception      = Signal(False)
        csr_exception_code = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE])
        csr_eret           = Signal(False)

        mem_mem_data       = Signal(modbv(0)[32:])
        mem_csr_data       = Signal(modbv(0)[32:])

        mem_mem_wdata      = Signal(modbv(0)[32:])

        # WB stage
        wb_pc              = Signal(modbv(0)[32:])
        wb_wb_addr         = Signal(modbv(0)[5:])
        wb_wb_wdata        = Signal(modbv(0)[32:])
        wb_wb_we           = Signal(False)
        wb_rf_writePort    = RFWritePort()

        # ----------------------------------------------------------------------
        # Build the pipeline.
        # ----------------------------------------------------------------------
        ctrl_unit = Ctrlpath(self.clk,
                             self.rst,
                             if_kill,
                             id_stall,
                             id_kill,
                             full_stall,
                             pipeline_kill,
                             pc_select,
                             id_br_type,
                             id_op1_select,
                             id_op2_select,
                             id_sel_imm,
                             id_alu_funct,
                             id_mem_type,
                             id_mem_funct,
                             id_mem_valid,
                             id_csr_cmd,
                             id_mem_data_sel,
                             id_wb_we,
                             ex_fwd1_select,
                             ex_fwd2_select,
                             ex_rs1_addr,
                             ex_rs2_addr,
                             ex_wb_we,
                             mem_wb_addr,
                             mem_wb_we,
                             wb_wb_addr,
                             wb_wb_we,
                             csr_exception,
                             csr_exception_code,
                             csr_eret,
                             retire,
                             prv,
                             illegal_access,
                             imem_pipeline,
                             dmem_pipeline,
                             self.imem,
                             self.dmem).GetRTL()

        @always_comb
        def _ctrl_assignments():
            csr_exc_io.exception.next = csr_exception
            csr_exc_io.exception_code.next = csr_exception_code
            csr_exc_io.eret.next = csr_eret

        # A stage
        # ----------------------------------------------------------------------
        pc_mux = Mux4(pc_select,
                      if_pc_next,
                      ex_pc_brjmp,
                      ex_pc_jalr,
                      exc_pc,
                      a_pc).GetRTL()
        # IF stage
        # ----------------------------------------------------------------------
        pc_reg = PCreg(self.clk,
                       self.rst,
                       id_stall,
                       full_stall,
                       pipeline_kill,
                       a_pc,
                       if_pc).GetRTL()

        @always_comb
        def _pc_next():
            imem_pipeline.req.addr.next = if_pc
            if_pc_next.next     = if_pc + 4
            if_instruction.next = imem_pipeline.resp.data
            # --
            imem_pipeline.req.data.next = 0xDEADC0DE
            imem_pipeline.req.fcn.next = MemoryOpConstant.MT_W
            imem_pipeline.req.typ.next = MemoryOpConstant.M_RD
            imem_pipeline.req.valid.next = True

        # ID stage
        # ----------------------------------------------------------------------
        ifid_reg = IFIDReg(self.clk,
                           self.rst,
                           id_stall,
                           full_stall,
                           if_kill,
                           pipeline_kill,
                           if_pc,
                           if_instruction,
                           id_pc,
                           id_instruction).GetRTL()

        reg_file = RegisterFile(self.clk,
                                self.rst,
                                id_rf_portA,
                                id_rf_portB,
                                wb_rf_writePort).GetRTL()

        @always_comb
        def _id_assignment():
            id_rs1_addr.next    = id_instruction[20:15]
            id_rs2_addr.next    = id_instruction[25:20]
            id_rf_portA.ra.next = id_instruction[20:15]
            id_rf_portB.ra.next = id_instruction[25:20]
            id_rs1_data.next    = id_rf_portA.rd
            id_rs2_data.next    = id_rf_portB.rd
            id_csr_addr.next    = id_instruction[32:20]

        # EX stage
        # ----------------------------------------------------------------------
        idex_reg = IDEXReg(self.clk,
                           self.rst,
                           id_stall,
                           full_stall,
                           id_kill,
                           pipeline_kill,
                           id_pc,
                           id_instruction,
                           id_br_type,
                           id_rs1_data,
                           id_rs2_data,
                           id_rs1_addr,
                           id_rs2_addr,
                           id_op1_select,
                           id_op2_select,
                           id_sel_imm,
                           id_alu_funct,
                           id_mem_type,
                           id_mem_funct,
                           id_mem_valid,
                           id_csr_addr,
                           id_csr_cmd,
                           id_mem_data_sel,
                           id_wb_addr,
                           id_wb_we,
                           ex_pc,
                           ex_instruction,
                           ex_br_type,
                           ex_rs1_data,
                           ex_rs2_data,
                           ex_op1_select,
                           ex_op2_select,
                           ex_sel_imm,
                           ex_rs1_addr,
                           ex_rs2_addr,
                           ex_alu_funct,
                           ex_mem_type,
                           ex_mem_funct,
                           ex_mem_valid,
                           ex_csr_addr,
                           ex_csr_cmd,
                           ex_mem_data_sel,
                           ex_wb_addr,
                           ex_wb_we).GetRTL()

        op1_data_fwd = Mux4(ex_fwd1_select,
                            ex_rs1_data,
                            mem_mem_wdata,
                            wb_wb_wdata,
                            0,
                            ex_op1).GetRTL()

        op2_data_fwd = Mux4(ex_fwd2_select,
                            ex_rs2_data,
                            mem_mem_wdata,
                            wb_wb_wdata,
                            0,
                            ex_op2).GetRTL()

        imm_gen = IMMGen(ex_sel_imm,
                         ex_instruction,
                         ex_imm).GetRTL()

        op1_mux = Mux4(ex_op1_select,
                       0,
                       ex_op1,
                       ex_pc,
                       0,
                       ex_op1_data).GetRTL()

        op2_mux = Mux4(ex_op2_select,
                       0,
                       ex_op2,
                       ex_imm,
                       4,
                       ex_op2_data).GetRTL()

        alu = ALU(aluIO).GetRTL()

        @always_comb
        def _ex_assignments():
            aluIO.function.next = ex_alu_funct
            aluIO.input1.next   = ex_op1_data
            aluIO.input2.next   = ex_op2_data
            aluIO.output.next   = ex_alu_out
            ex_alu_out.next     = aluIO.output
            ex_pc_brjmp.next    = ex_pc + ex_imm
            ex_pc_jalr.next     = aluIO.output
            ex_mem_wdata.next   = ex_op2

        # MEM stage
        # ----------------------------------------------------------------------
        exmem_reg = EXMEMReg(self.clk,
                             self.rst,
                             full_stall,
                             pipeline_kill,
                             ex_pc,
                             ex_alu_out,
                             ex_mem_wdata,
                             ex_mem_type,
                             ex_mem_funct,
                             ex_mem_valid,
                             ex_csr_addr,
                             ex_csr_cmd,
                             ex_mem_data_sel,
                             ex_wb_addr,
                             ex_wb_we,
                             mem_pc,
                             mem_alu_out,
                             mem_mem_wdata,
                             mem_mem_type,
                             mem_mem_funct,
                             mem_mem_valid,
                             mem_csr_addr,
                             mem_csr_cmd,
                             mem_mem_data_sel,
                             mem_wb_addr,
                             mem_wb_we).GetRTL()

        csr = CSR(self.clk,
                  self.rst,
                  csr_rw,
                  csr_exc_io,
                  retire,
                  prv,
                  illegal_access).GetRTL()

        mdata_mux = Mux4(mem_mem_data_sel,
                         mem_alu_out,
                         mem_mem_data,
                         mem_csr_data,
                         0,
                         mem_mem_wdata).GetRTL()

        @always_comb
        def _mem_assignments():
            dmem_pipeline.req.addr       = mem_alu_out
            dmem_pipeline.req.data.next  = mem_mem_wdata
            dmem_pipeline.req.fcn.next   = mem_mem_funct
            dmem_pipeline.req.typ.next   = mem_mem_type
            dmem_pipeline.req.valid.next = mem_mem_valid
            mem_mem_data.next            = dmem_pipeline.resp.data
            mem_csr_data.next            = csr.rw.rdata

        # WB stage
        # ----------------------------------------------------------------------
        memwb_reg = MEMWBReg(self.clk,
                             self.rst,
                             full_stall,
                             pipeline_kill,
                             mem_pc,
                             mem_wb_addr,
                             mem_mem_wdata,
                             mem_wb_we,
                             wb_pc,
                             wb_wb_addr,
                             wb_wb_wdata,
                             wb_wb_we).GetRTL()

        @always_comb
        def _wb_assignments():
            wb_rf_writePort.wa.next = wb_wb_addr
            wb_rf_writePort.wd.next = wb_wb_wdata
            wb_rf_writePort.we.next = wb_wb_we

        return (pc_mux, pc_reg, _pc_next, ifid_reg, reg_file, op1_mux, op2_mux,
                op1_data_fwd, op2_data_fwd, imm_gen, _id_assignment, idex_reg, alu,
                _ex_assignments, exmem_reg, _mem_assignments, csr, mdata_mux, memwb_reg,
                _wb_assignments, ctrl_unit, _ctrl_assignments)

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
