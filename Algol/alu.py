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


class ALUFunction:
    SZ_OP   = 4
    OP_ADD  = modbv(0)[SZ_OP:]
    OP_SLL  = modbv(1)[SZ_OP:]
    OP_XOR  = modbv(4)[SZ_OP:]
    OP_SRL  = modbv(5)[SZ_OP:]
    OP_OR   = modbv(6)[SZ_OP:]
    OP_AND  = modbv(7)[SZ_OP:]
    OP_SEQ  = modbv(8)[SZ_OP:]
    OP_SNE  = modbv(9)[SZ_OP:]
    OP_SUB  = modbv(10)[SZ_OP:]
    OP_SRA  = modbv(11)[SZ_OP:]
    OP_SLT  = modbv(12)[SZ_OP:]
    OP_SGE  = modbv(13)[SZ_OP:]
    OP_SLTU = modbv(14)[SZ_OP:]
    OP_SGEU = modbv(15)[SZ_OP:]


class ALUPortIO:
    def __init__(self):
        self.function = Signal(modbv(0)[ALUFunction.SZ_OP:])
        self.input1 = Signal(modbv(0)[32:])
        self.input2 = Signal(modbv(0)[32:])
        self.output = Signal(modbv(0)[32:])


class ALU:
    def __init__(self,
                 IO: ALUPortIO):
        self.IO = IO

    def GetRTL(self):
        io = self.IO

        @always_comb
        def rtl():
            shamt = io.input2[5:0]
            if io.function == ALUFunction.OP_ADD:
                io.output.next = io.input1 + io.input2
            elif io.function == ALUFunction.OP_SLL:
                io.output.next = io.input1 << shamt
            elif io.function == ALUFunction.OP_XOR:
                io.output.next = io.input1 ^ io.input2
            elif io.function == ALUFunction.OP_SRL:
                io.output.next = io.input1 >> shamt
            elif io.function == ALUFunction.OP_OR:
                io.output.next = io.input1 | io.input2
            elif io.function == ALUFunction.OP_AND:
                io.output.next = io.input1 & io.input2
            elif io.function == ALUFunction.OP_SEQ:
                io.output.next = concat(0, io.input1 == io.input2)
            elif io.function == ALUFunction.OP_SNE:
                io.output.next = concat(0, io.input1 != io.input2)
            elif io.function == ALUFunction.OP_SUB:
                io.output.next = io.input1 - io.input2
            elif io.function == ALUFunction.OP_SRA:
                io.output.next = io.input1.signed() >> shamt
            elif io.function == ALUFunction.OP_SLT:
                io.output.next = concat(0, io.input1.signed() < io.input2.signed())
            elif io.function == ALUFunction.OP_SGE:
                io.output.next = concat(0, io.input1.signed() >= io.input2.signed())
            elif io.function == ALUFunction.OP_SLTU:
                io.output.next = concat(0, io.input1 < io.input2)
            elif io.function == ALUFunction.OP_SGEU:
                io.output.next = concat(0, io.input1 >= io.input2)
            else:
                io.output.next = 0

        return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
