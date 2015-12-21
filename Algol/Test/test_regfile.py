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

from Algol.regfile import RegisterFile
import random
from myhdl import instance
from myhdl import delay
from myhdl import Simulation
from myhdl import StopSimulation


def _testbench():
    '''
    Write 32 random values, and read those values.
    Compare the data from portA and portB with the values
    stored in a temporal list. Print error in case of mismatch.
    '''
    regFile = RegisterFile()
    clk, portA, portB, writePort = regFile.GetSignals()
    dut = regFile.GetRTL()

    values = [random.randrange(0, 2**32) for _ in range(32)]  # random values. Used as reference.

    @instance
    def stimulus():
        # write random data
        for i in range(32):
            writePort.wa.next = i
            writePort.wd.next = values[i]
            writePort.we.next = 1
            clk.next = 1
            yield delay(5)
            writePort.we.next = 1
            clk.next = 0
            yield delay(5)

        # read data, port A
        for i in range(32):
            portA.ra.next = i
            clk.next = 1
            yield delay(5)
            clk.next = 0
            # Check if the value is ok
            condition = (i == 0 and portA.rd == 0) or (i != 0 and portA.rd == values[i])
            assert condition, "ERROR at reg {0:02}: Value = {1}.\tRef = {1}".format(i, portA.rd, values[i])
            yield delay(5)

        # read data, port B
        for i in range(32):
            portB.ra.next = i
            clk.next = 1
            yield delay(5)
            clk.next = 0
            # Check if the value is ok
            condition = (i == 0 and portB.rd == 0) or (i != 0 and portB.rd == values[i])
            assert condition, "ERROR at reg {0:02}: Value = {1}.\tRef = {1}".format(i, portB.rd, values[i])
            yield delay(5)

        raise StopSimulation

    return dut, stimulus


def test_regfile():
    sim = Simulation(_testbench())
    sim.run()

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
