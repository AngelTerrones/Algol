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
from Core.csr import CSRCMD
from Core.csr import CSRExceptionCode
from Core.csr import CSRModes
from Core.wishbone import WishboneMaster
from Core.wishbone import WishboneMasterGenerator
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
    #                  Illegal                                                 Valid memory operation                                           OP1 select
    #                  |  Fence.I                                              |  Memory Function (type)                                        |                 OP2 select
    #                  |  |  Fence                                             |  |            Memory type                                      |                 |                 Branch/Jump
    #                  |  |  |  ecall                                          |  |            |              ALU operation                     |                 |                 |
    #                  |  |  |  |  ebreak                                      |  |            |              |                 IMM type        |                 |                 |
    #                  |  |  |  |  |  eret                                     |  |            |              |                 |               |                 |                 |
    #                  |  |  |  |  |  |  RF WE              CSR command        |  |            |              |                 |               |                 |                 |
    #                  |  |  |  |  |  |  |  Sel dat to WB   |                  |  |            |              |                 |               |                 |                 |
    #                  |  |  |  |  |  |  |  |               |                  |  |            |              |                 |               |                 |                 |
    #                  |  |  |  |  |  |  |  |               |                  |  |            |              |                 |               |                 |                 |
    NOP       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    INVALID   = concat(Y, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    LUI       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_U,  Consts._OP1_ZERO, Consts._OP2_IMM,  Consts._BR_N).__int__()
    AUIPC     = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_U,  Consts._OP1_PC,   Consts._OP2_IMM,  Consts._BR_N).__int__()
    JAL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_UJ, Consts._OP1_PC,   Consts._OP2_FOUR, Consts._BR_J).__int__()
    JALR      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_PC,   Consts._OP2_FOUR, Consts._BR_JR).__int__()
    BEQ       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_EQ).__int__()
    BNE       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_NE).__int__()
    BLT       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_LT).__int__()
    BGE       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_GE).__int__()
    BLTU      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_LTU).__int__()
    BGEU      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_SB, Consts._OP1_X,    Consts._OP2_X,    Consts._BR_GEU).__int__()
    LB        = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, Consts.M_RD, Consts._MT_B,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LH        = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, Consts.M_RD, Consts._MT_H,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LW        = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, Consts.M_RD, Consts._MT_W,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LBU       = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, Consts.M_RD, Consts._MT_BU, ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    LHU       = concat(N, N, N, N, N, N, Y, Consts._WB_MEM, CSRCMD._CSR_IDLE,  Y, Consts.M_RD, Consts._MT_HU, ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SB        = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  Y, Consts.M_WR, Consts._MT_B,  ALUOp._OP_ADD,    Consts._IMM_S,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SH        = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  Y, Consts.M_WR, Consts._MT_H,  ALUOp._OP_ADD,    Consts._IMM_S,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SW        = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  Y, Consts.M_WR, Consts._MT_W,  ALUOp._OP_ADD,    Consts._IMM_S,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ADDI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SLTI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SLT,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SLTIU     = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SLTU,   Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    XORI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_XOR,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ORI       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_OR,     Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ANDI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_AND,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SLLI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SLL,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SRLI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SRL,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    SRAI      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SRA,    Consts._IMM_I,  Consts._OP1_RS1,  Consts._OP2_IMM,  Consts._BR_N).__int__()
    ADD       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SUB       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SUB,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SLL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SLL,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SLT       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SLT,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SLTU      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SLTU,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    XOR       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_XOR,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SRL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SRL,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    SRA       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_SRA,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    OR        = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_OR,     Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    AND       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_AND,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    FENCE     = concat(N, N, Y, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    FENCE_I   = concat(N, Y, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    CSRRW     = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_WRITE, N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRS     = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_SET,   N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRC     = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_CLEAR, N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRWI    = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_WRITE, N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRSI    = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_SET,   N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    CSRRCI    = concat(N, N, N, N, N, N, Y, Consts._WB_CSR, CSRCMD._CSR_CLEAR, N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_ZERO, Consts._OP2_ZERO, Consts._BR_N).__int__()
    ECALL     = concat(N, N, N, Y, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    EBREAK    = concat(N, N, N, N, Y, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    ERET      = concat(N, N, N, N, N, Y, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    MRTS      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    MRTH      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    HRTS      = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    WFI       = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    SFENCE_VM = concat(N, N, N, N, N, N, N, Consts._WB_X,   CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_ADD,    Consts._IMM_X,  Consts._OP1_X,    Consts._OP2_X,    Consts._BR_N).__int__()
    MUL       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_MUL,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    MULH      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_MULH,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    MULHSU    = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_MULHSU, Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    MULHU     = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_MULHU,  Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    DIV       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_DIV,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    DIVU      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_DIVU,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    REM       = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_REM,    Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()
    REMU      = concat(N, N, N, N, N, N, Y, Consts._WB_ALU, CSRCMD._CSR_IDLE,  N, Consts.M_X,  Consts._MT_X,  ALUOp._OP_REMU,   Consts._IMM_X,  Consts._OP1_RS1,  Consts._OP2_RS2,  Consts._BR_N).__int__()


class CtrlIO:
    """
    Defines a bundle for the IO interface between the cpath and the dpath.

    :ivar id_instruction:     Intruction at ID stage
    :ivar if_kill:            Kill the IF stage
    :ivar id_stall:           Stall the ID stage
    :ivar id_kill:            Kill the ID stage
    :ivar full_stall:         Stall whole pipeline
    :ivar pipeline_kill:      Kill the pipeline
    :ivar pc_select:          Select next PC
    :ivar id_op1_select:      Data select for OP1 at ID stage
    :ivar id_op2_select:      Data select for OP2 at ID stage
    :ivar id_sel_imm:         Select the Immediate
    :ivar id_alu_funct:       ALU opcode
    :ivar id_mem_type:        Data size for memory operations: byte, half-word, word
    :ivar id_mem_funct:       Memory function: read (RD) or write (WR)
    :ivar id_mem_valid:       Valid memory operation
    :ivar id_csr_cmd:         CSR command
    :ivar id_mem_data_sel:    Data source for mux at MEM stage: ALU, memory or CSR
    :ivar id_wb_we:           Commit data to RF
    :ivar id_fwd1_select:     Forwarding selector for OP1
    :ivar id_fwd2_select:     Forwarding selector for OP2
    :ivar id_rs1_addr:        OP1 address
    :ivar id_rs2_addr:        OP2 address
    :ivar id_op1:             OP1 data
    :ivar id_op2:             OP2 data
    :ivar ex_wb_addr:         RF write address at EX stage
    :ivar ex_wb_we:           RF write enable at EX stage
    :ivar ex_req_stall:       Long operation in EX.
    :ivar mem_wb_addr:        RF write address at MEM stage
    :ivar mem_wb_we:          RF write enable at MEM stage
    :ivar wb_wb_addr:         RF write address at WB stage
    :ivar wb_wb_we:           RF write enable at WB stage
    :ivar csr_eret:           Instruction is ERET
    :ivar csr_prv:            Priviledge level at MEM stage
    :ivar csr_illegal_access: Illegal access to CSR: CSR at MEM
    :ivar csr_interrupt:      External interrupt: CSR at ID
    :ivar csr_interrupt_code: Interrupt code: CSR at ID
    :ivar csr_exception:      Exception detected: CSR at MEM
    :ivar csr_exception_code: Exception code: CSR at MEM
    :ivar csr_retire:         Increment instruction count: CSR at MEM
    :ivar imem_pipeline:      Instruction memory access request from dpath
    :ivar dmem_pipeline:      Data memory access request from dpath
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
        self.id_mem_type        = Signal(modbv(0)[Consts.SZ_MT:])
        self.id_mem_funct       = Signal(modbv(0)[Consts.SZ_M:])
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
        self.ex_req_stall       = Signal(False)
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


def Ctrlpath(clk,
             rst,
             io,
             imem,
             dmem):
    """
    The decoder, exception, hazard detection, and control unit.

    :param clk:  Main clock
    :param rst:  Main reset
    :param io:   Interface with dapath
    :param imem: Wishbone master (instruction port)
    :param dmem: Wishbone master (data port)
    """
    imem_m = WishboneMaster(imem)
    dmem_m = WishboneMaster(dmem)

    id_br_type            = Signal(modbv(0)[Consts.SZ_BR:])
    id_eq                 = Signal(False)
    id_lt                 = Signal(False)
    id_ltu                = Signal(False)
    id_fence_i            = Signal(False)
    id_fence              = Signal(False)

    if_imem_misalign      = Signal(False)
    if_imem_fault         = Signal(False)
    id_breakpoint         = Signal(False)
    id_eret               = Signal(False)
    id_ebreak             = Signal(False)
    id_ecall              = Signal(False)
    id_illegal_inst       = Signal(False)
    mem_ld_misalign       = Signal(False)
    mem_ld_fault          = Signal(False)
    mem_st_misalign       = Signal(False)
    mem_st_fault          = Signal(False)

    id_imem_misalign      = Signal(False)
    id_imem_fault         = Signal(False)
    ex_breakpoint         = Signal(False)
    ex_eret               = Signal(False)
    ex_ecall              = Signal(False)
    ex_exception          = Signal(False)
    ex_exception_code     = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
    ex_mem_funct          = Signal(modbv(0)[Consts.SZ_M:])
    ex_mem_valid          = Signal(False)
    ex_csr_cmd            = Signal(modbv(0)[CSRCMD.SZ_CMD:])
    mem_breakpoint        = Signal(False)
    mem_eret              = Signal(False)
    mem_ecall             = Signal(False)
    mem_ecall_u           = Signal(False)
    mem_ecall_s           = Signal(False)
    mem_ecall_h           = Signal(False)
    mem_ecall_m           = Signal(False)
    mem_exception_ex      = Signal(False)
    mem_exception_code_ex = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
    mem_exception         = Signal(False)
    mem_exception_code    = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
    mem_mem_funct         = Signal(modbv(0)[Consts.SZ_M:])
    wb_mem_funct          = Signal(modbv(0)[Consts.SZ_M:])
    control               = Signal(modbv(0)[33:])

    if_misalign           = Signal(False)
    mem_misalign          = Signal(False)

    opcode                = Signal(modbv(0)[7:])
    funct3                = Signal(modbv(0)[3:])
    funct7                = Signal(modbv(0)[7:])

    @always_comb
    def _ctrl_assignment():
        """
        Get the opcode and funct3 fields from the instruction.
        """
        opcode.next = io.id_instruction[7:0]
        funct3.next = io.id_instruction[15:12]
        funct7.next = io.id_instruction[32:25]

    @always_comb
    def _ctrl_signal_assignment():
        """
        Instruction decoding.
        """
        if opcode == Opcodes.RV32_LUI:
            control.next = CtrlSignals.LUI
        elif opcode == Opcodes.RV32_AUIPC:
            control.next = CtrlSignals.AUIPC
        elif opcode == Opcodes.RV32_JAL:
            control.next = CtrlSignals.JAL
        elif opcode == Opcodes.RV32_JALR:
            control.next = CtrlSignals.JALR
        elif opcode == Opcodes.RV32_BRANCH:
            if funct3 == BranchFunct3.RV32_F3_BEQ:
                control.next = CtrlSignals.BEQ
            elif funct3 == BranchFunct3.RV32_F3_BNE:
                control.next = CtrlSignals.BNE
            elif funct3 == BranchFunct3.RV32_F3_BLT:
                control.next = CtrlSignals.BLT
            elif funct3 == BranchFunct3.RV32_F3_BGE:
                control.next = CtrlSignals.BGE
            elif funct3 == BranchFunct3.RV32_F3_BLTU:
                control.next = CtrlSignals.BLTU
            elif funct3 == BranchFunct3.RV32_F3_BGEU:
                control.next = CtrlSignals.BGEU
            else:
                control.next = CtrlSignals.INVALID
        elif opcode == Opcodes.RV32_LOAD:
            if funct3 == LoadFunct3.RV32_F3_LB:
                control.next = CtrlSignals.LB
            elif funct3 == LoadFunct3.RV32_F3_LH:
                control.next = CtrlSignals.LH
            elif funct3 == LoadFunct3.RV32_F3_LW:
                control.next = CtrlSignals.LW
            elif funct3 == LoadFunct3.RV32_F3_LBU:
                control.next = CtrlSignals.LBU
            elif funct3 == LoadFunct3.RV32_F3_LHU:
                control.next = CtrlSignals.LHU
            else:
                control.next = CtrlSignals.INVALID
        elif opcode == Opcodes.RV32_STORE:
            if funct3 == StoreFunct3.RV32_F3_SB:
                control.next = CtrlSignals.SB
            elif funct3 == StoreFunct3.RV32_F3_SH:
                control.next = CtrlSignals.SH
            elif funct3 == StoreFunct3.RV32_F3_SW:
                control.next = CtrlSignals.SW
            else:
                control.next = CtrlSignals.INVALID
        elif opcode == Opcodes.RV32_IMM:
            if funct3 == ArithmeticFunct3.RV32_F3_ADD_SUB:
                control.next = CtrlSignals.ADDI
            elif funct3 == ArithmeticFunct3.RV32_F3_SLT:
                control.next = CtrlSignals.SLTI
            elif funct3 == ArithmeticFunct3.RV32_F3_SLTU:
                control.next = CtrlSignals.SLTIU
            elif funct3 == ArithmeticFunct3.RV32_F3_XOR:
                control.next = CtrlSignals.XORI
            elif funct3 == ArithmeticFunct3.RV32_F3_OR:
                control.next = CtrlSignals.ORI
            elif funct3 == ArithmeticFunct3.RV32_F3_AND:
                control.next = CtrlSignals.ANDI
            elif funct3 == ArithmeticFunct3.RV32_F3_SLL:
                control.next = CtrlSignals.SLLI
            elif funct3 == ArithmeticFunct3.RV32_F3_SRL_SRA:
                if io.id_instruction[30]:
                    control.next = CtrlSignals.SRAI
                else:
                    control.next = CtrlSignals.SRLI
            else:
                control.next = CtrlSignals.INVALID
        elif opcode == Opcodes.RV32_OP:
            if funct7 != MulDivFunct.RV32_F7_MUL_DIV:
                if funct3 == ArithmeticFunct3.RV32_F3_ADD_SUB:
                    if io.id_instruction[30]:
                        control.next = CtrlSignals.SUB
                    else:
                        control.next = CtrlSignals.ADD
                elif funct3 == ArithmeticFunct3.RV32_F3_SLT:
                    control.next = CtrlSignals.SLT
                elif funct3 == ArithmeticFunct3.RV32_F3_SLTU:
                    control.next = CtrlSignals.SLTU
                elif funct3 == ArithmeticFunct3.RV32_F3_XOR:
                    control.next = CtrlSignals.XOR
                elif funct3 == ArithmeticFunct3.RV32_F3_OR:
                    control.next = CtrlSignals.OR
                elif funct3 == ArithmeticFunct3.RV32_F3_AND:
                    control.next = CtrlSignals.AND
                elif funct3 == ArithmeticFunct3.RV32_F3_SLL:
                    control.next = CtrlSignals.SLL
                elif funct3 == ArithmeticFunct3.RV32_F3_SRL_SRA:
                    if io.id_instruction[30]:
                        control.next = CtrlSignals.SRA
                    else:
                        control.next = CtrlSignals.SRL
                else:
                    control.next = CtrlSignals.INVALID
            elif funct7 == MulDivFunct.RV32_F7_MUL_DIV:
                if funct3 == MulDivFunct.RV32_F3_MUL:
                    control.next = CtrlSignals.MUL
                elif funct3 == MulDivFunct.RV32_F3_MULH:
                    control.next = CtrlSignals.MULH
                elif funct3 == MulDivFunct.RV32_F3_MULHSU:
                    control.next = CtrlSignals.MULHSU
                elif funct3 == MulDivFunct.RV32_F3_MULHU:
                    control.next = CtrlSignals.MULHU
                elif funct3 == MulDivFunct.RV32_F3_DIV:
                    control.next = CtrlSignals.DIV
                elif funct3 == MulDivFunct.RV32_F3_DIVU:
                    control.next = CtrlSignals.DIVU
                elif funct3 == MulDivFunct.RV32_F3_REM:
                    control.next = CtrlSignals.REM
                elif funct3 == MulDivFunct.RV32_F3_REMU:
                    control.next = CtrlSignals.REMU
                else:
                    control.next = CtrlSignals.INVALID
            else:
                control.next = CtrlSignals.INVALID
        elif opcode == Opcodes.RV32_FENCE:
            if funct3 == FenceFunct3.RV32_F3_FENCE:
                control.next = CtrlSignals.FENCE
            elif funct3 == FenceFunct3.RV32_F3_FENCE_I:
                control.next = CtrlSignals.FENCE_I
            else:
                control.next = CtrlSignals.INVALID
        elif opcode == Opcodes.RV32_SYSTEM:
            if funct3 == SystemFunct3.RV32_F3_PRIV:
                if io.id_instruction[32:20] == PrivFunct12.RV32_F12_ECALL:
                    control.next = CtrlSignals.ECALL
                elif io.id_instruction[32:20] == PrivFunct12.RV32_F12_EBREAK:
                    control.next = CtrlSignals.EBREAK
                elif io.id_instruction[32:20] == PrivFunct12.RV32_F12_ERET:
                    control.next = CtrlSignals.ERET
                else:
                    control.next = CtrlSignals.INVALID
            elif funct3 == SystemFunct3.RV32_F3_CSRRW:
                control.next = CtrlSignals.CSRRW
            elif funct3 == SystemFunct3.RV32_F3_CSRRS:
                control.next = CtrlSignals.CSRRS
            elif funct3 == SystemFunct3.RV32_F3_CSRRC:
                control.next = CtrlSignals.CSRRC
            elif funct3 == SystemFunct3.RV32_F3_CSRRWI:
                control.next = CtrlSignals.CSRRWI
            elif funct3 == SystemFunct3.RV32_F3_CSRRSI:
                control.next = CtrlSignals.CSRRSI
            elif funct3 == SystemFunct3.RV32_F3_CSRRCI:
                control.next = CtrlSignals.CSRRCI
            else:
                control.next = CtrlSignals.INVALID
        else:
            control.next = CtrlSignals.INVALID

    @always_comb
    def _assignments():
        """
        Individual assignment of control signals.

        Each signal correspond to slice in the vectored control signal (check CtrlSignals class).
        Except the 'id_csr_cmd' signal: This signal depends if the control is a CSR_IDLE command.
        If it is an CSR_IDLE command, we need to check 'id_rs1_addr': in case of being equal to zero, the
        command does not write to the CSR, becoming a CSR_READ command.
        """
        id_br_type.next         = control[4:0]
        io.id_op2_select.next   = control[6:4]
        io.id_op1_select.next   = control[8:6]
        io.id_sel_imm.next      = control[11:8]
        io.id_alu_funct.next    = control[16:11]
        io.id_mem_type.next     = control[19:16]
        io.id_mem_funct.next    = control[19]
        io.id_mem_valid.next    = control[20]
        io.id_csr_cmd.next      = control[24:21] if (control[24:21] == CSRCMD.CSR_IDLE or io.id_rs1_addr != 0) else modbv(CSRCMD.CSR_READ)[CSRCMD.SZ_CMD:]
        io.id_mem_data_sel.next = control[26:24]
        io.id_wb_we.next        = control[26]
        id_eret.next            = control[27]
        id_ebreak.next          = control[28]
        id_ecall.next           = control[29]
        id_fence.next           = control[30]
        id_fence_i.next         = control[31]

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
        io.csr_retire.next   = not io.full_stall and not io.csr_exception
        io.csr_eret.next     = mem_eret and io.csr_prv != CSRModes.PRV_U and not io.full_stall
        id_illegal_inst.next = control[32]
        id_breakpoint.next   = id_ebreak

    @always_comb
    def _assignments3():
        """
        Determines address misalignment.
        """
        if_misalign.next  = (io.imem_pipeline.addr[0] if (io.imem_pipeline.typ == Consts.MT_H) or (io.imem_pipeline.typ == Consts.MT_HU) else
                             ((io.imem_pipeline.addr[0] or io.imem_pipeline.addr[1]) if io.imem_pipeline.typ == Consts.MT_W else
                              (False)))
        mem_misalign.next = (io.dmem_pipeline.addr[0] if (io.dmem_pipeline.typ == Consts.MT_H) or (io.dmem_pipeline.typ == Consts.MT_HU) else
                             ((io.dmem_pipeline.addr[0] or io.dmem_pipeline.addr[1]) if io.dmem_pipeline.typ == Consts.MT_W else
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
        if_imem_misalign.next = if_misalign
        if_imem_fault.next    = imem_m.err_i
        mem_ld_misalign.next  = (io.dmem_pipeline.valid and
                                 io.dmem_pipeline.fcn == Consts.M_RD and
                                 mem_misalign)
        mem_ld_fault.next     = dmem_m.err_i
        mem_st_misalign.next  = (io.dmem_pipeline.valid and
                                 io.dmem_pipeline.fcn == Consts.M_WR and
                                 mem_misalign)
        mem_st_fault.next     = dmem_m.err_i

    @always(clk.posedge)
    def _ifid_register():
        """
        Internal pipeline register: IF->ID

        Register the exception signals generated in the IF stage.
        """
        if rst:
            id_imem_fault.next    = False
            id_imem_misalign.next = False
        else:
            id_imem_fault.next    = (id_imem_fault if (io.id_stall or io.full_stall) else
                                     (False if (io.pipeline_kill or io.if_kill) else
                                      if_imem_fault))
            id_imem_misalign.next = (id_imem_misalign if (io.id_stall or io.full_stall) else
                                     (False if (io.pipeline_kill or io.if_kill) else
                                      if_imem_misalign))

    @always(clk.posedge)
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
        if rst:
            ex_exception.next      = False
            ex_exception_code.next = CSRExceptionCode.E_ILLEGAL_INST
            ex_mem_funct.next      = Consts.M_X
            ex_mem_valid.next      = False
            ex_breakpoint.next     = False
            ex_eret.next           = False
            ex_ecall.next          = False
            ex_csr_cmd.next        = CSRCMD.CSR_IDLE
        else:
            if (io.pipeline_kill or io.id_kill or io.id_stall) and not io.full_stall:
                ex_exception.next      = False
                ex_exception_code.next = modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:]
                ex_mem_funct.next      = Consts.M_X
                ex_breakpoint.next     = False
                ex_eret.next           = False
                ex_ecall.next          = False
                ex_csr_cmd.next        = CSRCMD.CSR_IDLE
            elif not io.id_stall and not io.full_stall:
                ex_exception.next      = (id_imem_misalign or id_imem_fault or id_illegal_inst or
                                          id_breakpoint or io.csr_interrupt)
                ex_exception_code.next = (io.csr_interrupt_code if io.csr_interrupt else
                                          (modbv(CSRExceptionCode.E_INST_ADDR_MISALIGNED)[CSRExceptionCode.SZ_ECODE:] if id_imem_misalign else
                                           (modbv(CSRExceptionCode.E_INST_ACCESS_FAULT)[CSRExceptionCode.SZ_ECODE:] if id_imem_fault else
                                            (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:] if id_illegal_inst else
                                             (modbv(CSRExceptionCode.E_BREAKPOINT)[CSRExceptionCode.SZ_ECODE:] if id_breakpoint else
                                              (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:]))))))
                ex_mem_funct.next      = io.id_mem_funct
                ex_mem_valid.next      = io.id_mem_valid
                ex_breakpoint.next     = id_breakpoint
                ex_eret.next           = id_eret
                ex_ecall.next          = id_ecall
                ex_csr_cmd.next        = io.id_csr_cmd

    @always(clk.posedge)
    def _exmem_register():
        """
        Internal pipeline register: EX->MEM

        Register the (exception) signals coming from the EX stage.
        This stage does not generates eceptions.
        """
        if rst:
            mem_breakpoint.next        = False
            mem_eret.next              = False
            mem_ecall.next             = False
            mem_mem_funct.next         = False
            mem_exception_ex.next      = False
            mem_exception_code_ex.next = modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:]
        else:
            mem_breakpoint.next        = (mem_breakpoint if io.full_stall else (N if io.pipeline_kill else ex_breakpoint))
            mem_eret.next              = (mem_eret if io.full_stall else (N if io.pipeline_kill else ex_eret))
            mem_ecall.next             = (mem_ecall if io.full_stall else (N if io.pipeline_kill else ex_ecall))
            mem_mem_funct.next         = (mem_mem_funct if io.full_stall else (Consts.M_RD if io.pipeline_kill else ex_mem_funct))
            mem_exception_ex.next      = (mem_exception_ex if io.full_stall else (N if io.pipeline_kill else ex_exception))
            mem_exception_code_ex.next = (mem_exception_code_ex if io.full_stall else (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:] if io.pipeline_kill else ex_exception_code))

    @always(clk.posedge)
    def _memwb_register():
        """
        Internal pipeline register: MEM->WB

        Register the memory operation executed at MEM. This is necessary for the correct execution of
        the FENCE.I instruction.
        """
        if rst:
            wb_mem_funct.next = False
        else:
            wb_mem_funct.next = (wb_mem_funct if io.full_stall else (Consts.M_RD if io.pipeline_kill else mem_mem_funct))

    @always_comb
    def _ecall_assignment():
        """
        Check the correct enviroment call.
        """
        mem_ecall_u.next = io.csr_prv == CSRModes.PRV_U and mem_ecall
        mem_ecall_s.next = io.csr_prv == CSRModes.PRV_S and mem_ecall
        mem_ecall_h.next = io.csr_prv == CSRModes.PRV_H and mem_ecall
        mem_ecall_m.next = io.csr_prv == CSRModes.PRV_M and mem_ecall

    @always_comb
    def _exc_assignment():
        """
        Set the exception flag to the CSR, and the exception code.

        Priority for code assignment: IF > ID > MEM.
        """
        mem_exception.next      = (mem_exception_ex or mem_ld_misalign or mem_ld_fault or
                                   mem_st_misalign or mem_st_misalign or mem_ecall_u or
                                   mem_ecall_s or mem_ecall_h or mem_ecall_m or mem_breakpoint or
                                   io.csr_illegal_access)
        mem_exception_code.next = (mem_exception_code_ex if mem_exception_ex else
                                   (modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:] if io.csr_illegal_access else
                                    (modbv(CSRExceptionCode.E_BREAKPOINT)[CSRExceptionCode.SZ_ECODE:] if mem_breakpoint else
                                     (modbv(CSRExceptionCode.E_ECALL_FROM_U)[CSRExceptionCode.SZ_ECODE:] if mem_ecall_u else
                                      (modbv(CSRExceptionCode.E_ECALL_FROM_S)[CSRExceptionCode.SZ_ECODE:] if mem_ecall_s else
                                       (modbv(CSRExceptionCode.E_ECALL_FROM_H)[CSRExceptionCode.SZ_ECODE:] if mem_ecall_h else
                                        (modbv(CSRExceptionCode.E_ECALL_FROM_M)[CSRExceptionCode.SZ_ECODE:] if mem_ecall_m else
                                         (modbv(CSRExceptionCode.E_LOAD_ACCESS_FAULT)[CSRExceptionCode.SZ_ECODE:] if mem_ld_fault else
                                          (modbv(CSRExceptionCode.E_LOAD_ADDR_MISALIGNED)[CSRExceptionCode.SZ_ECODE:] if mem_ld_misalign else
                                           (modbv(CSRExceptionCode.E_AMO_ACCESS_FAULT)[CSRExceptionCode.SZ_ECODE:] if mem_st_fault else
                                            (modbv(CSRExceptionCode.E_AMO_ADDR_MISALIGNED)[CSRExceptionCode.SZ_ECODE:] if mem_st_misalign else
                                             modbv(CSRExceptionCode.E_ILLEGAL_INST)[CSRExceptionCode.SZ_ECODE:])))))))))))

    @always_comb
    def _branch_detect():
        """
        Generate branch conditions: EQ, LT and LTU.
        """
        id_eq.next  = io.id_op1 == io.id_op2
        id_lt.next  = io.id_op1.signed() < io.id_op2.signed()
        id_ltu.next = io.id_op1 < io.id_op2

    @always_comb
    def _pc_select():
        """
        Set the control signal for the next PC multiplexer.

        Priority: PC from CSR (exception handler or epc), PC for branch and jump instructions, PC for jump
        register instructions, and PC + 4.
        """
        io.pc_select.next = (modbv(Consts.PC_EXC)[Consts.SZ_PC_SEL:] if io.csr_exception or io.csr_eret else
                                  (modbv(Consts.PC_BRJMP)[Consts.SZ_PC_SEL:] if ((id_br_type == Consts.BR_J) or
                                                                                 (id_br_type == Consts.BR_NE and not id_eq) or
                                                                                 (id_br_type == Consts.BR_EQ and id_eq) or
                                                                                 (id_br_type == Consts.BR_LT and id_lt) or
                                                                                 (id_br_type == Consts.BR_LTU and id_ltu) or
                                                                                 (id_br_type == Consts.BR_GE and not id_lt) or
                                                                                 (id_br_type == Consts.BR_GEU and not id_ltu)) else
                                   (modbv(Consts.PC_JALR)[Consts.SZ_PC_SEL:] if id_br_type == Consts.BR_JR else
                                    (modbv(Consts.PC_4)[Consts.SZ_PC_SEL:]))))

    @always_comb
    def _fwd_ctrl():
        """
        Set forwarding controls.

        Rules: the read address is not r0, the read address must match the write address, and the instruction must write to the RF (we == 1).
        Priority: EX > MEM > WB
        """
        io.id_fwd1_select.next = (modbv(Consts.FWD_EX)[Consts.SZ_FWD:] if io.id_rs1_addr != 0 and io.id_rs1_addr == io.ex_wb_addr and io.ex_wb_we else
                                       (modbv(Consts.FWD_MEM)[Consts.SZ_FWD:] if io.id_rs1_addr != 0 and io.id_rs1_addr == io.mem_wb_addr and io.mem_wb_we else
                                        (modbv(Consts.FWD_WB)[Consts.SZ_FWD:] if io.id_rs1_addr != 0 and io.id_rs1_addr == io.wb_wb_addr and io.wb_wb_we else
                                         modbv(Consts.FWD_N)[Consts.SZ_FWD:])))
        io.id_fwd2_select.next = (modbv(Consts.FWD_EX)[Consts.SZ_FWD:] if io.id_rs2_addr != 0 and io.id_rs2_addr == io.ex_wb_addr and io.ex_wb_we else
                                       (modbv(Consts.FWD_MEM)[Consts.SZ_FWD:] if io.id_rs2_addr != 0 and io.id_rs2_addr == io.mem_wb_addr and io.mem_wb_we else
                                        (modbv(Consts.FWD_WB)[Consts.SZ_FWD:] if io.id_rs2_addr != 0 and io.id_rs2_addr == io.wb_wb_addr and io.wb_wb_we else
                                         (modbv(Consts.FWD_N)[Consts.SZ_FWD:]))))

    @always_comb
    def _ctrl_pipeline():
        """
        Set control signals for pipeline registers.
        """
        imem_stall            = io.imem_pipeline.valid and not imem_m.ack_i and not io.csr_exception
        dmem_stall            = io.dmem_pipeline.valid and not dmem_m.ack_i and not io.csr_exception
        io.if_kill.next       = io.pc_select != Consts.PC_4
        io.id_stall.next      = (((io.id_fwd1_select == Consts.FWD_EX or io.id_fwd2_select == Consts.FWD_EX) and
                                  ((ex_mem_funct == Consts.M_RD and ex_mem_valid) or ex_csr_cmd != CSRCMD.CSR_IDLE)) or
                                 (id_fence_i and (ex_mem_funct == Consts.M_WR or mem_mem_funct == Consts.M_WR or wb_mem_funct == Consts.M_WR)))
        io.id_kill.next       = False
        io.full_stall.next    = imem_stall or dmem_stall or io.ex_req_stall
        io.pipeline_kill.next = io.csr_exception or io.csr_eret

    @always_comb
    def _exc_detect():
        """
        Connect the internal exception registers to the CSR exception ports.
        """
        io.csr_exception.next      = mem_exception
        io.csr_exception_code.next = mem_exception_code

    @always_comb
    def _imem_assignment():
        """
        Connect the pipeline imem_m port to the control imem_m port.
        """
        imem_m.addr_o.next          = io.imem_pipeline.addr
        imem_m.dat_o.next           = io.imem_pipeline.wdata
        imem_m.sel_o.next           = 0b0000  # always read
        io.imem_pipeline.rdata.next = imem_m.dat_i

    @always_comb
    def _dmem_assignment():
        """
        Connect the pipeline dmem_m port to the control dmem_m port.
        """
        dmem_m.addr_o.next = io.dmem_pipeline.addr

    @always_comb
    def _dmem_read_data():
        """
        Data convertion from dmem_m to pipeline.

        Generate the correct data type:
        - Signed byte.
        - Unsigned byte.
        - Signed half-word
        - Unsigned half-word
        - Word
        """
        if io.dmem_pipeline.typ[2:0] == Consts.MT_B:
            if io.dmem_pipeline.addr[2:0] == 0:
                io.dmem_pipeline.rdata.next = dmem_m.dat_i[8:0].signed() if not io.dmem_pipeline.typ[2] else dmem_m.dat_i[8:0]
            elif io.dmem_pipeline.addr[2:0] == 1:
                io.dmem_pipeline.rdata.next = dmem_m.dat_i[16:8].signed() if not io.dmem_pipeline.typ[2] else dmem_m.dat_i[16:8]
            elif io.dmem_pipeline.addr[2:0] == 2:
                io.dmem_pipeline.rdata.next = dmem_m.dat_i[24:16].signed() if not io.dmem_pipeline.typ[2] else dmem_m.dat_i[24:16]
            else:
                io.dmem_pipeline.rdata.next = dmem_m.dat_i[32:24].signed() if not io.dmem_pipeline.typ[2] else dmem_m.dat_i[32:24]
        elif io.dmem_pipeline.typ[2:0] == Consts.MT_H:
            if not io.dmem_pipeline.addr[1]:
                io.dmem_pipeline.rdata.next = dmem_m.dat_i[16:0].signed() if not io.dmem_pipeline.typ[2] else dmem_m.dat_i[16:0]
            else:
                io.dmem_pipeline.rdata.next = dmem_m.dat_i[32:16].signed() if not io.dmem_pipeline.typ[2] else dmem_m.dat_i[32:16]
        else:
            io.dmem_pipeline.rdata.next = dmem_m.dat_i

    @always_comb
    def _dmem_write_data():
        """
        Data convertion from pipeline to dmem_m.

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
        if io.dmem_pipeline.fcn == Consts.M_WR:
            dmem_m.sel_o.next = (concat(io.dmem_pipeline.addr[2:0] == 3,
                                        io.dmem_pipeline.addr[2:0] == 2,
                                        io.dmem_pipeline.addr[2:0] == 1,
                                        io.dmem_pipeline.addr[2:0] == 0) if io.dmem_pipeline.typ[2:0] == Consts.MT_B else
                                 (concat(io.dmem_pipeline.addr[2:0] == 2,
                                         io.dmem_pipeline.addr[2:0] == 2,
                                         io.dmem_pipeline.addr[2:0] == 0,
                                         io.dmem_pipeline.addr[2:0] == 0) if io.dmem_pipeline.typ[2:0] == Consts.MT_H else
                                 modbv(0b1111)[4:]))
        else:
            dmem_m.sel_o.next = 0b0000

        # Data to memory
        dmem_m.dat_o.next = (concat(io.dmem_pipeline.wdata[8:0],
                                    io.dmem_pipeline.wdata[8:0],
                                    io.dmem_pipeline.wdata[8:0],
                                    io.dmem_pipeline.wdata[8:0]) if io.dmem_pipeline.typ[2:0] == Consts.MT_B else
                             (concat(io.dmem_pipeline.wdata[16:0],
                                     io.dmem_pipeline.wdata[16:0]) if io.dmem_pipeline.typ[2:0] == Consts.MT_H else
                              (io.dmem_pipeline.wdata)))

    im_flagread  = Signal(False)
    im_flagwrite = Signal(False)
    im_flagrmw   = Signal(False)
    imem_wbm     = WishboneMasterGenerator(clk, rst, imem_m, im_flagread, im_flagwrite, im_flagrmw).gen_wbm()  # NOQA for unused variable
    dm_flagread  = Signal(False)
    dm_flagwrite = Signal(False)
    dm_flagrmw   = Signal(False)
    dmem_wbm     = WishboneMasterGenerator(clk, rst, dmem_m, dm_flagread, dm_flagwrite, dm_flagrmw).gen_wbm()  # NOQA for unused variable

    @always_comb
    def iwbm_trigger():
        im_flagread.next  = not io.imem_pipeline.fcn and io.imem_pipeline.valid and not imem_m.ack_i and not io.csr_exception
        im_flagwrite.next = io.imem_pipeline.fcn and io.imem_pipeline.valid and not imem_m.ack_i and not io.csr_exception
        im_flagrmw.next   = False

    @always_comb
    def dwbm_trigger():
        dm_flagread.next  = not io.dmem_pipeline.fcn and io.dmem_pipeline.valid and not dmem_m.ack_i and not io.csr_exception
        dm_flagwrite.next = io.dmem_pipeline.fcn and io.dmem_pipeline.valid and not dmem_m.ack_i and not io.csr_exception
        dm_flagrmw.next   = False

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
