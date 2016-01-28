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
from math import ceil
from math import log
from myhdl import Signal
from myhdl import modbv
from myhdl import always_comb
from myhdl import always
from myhdl import instances
from Algol.memIO import MemoryOpConstant
from Algol.memIO import MemPortIO


class Memory:
    def __init__(self,
                 clk:  Signal,
                 rst:  Signal,
                 imem: MemPortIO,
                 dmem: MemPortIO,
                 SIZE: int,
                 BIN:  str):
        assert SIZE >= 2**12, "Memory size must be a positive number. Min value= 4 KB."
        assert type(BIN) == str and len(BIN) != 0, "Please, indicate a valid name for the bin file."

        aw              = int(ceil(log(SIZE, 2)))
        self.clk        = clk
        self.rst        = rst
        self.imem       = imem
        self.dmem       = dmem
        self._data_o    = Signal(modbv(0)[32:])
        self._memory    = [Signal(modbv(0)[32:]) for ii in range(0, 2**aw)]
        self._imem_addr = Signal(modbv(0)[30:])
        self._dmem_addr = Signal(modbv(0)[30:])

        self.LoadMemory(2**aw, BIN)

    def LoadMemory(size: int, bin_file: str):
        pass

    def GetRTL(self):
        @always(self.clk)
        def set_ready_signal():
            self.imem.resp.valid.next = False if self.rst else self.imem.req.valid
            self.dmem.resp.valid.next = False if self.rst else self.dmem.req.valid

        @always_comb
        def assignment_data_o():
            self.imem.resp.data.next = self._data_o if self.imem.resp.valid else None
            self.dmem.resp.data.next = self._data_o if self.dmem.resp.valid else None

        @always_comb
        def set_fault():
            self.imem.resp.fault.next = False
            self.dmem.resp.fault.next = False

        @always_comb
        def assignment_addr():
            # This memory is addressed by word, not byte. Ignore the 2 LSB.
            self._imem_addr = self.imem.req.add[32:2]
            self._dmem_addr = self.dmem.req.add[32:2]

        @always(self.clk)
        def imem_rtl():
            self._data_o.next = self._memory[self._imem_addr]

            if self.imem.req.fcn == MemoryOpConstant.M_WR:
                we                = self.imem.req.wr
                data              = self.imem.req.data
                self._data_o.next = self.imem.req.data
                self._memory[self._imem_addr][8:0].next   = data if we[0] and self.imem.req.valid else self._memory[self._imem_addr][8:0]
                self._memory[self._imem_addr][16:8].next  = data if we[1] and self.imem.req.valid else self._memory[self._imem_addr][16:8]
                self._memory[self._imem_addr][24:16].next = data if we[2] and self.imem.req.valid else self._memory[self._imem_addr][24:16]
                self._memory[self._imem_addr][32:24].next = data if we[3] and self.imem.req.valid else self._memory[self._imem_addr][32:24]

        @always(self.clk)
        def dmem_rtl():
            self._data_o.next = self._memory[self._imem_addr]

            if self.dmem.req.fcn == MemoryOpConstant.M_WR:
                we                = self.dmem.req.wr
                data              = self.dmem.req.data
                self._data_o.next = self.dmem.req.data
                self._memory[self._dmem_addr][8:0].next   = data if we[0] and self.dmem.req.valid else self._memory[self._dmem_addr][8:0]
                self._memory[self._dmem_addr][16:8].next  = data if we[1] and self.dmem.req.valid else self._memory[self._dmem_addr][16:8]
                self._memory[self._dmem_addr][24:16].next = data if we[2] and self.dmem.req.valid else self._memory[self._dmem_addr][24:16]
                self._memory[self._dmem_addr][32:24].next = data if we[3] and self.dmem.req.valid else self._memory[self._dmem_addr][32:24]

        return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
