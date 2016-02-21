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


class MultiplierOP:
    """
    Define the commands for the multiplier:
    - signed x signed
    - unsigned x unsigned
    - signed x unsigned
    """
    SZ_OP    = 3
    OP_IDLE  = 0b000
    OP_SS    = 0b001
    OP_UU    = 0b010
    OP_SU    = 0b100
    _OP_IDLE = modbv(OP_IDLE)[SZ_OP:]
    _OP_SS   = modbv(OP_SS)[SZ_OP:]
    _OP_UU   = modbv(OP_UU)[SZ_OP:]
    _OP_SU   = modbv(OP_SU)[SZ_OP:]


class MultiplierIO:
    """
    Defines the IO port.

    :ivar input1: Input data (port 1)
    :ivar input2: Input data (port 2)
    :ivar cmd:    Command: S*S, U*U, S*U
    :ivar enable: Enable operation
    :ivar stall:  Stop the pipeline, keep data
    :ivar kill:   Kill the pipeline, flush data
    :ivar output: 64-bit result
    :ivar active: The multiplier is performing an operation
    :ivar ready:  The output data is valid
    """
    def __init__(self):
        self.input1 = Signal(modbv(0)[32:])
        self.input2 = Signal(modbv(0)[32:])
        self.cmd    = Signal(modbv(0)[MultiplierOP.SZ_OP:])
        self.enable = Signal(False)
        self.stall  = Signal(False)
        self.kill   = Signal(False)
        self.output = Signal(modbv(0)[64:])
        self.active = Signal(False)
        self.ready  = Signal(False)


class Multiplier:
    """
    A pipelined 32-bit x 32-bit multiplier.
    """
    def __init__(self,
                 clk: Signal,
                 rst: Signal,
                 io:  MultiplierIO):
        """
        Initializes the IO ports.

        :param clk: System clock
        :param rst: System reset
        :param io:  An IO bundle
        """
        self.clk = clk
        self.rst = rst
        self.io  = io

    def GetRTL(self):
        """
        Define the module behavior.
        """
        A            = Signal(modbv(0)[33:])
        B            = Signal(modbv(0)[33:])
        result_ll_0  = Signal(modbv(0)[32:])
        result_lh_0  = Signal(modbv(0)[32:])
        result_hl_0  = Signal(modbv(0)[32:])
        result_hh_0  = Signal(modbv(0)[32:])
        result_ll_1  = Signal(modbv(0)[32:])
        result_hh_1  = Signal(modbv(0)[32:])
        result_mid_1 = Signal(modbv(0)[33:])
        result_mult  = Signal(modbv(0)[64:])
        active0      = Signal(modbv(0)[1:])
        active1      = Signal(modbv(0)[1:])
        active2      = Signal(modbv(0)[1:])
        active3      = Signal(modbv(0)[1:])
        sign_result0 = Signal(modbv(0)[1:])
        sign_result1 = Signal(modbv(0)[1:])
        sign_result2 = Signal(modbv(0)[1:])
        sign_result3 = Signal(modbv(0)[1:])
        sign_a       = Signal(modbv(0)[1:])
        sign_b       = Signal(modbv(0)[1:])
        partial_sum  = Signal(modbv(0)[48:])
        a_sign_ext   = Signal(modbv(0)[33:])
        b_sign_ext   = Signal(modbv(0)[33:])

        @always_comb
        def assignments_0():
            sign_a.next         = self.io.input1[31] if (self.io.cmd[0] or self.io.cmd[2]) else modbv(0)[1:]
            sign_b.next         = self.io.input2[31] if self.io.cmd[0] else modbv(0)[1:]
            partial_sum.next    = concat(modbv(0)[15:], result_mid_1) + concat(result_hh_1[32:], result_ll_1[32:16])
            self.io.output.next = -result_mult if sign_result3 else result_mult
            self.io.ready.next  = active3
            self.io.active.next = active0 | active1 | active2 | active3

        @always_comb
        def assignments_1():
            a_sign_ext.next = concat(sign_a, self.io.input1)
            b_sign_ext.next = concat(sign_b, self.io.input2)

        @always(self.clk.posedge)
        def pipeline():
            if self.rst or self.io.kill:
                A.next            = modbv(0)[33:]
                B.next            = modbv(0)[33:]
                active0.next      = modbv(0)[1:]
                active1.next      = modbv(0)[1:]
                active2.next      = modbv(0)[1:]
                active3.next      = modbv(0)[1:]
                result_hh_0.next  = modbv(0)[31:]
                result_hh_1.next  = modbv(0)[31:]
                result_hl_0.next  = modbv(0)[31:]
                result_lh_0.next  = modbv(0)[31:]
                result_ll_0.next  = modbv(0)[31:]
                result_ll_1.next  = modbv(0)[31:]
                result_mid_1.next = modbv(0)[31:]
                result_mult.next  = modbv(0)[64:]
                sign_result0.next = modbv(0)[1:]
                sign_result1.next = modbv(0)[1:]
                sign_result2.next = modbv(0)[1:]
                sign_result3.next = modbv(0)[1:]
            elif not self.io.stall:
                # fist stage
                A.next            = -a_sign_ext if sign_a else a_sign_ext
                B.next            = -b_sign_ext if sign_b else b_sign_ext
                sign_result0.next = sign_a ^ sign_b
                active0.next      = self.io.enable
                # second stage
                result_ll_0.next  = A[16:0] * B[16:0]
                result_lh_0.next  = A[16:0] * B[33:16]
                result_hl_0.next  = A[33:16] * B[16:0]
                result_hh_0.next  = A[32:16] * B[32:16]
                sign_result1.next = sign_result0
                active1.next      = active0
                # third stage
                result_ll_1.next  = result_ll_0
                result_hh_1.next  = result_hh_0
                result_mid_1.next = result_lh_0 + result_hl_0
                sign_result2.next = sign_result1
                active2.next      = active1
                # fourth stage
                result_mult.next  = concat(partial_sum, result_ll_1[16:0])
                sign_result3.next = sign_result2
                active3.next      = active2

        return instances()
# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
