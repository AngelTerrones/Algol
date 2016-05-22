#=======================================================================
# Makefile for riscv-tests/isa
#-----------------------------------------------------------------------

isa_src_dir := ./isa

include $(isa_src_dir)/rv64ui/Makefrag
include $(isa_src_dir)/rv64uf/Makefrag
include $(isa_src_dir)/rv64si/Makefrag
include $(isa_src_dir)/rv64mi/Makefrag
include $(isa_src_dir)/rv32ui/Makefrag
include $(isa_src_dir)/rv32si/Makefrag
include $(isa_src_dir)/rv32mi/Makefrag

default: all

#--------------------------------------------------------------------
# Build rules
#--------------------------------------------------------------------

RISCV_PREFIX=riscv64-unknown-elf-
RISCV_GCC = $(RISCV_PREFIX)gcc
ENTROPY = -DENTROPY=$(shell echo $$$$)
RISCV_GCC_OPTS = $(ENTROPY) -static -mcmodel=medany -fvisibility=hidden -nostdlib -nostartfiles
RISCV_OBJDUMP = $(RISCV_PREFIX)objdump --disassemble-all --disassemble-zeroes --section=.text --section=.text.startup --section=.text.init --section=.data
RISCV_SIM = spike
MAKE_HEX ?= $(isa_src_dir)/../../../Software/utils/makehex.py

vpath %.S $(isa_src_dir)

#------------------------------------------------------------
# Build assembly tests

%.hex: %
	$(RISCV_PREFIX)objcopy -O binary $< $<.bin
	python3 $(MAKE_HEX) $<.bin 16384 0x100 4 > $@
	rm $<.bin

%.dump: %
	$(RISCV_OBJDUMP) $< > $@


define compile_template

$$($(1)_p_tests): $(1)-p-%: $(1)/%.S
	$$(RISCV_GCC) $(2) $$(RISCV_GCC_OPTS) -I$(isa_src_dir)/../env/p -I$(isa_src_dir)/macros/scalar -T$(isa_src_dir)/../env/p/link.ld $$< -o $$@
$(1)_tests += $$($(1)_p_tests)

$$($(1)_pt_tests): $(1)-pt-%: $(1)/%.S
	$$(RISCV_GCC) $(2) $$(RISCV_GCC_OPTS) -I$(isa_src_dir)/../env/pt -I$(isa_src_dir)/macros/scalar -T$(isa_src_dir)/../env/pt/link.ld $$< -o $$@
$(1)_tests += $$($(1)_pt_tests)

$$($(1)_pm_tests): $(1)-pm-%: $(1)/%.S
	$$(RISCV_GCC) $(2) $$(RISCV_GCC_OPTS) -I$(isa_src_dir)/../env/pm -I$(isa_src_dir)/macros/scalar -T$(isa_src_dir)/../env/pm/link.ld $$< -o $$@
$(1)_tests += $$($(1)_pm_tests)

$$($(1)_v_tests): $(1)-v-%: $(1)/%.S
	$$(RISCV_GCC) $(2) $$(RISCV_GCC_OPTS) -std=gnu99 -O2 -I$(isa_src_dir)/../env/v -I$(isa_src_dir)/macros/scalar -T$(isa_src_dir)/../env/v/link.ld $(isa_src_dir)/../env/v/entry.S $(isa_src_dir)/../env/v/vm.c $$< -lc -o $$@
$(1)_tests += $$($(1)_v_tests)

$(1)_tests_dump = $$(addsuffix .dump, $$($(1)_tests))
$(1)_tests_hex = $$(addsuffix .hex, $$($(1)_tests))

$(1): $$($(1)_tests_dump) $$($(1)_tests_hex)

.PHONY: $(1)

tests += $$($(1)_tests)

endef

$(eval $(call compile_template,rv32ui,-m32))
$(eval $(call compile_template,rv32si,-m32))
$(eval $(call compile_template,rv32mi,-m32))

tests_dump = $(addsuffix .dump, $(tests))
tests_hex = $(addsuffix .hex, $(tests))

junk += $(tests) $(tests_dump) $(tests_hex) #$(tests_out) $(tests32_out)

#------------------------------------------------------------
# Default

all: $(tests_dump) $(tests_hex)

#------------------------------------------------------------
# Clean up

clean:
	rm -rf $(junk)
