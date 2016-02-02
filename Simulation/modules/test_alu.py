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

from Core.alu import ALU
from Core.alu import ALUFunction
from Core.alu import ALUPortIO
import random
from myhdl import modbv
from myhdl import instance
from myhdl import delay
from myhdl import Simulation
from myhdl import StopSimulation


def _testbench():
    """
    Testbech for the ALU module
    """
    aluIO = ALUPortIO()
    alu = ALU(aluIO)
    dut = alu.GetRTL()

    @instance
    def stimulus():
        yield delay(5)

        # Execute 1000 tests.
        for j in range(1000):
            aluIO.input1.next = random.randrange(0, 2**32)
            aluIO.input2.next = random.randrange(0, 2**32)
            a = aluIO.input1
            b = aluIO.input2

            # Test each function
            for i in range(16):
                aluIO.function.next = i
                yield delay(1)
                shamt = aluIO.input2[5:0]

                if i == ALUFunction.OP_ADD:
                    assert aluIO.output == modbv(a + b)[32:], "Error ADD"
                elif i == ALUFunction.OP_SLL:
                    assert aluIO.output == modbv(a << shamt)[32:], "Error SLL"
                elif i == ALUFunction.OP_XOR:
                    assert aluIO.output == a ^ b, "Error XOR"
                elif i == ALUFunction.OP_SRL:
                    assert aluIO.output == a >> shamt, "Error SRL"
                elif i == ALUFunction.OP_OR:
                    assert aluIO.output == a | b, "Error OR"
                elif i == ALUFunction.OP_AND:
                    assert aluIO.output == a & b, "Error AND"
                elif i == ALUFunction.OP_SEQ:
                    assert aluIO.output == modbv(a == b)[32:], "Error SEQ"
                elif i == ALUFunction.OP_SNE:
                    assert aluIO.output == modbv(a != b)[32:], "Error SNE"
                elif i == ALUFunction.OP_SUB:
                    assert aluIO.output == modbv(a - b)[32:], "Error SUB"
                elif i == ALUFunction.OP_SRA:
                    assert aluIO.output == modbv(a.signed() >> shamt)[32:], "Error SRA"
                elif i == ALUFunction.OP_SLT:
                    assert aluIO.output == modbv(a.signed() < b.signed())[32:], "Error SLT"
                elif i == ALUFunction.OP_SGE:
                    assert aluIO.output == modbv(a.signed() >= b.signed())[32:], "Error SGE"
                elif i == ALUFunction.OP_SLTU:
                    assert aluIO.output == modbv(abs(a) < b)[32:], "Error SLTU"
                elif i == ALUFunction.OP_SGEU:
                    assert aluIO.output == modbv(abs(a) >= b)[32:], "Error SGEU"
                else:
                    assert aluIO.output == 0, "Error UNDEFINED OP"

        raise StopSimulation

    return dut, stimulus


def test_alu():
    """
    ALU: Test behavioral.
    """
    sim = Simulation(_testbench())
    sim.run()

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
