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
    X          = False
    Y          = True
    N          = False
    # PC Select Signal
    SZ_PC_SEL  = 2
    PC_4       = modbv(0)[SZ_PC_SEL:]
    PC_BRJMP   = modbv(1)[SZ_PC_SEL:]
    PC_JALR    = modbv(2)[SZ_PC_SEL:]
    PC_EXC     = modbv(3)[SZ_PC_SEL:]
    # Branch type
    SZ_BR      = 4
    BR_X       = 0
    BR_N       = modbv(0)[SZ_BR:]
    BR_NE      = modbv(1)[SZ_BR:]
    BR_EQ      = modbv(2)[SZ_BR:]
    BR_GE      = modbv(3)[SZ_BR:]
    BR_GEU     = modbv(4)[SZ_BR:]
    BR_LT      = modbv(5)[SZ_BR:]
    BR_LTU     = modbv(6)[SZ_BR:]
    BR_J       = modbv(7)[SZ_BR:]
    # RS1 Operand Select Signal
    SZ_OP1     = 2
    OP1_X      = modbv(0)[SZ_OP1:]
    OP1_ZERO   = modbv(0)[SZ_OP1:]
    OP1_RS1    = modbv(1)[SZ_OP1:]
    OP1_PC     = modbv(2)[SZ_OP1:]
    # RS2 Operand Select Signal
    SZ_OP2     = 3
    OP2_X      = modbv(0)[SZ_OP2:]
    OP2_ZERO   = modbv(0)[SZ_OP2:]
    OP2_RS2    = modbv(1)[SZ_OP2:]
    OP2_IMM    = modbv(2)[SZ_OP2:]
    OP2_FOUR   = modbv(3)[SZ_OP2:]
    # IMM
    SZ_IMM     = 3
    IMM_X      = 0
    IMM_S      = 0
    IMM_SB     = 1
    IMM_U      = 2
    IMM_UJ     = 3
    IMM_I      = 4
    IMM_Z      = 5
    # Forwarding
    SZ_FWD     = 1
    FWD_X      = False
    FWD_N      = False
    FWD_Y      = True
    # WB signals
    SZ_WB      = 2
    WB_X       = 0
    WB_ALU     = 0
    WB_MEM     = 1
    WB_CSR     = 2
    # PRIV
    MTVEC      = 0x100
    START_ADDR = MTVEC + 0x100
    # NOP
    BUBBLE     = 0x4033  # XOR r0, r0, r0
    NOP        = 0x13    # ADDI r0, r0, 0

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
