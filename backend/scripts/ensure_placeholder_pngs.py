"""Write minimal placeholder PNGs for support-assets walkthrough folders."""

from __future__ import annotations

import base64
import struct
import zlib
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ASSETS = BACKEND_ROOT / "support-assets"

# 320x180 blue-tinted placeholder
WIDTH, HEIGHT = 320, 180


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _build_png() -> bytes:
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)
        for x in range(WIDTH):
            raw.extend((70, 120, 200, 255))
    compressed = zlib.compress(bytes(raw), 9)
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )


PNG_BYTES = _build_png()

FOLDERS = [
    "enroll_course",
    "submit_assignment",
    "watch_lecture",
    "view_grades",
    "download_notes",
    "password_reset",
    "payment_failed",
    "upload_documents",
    "profile_update",
    "account_settings",
]


def main() -> None:
    for folder in FOLDERS:
        path = ASSETS / folder
        path.mkdir(parents=True, exist_ok=True)
        for n in (1, 2, 3):
            out = path / f"step{n}.png"
            if not out.exists() or out.stat().st_size < 200:
                out.write_bytes(PNG_BYTES)
                print("wrote", out)


if __name__ == "__main__":
    main()
