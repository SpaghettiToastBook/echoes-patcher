# Source: http://www.metroid2002.com/retromodding/wiki/STRG_(Metroid_Prime)

import dataclasses
import struct

from util import unpack_ascii, unpack_null_terminated_ascii, unpack_null_terminated_utf_16, \
    pack_ascii, pack_null_terminated_ascii, pack_null_terminated_utf_16

__all__ = ("STRGLanguageTable", "STRGNameEntry", "STRGNameTable", "STRGStringTable", "STRG")


@dataclasses.dataclass(frozen=True)
class STRGLanguageTable:
    _struct = struct.Struct(">4sII")

    language_ID: str
    strings_offset: int
    strings_size: int

    @classmethod
    def from_packed(cls, packed: bytes):
        language_ID_bytes, strings_offset, strings_size = cls._struct.unpack(packed)
        return cls(unpack_ascii(language_ID_bytes), strings_offset, strings_size)

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return self._struct.pack(
            pack_ascii(self.language_ID),
            self.strings_offset,
            self.strings_size,
        )


@dataclasses.dataclass(frozen=True)
class STRGNameEntry:
    _struct = struct.Struct(">II")

    offset: int
    string_index: int

    @classmethod
    def from_packed(cls, packed: bytes):
        return cls(*cls._struct.unpack(packed))

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return self._struct.pack(self.offset, self.string_index)


@dataclasses.dataclass(frozen=True)
class STRGNameTable:
    _struct = struct.Struct(">II")

    count: int
    size: int
    entries: tuple
    names: tuple

    @classmethod
    def from_packed(cls, packed: bytes):
        count, size = cls._struct.unpack(packed[:8])

        offset = 8
        entries = []
        for i in range(count):
            entries.append(STRGNameEntry.from_packed(packed[offset:offset+8]))
            offset += 8

        names = []
        for entry in entries:
            offset = 8 + entry.offset
            name_length = packed[offset:].index(b"\x00")
            names.append(unpack_null_terminated_ascii(packed[offset:offset+name_length+1]))

        return cls(count, size, tuple(entries), tuple(names))

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join((
            self._struct.pack(self.count, self.size),
            *(entry.packed() for entry in self.entries),
            *(pack_null_terminated_ascii(name) for name in self.names),
        ))

    def get_string_index_for_name(self, name: str):
        return self.entries[self.names.index(name)].string_index


@dataclasses.dataclass(frozen=True)
class STRGStringTable:
    count: int
    offsets: tuple
    strings: tuple

    @classmethod
    def from_packed(cls, packed: bytes, string_count: int):
        string_offsets = struct.unpack(f">{string_count}I", packed[:4*string_count])

        strings = []
        for offset in string_offsets:
            string_length = packed[offset:].index(b"\x00\x00")
            strings.append(unpack_null_terminated_utf_16(packed[offset:offset+string_length+2]))

        return cls(string_count, string_offsets, tuple(strings))

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join((
            struct.pack(f">{self.count}I", *self.offsets),
            *(pack_null_terminated_utf_16(string) for _, string in sorted(zip(self.offsets, self.strings))),
        ))

    def with_string_replaced(self, index: int, new_string: str):
        size_diff = \
            len(pack_null_terminated_utf_16(new_string)) - len(pack_null_terminated_utf_16(self.strings[index]))

        new_offsets = list(self.offsets[:index+1])
        for offset in self.offsets[index+1:]:
            new_offsets.append(offset+size_diff)

        return dataclasses.replace(
            self,
            offsets=tuple(new_offsets),
            strings=(*self.strings[:index], new_string, *self.strings[index+1:]),
        )


@dataclasses.dataclass(frozen=True)
class STRG:
    asset_type = "STRG"

    _struct = struct.Struct(">IIII")

    magic_number: int
    version: int
    language_count: int
    string_count: int
    language_tables: tuple = dataclasses.field(repr=False)
    name_table: STRGNameTable = dataclasses.field(repr=False)
    string_tables: tuple = dataclasses.field(repr=False)

    def __post_init__(self):
        language_ID_to_index_map = {}
        for index, language_table in enumerate(self.language_tables):
            language_ID_to_index_map[language_table.language_ID] = index
        object.__setattr__(self, "_language_ID_to_index_map", language_ID_to_index_map)

    @classmethod
    def from_packed(cls, packed: bytes):
        magic_number, version, language_count, string_count = cls._struct.unpack(packed[:16])

        offset = 16
        language_tables = []
        for i in range(language_count):
            language_tables.append(STRGLanguageTable.from_packed(packed[offset:offset+12]))
            offset += 12

        name_table = STRGNameTable.from_packed(packed[offset:])
        string_tables_offset = offset + 8 + name_table.size

        string_tables = []
        for language_table in language_tables:
            offset, size = string_tables_offset + language_table.strings_offset, language_table.strings_size
            string_tables.append(STRGStringTable.from_packed(packed[offset:offset+size], string_count))

        return cls(
            magic_number,
            version,
            language_count,
            string_count,
            tuple(language_tables),
            name_table,
            tuple(string_tables),
        )

    @property
    def packed_size(self) -> int:
        language_tables_size = sum(language_table.packed_size for language_table in self.language_tables)
        string_tables_size = sum(string_table.packed_size for string_table in self.string_tables)

        return 4 + 4 + 4 + 4 + language_tables_size + self.name_table.packed_size + string_tables_size

    def packed(self) -> bytes:
        return b"".join((
            self._struct.pack(self.magic_number, self.version, self.language_count, self.string_count),
            *(language_table.packed() for language_table in self.language_tables),
            self.name_table.packed(),
            *(string_table.packed() for string_table in self.string_tables),
        ))

    def get_string_table_by_language_ID(self, language_ID: str) -> STRGStringTable:
        return self.string_tables[self._language_ID_to_index_map[language_ID]]

    def with_string_table_replaced(self, index: int, new_string_table: STRGStringTable):
        old_language_table = self.language_tables[index]
        new_language_table = dataclasses.replace(old_language_table, strings_size=new_string_table.packed_size)

        size_diff = new_language_table.strings_size - old_language_table.strings_size
        new_language_tables = [*self.language_tables[:index], new_language_table]
        for language_table in self.language_tables[index+1:]:
            new_language_tables.append(
                dataclasses.replace(language_table, strings_offset=language_table.strings_size+size_diff)
            )

        return dataclasses.replace(
            self,
            language_tables=tuple(new_language_tables),
            string_tables=(*self.string_tables[:index], new_string_table, *self.string_tables[index+1:]),
        )

    def with_string_table_replaced_by_language_ID(self, language_ID: str, new_string_table: STRGStringTable):
        index = self._language_ID_to_index_map[language_ID]
        return self.with_string_table_replaced(index, new_string_table)