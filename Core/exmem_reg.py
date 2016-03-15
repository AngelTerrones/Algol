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
from Core.csr import CSRCMD


def EXMEMReg(clk,
             rst,
             full_stall,
             pipeline_kill,
             ex_pc,
             ex_alu_out,
             ex_mem_wdata,
             ex_mem_type,
             ex_mem_funct,
             ex_mem_valid,
             ex_mem_data_sel,
             ex_wb_addr,
             ex_wb_we,
             ex_csr_addr,
             ex_csr_wdata,
             ex_csr_cmd,
             mem_pc,
             mem_alu_out,
             mem_mem_wdata,
             mem_mem_type,
             mem_mem_funct,
             mem_mem_valid,
             mem_mem_data_sel,
             mem_wb_addr,
             mem_wb_we,
             mem_csr_addr,
             mem_csr_wdata,
             mem_csr_cmd):
    @always(clk.posedge)
    def rtl():
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
            mem_pc.next           = (mem_pc if full_stall else ex_pc)
            mem_alu_out.next      = (mem_alu_out if full_stall else ex_alu_out)
            mem_mem_wdata.next    = (mem_mem_wdata if full_stall else ex_mem_wdata)
            mem_mem_type.next     = (mem_mem_type if full_stall else ex_mem_type)
            mem_mem_funct.next    = (mem_mem_funct if full_stall else ex_mem_funct)
            mem_mem_data_sel.next = (mem_mem_data_sel if full_stall else ex_mem_data_sel)
            mem_wb_addr.next      = (mem_wb_addr if full_stall else ex_wb_addr)
            mem_csr_addr.next     = (mem_csr_addr if full_stall else ex_csr_addr)
            mem_csr_wdata.next    = (mem_csr_wdata if full_stall else ex_csr_wdata)
            mem_mem_valid.next    = (mem_mem_valid if full_stall else (False if pipeline_kill else ex_mem_valid))
            mem_wb_we.next        = (mem_wb_we if full_stall else (False if pipeline_kill else ex_wb_we))
            mem_csr_cmd.next      = (mem_csr_cmd if (full_stall) else (modbv(CSRCMD.CSR_IDLE)[CSRCMD.SZ_CMD:] if pipeline_kill else ex_csr_cmd))
    return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
