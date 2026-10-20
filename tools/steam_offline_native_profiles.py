"""Immutable exact native SteamUI profiles; no state observation or wire schema.

Source-only image lookup is not admission. Native provider and public gate both
join the same Steam incarnation version to the actual UI size/digest through
select_profile; a version and an approved unrelated image never form a profile.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Final


@dataclass(frozen=True, slots=True)
class NativeOfflineProfile:
    profile_id: str
    steam_version: str
    image_sha256: str
    image_bytes: int
    image_size: int
    value_rva: int
    tray_manager_rva: int
    tray_offset: int
    producer_rva: int
    producer: bytes
    anchors: tuple[tuple[int, bytes], ...]


PROFILE_1096: Final[NativeOfflineProfile] = NativeOfflineProfile(
    'steamui-10.96.30.42-cb387ade', '10.96.30.42',
    'cb387adefbbac64a3c1490d4275d00daf3a1e0219b4580726ef7681db7429278',
    18962584, 19238912, 0x1123627, 0x1121AA0, 0x154, 0x616D0C,
    bytes.fromhex('440fb60513c9b000488d157d3b7400488bcbe81d9e3b00'),
    ((0x616D0C, bytes.fromhex('440fb60513c9b000488d157d3b7400488bcbe81d9e3b00')),
     (0x5D39B0, bytes.fromhex('40534883ec20488bd9e852d8f2ff488bc8488b10ff92880000008883e70100004883c4205bc3')),
     (0x6869DF, bytes.fromhex('488d0d5acaa900e8c5cff4ff')),
     (0x6158E4, bytes.fromhex('803d3cddb000007419488b0dacc1b0004533c0ba04000000e81fc7f6ff')),
     (0x582038, bytes.fromhex('8bfa4c8bf1490f45f03b9154010000')),
     (0x582071, bytes.fromhex('4189be54010000'))),
)
PROFILE_1112: Final[NativeOfflineProfile] = NativeOfflineProfile(
    'steamui-11.12.30.7-1b945794', '11.12.30.7',
    '1b9457943205dc3af0bd53463ba331cbd2a381388699705c02271aac7a2b1252',
    19449496, 19730432, 0x1194EC7, 0x11932E0, 0x154, 0x63EA4C,
    bytes.fromhex('440fb6057364b500488d150da37700488bcbe83d703d00'),
    ((0x63EA4C, bytes.fromhex('440fb6057364b500488d150da37700488bcbe83d703d00')),
     (0x5F7D00, bytes.fromhex('40534883ec20488bd9e8c280f2ff488bc8488b10ff92880000008883870100004883c4205bc3')),
     (0x6B2FFF, bytes.fromhex('488d0d3a1dae00e8f54cf4ff')),
     (0x63D524, bytes.fromhex('803d9c79b500007419488b0dac5db5004533c0ba04000000e87f53f6ff')),
     (0x5A28DE, bytes.fromhex('8bfa4c8bf13b9154010000')),
     (0x5A290E, bytes.fromhex('4189be54010000'))),
)
PROFILES: Final[tuple[NativeOfflineProfile, ...]] = (PROFILE_1096, PROFILE_1112)


def _source_key(image_bytes: int, image_sha256: str) -> tuple[int, str]:
    if type(image_bytes) is not int or image_bytes <= 0:
        raise ValueError('Exact positive UI byte count required')
    if type(image_sha256) is not str or re.fullmatch('[0-9a-f]{64}', image_sha256) is None:
        raise ValueError('Exact lowercase UI SHA256 required')
    return image_bytes, image_sha256


def source_profile(image_bytes: int, image_sha256: str) -> NativeOfflineProfile:
    """Resolve file-only anchors; caller must still join the Steam version."""
    key = _source_key(image_bytes, image_sha256)
    matches = tuple(p for p in PROFILES if (p.image_bytes, p.image_sha256) == key)
    if len(matches) != 1:
        raise ValueError('SteamUI source is not one unique exact profile')
    return matches[0]


def select_profile(steam_version: str, image_bytes: int,
                   image_sha256: str) -> NativeOfflineProfile:
    if type(steam_version) is not str:
        raise ValueError('Exact Steam version string required')
    profile = source_profile(image_bytes, image_sha256)
    if steam_version != profile.steam_version:
        raise ValueError('Steam incarnation and SteamUI source cross profiles')
    return profile


def supported_version(steam_version: str) -> bool:
    """Identity prefilter only, never version-only source admission."""
    return type(steam_version) is str and any(p.steam_version == steam_version for p in PROFILES)
