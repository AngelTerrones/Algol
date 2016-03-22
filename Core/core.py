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

from myhdl import always_comb
from myhdl import Signal
from Core.dpath import Datapath
from Core.cpath import Ctrlpath
from Core.cpath import CtrlIO
from Core.wishbone import WishboneIntercon
from Core.icache import ICache
from Core.dcache import DCache


def Core(clk_i,
         rst_i,
         imem,
         dmem,
         toHost,
         IC_BLOCK_WIDTH=3,
         IC_SET_WIDTH=8,
         IC_NUM_WAYS=2,
         DC_BLOCK_WIDTH=3,
         DC_SET_WIDTH=8,
         DC_NUM_WAYS=2):
    """
    Core top module.
    This module use interfaces, for use in an integrated SoC.

    :param clk:    System clock
    :param rst:    System reset
    :param imem:   Instruction memory port (Wishbone master)
    :paran dmem:   Data memory port (Wishbone master)
    :param toHost: CSR's mtohost register. For simulation purposes.
    """
    ctrl_dpath   = CtrlIO()
    icache_flush = Signal(False)
    dcache_flush = Signal(False)
    cpu_intercon = WishboneIntercon()
    mem_intercon = WishboneIntercon()

    dpath = Datapath(clk_i,
                     rst_i,
                     ctrl_dpath,
                     toHost)
    cpath = Ctrlpath(clk_i,
                     rst_i,
                     ctrl_dpath,
                     icache_flush,
                     dcache_flush,
                     cpu_intercon,
                     mem_intercon)
    icache = ICache(clk_i=clk_i,
                    rst_i=rst_i,
                    cpu=cpu_intercon,
                    mem=imem,
                    invalidate=icache_flush,
                    D_WIDTH=32,
                    BLOCK_WIDTH=IC_BLOCK_WIDTH,
                    SET_WIDTH=IC_SET_WIDTH,
                    WAYS=IC_NUM_WAYS,
                    LIMIT_WIDTH=32)
    dcache = DCache(clk_i=clk_i,
                    rst_i=rst_i,
                    cpu=mem_intercon,
                    mem=dmem,
                    invalidate=dcache_flush,
                    D_WIDTH=32,
                    BLOCK_WIDTH=DC_BLOCK_WIDTH,
                    SET_WIDTH=DC_SET_WIDTH,
                    WAYS=DC_NUM_WAYS,
                    LIMIT_WIDTH=32)

    return dpath, cpath, icache, dcache


def CoreHDL(clk_i,
            rst_i,
            toHost,
            imem_addr_o,
            imem_dat_o,
            imem_sel_o,
            imem_cti_o,
            imem_cyc_o,
            imem_we_o,
            imem_stb_o,
            imem_dat_i,
            imem_stall_i,
            imem_ack_i,
            imem_err_i,
            dmem_addr_o,
            dmem_dat_o,
            dmem_sel_o,
            dmem_cti_o,
            dmem_cyc_o,
            dmem_we_o,
            dmem_stb_o,
            dmem_dat_i,
            dmem_stall_i,
            dmem_ack_i,
            dmem_err_i):
    """
    Core top Module.
    This module use single ports, for verilog translation, and avoid
    generating ugly names for top ports.
    """

    imem = WishboneIntercon()
    dmem = WishboneIntercon()
    core = Core(clk_i=clk_i,
                rst_i=rst_i,
                toHost=toHost,
                imem=imem,
                dmem=dmem)

    @always_comb
    def assign():
        # Instruction memory
        imem_addr_o.next = imem.addr
        imem_dat_o.next  = imem.dat_o
        imem_sel_o.next  = imem.sel
        imem_cti_o.next  = imem.cti
        imem_cyc_o.next  = imem.cyc
        imem_we_o.next   = imem.we
        imem_stb_o.next  = imem.stb
        imem.dat_i.next  = imem_dat_i
        imem.stall.next  = imem_stall_i
        imem.ack.next    = imem_ack_i
        imem.err.next    = imem_err_i
        # Data memory
        dmem_addr_o.next = dmem.addr
        dmem_dat_o.next  = dmem.dat_o
        dmem_sel_o.next  = dmem.sel
        dmem_cti_o.next  = dmem.cti
        dmem_cyc_o.next  = dmem.cyc
        dmem_we_o.next   = dmem.we
        dmem_stb_o.next  = dmem.stb
        dmem.dat_i.next  = dmem_dat_i
        dmem.stall.next  = dmem_stall_i
        dmem.ack.next    = dmem_ack_i
        dmem.err.next    = dmem_err_i

    return core, assign

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
