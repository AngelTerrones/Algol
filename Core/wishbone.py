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

    :ivar clk.    System clock
    :ivar rst:    System reset
    :ivar addr:   Address
    :ivar data_o: Data output
    :ivar data_i: Data input
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
        self.clk   = Signal(False)
        self.rst   = Signal(False)
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

    :param intercon: the intercon bus.
    """
    def __init__(self, intercon):
        """
        Initializes the IO ports.
        """
        if not isinstance(intercon, WishboneIntercon):
            raise AttributeError("Unknown intercon type for {0}".format(str(intercon)))

        self.clk_i   = intercon.clk
        self.rst_i   = intercon.rst
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

    :param intercon: the intercon bus.
    """
    def __init__(self, intercon):
        """
        Initializes the IO ports.
        """
        if not isinstance(intercon, WishboneIntercon):
            raise AttributeError("Unknown intercon type for {0}".format(str(intercon)))

        self.clk_i   = intercon.clk
        self.rst_i   = intercon.rst
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
    def __init__(self, master_signals, flagread, flagwrite, flagrmw):
        if isinstance(master_signals, WishboneMaster):
            self.wbmsig = master_signals
        else:
            raise AttributeError("Argument slave_signals must be of type WishboneSlave. Argument: {0}".format(str(master_signals)))

        self.flagread  = flagread
        self.flagwrite = flagwrite
        self.flagrmw   = flagrmw

    def gen_wbm(self):
        """
        State machine for master.
        Generates the state signals for the master.
        """
        self.wbm_states_t = enum('WBM_IDLE',
                                 'WBM_INCYCLE',
                                 'WBM_READ_WAIT',
                                 'WBM_WRITE_WAIT',
                                 'WBM_RMW_RD_WAIT',
                                 'WBM_RMW_MID_WAIT',
                                 'WBM_RMW_WR_WAIT')
        self.wbm_state = Signal(self.wbm_states_t.WBM_IDLE)

        self.list_trig_signals = []
        for i in zip(('trig_rd', 'trig_wr', 'trig_rmw'), self.wbm_states_t._names[2:5], (self.flagread, self.flagwrite, self.flagrmw)):
            self.list_trig_signals.append({"name": i[0], "initstate": getattr(self.wbm_states_t, i[1]), "trig": i[2]})

        trig_vector = Signal(modbv(0)[len(self.list_trig_signals):])
        ack_vector     = Signal(modbv(0)[2:])

        @always_comb
        def concat_trig_vector():
            trig_vector.next = concat(self.flagread, self.flagwrite, self.flagrmw)

        @always_comb
        def concat_ack_vector():
            ack_vector.next = concat(self.wbmsig.ack_i, self.wbmsig.err_i)

        # state machine
        @always(self.wbmsig.clk_i.posedge)
        def wbmstate_fsm():
            if self.wbmsig.rst_i:
                self.wbm_state.next = self.wbm_states_t.WBM_IDLE
            else:
                if self.wbm_state == self.wbm_states_t.WBM_IDLE:
                    # No access to master bus
                    # Check for trigger signals
                    if trig_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                    else:
                        for i in self.list_trig_signals:
                            if i['trig']:
                                self.wbm_state.next = i['initstate']
                elif self.wbm_state == self.wbm_states_t.WBM_INCYCLE:
                    # Current cycle in progress, but inactive.
                    # CYC_O is asserted, and STB_O is deasserted.
                    if trig_vector == 0:
                        self.wbm_state.next = self.wbm_states_t.WBM_IDLE
                    else:
                        for i in self.list_trig_signals:
                            if i['trig']:
                                self.wbm_state.next = i['initstate']
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
    def __init__(self, slave_signals, flagbusy, flagerr, flagwait):
        if isinstance(slave_signals, WishboneSlave):
            self.wbssig = slave_signals
        else:
            raise AttributeError("Argument slave_signals must be of type WishboneSlave. Argument: {0}".format(str(slave_signals)))

        self.flagbusy = flagbusy
        self.flagerr  = flagerr
        self.flagwait = flagwait

    def gen_wbs(self):
        """
        State machine for slave.
        Generates the state signals for the slave.
        """
        self.wbs_states_t = enum('WBS_IDLE',
                                 'WBS_INCYCLE',
                                 'WBS_READ_WAIT',
                                 'WBS_WRITE_WAIT')
        self.wbs_state = Signal(self.wbs_states_t.WBS_IDLE)

        @always(self.wbssig.clk_i.posedge)
        def wbsstate_fsm():
            if self.wbssig.rst_i:
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
