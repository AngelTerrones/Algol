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
import os.path
from myhdl import Signal
from myhdl import modbv
from myhdl import always_comb
from myhdl import always
from myhdl import instances
from myhdl import concat
from Core.memIO import MemOp


def LoadMemory(size_mem: int,
               bin_file: str,
               bytes_x_line: int,
               memory: list):
    """
    Load a HEX file. The file have (2 * NBYTES + 1) por line.
    """
    n_lines = int(os.path.getsize(bin_file) / (2 * bytes_x_line + 1))  # calculate number of lines in the file
    bytes_file = n_lines * bytes_x_line
    assert bytes_file <= size_mem, "Error, HEX file is to big: {0} < {1}".format(size_mem, bytes_file)
    word_x_line = bytes_x_line >> 2

    with open(bin_file) as f:
        lines_f = [line.strip() for line in f]
        lines = [line[8 * i:8 * (i + 1)] for line in lines_f for i in range(word_x_line - 1, -1, -1)]

    for addr in range(size_mem >> 2):
        data = int(lines[addr], 16)
        memory[addr] = Signal(modbv(data)[32:])


def Memory(clk,
           rst,
           imem,
           dmem,
           SIZE,
           HEX,
           BYTES_X_LINE):
    """
    Test memory.
    """
    assert SIZE >= 2**12, "Memory depth must be a positive number. Min value= 4 KB."
    assert not (SIZE & (SIZE - 1)), "Memory size must be a power of 2"
    assert type(BYTES_X_LINE) == int and BYTES_X_LINE > 0, "Number of bytes por line must be a positive number"
    assert not (BYTES_X_LINE & (BYTES_X_LINE - 1)), "Number of bytes por line must be a power of 2"
    assert type(HEX) == str and len(HEX) != 0, "Please, indicate a valid name for the bin file."
    assert os.path.isfile(HEX), "HEX file does not exist. Please, indicate a valid name"

    aw           = int(ceil(log(SIZE, 2)))
    bytes_x_line = BYTES_X_LINE
    i_data_o     = Signal(modbv(0)[32:])
    d_data_o     = Signal(modbv(0)[32:])
    _memory      = [None for ii in range(0, 2**(aw - 2))]  # WORDS, no bytes
    _imem_addr   = Signal(modbv(0)[30:])
    _dmem_addr   = Signal(modbv(0)[30:])

    LoadMemory(SIZE, HEX, bytes_x_line, _memory)

    @always(clk.posedge)
    def set_ready_signal():
        imem.ready.next = False if rst else imem.valid
        dmem.ready.next = False if rst else dmem.valid

    @always_comb
    def assignment_data_o():
        imem.rdata.next = i_data_o if imem.ready else 0xDEADF00D
        dmem.rdata.next = d_data_o if dmem.ready else 0xDEADF00D

    @always(clk.posedge)
    def set_fault():
        imem.fault.next = False
        dmem.fault.next = False

    @always_comb
    def assignment_addr():
        # This memory is addressed by word, not byte. Ignore the 2 LSB.
        _imem_addr.next = imem.addr[aw:2]
        _dmem_addr.next = dmem.addr[aw:2]

    @always(clk.posedge)
    def imem_rtl():
        i_data_o.next = _memory[_imem_addr]

        if imem.fcn == MemOp.M_WR:
            we            = imem.wr
            data          = imem.wdata
            i_data_o.next = imem.wdata
            _memory[_imem_addr].next = concat(data[8:0] if we[0] and imem.valid else _memory[_imem_addr][8:0],
                                              data[16:8] if we[1] and imem.valid else _memory[_imem_addr][16:8],
                                              data[24:16] if we[2] and imem.valid else _memory[_imem_addr][24:16],
                                              data[32:24] if we[3] and imem.valid else _memory[_imem_addr][32:24])

    @always(clk.posedge)
    def dmem_rtl():
        d_data_o.next = _memory[_dmem_addr]

        if dmem.fcn == MemOp.M_WR:
            we            = dmem.wr
            data          = dmem.wdata
            d_data_o.next = dmem.wdata
            _memory[_dmem_addr].next = concat(data[8:0] if we[0] and dmem.valid else _memory[_dmem_addr][8:0],
                                              data[16:8] if we[1] and dmem.valid else _memory[_dmem_addr][16:8],
                                              data[24:16] if we[2] and dmem.valid else _memory[_dmem_addr][24:16],
                                              data[32:24] if we[3] and dmem.valid else _memory[_dmem_addr][32:24])

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
