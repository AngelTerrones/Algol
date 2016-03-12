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
from Core.dpath import Datapath
from Core.cpath import Ctrlpath
from Core.cpath import CtrlIO
from Core.wishbone import WishboneMaster
from Core.wishbone import WishboneIntercon


def Core(clk,
         rst,
         imem,
         dmem,
         toHost):
    """
    Core top module.
    This module use interfaces, for use in an integrated SoC.

    :param clk:    System clock
    :param rst:    System reset
    :param imem:   Instruction memory port (Wishbone master)
    :paran dmem:   Data memory port (Wishbone master)
    :param toHost: CSR's mtohost register. For simulation purposes.
    """
    ctrl_dpath = CtrlIO()

    dpath = Datapath(clk,
                     rst,
                     ctrl_dpath,
                     toHost)
    cpath = Ctrlpath(clk,
                     rst,
                     ctrl_dpath,
                     imem,
                     dmem)

    return dpath, cpath


def CoreHDL(clk,
            rst,
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
    imem_m = WishboneMaster(imem)
    dmem_m = WishboneMaster(dmem)
    core = Core(clk=clk,
                rst=rst,
                toHost=toHost,
                imem=imem_m,
                dmem=dmem_m)

    @always_comb
    def assign():
        imem_addr_o.next    = imem_m.addr_o
        imem_dat_o.next     = imem_m.dat_o
        imem_sel_o.next     = imem_m.sel_o
        imem_cti_o.next     = imem_m.cti_o
        imem_cyc_o.next     = imem_m.cyc_o
        imem_we_o.next      = imem_m.we_o
        imem_stb_o.next     = imem_m.stb_o
        imem_m.dat_i.next   = imem_dat_i
        imem_m.stall_i.next = imem_stall_i
        imem_m.ack_i.next   = imem_ack_i
        imem_m.err_i.next   = imem_err_i

        dmem_addr_o.next    = dmem_m.addr_o
        dmem_dat_o.next     = dmem_m.dat_o
        dmem_sel_o.next     = dmem_m.sel_o
        dmem_cti_o.next     = dmem_m.cti_o
        dmem_cyc_o.next     = dmem_m.cyc_o
        dmem_we_o.next      = dmem_m.we_o
        dmem_stb_o.next     = dmem_m.stb_o
        dmem_m.dat_i.next   = dmem_dat_i
        dmem_m.stall_i.next = dmem_stall_i
        dmem_m.ack_i.next   = dmem_ack_i
        dmem_m.err_i.next   = dmem_err_i

    return core, assign

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
