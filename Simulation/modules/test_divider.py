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

from Core.divider import Divider
from Core.divider import DividerIO
import random
from myhdl import modbv
from myhdl import Signal
from myhdl import instance
from myhdl import always
from myhdl import delay
from myhdl import Simulation
from myhdl import StopSimulation

N_TEST = 1000


def _testbench(signed_op=True):
    """
    Testbech for the Multiplier module
    """
    clk = Signal(False)
    rst = Signal(True)
    divIO = DividerIO()
    dut = Divider(clk=clk,
                  rst=rst,
                  io=divIO).GetRTL()

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
            divIO.dividend.next = Signal(modbv(random.randint(0, 2**32)))
            divIO.divisor.next = Signal(modbv(random.randint(0, 2**32)))
            divIO.divs.next = signed_op
            divIO.divu.next = not signed_op
            yield clk.negedge
            divIO.divs.next = False
            divIO.divu.next = False
            yield divIO.active.negedge
            yield halfperiod

            # verify
            if signed_op:
                q_ref = int(divIO.dividend.signed() / divIO.divisor.signed())
                r_ref = divIO.dividend.signed() - int(divIO.dividend.signed() / divIO.divisor.signed()) * divIO.divisor.signed()
                q_eq = divIO.quotient.signed() == q_ref
                r_eq = divIO.remainder.signed() == r_ref
                assert q_eq and r_eq, "Error (S / S): {0}/{1} = Q: {2}, R: {3} | DUT: Q = {4}, R = {5}".format(divIO.dividend.signed(),
                                                                                                               divIO.divisor.signed(),
                                                                                                               q_ref,
                                                                                                               r_ref,
                                                                                                               divIO.quotient.signed(),
                                                                                                               divIO.remainder.signed())
            else:
                q_ref = divIO.dividend // divIO.divisor
                r_ref = divIO.dividend % divIO.divisor
                q_eq = divIO.quotient == q_ref
                r_eq = divIO.remainder == r_ref
                assert q_eq and r_eq, "Error (U / U): {0}/{1} = Q: {2}, R: {3} | DUT: Q = {4}, R = {5}".format(divIO.dividend,
                                                                                                               divIO.divisor,
                                                                                                               q_ref,
                                                                                                               r_ref,
                                                                                                               divIO.quotient,
                                                                                                               divIO.remainder)
        raise StopSimulation

    return dut, clk_drive, stimulus


def test_divider_ss():
    """
    Divider: Test signed * signed operations
    """
    sim = Simulation(_testbench(True))
    sim.run()


def test_divider_uu():
    """
    Divider: Test unsigned * unsigned operations
    """
    sim = Simulation(_testbench(False))
    sim.run()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
