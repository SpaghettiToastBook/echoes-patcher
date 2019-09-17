# Source: http://www.metroid2002.com/retromodding/wiki/DGRP_(File_Format)

import dataclasses
import struct

from util import unpack_int, unpack_ascii, pack_int, pack_ascii

__all__ = ("DGRP",)


@dataclasses.dataclass(frozen=True)
class Dependency:
    _struct = struct.Struct(">4sI")

    asset_type: str
    asset_ID: int

    @classmethod
    def from_packed(cls, packed: bytes):
        asset_type_bytes, asset_ID = cls._struct.unpack(packed)
        return cls(unpack_ascii(asset_type_bytes), asset_ID)

    def packed(self) -> bytes:
        return self._struct.pack(pack_ascii(self.asset_type), self.asset_ID)


@dataclasses.dataclass(frozen=True)
class DGRP:
    asset_type = "DGRP"

    dependency_count: int
    dependencies: tuple

    @classmethod
    def from_packed(cls, packed: bytes):
        dependency_count = unpack_int(packed[:4])
        dependencies = tuple(Dependency.from_packed(packed[4 + 8*i : 4 + 8*(i+1)]) for i in range(dependency_count))
        return cls(dependency_count, dependencies)

    def packed(self) -> bytes:
        return b"".join((
            pack_int(self.dependency_count),
            *(dependency.packed() for dependency in self.dependencies),
        ))