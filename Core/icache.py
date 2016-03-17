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


def ICache(clk_i,
           rst_i,
           cpu,
           mem,
           invalidate,
           D_WIDTH=32,
           BLOCK_WIDTH=5,
           SET_WIDTH=9,
           WAYS=2,
           LIMIT_WIDTH=32):
    """
    The Instruction Cache module.

    :param clk:         System clock
    :param rst:         System reset
    :param invalidate:  Enable flush cache
    :param cpu:         CPU interface (Wishbone Interconnect to master port)
    :param mem:         Memory interface (Wishbone Interconnect to slave port)
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
    WAY_WIDTH            = BLOCK_WIDTH + SET_WIDTH  # cache mem_wbm address width
    TAG_WIDTH            = LIMIT_WIDTH - WAY_WIDTH  # tag size
    # width and index for tags
    TAGMEM_WAY_WIDTH     = TAG_WIDTH + 1         # Add the valid bit
    TAGMEM_WAY_VALID     = TAGMEM_WAY_WIDTH - 1  # Valid bit index
    # calculate the needed LRU bits (from mor1kx_icache.v)
    TAG_LRU_WIDTH        = (WAYS * (WAYS - 1)) >> 1  # (N*(N-1))/2
    # TAG_LRU_WIDTH_BITS = TAG_LRU_WIDTH if WAYS >= 2 else 1
    # Size of tag memory
    TAGMEM_WIDTH         = (TAGMEM_WAY_WIDTH * WAYS) + TAG_LRU_WIDTH  # width of one tag line.
    # --------------------------------------------------------------------------
    ic_states = enum('CHECK', 'FETCH', 'WAIT', 'FLUSH', 'FLUSH_LAST', encoding='one_hot')

    cpu_wbs = WishboneSlave(cpu)
    mem_wbm = WishboneMaster(mem)
    cpu_busy  = Signal(False)
    cpu_err   = Signal(False)
    cpu_wait  = Signal(False)
    mem_read  = Signal(False)
    mem_write = Signal(False)
    mem_rmw   = Signal(False)

    tag_rw_port       = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    tag_flush_port    = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)
    cache_read_port   = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    cache_update_port = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    data_cache        = [cache_read_port[i].data_o for i in range(0, WAYS)]

    state             = Signal(ic_states.CHECK)
    n_state           = Signal(ic_states.CHECK)

    busy              = Signal(False)

    miss              = Signal(False)
    miss_w            = Signal(modbv(0)[WAYS:])
    miss_w_and        = Signal(False)
    final_fetch       = Signal(False)
    final_flush       = Signal(False)

    lru_select        = Signal(modbv(0)[WAYS:])
    current_lru       = Signal(modbv(0)[TAG_LRU_WIDTH:])
    update_lru        = Signal(modbv(0)[TAG_LRU_WIDTH:])
    access_lru        = Signal(modbv(0)[WAYS:])
    lru_pre           = Signal(modbv(0)[WAYS:])
    lru_post          = Signal(modbv(0)[WAYS:])

    # tag in/out signals: For data assignment
    tag_in            = [Signal(modbv(0)[TAGMEM_WAY_WIDTH:]) for _ in range(0, WAYS)]
    tag_out           = [Signal(modbv(0)[TAGMEM_WAY_WIDTH:]) for _ in range(0, WAYS)]
    lru_in            = Signal(modbv(0)[TAG_LRU_WIDTH:])
    lru_out           = Signal(modbv(0)[TAG_LRU_WIDTH:])
    tag_we            = Signal(False)

    # refill signals
    refill_addr       = Signal(modbv(0)[LIMIT_WIDTH:])
    refill_valid      = Signal(False)
    n_refill_addr     = Signal(modbv(0)[LIMIT_WIDTH:])
    n_refill_valid    = Signal(False)

    # flush signals
    flush             = Signal(False)
    flush_addr        = Signal(modbv(0)[SET_WIDTH:])
    flush_we          = Signal(False)
    n_flush_addr      = Signal(modbv(0)[SET_WIDTH:])
    n_flush_we        = Signal(False)
    n_flush           = Signal(False)

    valid_q           = Signal(False)

    @always_comb
    def assignments():
        final_fetch.next        = (refill_addr[BLOCK_WIDTH:] == modbv(~3)[BLOCK_WIDTH:]) and mem_wbm.ack_i and mem_wbm.stb_o and mem_wbm.cyc_o
        lru_select.next         = lru_pre
        current_lru.next        = lru_out
        access_lru.next         = ~miss_w
        busy.next               = state != ic_states.CHECK
        final_flush.next        = flush_addr == 0

    @always(clk_i.posedge)
    def reg_read():
        if rst_i:
            valid_q.next = False
        else:
            valid_q.next = cpu_wbs.cyc_i and cpu_wbs.stb_i

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
        valid_read = cpu_wbs.cyc_i and cpu_wbs.stb_i and not cpu_wbs.we_i
        miss.next  = miss_w_and and valid_read and not flush and not invalidate

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

    @always(clk_i.posedge)
    def update_state():
        if rst_i:
            state.next = ic_states.FLUSH
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
                n_refill_addr.next  = concat(cpu_wbs.addr_i[LIMIT_WIDTH:BLOCK_WIDTH], modbv(0)[BLOCK_WIDTH:])
                n_refill_valid.next = True  # not mem_wbm.ready?
        elif state == ic_states.FETCH:
            n_refill_valid.next = True
            if refill_valid and mem_wbm.ack_i:
                if final_fetch:
                    n_refill_valid.next = False
                    n_refill_addr.next = 0
                else:
                    n_refill_valid.next = True
                    n_refill_addr.next  = refill_addr + modbv(4)[BLOCK_WIDTH:]

    @always(clk_i.posedge)
    def update_fetch():
        if rst_i:
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
                        tag_in[i].next = concat(True, cpu_wbs.addr_i[LIMIT_WIDTH:WAY_WIDTH])
                tag_we.next = True
            else:
                lru_in.next = update_lru
                tag_we.next = True

    @always_comb
    def flush_next_state():
        n_flush_we.next   = False
        n_flush_addr.next = flush_addr
        n_flush.next      = flush

        if state == ic_states.CHECK:
            if flush or invalidate:
                n_flush.next      = False
                n_flush_addr.next = modbv(-1)[SET_WIDTH:]
                n_flush_we.next   = True
        elif state == ic_states.FLUSH:
            n_flush_addr.next = flush_addr - modbv(1)[SET_WIDTH:]
            n_flush_we.next   = True
        elif state == ic_states.FLUSH_LAST:
            n_flush_we.next = False
        else:
            n_flush.next = invalidate

    @always(clk_i.posedge)
    def update_flush():
        if rst_i:
            flush_addr.next = modbv(-1)[SET_WIDTH:]
            flush_we.next   = False
            flush.next      = False
        else:
            flush_addr.next = n_flush_addr
            flush_we.next   = n_flush_we
            flush.next      = n_flush

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
        cpu_wbs.dat_o.next = temp

    @always_comb
    def mem_port_assign():
        """
        Assignments to the mem_wbm interface for refill operations.
        """
        mem_wbm.addr_o.next = refill_addr
        mem_wbm.dat_o.next  = 0x0BADF00D
        mem_wbm.sel_o.next  = modbv(0)[4:]
        # mem_wbm.we_o.next   = False
        # mem_wbm..next = refill_valid

    @always_comb
    def cache_mem_r():
        for i in range(0, WAYS):
            cache_read_port[i].clk.next    = clk_i
            cache_read_port[i].addr.next   = cpu_wbs.addr_i[WAY_WIDTH:2]
            cache_read_port[i].data_i.next = 0xAABBCCDD
            cache_read_port[i].we.next     = False

    @always_comb
    def cache_mem_update():
        # Connect the mem_wbm data_i port to the cache memories.
        for i in range(0, WAYS):
            # ignore data_o from update port
            cache_update_port[i].clk.next    = clk_i
            cache_update_port[i].addr.next   = refill_addr[WAY_WIDTH:2]
            cache_update_port[i].data_i.next = mem_wbm.dat_i
            cache_update_port[i].we.next     = lru_select[i] & mem_wbm.ack_i

    @always_comb
    def wbs_cpu_flags():
        cpu_err.next  = mem_wbm.err_i
        cpu_wait.next = miss_w_and or not valid_q or busy
        cpu_busy.next = busy

    @always_comb
    def wbm_mem_flags():
        mem_read.next  = refill_valid and not final_fetch
        mem_write.next = False
        mem_rmw.next   = False

    # Generate the wishbone interfaces
    wbs_cpu = WishboneSlaveGenerator(clk_i, rst_i, cpu_wbs, cpu_busy, cpu_err, cpu_wait).gen_wbs()  # noqa
    wbm_mem = WishboneMasterGenerator(clk_i, rst_i, mem_wbm, mem_read, mem_write, mem_rmw).gen_wbm()  # noqa

    # Instantiate memory
    tag_mem = RAM_DP(tag_rw_port, tag_flush_port, A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WIDTH)  # noqa

    # instantiate main memory (cache)
    cache_mem = [RAM_DP(cache_read_port[i], cache_update_port[i], A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for i in range(0, WAYS)]  # noqa

    lru_m = CacheLRU(current_lru, access_lru, update_lru, lru_pre, lru_post, NUMWAYS=WAYS)  # noqa

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
