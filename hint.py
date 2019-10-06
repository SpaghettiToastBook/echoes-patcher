# Source: http://www.metroid2002.com/retromodding/wiki/DGRP_(File_Format)

import dataclasses
import struct

from util import unpack_null_terminated_ascii, pack_null_terminated_ascii

__all__ = ("HintLocation", "HINT")


@dataclasses.dataclass(frozen=True)
class HintLocation:
    _struct = struct.Struct(">IIII")

    world_MLVL_asset_ID: int
    room_MREA_asset_ID: int
    room_index: int
    map_text_STRG_asset_ID: int

    @classmethod
    def from_packed(cls, packed: bytes):
        return cls(*cls._struct.unpack(packed))

    @property
    def packed_size(self) -> int:
        return 4 + 4 + 4 + 4

    def packed(self) -> bytes:
        return self._struct.pack(
            self.world_MLVL_asset_ID,
            self.room_MREA_asset_ID,
            self.room_index,
            self.map_text_STRG_asset_ID,
        )


@dataclasses.dataclass(frozen=True)
class Hint:
    _struct = struct.Struct(">ffIfI")

    name: str
    immediate_time: float
    normal_time: float
    text_STRG_asset_ID: int
    text_time: float
    location_count: int
    locations: tuple = dataclasses.field(repr=False)

    @classmethod
    def from_packed(cls, packed: bytes):
        offset = packed.index(b"\x00") + 1
        name = unpack_null_terminated_ascii(packed[:offset])

        immediate_time, normal_time, text_STRG_asset_ID, \
            text_time, location_count = cls._struct.unpack(packed[offset:offset+20])
        offset += 20

        return cls(
            name,
            immediate_time,
            normal_time,
            text_STRG_asset_ID,
            text_time,
            location_count,
            tuple(HintLocation.from_packed(packed[offset + 16*i:offset + 16*(i+1)]) for i in range(location_count)),
        )

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join((
            pack_null_terminated_ascii(self.name),
            self._struct.pack(
                self.immediate_time,
                self.normal_time,
                self.text_STRG_asset_ID,
                self.text_time,
                self.location_count,
            ),
            *(location.packed() for location in self.locations),
        ))


@dataclasses.dataclass(frozen=True)
class HINT:
    _struct = struct.Struct(">III")

    magic: int
    version: int
    hint_count: int
    hints: tuple = dataclasses.field(repr=False)

    @classmethod
    def from_packed(cls, packed: bytes):
        magic, version, hint_count = cls._struct.unpack(packed[:12])

        offset = 12
        hints = []
        for i in range(hint_count):
            hint = Hint.from_packed(packed[offset:])
            hints.append(hint)
            offset += hint.packed_size

        return cls(magic, version, hint_count, tuple(hints))

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join(
            self._struct.pack(self.magic, self.version, self.hint_count),
            *(hint.packed() for hint in self.hints),
        )

    def with_hints_replaced(self, new_hints):
        new_hints = tuple(new_hints)
        return dataclasses.replace(self, hint_count=len(new_hints), hints=new_hints)