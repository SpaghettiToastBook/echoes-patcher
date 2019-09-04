# Source: http://www.metroid2002.com/retromodding/wiki/DUMB_(File_Format)

import dataclasses

__all__ = ("DUMB",)


@dataclasses.dataclass(frozen=True)
class DUMB:
    asset_type = "DUMB"

    data: bytes

    @classmethod
    def from_packed(cls, packed: bytes):
        return cls(packed)

    @property
    def packed_size(self) -> int:
        return len(self.data)

    def packed(self) -> bytes:
        return self.data