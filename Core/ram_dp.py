#!/usr/bin/env python
# Copyright (c) 2016 Angel Terrones (<angelterrones@gmail.com>)
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

from myhdl import Signal
from myhdl import always
from myhdl import modbv


class RAMIOPort:
    """
    Defines the RAM's IO port.

    :ivar clk:    Port's clock
    :ivar addr:   Address
    :ivar data_i: Data input
    :ivar data_o: Data output
    :ivar we:     Write enable
    """
    def __init__(self,
                 A_WIDTH=10,
                 D_WIDTH=8):
        """
        Initializes the IO ports.
        """
        self.clk    = Signal(False)
        self.addr   = Signal(modbv(0)[A_WIDTH:])
        self.data_i = Signal(modbv(0)[D_WIDTH:])
        self.data_o = Signal(modbv(0)[D_WIDTH:])
        self.we     = Signal(False)


def RAM_DP(portA,
           portB,
           A_WIDTH=10,
           D_WIDTH=8):
    """
    A dual-port RAM module.

    :param portA:  IO bundle (port A)
    :param portB:  IO bundle (port B)
    :param A_WITH: Address width
    :param D_WITH: Data width
    """
    assert len(portA.addr) == len(portB.addr) == A_WIDTH, "Error: Address width mismatch."
    assert len(portA.data_i) == len(portB.data_o) == D_WIDTH, "Error: Data width mismatch."

    _ram = [Signal(modbv(0)[D_WIDTH:]) for ii in range(0, 2**A_WIDTH)]

    @always(portA.clk.posedge)
    def rtl_port_a():
        if portA.we:
            _ram[portA.addr].next = portA.data_i
        portA.data_o.next = _ram[portA.addr]

    @always(portB.clk.posedge)
    def rtl_port_b():
        if portB.we:
            _ram[portB.addr].next = portB.data_i
        portB.data_o.next = _ram[portB.addr]

    return rtl_port_a, rtl_port_b

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
