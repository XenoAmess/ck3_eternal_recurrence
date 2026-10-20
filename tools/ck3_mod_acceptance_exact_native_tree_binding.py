"""Validate the explicit nonancestor exact-Native-tree compiled closure.

This contract is metadata only. Every source byte and the complete ordinary
Native qualification remain independently checked by the calling consumers.
"""
from __future__ import annotations
import re

SCHEMA = "ck3-native-worktree-exact-tree-source-binding-v1"

def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)

def validate_pin(value: object) -> None:
    require(isinstance(value, dict), "Exact-tree compiled reference must be an object")
    if not isinstance(value, dict):
        raise ValueError("Exact-tree compiled reference must be an object")
    require(set(value) == {"path", "bytes", "sha256"}, "Exact-tree compiled reference fields differ")
    path, size, digest = value.get("path"), value.get("bytes"), value.get("sha256")
    require(isinstance(path, str) and bool(path) and type(size) is int and size > 0
            and isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest) is not None,
            "Exact-tree compiled reference must have a path, exact integer size and SHA256")

def validate_compiled_inputs(declared: object, actual: object) -> None:
    require(isinstance(declared, dict), "Explicit exact-tree compiled inputs required")
    if not isinstance(declared, dict):
        raise ValueError("Explicit exact-tree compiled inputs required")
    refs = {"configured_scope", "codemodel", "compile_commands", "production_freeze", "published_dll"}
    require(set(declared) == refs | {"production_TUs", "unique_production_source_count", "production_source_set_sha256"},
            "Exact-tree compiled input fields differ")
    for name in refs:
        validate_pin(declared[name])
    counts = declared.get("production_TUs")
    require(isinstance(counts, dict) and bool(counts), "Exact-tree production TU counts required")
    if not isinstance(counts, dict):
        raise ValueError("Exact-tree production TU counts required")
    require(all(isinstance(name, str) and name and type(n) is int and n > 0 for name, n in counts.items()),
            "Exact-tree production TU counts must be positive exact integers")
    total, digest = declared.get("unique_production_source_count"), declared.get("production_source_set_sha256")
    require(type(total) is int and total > 0 and isinstance(digest, str)
            and re.fullmatch("[0-9a-f]{64}", digest) is not None,
            "Exact-tree production body count/fingerprint invalid")
    require(declared == actual, "Explicit exact-tree compiled inputs differ from actual original FileAPI/commands/DLL")
