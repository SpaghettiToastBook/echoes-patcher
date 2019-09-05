# Sources:
# http://www.metroid2002.com/retromodding/wiki/TREE_(File_Format),
# https://gist.github.com/Antidote/70bd02369598e5ceb1210faf61bf1467

import dataclasses
import struct

from scly_common import Property, PropertyStruct, ScriptObject

__all__ = ("ScanTree",)


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


@dataclasses.dataclass(frozen=True, init=False)
class EditorProperties(PropertyStruct):
    name: str
    translation: Vector
    rotation: Vector
    translation: Vector
    active: bool

    def __post_init__(self):
        super().__post_init__()

        object.__setattr__(
            self,
            "name",
            self.get_subproperty_by_ID(0x494E414D).data[:-1].decode("ascii"),
        )
        object.__setattr__(
            self,
            "translation",
            Vector.from_packed(self.get_subproperty_by_ID(0x5846524D).data[:12]),
        )
        object.__setattr__(
            self,
            "rotation",
            Vector.from_packed(self.get_subproperty_by_ID(0x5846524D).data[12:24]),
        )
        object.__setattr__(
            self,
            "scale",
            Vector.from_packed(self.get_subproperty_by_ID(0x5846524D).data[24:]),
        )
        object.__setattr__(self, "active", bool(self.get_subproperty_by_ID(0x41435456).data[0]))

class ScannableParameters(PropertyStruct):
    pass


class ScanTreeScriptObject(ScriptObject):
    @classmethod
    def from_packed(cls, packed: bytes):
        return super().from_packed(packed, {
            0x255A4580: EditorProperties,
            0x2DA1EC33: ScannableParameters,
        })

    @property
    def editor_properties(self) -> EditorProperties:
        return self.base_property_struct.get_subproperty_by_ID(0x255A4580)

    @property
    def name_string_STRG_asset_ID(self) -> int:
        return struct.unpack(">I", self.base_property_struct.get_subproperty_by_ID(0x46219BAC).data)[0]

    @property
    def name_string_name(self) -> str:
        return self.base_property_struct.get_subproperty_by_ID(0x32698BD6).data[:-1].decode("ascii")


class SCND(ScanTreeScriptObject):
    pass

class SCSN(ScanTreeScriptObject):
    @property
    def scannable_parameters(self) -> ScannableParameters:
        return self.base_property_struct.get_subproperty_by_ID(0x2DA1EC33)

class SCIN(ScanTreeScriptObject):
    @property
    def inventory_slot(self) -> bytes:
        return self.base_property_struct.get_subproperty_by_ID(0x3D326F90).data

    @property
    def scannable_parameters(self) -> ScannableParameters:
        return self.base_property_struct.get_subproperty_by_ID(0x2DA1EC33)

class SCSL(ScanTreeScriptObject):
    pass

class SCMN(ScanTreeScriptObject):
    @property
    def menu_options_STRG_asset_ID(self) -> int:
        return struct.unpack(">I", self.base_property_struct.get_subproperty_by_ID(0xA6A874E9).data)[0]

    @property
    def option_1_string_name(self) -> str:
        return self.base_property_struct.get_subproperty_by_ID(0x30531924).data[:-1].decode("ascii")

    @property
    def option_2_string_name(self) -> str:
        return self.base_property_struct.get_subproperty_by_ID(0x01BB03B9).data[:-1].decode("ascii")

    @property
    def option_3_string_name(self) -> str:
        return self.base_property_struct.get_subproperty_by_ID(0xA7CC080D).data[:-1].decode("ascii")

    @property
    def option_4_string_name(self) -> str:
        return self.base_property_struct.get_subproperty_by_ID(0x626B3683).data[:-1].decode("ascii")


@dataclasses.dataclass(frozen=True)
class ScanTree:
    asset_type = "DUMB"

    _struct = struct.Struct(">4sIBI")
    _script_object_classes = {
        "SCND": SCND,
        "SCSN": SCSN,
        "SCIN": SCIN,
        "SCSL": SCSL,
        "SCMN": SCMN,
    }

    magic: str
    root_node_instance_ID: int
    unknown: int
    object_count: int
    objects: tuple = dataclasses.field(repr=False)

    @classmethod
    def from_packed(cls, packed: bytes):
        magic, root_node_instance_ID, unknown, object_count = cls._struct.unpack(packed[:13])

        offset = 13
        objects = []
        for i in range(object_count):
            object_type = struct.unpack(">4s", packed[offset:offset+4])[0].decode("ascii")
            object_ = cls._script_object_classes[object_type].from_packed(packed[offset:])

            objects.append(object_)
            offset += object_.packed_size

        return cls(magic.decode("ascii"), root_node_instance_ID, unknown, object_count, tuple(objects))

    @property
    def packed_size(self) -> int:
        return len(self.packed())

    def packed(self) -> bytes:
        return b"".join((
            self._struct.pack(self.magic.encode("ascii"), self.root_node_instance_ID, self.unknown, self.object_count),
            *(object_.packed() for object_ in self.objects),
        ))

    def with_object_replaced(self, index: int, new_object: ScanTreeScriptObject):
        return dataclasses.replace(self, objects=(*self.objects[:index], new_object, *self.objects[index+1:]))

    def with_object_appended(self, new_object: ScanTreeScriptObject):
        return dataclasses.replace(self, object_count=self.object_count+1, objects=self.objects+(new_object,))