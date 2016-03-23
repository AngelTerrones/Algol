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
from Core.wishbone import WishboneIntercon
from Core.dcache import DCache
from Simulation.modules.ram_bus import RamBus
import random
from myhdl import instance
from myhdl import always_comb
from myhdl import Signal
from myhdl import Simulation
from myhdl import StopSimulation
from myhdl import delay
from myhdl import Error
from myhdl import traceSignals
from myhdl import instances
import pytest


MEM_SIZE      = 2**15  # Bytes
MEM_TEST_FILE = 'Simulation/modules/mem.hex'
BYTES_X_LINE  = 16


def _testbench():
    rb         = RamBus(memory_size=MEM_SIZE >> 2)
    cpu        = WishboneIntercon()
    dmem       = WishboneIntercon()
    invalidate = Signal(False)
    dut = DCache(clk_i=rb.clkb,  # noqa
                 rst_i=False,
                 cpu=rb.dmem_intercon,
                 mem=dmem,
                 invalidate=invalidate,
                 D_WIDTH=32,
                 BLOCK_WIDTH=3,
                 SET_WIDTH=5,
                 WAYS=4,
                 LIMIT_WIDTH=32)
    mem = Memory(clka_i=rb.clka,  # noqa
                 rsta_i=False,
                 imem=rb.imem_intercon,
                 clkb_i=rb.clkb,
                 rstb_i=False,
                 dmem=dmem,
                 SIZE=MEM_SIZE,
                 HEX=MEM_TEST_FILE,
                 BYTES_X_LINE=BYTES_X_LINE)

    tb_clk = rb.gen_clocks()  # noqa

    # Load the test file. Used as reference.
    with open(MEM_TEST_FILE) as f:
        words_x_line = BYTES_X_LINE >> 2
        lines_f = [line.strip() for line in f]
        lines = [line[8 * i:8 * (i + 1)] for line in lines_f for i in range(words_x_line - 1, -1, -1)]

    @instance
    def timeout():
        # Avoid waiting until armageddon
        yield delay(1000000)
        raise Error("Test failed: Timeout")

    @always_comb
    def port_assign():
        # This assignments are for the purpose of being able to watch this
        # signal GTKWave.
        cpu.addr.next  = rb.dmem_intercon.addr
        cpu.dat_o.next = rb.dmem_intercon.dat_o
        cpu.dat_i.next = rb.dmem_intercon.dat_i
        cpu.sel.next   = rb.dmem_intercon.sel
        cpu.cti.next   = rb.dmem_intercon.cti
        cpu.cyc.next   = rb.dmem_intercon.cyc
        cpu.we.next    = rb.dmem_intercon.we
        cpu.stb.next   = rb.dmem_intercon.stb
        cpu.stall.next = rb.dmem_intercon.stall
        cpu.ack.next   = rb.dmem_intercon.ack
        cpu.err.next   = rb.dmem_intercon.err

    @instance
    def stimulus():
        # Read data from memory: first round
        for addr in range(rb.depth >> 5):  # Address in words
            yield rb.read(addr << 2)  # Address in bytes
            data = int(lines[addr], 16)
            assert rb.dmem.dat_i == data, "Data loading (1): Data mismatch! Addr = {0:#x}: {1} != {2:#x}".format(addr << 2,
                                                                                                                 hex(rb.dmem.dat_i),
                                                                                                                 data)
        # Test invalidate
        invalidate.next = True
        yield delay(10)
        invalidate.next = False
        for addr in range(rb.depth >> 5):  # Address in words
            yield rb.read(addr << 2)  # Address in bytes
            data = int(lines[addr], 16)
            assert rb.dmem.dat_i == data, "Data loading (2): Data mismatch! Addr = {0:#x}: {1} != {2:#x}".format(addr << 2,
                                                                                                                 hex(rb.dmem.dat_i),
                                                                                                                 data)
        # Write the cache: mem[addr] = addr
        for addr in range(rb.depth >> 4):
            yield rb.write(addr << 2, addr)

        for addr in range(rb.depth >> 4):
            yield rb.read(addr << 2)
            assert rb.dmem.dat_i == rb.mirror_mem[addr], "R/W: Data mismatch! Addr = {0:#x}".format(addr << 2)

        # Read uncached area
        for addr in range(rb.depth >> 4):
            yield rb.read((addr << 2) | 0x80000000)
            assert rb.dmem.dat_i == rb.mirror_mem[addr], "R/W: Data mismatch! Addr = {0:#x}".format(addr << 2)

        # TODO: Test write uncached area

        raise StopSimulation

    return instances()


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


def test_cache():
    """
    Cache: Test loading from memory
    """
    gen_test_file()
    sim = Simulation(traceSignals(_testbench))
    sim.run()


def test_cache_assertions():
    """
    Memory: Test assertions
    """
    clk = Signal(False)
    rst = Signal(False)
    invalidate = Signal(False)
    cpu = WishboneIntercon()
    mem = WishboneIntercon()

    # Test data width size
    with pytest.raises(AssertionError):
        DCache(clk,
               rst,
               cpu,
               mem,
               invalidate,
               D_WIDTH=64,
               BLOCK_WIDTH=5,
               SET_WIDTH=9,
               WAYS=2,
               LIMIT_WIDTH=32)

    # Test block width size
    with pytest.raises(AssertionError):
        DCache(clk,
               rst,
               cpu,
               mem,
               invalidate,
               D_WIDTH=32,
               BLOCK_WIDTH=-4,
               SET_WIDTH=9,
               WAYS=2,
               LIMIT_WIDTH=32)

    # Test ways size
    with pytest.raises(AssertionError):
        DCache(clk,
               rst,
               cpu,
               mem,
               invalidate,
               D_WIDTH=32,
               BLOCK_WIDTH=6,
               SET_WIDTH=9,
               WAYS=3,
               LIMIT_WIDTH=32)

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
