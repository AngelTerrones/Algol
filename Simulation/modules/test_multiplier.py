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

from Core.multiplier import Multiplier
from Core.multiplier import MultiplierOP
from Core.multiplier import MultiplierIO
import random
from myhdl import modbv
from myhdl import Signal
from myhdl import instance
from myhdl import always
from myhdl import delay
from myhdl import Simulation
from myhdl import StopSimulation
from myhdl import Error

N_TEST = 1000


def _testbench(cmd):
    """
    Testbech for the Multiplier module
    """
    clk = Signal(False)
    rst = Signal(True)
    multIO = MultiplierIO()
    dut = Multiplier(clk=clk,
                     rst=rst,
                     io=multIO).GetRTL()

    halfperiod = delay(5)

    @always(halfperiod)
    def clk_drive():
        clk.next = not clk

    @instance
    def stimulus():
        yield delay(5)
        rst.next = 0

        for i in range(N_TEST):
            yield clk.negedge
            multIO.input1.next = Signal(modbv(random.randint(0, 2**32)))
            multIO.input2.next = Signal(modbv(random.randint(0, 2**32)))
            multIO.cmd.next = cmd
            multIO.enable.next = True
            yield clk.negedge
            multIO.enable.next = False
            yield multIO.ready.posedge
            yield halfperiod

            # verify
            if cmd == MultiplierOP.OP_SS:
                ref = multIO.input1.signed() * multIO.input2.signed()
                assert ref == multIO.output.signed(), "Error (S * S): {0} * {1} = {2} | DUT: {3}".format(multIO.input1.signed(),
                                                                                                         multIO.input2.signed(),
                                                                                                         ref,
                                                                                                         multIO.output.signed())
            elif cmd == MultiplierOP.OP_UU:
                ref = multIO.input1 * multIO.input2
                assert ref == multIO.output, "Error (U * U): {0} * {1} = {2} | DUT: {3}".format(multIO.input1,
                                                                                                multIO.input2,
                                                                                                ref,
                                                                                                multIO.output)
            elif cmd == MultiplierOP.OP_SU:
                ref = multIO.input1.signed() * multIO.input2
                assert ref == multIO.output.signed(), "Error (S * U): {0} * {1} = {2} | DUT: {3}".format(multIO.input1.signed(),
                                                                                                         multIO.input2,
                                                                                                         ref,
                                                                                                         multIO.output.signed())
            else:
                raise Error("Command unknown.")

        raise StopSimulation

    return dut, clk_drive, stimulus


def test_multiplier_ss():
    """
    Multiplier: Test signed * signed operations
    """
    sim = Simulation(_testbench(MultiplierOP.OP_SS))
    sim.run()


def test_multiplier_uu():
    """
    Multiplier: Test unsigned * unsigned operations
    """
    sim = Simulation(_testbench(MultiplierOP.OP_UU))
    sim.run()


def test_multiplier_su():
    """
    Multiplier: Test signed * unsigned operations
    """
    sim = Simulation(_testbench(MultiplierOP.OP_SU))
    sim.run()

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
