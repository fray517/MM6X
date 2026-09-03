"""Read-only MM6 LOD (Icons.lod / games.lod) helpers.

Offsets follow OpenEnroth LodEntry_MM6: file dataOffset is relative
to the root directory dataOffset, not an absolute file position.
Text tables in Icons.lod use LodImageHeader_MM6 with flags bit 0x100
and a zlib payload. games.lod maps use u32+u32+zlib (`size_pair`).
VERIFIED_SOURCE: OpenEnroth LodReader / LodFormats.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

HEADER_SIZE = 256
ENTRY_SIZE = 32
IMAGE_HEADER_SIZE = 48
COMPRESSION_HEADER_SIZE = 16
TEXT_FLAG = 0x100
MVII_VERSION = 91969
MVII_SIGNATURE = b"mvii"


@dataclass(frozen=True)
class LodEntry:
    """One directory record after the root entry."""

    name: str
    offset: int
    size: int


class LodError(ValueError):
    """Malformed or unexpected LOD layout."""


def _cstring(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def _unpack_entry(rec: bytes, base: int) -> LodEntry:
    if len(rec) < ENTRY_SIZE:
        raise LodError("truncated LOD directory entry")
    name = _cstring(rec[:16])
    rel_off, size = struct.unpack_from("<II", rec, 16)
    return LodEntry(name=name, offset=base + rel_off, size=size)


class Mm6Lod:
    """Single-directory MM6 LOD (vanilla layout)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        try:
            self._data = path.read_bytes()
        except OSError as exc:
            raise LodError(f"cannot read {path}: {exc}") from exc
        if len(self._data) < HEADER_SIZE + ENTRY_SIZE:
            raise LodError(f"{path.name}: file too small for MM6 LOD")
        sig = self._data[:4]
        if sig[:3] != b"LOD":
            raise LodError(
                f"{path.name}: expected LOD signature, got {sig!r}"
            )
        root = self._data[HEADER_SIZE : HEADER_SIZE + ENTRY_SIZE]
        self.root_name = _cstring(root[:16])
        root_off, root_size = struct.unpack_from("<II", root, 16)
        num_items = struct.unpack_from("<H", root, 28)[0]
        if root_off + num_items * ENTRY_SIZE > len(self._data):
            raise LodError(f"{path.name}: directory points outside file")
        self._entries: dict[str, LodEntry] = {}
        self._order: list[str] = []
        for index in range(num_items):
            start = root_off + index * ENTRY_SIZE
            rec = self._data[start : start + ENTRY_SIZE]
            entry = _unpack_entry(rec, root_off)
            if not entry.name:
                continue
            key = entry.name.casefold()
            if key in self._entries:
                continue
            self._entries[key] = entry
            self._order.append(entry.name)
        self.root_offset = root_off
        self.root_size = root_size
        self.num_items = num_items

    def names(self) -> list[str]:
        return list(self._order)

    def get(self, name: str) -> LodEntry | None:
        return self._entries.get(name.casefold())

    def read_blob(self, name: str) -> bytes:
        entry = self.get(name)
        if entry is None:
            raise LodError(f"{self.path.name}: no entry {name!r}")
        end = entry.offset + entry.size
        if end > len(self._data):
            raise LodError(
                f"{self.path.name}: {name!r} points outside file"
            )
        return self._data[entry.offset : end]


def _is_mvii(blob: bytes) -> bool:
    if len(blob) < COMPRESSION_HEADER_SIZE:
        return False
    version, sig = struct.unpack_from("<I4s", blob, 0)
    return version == MVII_VERSION and sig == MVII_SIGNATURE


def _is_text_image(blob: bytes) -> bool:
    if len(blob) < IMAGE_HEADER_SIZE:
        return False
    size, data_size = struct.unpack_from("<II", blob, 16)
    width, height = struct.unpack_from("<HH", blob, 24)
    flags = struct.unpack_from("<I", blob, 44)[0]
    if size != 0 or width != 0 or height != 0:
        return False
    if not (flags & TEXT_FLAG):
        return False
    if data_size == 0:
        return False
    return len(blob) >= IMAGE_HEADER_SIZE + data_size


def _inflate(payload: bytes, expected: int) -> bytes:
    raw = zlib.decompress(payload)
    if expected and len(raw) != expected:
        raise LodError(
            f"zlib size {len(raw)} != header decompressedSize "
            f"{expected}"
        )
    return raw


def _is_size_pair_zlib(blob: bytes) -> bool:
    """games.lod maps: u32 comp_size, u32 decomp_size, zlib payload."""
    if len(blob) < 10:
        return False
    comp_size, decomp_size = struct.unpack_from("<II", blob, 0)
    if comp_size + 8 != len(blob):
        return False
    if decomp_size < comp_size:
        return False
    cmf_flg = blob[8:10]
    return cmf_flg[0] == 0x78 and cmf_flg[1] in (0x01, 0x9C, 0xDA)


def decode_maybe_compressed(blob: bytes) -> tuple[bytes, str]:
    """Return (payload, how). how: mvii | text_image | size_pair | raw."""
    if _is_mvii(blob):
        data_size, dec_size = struct.unpack_from("<II", blob, 8)
        start = COMPRESSION_HEADER_SIZE
        if data_size == len(blob):
            payload = blob[start:]
        else:
            payload = blob[start : start + data_size]
        if dec_size:
            return _inflate(payload, dec_size), "mvii"
        return payload, "mvii"
    if _is_text_image(blob):
        data_size = struct.unpack_from("<I", blob, 20)[0]
        dec_size = struct.unpack_from("<I", blob, 40)[0]
        payload = blob[IMAGE_HEADER_SIZE : IMAGE_HEADER_SIZE + data_size]
        if dec_size:
            return _inflate(payload, dec_size), "text_image"
        return payload, "text_image"
    if _is_size_pair_zlib(blob):
        decomp_size = struct.unpack_from("<I", blob, 4)[0]
        payload = blob[8:]
        return _inflate(payload, decomp_size), "size_pair"
    return blob, "raw"
