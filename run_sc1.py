#!/usr/bin/env python3
"""
Load and run an SC-1 program from the command line.

Usage:
  ./run_sc1.py sample.sc1
  ./run_sc1.py examples/counter.sc1 --entry 0 --max-steps 1000000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sc1 import (
    InterruptController,
    MAX_MEM_SIZE,
    Memory,
    PygameTextConsole,
    SC1CPU,
    StorageDevice,
    StdoutDevice,
    parse_program_lines,
)


def _int_auto(s: str) -> int:
    return int(s, 0)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SC-1: load a program into memory and run the CPU.")
    p.add_argument("program", type=Path, help=".sc1 or text program file (one instruction per line)")
    p.add_argument(
        "--mem-size",
        type=_int_auto,
        default=MAX_MEM_SIZE,
        metavar="BYTES",
        help=f"memory size in bytes (1..{MAX_MEM_SIZE}; default: {MAX_MEM_SIZE})",
    )
    p.add_argument(
        "--entry",
        type=_int_auto,
        default=0,
        metavar="ADDR",
        help="memory address where execution starts (decimal or 0x...; default: 0)",
    )
    p.add_argument(
        "--max-steps",
        type=int,
        default=1_000_000,
        metavar="N",
        help="maximum CPU steps (infinite-loop guard)",
    )
    p.add_argument(
        "--mem-u16",
        type=_int_auto,
        action="append",
        default=[],
        metavar="ADDR",
        help="after run, print the 16-bit word at this address (may be repeated)",
    )
    p.add_argument(
        "--pygame",
        action="store_true",
        help="render interrupt output in a pygame window (requires pygame)",
    )
    p.add_argument(
        "--storage-dir",
        type=Path,
        default=Path("storage"),
        metavar="DIR",
        help="host directory for disk syscalls (default: ./storage)",
    )
    args = p.parse_args(argv)

    path: Path = args.program
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    try:
        prog_bytes = parse_program_lines(text)
    except ValueError as e:
        print(f"Error: program parse — {e}", file=sys.stderr)
        return 1

    try:
        mem = Memory(size=args.mem_size)
    except (TypeError, ValueError) as e:
        print(f"Error: invalid --mem-size — {e}", file=sys.stderr)
        return 1

    if args.entry < 0 or args.entry >= mem.size:
        print(f"Error: invalid --entry: {args.entry} (mem-size={mem.size})", file=sys.stderr)
        return 1
    if len(prog_bytes) > mem.size - args.entry:
        print("Error: program exceeds memory bounds.", file=sys.stderr)
        return 1

    mem.load_bytes(args.entry, prog_bytes)
    devices = []
    if args.pygame:
        try:
            devices.append(PygameTextConsole())
        except ModuleNotFoundError as e:
            print(f"Error: pygame not installed — {e}", file=sys.stderr)
            return 1
    devices.append(StorageDevice(root=args.storage_dir))
    devices.append(StdoutDevice())
    ic = InterruptController(devices=devices)

    cpu = SC1CPU(mem, interrupts=ic)
    cpu.reset(entry=args.entry)

    try:
        # If pygame is enabled, run step-by-step so the window stays responsive.
        if args.pygame:
            steps = 0
            while not cpu.halted and steps < args.max_steps:
                cpu.step()
                ic.tick()
                steps += 1
            if steps >= args.max_steps and not cpu.halted:
                raise RuntimeError("Step limit exceeded (maybe infinite loop).")
        else:
            steps = cpu.run(max_steps=args.max_steps)
    except RuntimeError as e:
        print(f"Error: CPU — {e}", file=sys.stderr)
        return 1

    print(f"File: {path}")
    print(f"Memory size: {mem.size} bytes")
    print(f"Bytes loaded: {len(prog_bytes)} (entry address 0x{args.entry:04X})")
    print(f"Steps: {steps}")
    print(f"HALT: {cpu.halted}  ACC=0x{cpu.acc:04X}  X=0x{cpu.x:04X}  PC=0x{cpu.pc:04X}")
    for addr in args.mem_u16:
        a = addr & 0xFFFF
        try:
            w = mem.read_u16(a)
        except IndexError as e:
            print(f"mem[0x{a:04X}] (u16) = <out of bounds> ({e})")
        else:
            print(f"mem[0x{a:04X}] (u16) = 0x{w:04X} ({w})")

    if args.pygame:
        print("Program halted. Close the pygame window to exit.")
        try:
            while True:
                ic.tick()
        except KeyboardInterrupt:
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
