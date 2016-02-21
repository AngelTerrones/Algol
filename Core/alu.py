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


class ALUOp:
    """
    List of ALU opcodes.
    """
    OP_ADD   = 0
    OP_SLL   = 1
    OP_XOR   = 4
    OP_SRL   = 5
    OP_OR    = 6
    OP_AND   = 7
    OP_SEQ   = 8
    OP_SNE   = 9
    OP_SUB   = 10
    OP_SRA   = 11
    OP_SLT   = 12
    OP_SGE   = 13
    OP_SLTU  = 14
    OP_SGEU  = 15
    _OP_ADD  = modbv(0)[SZ_OP:]
    _OP_SLL  = modbv(1)[SZ_OP:]
    _OP_XOR  = modbv(4)[SZ_OP:]
    _OP_SRL  = modbv(5)[SZ_OP:]
    _OP_OR   = modbv(6)[SZ_OP:]
    _OP_AND  = modbv(7)[SZ_OP:]
    _OP_SEQ  = modbv(8)[SZ_OP:]
    _OP_SNE  = modbv(9)[SZ_OP:]
    _OP_SUB  = modbv(10)[SZ_OP:]
    _OP_SRA  = modbv(11)[SZ_OP:]
    _OP_SLT  = modbv(12)[SZ_OP:]
    _OP_SGE  = modbv(13)[SZ_OP:]
    _OP_SLTU = modbv(14)[SZ_OP:]
    _OP_SGEU = modbv(15)[SZ_OP:]
    SZ_OP      = 5


class ALUPortIO:
    """
    Defines the IO port.

    :ivar function: ALU opcode
    :ivar input1:   Data input
    :ivar input2:   Data input
    :ivar output:   Data output
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.function = Signal(modbv(0)[ALUOp.SZ_OP:])
        self.input1   = Signal(modbv(0)[32:])
        self.input2   = Signal(modbv(0)[32:])
        self.output   = Signal(modbv(0)[32:])


class ALU:
    """
    Defines an Arithmetic-Logic Unit (ALU)
    """
    def __init__(self,
                 IO: ALUPortIO):
        """
        Initializes the IO ports.

        :param IO: An IO bundle (Function, Input1, Input2, Output)
        """
        self.IO = IO

    def GetRTL(self):
        """
        Defines the module behavior
        """
        io = self.IO

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
            else:
                io.output.next = 0

        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
