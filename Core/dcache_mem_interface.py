#!/usr/bin/env python
# Copyright (c) 2016 Angel Terrones (<angelterrones@gmail.com>)
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
from myhdl import enum
from myhdl import instances


class CacheIFIO():
    """
    Cache control interface
    """
    def __init__(self):
        self.address_i   = Signal(modbv(0)[32:])
        self.data_i      = Signal(modbv(0)[32:])
        self.data_o      = Signal(modbv(0)[32:])
        self.fill        = Signal(False)
        self.evict       = Signal(False)
        self.read_single = Signal(False)
        self.wr_single   = Signal(modbv(0)[4:])
        self.done        = Signal(False)


class CacheMemIO:
    """
    Defines the Cache's MEM IO port.

    :ivar addr:   Address
    :ivar data_i: Data input
    :ivar data_o: Data output
    :ivar we:     Write enable
    """
    def __init__(self,
                 A_WIDTH=10,
                 D_WIDTH=8):
        """
        Initializes the IO ports.
        """
        self.addr   = Signal(modbv(0)[A_WIDTH:])
        self.data_i = Signal(modbv(0)[D_WIDTH:])
        self.data_o = Signal(modbv(0)[D_WIDTH:])
        self.we     = Signal(False)


def DCacheMemInterface(clk,
                       rst,
                       cache_if,
                       cache_mem_io,
                       mem,
                       BLOCK_WIDTH=5,
                       SET_WIDTH=9):
    """
    Handles mem interface.
    """
    fsm_states = enum('IDLE',
                      'FETCH',
                      'WRITE1',
                      'WRITE2',
                      'WRITE3',
                      'MEM_SINGLE')

    state   = Signal(fsm_states.IDLE)
    n_state = Signal(fsm_states.IDLE)

    wr_and  = Signal(False)
    request_idx = Signal(modbv(0)[BLOCK_WIDTH - 2:])

    @always_comb
    def wr_and_reduce():
        tmp = True
        for value in cache_if.wr_single:
            tmp = tmp and value
        wr_and.next = tmp

    @always_comb
    def next_state_logic():
        n_state.next = state
        if state == fsm_states.IDLE:
            if cache_if.evict:
                n_state.next = fsm_states.WRITE1
            elif cache_if.fill:
                n_state.next = fsm_states.FETCH
            elif cache_if.read_single or wr_and:
                n_state.next = fsm_states.MEM_SINGLE
        elif state == fsm_states.FETCH:
            if mem.ready and request_idx == modbv(-1)[BLOCK_WIDTH - 2:]:
                n_state.next = fsm_states.IDLE
        elif state == fsm_states.WRITE1:
            n_state.next = fsm_states.WRITE2
        elif state == fsm_states.WRITE2:
            pass
        elif state == fsm_states.WRITE3:
            pass
        elif state == fsm_states.MEM_SINGLE:
            pass

    @always(clk.posedge)
    def update_state():
        if rst:
            state.next = fsm_states.IDLE
        else:
            state.next = n_state

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
