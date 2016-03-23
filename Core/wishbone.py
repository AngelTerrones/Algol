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
from myhdl import modbv
from myhdl import enum
from myhdl import concat
from myhdl import always
from myhdl import always_comb
from myhdl import instances


class WishboneIntercon:
    """
    Defines an Wishbone IO interface.

    :ivar addr:   Address
    :ivar data_o: Data output (from master)
    :ivar data_i: Data input (to master)
    :ivar sel:    Select byte to write
    :ivar cti:    Cycle Type Identifier
    :ivar cyc:    Valid bus cycle in progress
    :ivar we:     Write enable
    :ivar stb:    Valid data transfer cycle
    :ivar stall:  Pipeline stall: Slave is not able to accept the transfer in the transaction queue
    :ivar ack:    Normal termination of a bus cycle
    :ivar err:    Abnormal cycle termination
    """
    def __init__(self):
        """
        Initializes the IO ports.
        """
        self.addr  = Signal(modbv(0)[32:])
        self.dat_o = Signal(modbv(0)[32:])
        self.dat_i = Signal(modbv(0)[32:])
        self.sel   = Signal(modbv(0)[4:])
        self.cti   = Signal(modbv(0)[3:])
        self.cyc   = Signal(False)
        self.we    = Signal(False)
        self.stb   = Signal(False)
        self.stall = Signal(False)
        self.ack   = Signal(False)
        self.err   = Signal(False)


class WishboneMaster:
    """
    Defines the wishbone master signals.
    """
    def __init__(self, intercon):
        """
        Initializes the IO ports, using the intercon.

        :param intercon: the intercon bus.
        """
        if not isinstance(intercon, WishboneIntercon):
            raise AttributeError("Unknown intercon type for {0}".format(str(intercon)))

        self.addr_o  = intercon.addr
        self.dat_o   = intercon.dat_o
        self.dat_i   = intercon.dat_i
        self.sel_o   = intercon.sel
        self.cti_o   = intercon.cti
        self.cyc_o   = intercon.cyc
        self.we_o    = intercon.we
        self.stb_o   = intercon.stb
        self.stall_i = intercon.stall
        self.ack_i   = intercon.ack
        self.err_i   = intercon.err


class WishboneSlave:
    """
    Defines the wishbone slave signals
    """
    def __init__(self, intercon):
        """
        Initializes the IO ports using the intercon signals.

        :param intercon: the intercon bus.
        """
        if not isinstance(intercon, WishboneIntercon):
            raise AttributeError("Unknown intercon type for {0}".format(str(intercon)))

        self.addr_i  = intercon.addr
        self.dat_o   = intercon.dat_i
        self.dat_i   = intercon.dat_o
        self.sel_i   = intercon.sel
        self.cti_i   = intercon.cti
        self.cyc_i   = intercon.cyc
        self.we_i    = intercon.we
        self.stb_i   = intercon.stb
        self.stall_o = intercon.stall
        self.ack_o   = intercon.ack
        self.err_o   = intercon.err


class WishboneMasterGenerator():
    """
    Wishbone Master generator.

    This clase generates the state machine for a master device.
    The class requires trigger signals to start a wishbone cycle access.

    Support for classic cycle only.
    """
    def __init__(self, clk_i, rst_i, master_signals, flagread, flagwrite, flagrmw):
        """
        Initializes the class.

        :param clk_i:          Wishbone clock
        :param rst_i:          Wishbone reset
        :param master_signals: Wishbone master signals to drive.
        :param flagread:       Initiates a read cycle.
        :param flagwrite:      Initiates a write cycle.
        :param flagrmw:        Initiates a read-modify-write access.
        """
        if isinstance(master_signals, WishboneMaster):
            self.wbmsig = master_signals
        else:
            raise AttributeError("Argument slave_signals must be of type WishboneSlave. Argument: {0}".format(str(master_signals)))

        self.clk       = clk_i
        self.rst       = rst_i
        self.flagread  = flagread
        self.flagwrite = flagwrite
        self.flagrmw   = flagrmw

    def gen_wbm(self):
        """
        State machine for master.
        Creates the state machine for a master device.
        """
        self.wbm_states_t = enum('WBM_IDLE',
                                 'WBM_INCYCLE',
                                 'WBM_READ_WAIT',
                                 'WBM_WRITE_WAIT',
                                 'WBM_RMW_RD_WAIT',
                                 'WBM_RMW_MID_WAIT',
                                 'WBM_RMW_WR_WAIT')
        self.wbm_state = Signal(self.wbm_states_t.WBM_IDLE)

        trig_vector = Signal(modbv(0)[3:])
        ack_vector  = Signal(modbv(0)[2:])

        @always_comb
        def concat_trig_vector():
            trig_vector.next = concat(self.flagread,
                                      self.flagwrite,
                                      self.flagrmw)

        @always_comb
        def concat_ack_vector():
            ack_vector.next = concat(self.wbmsig.ack_i, self.wbmsig.err_i)

        # state machine
        @always(self.clk.posedge)
        def wbmstate_fsm():
            if self.rst:
                self.wbm_state.next = self.wbm_states_t.WBM_IDLE
            else:
                if self.wbm_state == self.wbm_states_t.WBM_IDLE:
                    # No access to master bus
                    # Check for trigger signals
                    if trig_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                    else:
                        if self.flagread:
                            self.wbm_state.next = self.wbm_states_t.WBM_READ_WAIT
                        elif self.flagwrite:
                            self.wbm_state.next = self.wbm_states_t.WBM_WRITE_WAIT
                        elif self.flagrmw:
                            self.wbm_state.next = self.wbm_states_t.WBM_RMW_RD_WAIT
                elif self.wbm_state == self.wbm_states_t.WBM_INCYCLE:
                    # Current cycle in progress, but inactive.
                    # CYC_O is asserted, and STB_O is deasserted.
                    if trig_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                    else:
                        if self.flagread:
                            self.wbm_state.next = self.wbm_states_t.WBM_READ_WAIT
                        elif self.flagwrite:
                            self.wbm_state.next = self.wbm_states_t.WBM_WRITE_WAIT
                        elif self.flagrmw:
                            self.wbm_state.next = self.wbm_states_t.WBM_RMW_RD_WAIT
                elif self.wbm_state == self.wbm_states_t.WBM_READ_WAIT:
                    # Read operaton in the bus
                    if ack_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_READ_WAIT
                    else:
                        # check for ACK or ERR
                        if not self.wbmsig.err_i:
                            # No error: ACK
                            # Check for end of cycle
                            if trig_vector == 0:
                                self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                            else:
                                self.wbm_state.next = self.wbm_states_t.WBM_INCYCLE
                        else:
                            # Error in cycle
                            self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                elif self.wbm_state == self.wbm_states_t.WBM_WRITE_WAIT:
                    # Write operation in the bus
                    if ack_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_WRITE_WAIT
                    else:
                        # check for ACK or ERR
                        if not self.wbmsig.err_i:
                            # No error: ACK
                            # Check for end of cycle
                            if trig_vector == 0:
                                self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                            else:
                                self.wbm_state.next = self.wbm_states_t.WBM_INCYCLE
                        else:
                            # Error in cycle
                            self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                elif self.wbm_state == self.wbm_states_t.WBM_RMW_RD_WAIT:
                    # Read stage for RMW operation
                    if ack_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_RMW_RD_WAIT
                    else:
                        # check for ACK or ERR
                        if not self.wbmsig.err_i:
                            # No error: ACK
                            self.wbm_state.next = self.wbm_states_t.WBM_RMW_MID_WAIT
                        else:
                            # Error in cycle
                            self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                elif self.wbm_state == self.wbm_states_t.WBM_RMW_MID_WAIT:
                    # middle stage for RMW operation
                    self.wbm_state.next = self.wbm_states_t.WBM_RMW_WR_WAIT
                elif self.wbm_state == self.wbm_states_t.WBM_RMW_WR_WAIT:
                    # Write state for RMW operation
                    if ack_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_RMW_WR_WAIT
                    else:
                        self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                else:
                    self.wbm_state.next = self.wbm_states_t.WBM_IDLE

        @always_comb
        def wbmstate_signals():
            # CYC generation
            if self.wbm_state == self.wbm_states_t.WBM_IDLE:
                self.wbmsig.cyc_o.next = False
            else:
                self.wbmsig.cyc_o.next = True
            # STB generation
            if self.wbm_state == self.wbm_states_t.WBM_IDLE or self.wbm_state == self.wbm_states_t.WBM_INCYCLE or self.wbm_state == self.wbm_states_t.WBM_RMW_MID_WAIT:
                self.wbmsig.stb_o.next = False
            else:
                self.wbmsig.stb_o.next = True
            # WE generation
            if self.wbm_state == self.wbm_states_t.WBM_WRITE_WAIT or self.wbm_state == self.wbm_states_t.WBM_RMW_WR_WAIT:
                self.wbmsig.we_o.next = True
            else:
                self.wbmsig.we_o.next = False

            # CTI generation
            self.wbmsig.cti_o.next = 0

        return instances()


class WishboneSlaveGenerator():
    """
    Wishbone Slave generator.

    This clase generates the state machine for a slave device.
    The class requires trigger signals to responde a wishbone cycle access.

    Support for classic cycle only.
    """
    def __init__(self, clk_i, rst_i, slave_signals, flagbusy, flagerr, flagwait):
        """
        Initializes the class.

        :param clk_i:         Wishbone clock
        :param rst_i:         Wishbone reset
        :param slave_signals: Wishbone slave signals to drive.
        :param flagbusy:      Slave is not able to accept a transfer.
        :param flagerr:       Slave indicates a transaction error.
        :param flagwait:      Slave is working.
        """
        if isinstance(slave_signals, WishboneSlave):
            self.wbssig = slave_signals
        else:
            raise AttributeError("Argument slave_signals must be of type WishboneSlave. Argument: {0}".format(str(slave_signals)))

        self.clk      = clk_i
        self.rst      = rst_i
        self.flagbusy = flagbusy
        self.flagerr  = flagerr
        self.flagwait = flagwait

    def gen_wbs(self):
        """
        State machine for slave.
        Creates the state machine for a slave device.
        """
        self.wbs_states_t = enum('WBS_IDLE',
                                 'WBS_INCYCLE',
                                 'WBS_READ_WAIT',
                                 'WBS_WRITE_WAIT')
        self.wbs_state = Signal(self.wbs_states_t.WBS_IDLE)

        @always(self.clk.posedge)
        def wbsstate_fsm():
            if self.rst:
                self.wbs_state.next = self.wbs_states_t.WBS_IDLE
            else:
                # state transition
                if self.wbs_state == self.wbs_states_t.WBS_IDLE:
                    # Default state: no access
                    # Check CYC for state transition
                    if not self.wbssig.cyc_i:
                        self.wbs_state.next = self.wbs_states_t.WBS_IDLE
                    else:
                        # new cycle
                        # Asserted STB: check operation. Else, wait state (incycle)
                        if not self.wbssig.stb_i:
                            self.wbs_state.next = self.wbs_states_t.WBS_INCYCLE
                        else:
                            if not self.wbssig.we_i:
                                self.wbs_state.next = self.wbs_states_t.WBS_READ_WAIT
                            else:
                                self.wbs_state.next = self.wbs_states_t.WBS_WRITE_WAIT
                elif self.wbs_state == self.wbs_states_t.WBS_INCYCLE:
                    # Current cycle in progress, but inactive.
                    # CYC is asserted, but STB is deasserted.
                    # Change state with STB signal (or exit with CYC deassertion)
                    if not self.wbssig.cyc_i:
                        self.wbs_state.next = self.wbs_states_t.WBS_IDLE
                    else:
                        if not self.wbssig.stb_i:
                            self.wbs_state.next = self.wbs_states_t.WBS_INCYCLE
                        else:
                            if not self.wbssig.we_i:
                                self.wbs_state.next = self.wbs_states_t.WBS_READ_WAIT
                            else:
                                self.wbs_state.next = self.wbs_states_t.WBS_WRITE_WAIT
                elif self.wbs_state == self.wbs_states_t.WBS_READ_WAIT:
                    # Read operation in the bus. Check flag wait.
                    if self.flagwait or self.flagbusy:
                        self.wbs_state.next = self.wbs_states_t.WBS_READ_WAIT
                    elif self.flagerr:
                        self.wbs_state.next = self.wbs_states_t.WBS_IDLE
                    else:
                        if not self.wbssig.cyc_i:
                            self.wbs_state.next = self.wbs_states_t.WBS_IDLE
                        else:
                            if not self.wbssig.stb_i:
                                self.wbs_state.next = self.wbs_states_t.WBS_INCYCLE
                            else:
                                if not self.wbssig.we_i:
                                    self.wbs_state.next = self.wbs_states_t.WBS_READ_WAIT
                                else:
                                    self.wbs_state.next = self.wbs_states_t.WBS_WRITE_WAIT
                elif self.wbs_state == self.wbs_states_t.WBS_WRITE_WAIT:
                    # Write operation in the bus. Check flag wait.
                    if self.flagwait or self.flagbusy:
                        self.wbs_state.next = self.wbs_states_t.WBS_WRITE_WAIT
                    elif self.flagerr:
                        self.wbs_state.next = self.wbs_states_t.WBS_IDLE
                    else:
                        if not self.wbssig.cyc_i:
                            self.wbs_state.next = self.wbs_states_t.WBS_IDLE
                        else:
                            if not self.wbssig.stb_i:
                                self.wbs_state.next = self.wbs_states_t.WBS_INCYCLE
                            else:
                                if not self.wbssig.we_i:
                                    self.wbs_state.next = self.wbs_states_t.WBS_READ_WAIT
                                else:
                                    self.wbs_state.next = self.wbs_states_t.WBS_WRITE_WAIT
                else:
                    self.wbs_state.next = self.wbs_states_t.WBS_IDLE

        @always_comb
        def wbsstate_signals():
            # ack
            if self.wbs_state == self.wbs_states_t.WBS_READ_WAIT or self.wbs_state == self.wbs_states_t.WBS_WRITE_WAIT:
                self.wbssig.ack_o.next = not self.flagwait and self.wbssig.cyc_i and self.wbssig.stb_i
            else:
                self.wbssig.ack_o.next = False
            # stall
            self.wbssig.stall_o.next = self.flagbusy
            # err
            self.wbssig.err_o.next = self.flagerr

        return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
