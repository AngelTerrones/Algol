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


class WishboneIntercon:
    """
    Defines an Wishbone IO interface.

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

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
