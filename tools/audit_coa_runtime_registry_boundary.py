#!/usr/bin/env python3
"""Freeze the exact-build boundary around CK3's CoA runtime registry.

This audit deliberately does not turn binary strings into an ABI claim.  It
proves that the exact executable contains relevant semantic labels while the
checked-in public tools continue to expose only static source catalogs and a
direct-DDS mount projection with explicit negative provenance flags.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Final


EXPECTED_BUILD: Final = "1.19.0.6"
EXPECTED_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
REGISTRY_MARKERS: Final = (
    b"coat_of_arms_manager_database_values",
    b"coat_of_arms_manager_database_keys",
    b"coat_of_arms_manager_database",
    b"coat_of_arms_manager_name_map_values",
    b"coat_of_arms_manager_name_map_keys",
    b"coat_of_arms_manager_name_map",
    b"coat_of_arms_manager",
    b"coat_of_arms_dynamic_definitions",
    b"coat_of_arms_script_database",
)
EMBEDDED_PATH_MARKERS: Final = frozenset({
    b"coat_of_arms_dynamic_definitions",
    b"coat_of_arms_script_database",
})
INSPECTED_SOURCES: Final = (
    Path("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"),
    Path("ck3_autonomous_player/src/xar_autoplayer/coat_of_arms_definitions.py"),
    Path("ck3_autonomous_player/src/xar_autoplayer/coat_of_arms_vfs_resolution.py"),
)
REQUIRED_BOUNDARY_TOKENS: Final = {
    INSPECTED_SOURCES[0]: (
        "ck3_query_coat_of_arms_definition_catalog_v1",
        "ck3_read_coat_of_arms_definition_v1",
        "ck3_project_coat_of_arms_vfs_asset_winner_v1",
    ),
    INSPECTED_SOURCES[1]: (
        '"engine_mount_observed": False',
        '"vfs_winner_claimed": False',
        '"dlc_and_mod_overrides_included": False',
    ),
    INSPECTED_SOURCES[2]: (
        '"engine_resolver_called": False',
        '"resource_registration_observed": False',
        '"replace_path_applied": False',
        '"definition_merge_applied": False',
        '"claim_scope": "direct_dds_path_winner_projection_only"',
    ),
}
FORBIDDEN_PUBLIC_TOOL_TOKENS: Final = (
    "ck3_query_coat_of_arms_runtime_registry",
    "ck3_read_coat_of_arms_runtime_definition",
    "ck3_resolve_coat_of_arms_runtime_resource",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def find_ascii_markers(data: bytes) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for marker in REGISTRY_MARKERS:
        offsets: list[int] = []
        start = 0
        while True:
            offset = data.find(marker, start)
            if offset < 0:
                break
            before_is_boundary = offset == 0 or data[offset - 1] == 0
            after = offset + len(marker)
            after_is_boundary = after == len(data) or data[after] == 0
            if marker in EMBEDDED_PATH_MARKERS or (
                before_is_boundary and after_is_boundary
            ):
                offsets.append(offset)
            start = offset + 1
        rows.append({"marker": marker.decode("ascii"), "offsets": offsets})
    return rows


def audit_repository_contract(root: Path) -> dict[str, object]:
    receipts: list[dict[str, object]] = []
    combined = ""
    for relative_path in INSPECTED_SOURCES:
        path = root / relative_path
        data = path.read_bytes()
        text = data.decode("utf-8")
        missing = [
            token for token in REQUIRED_BOUNDARY_TOKENS[relative_path]
            if token not in text
        ]
        if missing:
            raise RuntimeError(f"{relative_path} lost boundary tokens: {missing}")
        combined += "\n" + text
        receipts.append({
            "path": relative_path.as_posix(),
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        })
    leaked = [token for token in FORBIDDEN_PUBLIC_TOOL_TOKENS if token in combined]
    if leaked:
        raise RuntimeError(f"unverified runtime registry tools are public: {leaked}")
    return {
        "source_receipts": receipts,
        "required_negative_provenance_present": True,
        "unverified_runtime_registry_tools_public": False,
    }


def build_evidence(root: Path, executable: Path) -> dict[str, object]:
    executable_data = executable.read_bytes()
    executable_sha256 = sha256_bytes(executable_data)
    if executable_sha256 != EXPECTED_EXECUTABLE_SHA256:
        raise RuntimeError(
            "CK3 executable does not match the frozen 1.19.0.6 build: "
            f"{executable_sha256}"
        )
    markers = find_ascii_markers(executable_data)
    missing = [row["marker"] for row in markers if not row["offsets"]]
    if missing:
        raise RuntimeError(f"exact executable lost expected CoA manager labels: {missing}")
    repository = audit_repository_contract(root)
    return {
        "schema": "ck3-coat-of-arms-runtime-registry-boundary-v1",
        "schema_version": 1,
        "status": "bounded_negative",
        "ck3_build": EXPECTED_BUILD,
        "executable": {
            "path": str(executable.resolve()),
            "bytes": len(executable_data),
            "sha256": executable_sha256,
        },
        "binary_semantic_labels": markers,
        "repository_contract": repository,
        "conclusion": {
            "runtime_manager_labels_present": True,
            "verified_registry_accessor_or_layout": False,
            "verified_engine_definition_winner_query": False,
            "verified_engine_resource_winner_query": False,
            "safe_public_upgrade_available": False,
            "retained_product_contract": "resolved_overlay_or_base_game_hash_bound_projection",
        },
        "claim_boundary": (
            "ASCII labels establish only that the exact executable names internal CoA manager "
            "state. They do not identify a callable accessor, object lifetime, container layout, "
            "definition merge rule, resource resolver, or source provenance. Until those have an "
            "exact-build ABI contract and native read-only proof, the product must keep static "
            "definition catalogs and direct-DDS projection explicitly separate from engine truth."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ck3-executable", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = build_evidence(args.root.resolve(), args.ck3_executable.resolve())
    rendered = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
