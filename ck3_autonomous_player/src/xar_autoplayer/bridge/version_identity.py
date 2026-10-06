"""Exact CK3 build identities shared by stable native wire contracts.

Accepting a frame's identity does not advertise gameplay capabilities. Those
come from the native adapter's hello and its per-build implementation.
"""

from __future__ import annotations

from dataclasses import dataclass


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
NATIVE_BUILD_IDENTITIES = (CK3_11906, CK3_12002, CK3_12003, CK3_12004)


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
