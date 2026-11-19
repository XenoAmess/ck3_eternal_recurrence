"""Exact CK3 build identities shared by stable native wire contracts.

Accepting a frame's identity does not advertise gameplay capabilities. Those
come from the native adapter's hello and its per-build implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class NativeBuildIdentity:
    game_version: str
    executable_sha256: str

    def backend_id(self, suffix: str) -> str:
        return f"ck3-{self.game_version}-native-{suffix}"


CK3_11906 = NativeBuildIdentity(
    "1.19.0.6",
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
)
CK3_12002 = NativeBuildIdentity(
    "1.20.0.2",
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
)
CK3_12003 = NativeBuildIdentity(
    "1.20.0.3",
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
)
CK3_12004 = NativeBuildIdentity(
    "1.20.0.4",
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
)
CK3_1210 = NativeBuildIdentity(
    "1.21.0",
    "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC",
)
NATIVE_BUILD_IDENTITIES = (CK3_11906, CK3_12002, CK3_12003, CK3_12004, CK3_1210)

# Installed-engine metadata for fixture preparation. This executable has no
# qualified native adapter yet; keep it outside NATIVE_BUILD_IDENTITIES.
CK3_121003 = NativeBuildIdentity(
    "1.21.0.3",
    "859F0D380098ADCB130EB9D453458222749FCDF6D46126AD0ED99D78F9A0AA28",
)
ENGINE_BUILD_IDENTITIES = (*NATIVE_BUILD_IDENTITIES, CK3_121003)


@dataclass(frozen=True)
class FlorinFullSource:
    snapshot_id: str
    public_revision: int
    native_revision: int
    date_raw: int
    game_pid: int
    connection_generation: int
    played_character_id: int
    scope_sha256: str


def florin_full_source(snapshot: object, expected_revision: int | None) -> FlorinFullSource:
    """One shared projection of the existing received Full; no query result may invent these fields."""
    if not isinstance(snapshot, dict):
        raise ValueError("actual Florin Full snapshot required")
    diagnostics, actor = snapshot.get("diagnostics"), snapshot.get("played_character")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    if (not isinstance(diagnostics, dict) or not isinstance(hello, dict) or not isinstance(actor, dict)
            or require_exact_native_build(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256")) != CK3_1210
            or hello.get("game_adapter_id") != "ck3-1.21.0-msvc-x64" or hello.get("ck3_build_match") is not True
            or snapshot.get("schema") != "ck3_1210_full_state_v1"
            or require_exact_native_build(snapshot.get("game_version"), snapshot.get("executable_sha256")) != CK3_1210
            or snapshot.get("adapter_id") != "ck3-1.21.0-msvc-x64"
            or snapshot.get("backend") != "ck3-1.21.0-native-headless-main-thread"
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True or actor.get("alive") is not True):
        raise ValueError("control requires exact Florin living paused Full and HELLO")
    revision, native = _florin_positive_uint64(snapshot.get("revision")), _florin_positive_uint64(snapshot.get("native_revision"))
    pid, generation = _florin_positive_uint64(diagnostics.get("bridge_pid")), _florin_positive_uint64(diagnostics.get("connection_generation"))
    date = snapshot.get("date_raw")
    character = actor.get("character_id")
    if (type(character) is not int or not -(2**31) <= character < 2**31 or character == -1
            or type(date) is not int or date < 0 or snapshot.get("snapshot_id") != f"native:{native}"):
        raise ValueError("Full identity/date/player is malformed")
    if type(hello.get("pid")) is not int or hello.get("pid") != pid:
        raise ValueError("Full Game differs from actual HELLO process")
    if expected_revision is not None and (type(expected_revision) is not int or revision != expected_revision):
        raise ValueError("Full differs from requested public revision")
    scope = json.dumps({"episode_run_id": snapshot.get("episode_run_id"),
                        "managed_campaign_run_binding": snapshot.get("managed_campaign_run_binding")},
                       ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    return FlorinFullSource(f"native:{native}", revision, native, date, pid, generation, character,
                            hashlib.sha256(scope).hexdigest())


def _florin_positive_uint64(value: object) -> int:
    if type(value) is not int or not 1 <= value <= 2**64 - 1:
        raise ValueError("Full control requires positive exact revision and Game identity")
    return value


def require_exact_native_build(
    game_version: object, executable_sha256: object,
) -> NativeBuildIdentity:
    """Return the frozen version/SHA pair, rejecting mixed or unknown builds."""
    if isinstance(executable_sha256, str):
        normalized_sha256 = executable_sha256.upper()
        for build in NATIVE_BUILD_IDENTITIES:
            if (
                game_version == build.game_version
                and normalized_sha256 == build.executable_sha256
            ):
                return build
    raise ValueError("native source does not match a frozen exact build")


def require_exact_native_backend(
    game_version: object,
    executable_sha256: object,
    backend_id: object,
    *,
    suffix: str,
) -> NativeBuildIdentity:
    """Bind a versioned native source name to the same exact executable."""
    build = require_exact_native_build(game_version, executable_sha256)
    if backend_id != build.backend_id(suffix):
        raise ValueError("native backend does not match the frozen exact build")
    return build
