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
    OP_XOR     = 2
    OP_SRL     = 3
    OP_OR      = 4
    OP_AND     = 5
    OP_SUB     = 6
    OP_SRA     = 7
    OP_SLT     = 8
    OP_SLTU    = 9
    OP_MUL     = 10
    OP_MULH    = 11
    OP_MULHSU  = 12
    OP_MULHU   = 13
    OP_DIV     = 14
    OP_DIVU    = 15
    OP_REM     = 16
    OP_REMU    = 17
    _OP_ADD    = modbv(OP_ADD)[SZ_OP:]
    _OP_SLL    = modbv(OP_SLL)[SZ_OP:]
    _OP_XOR    = modbv(OP_XOR)[SZ_OP:]
    _OP_SRL    = modbv(OP_SRL)[SZ_OP:]
    _OP_OR     = modbv(OP_OR)[SZ_OP:]
    _OP_AND    = modbv(OP_AND)[SZ_OP:]
    _OP_SUB    = modbv(OP_SUB)[SZ_OP:]
    _OP_SRA    = modbv(OP_SRA)[SZ_OP:]
    _OP_SLT    = modbv(OP_SLT)[SZ_OP:]
    _OP_SLTU   = modbv(OP_SLTU)[SZ_OP:]
    _OP_MUL    = modbv(OP_MUL)[SZ_OP:]
    _OP_MULH   = modbv(OP_MULH)[SZ_OP:]
    _OP_MULHSU = modbv(OP_MULHSU)[SZ_OP:]
    _OP_MULHU  = modbv(OP_MULHU)[SZ_OP:]
    _OP_DIV    = modbv(OP_DIV)[SZ_OP:]
    _OP_DIVU   = modbv(OP_DIVU)[SZ_OP:]
    _OP_REM    = modbv(OP_REM)[SZ_OP:]
    _OP_REMU   = modbv(OP_REMU)[SZ_OP:]


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
            multIO.cmd.next     = (modbv(MultiplierOP.OP_SS)[MultiplierOP.SZ_OP:] if mult_ss else
                                   (modbv(MultiplierOP.OP_SU)[MultiplierOP.SZ_OP:] if mult_su else
                                    (modbv(MultiplierOP.OP_UU)[MultiplierOP.SZ_OP:] if mult_uu else
                                     modbv(MultiplierOP.OP_IDLE)[MultiplierOP.SZ_OP:])))
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
            elif io.function == ALUOp.OP_SUB:
                io.output.next = io.input1 - io.input2
            elif io.function == ALUOp.OP_SRA:
                io.output.next = io.input1.signed() >> io.input2[5:0]
            elif io.function == ALUOp.OP_SLT:
                io.output.next = concat(modbv(0)[31:], io.input1.signed() < io.input2.signed())
            elif io.function == ALUOp.OP_SLTU:
                io.output.next = concat(modbv(0)[31:], io.input1 < io.input2)
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
