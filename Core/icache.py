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
from memIO import MemOp
from functools import reduce


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
    TAG_LRU_WIDTH_BITS = TAG_LRU_WIDTH if WAYS >= 2 else 1
    # Size of tag memory
    TAGMEM_WIDTH = (TAGMEM_WAY_WIDTH * WAYS) + TAG_LRU_WIDTH
    # --------------------------------------------------------------------------

    ic_states = enum('CHECK', 'FETCH', 'WAIT', 'FLUSH', 'FLUSH_LAST', encoding='one_hot')

    tag_read_port     = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    tag_update_port   = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    cache_read_port   = [RAMIOPort(A_WIDTH=WAY_WIDTH, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    cache_update_port = [RAMIOPort(A_WIDTH=WAY_WIDTH, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    state             = Signal(ic_states.CHECK)
    n_state           = Signal(ic_states.CHECK)

    busy              = Signal(False)

    tag_address       = Signal(modbv(0)[TAG_WIDTH:])
    tag_in            = [Signal(0)[TAG_WIDTH:] for _ in range(0, WAYS)]
    tag_out           = [Signal(0)[TAG_WIDTH:] for _ in range(0, WAYS)]

    cache_mem_addr    = Signal(modbv(0)[WAY_WIDTH:])

    miss_w            = [Signal(False) for _ in range(0, WAYS)]
    miss_w_and        = Signal(False)
    miss              = Signal(False)

    flush             = Signal(False)
    n_flush           = Signal(False)
    flush_addr        = Signal(modbv(0)[LIMIT_WIDTH:])
    flush_we          = Signal(False)
    final_flush       = Signal(False)

    final_fetch       = Signal(False)
    fetch_addr        = Signal(modbv(0)[LIMIT_WIDTH:])

    @always_comb
    def assigments():
        busy.next           = state != ic_states.CHECK
        final_flush.next    = tag_update_port.addr == 0
        cache_mem_addr.next = cpu.addr[WAY_WIDTH:2]

    @always_comb
    def cpu_assignments():
        # cpu data_in assignment: instruction.
        cpu.rdata.next = 0x0BADF00D
        for i in range(0, WAYS):
            if not miss_w[i]:
                cpu.rdata.next = cache_read_port[i].data_o

        # cpu ready signal assigment: the module is not busy (flush/refill) and finished
        # memory transactions.
        cpu.ready.next = (False if busy else
                          (not miss_w_and if cpu.fnc == MemOp.M_RD and cpu.valid else
                           False))
        # cpu fault assignment
        cpu.fault.next = mem.fault

    @always_comb
    def mem_assignments():
        pass

    @always_comb
    def tag_assigments():
        for i in range(0, WAYS):
            tag_out[i].next = tag_read_port.data_o[TAGMEM_WAY_WIDTH * (i + 1):TAGMEM_WAY_WIDTH * i]
            tag_read_port.data_i[TAGMEM_WAY_WIDTH * (i + 1):TAGMEM_WAY_WIDTH * i].next = tag_in[i]
        tag_address.next      = cpu.addr[SET_WIDTH:0]
        tag_read_port.we.next = False

    @always_comb
    def cache_mem_assignment():
        for i in range(0, WAYS):
            cache_read_port[i].addr.next   = cache_mem_addr
            cache_read_port[i].data_i.next = 0xDEADC0DE
            cache_read_port[i].we.next     = False

    @always_comb
    def miss_check():
        for i in range(0, WAYS):
            miss_w[i].next = (not tag_out[i][TAGMEM_WAY_VALID] or tag_out[i] != cpu.addr[LIMIT_WIDTH:WAY_WIDTH])
        miss_w_and.next = reduce(lambda x, y: x and y, miss_w)
        miss.next = miss_w_and and cpu.fcn == MemOp.M_RD and not flush and not invalidate

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
                n_state.next = ic_states.FLUSH_LAST
            else:
                n_state.next = ic_states.FLUSH
        elif state == ic_states.FLUSH_LAST:
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

    @always_comb
    def flush_next_state():
        flush_addr.next = tag_update_port.addr
        flush_we.next   = tag_update_port.we
        n_flush.next    = flush

        if state == ic_states.CHECK:
            if flush or invalidate:
                flush_addr.next = modbv(0xFFFFFFFF)[SET_WIDTH:]
                flush_we.next   = True
                n_flush.next    = False
        elif state == ic_states.FLUSH:
            flush_addr.next = tag_update_port.addr - 1
            flush_we.next   = True
        elif state == ic_states.FLUSH_LAST:
            flush_we.next = False
        else:
            # latch the invalidate signal
            n_flush.next = invalidate

    @always(clk.posedge)
    def flush_update():
        if rst:
            tag_update_port.addr.next = modbv(0xFFFFFFFF)[SET_WIDTH:]
            tag_update_port.we.next   = False
            flush.next                = False
        else:
            tag_update_port.addr.next = flush_addr
            tag_update_port.we.next   = flush_we
            flush.next                = n_flush

    @always_comb
    def tag_write():
        for i in range(0, WAYS):
            tag_in[i].next          = tag_out[i]
        tag_update_port.we.next = False

        if state == ic_states.CHECK:
            if miss:
                pass
            else:
                # update LRU
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
    cache_mem = [RAM_DP(cache_read_port[i],
                        cache_update_port[i],
                        A_WIDTH=WAY_WIDTH - 2,
                        D_WIDTH=D_WIDTH)
                 for i in range(0, WAYS)]

    # Bypass the cache if this module is disabled.
    if ENABLE:
        return next_state_logic, update_state, tag_mem, cache_mem
    else:
        return no_cache

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
