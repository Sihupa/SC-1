"""
SC-1 CPU: 16-bit ACC and X, 16-bit PC (byte offset), NOP…HALT execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sc1.instructions import EXTRA_BYTES, Opcode
from sc1.memory import Memory
from sc1.interrupts import InterruptController


@dataclass
class SC1CPU:
    mem: Memory
    interrupts: InterruptController | None = None
    pc: int = 0
    acc: int = 0
    x: int = 0
    sp: int = 0
    halted: bool = field(default=False, init=False)

    def reset(self, entry: int = 0) -> None:
        self.pc = entry & 0xFFFF
        self.acc = 0
        self.x = 0
        # Stack grows downward. Default SP: top of memory (word-aligned).
        self.sp = self.mem.size & 0xFFFE
        self.halted = False

    def _push_u16(self, value: int) -> None:
        self.sp = (self.sp - 2) & 0xFFFF
        self.mem.write_u16(self.sp, value & 0xFFFF)

    def _pop_u16(self) -> int:
        v = self.mem.read_u16(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        return v

    def step(self) -> None:
        if self.halted:
            return
        op = self.mem.read_u8(self.pc)
        try:
            opcode = Opcode(op)
        except ValueError:
            raise RuntimeError(f"Unknown opcode 0x{op:02X} @ PC={self.pc}")

        extra = EXTRA_BYTES[opcode]
        pc_next = self.pc + 1 + extra

        def imm16() -> int:
            lo = self.mem.read_u8(self.pc + 1)
            hi = self.mem.read_u8(self.pc + 2)
            return lo | (hi << 8)

        def addr16() -> int:
            return imm16()

        def imm8() -> int:
            return self.mem.read_u8(self.pc + 1)

        if opcode == Opcode.NOP:
            # No operation.
            pass
        elif opcode == Opcode.LDA_IMM:
            # ACC <- 16-bit immediate (bytes after opcode).
            self.acc = imm16()
        elif opcode == Opcode.LDA_MEM:
            # ACC <- 16-bit word at absolute address.
            self.acc = self.mem.read_u16(addr16())
        elif opcode == Opcode.STA:
            # mem[addr] <- ACC as a 16-bit word (little-endian).
            self.mem.write_u16(addr16(), self.acc)
        elif opcode == Opcode.ADD_IMM:
            # ACC <- (ACC + immediate) mod 2**16.
            self.acc = (self.acc + imm16()) & 0xFFFF
        elif opcode == Opcode.SUB_IMM:
            # ACC <- (ACC - immediate) mod 2**16.
            self.acc = (self.acc - imm16()) & 0xFFFF
        elif opcode == Opcode.AND_IMM:
            # Bitwise AND with immediate.
            self.acc = self.acc & imm16()
        elif opcode == Opcode.OR_IMM:
            # Bitwise OR with immediate.
            self.acc = self.acc | imm16()
        elif opcode == Opcode.XOR_IMM:
            # Bitwise XOR with immediate.
            self.acc = self.acc ^ imm16()
        elif opcode == Opcode.LDX_IMM:
            # X <- 16-bit immediate.
            self.x = imm16()
        elif opcode == Opcode.LDX_MEM:
            # X <- 16-bit word at absolute address.
            self.x = self.mem.read_u16(addr16())
        elif opcode == Opcode.STX:
            # mem[addr] <- X as a 16-bit word.
            self.mem.write_u16(addr16(), self.x)
        elif opcode == Opcode.ADDX_IMM:
            # X <- (X + immediate) mod 2**16.
            self.x = (self.x + imm16()) & 0xFFFF
        elif opcode == Opcode.INX:
            # X <- (X + 1) mod 2**16.
            self.x = (self.x + 1) & 0xFFFF
        elif opcode == Opcode.DEX:
            # X <- (X - 1) mod 2**16.
            self.x = (self.x - 1) & 0xFFFF
        elif opcode == Opcode.TAX:
            # X <- ACC.
            self.x = self.acc & 0xFFFF
        elif opcode == Opcode.TXA:
            # ACC <- X.
            self.acc = self.x & 0xFFFF
        elif opcode == Opcode.ADD_MEM:
            # ACC <- (ACC + mem[addr]) mod 2**16.
            self.acc = (self.acc + self.mem.read_u16(addr16())) & 0xFFFF
        elif opcode == Opcode.SUB_MEM:
            # ACC <- (ACC - mem[addr]) mod 2**16.
            self.acc = (self.acc - self.mem.read_u16(addr16())) & 0xFFFF
        elif opcode == Opcode.LDA_X:
            # ACC <- 16-bit word at address in X.
            self.acc = self.mem.read_u16(self.x & 0xFFFF)
        elif opcode == Opcode.STA_X:
            # mem[X] <- ACC as a 16-bit word.
            self.mem.write_u16(self.x & 0xFFFF, self.acc)
        elif opcode == Opcode.ADD_X:
            # ACC <- (ACC + mem[X]) mod 2**16.
            self.acc = (self.acc + self.mem.read_u16(self.x & 0xFFFF)) & 0xFFFF
        elif opcode == Opcode.SUB_X:
            # ACC <- (ACC - mem[X]) mod 2**16.
            self.acc = (self.acc - self.mem.read_u16(self.x & 0xFFFF)) & 0xFFFF
        elif opcode == Opcode.PUSH_ACC:
            # Push ACC (u16) onto the stack.
            self._push_u16(self.acc)
        elif opcode == Opcode.POP_ACC:
            # Pop u16 from stack into ACC.
            self.acc = self._pop_u16()
        elif opcode == Opcode.PUSH_X:
            # Push X (u16) onto the stack.
            self._push_u16(self.x)
        elif opcode == Opcode.POP_X:
            # Pop u16 from stack into X.
            self.x = self._pop_u16()
        elif opcode == Opcode.LSP_IMM:
            # SP <- immediate (word-aligned).
            self.sp = imm16() & 0xFFFE
        elif opcode == Opcode.CALL:
            # Push return address and jump to subroutine.
            self._push_u16(pc_next & 0xFFFF)
            self.pc = addr16()
            return
        elif opcode == Opcode.RET:
            # Return from subroutine.
            self.pc = self._pop_u16() & 0xFFFF
            return
        elif opcode == Opcode.INT:
            # Software interrupt / syscall.
            int_id = imm8()
            if self.interrupts is not None:
                self.interrupts.handle(int_id, self)
        elif opcode == Opcode.JMP:
            # Unconditional jump: PC <- address.
            self.pc = addr16()
            return
        elif opcode == Opcode.JZ:
            # If ACC is zero, PC <- address; else fall through to next instruction.
            dest = addr16()
            if self.acc & 0xFFFF == 0:
                self.pc = dest
                return
        elif opcode == Opcode.JNZ:
            # If ACC is not zero, PC <- address; else fall through to next instruction.
            dest = addr16()
            if self.acc & 0xFFFF != 0:
                self.pc = dest
                return
        elif opcode == Opcode.HALT:
            # Stop execution; leave PC at byte after this instruction.
            self.halted = True
            self.pc = pc_next
            return

        self.pc = pc_next

    def run(self, max_steps: int = 1_000_000) -> int:
        steps = 0
        while not self.halted and steps < max_steps:
            try:
                self.step()
            except IndexError as e:
                raise RuntimeError(f"Memory access out of bounds: {e}") from e
            steps += 1
        if steps >= max_steps and not self.halted:
            raise RuntimeError("Step limit exceeded (maybe infinite loop).")
        return steps
