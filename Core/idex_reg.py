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

from myhdl import always
from myhdl import modbv
from Core.consts import Consts
from Core.alu import ALUOp
from Core.memIO import MemOp
from Core.csr import CSRCMD


def IDEXReg(clk,
            rst,
            id_stall,
            full_stall,
            id_kill,
            pipeline_kill,
            id_pc,
            id_op1_data,
            id_op2_data,
            id_alu_funct,
            id_mem_type,
            id_mem_funct,
            id_mem_valid,
            id_mem_wdata,
            id_mem_data_sel,
            id_wb_addr,
            id_wb_we,
            id_csr_addr,
            id_csr_wdata,
            id_csr_cmd,
            ex_pc,
            ex_op1_data,
            ex_op2_data,
            ex_alu_funct,
            ex_mem_type,
            ex_mem_funct,
            ex_mem_valid,
            ex_mem_wdata,
            ex_mem_data_sel,
            ex_wb_addr,
            ex_wb_we,
            ex_csr_addr,
            ex_csr_wdata,
            ex_csr_cmd):
    @always(clk.posedge)
    def rtl():
        if rst == 1:
            ex_pc.next           = 0
            ex_op1_data.next     = 0
            ex_op2_data.next     = 0
            ex_alu_funct.next    = ALUOp.OP_ADD
            ex_mem_type.next     = MemOp.MT_X
            ex_mem_funct.next    = MemOp.M_X
            ex_mem_valid.next    = False
            ex_mem_wdata.next    = 0
            ex_mem_data_sel.next = Consts.WB_X
            ex_wb_addr.next      = 0
            ex_wb_we.next        = False
            ex_csr_addr.next     = 0
            ex_csr_wdata.next    = 0
            ex_csr_cmd.next      = CSRCMD.CSR_IDLE
        else:
            # id_stall and full_stall are not related.
            ex_pc.next           = (ex_pc if (id_stall or full_stall) else (id_pc))
            ex_op1_data.next     = (ex_op1_data if (id_stall or full_stall) else (id_op1_data))
            ex_op2_data.next     = (ex_op2_data if (id_stall or full_stall) else (id_op2_data))
            ex_alu_funct.next    = (ex_alu_funct if (id_stall or full_stall) else (id_alu_funct))
            ex_mem_type.next     = (ex_mem_type if (id_stall or full_stall) else (id_mem_type))
            ex_mem_wdata.next    = (ex_mem_wdata if (id_stall or full_stall) else (id_mem_wdata))
            ex_mem_data_sel.next = (ex_mem_data_sel if (id_stall or full_stall) else (id_mem_data_sel))
            ex_wb_addr.next      = (ex_wb_addr if (id_stall or full_stall) else (id_wb_addr))
            ex_csr_addr.next     = (ex_csr_addr if (id_stall or full_stall) else (id_csr_addr))
            ex_csr_wdata.next    = (ex_csr_wdata if (id_stall or full_stall) else (id_csr_wdata))
            ex_mem_funct.next    = (ex_mem_funct if full_stall else
                                    (MemOp.M_X if (pipeline_kill or id_kill or (id_stall and not full_stall)) else
                                     (id_mem_funct)))
            ex_mem_valid.next    = (ex_mem_valid if full_stall else
                                    (False if (pipeline_kill or id_kill or (id_stall and not full_stall)) else
                                     (id_mem_valid)))
            ex_wb_we.next        = (ex_wb_we if full_stall else
                                    (False if (pipeline_kill or id_kill or (id_stall and not full_stall)) else
                                     (id_wb_we)))
            ex_csr_cmd.next      = (ex_csr_cmd if full_stall else
                                    (modbv(CSRCMD.CSR_IDLE)[CSRCMD.SZ_CMD:] if (pipeline_kill or id_kill or (id_stall and not full_stall)) else
                                     (id_csr_cmd)))
    return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
