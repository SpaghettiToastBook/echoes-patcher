# Source: http://www.metroid2002.com/retromodding/wiki/Scriptable_Layers_(Metroid_Prime_2)

import dataclasses
import struct

__all__ = ("Connection", "Property", "PropertyStruct", "ScriptObject")


@dataclasses.dataclass(frozen=True)
class Connection:
    _struct = struct.Struct(">4s4sI")

    state: str
    message: str
    target_instance_ID: int

    @classmethod
    def from_packed(cls, packed: bytes):
        state_bytes, message_bytes, target_instance_ID = cls._struct.unpack(packed)
        return cls(
            state_bytes.decode("ascii"),
            message_bytes.decode("ascii"),
            target_instance_ID,
        )

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return self._struct.pack(
            self.state.encode("ascii"),
            self.message.encode("ascii"),
            self.target_instance_ID,
        )


@dataclasses.dataclass(frozen=True)
class Property:
    _struct = struct.Struct(">IH")

    ID: int
    size: int
    data: bytes

    @classmethod
    def from_packed(cls, packed: bytes):
        ID, size = cls._struct.unpack(packed[:6])
        return cls(ID, size, packed[6:6+size])

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join((self._struct.pack(self.ID, self.size), self.data))


@dataclasses.dataclass(frozen=True)
class PropertyStruct:
    _struct = struct.Struct(">IHH")
    _property_struct_IDs = frozenset({
        # TODO: Actually use a complete list
        0xFFFFFFFF, # Base struct

        0x1C5B4A3A, # SCAN: ScanInfoSecondaryModel 1
        0x8728A0EE, # SCAN: ScanInfoSecondaryModel 2
        0xF1CD99D3, # SCAN: ScanInfoSecondaryModel 3
        0x6ABE7307, # SCAN: ScanInfoSecondaryModel 4
        0x1C07EBA9, # SCAN: ScanInfoSecondaryModel 5
        0x8774017D, # SCAN: ScanInfoSecondaryModel 6
        0xF1913840, # SCAN: ScanInfoSecondaryModel 7
        0x6AE2D294, # SCAN: ScanInfoSecondaryModel 8
        0x1CE2091C, # SCAN: ScanInfoSecondaryModel 9

        0x255A4580, # TREE: EditorProperties
        0x2DA1EC33, # TREE: ScannableParameters
    })

    ID: int
    size: int
    subproperty_count: int
    subproperties: tuple = dataclasses.field(repr=False)

    def __post_init__(self):
        _subproperty_ID_to_index_map = {}
        for i, subproperty in enumerate(self.subproperties):
            _subproperty_ID_to_index_map[subproperty.ID] = i
        object.__setattr__(self, "_subproperty_ID_to_index_map", _subproperty_ID_to_index_map)

    @classmethod
    def from_packed(cls, packed: bytes, subproperty_struct_classes: dict = {}):
        ID, size, subproperty_count = cls._struct.unpack(packed[:8])

        offset = 8
        subproperties = []
        for i in range(subproperty_count):
            subproperty_ID, subproperty_size = struct.unpack(">IH", packed[offset:offset+6])
            if subproperty_ID in cls._property_struct_IDs:
                subproperty_class = subproperty_struct_classes.get(subproperty_ID, PropertyStruct)
            else:
                subproperty_class = Property

            subproperty = subproperty_class.from_packed(packed[offset:offset+6+subproperty_size])
            subproperties.append(subproperty)
            offset += subproperty.packed_size

        return cls(ID, size, subproperty_count, tuple(subproperties))

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join((
            self._struct.pack(self.ID, self.size, self.subproperty_count),
            *(subproperty.packed() for subproperty in self.subproperties),
        ))

    def get_subproperty_by_ID(self, subproperty_ID):
        return self.subproperties[self._subproperty_ID_to_index_map[subproperty_ID]]


@dataclasses.dataclass(frozen=True)
class ScriptObject:
    _struct = struct.Struct(">4sHIH")

    instance_type: str
    instance_size: int
    instance_ID: int
    connection_count: int
    connections: tuple
    base_property_struct: PropertyStruct

    @classmethod
    def from_packed(cls, packed: bytes, subproperty_struct_classes: dict = {}):
        instance_type_bytes, instance_size, instance_ID, connection_count = cls._struct.unpack(packed[:12])
        instance_type = instance_type_bytes.decode("ascii")

        offset = 12
        connections = []
        for i in range(connection_count):
            connections.append(Connection.from_packed(packed[offset:offset+12]))
            offset += 12

        return cls(
            instance_type,
            instance_size,
            instance_ID,
            connection_count,
            tuple(connections),
            PropertyStruct.from_packed(packed[offset:], subproperty_struct_classes),
        )

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join((
            self._struct.pack(
                self.instance_type.encode("ascii"),
                self.instance_size,
                self.instance_ID,
                self.connection_count
            ),
            *(connection.packed() for connection in self.connections),
            self.base_property_struct.packed(),
        ))

    def with_connections_replaced(self, new_connections):
        new_connection_count = len(tuple(new_connections))
        return dataclasses.replace(
            self,
            instance_size=self.instance_size + 12*(new_connection_count - self.connection_count),
            connection_count=new_connection_count,
            connections=tuple(sorted(new_connections, key=lambda conn: conn.target_instance_ID)),
        )