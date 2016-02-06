#!/usr/bin/env python
# Copyright (c) 2015 Angel Terrones (<angelterrones@gmail.com>)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# inp the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included inp
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
from myhdl import modbv
from myhdl import always_comb
from myhdl import always
from myhdl import instances
from myhdl import concat
from Core.consts import Consts


class CSRAddressMap:
    """
    Address map for:
    - User level
    - Supervisor level (subset)
    - Machine level (subset)
    """
    SZ_ADDR            = 12
    CSR_ADDR_CYCLE     = 0xC00
    CSR_ADDR_TIME      = 0xC01
    CSR_ADDR_INSTRET   = 0xC02
    CSR_ADDR_CYCLEH    = 0xC80
    CSR_ADDR_TIMEH     = 0xC81
    CSR_ADDR_INSTRETH  = 0xC82
    CSR_ADDR_MCPUID    = 0xF00
    CSR_ADDR_MIMPID    = 0xF01
    CSR_ADDR_MHARTID   = 0xF10
    CSR_ADDR_MSTATUS   = 0x300
    CSR_ADDR_MTVEC     = 0x301
    CSR_ADDR_MTDELEG   = 0x302
    CSR_ADDR_MIE       = 0x304
    CSR_ADDR_MTIMECMP  = 0x321
    CSR_ADDR_MTIME     = 0x701
    CSR_ADDR_MTIMEH    = 0x741
    CSR_ADDR_MSCRATCH  = 0x340
    CSR_ADDR_MEPC      = 0x341
    CSR_ADDR_MCAUSE    = 0x342
    CSR_ADDR_MBADADDR  = 0x343
    CSR_ADDR_MIP       = 0x344
    CSR_ADDR_CYCLEW    = 0x900
    CSR_ADDR_TIMEW     = 0x901
    CSR_ADDR_INSTRETW  = 0x902
    CSR_ADDR_CYCLEHW   = 0x980
    CSR_ADDR_TIMEHW    = 0x981
    CSR_ADDR_INSTRETHW = 0x982
    CSR_ADDR_TO_HOST   = 0x780
    CSR_ADDR_FROM_HOST = 0x781


class CSRExceptionCode:
    SZ_ECODE               = 4
    # Exception codes
    E_INST_ADDR_MISALIGNED = 0
    E_INST_ACCESS_FAULT    = 1
    E_ILLEGAL_INST         = 2
    E_BREAKPOINT           = 3
    E_LOAD_ADDR_MISALIGNED = 4
    E_LOAD_ACCESS_FAULT    = 5
    E_AMO_ADDR_MISALIGNED  = 6
    E_AMO_ACCESS_FAULT     = 7
    E_ECALL_FROM_U         = 8
    E_ECALL_FROM_S         = 9
    E_ECALL_FROM_H         = 10
    E_ECALL_FROM_M         = 11
    # Interrupt codes
    I_SOFTWARE             = 0
    I_TIMER                = 1


class CSRCommand:
    SZ_CMD    = 3
    CSR_IDLE  = modbv(0)[SZ_CMD:]
    CSR_READ  = modbv(4)[SZ_CMD:]
    CSR_WRITE = modbv(5)[SZ_CMD:]
    CSR_SET   = modbv(6)[SZ_CMD:]
    CSR_CLEAR = modbv(7)[SZ_CMD:]


class CSRModes:
    SZ_MODE = 2
    PRV_U   = 0
    PRV_S   = 1
    PRV_H   = 2
    PRV_M   = 3


class CSRFileRWIO:
    def __init__(self):
        self.addr  = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])  # I: Register address
        self.cmd   = Signal(modbv(0)[CSRCommand.SZ_CMD:])      # I: command
        self.wdata = Signal(modbv(0)[32:])  # I: input data
        self.rdata = Signal(modbv(0)[32:])  # O: output data


class CSRExceptionIO:
    def __init__(self):
        self.interrupt           = Signal(False)  # O
        self.interrupt_code      = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])  # O
        self.exception           = Signal(False)          # I: from Control Unit.
        self.exception_code      = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])   # I: from Control Unit.
        self.eret                = Signal(False)          # I: the current instruction (@MEM) is ERET.
        self.exception_load_addr = Signal(modbv(0)[32:])  # I: Load address caused an exception.
        self.exception_pc        = Signal(modbv(0)[32:])  # I
        self.exception_handler   = Signal(modbv(0)[32:])  # O: Trap PC
        self.epc                 = Signal(modbv(0)[32:])  # O: Return address


class CSR:
    def __init__(self,
                 clk:            Signal(False),
                 rst:            Signal(False),
                 rw:             CSRFileRWIO(),
                 exc_io:         CSRExceptionIO(),
                 retire:         Signal(False),
                 prv:            Signal(modbv(0)[CSRModes.SZ_MODE:]),
                 illegal_access: Signal(False)):
        self.clk            = clk
        self.rst            = rst
        self.rw             = rw
        self.exc_io         = exc_io
        self.retire         = retire
        self.prv            = prv
        self.illegal_access = illegal_access

    def GetRTL(self):
        # registers
        cycle_full      = Signal(modbv(0)[64:])
        cycle           = Signal(modbv(0)[32:])
        cycleh          = Signal(modbv(0)[32:])

        time_full       = Signal(modbv(0)[64:])
        time            = Signal(modbv(0)[32:])
        timeh           = Signal(modbv(0)[32:])

        instret_full    = Signal(modbv(0)[64:])
        instret         = Signal(modbv(0)[32:])
        instreth        = Signal(modbv(0)[32:])

        mcpuid          = Signal(modbv(0)[32:])
        mimpid          = Signal(modbv(0)[32:])
        mhartid         = Signal(modbv(0)[32:])
        mstatus         = Signal(modbv(0)[32:])
        mtvec           = Signal(modbv(0)[32:])
        mtdeleg         = Signal(modbv(0)[32:])
        mie             = Signal(modbv(0)[32:])
        mtimecmp        = Signal(modbv(0)[32:])

        mtime_full      = Signal(modbv(0)[64:])
        mtime           = Signal(modbv(0)[32:])
        mtimeh          = Signal(modbv(0)[32:])

        mscratch        = Signal(modbv(0)[32:])
        mepc            = Signal(modbv(0)[32:])
        mcause          = Signal(modbv(0)[32:])
        mbadaddr        = Signal(modbv(0)[32:])
        mip             = Signal(modbv(0)[32:])

        mtohost         = Signal(modbv(0)[32:])
        mfromhost       = Signal(modbv(0)[32:])

        # aux
        wdata_aux       = Signal(modbv(0)[32:])
        priv_stack      = Signal(modbv(0)[6:])
        mtie            = Signal(False)
        msie            = Signal(False)
        mtip            = Signal(False)
        msip            = Signal(False)
        mecode          = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
        mint            = Signal(False)
        ie              = Signal(False)
        mtimer_expired  = Signal(False)
        system_en       = Signal(False)
        system_wen      = Signal(False)
        wen_internal    = Signal(False)
        illegal_region  = Signal(False)
        defined         = Signal(False)
        uinterrupt      = Signal(False)
        minterrupt      = Signal(False)
        interrupt_taken = Signal(False)
        interrupt_code  = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])
        code_imem       = Signal(False)

        @always_comb
        def assigments():
            cycle.next                         = cycle_full[32:0]
            cycleh.next                        = cycle_full[64:32]
            time.next                          = time_full[32:0]
            timeh.next                         = time_full[64:32]
            instret.next                       = instret_full[32:0]
            instreth.next                      = instret_full[64:32]
            mtime.next                         = mtime_full[32:0]
            mtimeh.next                        = mtime_full[64:32]

            self.exc_io.interrupt.next         = mint
            self.exc_io.interrupt_code.next    = mecode
            self.exc_io.exception_handler.next = mtvec + (self.prv << 6)
            self.illegal_access.next           = illegal_region | (system_en & (not defined))
            self.exc_io.epc.next               = mepc
            ie.next                            = priv_stack[0]
            wen_internal.next                  = system_wen
            uinterrupt.next                    = 0
            minterrupt.next                    = mtie & mtimer_expired
            mcpuid.next                        = (1 << 20) | (1 << 8)  # RV32I, support for U mode
            mimpid.next                        = 0x8000
            mhartid.next                       = 0
            mstatus.next                       = concat(modbv(0)[26:], priv_stack)
            mtdeleg.next                       = 0
            mip.next                           = concat(mtip, modbv(0)[3:], msip, modbv(0)[3:])
            mie.next                           = concat(mtie, modbv(0)[3:], msie, modbv(0)[3:])
            mcause.next                        = concat(mint, modbv(0)[27:], mecode)
            code_imem.next                     = (self.exc_io.exception_code == CSRExceptionCode.E_INST_ADDR_MISALIGNED |
                                                  self.exc_io.exception_code == CSRExceptionCode.E_INST_ACCESS_FAULT)

        @always_comb
        def assigments2():
            self.prv.next                      = priv_stack[3:1]
            mtimer_expired.next                = mtimecmp == mtime
            system_en.next                     = self.rw.cmd[3]
            system_wen.next                    = self.rw.cmd[0] | self.rw.cmd[1]

        @always_comb
        def assigments3():
            illegal_region.next                = ((system_wen & (self.rw.addr[12:10] == 0b11)) |
                                                  (system_en & (self.rw.addr[11:8] > self.prv)))

        @always_comb
        def _wdata_aux():
            if system_wen:
                if self.rw.cmd == CSRCommand.CSR_SET:
                    wdata_aux.next = self.rw.rdata | self.rw.wdata
                elif self.rw.cmd == CSRCommand.CSR_CLEAR:
                    wdata_aux.next = self.rw.rdata & ~self.rw.wdata
                else:
                    wdata_aux.next = self.rw.wdata

        @always_comb
        def _interrupt_code():
            interrupt_code.next = CSRExceptionCode.I_TIMER
            if self.prv == CSRModes.PRV_U:
                interrupt_taken.next = (ie & uinterrupt) | minterrupt
            elif self.prv == CSRModes.PRV_M:
                interrupt_taken.next = ie & minterrupt
            else:
                interrupt_taken.next = 1

        @always(self.clk.posedge)
        def _priv_stack():
            if self.rst:
                priv_stack.next = 0b000110
            elif wen_internal & (self.rw.addr == CSRAddressMap.CSR_ADDR_MSTATUS):
                priv_stack.next = wdata_aux[6:0]
            elif self.exc_io.exception:
                # All exceptions to machine mode
                priv_stack.next = concat(priv_stack[3:0], modbv(0b11)[2:], False)
            elif self.exc_io.eret:
                priv_stack.next = concat(modbv(0)[2:], True, priv_stack[6:3])

        @always(self.clk.posedge)
        def _mtip_msip():
            if self.rst:
                mtip.next = 0
                msip.next = 0
            else:
                if mtimer_expired:
                    mtip.next = 1
                elif wen_internal & (self.rw.addr == CSRAddressMap.CSR_ADDR_MTIMECMP):
                    mtip.next = 0
                elif wen_internal & (self.rw.addr == CSRAddressMap.CSR_ADDR_MIP):
                    mtip.next = wdata_aux[7]
                    msip.next = wdata_aux[3]

        @always(self.clk.posedge)
        def _mtie_msie():
            if self.rst:
                mtie.next = 0
                msie.next = 0
            elif wen_internal & (self.rw.addr == CSRAddressMap.CSR_ADDR_MIE):
                mtie.next = wdata_aux[7]
                msie.next = wdata_aux[3]

        @always(self.clk.posedge)
        def _mepc():
            if self.exc_io.exception | interrupt_taken:
                mepc.next = self.exc_io.exception_pc & ~0x03
            elif wen_internal & (self.rw.addr == CSRAddressMap.CSR_ADDR_MEPC):
                mepc.next = wdata_aux & ~0x03

        @always(self.clk.posedge)
        def _mecode_mint():
            if self.rst:
                mecode.next = 0
                mint.next = 0
            elif wen_internal & (self.rw.addr == CSRAddressMap.CSR_ADDR_MCAUSE):
                mecode.next = wdata_aux[4:0]
                mint.next = wdata_aux[31]
            elif interrupt_taken:
                mecode.next = interrupt_code
                mint.next = 1
            elif self.exc_io.exception:
                mecode.next = self.exc_io.exception_code
                mint.next = 0

        @always(self.clk.posedge)
        def _mbadaddr():
            if self.exc_io.exception:
                mbadaddr.next = self.exc_io.exception_pc if code_imem else self.exc_io.exception_load_addr
            elif wen_internal & (self.rw.addr == CSRAddressMap.CSR_ADDR_MBADADDR):
                mbadaddr.next = wdata_aux

        @always_comb
        def _read():
            addr = self.rw.addr
            if addr == CSRAddressMap.CSR_ADDR_CYCLE:
                self.rw.rdata.next = cycle
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_TIME:
                self.rw.rdata.next = time
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_INSTRET:
                self.rw.rdata.next = instret
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_CYCLEH:
                self.rw.rdata.next = cycleh
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_TIMEH:
                self.rw.rdata.next = timeh
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_INSTRETH:
                self.rw.rdata.next = instreth
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MCPUID:
                self.rw.rdata.next = mcpuid
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MIMPID:
                self.rw.rdata.next = mimpid
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MHARTID:
                self.rw.rdata.next = mhartid
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MSTATUS:
                self.rw.rdata.next = mstatus
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MTVEC:
                self.rw.rdata.next = mtvec
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MTDELEG:
                self.rw.rdata.next = mtdeleg
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MIE:
                self.rw.rdata.next = mie
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MTIMECMP:
                self.rw.rdata.next = mtimecmp
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MTIME:
                self.rw.rdata.next = mtime
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MTIMEH:
                self.rw.rdata.next = mtimeh
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MSCRATCH:
                self.rw.rdata.next = mscratch
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MEPC:
                self.rw.rdata.next = mepc
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MCAUSE:
                self.rw.rdata.next = mcause
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MBADADDR:
                self.rw.rdata.next = mbadaddr
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_MIP:
                self.rw.rdata.next = cycle
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_CYCLEW:
                self.rw.rdata.next = cycle
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_TIMEW:
                self.rw.rdata.next = time
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_INSTRETW:
                self.rw.rdata.next = instret
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_CYCLEHW:
                self.rw.rdata.next = cycleh
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_TIMEHW:
                self.rw.rdata.next = timeh
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_INSTRETHW:
                self.rw.rdata.next = instreth
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_TO_HOST:
                self.rw.rdata.next = mtohost
                defined.next = 1
            elif addr == CSRAddressMap.CSR_ADDR_FROM_HOST:
                self.rw.rdata.next = mfromhost
                defined.next = 1
            else:
                self.rw.rdata.next = 0
                defined.next = 0

        @always(self.clk.posedge)
        def _write():
            addr = self.rw.addr
            if self.rst:
                cycle_full.next   = 0
                time_full.next    = 0
                instret_full.next = 0
                mtime_full.next   = 0
                mtvec.next        = Consts.MTVEC
                mtohost.next      = 0
                mfromhost.next    = 0
            else:
                cycle_full.next = cycle_full + 1
                time_full.next  = time_full + 1
                mtime_full.next = mtime_full + 1
                if self.retire:
                    instret_full.next = instret_full + 1
                if wen_internal:
                    if addr == CSRAddressMap.CSR_ADDR_CYCLE:
                        cycle_full[32:0] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_TIME:
                        time_full[32:0] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_INSTRET:
                        instret_full[32:0] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_CYCLEH:
                        cycle_full[64:32] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_TIMEH:
                        time_full[64:32] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_INSTRETH:
                        instret_full[64:32] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_MTVEC:
                        mtvec.next = wdata_aux & ~0x03
                    elif addr == CSRAddressMap.CSR_ADDR_MTIMECMP:
                        mtimecmp.next = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_MTIME:
                        mtime_full[32:0].next = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_MTIMEH:
                        mtime_full[64:32].next = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_MSCRATCH:
                        mscratch.next = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_CYCLEW:
                        cycle_full[32:0] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_TIMEW:
                        time_full[32:0] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_INSTRETW:
                        instret_full[32:0] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_CYCLEHW:
                        cycle_full[64:32] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_TIMEHW:
                        time_full[64:32] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_INSTRETHW:
                        instret_full[64:32] = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_TO_HOST:
                        mtohost.next = wdata_aux
                    elif addr == CSRAddressMap.CSR_ADDR_FROM_HOST:
                        mfromhost.next = wdata_aux

        return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 140
# flycheck-flake8rc: ".flake8rc"
# End:
