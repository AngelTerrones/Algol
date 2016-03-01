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
from myhdl import instances
from Core.ram_dp import RAM_DP
from Core.ram_dp import RAMIOPort
from Core.memIO import MemOp
from Core.cache_lru import CacheLRU
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
    WAY_WIDTH = BLOCK_WIDTH + SET_WIDTH  # cache mem address width
    TAG_WIDTH = LIMIT_WIDTH - WAY_WIDTH  # tag size
    # width and index for tags
    TAGMEM_WAY_WIDTH = TAG_WIDTH + 1         # Add the valid bit
    TAGMEM_WAY_VALID = TAGMEM_WAY_WIDTH - 1  # Valid bit index
    # calculate the needed LRU bits (from mor1kx_icache.v)
    TAG_LRU_WIDTH = (WAYS * (WAYS - 1)) >> 1  # (N*(N-1))/2
    # TAG_LRU_WIDTH_BITS = TAG_LRU_WIDTH if WAYS >= 2 else 1
    # Size of tag memory
    TAGMEM_WIDTH = (TAGMEM_WAY_WIDTH * WAYS) + TAG_LRU_WIDTH  # width of one tag line.
    # --------------------------------------------------------------------------

    ic_states = enum('CHECK', 'FETCH', 'WAIT', 'FLUSH', 'FLUSH_LAST', encoding='one_hot')

    tag_rw_port       = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    tag_flush_port    = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    cache_read_port   = [RAMIOPort(A_WIDTH=WAY_WIDTH, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    cache_update_port = [RAMIOPort(A_WIDTH=WAY_WIDTH, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]

    state             = Signal(ic_states.CHECK)
    n_state           = Signal(ic_states.CHECK)

    busy              = Signal(False)

    miss              = Signal(False)
    miss_w            = Signal(modbv(0)[WAYS:])
    miss_w_and        = Signal(False)
    flush             = Signal(False)
    final_fetch       = Signal(False)
    final_flush       = Signal(False)

    lru_select        = Signal(modbv(0)[WAYS:])
    current_lru       = Signal(modbv(0)[TAG_LRU_WIDTH:])
    update_lru        = Signal(modbv(0)[TAG_LRU_WIDTH:])
    access_lru        = Signal(modbv(0)[WAYS:])
    lru_pre           = Signal(modbv(0)[WAYS:])
    lru_post          = Signal(modbv(0)[WAYS:])

    # tag in/out signals: For data assignment
    tag_in            = [Signal(modbv(0))[TAGMEM_WAY_WIDTH:] for _ in range(0, WAYS)]
    tag_out           = [Signal(modbv(0))[TAGMEM_WAY_WIDTH:] for _ in range(0, WAYS)]
    lru_in            = Signal(modbv(0))[TAG_LRU_WIDTH:]
    lru_out           = Signal(modbv(0))[TAG_LRU_WIDTH:]
    tag_we            = Signal(False)

    # refill signals
    refill_addr       = Signal(0)[LIMIT_WIDTH:]
    refill_valid      = Signal(False)
    n_refill_addr     = Signal(0)[LIMIT_WIDTH:]
    n_refill_valid    = Signal(False)

    @always_comb
    def assignments():
        tag_rw_port.clk.next    = clk
        tag_flush_port.clk.next = clk
        final_fetch.next        = refill_addr[BLOCK_WIDTH:] == modbv(~0x3)[BLOCK_WIDTH:]
        lru_select.next         = lru_pre
        current_lru.next        = lru_out
        access_lru.next         = ~miss_w

    @always_comb
    def miss_check():
        """
        For each way, check tag and valid flag, and reduce the vector using AND.
        If the vector is full of ones, the data is not in the cache: assert the miss flag.

        MISS: data not in cache and the memory operation is a valid read. Ignore this if
        the module is flushing data.
        """
        for i in range(0, WAYS):
            miss_w[i].next = (not tag_out[i][TAGMEM_WAY_VALID] or tag_out[i][TAGMEM_WAY_WIDTH:0] != cpu.addr[LIMIT_WIDTH:WAY_WIDTH])
        miss_w_and.next = reduce(lambda x, y: x and y, miss_w)
        miss.next = miss_w_and and (cpu.fcn == MemOp.M_RD) and not flush and not invalidate

    @always_comb
    def tag_rport():
        # for each way, assign tags
        for i in range(0, WAYS):
            tag_out[i].next = tag_rw_port.data_o[TAGMEM_WAY_WIDTH * (i + 1):TAGMEM_WAY_WIDTH * i]
            tag_rw_port.data_i[TAGMEM_WAY_WIDTH * (i + 1):TAGMEM_WAY_WIDTH * i].next = tag_in[i]
        # connect to the lru field for reading and updating
        lru_out.next = tag_rw_port.data_o[TAGMEM_WIDTH:(TAGMEM_WAY_WIDTH * WAYS)]
        tag_rw_port.data_i[TAGMEM_WIDTH:(TAGMEM_WAY_WIDTH * WAYS)].next = lru_in

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
            # fetch a line from memory
            if final_fetch:
                n_state.next = ic_states.WAIT
        elif state == ic_states.FLUSH:
            # invalidate tag memory
            if final_flush:
                n_state.next = ic_states.FLUSH_LAST
            else:
                n_state.next = ic_states.FLUSH
        elif state == ic_states.FLUSH_LAST:
            # last cycle for flush
            n_state.next = ic_states.WAIT
        elif state == ic_states.WAIT:
            n_state.next = ic_states.CHECK

    @always(clk.posedge)
    def update_state():
        if rst:
            state.next = ic_states.CHECK
        else:
            state.next = n_state

    @always_comb
    def fetch_fsm():
        n_refill_addr.next  = refill_addr
        n_refill_valid.next = False  # refill_valid

        if state == ic_states.CHECK:
            if flush or invalidate:
                n_refill_valid.next = False
            elif miss:
                n_refill_addr.next  = concat(cpu.addr[LIMIT_WIDTH:BLOCK_WIDTH], modbv(0)[BLOCK_WIDTH:])
                n_refill_valid.next = True  # not mem.ready?
        elif state == ic_states.FETCH:
            n_refill_valid.next = not mem.ready
            if not refill_valid and mem.ready:
                if final_fetch:
                    n_refill_valid.next = False
                else:
                    n_refill_addr.next  = refill_addr + 4

    @always(clk.posedge)
    def update_fetch():
        if rst:
            refill_addr.next  = 0
            refill_valid.next = False
        else:
            refill_addr.next  = n_refill_addr
            refill_valid.next = n_refill_valid

    @always_comb
    def tag_write():
        """
        Update the tag and lru field.
        Tag: update when failure.
        lru: update after refilling or hit.
        """
        for i in range(0, WAYS):
            tag_in[i].next = tag_out[i]
        tag_we.next = False
        lru_in.next = lru_out

        if state == ic_states.CHECK:
            if flush or invalidate:
                tag_we.next = False
            if miss:
                for i in range(0, WAYS):
                    if lru_select[i]:
                        tag_in[i][TAG_WIDTH:0].next      = cpu.addr[LIMIT_WIDTH:WAY_WIDTH]
                        tag_in[i][TAGMEM_WAY_VALID].next = True
                tag_we.next = True
            else:
                lru_in.next = update_lru
                tag_we.next = True

    @always_comb
    def tag_port_assign():
        tag_rw_port.we.next    = False
        tag_flush_port.we.next = False

    @always_comb
    def cpu_port_assign():
        """
        Assignments to the cpu interface.
        """
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
    def mem_port_assign():
        """
        Assignments to the mem interface for refill operations.
        """
        mem.addr.next  = refill_addr
        mem.wdata.next = 0x0BADF00D
        mem.wr.next    = modbv(0)[4:]
        mem.fcn.next   = MemOp.M_RD
        mem.valid.next = refill_valid

    @always_comb
    def chache_mem_r():
        for i in range(0, WAYS):
            cache_read_port[i].clk.next    = clk
            cache_read_port[i].addr.next   = cpu.addr[WAY_WIDTH:]
            cache_read_port[i].data_i.next = 0xAABBCCDD

    @always_comb
    def cache_mem_update():
        # Connect the mem data_i port to the cache memories.
        for i in range(0, WAYS):
            # ignore data_o from update port
            cache_update_port[i].clk.next = clk
            cache_update_port[i].addr.next = 0
            cache_update_port[i].data_i.next = mem.rdata
            cache_update_port[i].we.next = lru_select[i]

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
    tag_mem = RAM_DP(tag_rw_port,
                     tag_flush_port,
                     A_WIDTH=SET_WIDTH,
                     D_WIDTH=TAGMEM_WIDTH)

    # instantiate main memory (cache)
    cache_mem = [RAM_DP(cache_read_port[i],
                        cache_update_port[i],
                        A_WIDTH=WAY_WIDTH - 2,
                        D_WIDTH=D_WIDTH)
                 for i in range(0, WAYS)]

    lru_m = CacheLRU(current_lru,
                     access_lru,
                     update_lru,
                     lru_pre,
                     lru_post)

    # Bypass the cache if this module is disabled.
    if ENABLE:
        return tag_mem, cache_mem, lru_m, instances()
    else:
        return no_cache

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
