import functools
import struct

__all__ = (
    "unpack_bool",
    "unpack_bool_from_int",
    "unpack_int",
    "unpack_ascii",
    "unpack_null_terminated_ascii",
    "unpack_null_terminated_utf_16",
    "pack_int",
    "pack_ascii",
    "pack_null_terminated_ascii",
    "pack_null_terminated_utf_16",
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