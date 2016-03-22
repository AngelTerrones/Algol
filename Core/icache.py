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
    :param cpu:         CPU slave interface (Wishbone Interconnect to master port)
    :param mem:         Memory master interface (Wishbone Interconnect to slave port)
    :param invalidate:  Enable flush cache
    :param D_WIDTH:     Data width
    :param BLOCK_WIDTH: Address width for byte access inside a block line
    :param SET_WIDTH:   Address width for line access inside a block
    :param WAYS:        Number of ways for associative cache (Minimum: 2)
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
    # --------------------------------------------------------------------------
    ic_states = enum('IDLE',
                     'READ',
                     'FETCH',
                     'FLUSH',
                     'FLUSH_LAST')

    cpu_wbs            = WishboneSlave(cpu)
    mem_wbm            = WishboneMaster(mem)
    cpu_busy           = Signal(False)
    cpu_err            = Signal(False)
    cpu_wait           = Signal(False)
    mem_read           = Signal(False)
    mem_write          = Signal(False)
    mem_rmw            = Signal(False)

    tag_rw_port        = [RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WAY_WIDTH) for i in range(WAYS)]
    tag_flush_port     = [RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WAY_WIDTH) for i in range(WAYS)]
    tag_lru_rw_port    = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAG_LRU_WIDTH)
    tag_lru_flush_port = RAMIOPort(A_WIDTH=SET_WIDTH, D_WIDTH=TAG_LRU_WIDTH)
    cache_read_port    = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    cache_update_port  = [RAMIOPort(A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for _ in range(0, WAYS)]
    data_cache         = [cache_read_port[i].data_o for i in range(0, WAYS)]

    state              = Signal(ic_states.IDLE)
    n_state            = Signal(ic_states.IDLE)

    busy               = Signal(False)

    miss               = Signal(False)
    miss_w             = Signal(modbv(0)[WAYS:])
    miss_w_and         = Signal(False)
    final_fetch        = Signal(False)
    final_flush        = Signal(False)

    lru_select         = Signal(modbv(0)[WAYS:])
    current_lru        = Signal(modbv(0)[TAG_LRU_WIDTH:])
    update_lru         = Signal(modbv(0)[TAG_LRU_WIDTH:])
    access_lru         = Signal(modbv(0)[WAYS:])
    lru_pre            = Signal(modbv(0)[WAYS:])
    lru_post           = Signal(modbv(0)[WAYS:])

    # tag in/out signals: For data assignment
    tag_in             = [Signal(modbv(0)[TAGMEM_WAY_WIDTH:]) for _ in range(0, WAYS)]
    tag_out            = [Signal(modbv(0)[TAGMEM_WAY_WIDTH:]) for _ in range(0, WAYS)]
    lru_in             = Signal(modbv(0)[TAG_LRU_WIDTH:])
    lru_out            = Signal(modbv(0)[TAG_LRU_WIDTH:])
    tag_we             = Signal(False)

    # refill signals
    refill_addr        = Signal(modbv(0)[LIMIT_WIDTH:])
    refill_valid       = Signal(False)
    n_refill_addr      = Signal(modbv(0)[LIMIT_WIDTH:])
    n_refill_valid     = Signal(False)

    # flush signals
    flush_addr         = Signal(modbv(0)[SET_WIDTH:])
    flush_we           = Signal(False)
    n_flush_addr       = Signal(modbv(0)[SET_WIDTH:])
    n_flush_we         = Signal(False)

    @always_comb
    def assignments():
        final_fetch.next        = (refill_addr[BLOCK_WIDTH:] == modbv(~3)[BLOCK_WIDTH:]) and mem_wbm.ack_i and mem_wbm.stb_o and mem_wbm.cyc_o
        lru_select.next         = lru_pre
        current_lru.next        = lru_out
        access_lru.next         = ~miss_w
        busy.next               = state != ic_states.IDLE
        final_flush.next        = flush_addr == 0

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
        """
        Vector reduce: check for full miss.
        """
        value = True
        for i in range(0, WAYS):
            value = value and miss_w[i]
        miss_w_and.next = value

    @always_comb
    def miss_check_3():
        """
        Check for valid wishbone cycle, and full miss.
        """
        valid_read = cpu_wbs.cyc_i and cpu_wbs.stb_i and not cpu_wbs.we_i
        miss.next  = miss_w_and and valid_read and not invalidate

    trwp_clk    = [tag_rw_port[i].clk for i in range(WAYS)]
    trwp_addr   = [tag_rw_port[i].addr for i in range(WAYS)]
    trwp_data_i = [tag_rw_port[i].data_i for i in range(WAYS)]
    trwp_data_o = [tag_rw_port[i].data_o for i in range(WAYS)]
    trwp_we     = [tag_rw_port[i].we for i in range(WAYS)]

    @always_comb
    def tag_rport():
        """
        Connect to the Tag memory's R/W port.
        This includes the lru data.
        """
        for i in range(WAYS):
            trwp_clk[i].next    = clk_i
            trwp_addr[i].next   = cpu_wbs.addr_i[WAY_WIDTH:BLOCK_WIDTH]
            trwp_data_i[i].next = tag_in[i]
            trwp_we[i].next     = tag_we
            tag_out[i].next     = trwp_data_o[i]
        # LRU memory
        tag_lru_rw_port.clk.next    = clk_i
        tag_lru_rw_port.data_i.next = lru_in
        lru_out.next                = tag_lru_rw_port.data_o
        tag_lru_rw_port.addr.next   = cpu_wbs.addr_i[WAY_WIDTH:BLOCK_WIDTH]
        tag_lru_rw_port.we.next     = tag_we

    @always_comb
    def next_state_logic():
        """
        Cache FSM. Set the next state.
        """
        n_state.next = state
        if state == ic_states.IDLE:
            if invalidate:
                # cache flush
                n_state.next = ic_states.FLUSH
            elif cpu_wbs.cyc_i and not cpu_wbs.we_i:
                # miss: refill line
                n_state.next = ic_states.READ
        elif state == ic_states.READ:
            if not miss:
                # miss: refill line
                n_state.next = ic_states.IDLE
            else:
                n_state.next = ic_states.FETCH
        elif state == ic_states.FETCH:
            # fetch a line from memory
            if final_fetch:
                n_state.next = ic_states.IDLE
        elif state == ic_states.FLUSH:
            # invalidate tag memory
            if final_flush:
                n_state.next = ic_states.FLUSH_LAST
            else:
                n_state.next = ic_states.FLUSH
        elif state == ic_states.FLUSH_LAST:
            # last cycle for flush
            n_state.next = ic_states.IDLE

    @always(clk_i.posedge)
    def update_state():
        """
        Register the next state.
        """
        if rst_i:
            state.next = ic_states.FLUSH
        else:
            state.next = n_state

    @always_comb
    def fetch_fsm():
        """
        FSM for fetching data from the cache.
        This handles the fetch address.
        """
        n_refill_addr.next  = refill_addr
        n_refill_valid.next = False  # refill_valid

        if state == ic_states.IDLE:
            if invalidate:
                n_refill_valid.next = False
        elif state == ic_states.READ:
            if miss:
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

        if state == ic_states.IDLE:
            if invalidate:
                tag_we.next = False
        elif state == ic_states.READ:
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
        """
        Handles the address for flush operations.
        """
        n_flush_we.next   = False
        n_flush_addr.next = flush_addr

        if state == ic_states.IDLE:
            if invalidate:
                n_flush_addr.next = modbv(-1)[SET_WIDTH:]
                n_flush_we.next   = True
        elif state == ic_states.FLUSH:
            n_flush_addr.next = flush_addr - modbv(1)[SET_WIDTH:]
            n_flush_we.next   = True
        elif state == ic_states.FLUSH_LAST:
            n_flush_we.next = False

    @always(clk_i.posedge)
    def update_flush():
        if rst_i:
            flush_addr.next = modbv(-1)[SET_WIDTH:]
            flush_we.next   = False
        else:
            flush_addr.next = n_flush_addr
            flush_we.next   = n_flush_we

    tfp_clk    = [tag_flush_port[i].clk for i in range(WAYS)]
    tfp_addr   = [tag_flush_port[i].addr for i in range(WAYS)]
    tfp_data_i = [tag_flush_port[i].data_i for i in range(WAYS)]
    tfp_we     = [tag_flush_port[i].we for i in range(WAYS)]

    @always_comb
    def tag_port_assign():
        """
        Connect to the Tag memory's flush port.
        This includes the lru data.
        """
        for i in range(WAYS):
            tfp_clk[i].next    = clk_i
            tfp_addr[i].next   = flush_addr
            tfp_data_i[i].next = modbv(0)[TAGMEM_WAY_WIDTH:]
            tfp_we[i].next     = flush_we
        # connect to the LRU memory
        tag_lru_flush_port.clk.next    = clk_i
        tag_lru_flush_port.addr.next   = flush_addr
        tag_lru_flush_port.data_i.next = modbv(0)[TAG_LRU_WIDTH:]
        tag_lru_flush_port.we.next     = flush_we

    @always_comb
    def cpu_data_assign():
        """
        Assignments to the cpu interface: dat_o.
        """
        # cpu data_in assignment: instruction.
        temp = data_cache[0]
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

    # To Verilog
    crp_clk    = [cache_read_port[i].clk for i in range(0, WAYS)]
    crp_addr   = [cache_read_port[i].addr for i in range(0, WAYS)]
    crp_data_i = [cache_read_port[i].data_i for i in range(0, WAYS)]
    crp_we     = [cache_read_port[i].we for i in range(0, WAYS)]

    @always_comb
    def cache_mem_r():
        """
        Connect to the Cache memory's R/W port.
        """
        for i in range(0, WAYS):
            crp_clk[i].next    = clk_i
            crp_addr[i].next   = cpu_wbs.addr_i[WAY_WIDTH:2]
            crp_data_i[i].next = 0xAABBCCDD
            crp_we[i].next     = False

    # To Verilog
    cup_clk    = [cache_update_port[i].clk for i in range(0, WAYS)]
    cup_addr   = [cache_update_port[i].addr for i in range(0, WAYS)]
    cup_data_i = [cache_update_port[i].data_i for i in range(0, WAYS)]
    cup_we     = [cache_update_port[i].we for i in range(0, WAYS)]

    @always_comb
    def cache_mem_update():
        """
        Connect to the Cache memory's refill port.
        """
        for i in range(0, WAYS):
            # ignore data_o from update port
            cup_clk[i].next    = clk_i
            cup_addr[i].next   = refill_addr[WAY_WIDTH:2]
            cup_data_i[i].next = mem_wbm.dat_i
            cup_we[i].next     = lru_select[i] & mem_wbm.ack_i

    @always_comb
    def wbs_cpu_flags():
        """
        Wishbone slave trigger signals.
        """
        cpu_err.next  = mem_wbm.err_i
        cpu_wait.next = miss_w_and or state != ic_states.READ
        cpu_busy.next = busy

    @always_comb
    def wbm_mem_flags():
        """
        Wishbone master trigger signals.
        """
        mem_read.next  = refill_valid and not final_fetch
        mem_write.next = False
        mem_rmw.next   = False

    # Generate the wishbone interfaces
    wbs_cpu = WishboneSlaveGenerator(clk_i, rst_i, cpu_wbs, cpu_busy, cpu_err, cpu_wait).gen_wbs()  # noqa
    wbm_mem = WishboneMasterGenerator(clk_i, rst_i, mem_wbm, mem_read, mem_write, mem_rmw).gen_wbm()  # noqa

    # Instantiate tag memories
    tag_mem = [RAM_DP(tag_rw_port[i], tag_flush_port[i], A_WIDTH=SET_WIDTH, D_WIDTH=TAGMEM_WAY_WIDTH) for i in range(WAYS)]  # noqa
    tag_lru = RAM_DP(tag_lru_rw_port, tag_lru_flush_port, A_WIDTH=SET_WIDTH, D_WIDTH=TAG_LRU_WIDTH)  # noqa

    # instantiate main memory (cache)
    cache_mem = [RAM_DP(cache_read_port[i], cache_update_port[i], A_WIDTH=WAY_WIDTH - 2, D_WIDTH=D_WIDTH) for i in range(0, WAYS)]  # noqa

    # LRU unit.
    lru_m = CacheLRU(current_lru, access_lru, update_lru, lru_pre, lru_post, NUMWAYS=WAYS)  # noqa

    return instances()

# Local Variables:
# flycheck-flake8-maximum-line-length: 300
# flycheck-flake8rc: ".flake8rc"
# End:
