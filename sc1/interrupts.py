"""
Interrupt / syscall handling for SC-1.

Design:
- SC-1 has a software interrupt instruction INT <id8>.
- The interrupt handler runs in the host (Python) and may implement I/O devices.
- By default, this is used for output (stdout or pygame console).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from sc1.cpu import SC1CPU


class InterruptDevice(Protocol):
    def handle(self, int_id: int, cpu: "SC1CPU") -> bool:  # pragma: no cover
        """Return True if the interrupt was handled."""

    def tick(self) -> None:  # pragma: no cover
        """Optional per-frame pump (pygame)."""


@dataclass
class InterruptController:
    devices: list[InterruptDevice]

    def handle(self, int_id: int, cpu: "SC1CPU") -> None:
        for d in self.devices:
            if d.handle(int_id, cpu):
                return

    def tick(self) -> None:
        for d in self.devices:
            d.tick()


def _u16_to_dec(n: int) -> str:
    return str(n & 0xFFFF)


@dataclass
class StdoutDevice:
    """
    Minimal console on stdout via interrupts.

    Interrupt IDs:
      1: putc   -> print chr(ACC & 0xFF) (no newline)
      2: print  -> print unsigned decimal ACC (no newline)
      3: nl     -> print newline
    """

    def handle(self, int_id: int, cpu: "SC1CPU") -> bool:
        if int_id == 1:
            ch = chr(cpu.acc & 0xFF)
            print(ch, end="", flush=True)
            return True
        if int_id == 2:
            print(_u16_to_dec(cpu.acc), end="", flush=True)
            return True
        if int_id == 3:
            print("", flush=True)
            return True
        return False

    def tick(self) -> None:
        return


@dataclass
class PygameTextConsole:
    """
    Simple pygame text console.

    Same interrupt IDs as StdoutDevice.
    """

    width: int = 800
    height: int = 600
    font_size: int = 20
    fg: tuple[int, int, int] = (230, 230, 230)
    bg: tuple[int, int, int] = (20, 20, 20)
    title: str = "SC-1 Console"
    fps: int = 60

    def __post_init__(self) -> None:
        import pygame  # type: ignore

        pygame.init()
        self._pygame = pygame
        self._screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self._font = pygame.font.Font(None, self.font_size)
        self._clock = pygame.time.Clock()
        self._buf: list[str] = [""]
        self._dirty = True

    def _append_text(self, s: str) -> None:
        if not self._buf:
            self._buf = [""]
        self._buf[-1] += s
        self._dirty = True

    def _newline(self) -> None:
        self._buf.append("")
        if len(self._buf) > 2000:
            self._buf = self._buf[-2000:]
        self._dirty = True

    def handle(self, int_id: int, cpu: "SC1CPU") -> bool:
        if int_id == 1:
            self._append_text(chr(cpu.acc & 0xFF))
            return True
        if int_id == 2:
            self._append_text(_u16_to_dec(cpu.acc))
            return True
        if int_id == 3:
            self._newline()
            return True
        return False

    def tick(self) -> None:
        pygame = self._pygame
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit(0)

        if self._dirty:
            self._screen.fill(self.bg)
            # Render last N lines that fit.
            line_h = self._font.get_linesize()
            max_lines = max(1, self.height // line_h)
            lines = self._buf[-max_lines:]
            y = 0
            for line in lines:
                surf = self._font.render(line, True, self.fg)
                self._screen.blit(surf, (8, y))
                y += line_h
            pygame.display.flip()
            self._dirty = False

        self._clock.tick(self.fps)


# Storage-backed disk access (restricted to a single directory).
IOCB_BASE = 0x00F0
IOCB_PATH_PTR = IOCB_BASE + 0x00  # u16
IOCB_BUF_PTR = IOCB_BASE + 0x02   # u16
IOCB_LEN = IOCB_BASE + 0x04       # u16 (requested length)
IOCB_STATUS = IOCB_BASE + 0x06    # u16 (0 ok, else error)
IOCB_COUNT = IOCB_BASE + 0x08     # u16 (bytes read/written)


def _read_c_string(cpu: "SC1CPU", ptr: int, max_len: int = 255) -> str:
    out = bytearray()
    for i in range(max_len):
        b = cpu.mem.read_u8((ptr + i) & 0xFFFF)
        if b == 0:
            break
        out.append(b)
    return out.decode("utf-8", errors="strict")


def _safe_storage_path(root: Path, rel: str) -> Path:
    # Disallow absolute paths and path traversal; keep everything under root.
    if rel.startswith("/") or rel.startswith("\\"):
        raise ValueError("absolute paths are not allowed")
    p = (root / rel).resolve()
    root_resolved = root.resolve()
    if p == root_resolved or root_resolved in p.parents:
        return p
    raise ValueError("path escapes storage root")


@dataclass
class StorageDevice:
    """
    Storage-backed disk I/O restricted to a root directory.

    Syscalls use a fixed I/O control block (IOCB) in memory:
      path_ptr  @ 0x00F0 (u16) -> C-string (UTF-8) file name (e.g. "hello.txt\\0")
      buf_ptr   @ 0x00F2 (u16) -> data buffer
      len       @ 0x00F4 (u16) -> requested length
      status    @ 0x00F6 (u16) -> 0 ok, else error
      count     @ 0x00F8 (u16) -> bytes read/written

    Interrupt IDs:
      16 (0x10): WRITE_FILE  -> write `len` bytes from buf_ptr to storage/path
      17 (0x11): READ_FILE   -> read up to `len` bytes into buf_ptr from storage/path
      18 (0x12): MKDIR       -> create directory at storage/path (parents ok)
    """

    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def handle(self, int_id: int, cpu: "SC1CPU") -> bool:
        if int_id not in (16, 17, 18):
            return False

        # Default outputs
        cpu.mem.write_u16(IOCB_STATUS, 0)
        cpu.mem.write_u16(IOCB_COUNT, 0)

        try:
            path_ptr = cpu.mem.read_u16(IOCB_PATH_PTR)
            buf_ptr = cpu.mem.read_u16(IOCB_BUF_PTR)
            length = cpu.mem.read_u16(IOCB_LEN)

            rel = _read_c_string(cpu, path_ptr)
            path = _safe_storage_path(self.root, rel)

            if int_id == 18:
                path.mkdir(parents=True, exist_ok=True)
                return True

            if int_id == 16:
                data = cpu.mem.dump(buf_ptr, length)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                cpu.mem.write_u16(IOCB_COUNT, len(data))
                return True

            # READ
            data = path.read_bytes()
            chunk = data[:length]
            cpu.mem.load_bytes(buf_ptr, chunk)
            cpu.mem.write_u16(IOCB_COUNT, len(chunk))
            return True

        except FileNotFoundError:
            cpu.mem.write_u16(IOCB_STATUS, 2)
            return True
        except (UnicodeDecodeError, ValueError):
            cpu.mem.write_u16(IOCB_STATUS, 3)
            return True
        except (IndexError, OSError):
            cpu.mem.write_u16(IOCB_STATUS, 4)
            return True

    def tick(self) -> None:
        return

