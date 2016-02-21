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
from myhdl import always
from myhdl import always_comb
from myhdl import modbv
from myhdl import instances
from myhdl import concat
from Core.consts import Consts
from Core.alu import ALUOp
from Core.memIO import MemPortIO
from Core.memIO import MemOp
from Core.csr import CSRCMD
from Core.csr import CSRExceptionCode
from Core.csr import CSRModes
from Core.instructions import Opcodes
from Core.instructions import BranchFunct3
from Core.instructions import LoadFunct3
from Core.instructions import StoreFunct3
from Core.instructions import ArithmeticFunct3
from Core.instructions import FenceFunct3
from Core.instructions import SystemFunct3
from Core.instructions import PrivFunct12
from Core.instructions import MulDivFunct

Y = True
N = False


class CtrlSignals:
    """
    Vectorizes the datapath control signal.

    ISA: RV32I + priviledge instructions v1.7
    """
    # Control signals
    #                  Illegal                                                 Valid memory operation                                         OP1 select
    #                  |  Fence.I                                              |  Memory Function (type)                                      |                 OP2 select
    #                  |  |  Fence                                             |  |           Memory type                                     |                 |                 Branch/Jump
    #                  |  |  |  ecall                                          |  |           |             ALU operation                     |                 |                 |
    #                  |  |  |  |  ebreak                                      |  |           |             |                 IMM type        |                 |                 |
    #                  |  |  |  |  |  eret                                     |  |           |             |                 |               |                 |                 |
    #                  |  |  |  |  |  |  RF WE              CSR command        |  |           |             |                 |               |                 |                 |
    #                  |  |  |  |  |  |  |  Sel dat to WB   |                  |  |           |             |                 |               |                 |                 |
    #                  |  |  |  |  |  |  |  |               |                  |  |           |             |                 |               |                 |                 |
    #                  |  |  |  |  |  |  |  |               |                  |  |           |             |                 |               |                 |                 |
    NOP       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    INVALID   = concat(Y, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    LUI       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_U,  Consts._OP1_ZERO, Consts._OP2_IMM,  Consts._BR_N).__int__()
    AUIPC     = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_U,  Consts._OP1_PC,   Consts._OP2_IMM,  Consts._BR_N).__int__()
    JAL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_UJ, Consts._OP1_PC,   Consts._OP2_FOUR, Consts._BR_J).__int__()
    JALR      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_PC,   Consts._OP2_FOUR, Consts._BR_JR).__int__()
    BEQ       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_EQ).__int__()
    BNE       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_NE).__int__()
    BLT       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_LT).__int__()
    BGE       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_GE).__int__()
    BLTU      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_LTU).__int__()
    BGEU      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_GEU).__int__()
    LB        = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, MemOp.M_RD, MemOp._MT_B,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LH        = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, MemOp.M_RD, MemOp._MT_H,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LW        = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, MemOp.M_RD, MemOp._MT_W,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LBU       = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, MemOp.M_RD, MemOp._MT_BU, ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LHU       = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, MemOp.M_RD, MemOp._MT_HU, ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SB        = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  Y, MemOp.M_WR, MemOp._MT_B,  ALUOp._OP_ADD,    Consts._IMM_S,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SH        = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  Y, MemOp.M_WR, MemOp._MT_H,  ALUOp._OP_ADD,    Consts._IMM_S,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SW        = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  Y, MemOp.M_WR, MemOp._MT_W,  ALUOp._OP_ADD,    Consts._IMM_S,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ADDI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SLTI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SLT,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SLTIU     = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SLTU,   Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    XORI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_XOR,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ORI       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_OR,     Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ANDI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_AND,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SLLI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SLL,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SRLI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SRL,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SRAI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SRA,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ADD       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SUB       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SUB,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SLL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SLL,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SLT       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SLT,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SLTU      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SLTU,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    XOR       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_XOR,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SRL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SRL,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SRA       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_SRA,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    OR        = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_OR,     Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    AND       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_AND,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    FENCE     = concat(N, N, Y, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    FENCE_I   = concat(N, Y, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    CSRRW     = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_WRITE, N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRS     = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_SET,   N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRC     = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_CLEAR, N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRWI    = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_WRITE, N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRSI    = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_SET,   N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRCI    = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_CLEAR, N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    ECALL     = concat(N, N, N, Y, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    EBREAK    = concat(N, N, N, N, Y, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    ERET      = concat(N, N, N, N, N, Y, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    MRTS      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    MRTH      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    HRTS      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    WFI       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    SFENCE_VM = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    MUL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_MUL,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    MULH      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_MULH,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    MULHSU    = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_MULHSU, Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    MULHU     = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_MULHU,  Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    DIV       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_DIV,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    DIVU      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_DIVU,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    REM       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_REM,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    REMU      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, MemOp.M_X,  MemOp._MT_X,  ALUOp._OP_REMU,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()


class CtrlIO:
    """
    Defines a bundle for the IO interface between the cpath and the dpath.

    : ivar id_instruction:     Intruction at ID stage
    : ivar if_kill:            Kill the IF stage
    : ivar id_stall:           Stall the ID stage
    : ivar id_kill:            Kill the ID stage
    : ivar full_stall:         Stall whole pipeline
    : ivar pipeline_kill:      Kill the pipeline
    : ivar pc_select:          Select next PC
    : ivar id_op1_select:      Data select for OP1 at ID stage
    : ivar id_op2_select:      Data select for OP2 at ID stage
    : ivar id_sel_imm:         Select the Immediate
    : ivar id_alu_funct:       ALU opcode
    : ivar id_mem_type:        Data size for memory operations: byte, half-word, word
    : ivar id_mem_funct:       Memory function: read (RD) or write (WR)
    : ivar id_mem_valid:       Valid memory operation
    : ivar id_csr_cmd:         CSR command
    : ivar id_mem_data_sel:    Data source for mux at MEM stage: ALU, memory or CSR
    : ivar id_wb_we:           Commit data to RF
    : ivar id_fwd1_select:     Forwarding selector for OP1
    : ivar id_fwd2_select:     Forwarding selector for OP2
    : ivar id_rs1_addr:        OP1 address
    : ivar id_rs2_addr:        OP2 address
    : ivar id_op1:             OP1 data
    : ivar id_op2:             OP2 data
    : ivar ex_wb_addr:         RF write address at EX stage
    : ivar ex_wb_we:           RF write enable at EX stage
    : ivar mem_wb_addr:        RF write address at MEM stage
    : ivar mem_wb_we:          RF write enable at MEM stage
    : ivar wb_wb_addr:         RF write address at WB stage
    : ivar wb_wb_we:           RF write enable at WB stage
    : ivar csr_eret:           Instruction is ERET
    : ivar csr_prv:            Priviledge level at MEM stage
    : ivar csr_illegal_access: Illegal access to CSR: CSR at MEM
    : ivar csr_interrupt:      External interrupt: CSR at ID
    : ivar csr_interrupt_code: Interrupt code: CSR at ID
    : ivar csr_exception:      Exception detected: CSR at MEM
    : ivar csr_exception_code: Exception code: CSR at MEM
    : ivar csr_retire:         Increment instruction count: CSR at MEM
    : ivar imem_pipeline:      Instruction memory access request from dpath
    : ivar dmem_pipeline:      Data memory access request from dpath
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.id_instruction     = Signal(modbv(0)[32:])
        self.if_kill            = Signal(False)
        self.id_stall           = Signal(False)
        self.id_kill            = Signal(False)
        self.full_stall         = Signal(False)
        self.pipeline_kill      = Signal(False)
        self.pc_select          = Signal(modbv(0)[Consts.SZ_PC_SEL:])
        self.id_op1_select      = Signal(modbv(0)[Consts.SZ_OP1:])
        self.id_op2_select      = Signal(modbv(0)[Consts.SZ_OP2:])
        self.id_sel_imm         = Signal(modbv(0)[Consts.SZ_IMM:])
        self.id_alu_funct       = Signal(modbv(0)[ALUOp.SZ_OP:])
        self.id_mem_type        = Signal(modbv(0)[MemOp.SZ_MT:])
        self.id_mem_funct       = Signal(modbv(0)[MemOp.SZ_M:])
        self.id_mem_valid       = Signal(False)
        self.id_csr_cmd         = Signal(modbv(0)[CSRCMD.SZ_CMD:])
        self.id_mem_data_sel    = Signal(modbv(0)[Consts.SZ_WB:])
        self.id_wb_we           = Signal(False)
        self.id_fwd1_select     = Signal(modbv(0)[Consts.SZ_FWD:])
        self.id_fwd2_select     = Signal(modbv(0)[Consts.SZ_FWD:])
        self.id_rs1_addr        = Signal(modbv(0)[5:])
        self.id_rs2_addr        = Signal(modbv(0)[5:])
        self.id_op1             = Signal(modbv(0)[32:])
        self.id_op2             = Signal(modbv(0)[32:])
        self.ex_wb_addr         = Signal(modbv(0)[5:])
        self.ex_wb_we           = Signal(False)
        #
        self.ex_req_stall       = Signal(False)
        #
        self.mem_wb_addr        = Signal(modbv(0)[5:])
        self.mem_wb_we          = Signal(False)
        self.wb_wb_addr         = Signal(modbv(0)[5:])
        self.wb_wb_we           = Signal(False)
        self.csr_eret           = Signal(False)
        self.csr_prv            = Signal(modbv(0)[CSRModes.SZ_MODE:])
        self.csr_illegal_access = Signal(False)
        self.csr_interrupt      = Signal(False)
        self.csr_interrupt_code = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
        self.csr_exception      = Signal(False)
        self.csr_exception_code = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
        self.csr_retire         = Signal(False)
        self.imem_pipeline      = MemDpathIO()
        self.dmem_pipeline      = MemDpathIO()


class MemDpathIO:
    """
    Defines the interface for memory accesses from dpath

    :ivar addr:  Memory address
    :ivar wdata: Write data
    :ivar typ:   Data ype: byte, half-word, word
    :ivar fcn:   Access type: read or write
    :ivar valid: The request is valid
    :ivar rdata: Read data
    """
    def __init__(self):
        self.addr  = Signal(modbv(0)[32:])
        self.wdata = Signal(modbv(0)[32:])
        self.typ   = Signal(modbv(0)[3:])
        self.fcn   = Signal(False)
        self.valid = Signal(False)
        self.rdata = Signal(modbv(0)[32:])


class Ctrlpath:
    """
    The decoder, exception, hazard detection, and control unit.
    """
    def __init__(self,
                 clk:  Signal,
                 rst:  Signal,
                 io:   CtrlIO,
                 imem: MemPortIO,
                 dmem: MemPortIO):
        """
        Initializes the IO interface and internal signals

        :param clk:  Main clock
        :param rst:  Main reset
        :param io:   Interface with dapath
        :param imem: Interface with instruction memory
        :param dmem: Interface with data memory
        """
        self.clk                   = clk
        self.rst                   = rst
        self.io                    = io
        self.imem                  = imem
        self.dmem                  = dmem

        self.id_br_type            = Signal(modbv(0)[Consts.SZ_BR:])
        self.id_eq                 = Signal(False)
        self.id_lt                 = Signal(False)
        self.id_ltu                = Signal(False)
        self.id_fence_i            = Signal(False)
        self.id_fence              = Signal(False)

        self.if_imem_misalign      = Signal(False)
        self.if_imem_fault         = Signal(False)
        self.id_breakpoint         = Signal(False)
        self.id_eret               = Signal(False)
        self.id_ebreak             = Signal(False)
        self.id_ecall              = Signal(False)
        self.id_illegal_inst       = Signal(False)
        self.mem_ld_misalign       = Signal(False)
        self.mem_ld_fault          = Signal(False)
        self.mem_st_misalign       = Signal(False)
        self.mem_st_fault          = Signal(False)

        self.id_imem_misalign      = Signal(False)
        self.id_imem_fault         = Signal(False)
        self.ex_breakpoint         = Signal(False)
        self.ex_eret               = Signal(False)
        self.ex_ecall              = Signal(False)
        self.ex_exception          = Signal(False)
        self.ex_exception_code     = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
        self.ex_mem_funct          = Signal(modbv(0)[MemOp.SZ_M:])
        self.ex_mem_valid          = Signal(False)
        self.ex_csr_cmd            = Signal(modbv(0)[CSRCMD.SZ_CMD:])
        self.mem_breakpoint        = Signal(False)
        self.mem_eret              = Signal(False)
        self.mem_ecall             = Signal(False)
        self.mem_ecall_u           = Signal(False)
        self.mem_ecall_s           = Signal(False)
        self.mem_ecall_h           = Signal(False)
        self.mem_ecall_m           = Signal(False)
        self.mem_exception_ex      = Signal(False)
        self.mem_exception_code_ex = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
        self.mem_exception         = Signal(False)
        self.mem_exception_code    = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
        self.mem_mem_funct         = Signal(modbv(0)[MemOp.SZ_M:])
        self.wb_mem_funct          = Signal(modbv(0)[MemOp.SZ_M:])
        self.control               = Signal(modbv(0)[33:])

        self.if_misalign           = Signal(False)
        self.mem_misalign          = Signal(False)

        self.opcode                = Signal(modbv(0)[7:])
        self.funct3                = Signal(modbv(0)[3:])
        self.funct7                = Signal(modbv(0)[7:])

    def GetRTL(self):
        """
        Defines the module behavior.
        """
        @always_comb
        def _ctrl_assignment():
            """
            Get the opcode and funct3 fields from the instruction.
            """
            self.opcode.next = self.io.id_instruction[7:0]
            self.funct3.next = self.io.id_instruction[15:12]
            self.funct7.next = self.io.id_instruction[32:25]

        @always_comb
        def _ctrl_signal_assignment():
            """
            Instruction decoding.
            """
            if self.opcode == Opcodes.RV32_LUI:
                self.control.next = CtrlSignals.LUI
            elif self.opcode == Opcodes.RV32_AUIPC:
                self.control.next = CtrlSignals.AUIPC
            elif self.opcode == Opcodes.RV32_JAL:
                self.control.next = CtrlSignals.JAL
            elif self.opcode == Opcodes.RV32_JALR:
                self.control.next = CtrlSignals.JALR
            elif self.opcode == Opcodes.RV32_BRANCH:
                if self.funct3 == BranchFunct3.RV32_F3_BEQ:
                    self.control.next = CtrlSignals.BEQ
                elif self.funct3 == BranchFunct3.RV32_F3_BNE:
                    self.control.next = CtrlSignals.BNE
                elif self.funct3 == BranchFunct3.RV32_F3_BLT:
                    self.control.next = CtrlSignals.BLT
                elif self.funct3 == BranchFunct3.RV32_F3_BGE:
                    self.control.next = CtrlSignals.BGE
                elif self.funct3 == BranchFunct3.RV32_F3_BLTU:
                    self.control.next = CtrlSignals.BLTU
                elif self.funct3 == BranchFunct3.RV32_F3_BGEU:
                    self.control.next = CtrlSignals.BGEU
                else:
                    self.control.next = CtrlSignals.INVALID
            elif self.opcode == Opcodes.RV32_LOAD:
                if self.funct3 == LoadFunct3.RV32_F3_LB:
                    self.control.next = CtrlSignals.LB
                elif self.funct3 == LoadFunct3.RV32_F3_LH:
                    self.control.next = CtrlSignals.LH
                elif self.funct3 == LoadFunct3.RV32_F3_LW:
                    self.control.next = CtrlSignals.LW
                elif self.funct3 == LoadFunct3.RV32_F3_LBU:
                    self.control.next = CtrlSignals.LBU
                elif self.funct3 == LoadFunct3.RV32_F3_LHU:
                    self.control.next = CtrlSignals.LHU
                else:
                    self.control.next = CtrlSignals.INVALID
            elif self.opcode == Opcodes.RV32_STORE:
                if self.funct3 == StoreFunct3.RV32_F3_SB:
                    self.control.next = CtrlSignals.SB
                elif self.funct3 == StoreFunct3.RV32_F3_SH:
                    self.control.next = CtrlSignals.SH
                elif self.funct3 == StoreFunct3.RV32_F3_SW:
                    self.control.next = CtrlSignals.SW
                else:
                    self.control.next = CtrlSignals.INVALID
            elif self.opcode == Opcodes.RV32_IMM:
                if self.funct3 == ArithmeticFunct3.RV32_F3_ADD_SUB:
                    self.control.next = CtrlSignals.ADDI
                elif self.funct3 == ArithmeticFunct3.RV32_F3_SLT:
                    self.control.next = CtrlSignals.SLTI
                elif self.funct3 == ArithmeticFunct3.RV32_F3_SLTU:
                    self.control.next = CtrlSignals.SLTIU
                elif self.funct3 == ArithmeticFunct3.RV32_F3_XOR:
                    self.control.next = CtrlSignals.XORI
                elif self.funct3 == ArithmeticFunct3.RV32_F3_OR:
                    self.control.next = CtrlSignals.ORI
                elif self.funct3 == ArithmeticFunct3.RV32_F3_AND:
                    self.control.next = CtrlSignals.ANDI
                elif self.funct3 == ArithmeticFunct3.RV32_F3_SLL:
                    self.control.next = CtrlSignals.SLLI
                elif self.funct3 == ArithmeticFunct3.RV32_F3_SRL_SRA:
                    if self.io.id_instruction[30]:
                        self.control.next = CtrlSignals.SRAI
                    else:
                        self.control.next = CtrlSignals.SRLI
                else:
                    self.control.next = CtrlSignals.INVALID
            elif self.opcode == Opcodes.RV32_OP:
                if self.funct7 != MulDivFunct.RV32_F7_MUL_DIV:
                    if self.funct3 == ArithmeticFunct3.RV32_F3_ADD_SUB:
                        if self.io.id_instruction[30]:
                            self.control.next = CtrlSignals.SUB
                        else:
                            self.control.next = CtrlSignals.ADD
                    elif self.funct3 == ArithmeticFunct3.RV32_F3_SLT:
                        self.control.next = CtrlSignals.SLT
                    elif self.funct3 == ArithmeticFunct3.RV32_F3_SLTU:
                        self.control.next = CtrlSignals.SLTU
                    elif self.funct3 == ArithmeticFunct3.RV32_F3_XOR:
                        self.control.next = CtrlSignals.XOR
                    elif self.funct3 == ArithmeticFunct3.RV32_F3_OR:
                        self.control.next = CtrlSignals.OR
                    elif self.funct3 == ArithmeticFunct3.RV32_F3_AND:
                        self.control.next = CtrlSignals.AND
                    elif self.funct3 == ArithmeticFunct3.RV32_F3_SLL:
                        self.control.next = CtrlSignals.SLL
                    elif self.funct3 == ArithmeticFunct3.RV32_F3_SRL_SRA:
                        if self.io.id_instruction[30]:
                            self.control.next = CtrlSignals.SRA
                        else:
                            self.control.next = CtrlSignals.SRL
                    else:
                        self.control.next = CtrlSignals.INVALID
                elif self.funct7 == MulDivFunct.RV32_F7_MUL_DIV:
                    if self.funct3 == MulDivFunct.RV32_F3_MUL:
                        self.control.next = CtrlSignals.MUL
                    elif self.funct3 == MulDivFunct.RV32_F3_MULH:
                        self.control.next = CtrlSignals.MULH
                    elif self.funct3 == MulDivFunct.RV32_F3_MULHSU:
                        self.control.next = CtrlSignals.MULHSU
                    elif self.funct3 == MulDivFunct.RV32_F3_MULHU:
                        self.control.next = CtrlSignals.MULHU
                    elif self.funct3 == MulDivFunct.RV32_F3_DIV:
                        self.control.next = CtrlSignals.DIV
                    elif self.funct3 == MulDivFunct.RV32_F3_DIVU:
                        self.control.next = CtrlSignals.DIVU
                    elif self.funct3 == MulDivFunct.RV32_F3_REM:
                        self.control.next = CtrlSignals.REM
                    elif self.funct3 == MulDivFunct.RV32_F3_REMU:
                        self.control.next = CtrlSignals.REMU
                    else:
                        self.control.next = CtrlSignals.INVALID
                else:
                    self.control.next = CtrlSignals.INVALID
            elif self.opcode == Opcodes.RV32_FENCE:
                if self.funct3 == FenceFunct3.RV32_F3_FENCE:
                    self.control.next = CtrlSignals.FENCE
                elif self.funct3 == FenceFunct3.RV32_F3_FENCE_I:
                    self.control.next = CtrlSignals.FENCE_I
                else:
                    self.control.next = CtrlSignals.INVALID
            elif self.opcode == Opcodes.RV32_SYSTEM:
                if self.funct3 == SystemFunct3.RV32_F3_PRIV:
                    if self.io.id_instruction[32:20] == PrivFunct12.RV32_F12_ECALL:
                        self.control.next = CtrlSignals.ECALL
                    elif self.io.id_instruction[32:20] == PrivFunct12.RV32_F12_EBREAK:
                        self.control.next = CtrlSignals.EBREAK
                    elif self.io.id_instruction[32:20] == PrivFunct12.RV32_F12_ERET:
                        self.control.next = CtrlSignals.ERET
                    else:
                        self.control.next = CtrlSignals.INVALID
                elif self.funct3 == SystemFunct3.RV32_F3_CSRRW:
                    self.control.next = CtrlSignals.CSRRW
                elif self.funct3 == SystemFunct3.RV32_F3_CSRRS:
                    self.control.next = CtrlSignals.CSRRS
                elif self.funct3 == SystemFunct3.RV32_F3_CSRRC:
                    self.control.next = CtrlSignals.CSRRC
                elif self.funct3 == SystemFunct3.RV32_F3_CSRRWI:
                    self.control.next = CtrlSignals.CSRRWI
                elif self.funct3 == SystemFunct3.RV32_F3_CSRRSI:
                    self.control.next = CtrlSignals.CSRRSI
                elif self.funct3 == SystemFunct3.RV32_F3_CSRRCI:
                    self.control.next = CtrlSignals.CSRRCI
                else:
                    self.control.next = CtrlSignals.INVALID
            else:
                self.control.next = CtrlSignals.INVALID

        @always_comb
        def _assignments():
            """
            Individual assignment of control signals.

            Each signal correspond to slice in the vectored control signal (check CtrlSignals class).
            Except the 'id_csr_cmd' signal: This signal depends if the control is a CSR_IDLE command.
            If it is an CSR_IDLE command, we need to check 'id_rs1_addr': in case of being equal to zero, the
            command does not write to the CSR, becoming a CSR_READ command.
            """
            self.id_br_type.next         = self.control[4:0]
            self.io.id_op2_select.next   = self.control[6:4]
            self.io.id_op1_select.next   = self.control[8:6]
            self.io.id_sel_imm.next      = self.control[11:8]
            self.io.id_alu_funct.next    = self.control[16:11]
            self.io.id_mem_type.next     = self.control[19:16]
            self.io.id_mem_funct.next    = self.control[19]
            self.io.id_mem_valid.next    = self.control[20]
            self.io.id_csr_cmd.next      = self.control[24:21] if (self.control[24:21] == CSRCMD.CSR_IDLE or self.io.id_rs1_addr != 0) else modbv(CSRCMD.CSR_READ)[CSRCMD.SZ_CMD:]
            self.io.id_mem_data_sel.next = self.control[26:24]
            self.io.id_wb_we.next        = self.control[26]
            self.id_eret.next            = self.control[27]
            self.id_ebreak.next          = self.control[28]
            self.id_ecall.next           = self.control[29]
            self.id_fence.next           = self.control[30]
            self.id_fence_i.next         = self.control[31]

        @always_comb
        def _assignments2():
            """
            Assign to the 'retire', 'eret', 'id_illegal_inst' and 'id_breakpoint' signals.

            Retire: Increment the executed instruction counter at MEM if the pipeline is not stalled, and
            the instruction have not caused an exception.
            Eret: Check the eret flag at MEM, no pipeline stall and priviledge mode other that 'USER'.
            Illegal instruction: From instruction decode. Complement with illegal access to CSR at MEM stage.
            Breakpoint: Fom instruction decode.
            """
            self.io.csr_retire.next   = not self.io.full_stall and not self.io.csr_exception
            self.io.csr_eret.next     = self.mem_eret and self.io.csr_prv != CSRModes.PRV_U and not self.io.full_stall
            self.id_illegal_inst.next = self.control[32]
            self.id_breakpoint.next   = self.id_ebreak

        @always_comb
        def _assignments3():
            """
            Determines address misalignment.
            """
            self.if_misalign.next       = (self.io.imem_pipeline.addr[0] if (self.io.imem_pipeline.typ == MemOp.MT_H) or (self.io.imem_pipeline.typ == MemOp.MT_HU) else
                                           ((self.io.imem_pipeline.addr[0] or self.io.imem_pipeline.addr[1]) if self.io.imem_pipeline.typ == MemOp.MT_W else
                                           (False)))
            self.mem_misalign.next      = (self.io.dmem_pipeline.addr[0] if (self.io.dmem_pipeline.typ == MemOp.MT_H) or (self.io.dmem_pipeline.typ == MemOp.MT_HU) else
                                           ((self.io.dmem_pipeline.addr[0] or self.io.dmem_pipeline.addr[1]) if self.io.dmem_pipeline.typ == MemOp.MT_W else
                                            (False)))

        @always_comb
        def _assignments4():
            """
            Check for memory related exceptions.

            Exceptions:
            - E_INST_ADDR_MISALIGNED
            - E_INST_ACCESS_FAULT
            - E_LOAD_ADDR_MISALIGNED
            - E_LOAD_ACCESS_FAULT
            - E_AMO_ADDR_MISALIGNED
            - E_AMO_ACCESS_FAULT
            """
            self.if_imem_misalign.next  = self.if_misalign
            self.if_imem_fault.next     = self.imem.fault
            self.mem_ld_misalign.next   = (self.io.dmem_pipeline.valid and
                                           self.io.dmem_pipeline.fcn == MemOp.M_RD and
                                           self.mem_misalign)
            self.mem_ld_fault.next      = self.dmem.fault
            self.mem_st_misalign.next   = (self.io.dmem_pipeline.valid and
                                           self.io.dmem_pipeline.fcn == MemOp.M_WR and
                                           self.mem_misalign)
            self.mem_st_fault.next      = self.dmem.fault

        @always(self.clk.posedge)
        def _ifid_register():
            """
            Internal pipeline register: IF->ID

            Register the exception signals generated in the IF stage.
            """
            if self.rst:
                self.id_imem_fault.next    = False
                self.id_imem_misalign.next = False
            else:
                self.id_imem_fault.next    = (self.id_imem_fault if (self.io.id_stall or self.io.full_stall) else
                                              (False if (self.io.pipeline_kill or self.io.if_kill) else
                                               self.if_imem_fault))
                self.id_imem_misalign.next = (self.id_imem_misalign if (self.io.id_stall or self.io.full_stall) else
                                              (False if (self.io.pipeline_kill or self.io.if_kill) else
                                               self.if_imem_misalign))

        @always(self.clk.posedge)
        def _idex_register():
            """
            Internal pipeline register: ID->EX

            Register the exceptions signals generated in ID stage: IF + ID exceptions.
            ID exceptions:
            - E_ILLEGAL_INST
            - E_BREAKPOINT
            - Interrupts: software and timer.

            In case of multiple exceptions (the instruction generated an exception at IF, and then at ID),
            blame IF. The priority of exceptions with origin in IF (or ID) is arbitrary.
            """
            if self.rst:
                self.ex_exception.next      = False
                self.ex_exception_code.next = CSRExceptionCode.E_ILLEGAL_INST
                self.ex_mem_funct.next      = MemOp.M_X
                self.ex_mem_valid.next      = False
                self.ex_breakpoint.next     = False
                self.ex_eret.next           = False
                self.ex_ecall.next          = False
                self.ex_csr_cmd.next        = CSRCMD.CSR_IDLE
            else:
                if (self.io.pipeline_kill or self.io.id_kill or self.io.id_stall) and not self.io.full_stall:
                    self.ex_exception.next      = False
                    self.ex_exception_code.next = modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:]
                    self.ex_mem_funct.next      = MemOp.M_X
                    self.ex_breakpoint.next     = False
                    self.ex_eret.next           = False
                    self.ex_ecall.next          = False
                    self.ex_csr_cmd.next        = CSRCMD.CSR_IDLE
                elif not self.io.id_stall and not self.io.full_stall:
                    self.ex_exception.next      = (self.id_imem_misalign or self.id_imem_fault or self.id_illegal_inst or
                                                   self.id_breakpoint or self.io.csr_interrupt)
                    self.ex_exception_code.next = (self.io.csr_interrupt_code if self.io.csr_interrupt else
                                                   (modbv(CSRExceptionCode.E_INST_ADDR_MISALIGNED)[CSRExceptionCode.SZ_ECODE:] if self.id_imem_misalign else
                                                    (modbv(CSRExceptionCode.E_INST_ACCESS_FAULT)[CSRExceptionCode.SZ_ECODE:] if self.id_imem_fault else
                                                     (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:] if self.id_illegal_inst else
                                                      (modbv(CSRExceptionCode.E_BREAKPOINT)[CSRExceptionCode.SZ_ECODE:] if self.id_breakpoint else
                                                       (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:]))))))
                    self.ex_mem_funct.next      = self.io.id_mem_funct
                    self.ex_mem_valid.next      = self.io.id_mem_valid
                    self.ex_breakpoint.next     = self.id_breakpoint
                    self.ex_eret.next           = self.id_eret
                    self.ex_ecall.next          = self.id_ecall
                    self.ex_csr_cmd.next        = self.io.id_csr_cmd

        @always(self.clk.posedge)
        def _exmem_register():
            """
            Internal pipeline register: EX->MEM

            Register the (exception) signals coming from the EX stage.
            This stage does not generates eceptions.
            """
            if self.rst:
                self.mem_breakpoint.next        = False
                self.mem_eret.next              = False
                self.mem_ecall.next             = False
                self.mem_mem_funct.next         = False
                self.mem_exception_ex.next      = False
                self.mem_exception_code_ex.next = modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:]
            else:
                self.mem_breakpoint.next        = (self.mem_breakpoint if self.io.full_stall else (N if self.io.pipeline_kill else self.ex_breakpoint))
                self.mem_eret.next              = (self.mem_eret if self.io.full_stall else (N if self.io.pipeline_kill else self.ex_eret))
                self.mem_ecall.next             = (self.mem_ecall if self.io.full_stall else (N if self.io.pipeline_kill else self.ex_ecall))
                self.mem_mem_funct.next         = (self.mem_mem_funct if self.io.full_stall else (MemOp.M_RD if self.io.pipeline_kill else self.ex_mem_funct))
                self.mem_exception_ex.next      = (self.mem_exception_ex if self.io.full_stall else (N if self.io.pipeline_kill else self.ex_exception))
                self.mem_exception_code_ex.next = (self.mem_exception_code_ex if self.io.full_stall else (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:] if self.io.pipeline_kill else self.ex_exception_code))

        @always(self.clk.posedge)
        def _memwb_register():
            """
            Internal pipeline register: MEM->WB

            Register the memory operation executed at MEM. This is necessary for the correct execution of
            the FENCE.I instruction.
            """
            if self.rst:
                self.wb_mem_funct.next = False
            else:
                self.wb_mem_funct.next = (self.wb_mem_funct if self.io.full_stall else (MemOp.M_RD if self.io.pipeline_kill else self.mem_mem_funct))

        @always_comb
        def _ecall_assignment():
            """
            Check the correct enviroment call.
            """
            self.mem_ecall_u.next = self.io.csr_prv == CSRModes.PRV_U and self.mem_ecall
            self.mem_ecall_s.next = self.io.csr_prv == CSRModes.PRV_S and self.mem_ecall
            self.mem_ecall_h.next = self.io.csr_prv == CSRModes.PRV_H and self.mem_ecall
            self.mem_ecall_m.next = self.io.csr_prv == CSRModes.PRV_M and self.mem_ecall

        @always_comb
        def _exc_assignment():
            """
            Set the exception flag to the CSR, and the exception code.

            Priority for code assignment: IF > ID > MEM.
            """
            self.mem_exception.next      = (self.mem_exception_ex or self.mem_ld_misalign or self.mem_ld_fault or
                                            self.mem_st_misalign or self.mem_st_misalign or self.mem_ecall_u or
                                            self.mem_ecall_s or self.mem_ecall_h or self.mem_ecall_m or self.mem_breakpoint or
                                            self.io.csr_illegal_access)
            self.mem_exception_code.next = (self.mem_exception_code_ex if self.mem_exception_ex else
                                            (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:] if self.io.csr_illegal_access else
                                             (modbv(CSRExceptionCode.E_BREAKPOINT)[CSRExceptionCode.SZ_ECODE:] if self.mem_breakpoint else
                                              (modbv(CSRExceptionCode.E_ECALL_FROM_U)[CSRExceptionCode.SZ_ECODE:] if self.mem_ecall_u else
                                               (modbv(CSRExceptionCode.E_ECALL_FROM_S)[CSRExceptionCode.SZ_ECODE:] if self.mem_ecall_s else
                                                (modbv(CSRExceptionCode.E_ECALL_FROM_H)[CSRExceptionCode.SZ_ECODE:] if self.mem_ecall_h else
                                                 (modbv(CSRExceptionCode.E_ECALL_FROM_M)[CSRExceptionCode.SZ_ECODE:] if self.mem_ecall_m else
                                                  (modbv(CSRExceptionCode.E_LOAD_ACCESS_FAULT)[CSRExceptionCode.SZ_ECODE:] if self.mem_ld_fault else
                                                   (modbv(CSRExceptionCode.E_LOAD_ADDR_MISALIGNED)[CSRExceptionCode.SZ_ECODE:] if self.mem_ld_misalign else
                                                    (modbv(CSRExceptionCode.E_AMO_ACCESS_FAULT)[CSRExceptionCode.SZ_ECODE:] if self.mem_st_fault else
                                                     (modbv(CSRExceptionCode.E_AMO_ADDR_MISALIGNED)[CSRExceptionCode.SZ_ECODE:] if self.mem_st_misalign else
                                                      modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:])))))))))))

        @always_comb
        def _branch_detect():
            """
            Generate branch conditions: EQ, LT and LTU.
            """
            self.id_eq.next  = self.io.id_op1 == self.io.id_op2
            self.id_lt.next  = self.io.id_op1.signed() < self.io.id_op2.signed()
            self.id_ltu.next = self.io.id_op1 < self.io.id_op2

        @always_comb
        def _pc_select():
            """
            Set the control signal for the next PC multiplexer.

            Priority: PC from CSR (exception handler or epc), PC for branch and jump instructions, PC for jump
            register instructions, and PC + 4.
            """
            self.io.pc_select.next = (modbv(Consts.PC_EXC)[Consts.SZ_PC_SEL:] if self.io.csr_exception or self.io.csr_eret else
                                      (modbv(Consts.PC_BRJMP)[Consts.SZ_PC_SEL:] if ((self.id_br_type == Consts.BR_J) or
                                                                                     (self.id_br_type == Consts.BR_NE and not self.id_eq) or
                                                                                     (self.id_br_type == Consts.BR_EQ and self.id_eq) or
                                                                                     (self.id_br_type == Consts.BR_LT and self.id_lt) or
                                                                                     (self.id_br_type == Consts.BR_LTU and self.id_ltu) or
                                                                                     (self.id_br_type == Consts.BR_GE and not self.id_lt) or
                                                                                     (self.id_br_type == Consts.BR_GEU and not self.id_ltu)) else
                                       (modbv(Consts.PC_JALR)[Consts.SZ_PC_SEL:] if self.id_br_type == Consts.BR_JR else
                                        (modbv(Consts.PC_4)[Consts.SZ_PC_SEL:]))))

        @always_comb
        def _fwd_ctrl():
            """
            Set forwarding controls.

            Rules: the read address is not r0, the read address must match the write address, and the instruction must write to the RF (we == 1).
            Priority: EX > MEM > WB
            """
            self.io.id_fwd1_select.next = (modbv(Consts.FWD_EX)[Consts.SZ_FWD:] if self.io.id_rs1_addr != 0 and self.io.id_rs1_addr == self.io.ex_wb_addr and self.io.ex_wb_we else
                                           (modbv(Consts.FWD_MEM)[Consts.SZ_FWD:] if self.io.id_rs1_addr != 0 and self.io.id_rs1_addr == self.io.mem_wb_addr and self.io.mem_wb_we else
                                            (modbv(Consts.FWD_WB)[Consts.SZ_FWD:] if self.io.id_rs1_addr != 0 and self.io.id_rs1_addr == self.io.wb_wb_addr and self.io.wb_wb_we else
                                             modbv(Consts.FWD_N)[Consts.SZ_FWD:])))
            self.io.id_fwd2_select.next = (modbv(Consts.FWD_EX)[Consts.SZ_FWD:] if self.io.id_rs2_addr != 0 and self.io.id_rs2_addr == self.io.ex_wb_addr and self.io.ex_wb_we else
                                           (modbv(Consts.FWD_MEM)[Consts.SZ_FWD:] if self.io.id_rs2_addr != 0 and self.io.id_rs2_addr == self.io.mem_wb_addr and self.io.mem_wb_we else
                                            (modbv(Consts.FWD_WB)[Consts.SZ_FWD:] if self.io.id_rs2_addr != 0 and self.io.id_rs2_addr == self.io.wb_wb_addr and self.io.wb_wb_we else
                                             (modbv(Consts.FWD_N)[Consts.SZ_FWD:]))))

        @always_comb
        def _ctrl_pipeline():
            """
            Set control signals for pipeline registers.
            """
            self.io.if_kill.next       = self.io.pc_select != Consts.PC_4
            self.io.id_stall.next      = (((self.io.id_fwd1_select == Consts.FWD_EX or self.io.id_fwd2_select == Consts.FWD_EX) and
                                           ((self.ex_mem_funct == MemOp.M_RD and self.ex_mem_valid) or self.ex_csr_cmd != CSRCMD.CSR_IDLE)) or
                                          (self.id_fence_i and (self.ex_mem_funct == MemOp.M_WR or self.mem_mem_funct == MemOp.M_WR or self.wb_mem_funct == MemOp.M_WR)))
            self.io.id_kill.next       = False
            self.io.full_stall.next    = self.imem.valid or self.dmem.valid or self.io.ex_req_stall
            self.io.pipeline_kill.next = self.io.csr_exception or self.io.csr_eret

        @always_comb
        def _exc_detect():
            """
            Connect the internal exception registers to the CSR exception ports.
            """
            self.io.csr_exception.next      = self.mem_exception
            self.io.csr_exception_code.next = self.mem_exception_code

        @always_comb
        def _imem_assignment():
            """
            Connect the pipeline imem port to the control imem port.
            """
            self.imem.addr.next              = self.io.imem_pipeline.addr
            self.imem.wdata.next             = self.io.imem_pipeline.wdata
            self.imem.fcn.next               = self.io.imem_pipeline.fcn
            self.imem.wr.next                = 0b0000  # always read
            self.io.imem_pipeline.rdata.next = self.imem.rdata

        @always_comb
        def _imem_control():
            """
            Logic for the valid signal.

            Enable the access if the pipeline requests it, and wait until the memory response. Abort in case
            of exception.
            """
            self.imem.valid.next = (self.io.imem_pipeline.valid and (not self.imem.ready) and
                                    not self.io.csr_exception)

        @always_comb
        def _dmem_assignment():
            """
            Connect the pipeline dmem port to the control dmem port.
            """
            self.dmem.addr.next = self.io.dmem_pipeline.addr
            self.dmem.fcn.next  = self.io.dmem_pipeline.fcn

        @always_comb
        def _dmem_read_data():
            """
            Data convertion from dmem to pipeline.

            Generate the correct data type:
            - Signed byte.
            - Unsigned byte.
            - Signed half-word
            - Unsigned half-word
            - Word
            """
            if self.io.dmem_pipeline.typ[2:0] == MemOp.MT_B:
                if self.io.dmem_pipeline.addr[2:0] == 0:
                    self.io.dmem_pipeline.rdata.next = self.dmem.rdata[8:0].signed() if not self.io.dmem_pipeline.typ[2] else self.dmem.rdata[8:0]
                elif self.io.dmem_pipeline.addr[2:0] == 1:
                    self.io.dmem_pipeline.rdata.next = self.dmem.rdata[16:8].signed() if not self.io.dmem_pipeline.typ[2] else self.dmem.rdata[16:8]
                elif self.io.dmem_pipeline.addr[2:0] == 2:
                    self.io.dmem_pipeline.rdata.next = self.dmem.rdata[24:16].signed() if not self.io.dmem_pipeline.typ[2] else self.dmem.rdata[24:16]
                else:
                    self.io.dmem_pipeline.rdata.next = self.dmem.rdata[32:24].signed() if not self.io.dmem_pipeline.typ[2] else self.dmem.rdata[32:24]
            elif self.io.dmem_pipeline.typ[2:0] == MemOp.MT_H:
                if not self.io.dmem_pipeline.addr[1]:
                    self.io.dmem_pipeline.rdata.next = self.dmem.rdata[16:0].signed() if not self.io.dmem_pipeline.typ[2] else self.dmem.rdata[16:0]
                else:
                    self.io.dmem_pipeline.rdata.next = self.dmem.rdata[32:16].signed() if not self.io.dmem_pipeline.typ[2] else self.dmem.rdata[32:16]
            else:
                self.io.dmem_pipeline.rdata.next = self.dmem.rdata

        @always_comb
        def _dmem_write_data():
            """
            Data convertion from pipeline to dmem.

            Generate a pattern to write to memory:
            - Byte: [b, b, b, b]
            - Half-word: [h, h]
            - Word: [w]
            with the wr signal:
            - Byte: [b3, b2, b1, b0]
            - Half-word: [h1, h1, h0, h0]
            - Word: [1, 1, 1, 1]
            where:
            - bx = bytes x, x in [3, 2, 1, 0]
            - hx = halfword x, x in [1, 0]
            """
            # set WR
            if self.io.dmem_pipeline.fcn == MemOp.M_WR:
                self.dmem.wr.next = (concat(self.io.dmem_pipeline.addr[2:0] == 3,
                                            self.io.dmem_pipeline.addr[2:0] == 2,
                                            self.io.dmem_pipeline.addr[2:0] == 1,
                                            self.io.dmem_pipeline.addr[2:0] == 0) if self.io.dmem_pipeline.typ[2:0] == MemOp.MT_B else
                                     (concat(self.io.dmem_pipeline.addr[2:0] == 2,
                                             self.io.dmem_pipeline.addr[2:0] == 2,
                                             self.io.dmem_pipeline.addr[2:0] == 0,
                                             self.io.dmem_pipeline.addr[2:0] == 0) if self.io.dmem_pipeline.typ[2:0] == MemOp.MT_H else
                                      modbv(0b1111)[4:]))
            else:
                self.dmem.wr.next = 0b0000

            # Data to memory
            self.dmem.wdata.next = (concat(self.io.dmem_pipeline.wdata[8:0],
                                           self.io.dmem_pipeline.wdata[8:0],
                                           self.io.dmem_pipeline.wdata[8:0],
                                           self.io.dmem_pipeline.wdata[8:0]) if self.io.dmem_pipeline.typ[2:0] == MemOp.MT_B else
                                    (concat(self.io.dmem_pipeline.wdata[16:0],
                                            self.io.dmem_pipeline.wdata[16:0]) if self.io.dmem_pipeline.typ[2:0] == MemOp.MT_H else
                                     (self.io.dmem_pipeline.wdata)))

        @always_comb
        def _dmem_control():
            """
            Logic for the valid signal.

            Enable the access if the pipeline requests it, and wait until the memory response. Abort in case
            of exception.
            """
            self.dmem.valid.next = (self.io.dmem_pipeline.valid and (not self.dmem.ready) and
                                    not self.io.csr_exception)

        return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
