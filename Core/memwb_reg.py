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


def MEMWBReg(clk,
             rst,
             full_stall,
             pipeline_kill,
             mem_pc,
             mem_wb_addr,
             mem_wb_wdata,
             mem_wb_we,
             wb_pc,
             wb_wb_addr,
             wb_wb_wdata,
             wb_wb_we):
    @always(clk.posedge)
    def rtl():
        if rst == 1:
            wb_pc.next       = 0
            wb_wb_addr.next  = 0
            wb_wb_wdata.next = 0
            wb_wb_we.next    = False
        else:
            wb_pc.next       = (wb_pc if full_stall else mem_pc)
            wb_wb_addr.next  = (wb_wb_addr if full_stall else mem_wb_addr)
            wb_wb_wdata.next = (wb_wb_wdata if full_stall else mem_wb_wdata)
            wb_wb_we.next    = (wb_wb_we if full_stall else (False if pipeline_kill else mem_wb_we))
    return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
