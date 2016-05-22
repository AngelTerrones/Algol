![logo](Documentation/img/logo.png)

Algol is a CPU core that implements the [RISC-V RV32IM Instruction Set](http://riscv.org/).

Tools for development (gcc, binutils, etc.) can be obtained from the 
[RISC-V website](http://riscv.org/software-tools/). The 
[verification suit](http://riscv.org/software-tools/riscv-tests/) expect a `riscv64-unknown-elf-` 
toolchain installed in `$PATH` (see [build instructions](http://riscv.org/software-tools/#quickstart)).

Algol is free and open hardware licensed under the [MIT license](https://en.wikipedia.org/wiki/MIT_License).

## Table of Contents
- [Processor Details](#processor-details)
- [Getting Started](#getting-started)
- [Software Details](#software-details)
- [Directory Layout](#directory-layout)
- [Build the toolchain](#build-the-toolchain)
- [License](#license)

## Processor Details

- Single-issue in-order 5-stage pipeline with full forwarding and hazard detection.
- Harvard architecture, with separate instruction and data ports.
- RISC-V RV32IM ISA.
- Configurable L1 instruction cache, N-way Associative.
- Configurable L1 data cache, N-way Associative, write-back, write-allocate.
- No MMU.
- No FPU. Software-base floating point support (toolchain).
- Multi-cycle hardware divider.
- 5-stage pipeline hardwate multiplier.
- Support for the Machine and User levels. 
- Wishbone interface.
- Designed completely in python using [MyHDL](http://myhdl.org/).

The project includes only the standalone RISC-V core.

## Getting Started

This repository provides all you need to simulate and synthesize the processor:

- Standalone processor.
- Simulation memory using BRAM, modelled in python.
- Scripts (python) to simulate the modules, and the cpu.

## Software Details

- Simulation done in python, using [MyHDL](http://myhdl.org/).
- Software [toolchain](http://riscv.org/software-tools/) using gcc.
- [Verification suit](http://riscv.org/software-tools/riscv-tests/) written in assembly:

## Directory Layout

#### README.md

This file.

#### main

Main script for simulation and conversion to verilog.

#### Documentation/

LaTeX source files for the CPU manual.

#### Core/

Python files describing the Algol CPU.

#### Simulation/

Test environment for the Algol CPU and its modules.

##### core/

Testbench for CPU verification. Uses the pure-python MyHDL simulator.

##### modules/

Testbenchs for module verification. Uses the pure-python MyHDL simulator.

##### tests/

Basic instruction-level tests. Taken from [riscv-tests](http://riscv.org/software-tools/riscv-tests/) 
(git rev ac467e1).


## CPU Verification

To verify the processor, use the `main` script.

Type `./main -h` to get the main help:

```
usage: main [-h] {module,core,compile_tests,clean_tests,to_verilog} ...

Algol (RISC-V processor). Main simulation script.

optional arguments:
  -h, --help            show this help message and exit

Sub-commands:
  Available functions

  {module,core,compile_tests,clean_tests,to_verilog}
                        Description
    module              Run tests for modules
    core                Run assembler tests in the RV32 processor
    compile_tests       Compile all the RISC-V tests
    clean_tests         Clean the RISC-V test folder
    to_verilog          Convert design to Verilog
```

Type `./main core -h` to get the help for the `core` sub-command:

```
usage: main core [-h] (-f FILE | -a) [--vcd]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Run a specific test
  -a, --all             Run all tests
  --vcd                 Generate VCD files
```


To verify the CPU using a single ISA test (using `pytest`):

```
./main core -f Simulation/tests/rv32ui-p-lw.hex
Test session starts (platform: linux, Python 3.5.1, pytest 2.9.1, pytest-sugar 0.5.1)
cachedir: .cache
rootdir: /home/angelterrones/Projects/Algol, inifile:
plugins: sugar-0.5.1, cov-2.2.1

 Simulation/core/test_core.pytest_core[131072-Simulation/tests/rv32ui-p-lw.hex-16-False] ✓                                                                 100% ██████████

Results (6.81s):
       1 passed
```

To verify the CPU using all the `rv32ui-p-` tests: `./main core -a`

## Build the toolchain

The default settings in the [riscv-tools](https://github.com/riscv/riscv-tools) build
scripts will build a compiler, assembler and linker that can target any RISC-V ISA.

The following commands will build the RISC-V gnu toolchain and libraries, and install it in `/opt/riscv`:

    # Ubuntu packages needed:
    sudo apt-get install autoconf automake autotools-dev curl libmpc-dev libmpfr-dev \
            libgmp-dev gawk build-essential bison flex texinfo gperf

    sudo mkdir /opt/riscv
    sudo chown $USER /opt/riscv

    cd /folder/to/download/toolchain
    git clone https://github.com/riscv/riscv-gnu-toolchain
    cd riscv-gnu-toolchain
    git checkout f2a2c87

    mkdir build; cd build
    ../configure --prefix=/opt/riscv
    make -j$(nproc)

The commands will all be named using the prefix `riscv64-unknown-elf-`.

*Note: This instructions are for git rev f2a2c87 (2016-02-27) of riscv-gnu-toolchain.*

## License

Copyright (c) 2016 Angel Terrones (<angelterrones@gmail.com>).

Release under the [MIT License](MITlicense.md).

[1]: http://iverilog.icarus.com
