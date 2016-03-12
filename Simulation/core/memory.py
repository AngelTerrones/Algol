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
from Core.wishbone import WishboneSlave


def LoadMemory(size_mem,
               bin_file,
               bytes_x_line,
               memory):
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

    :param clk:          System clock
    :param rst:          System reset
    :param imem:         Instruction memory wishbone Interconnect
    :param dmem:         Data memory wishbone Interconnect
    :param SIZE:         Mmeory size (bytes)
    :param HEX:          Hex file to load
    :param BYTES_X_LINE: Data width in bytes
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
    def set_ack_signal():
        """
        Assert the ack signal one clock cycle.
        """
        imem.ack_o.next = False if rst else imem.stb_i and imem.cyc_i and not imem.ack_o
        dmem.ack_o.next = False if rst else dmem.stb_i and dmem.cyc_i and not dmem.ack_o

    @always_comb
    def assignment_data_o():
        imem.dat_o.next = i_data_o if imem.ack_o else 0xDEADF00D
        dmem.dat_o.next = d_data_o if dmem.ack_o else 0xDEADF00D

    @always(clk.posedge)
    def set_fault():
        imem.err_o.next = False
        dmem.err_o.next = False

    @always(clk.posedge)
    def set_stall():
        imem.stall_o.next = False
        dmem.stall_o.next = False

    @always_comb
    def assignment_addr():
        # This memory is addressed by word, not byte. Ignore the 2 LSB.
        _imem_addr.next = imem.addr_i[aw:2]
        _dmem_addr.next = dmem.addr_i[aw:2]

    @always(clk.posedge)
    def imem_rtl():
        i_data_o.next = _memory[_imem_addr]

        if imem.we_i and imem.stb_i:
            we            = imem.sel_i
            data          = imem.dat_i
            i_data_o.next = imem.dat_i
            _memory[_imem_addr].next = concat(data[32:24] if we[3] else _memory[_imem_addr][32:24],
                                              data[24:16] if we[2] else _memory[_imem_addr][24:16],
                                              data[16:8] if we[1] else _memory[_imem_addr][16:8],
                                              data[8:0] if we[0] else _memory[_imem_addr][8:0])

    @always(clk.posedge)
    def dmem_rtl():
        d_data_o.next = _memory[_dmem_addr]

        if dmem.we_i and dmem.stb_i:
            we            = dmem.sel_i
            data          = dmem.dat_i
            d_data_o.next = dmem.dat_i
            _memory[_dmem_addr].next = concat(data[32:24] if we[3] else _memory[_dmem_addr][32:24],
                                              data[24:16] if we[2] else _memory[_dmem_addr][24:16],
                                              data[16:8] if we[1] else _memory[_dmem_addr][16:8],
                                              data[8:0] if we[0] else _memory[_dmem_addr][8:0])

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
