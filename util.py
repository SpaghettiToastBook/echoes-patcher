import dataclasses
import functools
import struct

__all__ = (
    "unpack_bool",
    "unpack_bool_from_int",
    "unpack_int",
    "unpack_float",
    "unpack_ascii",
    "unpack_null_terminated_ascii",
    "unpack_null_terminated_utf_16",
    "pack_int",
    "pack_ascii",
    "pack_null_terminated_ascii",
    "pack_null_terminated_utf_16",
    "Vector",
)

BOOL_STRUCT  = struct.Struct(">?")
INT_STRUCT   = struct.Struct(">I")
FLOAT_STRUCT = struct.Struct(">f")


# Unpacking
def unpack_bool(packed: bytes) -> bool:
    return BOOL_STRUCT.unpack(packed)[0]

def unpack_bool_from_int(packed: bytes) -> bool:
    return bool(INT_STRUCT.unpack(packed)[0])

def unpack_int(packed: bytes) -> int:
    return INT_STRUCT.unpack(packed)[0]

def unpack_float(packed: bytes) -> float:
    return FLOAT_STRUCT.unpack(packed)[0]

def unpack_ascii(packed: bytes):
    return packed.decode("ascii")

def unpack_null_terminated_ascii(packed: bytes) -> str:
    return packed[:-1].decode("ascii")

def unpack_null_terminated_utf_16(packed: bytes) -> str:
    return packed[:-2].decode("utf-16-be")


# Packing
def pack_int(integer: int) -> bytes:
    return INT_STRUCT.pack(integer)

def pack_ascii(string: str) -> bytes:
    return string.encode("ascii")

def pack_null_terminated_ascii(string: str) -> bytes:
    return string.encode("ascii") + b"\x00"

def pack_null_terminated_utf_16(string: str) -> bytes:
    return string.encode("utf-16-be") + b"\x00\x00"


# Data types
@dataclasses.dataclass(frozen=True)
class Vector:
    _struct = struct.Struct(">fff")

    x: float
    y: float
    z: float

    @classmethod
    def from_packed(cls, packed: bytes):
        return cls(*cls._struct.unpack(packed))

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return self._struct.pack(self.x, self.y, self.z)