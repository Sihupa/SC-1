"""
Program text: each line is one full instruction — space-separated bytes 0–255 (opcode + operands).
"""

from __future__ import annotations

from sc1.instructions import instruction_length


def _parse_instruction_line(line: str) -> list[int]:
    """Parse all bytes on one line; text after # or ; starts a comment."""
    out: list[int] = []
    for tok in line.split():
        if tok.startswith("#") or tok.startswith(";"):
            break
        if not tok.isdigit():
            raise ValueError(f"Invalid token (only decimal 0–255 integers allowed): {tok!r}")
        n = int(tok)
        if n < 0 or n > 255:
            raise ValueError(f"Out of 0–255 range: {n}")
        out.append(n)
    return out


def parse_program_lines(text: str) -> list[int]:
    """
    Each non-empty line contains exactly one instruction (opcode + operand bytes).

    Blank lines and lines starting with # or ; are skipped.
    Inline comments: everything after # or ; on a line is ignored.
    """
    flat: list[int] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        if ";" in line:
            line = line.split(";", 1)[0].strip()
        if not line:
            continue
        bytes_line = _parse_instruction_line(line)
        if not bytes_line:
            raise ValueError(f"No instruction bytes on line: {raw_line!r}")
        op = bytes_line[0]
        try:
            want = instruction_length(op)
        except ValueError:
            raise ValueError(f"Unknown opcode: {op} — {raw_line!r}") from None
        if len(bytes_line) != want:
            raise ValueError(
                f"Line has {len(bytes_line)} byte(s), opcode 0x{op:02X} requires {want}: {raw_line!r}"
            )
        flat.extend(bytes_line)
    return flat


def program_lines_to_bytes(lines: list[int]) -> bytes:
    return bytes(lines)
