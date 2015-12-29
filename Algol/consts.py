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

from myhdl import modbv


class Consts:
    # control signals
    Y          = True
    N          = False
    # PC Select Signal
    PC_4       = modbv(0)[2:]
    PC_BRJMP   = modbv(1)[2:]
    PC_JALR    = modbv(2)[2:]
    PC_EXC     = modbv(3)[2:]
    # Branch type
    BR_N       = modbv(0)[4:]
    BR_NE      = modbv(1)[4:]
    BR_EQ      = modbv(2)[4:]
    BR_GE      = modbv(3)[4:]
    BR_GEU     = modbv(4)[4:]
    BR_LT      = modbv(5)[4:]
    BR_LTU     = modbv(6)[4:]
    BR_J       = modbv(7)[4:]
    BR_JR      = modbv(8)[4:]
    # RS1 Operand Select Signal
    OP1_X      = modbv(0)[2:]
    OP1_RS1    = modbv(0)[2:]
    OP1_PC     = modbv(1)[2:]
    OP1_IMZ    = modbv(2)[2:]
    # RS2 Operand Select Signal
    OP2_X      = modbv(0)[3:]
    OP2_RS2    = modbv(1)[3:]
    OP2_ITYPE  = modbv(2)[3:]
    OP2_STYPE  = modbv(3)[3:]
    OP2_SBTYPE = modbv(4)[3:]
    OP2_UTYPE  = modbv(5)[3:]
    OP2_JUTYPE = modbv(6)[3:]
    # PRIV
    MTVEC      = 0x100
    START_ADDR = MTVEC + 0x100

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
