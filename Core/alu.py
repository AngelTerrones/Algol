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
from myhdl import concat
from myhdl import always_comb
from myhdl import modbv
from Core.multiplier import Multiplier
from Core.multiplier import MultiplierIO
from Core.multiplier import MultiplierOP
from Core.divider import Divider
from Core.divider import DividerIO


class ALUOp:
    """
    List of ALU opcodes.
    """
    SZ_OP      = 5
    OP_ADD     = 0
    OP_SLL     = 1
    OP_XOR     = 4
    OP_SRL     = 5
    OP_OR      = 6
    OP_AND     = 7
    OP_SEQ     = 8
    OP_SNE     = 9
    OP_SUB     = 10
    OP_SRA     = 11
    OP_SLT     = 12
    OP_SGE     = 13
    OP_SLTU    = 14
    OP_SGEU    = 15
    OP_MUL     = 16
    OP_MULH    = 17
    OP_MULHSU  = 18
    OP_MULHU   = 19
    OP_DIV     = 20
    OP_DIVU    = 21
    OP_REM     = 22
    OP_REMU    = 23
    _OP_ADD    = modbv(0)[SZ_OP:]
    _OP_SLL    = modbv(1)[SZ_OP:]
    _OP_XOR    = modbv(4)[SZ_OP:]
    _OP_SRL    = modbv(5)[SZ_OP:]
    _OP_OR     = modbv(6)[SZ_OP:]
    _OP_AND    = modbv(7)[SZ_OP:]
    _OP_SEQ    = modbv(8)[SZ_OP:]
    _OP_SNE    = modbv(9)[SZ_OP:]
    _OP_SUB    = modbv(10)[SZ_OP:]
    _OP_SRA    = modbv(11)[SZ_OP:]
    _OP_SLT    = modbv(12)[SZ_OP:]
    _OP_SGE    = modbv(13)[SZ_OP:]
    _OP_SLTU   = modbv(14)[SZ_OP:]
    _OP_SGEU   = modbv(15)[SZ_OP:]
    _OP_MUL    = modbv(16)[SZ_OP:]
    _OP_MULH   = modbv(17)[SZ_OP:]
    _OP_MULHSU = modbv(18)[SZ_OP:]
    _OP_MULHU  = modbv(19)[SZ_OP:]
    _OP_DIV    = modbv(20)[SZ_OP:]
    _OP_DIVU   = modbv(21)[SZ_OP:]
    _OP_REM    = modbv(22)[SZ_OP:]
    _OP_REMU   = modbv(23)[SZ_OP:]


class ALUPortIO:
    """
    Defines the IO port.

    :ivar input1:   Data input
    :ivar input2:   Data input
    :ivar function: ALU opcode
    :ivar stall:
    :ivar kill:
    :ivar output:   Data output
    :ivar req_stall:
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.input1    = Signal(modbv(0)[32:])
        self.input2    = Signal(modbv(0)[32:])
        self.function  = Signal(modbv(0)[ALUOp.SZ_OP:])
        self.stall     = Signal(False)
        self.kill      = Signal(False)
        self.output    = Signal(modbv(0)[32:])
        self.req_stall = Signal(False)


class ALU:
    """
    Defines an Arithmetic-Logic Unit (ALU)
    """
    def __init__(self,
                 clk: Signal,
                 rst: Signal,
                 io:  ALUPortIO):
        """
        Initializes the IO ports.

        :param clk: System clock
        :param rst: System reset
        :param IO:  An IO bundle (Function, Input1, Input2, Output)
        """
        self.clk = clk
        self.rst = rst
        self.io  = io

    def GetRTL(self):
        """
        Defines the module behavior
        """
        io        = self.io
        multIO    = MultiplierIO()
        divIO     = DividerIO()
        mult_l    = Signal(modbv(0)[32:])
        mult_h    = Signal(modbv(0)[32:])
        quotient  = Signal(modbv(0)[32:])
        remainder = Signal(modbv(0)[32:])
        mult_ss   = Signal(False)
        mult_su   = Signal(False)
        mult_uu   = Signal(False)

        @always_comb
        def _mult_ops():
            mult_ss.next = io.function == ALUOp.OP_MUL or io.function == ALUOp.OP_MULH
            mult_su.next = io.function == ALUOp.OP_MULHSU
            mult_uu.next = io.function == ALUOp.OP_MULHU

        @always_comb
        def _assignments():
            multIO.input1.next  = self.io.input1
            multIO.input2.next  = self.io.input2
            multIO.cmd.next     = (MultiplierOP.OP_SS if mult_ss else
                                   (MultiplierOP.OP_SU if mult_su else
                                    (MultiplierOP.OP_UU if mult_uu else
                                     MultiplierOP.OP_IDLE)))
            multIO.enable.next  = (mult_ss or mult_su or mult_uu) and not multIO.active
            multIO.stall.next   = self.io.stall != io.req_stall
            multIO.kill.next    = self.io.kill
            mult_l.next         = multIO.output[32:0]
            mult_h.next         = multIO.output[64:32]

            divIO.dividend.next = self.io.input1
            divIO.divisor.next  = self.io.input2
            divIO.divs.next     = (io.function == ALUOp.OP_DIV or io.function == ALUOp.OP_REM) and not divIO.active
            divIO.divu.next     = (io.function == ALUOp.OP_DIVU or io.function == ALUOp.OP_REMU) and not divIO.active
            quotient.next       = divIO.quotient
            remainder.next      = divIO.remainder

        @always_comb
        def _assignments2():
            io.req_stall.next   = (divIO.divs or divIO.divu or (divIO.active != divIO.ready)) or (multIO.enable or (multIO.active != multIO.ready))

        @always_comb
        def rtl():
            if io.function == ALUOp.OP_ADD:
                io.output.next = io.input1 + io.input2
            elif io.function == ALUOp.OP_SLL:
                io.output.next = io.input1 << io.input2[5:0]
            elif io.function == ALUOp.OP_XOR:
                io.output.next = io.input1 ^ io.input2
            elif io.function == ALUOp.OP_SRL:
                io.output.next = io.input1 >> io.input2[5:0]
            elif io.function == ALUOp.OP_OR:
                io.output.next = io.input1 | io.input2
            elif io.function == ALUOp.OP_AND:
                io.output.next = io.input1 & io.input2
            elif io.function == ALUOp.OP_SEQ:
                io.output.next = concat(modbv(0)[31:], io.input1 == io.input2)
            elif io.function == ALUOp.OP_SNE:
                io.output.next = concat(modbv(0)[31:], io.input1 != io.input2)
            elif io.function == ALUOp.OP_SUB:
                io.output.next = io.input1 - io.input2
            elif io.function == ALUOp.OP_SRA:
                io.output.next = io.input1.signed() >> io.input2[5:0]
            elif io.function == ALUOp.OP_SLT:
                io.output.next = concat(modbv(0)[31:], io.input1.signed() < io.input2.signed())
            elif io.function == ALUOp.OP_SGE:
                io.output.next = concat(modbv(0)[31:], io.input1.signed() >= io.input2.signed())
            elif io.function == ALUOp.OP_SLTU:
                io.output.next = concat(modbv(0)[31:], io.input1 < io.input2)
            elif io.function == ALUOp.OP_SGEU:
                io.output.next = concat(modbv(0)[31:], io.input1 >= io.input2)
            elif io.function == ALUOp.OP_MUL:
                io.output.next = mult_l
            elif io.function == ALUOp.OP_MULH:
                io.output.next = mult_h
            elif io.function == ALUOp.OP_MULHSU:
                io.output.next = mult_h
            elif io.function == ALUOp.OP_MULHU:
                io.output.next = mult_h
            elif io.function == ALUOp.OP_DIV:
                io.output.next = quotient
            elif io.function == ALUOp.OP_DIVU:
                io.output.next = quotient
            elif io.function == ALUOp.OP_REM:
                io.output.next = remainder
            elif io.function == ALUOp.OP_REMU:
                io.output.next = remainder
            else:
                io.output.next = 0

        mult = Multiplier(self.clk,
                          self.rst,
                          multIO).GetRTL()

        div = Divider(self.clk,
                      self.rst,
                      divIO).GetRTL()

        return rtl, mult, div, _assignments, _mult_ops, _assignments2

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
