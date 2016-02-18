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
    PC_4       = 0
    PC_BRJMP   = 1
    PC_JALR    = 2
    PC_EXC     = 3
    _PC_4      = modbv(0)[SZ_PC_SEL:]
    _PC_BRJMP  = modbv(1)[SZ_PC_SEL:]
    _PC_JALR   = modbv(2)[SZ_PC_SEL:]
    _PC_EXC    = modbv(3)[SZ_PC_SEL:]
    # Branch type
    SZ_BR      = 4
    BR_X       = 0
    BR_N       = 0
    BR_NE      = 1
    BR_EQ      = 2
    BR_GE      = 3
    BR_GEU     = 4
    BR_LT      = 5
    BR_LTU     = 6
    BR_J       = 7
    BR_JR      = 8
    _BR_X      = modbv(0)[SZ_BR:]
    _BR_N      = modbv(0)[SZ_BR:]
    _BR_NE     = modbv(1)[SZ_BR:]
    _BR_EQ     = modbv(2)[SZ_BR:]
    _BR_GE     = modbv(3)[SZ_BR:]
    _BR_GEU    = modbv(4)[SZ_BR:]
    _BR_LT     = modbv(5)[SZ_BR:]
    _BR_LTU    = modbv(6)[SZ_BR:]
    _BR_J      = modbv(7)[SZ_BR:]
    _BR_JR     = modbv(8)[SZ_BR:]
    # RS1 Operand Select Signal
    SZ_OP1     = 2
    OP1_X      = 0
    OP1_RS1    = 0
    OP1_PC     = 1
    OP1_ZERO   = 2
    _OP1_X     = modbv(0)[SZ_OP1:]
    _OP1_RS1   = modbv(0)[SZ_OP1:]
    _OP1_PC    = modbv(1)[SZ_OP1:]
    _OP1_ZERO  = modbv(2)[SZ_OP1:]
    # RS2 Operand Select Signal
    SZ_OP2     = 2
    OP2_X      = 0
    OP2_RS2    = 0
    OP2_IMM    = 1
    OP2_FOUR   = 2
    OP2_ZERO   = 3
    _OP2_X     = modbv(0)[SZ_OP2:]
    _OP2_RS2   = modbv(0)[SZ_OP2:]
    _OP2_IMM   = modbv(1)[SZ_OP2:]
    _OP2_FOUR  = modbv(2)[SZ_OP2:]
    _OP2_ZERO  = modbv(3)[SZ_OP2:]
    # IMM
    SZ_IMM     = 3
    IMM_X      = 0
    IMM_S      = 0
    IMM_SB     = 1
    IMM_U      = 2
    IMM_UJ     = 3
    IMM_I      = 4
    IMM_Z      = 5
    _IMM_X     = modbv(0)[SZ_IMM:]
    _IMM_S     = modbv(0)[SZ_IMM:]
    _IMM_SB    = modbv(1)[SZ_IMM:]
    _IMM_U     = modbv(2)[SZ_IMM:]
    _IMM_UJ    = modbv(3)[SZ_IMM:]
    _IMM_I     = modbv(4)[SZ_IMM:]
    _IMM_Z     = modbv(5)[SZ_IMM:]
    # Forwarding
    SZ_FWD     = 2
    FWD_X      = 0
    FWD_N      = 0
    FWD_EX     = 1
    FWD_MEM    = 2
    FWD_WB     = 3
    _FWD_X     = modbv(0)[SZ_FWD:]
    _FWD_N     = modbv(0)[SZ_FWD:]
    _FWD_EX    = modbv(1)[SZ_FWD:]
    _FWD_MEM   = modbv(2)[SZ_FWD:]
    _FWD_WB    = modbv(3)[SZ_FWD:]
    # WB signals
    SZ_WB      = 2
    WB_X       = 0
    WB_ALU     = 0
    WB_MEM     = 1
    WB_CSR     = 2
    _WB_X      = modbv(0)[SZ_WB:]
    _WB_ALU    = modbv(0)[SZ_WB:]
    _WB_MEM    = modbv(1)[SZ_WB:]
    _WB_CSR    = modbv(2)[SZ_WB:]
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
