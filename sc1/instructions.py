"""
SC-1 — 16-bit microcomputer instruction set.

Each instruction is one or more bytes; multi-byte fields are little-endian.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Final


class Opcode(IntEnum):
    """Single-byte opcodes (0–255)."""

    NOP = 0x00
    LDA_IMM = 0x01  # ACC <- immediate (next 2 bytes)
    LDA_MEM = 0x02  # ACC <- mem[addr] (word; next 2 bytes are address)
    STA = 0x03      # mem[addr] <- ACC (word)
    ADD_IMM = 0x04
    SUB_IMM = 0x05
    AND_IMM = 0x06
    OR_IMM = 0x07
    XOR_IMM = 0x08
    LDX_IMM = 0x09  # X <- immediate 16-bit
    LDA_X = 0x0A    # ACC <- mem[X] (word; X is address)
    STA_X = 0x0B    # mem[X] <- ACC (word)
    JMP = 0x0C      # PC <- addr (byte address)
    JZ = 0x0D       # if ACC==0 then PC <- addr
    JNZ = 0x0E      # if ACC!=0 then PC <- addr
    HALT = 0x0F

    # Register/memory and indirect-friendly ops (for general computation)
    LDX_MEM = 0x10   # X <- mem[addr] (word)
    STX = 0x11       # mem[addr] <- X (word)
    ADDX_IMM = 0x12  # X <- X + imm16
    INX = 0x13       # X <- X + 1
    DEX = 0x14       # X <- X - 1
    TAX = 0x15       # X <- ACC
    TXA = 0x16       # ACC <- X
    ADD_MEM = 0x17   # ACC <- ACC + mem[addr] (word)
    SUB_MEM = 0x18   # ACC <- ACC - mem[addr] (word)
    ADD_X = 0x19     # ACC <- ACC + mem[X] (word)
    SUB_X = 0x1A     # ACC <- ACC - mem[X] (word)

    # Stack / calls
    PUSH_ACC = 0x20  # push ACC (u16) to stack
    POP_ACC = 0x21   # pop u16 from stack into ACC
    PUSH_X = 0x22    # push X (u16) to stack
    POP_X = 0x23     # pop u16 from stack into X
    LSP_IMM = 0x24   # SP <- imm16
    CALL = 0x25      # push return PC; PC <- addr
    RET = 0x26       # PC <- pop return PC

    # Interrupt / syscalls
    INT = 0x30       # software interrupt with 8-bit ID (next 1 byte)


# Short human-readable names (assembler-style labels)
MNEMONIC: Final[dict[str, Opcode]] = {
    "NOP": Opcode.NOP,
    "LDA": Opcode.LDA_IMM,  # immediate; separate mnemonic for mem
    "LDA#": Opcode.LDA_IMM,
    "LDA@": Opcode.LDA_MEM,
    "STA": Opcode.STA,
    "ADD": Opcode.ADD_IMM,
    "ADD@": Opcode.ADD_MEM,
    "SUB": Opcode.SUB_IMM,
    "SUB@": Opcode.SUB_MEM,
    "AND": Opcode.AND_IMM,
    "OR": Opcode.OR_IMM,
    "XOR": Opcode.XOR_IMM,
    "LDX": Opcode.LDX_IMM,
    "LDX@": Opcode.LDX_MEM,
    "STX": Opcode.STX,
    "ADDX": Opcode.ADDX_IMM,
    "INX": Opcode.INX,
    "DEX": Opcode.DEX,
    "TAX": Opcode.TAX,
    "TXA": Opcode.TXA,
    "LDA(X)": Opcode.LDA_X,
    "STA(X)": Opcode.STA_X,
    "ADD(X)": Opcode.ADD_X,
    "SUB(X)": Opcode.SUB_X,
    "PUSH": Opcode.PUSH_ACC,
    "POP": Opcode.POP_ACC,
    "PUSHX": Opcode.PUSH_X,
    "POPX": Opcode.POP_X,
    "LSP": Opcode.LSP_IMM,
    "CALL": Opcode.CALL,
    "RET": Opcode.RET,
    "INT": Opcode.INT,
    "JMP": Opcode.JMP,
    "JZ": Opcode.JZ,
    "JNZ": Opcode.JNZ,
    "HALT": Opcode.HALT,
}

# Extra bytes after opcode (for PC advance)
EXTRA_BYTES: Final[dict[Opcode, int]] = {
    Opcode.NOP: 0,
    Opcode.LDA_IMM: 2,
    Opcode.LDA_MEM: 2,
    Opcode.STA: 2,
    Opcode.ADD_IMM: 2,
    Opcode.SUB_IMM: 2,
    Opcode.AND_IMM: 2,
    Opcode.OR_IMM: 2,
    Opcode.XOR_IMM: 2,
    Opcode.LDX_IMM: 2,
    Opcode.LDA_X: 0,
    Opcode.STA_X: 0,
    Opcode.JMP: 2,
    Opcode.JZ: 2,
    Opcode.JNZ: 2,
    Opcode.HALT: 0,

    Opcode.LDX_MEM: 2,
    Opcode.STX: 2,
    Opcode.ADDX_IMM: 2,
    Opcode.INX: 0,
    Opcode.DEX: 0,
    Opcode.TAX: 0,
    Opcode.TXA: 0,
    Opcode.ADD_MEM: 2,
    Opcode.SUB_MEM: 2,
    Opcode.ADD_X: 0,
    Opcode.SUB_X: 0,

    Opcode.PUSH_ACC: 0,
    Opcode.POP_ACC: 0,
    Opcode.PUSH_X: 0,
    Opcode.POP_X: 0,
    Opcode.LSP_IMM: 2,
    Opcode.CALL: 2,
    Opcode.RET: 0,

    Opcode.INT: 1,
}


def instruction_length(op: int) -> int:
    """Total instruction size in bytes, including opcode."""
    o = Opcode(op)
    return 1 + EXTRA_BYTES[o]
