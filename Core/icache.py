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
from myhdl import enum
from myhdl import modbv
from ram_dp import RAM_DP
from ram_dp import RAMIOPort


def ICache(clk,
           rst,
           invalidate,
           cpu,
           mem,
           ENABLE=True,
           D_WIDTH=32,
           BLOCK_WIDTH=5,
           SET_WIDTH=9,
           WAYS=2,
           LIMIT_WIDTH=32):
    """
    The Instruction Cache module.

    :param clk:
    :param rst:
    :param invalidate:
    :param cpu:
    :param mem:
    :param ENABLE:
    :param D_WIDTH:
    :param BLOCK_WIDTH:
    :param SET_WIDTH:
    :param WAYS:
    :param LIMIT_WIDTH:
    """
    assert D_WIDTH == 32, "Error: Unsupported D_WIDTH. Supported values: {32}"
    assert BLOCK_WIDTH > 0, "Error: BLOCK_WIDTH must be a value > 0"
    assert SET_WIDTH > 0, "Error: SET_WIDTH must be a value > 0"
    assert not (WAYS & (WAYS - 1)), "Error: WAYS must be a power of 2"

    # --------------------------------------------------------------------------
    # params
    WAY_WIDTH = BLOCK_WIDTH + SET_WIDTH
    TAG_WIDTH = LIMIT_WIDTH - WAY_WIDTH
    # width and index for tags
    TAGMEM_WAY_WIDTH = TAG_WIDTH + 1
    TAGMEM_WAY_VALID = TAGMEM_WAY_WIDTH - 1
    # calculate the needed LRU bits (from mor1kx_icache.v)
    TAG_LRU_WIDTH = (WAYS * (WAYS - 1)) >> 1  # (N*(N-1))/2
    TAG_LRU_WAY_WIDTH_BITS = TAG_LRU_WIDTH if WAYS >= 2 else 1
    # Size of tag memory
    TAGMEM_WIDTH = (TAGMEM_WAY_WIDTH * WAYS) + TAG_LRU_WIDTH
    # --------------------------------------------------------------------------

    ic_states = enum('CHECK', 'FETCH', 'WAIT', 'FLUSH', encoding='one_hot')

    tag_read_port     = RAMIOPort()
    tag_update_port   = RAMIOPort()
    cache_read_port   = RAMIOPort()
    cache_update_port = RAMIOPort()
    state             = Signal(ic_states.CHECK)
    n_state           = Signal(ic_states.CHECK)

    tag_address       = Signal(modbv(0)[TAG_WIDTH:])
    tag_in = [Signal(0)[TAG_WIDTH:] for _ in range(0, WAYS)]
    tag_out = [Signal(0)[TAG_WIDTH:] for _ in range(0, WAYS)]

    @always_comb
    def assignments():
        pass

    @always_comb
    def next_state_logic():
        n_state.next = state
        if state == ic_states.CHECK:
            if flush or invalidate:
                # cache flush
                n_state.next = ic_states.FLUSH
            elif miss:
                # miss: refill line
                n_state.next = ic_states.FETCH
            else:
                # Hit or read request
                n_state.next = ic_states.CHECK
        elif state == ic_states.FETCH:
            if final_fetch:
                n_state.next = ic_states.WAIT
        elif state == ic_states.FLUSH:
            if final_flush:
                n_state.next = ic_states.WAIT
        elif state == ic_states.WAIT:
            n_state.next = ic_states.CHECK

    @always(clk.posedge)
    def update_state():
        if rst:
            state.next = ic_states.CHECK
        else:
            state.next = n_state

    @always(clk.posedge)
    def refill_fsm():
        pass

    @always(clk.posedge)
    def flush_fsm():
        pass

    @always_comb
    def no_cache():
        mem.addr.next  = cpu.addr
        mem.wdata.next = cpu.wdata
        mem.wr.next    = cpu.wr
        mem.fcn.next   = cpu.fcn
        mem.valid.next = cpu.valid
        cpu.rdata.next = mem.rdata
        cpu.ready.next = mem.ready
        cpu.fault.next = mem.fault

    # Instantiate memory
    tag_mem = RAM_DP(tag_read_port,
                     tag_update_port,
                     A_WIDTH=SET_WIDTH,
                     D_WIDTH=TAGMEM_WIDTH)

    # instantiate main memory (cache)
    cache_mem = [RAM_DP(cache_read_port,
                        cache_update_port,
                        A_WIDTH=WAY_WIDTH - 2,
                        D_WIDTH=D_WIDTH)
                 for _ in range(0, WAYS)]

    # Bypass the cache if this module is disabled.
    if ENABLE:
        return next_state_logic, update_state, tag_mem, cache_mem
    else:
        return no_cache

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
