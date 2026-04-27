"""
SC-1 memory: 16-bit address space, byte-oriented (0–255 values), 16-bit words LE.
"""

from __future__ import annotations

from typing import Final


ADDRESS_BITS: Final[int] = 16
MAX_MEM_SIZE: Final[int] = 1 << ADDRESS_BITS  # 65536 bytes


class Memory:
    """Byte-addressable memory (1..64 KiB)."""

    __slots__ = ("_raw", "_size")

    def __init__(self, size: int = MAX_MEM_SIZE) -> None:
        if not isinstance(size, int):
            raise TypeError("size must be an int")
        if size <= 0 or size > MAX_MEM_SIZE:
            raise ValueError(f"size must be in 1..{MAX_MEM_SIZE}")
        self._size = size
        self._raw = bytearray(size)

    @property
    def size(self) -> int:
        return self._size

    def _check_u8_addr(self, addr: int) -> int:
        a = addr & 0xFFFF
        if a >= self._size:
            raise IndexError(f"address out of bounds: 0x{a:04X} (size={self._size})")
        return a

    def _check_u16_addr(self, addr: int) -> int:
        a = addr & 0xFFFF
        if a + 1 >= self._size:
            raise IndexError(f"u16 address out of bounds: 0x{a:04X} (size={self._size})")
        return a

    def read_u8(self, addr: int) -> int:
        return self._raw[self._check_u8_addr(addr)]

    def write_u8(self, addr: int, value: int) -> None:
        self._raw[self._check_u8_addr(addr)] = value & 0xFF

    def read_u16(self, addr: int) -> int:
        a = self._check_u16_addr(addr)
        lo = self._raw[a]
        hi = self._raw[a + 1]
        return lo | (hi << 8)

    def write_u16(self, addr: int, value: int) -> None:
        a = self._check_u16_addr(addr)
        v = value & 0xFFFF
        self._raw[a] = v & 0xFF
        self._raw[a + 1] = (v >> 8) & 0xFF

    def load_bytes(self, start: int, data: bytes | bytearray | list[int]) -> None:
        """Write byte sequence starting at `start`."""
        a = start & 0xFFFF
        if a >= self._size:
            raise IndexError(f"start address out of bounds: 0x{a:04X} (size={self._size})")
        data_len = len(data)
        if a + data_len > self._size:
            raise IndexError(
                f"write would exceed memory bounds: start=0x{a:04X} len={data_len} size={self._size}"
            )
        for i, b in enumerate(data):
            self._raw[a + i] = int(b) & 0xFF

    def dump(self, start: int, length: int) -> bytes:
        if length < 0:
            raise ValueError("length must be >= 0")
        a = start & 0xFFFF
        if a >= self._size:
            raise IndexError(f"start address out of bounds: 0x{a:04X} (size={self._size})")
        end = a + length
        if end > self._size:
            raise IndexError(
                f"dump would exceed memory bounds: start=0x{a:04X} len={length} size={self._size}"
            )
        return bytes(self._raw[a:end])
