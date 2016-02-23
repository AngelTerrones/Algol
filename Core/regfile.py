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

from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import modbv


class RFReadPort:
    """
    Defines the RF's read IO port.

    :ivar ra: Read address
    :ivar rd: Read data
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.ra = Signal(modbv(0)[5:])
        self.rd = Signal(modbv(0)[32:])


class RFWritePort:
    """
    Defines the RF's write IO port.

    :ivar wa: Write address
    :ivar we: Write enable
    :ivar wd: Write data
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.wa = Signal(modbv(0)[5:])
        self.we = Signal(False)
        self.wd = Signal(modbv(0)[32:])


def RegisterFile(clk,
                 portA,
                 portB,
                 writePort):
    """
    The Register File (RF) module.
    32 32-bit registers, with the register 0 hardwired to zero.

    :param clk:       System clock
    :param portA:     IO bundle (read port)
    :param portB:     IO bundle (read port)
    :param writePort: IO bundle (write port)
    """
    _registers = [Signal(modbv(0)[32:]) for ii in range(0, 32)]

    @always_comb
    def read():
        """
        Asynchronous read operation.
        """
        portA.rd.next = _registers[portA.ra] if portA.ra != 0 else 0
        portB.rd.next = _registers[portB.ra] if portB.ra != 0 else 0

    @always(clk.posedge)
    def write():
        """
        Synchronous write operation.

        If the write address is zero, do nothing.
        """
        if writePort.wa != 0 and writePort.we == 1:
            _registers[writePort.wa].next = writePort.wd

    return read, write

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
