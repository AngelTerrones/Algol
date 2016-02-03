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
from Core.memIO import MemoryOpConstant
from Core.memIO import MemPortIO
import random
from myhdl import always
from myhdl import instance
from myhdl import Signal
from myhdl import delay
from myhdl import Simulation
from myhdl import StopSimulation
import pytest


MEM_SIZE      = 2**15  # Bytes
MEM_TEST_FILE = 'Simulation/modules/mem.hex'


class RamBus:
    def __init__(self, memory_size):
        ns = memory_size  # in words
        self.depth = ns
        self.clk = Signal(False)
        self.rst = Signal(False)
        self.imem = MemPortIO()
        self.dmem = MemPortIO()

        self.mirror_mem = [None for _ in range(ns)]

    def gen_clocks(self):
        @always(delay(3))
        def rambusclk():
            self.clk.next = not self.clk

        return rambusclk

    def write(self, addr, data):
        yield self.clk.posedge
        self.dmem.req.addr.next = addr
        self.dmem.req.data.next = data
        self.dmem.req.wr.next = 0b1111
        self.dmem.req.fcn.next = MemoryOpConstant.M_WR
        self.dmem.req.valid.next = True
        self.mirror_mem[addr >> 2] = data
        yield self.dmem.resp.valid.posedge
        yield self.clk.negedge
        self.dmem.req.valid.next = False

    def read(self, addr):
        yield self.clk.posedge
        self.dmem.req.addr.next = addr
        self.dmem.req.wr.next = 0b0000
        self.dmem.req.fcn.next = MemoryOpConstant.M_RD
        self.dmem.req.valid.next = True
        yield self.dmem.resp.valid.posedge
        yield self.clk.negedge
        self.dmem.req.valid.next = False


def _testbench():
    rb = RamBus(memory_size=MEM_SIZE >> 2)
    dut = Memory(clk=rb.clk,
                 rst=rb.rst,
                 imem=rb.imem,
                 dmem=rb.dmem,
                 SIZE=MEM_SIZE,
                 HEX=MEM_TEST_FILE).GetRTL()

    tb_clk = rb.gen_clocks()

    with open(MEM_TEST_FILE) as f:
        lines = [line.strip() for line in f]

    @instance
    def stimulus():
        # Testing the file loading
        for addr in range(rb.depth):  # Address in words
            yield rb.read(addr << 2)  # Address in bytes
            data = int(lines[addr], 16)
            assert rb.dmem.resp.data == data, "Data loading: Data mismatch! Addr = {0:#x}".format(addr << 2)

        # Testing R/W
        for addr in range(rb.depth):
            data = random.randint(0, 2**32)
            yield rb.write(addr << 2, data)

        for addr in range(rb.depth):  # Address in words
            yield rb.read(addr << 2)  # Address in bytes
            assert rb.dmem.resp.data == rb.mirror_mem[addr], "R/W: Data mismatch! Addr = {0:#x}".format(addr << 2)

        raise StopSimulation

    return dut, tb_clk, stimulus


def gen_test_file():
    """
    Generate a HEX file, with random values.
    """
    with open(MEM_TEST_FILE, 'w') as f:
        for _ in range(MEM_SIZE >> 2):
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
    imem = MemPortIO()
    dmem = MemPortIO()

    # Test minimun size
    with pytest.raises(AssertionError):
        Memory(clk=clk,
               rst=rst,
               imem=imem,
               dmem=dmem,
               SIZE=20,
               HEX=MEM_TEST_FILE).GetRTL()

    # test valid filename
    with pytest.raises(AssertionError):
        Memory(clk=clk,
               rst=rst,
               imem=imem,
               dmem=dmem,
               SIZE=MEM_SIZE,
               HEX='ERROR').GetRTL()
1
# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
