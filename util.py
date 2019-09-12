import functools
import struct

__all__ = (
    "unpack_bool",
    "unpack_bool_from_int",
    "unpack_int",
    "unpack_ascii",
    "unpack_null_terminated_ascii",
    "pack_int",
    "pack_ascii",
    "pack_null_terminated_ascii",
)

BOOL_STRUCT = struct.Struct(">?")
INT_STRUCT  = struct.Struct(">I")


# Unpacking
def unpack_bool(packed: bytes) -> bool:
    return BOOL_STRUCT.unpack(packed)[0]

def unpack_bool_from_int(packed: bytes) -> bool:
    return bool(INT_STRUCT.unpack(packed)[0])

def unpack_int(packed: bytes) -> int:
    return INT_STRUCT.unpack(packed)[0]

def unpack_ascii(packed: bytes):
    return packed.decode("ascii")

def unpack_null_terminated_ascii(packed: bytes) -> str:
    return packed[:-1].decode("ascii")


# Packing
def pack_int(integer: int) -> bytes:
    return INT_STRUCT.pack(integer)

def pack_ascii(string: str) -> bytes:
    return string.encode("ascii")

def pack_null_terminated_ascii(string: str) -> bytes:
    return string.encode("ascii") + b"\x00"