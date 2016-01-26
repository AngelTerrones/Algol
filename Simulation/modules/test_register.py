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

from Algol.common.register import Register
from random import randint
from myhdl import Signal
from myhdl import modbv
from myhdl import always
from myhdl import instance
from myhdl import delay
from myhdl import Simulation
from myhdl import StopSimulation


def _testbench():
    clk = Signal(False)
    rst = Signal(False)
    we = Signal(False)
    inp = Signal(modbv(0)[8:])
    out = Signal(modbv(4)[8:])

    reg = Register(clk=clk,
                   rst=rst,
                   we=we,
                   i=inp,
                   o=out)

    @always(delay(5))
    def clock():
        clk.next = not clk

    @instance
    def stimulus():
        rst.next = True
        we.next = True
        yield delay(10)
        rst.next = False
        for i in range(10):
            yield clk.negedge
            inp.next = randint(0, 2**8)
            yield clk.posedge
            yield delay(1)
            assert inp == out

        raise StopSimulation

    return reg.GetRTL(), clock, stimulus


def test_register():
    """
    Register: Test behavioral.
    """
    sim = Simulation(_testbench())
    sim.run()

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
