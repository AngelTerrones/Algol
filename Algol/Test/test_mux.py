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

from Algol.common.mux import Mux
from math import ceil
from math import log2
import random
from myhdl import instance
from myhdl import Signal
from myhdl import modbv
from myhdl import delay
from myhdl import Simulation
from myhdl import StopSimulation
import pytest


def _testbench():
    width = 8
    n_inputs = 4
    sel_width = ceil(log2(n_inputs))
    sel = Signal(modbv(0)[sel_width:])
    inputs = [Signal(modbv(0)[width:]) for _ in range(2**sel_width)]
    out = Signal(modbv(0)[width:])

    # instantiate mux
    dut_mux = Mux(sel=sel,
                  inputs=inputs,
                  out=out)
    dut = dut_mux.GetRTL()

    @instance
    def stimulus():
        values = [random.randint(0, 2**width) for _ in range(n_inputs)]
        for i in range(n_inputs):
            inputs[i].next = values[i]

        yield delay(5)

        for i in range(n_inputs):
            sel.next = i
            yield delay(5)
            assert out == values[i]

        raise StopSimulation

    return dut, stimulus


def test_mux():
    """
    Test behavioral
    """
    sim = Simulation(_testbench())
    sim.run()


def test_valid_settings():
    """
    Test if the module checks for valid settings.
    """
    width = 8
    n_inputs = 1
    sel_width = ceil(log2(n_inputs))
    sel = Signal(modbv(0)[sel_width:])
    inputs = [Signal(modbv(0)[width:]) for _ in range(2**sel_width)]
    out = Signal(modbv(0)[width:])

    # Test invalid width
    with pytest.raises(AssertionError):
        Mux(sel=sel,
            inputs=inputs,
            out=out)
1
# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
