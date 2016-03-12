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

from Simulation.core.memory import Memory
from Core.wishbone import WishboneSlave
from Core.wishbone import WishboneIntercon
from Simulation.modules.ram_bus import RamBus
import random
from myhdl import instance
from myhdl import Signal
from myhdl import Simulation
from myhdl import StopSimulation
import pytest


MEM_SIZE      = 2**15  # Bytes
MEM_TEST_FILE = 'Simulation/modules/mem.hex'
BYTES_X_LINE  = 16


def _testbench():
    rb = RamBus(memory_size=MEM_SIZE >> 2)
    imem = WishboneSlave(rb.imem_intercon)
    dmem = WishboneSlave(rb.dmem_intercon)
    dut = Memory(clk=rb.clk,
                 rst=rb.rst,
                 imem=imem,
                 dmem=dmem,
                 SIZE=MEM_SIZE,
                 HEX=MEM_TEST_FILE,
                 BYTES_X_LINE=BYTES_X_LINE)

    tb_clk = rb.gen_clocks()

    with open(MEM_TEST_FILE) as f:
        words_x_line = BYTES_X_LINE >> 2
        lines_f      = [line.strip() for line in f]
        lines        = [line[8 * i:8 * (i + 1)] for line in lines_f for i in range(words_x_line - 1, -1, -1)]

    @instance
    def stimulus():
        # Testing the file loading
        for addr in range(rb.depth):  # Address in words
            yield rb.read(addr << 2)  # Address in bytes
            data = int(lines[addr], 16)
            assert rb.dmem.dat_i == data, "Data loading: Data mismatch! Addr = {0:#x}: {1} != {2:#x}".format(addr << 2,
                                                                                                             hex(rb.dmem.dat_i),
                                                                                                             data)

        # Testing R/W
        for addr in range(rb.depth):
            data = random.randint(0, 2**32)
            yield rb.write(addr << 2, data)

        for addr in range(rb.depth):  # Address in words
            yield rb.read(addr << 2)  # Address in bytes
            assert rb.dmem.dat_i == rb.mirror_mem[addr], "R/W: Data mismatch! Addr = {0:#x}".format(addr << 2)

        raise StopSimulation

    return dut, tb_clk, stimulus


def gen_test_file():
    """
    Generate a HEX file, with random values.
    """
    with open(MEM_TEST_FILE, 'w') as f:
        depth = int(MEM_SIZE / BYTES_X_LINE)
        for _ in range(depth):
            for _ in range(BYTES_X_LINE >> 2):
                f.write(format(random.randint(0, 2**32), 'x').zfill(8))
            f.write('\n')


def test_memory():
    """
    Memory: Test load and R/W operations.
    """
    gen_test_file()
    sim = Simulation(_testbench())
    sim.run()


def test_memory_assertions():
    """
    Memory: Test assertions
    """
    clk = Signal(False)
    rst = Signal(False)
    imem_intercon = WishboneIntercon()
    dmem_intercon = WishboneIntercon()
    imem = WishboneSlave(imem_intercon)
    dmem = WishboneSlave(dmem_intercon)

    # Test minimun size
    with pytest.raises(AssertionError):
        Memory(clk=clk,
               rst=rst,
               imem=imem,
               dmem=dmem,
               SIZE=20,
               HEX=MEM_TEST_FILE,
               BYTES_X_LINE=BYTES_X_LINE)

    # test valid filename
    with pytest.raises(AssertionError):
        Memory(clk=clk,
               rst=rst,
               imem=imem,
               dmem=dmem,
               SIZE=MEM_SIZE,
               HEX='ERROR',
               BYTES_X_LINE=BYTES_X_LINE)

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
