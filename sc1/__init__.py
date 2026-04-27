"""
SC-1 — 16-bit microcomputer (instruction set, 64 KiB memory, one instruction per program line).
"""

from sc1.cpu import SC1CPU
from sc1.instructions import MNEMONIC, Opcode
from sc1.interrupts import InterruptController, PygameTextConsole, StdoutDevice, StorageDevice
from sc1.memory import MAX_MEM_SIZE, Memory
from sc1.program import parse_program_lines, program_lines_to_bytes

__all__ = [
    "MAX_MEM_SIZE",
    "MNEMONIC",
    "Memory",
    "Opcode",
    "InterruptController",
    "PygameTextConsole",
    "SC1CPU",
    "StorageDevice",
    "StdoutDevice",
    "parse_program_lines",
    "program_lines_to_bytes",
]
