# Source: http://www.metroid2002.com/retromodding/wiki/SCAN_(Metroid_Prime_2)

import dataclasses
import struct

from dgrp import DGRP
from scly_common import Property, PropertyStruct, ScriptObject
from util import unpack_bool, unpack_bool_from_int, unpack_int, unpack_float, unpack_ascii, \
    unpack_null_terminated_ascii, pack_ascii

__all__ = ("AnimationParameters", "ScannableObjectInfo", "ScanInfoSecondaryModel", "SCAN")


class AnimationParameters(PropertyStruct):
    pass


@dataclasses.dataclass(frozen=True)
class ScannableObjectInfo(ScriptObject):
    _secondary_model_property_IDs = (
        0x1C5B4A3A,
        0x8728A0EE,
        0xF1CD99D3,
        0x6ABE7307,
        0x1C07EBA9,
        0x8774017D,
        0xF1913840,
        0x6AE2D294,
        0x1CE2091C,
    )

    scan_text_asset_ID: int = dataclasses.field(init=False, repr=False)
    slow: bool = dataclasses.field(init=False)
    important: bool = dataclasses.field(init=False)
    use_logbook_model_after_scan: bool = dataclasses.field(init=False)
    post_scan_override_texture_asset_ID: int = dataclasses.field(init=False, repr=False)
    logbook_default_x_rotation: float = dataclasses.field(init=False)
    logbook_default_z_rotation: float = dataclasses.field(init=False)
    logbook_scale: float = dataclasses.field(init=False)
    logbook_model_asset_ID: int = dataclasses.field(init=False, repr=False)
    logbook_animation_set: AnimationParameters = dataclasses.field(init=False, repr=False)
    secondary_models: tuple = dataclasses.field(init=False, repr=False)

    def __post_init__(self):
        self._set_fields_from_property_data(
            ("scan_text_asset_ID",                  0x2F5B6423, unpack_int),
            ("slow",                                0xC308A322, unpack_bool_from_int),
            ("important",                           0xC308A322, unpack_bool_from_int),
            ("use_logbook_model_after_scan",        0x1733B1EC, unpack_bool),
            ("post_scan_override_texture_asset_ID", 0x53336141, unpack_int),
            ("logbook_default_x_rotation",          0x3DE0BA64, unpack_float),
            ("logbook_default_z_rotation",          0x2ADD6628, unpack_float),
            ("logbook_scale",                       0xD0C15066, unpack_float),
            ("logbook_model_asset_ID",              0xB7ADC418, unpack_int),
        )

        object.__setattr__(self, "logbook_animation_set", self.base_property_struct.get_subproperty_by_ID(0x15694EE1))

        secondary_models = []
        for ID in self._secondary_model_property_IDs:
            secondary_models.append(self.base_property_struct.get_subproperty_by_ID(ID))
        object.__setattr__(self, "secondary_models", tuple(secondary_models))

    @classmethod
    def from_packed(cls, packed: bytes):
        return super().from_packed(packed, {
            0x15694EE1: AnimationParameters,
            0x58F9FE99: AnimationParameters,
            **{ID: ScanInfoSecondaryModel for ID in cls._secondary_model_property_IDs},
        })


@dataclasses.dataclass(frozen=True)
class ScanInfoSecondaryModel(PropertyStruct):
    model_asset_ID: int = dataclasses.field(init=False)
    animation_set: AnimationParameters = dataclasses.field(init=False)
    attach_bone_name: str = dataclasses.field(init=False)

    def __post_init__(self):
        super().__post_init__()

        self._set_fields_from_subproperty_data(
            ("model_asset_ID",   0x1F7921BC, unpack_int),
            ("attach_bone_name", 0x3EA2BED8, unpack_null_terminated_ascii),
        )

        object.__setattr__(self, "animation_set", self.get_subproperty_by_ID(0xCDD202D1))

    @classmethod
    def from_packed(cls, packed: bytes):
        return super().from_packed(packed, {
            0xCDD202D1: AnimationParameters,
        })


@dataclasses.dataclass(frozen=True)
class SCAN:
    asset_type = "SCAN"

    _struct = struct.Struct(">4sIBI")

    magic: str
    unknown_1: int
    unknown_2: int
    object_count: int
    scannable_object_info: ScannableObjectInfo = dataclasses.field(repr=False)
    dependencies: DGRP = dataclasses.field(repr=False)

    @classmethod
    def from_packed(cls, packed: bytes):
        magic, unknown_1, unknown_2, object_count = cls._struct.unpack(packed[:13])
        scannable_object_info = ScannableObjectInfo.from_packed(packed[13:])

        return cls(
            unpack_ascii(magic),
            unknown_1,
            unknown_2,
            object_count,
            scannable_object_info,
            DGRP.from_packed(packed[13+scannable_object_info.packed_size:]),
        )

    @property
    def packed_size(self) -> int:
        return 4 + 4 + 1 + 4 + self.scannable_object_info.packed_size + self.dependencies.packed_size

    def packed(self) -> bytes:
        return b"".join((
            self._struct.pack(pack_ascii(self.magic), self.unknown_1, self.unknown_2, self.object_count),
            self.scannable_object_info.packed(),
            self.dependencies.packed(),
        ))

    def with_scannable_object_info_replaced(self, new_scannable_object_info: ScannableObjectInfo):
        return dataclasses.replace(self, scannable_object_info=new_scannable_object_info)