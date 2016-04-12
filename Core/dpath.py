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
from myhdl import always
from myhdl import instances
from Core.consts import Consts
from Core.regfile import RegisterFile
from Core.regfile import RFReadPort
from Core.regfile import RFWritePort
from Core.alu import ALU
from Core.alu import ALUOp
from Core.alu import ALUPortIO
from Core.csr import CSR
from Core.csr import CSRFileRWIO
from Core.csr import CSRCMD
from Core.csr import CSRExceptionIO
from Core.csr import CSRAddressMap
from Core.imm_gen import IMMGen
from Core.mux import Mux4
from Core.mux import Mux2


def Datapath(clk,
             rst,
             ctrlIO,
             toHost):
    """
    A 5-stage data path with data forwarding.

    :param clk:    System clock
    :param rst:    System reset
    :param ctrlIO: IO bundle. Interface with the cpath module
    :param toHost: Connected to the CSR's mtohost register. For simulation purposes.
    """
    a_pc             = Signal(modbv(0)[32:])
    if_pc            = Signal(modbv(0)[32:])
    if_instruction   = Signal(modbv(0)[32:])
    if_pc_next       = Signal(modbv(0)[32:])
    id_pc            = Signal(modbv(0)[32:])
    id_instruction   = Signal(modbv(0)[32:])
    id_rf_portA      = RFReadPort()
    id_rf_portB      = RFReadPort()
    id_imm           = Signal(modbv(0)[32:])
    id_rs1_data      = Signal(modbv(0)[32:])
    id_rs2_data      = Signal(modbv(0)[32:])
    id_op1           = Signal(modbv(0)[32:])
    id_op2           = Signal(modbv(0)[32:])
    id_op1_data      = Signal(modbv(0)[32:])
    id_op2_data      = Signal(modbv(0)[32:])
    id_mem_wdata     = Signal(modbv(0)[32:])
    id_pc_brjmp      = Signal(modbv(0)[32:])
    id_pc_jalr       = Signal(modbv(0)[32:])
    id_wb_addr       = Signal(modbv(0)[5:])
    id_csr_addr      = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])
    id_csr_wdata     = Signal(modbv(0)[32:])
    id_csr_cmd       = Signal(modbv(0)[CSRCMD.SZ_CMD:])
    ex_pc            = Signal(modbv(0)[32:])
    ex_data_out      = Signal(modbv(0)[32:])
    ex_alu_funct     = Signal(modbv(0)[ALUOp.SZ_OP:])
    ex_mem_wdata     = Signal(modbv(0)[32:])
    ex_mem_type      = Signal(modbv(0)[Consts.SZ_MT:])
    ex_mem_funct     = Signal(False)
    ex_mem_valid     = Signal(False)
    ex_mem_data_sel  = Signal(modbv(0)[Consts.SZ_WB:])
    ex_wb_addr       = Signal(modbv(0)[5:])
    ex_wb_we         = Signal(False)
    ex_op1_data      = Signal(modbv(0)[32:])
    ex_op2_data      = Signal(modbv(0)[32:])
    aluIO            = ALUPortIO()
    ex_csr_addr      = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])
    ex_csr_wdata     = Signal(modbv(0)[32:])
    ex_csr_cmd       = Signal(modbv(0)[CSRCMD.SZ_CMD:])
    exc_pc           = Signal(modbv(0)[32:])
    mem_pc           = Signal(modbv(0)[32:])
    mem_alu_out      = Signal(modbv(0)[32:])
    mem_mem_wdata    = Signal(modbv(0)[32:])
    mem_mem_type     = Signal(modbv(0)[Consts.SZ_MT:])
    mem_mem_funct    = Signal(False)
    mem_mem_valid    = Signal(False)
    mem_mem_data_sel = Signal(modbv(0)[Consts.SZ_WB:])
    mem_wb_addr      = Signal(modbv(0)[5:])
    mem_wb_wdata     = Signal(modbv(0)[32:])
    mem_wb_we        = Signal(False)
    csr_rw           = CSRFileRWIO()
    csr_exc_io       = CSRExceptionIO()
    mem_mem_data     = Signal(modbv(0)[32:])
    mem_csr_addr     = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])
    mem_csr_wdata    = Signal(modbv(0)[32:])
    mem_csr_rdata    = Signal(modbv(0)[32:])
    mem_csr_cmd      = Signal(modbv(0)[CSRCMD.SZ_CMD:])
    wb_pc            = Signal(modbv(0)[32:])
    wb_wb_addr       = Signal(modbv(0)[5:])
    wb_wb_wdata      = Signal(modbv(0)[32:])
    wb_wb_we         = Signal(False)
    wb_rf_writePort  = RFWritePort()

    # A stage
    # ----------------------------------------------------------------------
    pc_mux = Mux4(ctrlIO.pc_select,  # noqa
                  if_pc_next,
                  id_pc_brjmp,
                  id_pc_jalr,
                  exc_pc,
                  a_pc)

    # IF stage
    # ----------------------------------------------------------------------
    @always(clk.posedge)
    def pc():
        if rst == 1:
            if_pc.next = Consts.START_ADDR
        else:
            if (not ctrlIO.id_stall and not ctrlIO.full_stall) | ctrlIO.pipeline_kill:
                if_pc.next = a_pc

    @always_comb
    def _pc_next():
        ctrlIO.imem_pipeline.addr.next  = if_pc
        if_pc_next.next                 = if_pc + 4
        if_instruction.next             = ctrlIO.imem_pipeline.rdata
        ctrlIO.imem_pipeline.wdata.next = 0xDEADC0DE
        ctrlIO.imem_pipeline.typ.next   = Consts.MT_W
        ctrlIO.imem_pipeline.fcn.next   = Consts.M_RD
        ctrlIO.imem_pipeline.valid.next = True

    # ID stage
    # ----------------------------------------------------------------------
    @always(clk.posedge)
    def ifid():
        if rst == 1:
            id_pc.next          = 0
            id_instruction.next = Consts.BUBBLE
        else:
            id_pc.next          = (id_pc if ctrlIO.id_stall or ctrlIO.full_stall else (if_pc))
            id_instruction.next = (id_instruction if ctrlIO.id_stall or ctrlIO.full_stall else
                                   (Consts.BUBBLE if ctrlIO.pipeline_kill or ctrlIO.if_kill else
                                    (if_instruction)))

    reg_file = RegisterFile(clk,  # noqa
                            id_rf_portA,
                            id_rf_portB,
                            wb_rf_writePort)

    op1_data_fwd = Mux4(ctrlIO.id_fwd1_select,  # noqa
                        id_rs1_data,
                        ex_data_out,
                        mem_wb_wdata,
                        wb_wb_wdata,
                        id_op1)

    op2_data_fwd = Mux4(ctrlIO.id_fwd2_select,  # noqa
                        id_rs2_data,
                        ex_data_out,
                        mem_wb_wdata,
                        wb_wb_wdata,
                        id_op2)

    imm_gen = IMMGen(ctrlIO.id_sel_imm,  # noqa
                     id_instruction,
                     id_imm)

    op1_mux = Mux4(ctrlIO.id_op1_select,  # noqa
                   id_op1,
                   id_pc,
                   0x00000000,
                   0x00000BAD,
                   id_op1_data)

    op2_mux = Mux4(ctrlIO.id_op2_select,  # noqa
                   id_op2,
                   id_imm,
                   0x00000004,
                   0x00000000,
                   id_op2_data)

    @always_comb
    def _id_assignment():
        ctrlIO.id_instruction.next     = id_instruction
        id_rf_portA.ra.next            = id_instruction[20:15]
        id_rf_portB.ra.next            = id_instruction[25:20]
        ctrlIO.id_rs1_addr.next        = id_instruction[20:15]
        ctrlIO.id_rs2_addr.next        = id_instruction[25:20]
        id_rs1_data.next               = id_rf_portA.rd
        id_rs2_data.next               = id_rf_portB.rd
        id_wb_addr.next                = id_instruction[12:7]
        id_csr_addr.next               = id_instruction[32:20]
        id_mem_wdata.next              = id_op2
        id_pc_brjmp.next               = id_pc.signed() + id_imm.signed()
        id_pc_jalr.next                = id_op1.signed() + id_imm.signed()
        id_csr_addr.next               = id_instruction[32:20]
        id_csr_cmd.next                = ctrlIO.id_csr_cmd
        id_csr_wdata.next              = id_instruction[20:15] if id_instruction[14] else id_op1
        ctrlIO.csr_interrupt.next      = csr_exc_io.interrupt
        ctrlIO.csr_interrupt_code.next = csr_exc_io.interrupt_code
        ctrlIO.id_op1.next             = id_op1
        ctrlIO.id_op2.next             = id_op2

    # EX stage
    # ----------------------------------------------------------------------
    @always(clk.posedge)
    def idex():
        if rst == 1:
            ex_pc.next           = 0
            ex_op1_data.next     = 0
            ex_op2_data.next     = 0
            ex_alu_funct.next    = ALUOp.OP_ADD
            ex_mem_type.next     = Consts.MT_X
            ex_mem_funct.next    = Consts.M_X
            ex_mem_valid.next    = False
            ex_mem_wdata.next    = 0
            ex_mem_data_sel.next = Consts.WB_X
            ex_wb_addr.next      = 0
            ex_wb_we.next        = False
            ex_csr_addr.next     = 0
            ex_csr_wdata.next    = 0
            ex_csr_cmd.next      = CSRCMD.CSR_IDLE
        else:
            ex_pc.next           = (ex_pc if (ctrlIO.id_stall or ctrlIO.full_stall) else (id_pc))
            ex_op1_data.next     = (ex_op1_data if (ctrlIO.id_stall or ctrlIO.full_stall) else (id_op1_data))
            ex_op2_data.next     = (ex_op2_data if (ctrlIO.id_stall or ctrlIO.full_stall) else (id_op2_data))
            ex_alu_funct.next    = (ex_alu_funct if (ctrlIO.id_stall or ctrlIO.full_stall) else (ctrlIO.id_alu_funct))
            ex_mem_type.next     = (ex_mem_type if (ctrlIO.id_stall or ctrlIO.full_stall) else (ctrlIO.id_mem_type))
            ex_mem_wdata.next    = (ex_mem_wdata if (ctrlIO.id_stall or ctrlIO.full_stall) else (id_mem_wdata))
            ex_mem_data_sel.next = (ex_mem_data_sel if (ctrlIO.id_stall or ctrlIO.full_stall) else (ctrlIO.id_mem_data_sel))
            ex_wb_addr.next      = (ex_wb_addr if (ctrlIO.id_stall or ctrlIO.full_stall) else (id_wb_addr))
            ex_csr_addr.next     = (ex_csr_addr if (ctrlIO.id_stall or ctrlIO.full_stall) else (id_csr_addr))
            ex_csr_wdata.next    = (ex_csr_wdata if (ctrlIO.id_stall or ctrlIO.full_stall) else (id_csr_wdata))
            ex_mem_funct.next    = (ex_mem_funct if ctrlIO.full_stall else
                                    (Consts.M_X if (ctrlIO.pipeline_kill or ctrlIO.id_kill or (ctrlIO.id_stall and not ctrlIO.full_stall)) else
                                     (ctrlIO.id_mem_funct)))
            ex_mem_valid.next    = (ex_mem_valid if ctrlIO.full_stall else
                                    (False if (ctrlIO.pipeline_kill or ctrlIO.id_kill or (ctrlIO.id_stall and not ctrlIO.full_stall)) else
                                     (ctrlIO.id_mem_valid)))
            ex_wb_we.next        = (ex_wb_we if ctrlIO.full_stall else
                                    (False if (ctrlIO.pipeline_kill or ctrlIO.id_kill or (ctrlIO.id_stall and not ctrlIO.full_stall)) else
                                     (ctrlIO.id_wb_we)))
            ex_csr_cmd.next      = (ex_csr_cmd if ctrlIO.full_stall else
                                    (modbv(CSRCMD.CSR_IDLE)[CSRCMD.SZ_CMD:] if (ctrlIO.pipeline_kill or ctrlIO.id_kill or (ctrlIO.id_stall and not ctrlIO.full_stall)) else
                                     (id_csr_cmd)))

    alu = ALU(clk, rst, aluIO)  # noqa

    @always_comb
    def _ex_assignments():
        aluIO.input1.next        = ex_op1_data
        aluIO.input2.next        = ex_op2_data
        aluIO.function.next      = ex_alu_funct
        aluIO.stall.next         = ctrlIO.full_stall
        aluIO.kill.next          = ctrlIO.pipeline_kill
        ex_data_out.next         = aluIO.output
        ctrlIO.ex_req_stall.next = aluIO.req_stall
        ctrlIO.ex_wb_we.next     = ex_wb_we
        ctrlIO.ex_wb_addr.next   = ex_wb_addr

    # MEM stage
    # ----------------------------------------------------------------------
    @always(clk.posedge)
    def exmem():
        if rst == 1:
            mem_pc.next           = 0
            mem_mem_valid.next    = False
            mem_alu_out.next      = 0
            mem_mem_wdata.next    = 0
            mem_mem_type.next     = Consts.MT_X
            mem_mem_funct.next    = Consts.M_X
            mem_mem_data_sel.next = Consts.WB_X
            mem_wb_addr.next      = 0
            mem_wb_we.next        = False
            mem_csr_addr.next     = 0
            mem_csr_wdata.next    = 0
            mem_csr_cmd.next      = CSRCMD.CSR_IDLE
        else:
            mem_pc.next           = (mem_pc if ctrlIO.full_stall else ex_pc)
            mem_alu_out.next      = (mem_alu_out if ctrlIO.full_stall else ex_data_out)
            mem_mem_wdata.next    = (mem_mem_wdata if ctrlIO.full_stall else ex_mem_wdata)
            mem_mem_type.next     = (mem_mem_type if ctrlIO.full_stall else ex_mem_type)
            mem_mem_funct.next    = (mem_mem_funct if ctrlIO.full_stall else ex_mem_funct)
            mem_mem_data_sel.next = (mem_mem_data_sel if ctrlIO.full_stall else ex_mem_data_sel)
            mem_wb_addr.next      = (mem_wb_addr if ctrlIO.full_stall else ex_wb_addr)
            mem_csr_addr.next     = (mem_csr_addr if ctrlIO.full_stall else ex_csr_addr)
            mem_csr_wdata.next    = (mem_csr_wdata if ctrlIO.full_stall else ex_csr_wdata)
            mem_mem_valid.next    = (mem_mem_valid if ctrlIO.full_stall else (False if ctrlIO.pipeline_kill else ex_mem_valid))
            mem_wb_we.next        = (mem_wb_we if ctrlIO.full_stall else (False if ctrlIO.pipeline_kill else ex_wb_we))
            mem_csr_cmd.next      = (mem_csr_cmd if (ctrlIO.full_stall) else (modbv(CSRCMD.CSR_IDLE)[CSRCMD.SZ_CMD:] if ctrlIO.pipeline_kill else ex_csr_cmd))

    csr = CSR(clk,  # noqa
              rst,
              csr_rw,
              csr_exc_io,
              ctrlIO.csr_retire,
              ctrlIO.csr_prv,
              ctrlIO.csr_illegal_access,
              toHost)

    mdata_mux = Mux4(mem_mem_data_sel,  # noqa
                     mem_alu_out,
                     mem_mem_data,
                     mem_csr_rdata,
                     0x0BADF00D,
                     mem_wb_wdata)

    exc_pc_mux = Mux2(ctrlIO.csr_eret,  # noqa
                      csr_exc_io.exception_handler,
                      csr_exc_io.epc,
                      exc_pc)

    @always_comb
    def _mem_assignments():
        ctrlIO.dmem_pipeline.addr.next      = mem_alu_out
        ctrlIO.dmem_pipeline.wdata.next     = mem_mem_wdata
        ctrlIO.dmem_pipeline.fcn.next       = mem_mem_funct
        ctrlIO.dmem_pipeline.typ.next       = mem_mem_type
        ctrlIO.dmem_pipeline.valid.next     = mem_mem_valid
        mem_mem_data.next                   = ctrlIO.dmem_pipeline.rdata
        csr_exc_io.exception.next           = ctrlIO.csr_exception
        csr_exc_io.exception_code.next      = ctrlIO.csr_exception_code
        csr_exc_io.eret.next                = ctrlIO.csr_eret
        csr_exc_io.exception_load_addr.next = mem_alu_out
        csr_exc_io.exception_pc.next        = mem_pc
        csr_rw.addr.next                    = mem_csr_addr
        csr_rw.cmd.next                     = mem_csr_cmd
        csr_rw.wdata.next                   = mem_csr_wdata
        mem_csr_rdata.next                  = csr_rw.rdata
        ctrlIO.mem_wb_we.next               = mem_wb_we
        ctrlIO.mem_wb_addr.next             = mem_wb_addr

    # WB stage
    # ----------------------------------------------------------------------
    @always(clk.posedge)
    def memwb():
        if rst == 1:
            wb_pc.next       = 0
            wb_wb_addr.next  = 0
            wb_wb_wdata.next = 0
            wb_wb_we.next    = False
        else:
            wb_pc.next       = (wb_pc if ctrlIO.full_stall else mem_pc)
            wb_wb_addr.next  = (wb_wb_addr if ctrlIO.full_stall else mem_wb_addr)
            wb_wb_wdata.next = (wb_wb_wdata if ctrlIO.full_stall else mem_wb_wdata)
            wb_wb_we.next    = (wb_wb_we if ctrlIO.full_stall else (False if ctrlIO.pipeline_kill else mem_wb_we))

    @always_comb
    def _wb_assignments():
        wb_rf_writePort.wa.next = wb_wb_addr
        wb_rf_writePort.wd.next = wb_wb_wdata
        wb_rf_writePort.we.next = wb_wb_we
        ctrlIO.wb_wb_we.next    = wb_wb_we
        ctrlIO.wb_wb_addr.next  = wb_wb_addr

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
