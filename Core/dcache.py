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
from Core.cache_lru import CacheLRU
from Core.wishbone import WishboneMaster
from Core.wishbone import WishboneMasterGenerator
from Core.wishbone import WishboneSlave
from Core.wishbone import WishboneSlaveGenerator


def DCache(clk_i,
           rst_i,
           cpu,
           mem,
           invalidate,
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
    dc_states = enum('IDLE',
                     'SINGLE',
                     'READ',
                     'WRITE',
                     'FETCH',
                     'EVICTING',
                     'FLUSH1',
                     'FLUSH2',
                     'FLUSH3',
                     encoding='binary')
    # ports to memory
    tag_rw_port       = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    tag_flush_port    = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    cache_read_port   = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    cache_update_port = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    data_cache        = [cache_read_port[i].data_o for i in range(0, WAYS)]
    data_cache2       = [cache_update_port[i].data_o for i in range(0, WAYS)]
    tag_entry         = Signal(modbv(0)[TAG_WIDTH:])

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

    # flush signals
    flush_addr        = Signal(modbv(0)[SET_WIDTH:])
    flush_we          = Signal(False)
    n_flush_addr      = Signal(modbv(0)[SET_WIDTH:])
    n_flush_we        = Signal(False)

    # refill signals
    dc_update_addr    = Signal(modbv(0)[LIMIT_WIDTH:])
    evict_data        = Signal(modbv(0)[32:])

    # main FSM
    state             = Signal(dc_states.IDLE)
    n_state           = Signal(dc_states.IDLE)

    miss              = Signal(False)
    miss_w            = Signal(modbv(0)[WAYS:])
    miss_w_and        = Signal(False)
    valid             = Signal(False)
    dirty             = Signal(False)
    done              = Signal(False)
    cpu_active        = Signal(False)

    final_flush       = Signal(False)
    final_access      = Signal(False)
    fetch             = Signal(False)
    evict             = Signal(False)

    use_cache         = Signal(False)

    cpu_wbs   = WishboneSlave(cpu)
    mem_wbm   = WishboneMaster(mem)
    cpu_busy  = Signal(False)
    cpu_err   = Signal(False)
    cpu_wait  = Signal(False)
    mem_read  = Signal(False)
    mem_write = Signal(False)
    mem_rmw   = Signal(False)

    @always_comb
    def next_state_logic():
        n_state.next = state
        if state == dc_states.IDLE:
            if invalidate:
                # flush request
                n_state.next = dc_states.FLUSH1
            elif cpu_wbs.cyc_i and not cpu_wbs.we_i and not use_cache:
                # read (uncached)
                n_state.next = dc_states.SINGLE
            elif cpu_wbs.cyc_i and not cpu_wbs.we_i:
                # read (cached)
                n_state.next = dc_states.READ
            elif cpu_wbs.cyc_i and cpu_wbs.we_i and not use_cache:
                # write (uncached)
                n_state.next = dc_states.SINGLE
            elif cpu_wbs.cyc_i and cpu_wbs.we_i:
                # write (cached)
                n_state.next = dc_states.WRITE
        elif state == dc_states.SINGLE:
            if done:
                n_state.next = dc_states.IDLE
        elif state == dc_states.READ:
            if not miss:
                # cache hit
                n_state.next = dc_states.IDLE
            elif valid and dirty:
                # cache is valid but dirty
                n_state.next = dc_states.EVICTING
            else:
                # cache miss
                n_state.next = dc_states.FETCH
        elif state == dc_states.WRITE:
            if not miss:
                # Hit
                n_state.next = dc_states.IDLE
            elif valid and dirty:
                # Cache miss. Line is valid but dirty: write back
                n_state.next = dc_states.EVICTING
            else:
                n_state.next = dc_states.FETCH
        elif state == dc_states.EVICTING:
            if done:
                n_state.next = dc_states.FETCH
        elif state == dc_states.FETCH:
            if done:
                n_state.next = dc_states.IDLE
        elif state == dc_states.FLUSH1:
            n_state.next = dc_states.FLUSH2
        elif state == dc_states.FLUSH2:
            if dirty:
                n_state.next = dc_states.FLUSH3
            if final_flush:
                n_state.next = dc_states.IDLE
            else:
                n_state.next = dc_states.FLUSH1
        elif state == dc_states.FLUSH3:
            if done:
                if final_flush:
                    n_state.next = dc_states.IDLE
                else:
                    n_state.next = dc_states.FLUSH1

    @always(clk_i.posedge)
    def update_state():
        if rst_i:
            state.next = dc_states.IDLE
        else:
            state.next = n_state

    @always_comb
    def assignments():
        final_access.next = (dc_update_addr[BLOCK_WIDTH:] == modbv(~3)[BLOCK_WIDTH:]) and mem_wbm.ack_i and mem_wbm.cyc_o and mem_wbm.stb_o
        final_flush.next  = flush_addr == 0
        lru_select.next   = lru_pre
        current_lru.next  = lru_out
        access_lru.next   = ~miss_w
        use_cache.next    = not cpu_wbs.addr_i[31]  # Address < 0x8000_0000 use the cache

    @always_comb
    def tag_entry_assign():
        for i in range(0, WAYS):
            if lru_select[i]:
                tag_entry.next = tag_out[i][TAG_WIDTH:]

    @always_comb
    def done_fetch_evict_assign():
        fetch.next = state == dc_states.FETCH and not final_access
        evict.next = (state == dc_states.EVICTING or state == dc_states.FLUSH3) and not final_access
        done.next  = final_access if use_cache else mem_wbm.ack_i

    @always(clk_i.posedge)
    def cpu_active_assign():
        if rst_i:
            cpu_active.next = True
        else:
            cpu_active.next = cpu_wbs.cyc_i and cpu_wbs.stb_i

    @always_comb
    def miss_check():
        """
        For each way, check tag and valid flag, and reduce the vector using AND.
        If the vector is full of ones, the data is not in the cache: assert the miss flag.

        MISS: data not in cache and the memory operation is a valid read. Ignore this if
        the module is flushing data.
        """
        value = modbv(0)[WAYS:]
        for i in range(0, WAYS):
            value[i] = (not tag_out[i][TAGMEM_WAY_VALID] or tag_out[i][TAG_WIDTH:0] != cpu_wbs.addr_i[LIMIT_WIDTH:WAY_WIDTH])
        miss_w.next = value

    @always_comb
    def miss_check_2():
        value = True
        for i in range(0, WAYS):
            value = value and miss_w[i]
        miss_w_and.next = value

    @always_comb
    def miss_check_3():
        valid_access = cpu_wbs.cyc_i and cpu_wbs.stb_i and use_cache
        miss.next    = miss_w_and and valid_access and not invalidate

    @always_comb
    def get_valid_n_dirty():
        for i in range(0, WAYS):
            if lru_select[i]:
                valid.next = tag_out[i][TAGMEM_WAY_VALID]
                dirty.next = tag_out[i][TAGMEM_WAY_DIRTY]

    @always_comb
    def tag_rport():
        temp = modbv(0)[TAGMEM_WIDTH:]
        # for each way, assign tags
        for i in range(0, WAYS):
            tag_out[i].next = tag_rw_port.data_o[TAGMEM_WAY_WIDTH * (i + 1):TAGMEM_WAY_WIDTH * i]
            temp[TAGMEM_WAY_WIDTH * (i + 1):TAGMEM_WAY_WIDTH * i] = tag_in[i]

        temp[TAGMEM_WIDTH:(TAGMEM_WAY_WIDTH * WAYS)] = lru_in
        lru_out.next                                 = tag_rw_port.data_o[TAGMEM_WIDTH:(TAGMEM_WAY_WIDTH * WAYS)]
        tag_rw_port.clk.next                         = clk_i
        tag_rw_port.data_i.next                      = temp
        tag_rw_port.addr.next                        = cpu_wbs.addr_i[WAY_WIDTH:BLOCK_WIDTH]
        tag_rw_port.we.next                          = tag_we

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

        if state == dc_states.READ or state == dc_states.WRITE:
            if miss:
                for i in range(0, WAYS):
                    if lru_select[i]:
                        tag_in[i].next = concat(False, True, cpu_wbs.addr_i[LIMIT_WIDTH:WAY_WIDTH])
                tag_we.next = True
            else:
                if cpu_wbs.ack_o and cpu_wbs.cyc_i:
                    for i in range(0, WAYS):
                        if lru_select[i]:
                            tag_in[i].next = tag_out[i] | (cpu_wbs.we_i << TAGMEM_WAY_DIRTY)  # TODO: Optimize
                    lru_in.next = update_lru
                    tag_we.next = True

    @always_comb
    def flush_next_state():
        n_flush_we.next   = False
        n_flush_addr.next = flush_addr

        if state == dc_states.IDLE:
            if invalidate:
                n_flush_addr.next = modbv(-1)[SET_WIDTH:]
        elif state == dc_states.FLUSH1:
            n_flush_we.next = True
        elif state == dc_states.FLUSH2:
            n_flush_we.next = False
            n_flush_addr.next = flush_addr - modbv(1)[SET_WIDTH:]

    @always(clk_i.posedge)
    def update_flush():
        if rst_i:
            flush_addr.next = modbv(-1)[SET_WIDTH:]
            flush_we.next   = False
        else:
            flush_addr.next = n_flush_addr
            flush_we.next   = n_flush_we and not dirty

    @always(clk_i.posedge)
    def update_addr_fsm():
        if rst_i:
            dc_update_addr.next  = 0
        else:
            if state == dc_states.READ or state == dc_states.WRITE:
                if miss and not dirty:
                    dc_update_addr.next = concat(cpu_wbs.addr_i[LIMIT_WIDTH:BLOCK_WIDTH], modbv(0)[BLOCK_WIDTH:])
                elif miss and dirty:
                    dc_update_addr.next = concat(tag_entry, cpu_wbs.addr_i[WAY_WIDTH:2], modbv(0)[2:])
            elif state == dc_states.FLUSH2:
                if dirty:
                    dc_update_addr.next = concat(tag_entry, modbv(0)[BLOCK_WIDTH:])
            elif state == dc_states.EVICTING or state == dc_states.FETCH or state == dc_states.FLUSH3:
                if final_access:
                    dc_update_addr.next = concat(cpu_wbs.addr_i[LIMIT_WIDTH:BLOCK_WIDTH], modbv(0)[BLOCK_WIDTH:])
                elif mem_wbm.ack_i and mem_wbm.stb_o:
                    dc_update_addr.next = dc_update_addr + modbv(4)[BLOCK_WIDTH:]
            else:
                dc_update_addr.next = 0

    @always_comb
    def tag_port_assign():
        tag_flush_port.clk.next    = clk_i
        tag_flush_port.addr.next   = flush_addr
        tag_flush_port.data_i.next = modbv(0)[TAGMEM_WAY_WIDTH:]
        tag_flush_port.we.next     = flush_we

    @always_comb
    def cpu_data_assign():
        """
        Assignments to the cpu interface.
        """
        # cpu data_in assignment: instruction.
        temp = 0x12345678
        for i in range(0, WAYS):
            if not miss_w[i]:
                temp = data_cache[i]
        cpu_wbs.dat_o.next = temp if use_cache else mem_wbm.dat_i

    @always_comb
    def evict_data_assign():
        tmp = 0x12345678
        for i in range(0, WAYS):
            if lru_select[i]:
                tmp = data_cache2[i]
        evict_data.next = tmp

    @always_comb
    def mem_port_assign():
        """
        Assignments to the mem_wbm interface for refill operations.
        """
        mem_wbm.addr_o.next = dc_update_addr if use_cache else cpu_wbs.addr_i
        mem_wbm.dat_o.next  = evict_data if use_cache else cpu_wbs.dat_i
        mem_wbm.sel_o.next  = modbv(0b1111)[4:] if use_cache else cpu_wbs.sel_i

    @always_comb
    def cache_mem_rw():
        for i in range(0, WAYS):
            cache_read_port[i].clk.next    = clk_i
            cache_read_port[i].addr.next   = cpu_wbs.addr_i[WAY_WIDTH:2]
            cache_read_port[i].data_i.next = cpu_wbs.dat_i
            cache_read_port[i].we.next     = not miss_w[i] and not cpu_wbs.ack_o and cpu_wbs.we_i  # TODO: check for not ACK or ACK?

    @always_comb
    def cache_mem_update():
        # Connect the mem_wbm data_i port to the cache memories.
        for i in range(0, WAYS):
            cache_update_port[i].clk.next    = clk_i
            cache_update_port[i].addr.next   = dc_update_addr[WAY_WIDTH:2]
            cache_update_port[i].data_i.next = mem_wbm.dat_i
            cache_update_port[i].we.next     = lru_select[i] and mem_wbm.ack_i

    @always_comb
    def wbs_cpu_flags():
        cpu_err.next  = mem_wbm.err_i
        cpu_wait.next = miss_w_and or not (state == dc_states.READ or state == dc_states.WRITE) if use_cache else not mem_wbm.ack_i
        cpu_busy.next = False

    @always_comb
    def wbm_mem_flags():
        mem_read.next  = fetch if use_cache else not cpu_wbs.we_i
        mem_write.next = evict if use_cache else cpu_wbs.we_i
        mem_rmw.next   = False

    # Generate the wishbone interfaces
    wbs_cpu = WishboneSlaveGenerator(clk_i, rst_i, cpu_wbs, cpu_busy, cpu_err, cpu_wait).gen_wbs()  # noqa
    wbm_mem = WishboneMasterGenerator(clk_i, rst_i, mem_wbm, mem_read, mem_write, mem_rmw).gen_wbm()  # noqa

    # Instantiate tag memory
    tag_mem = RAM_DP(tag_rw_port, tag_flush_port, A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)  # noqa

    # Instantiate main memory (Cache)
    cache_mem = [RAM_DP(cache_read_port[i], cache_update_port[i], A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for i in range(0, WAYS)]  # noqa

    # LRU calculation
    lru_m = CacheLRU(current_lru, access_lru,  update_lru,  lru_pre,  lru_post, NUMWAYS=WAYS)  # noqa

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
