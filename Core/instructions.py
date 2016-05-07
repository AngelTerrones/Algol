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


class Opcodes:
    """
    List all the RV32I opcodes
    """
    RV32_NOP    = 0b0010011
    RV32_LUI    = 0b0110111
    RV32_AUIPC  = 0b0010111
    RV32_JAL    = 0b1101111
    RV32_JALR   = 0b1100111
    RV32_BRANCH = 0b1100011
    RV32_LOAD   = 0b0000011
    RV32_STORE  = 0b0100011
    RV32_IMM    = 0b0010011
    RV32_OP     = 0b0110011
    RV32_FENCE  = 0b0001111
    RV32_SYSTEM = 0b1110011


class BranchFunct3:
    RV32_F3_BEQ  = 0
    RV32_F3_BNE  = 1
    RV32_F3_BLT  = 4
    RV32_F3_BGE  = 5
    RV32_F3_BLTU = 6
    RV32_F3_BGEU = 7


class LoadFunct3:
    RV32_F3_LB  = 0
    RV32_F3_LH  = 1
    RV32_F3_LW  = 2
    RV32_F3_LBU = 4
    RV32_F3_LHU = 5


class StoreFunct3:
    RV32_F3_SB = 0
    RV32_F3_SH = 1
    RV32_F3_SW = 2


class ArithmeticFunct3:
    RV32_F3_ADD_SUB = 0
    RV32_F3_SLL     = 1
    RV32_F3_SLT     = 2
    RV32_F3_SLTU    = 3
    RV32_F3_XOR     = 4
    RV32_F3_SRL_SRA = 5
    RV32_F3_OR      = 6
    RV32_F3_AND     = 7


class FenceFunct3:
    RV32_F3_FENCE   = 0
    RV32_F3_FENCE_I = 1


class SystemFunct3:
    RV32_F3_PRIV   = 0
    RV32_F3_CSRRW  = 1
    RV32_F3_CSRRS  = 2
    RV32_F3_CSRRC  = 3
    RV32_F3_CSRRWI = 5
    RV32_F3_CSRRSI = 6
    RV32_F3_CSRRCI = 7


class PrivFunct12:
    RV32_F12_ECALL  = 0b000000000000
    RV32_F12_EBREAK = 0b000000000001
    RV32_F12_ERET   = 0b000100000000


class MulDivFunct:
    RV32_F7_MUL_DIV = 0b0000001
    RV32_F3_MUL     = 0
    RV32_F3_MULH    = 1
    RV32_F3_MULHSU  = 2
    RV32_F3_MULHU   = 3
    RV32_F3_DIV     = 4
    RV32_F3_DIVU    = 5
    RV32_F3_REM     = 6
    RV32_F3_REMU    = 7

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
