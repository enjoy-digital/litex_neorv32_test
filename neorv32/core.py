#
# This file is part of LiteX.
#
# Copyright (c) 2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.cores.cpu import CPU, CPU_GCC_TRIPLE_RISCV32

# Variants -----------------------------------------------------------------------------------------

CPU_VARIANTS = ["standard"]

# GCC Flags ----------------------------------------------------------------------------------------

GCC_FLAGS = {
    #                               /-------- Base ISA
    #                               |/------- Hardware Multiply + Divide
    #                               ||/----- Atomics
    #                               |||/---- Compressed ISA
    #                               ||||/--- Single-Precision Floating-Point
    #                               |||||/-- Double-Precision Floating-Point
    #                               imacfd
    "standard":         "-march=rv32i     -mabi=ilp32",
}

# NEORV32 ------------------------------------------------------------------------------------------

class NEORV32(CPU):
    family               = "riscv"
    name                 = "neorv32"
    human_name           = "NEORV32"
    variants             = CPU_VARIANTS
    data_width           = 32
    endianness           = "little"
    gcc_triple           = CPU_GCC_TRIPLE_RISCV32
    linker_output_format = "elf32-littleriscv"
    nop                  = "nop"
    io_regions           = {0x80000000: 0x80000000} # Origin, Length.

    # GCC Flags.
    @property
    def gcc_flags(self):
        flags =  GCC_FLAGS[self.variant]
        flags += " -D__neorv32__ "
        return flags

    def __init__(self, platform, variant="standard"):
        self.platform     = platform
        self.variant      = variant
        self.reset        = Signal()
        self.ibus         = ibus = wishbone.Interface()
        self.dbus         = dbus = wishbone.Interface()
        self.periph_buses = [ibus, dbus] # Peripheral buses (Connected to main SoC's bus).
        self.memory_buses = []           # Memory buses (Connected directly to LiteDRAM).

        # # #

        self.cpu_params = dict()

        # Add Verilog sources
        self.add_sources(platform)

    def set_reset_address(self, reset_address):
        self.reset_address = reset_address
        self.cpu_params.update(p_RESET_PC=reset_address)

    @staticmethod
    def add_sources(platform):
        # List VHDL sources.
        sources = [
            "neorv32_package.vhd",                  # Main CPU & Processor package file.
            "neorv32_cpu.vhd",                      # CPU top entity.
                "neorv32_cpu_alu.vhd",              # Arithmetic/logic unit.
                    "neorv32_cpu_cp_bitmanip.vhd",  # Bit-manipulation co-processor.
                    "neorv32_cpu_cp_cfu.vhd",       # Custom instructions co-processor.
                    "neorv32_cpu_cp_fpu.vhd",       # Single-precision FPU co-processor.
                    "neorv32_cpu_cp_muldiv.vhd",    # Integer multiplier/divider co-processor.
                    "neorv32_cpu_cp_shifter.vhd",   # Base ISA shifter unit.
                "neorv32_cpu_bus.vhd",              # Instruction and data bus interface unit.
                "neorv32_cpu_control.vhd",          # CPU control and CSR system.
                    "neorv32_cpu_decompressor.vhd", # Compressed instructions decoder.
                "neorv32_cpu_regfile.vhd",          # Data register file.
        ]

        # Download VHDL sources (if not already present).
        os.makedirs("rtl", exist_ok=True)
        for source in sources:
            if not os.path.exists(f"rtl/{source}"):
                os.system(f"wget https://raw.githubusercontent.com/stnolting/neorv32/main/rtl/core/{source} -P rtl")

        # Convert VHDL to Verilog through GHDL/Yosys.
        from litex.build import tools
        import subprocess
        cdir = os.path.dirname(__file__)
        ys = []
        ys.append("ghdl --ieee=synopsys -fexplicit -frelaxed-rules --std=08 \\")
        for source in sources:
            ys.append(os.path.join("rtl", source) + " \\")
        ys.append("-e neorv32_cpu")
        ys.append("chformal -assert -remove")
        ys.append("write_verilog {}".format(os.path.join(cdir, "neorv32.v")))
        tools.write_to_file(os.path.join(cdir, "neorv32.ys"), "\n".join(ys))
        if subprocess.call(["yosys", "-q", "-m", "ghdl", os.path.join(cdir, "neorv32.ys")]):
            raise OSError("Unable to convert NEORV32 CPU to verilog, please check your GHDL-Yosys-plugin install.")
        platform.add_source(os.path.join(cdir, "neorv32.v"))

    def do_finalize(self):
        assert hasattr(self, "reset_address")
        self.specials += Instance("neorv32_cpu", **self.cpu_params)
