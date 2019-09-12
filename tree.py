# Sources:
# http://www.metroid2002.com/retromodding/wiki/TREE_(File_Format),
# https://gist.github.com/Antidote/70bd02369598e5ceb1210faf61bf1467

import dataclasses
import struct

from scly_common import Property, PropertyStruct, ScriptObject
from util import unpack_bool, unpack_int, unpack_null_terminated_ascii

__all__ = ("EditorProperties", "ScannableParameters", "SCND", "SCSN", "SCIN", "SCSL", "SCMN", "ScanTree")


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


@dataclasses.dataclass(frozen=True)
class EditorProperties(PropertyStruct):
    name: str = dataclasses.field(init=False)
    translation: Vector = dataclasses.field(init=False)
    rotation: Vector = dataclasses.field(init=False)
    translation: Vector = dataclasses.field(init=False)
    scale: Vector = dataclasses.field(init=False)
    active: bool = dataclasses.field(init=False)

    def __post_init__(self):
        super().__post_init__()

        self._set_fields_from_subproperty_data(
            ("name",        0x494E414D, unpack_null_terminated_ascii),
            ("translation", 0x5846524D, lambda data: Vector.from_packed(data[:12])),
            ("rotation",    0x5846524D, lambda data: Vector.from_packed(data[12:24])),
            ("scale",       0x5846524D, lambda data: Vector.from_packed(data[24:])),
            ("active",      0x41435456, unpack_bool),
        )


@dataclasses.dataclass(frozen=True)
class ScannableParameters(PropertyStruct):
    SCAN_asset_ID: int = dataclasses.field(init=False)

    def __post_init__(self):
        super().__post_init__()

        self._set_fields_from_subproperty_data(("SCAN_asset_ID", 0xB94E9BE7, unpack_int))


@dataclasses.dataclass(frozen=True)
class ScanTreeScriptObject(ScriptObject):
    editor_properties: EditorProperties = dataclasses.field(init=False, repr=False)
    name_string_STRG_asset_ID: int = dataclasses.field(init=False)
    name_string_name: str = dataclasses.field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "editor_properties", self.base_property_struct.get_subproperty_by_ID(0x255A4580))
        self._set_fields_from_property_data(
            ("name_string_STRG_asset_ID", 0x46219BAC, unpack_int),
            ("name_string_name",          0x32698BD6, unpack_null_terminated_ascii),
        )

    @classmethod
    def from_packed(cls, packed: bytes):
        return super().from_packed(packed, {
            0x255A4580: EditorProperties,
            0x2DA1EC33: ScannableParameters,
        })


@dataclasses.dataclass(frozen=True)
class SCND(ScanTreeScriptObject):
    pass


@dataclasses.dataclass(frozen=True)
class SCSN(ScanTreeScriptObject):
    scannable_parameters: ScannableParameters = dataclasses.field(init=False, repr=False)

    def __post_init__(self):
        super().__post_init__()

        object.__setattr__(self, "scannable_parameters", self.base_property_struct.get_subproperty_by_ID(0x2DA1EC33))


@dataclasses.dataclass(frozen=True)
class SCIN(ScanTreeScriptObject):
    inventory_slot: int = dataclasses.field(init=False)
    scannable_parameters: ScannableParameters = dataclasses.field(init=False, repr=False)

    def __post_init__(self):
        super().__post_init__()

        self._set_fields_from_property_data(("inventory_slot", 0x3D326F90, unpack_int))
        object.__setattr__(self, "scannable_parameters", self.base_property_struct.get_subproperty_by_ID(0x2DA1EC33))


@dataclasses.dataclass(frozen=True)
class SCSL(ScanTreeScriptObject):
    unknown: int = dataclasses.field(init=False)

    def __post_init__(self):
        super().__post_init__()

        self._set_fields_from_property_data(("unknown", 0x0261A4E0, unpack_int))


@dataclasses.dataclass(frozen=True)
class SCMN(ScanTreeScriptObject):
    menu_options_STRG_asset_ID: int = dataclasses.field(init=False)
    option_1_string_name: str = dataclasses.field(init=False)
    option_2_string_name: str = dataclasses.field(init=False)
    option_3_string_name: str = dataclasses.field(init=False)
    option_4_string_name: str = dataclasses.field(init=False)

    def __post_init__(self):
        super().__post_init__()

        self._set_fields_from_property_data(
            ("menu_options_STRG_asset_ID", 0xA6A874E9, unpack_int),
            ("option_1_string_name", 0x30531924, unpack_null_terminated_ascii),
            ("option_2_string_name", 0x01BB03B9, unpack_null_terminated_ascii),
            ("option_3_string_name", 0xA7CC080D, unpack_null_terminated_ascii),
            ("option_4_string_name", 0x626B3683, unpack_null_terminated_ascii),
        )


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
    def packed_content_size(self) -> int:
        return 4 + 4 + 1 + 4 + sum(object_.packed_size for object_ in self.objects)

    @property
    def packed_padding_size(self) -> int:
        return (32 - (self.packed_content_size % 32)) % 32

    @property
    def packed_size(self) -> int:
        return self.packed_content_size + self.packed_padding_size

    def packed(self) -> bytes:
        return b"".join((
            self._struct.pack(self.magic.encode("ascii"), self.root_node_instance_ID, self.unknown, self.object_count),
            *(object_.packed() for object_ in self.objects),
            b"\xff" * self.packed_padding_size,
        ))

    def with_object_replaced(self, index: int, new_object: ScanTreeScriptObject):
        return dataclasses.replace(self, objects=(*self.objects[:index], new_object, *self.objects[index+1:]))

    def with_object_appended(self, new_object: ScanTreeScriptObject):
        return dataclasses.replace(self, object_count=self.object_count+1, objects=self.objects+(new_object,))