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
from myhdl import concat
from Core.ram_dp import RAM_DP
from Core.ram_dp import RAMIOPort
from Core.memIO import MemOp
from Core.cache_lru import CacheLRU


def DCache(clk,
           rst,
           req_flush,
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

    :param clk:         System clock
    :param rst:         System reset
    :param req_flush:   Invalidate the cache
    :param cpu:         CPU interface
    :param mem:         Memory interface
    :param ENABLE:      Enable generation of this module
    :param D_WIDTH:     Data width
    :param BLOCK_WIDTH: Address width for byte access inside a block line
    :param SET_WIDTH:   Address width for line access inside a block
    :param WAYS:        Number of ways for associative cache
    :param LIMIT_WIDTH: Maximum width for address
    """
    assert D_WIDTH == 32, "Error: Unsupported D_WIDTH. Supported values: {32}"
    assert BLOCK_WIDTH > 0, "Error: BLOCK_WIDTH must be a value > 0"
    assert SET_WIDTH > 0, "Error: SET_WIDTH must be a value > 0"
    assert not (WAYS & (WAYS - 1)), "Error: WAYS must be a power of 2"

    def cache():
        # --------------------------------------------------------------------------
        # params
        WAY_WIDTH            = BLOCK_WIDTH + SET_WIDTH  # cache mem address width
        TAG_WIDTH            = LIMIT_WIDTH - WAY_WIDTH  # tag size
        # width and index for tags
        TAGMEM_WAY_WIDTH     = TAG_WIDTH + 2         # Add the valid and dirty bit
        TAGMEM_WAY_VALID     = TAGMEM_WAY_WIDTH - 2  # Valid bit index
        TAGMEM_WAY_DIRTY     = TAGMEM_WAY_WIDTH - 1  # Dirty bit index
        # calculate the needed LRU bits (from mor1kx_icache.v)
        TAG_LRU_WIDTH        = (WAYS * (WAYS - 1)) >> 1  # (N*(N-1))/2
        # Size of tag memory
        TAGMEM_WIDTH         = (TAGMEM_WAY_WIDTH * WAYS) + TAG_LRU_WIDTH  # width of one tag line.
        # --------------------------------------------------------------------------
        dc_states = enum('IDLE'
                         'SINGLE',
                         'CHECK',
                         'FETCH',
                         'WAIT',
                         'WAIT2',
                         'WRITE',
                         'SINGLE_READY',
                         'EVICTING',
                         'UPDATE',
                         'FLUSH1',
                         'FLUSH2',
                         'FLUSH3',
                         'FLUSH4',
                         encoding='binary')
        # ports to memory
        tag_rw_port       = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
        tag_flush_port    = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
        cache_read_port   = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
        cache_update_port = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
        data_cache        = [cache_read_port[i].data_o for i in range(0, WAYS)]

        # tag in/out signals: For data assignment
        tag_in            = [Signal(modbv(0)[TAGMEM_WAY_WIDTH:]) for _ in range(0, WAYS)]
        tag_out           = [Signal(modbv(0)[TAGMEM_WAY_WIDTH:]) for _ in range(0, WAYS)]
        lru_in            = Signal(modbv(0)[TAG_LRU_WIDTH:])
        lru_out           = Signal(modbv(0)[TAG_LRU_WIDTH:])
        tag_we            = Signal(False)

        lru_select        = Signal(modbv(0)[WAYS:])
        current_lru       = Signal(modbv(0)[TAG_LRU_WIDTH:])
        update_lru        = Signal(modbv(0)[TAG_LRU_WIDTH:])
        access_lru        = Signal(modbv(0)[WAYS:])
        lru_pre           = Signal(modbv(0)[WAYS:])
        lru_post          = Signal(modbv(0)[WAYS:])

        # for memory access
        mem_addr          = Signal(modbv(0)[LIMIT_WIDTH:])
        mem_valid         = Signal(False)
        n_mem_addr        = Signal(modbv(0)[LIMIT_WIDTH:])
        n_mem_valid       = Signal(False)

        # flush signals
        flush             = Signal(False)
        flush_addr        = Signal(modbv(0)[SET_WIDTH:])
        flush_we          = Signal(False)
        n_flush_addr      = Signal(modbv(0)[SET_WIDTH:])
        n_flush_we        = Signal(False)
        n_flush           = Signal(False)
        flush_single      = Signal(False)

        # refill signals
        refill_addr       = Signal(modbv(0)[LIMIT_WIDTH:])
        refill_valid      = Signal(False)
        n_refill_addr     = Signal(modbv(0)[LIMIT_WIDTH:])
        n_refill_valid    = Signal(False)

        # main FSM
        state             = Signal(dc_states.IDLE)
        n_state           = Signal(dc_states.IDLE)

        miss              = Signal(False)
        miss_w            = Signal(modbv(0)[WAYS:])
        miss_w_and        = Signal(False)
        valid             = Signal(False)
        dirty             = Signal(False)
        done              = Signal(False)

        final_flush       = Signal(False)
        final_fetch       = Signal(False)
        final_evict       = Signal(False)

        use_cache         = Signal(False)

        @always_comb
        def next_state_logic():
            n_state.next = state
            if state == dc_states.IDLE:
                if req_flush or flush:
                    # flush request
                    n_state.next = dc_states.FLUSH2
                elif cpu.valid and not cpu.fcn and not use_cache:
                    # read (uncached)
                    n_state.next = dc_states.SINGLE
                elif cpu.valid and not cpu.fcn:
                    # read (cached)
                    n_state.next = dc_states.CHECK
                elif cpu.valid and cpu.fcn and not use_cache:
                    # write (uncached)
                    n_state.next = dc_states.SINGLE
                elif cpu.valid and cpu.fcn:
                    # write (cached)
                    n_state.next = dc_states.WRITE
            elif state == dc_states.WRITE:
                if not miss and dirty:
                    # Hit and line is dirty
                    n_state.next = dc_states.IDLE
                elif not miss and not dirty:
                    # Hit and make line dirty
                    n_state.next = dc_states.WAIT2
                elif valid and dirty:
                    # Cache is dirty: write back
                    n_state.next = dc_states.EVICTING
                else:
                    # Refill line
                    n_state.next = dc_states.UPDATE
            elif state == dc_states.EVICTING:
                if done:
                    if not cpu.fcn:
                        # write back for read
                        n_state.next = dc_states.FETCH
                    else:
                        # write for write
                        n_state.next = dc_states.UPDATE
            elif state == dc_states.UPDATE:
                if done:
                    n_state.next = dc_states.WAIT2
            elif state == dc_states.CHECK:
                if not miss:
                    # cache hit
                    n_state.next = dc_states.IDLE
                elif valid and dirty:
                    # cache is valid but dirty
                    n_state.next = dc_states.EVICTING
                else:
                    # cache miss
                    n_state.next = dc_states.FETCH
            elif state == dc_states.SINGLE:
                if done:
                    if cpu.fcn:
                        n_state.next = dc_states.SINGLE_READY
                    elif not miss and dirty:
                        n_state.next = dc_states.FLUSH4
                    elif not miss:
                        n_state.next = dc_states.SINGLE_READY
                    else:
                        n_state.next = dc_states.SINGLE_READY
            elif state == dc_states.FETCH:
                if done:
                    n_state.next = dc_states.WAIT
            elif state == dc_states.WAIT:
                n_state.next = dc_states.WAIT2
            elif state == dc_states.WAIT2:
                n_state.next = dc_states.IDLE
            elif state == dc_states.SINGLE_READY:
                n_state.next = dc_states.IDLE
            elif state == dc_states.FLUSH1:
                if final_flush:
                    n_state.next = dc_states.WAIT
                else:
                    n_state.next = dc_states.FLUSH2
            elif state == dc_states.FLUSH2:
                n_state.next = dc_states.FLUSH3
            elif state == dc_states.FLUSH3:
                if dirty:
                    n_state.next = dc_states.FLUSH4
                elif flush_single:
                    n_state.next = dc_states.WAIT
                else:
                    n_state.next = dc_states.FLUSH1
            elif state == dc_states.FLUSH4:
                if done:
                    if flush_single:
                        n_state.next = dc_states.SINGLE_READY
                    else:
                        n_state.next = dc_states.FLUSH1

        @always(clk.posedge)
        def update_state():
            if rst:
                state.next = dc_states.IDLE
            else:
                state.next = n_state

        # Instantiate tag memory
        tag_mem = RAM_DP(tag_rw_port,
                         tag_flush_port,
                         A_WIDTH=SET_WIDTH,
                         D_WIDTH=TAGMEM_WIDTH)

        # Instantiate main memory (Cache)
        cache_mem = [RAM_DP(cache_read_port[i],
                            cache_update_port[i],
                            A_WIDTH=WAY_WIDTH - 2,
                            D_WIDTH=D_WIDTH)
                     for i in range(0, WAYS)]

        # LRU memory
        lru_m = CacheLRU(current_lru,
                         access_lru,
                         update_lru,
                         lru_pre,
                         lru_post,
                         NUMWAYS=WAYS)

        return (tag_mem, cache_mem, lru_m)

    def no_cache():
        @always_comb
        def rtl():
            mem.addr.next  = cpu.addr
            mem.wdata.next = cpu.wdata
            mem.wr.next    = cpu.wr
            mem.fcn.next   = cpu.fcn
            mem.valid.next = cpu.valid
            cpu.rdata.next = mem.rdata
            cpu.ready.next = mem.ready
            cpu.fault.next = mem.fault

        return rtl

    # Bypass the cache if this module is disabled.
    if ENABLE:
        return cache()
    else:
        return no_cache()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
