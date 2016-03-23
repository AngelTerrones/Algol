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
    """
    Exception codes.
    (Priviledge mode v1.7)
    """
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


class CSRCMD:
    """
    CSR commands.

    The CSR_READ command is for those cases when the 'rs1' field is zero.
    """
    SZ_CMD     = 3
    CSR_IDLE   = 0
    CSR_READ   = 4
    CSR_WRITE  = 5
    CSR_SET    = 6
    CSR_CLEAR  = 7
    _CSR_IDLE  = modbv(0)[SZ_CMD:]
    _CSR_READ  = modbv(4)[SZ_CMD:]
    _CSR_WRITE = modbv(5)[SZ_CMD:]
    _CSR_SET   = modbv(6)[SZ_CMD:]
    _CSR_CLEAR = modbv(7)[SZ_CMD:]


class CSRModes:
    """
    Priviledge modes.
    """
    SZ_MODE = 2
    PRV_U   = 0
    PRV_S   = 1
    PRV_H   = 2
    PRV_M   = 3


class CSRFileRWIO:
    """
    Defines the CSR IO port for RW operations.

    :ivar addr:  Register address
    :ivar cmd:   CSR command
    :ivar wdata: Write data (input)
    :ivar rdata: Read data (output)
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.addr  = Signal(modbv(0)[CSRAddressMap.SZ_ADDR:])  # I: Register address
        self.cmd   = Signal(modbv(0)[CSRCMD.SZ_CMD:])      # I: command
        self.wdata = Signal(modbv(0)[32:])                     # I: input data
        self.rdata = Signal(modbv(0)[32:])                     # O: output data


class CSRExceptionIO:
    """
    Defines the CSR IO port for exception signals.

    :ivar interrupt:           Interrupt flag
    :ivar interrupt_code:      Type of interrupt
    :ivar exception:           Exception flag, from the CU
    :ivar exception_code:      Type of exception, from the CU
    :ivar eret:                Execute an ERET instruction
    :ivar exception_load_addr: Memory address for LD/ST instruction
    :ivar exception_pc:        The PC for the faulty instruction
    :ivar exception_handler:   Next PC for exceptions
    :ivar epc:                 Next PC after executing sucesfully an ERET instruction
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.interrupt           = Signal(False)                                 # O
        self.interrupt_code      = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])  # O
        self.exception           = Signal(False)                                 # I: from Control Unit.
        self.exception_code      = Signal(modbv(0)[CSRExceptionCode.SZ_ECODE:])  # I: from Control Unit.
        self.eret                = Signal(False)                                 # I: the current instruction (@MEM) is ERET.
        self.exception_load_addr = Signal(modbv(0)[32:])                         # I: Load address caused an exception.
        self.exception_pc        = Signal(modbv(0)[32:])                         # I
        self.exception_handler   = Signal(modbv(0)[32:])                         # O: Trap PC
        self.epc                 = Signal(modbv(0)[32:])                         # O: Return address


def CSR(clk,
        rst,
        rw,
        exc_io,
        retire,
        prv,
        illegal_access,
        toHost):
    """
    The Control and Status Registers (CSR)

    :param clk:            System clock
    :param rst:            System reset
    :param rw:             IO bundle for RW operations
    :param exc_io:         IO bundle for exception related operations
    :param retire:         Increment the counter for executed instructions
    :param prv:            Current priviledge mode (valid at MEM stage)
    :param illegal_access: The RW operation is invalid
    :param toHost:         Connected to the CSR's mtohost register. For simulation purposes.
    This module is necessary for exception handling.
    """
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

    # Connect this register to the IO for simulation purposes.
    # TODO: Remove this and use a debug interface.
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
        """
        Some assignments.
        """
        toHost.next                    = mtohost
        cycle.next                     = cycle_full[32:0]
        cycleh.next                    = cycle_full[64:32]
        time.next                      = time_full[32:0]
        timeh.next                     = time_full[64:32]
        instret.next                   = instret_full[32:0]
        instreth.next                  = instret_full[64:32]
        mtime.next                     = mtime_full[32:0]
        mtimeh.next                    = mtime_full[64:32]
        exc_io.interrupt.next          = mint
        exc_io.interrupt_code.next     = mecode
        exc_io.exception_handler.next  = mtvec + (prv << 6)
        illegal_access.next            = illegal_region or (system_en and (not defined))
        exc_io.epc.next                = mepc
        ie.next                        = priv_stack[0]
        wen_internal.next              = system_wen
        uinterrupt.next                = 0
        minterrupt.next                = mtie & mtimer_expired
        mcpuid.next                    = (1 << 20) | (1 << 8)  # RV32I, support for U mode
        mimpid.next                    = 0x8000
        mhartid.next                   = 0
        mstatus.next                   = concat(modbv(0)[26:], priv_stack)
        mtdeleg.next                   = 0
        mip.next                       = concat(mtip, modbv(0)[3:], msip, modbv(0)[3:])
        mie.next                       = concat(mtie, modbv(0)[3:], msie, modbv(0)[3:])
        mcause.next                    = concat(mint, modbv(0)[27:], mecode)
        code_imem.next                 = ((exc_io.exception_code == CSRExceptionCode.E_INST_ADDR_MISALIGNED) |
                                          (exc_io.exception_code == CSRExceptionCode.E_INST_ACCESS_FAULT))

    @always_comb
    def assigments2():
        """
        Continue the assignments.

        Avoid warnings from MyHDL about signals being translated as inout.
        """
        prv.next            = priv_stack[3:1]
        mtimer_expired.next = mtimecmp == mtime
        system_en.next      = rw.cmd[2]
        system_wen.next     = rw.cmd[0] | rw.cmd[1]

    @always_comb
    def assigments3():
        """
        Continue the assignments.

        Avoid warnings from MyHDL about signals being translated as inout.
        """
        illegal_region.next = ((system_wen & (rw.addr[12:10] == 0b11)) |  # Read only region
                               (system_en & (rw.addr[10:8] > prv)))  # Check priviledge level

    @always_comb
    def _wdata_aux():
        """
        Select the write data according to the command.
        """
        if system_wen:
            if rw.cmd == CSRCMD.CSR_SET:
                wdata_aux.next = rw.rdata | rw.wdata
            elif rw.cmd == CSRCMD.CSR_CLEAR:
                wdata_aux.next = rw.rdata & ~rw.wdata
            else:
                wdata_aux.next = rw.wdata
        else:
            wdata_aux.next = 0x0BADF00D

    @always_comb
    def _interrupt_code():
        """
        Set the interrupt code and flag.
        """
        interrupt_code.next = CSRExceptionCode.I_TIMER
        if prv == CSRModes.PRV_U:
            interrupt_taken.next = (ie & uinterrupt) | minterrupt
        elif prv == CSRModes.PRV_M:
            interrupt_taken.next = ie & minterrupt
        else:
            interrupt_taken.next = 1

    @always(clk.posedge)
    def _priv_stack():
        """
        The priviledge mode stack.

        - At reset: machine mode.
        - Exception: shift stack to the left, enter machine mode.
        - Eret: shift stack to the right. Set next mode to User leve.
        """
        if rst:
            priv_stack.next = 0b000110
        elif wen_internal & (rw.addr == CSRAddressMap.CSR_ADDR_MSTATUS):
            priv_stack.next = wdata_aux[6:0]
        elif exc_io.exception:
            # All exceptions to machine mode
            priv_stack.next = concat(priv_stack[3:0], modbv(0b11)[2:], False)
        elif exc_io.eret:
            priv_stack.next = concat(modbv(0)[2:], True, priv_stack[6:3])

    @always(clk.posedge)
    def _mtip_msip():
        """
        Handle the flags for interrupt pending.
        """
        if rst:
            mtip.next = 0
            msip.next = 0
        else:
            if mtimer_expired:
                mtip.next = 1
            elif wen_internal & (rw.addr == CSRAddressMap.CSR_ADDR_MTIMECMP):
                mtip.next = 0
            elif wen_internal & (rw.addr == CSRAddressMap.CSR_ADDR_MIP):
                mtip.next = wdata_aux[7]
                msip.next = wdata_aux[3]

    @always(clk.posedge)
    def _mtie_msie():
        """
        Handle the interrupt enable flags.
        """
        if rst:
            mtie.next = 0
            msie.next = 0
        elif wen_internal & (rw.addr == CSRAddressMap.CSR_ADDR_MIE):
            mtie.next = wdata_aux[7]
            msie.next = wdata_aux[3]

    @always(clk.posedge)
    def _mepc():
        """
        Handle writes to the mepc register.
        """
        if exc_io.exception | interrupt_taken:
            mepc.next = exc_io.exception_pc & ~0x03
        elif wen_internal & (rw.addr == CSRAddressMap.CSR_ADDR_MEPC):
            mepc.next = wdata_aux & ~0x03

    @always(clk.posedge)
    def _mecode_mint():
        """
        Handle writes to the 'mecode' and 'mint' registers.
        """
        if rst:
            mecode.next = 0
            mint.next = 0
        elif wen_internal & (rw.addr == CSRAddressMap.CSR_ADDR_MCAUSE):
            mecode.next = wdata_aux[4:0]
            mint.next = wdata_aux[31]
        elif interrupt_taken:
            mecode.next = interrupt_code
            mint.next = 1
        elif exc_io.exception:
            mecode.next = exc_io.exception_code
            mint.next = 0

    @always(clk.posedge)
    def _mbadaddr():
        """
        Handle writes to the 'mbadaddr' address.
        """
        if exc_io.exception:
            mbadaddr.next = exc_io.exception_pc if code_imem else exc_io.exception_load_addr
        elif wen_internal & (rw.addr == CSRAddressMap.CSR_ADDR_MBADADDR):
            mbadaddr.next = wdata_aux

    @always_comb
    def _read():
        """
        Read CSR registers.
        """
        if rw.addr == CSRAddressMap.CSR_ADDR_CYCLE:
            rw.rdata.next = cycle
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_TIME:
            rw.rdata.next = time
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRET:
            rw.rdata.next = instret
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_CYCLEH:
            rw.rdata.next = cycleh
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_TIMEH:
            rw.rdata.next = timeh
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRETH:
            rw.rdata.next = instreth
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MCPUID:
            rw.rdata.next = mcpuid
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MIMPID:
            rw.rdata.next = mimpid
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MHARTID:
            rw.rdata.next = mhartid
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MSTATUS:
            rw.rdata.next = mstatus
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MTVEC:
            rw.rdata.next = mtvec
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MTDELEG:
            rw.rdata.next = mtdeleg
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MIE:
            rw.rdata.next = mie
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MTIMECMP:
            rw.rdata.next = mtimecmp
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MTIME:
            rw.rdata.next = mtime
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MTIMEH:
            rw.rdata.next = mtimeh
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MSCRATCH:
            rw.rdata.next = mscratch
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MEPC:
            rw.rdata.next = mepc
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MCAUSE:
            rw.rdata.next = mcause
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MBADADDR:
            rw.rdata.next = mbadaddr
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_MIP:
            rw.rdata.next = mip
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_CYCLEW:
            rw.rdata.next = cycle
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_TIMEW:
            rw.rdata.next = time
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRETW:
            rw.rdata.next = instret
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_CYCLEHW:
            rw.rdata.next = cycleh
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_TIMEHW:
            rw.rdata.next = timeh
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRETHW:
            rw.rdata.next = instreth
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_TO_HOST:
            rw.rdata.next = mtohost
            defined.next = 1
        elif rw.addr == CSRAddressMap.CSR_ADDR_FROM_HOST:
            rw.rdata.next = mfromhost
            defined.next = 1
        else:
            rw.rdata.next = 0
            defined.next = 0

    @always(clk.posedge)
    def _write():
        """
        Handle writes to CSR registers.
        """
        if rst:
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
            if retire:
                instret_full.next = instret_full + 1
            if wen_internal:
                if rw.addr == CSRAddressMap.CSR_ADDR_CYCLE:
                    cycle_full[32:0].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_TIME:
                    time_full[32:0].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRET:
                    instret_full[32:0].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_CYCLEH:
                    cycle_full[64:32].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_TIMEH:
                    time_full[64:32].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRETH:
                    instret_full[64:32].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_MTVEC:
                    mtvec.next = wdata_aux & ~0x03
                elif rw.addr == CSRAddressMap.CSR_ADDR_MTIMECMP:
                    mtimecmp.next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_MTIME:
                    mtime_full[32:0].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_MTIMEH:
                    mtime_full[64:32].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_MSCRATCH:
                    mscratch.next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_CYCLEW:
                    cycle_full[32:0].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_TIMEW:
                    time_full[32:0].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRETW:
                    instret_full[32:0].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_CYCLEHW:
                    cycle_full[64:32].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_TIMEHW:
                    time_full[64:32].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_INSTRETHW:
                    instret_full[64:32].next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_TO_HOST:
                    mtohost.next = wdata_aux
                elif rw.addr == CSRAddressMap.CSR_ADDR_FROM_HOST:
                    mfromhost.next = wdata_aux

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 200
# flycheck-flake8rc: ".flake8rc"
# End:
