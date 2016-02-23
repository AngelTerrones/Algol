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
from myhdl import modbv
from myhdl import always
from myhdl import always_comb
from myhdl import instances
from myhdl import concat


class DividerIO:
    """
    Defines the IO port for the divider unit

    :ivar dividend:  Data input
    :ivar divisor:   Data input
    :ivar divs:      Signed operation
    :ivar divu:      Unsigned operation
    :ivar active:    The unit is busy performing an operation
    :ivar ready:     The output data is valid
    :ivar quotient:  Data output
    :ivar remainder: Data output
    """
    def __init__(self):
        self.dividend  = Signal(modbv(0)[32:])
        self.divisor   = Signal(modbv(0)[32:])
        self.divs      = Signal(False)
        self.divu      = Signal(False)
        self.active    = Signal(False)
        self.ready     = Signal(False)
        self.quotient  = Signal(modbv(0)[32:])
        self.remainder = Signal(modbv(0)[32:])


class Divider:
    """
    A 32-bit divider.
    """
    def __init__(self,
                 clk: Signal,
                 rst: Signal,
                 io:  DividerIO):
        """
        Initializes the IO ports

        :param clk: System clock
        :param rst: System reset
        :pram io:   An IO bundle
        """
        self.clk = clk
        self.rst = rst
        self.io  = io

    def GetRTL(self):
        """
        Defines the module behavior.

        WARNING: the op_divs/op_divu signal must be asserted only one cycle.
        Keeping it asserted for more than one cycle will restart the operation.
        The operation can be aborted by asserting the reset signal.
        """
        active        = Signal(False)
        neg_result    = Signal(False)
        neg_remainder = Signal(False)
        cycle         = Signal(modbv(0)[5:])
        result        = Signal(modbv(0)[32:])
        denominator   = Signal(modbv(0)[32:])
        residual      = Signal(modbv(0)[32:])
        partial_sub   = Signal(modbv(0)[33:])

        @always_comb
        def output():
            self.io.quotient.next  = result if neg_result == 0 else -result
            self.io.remainder.next = residual if neg_remainder == 0 else -residual
            self.io.ready.next     = self.io.active and not active
            partial_sub.next       = concat(residual[31:0], result[31]) - denominator

        @always(self.clk.posedge)
        def _active():
            if self.rst:
                self.io.active.next = False
            else:
                if self.io.active:
                    self.io.active.next = False if not active else True
                else:
                    self.io.active.next = True if self.io.divs or self.io.divu else False

        @always(self.clk.posedge)
        def rtl():
            if self.rst:
                active.next        = 0
                cycle.next         = 0
                denominator.next   = 0
                neg_result.next    = 0
                neg_remainder.next = 0
                residual.next      = 0
                result.next        = 0
            else:
                if self.io.divs:
                    cycle.next         = 31
                    result.next        = self.io.dividend if (self.io.dividend[31] == 0) else -self.io.dividend
                    denominator.next   = self.io.divisor if (self.io.divisor[31] == 0) else -self.io.divisor
                    residual.next      = 0
                    neg_result.next    = self.io.dividend[31] ^ self.io.divisor[31]
                    neg_remainder.next = self.io.dividend[31]
                    active.next        = 1
                elif self.io.divu:
                    cycle.next         = 31
                    result.next        = self.io.dividend
                    denominator.next   = self.io.divisor
                    residual.next      = 0
                    neg_result.next    = 0
                    neg_remainder.next = 0
                    active.next        = 1
                elif active:
                    if partial_sub[32] == 0:
                        residual.next = partial_sub[32:0]
                        result.next   = concat(result[31:0], modbv(1)[1:])
                    else:
                        residual.next = concat(residual[31:0], result[31])
                        result.next   = concat(result[31:0], modbv(0)[1:])

                    if cycle == 0:
                        active.next = 0

                    cycle.next = cycle - modbv(1)[5:]

        return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
