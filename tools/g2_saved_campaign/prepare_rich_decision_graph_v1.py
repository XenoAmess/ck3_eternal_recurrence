"""Pure rich delta before new cold metadata; never installs or rewrites receipts."""
from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import PureWindowsPath
import re
from types import MappingProxyType
from typing import TypedDict

from prepare_decision_display_runtime_v1 import transform_feed, transform_queue

MANIFEST = "presentation-c23/SOURCE-PINS-C23.json"
PROVIDER = "ROOT-DECISION-TEXT-PROVIDER-C23.json"
FEED = "root_p37c23_compact_decision_feed.py"
QUEUE = "root_p37c23_sdk_queue.py"
OUTER = "root_c23_canonical_outer.py"
CONTRACT = "decision_display_contract_v1.py"
PRESENTATION = "presentation-c23/g2_saved_campaign/"
CREATOR = frozenset("creator-tools/g2_saved_campaign/" + name for name in (
    "canonical_native_provider_chain_v1.py", "mcp_owned_stdio_binding_v1.py", "sdk_process_custody.py"))
CANONICAL = frozenset((OUTER, QUEUE, "root_native30_supervisor_c23.py",
    "root_checkpoint_bootstrap_c23.py", "launch_sdk_p37c23_owner.py",
    "root_p37c23_mcp_entry.py"))
QUALIFIED = MappingProxyType({
    CONTRACT: (20719, "95624aef8a277ff4f3bc7587dc4dae8624f89bbee6464ef5ce148c16e3d0d3fa"),
    "decision_text_view.py": (12416, "404c4737f77f11846afc6d6bda116e0d2051094d4b81dbd0685b0dd3397aa12e"),
    "decision_text_publisher.py": (29528, "dccf28aa9ccf2657695299cdecd5619f791988e6f801bc81e42f6f6782d787f2"),
})

Record = dict[str, object]


class SourceRef(TypedDict):
    path: str
    bytes: int
    sha256: str


class ManifestRef(SourceRef):
    relative_path: str


@dataclass(frozen=True)
class RichGraph:
    machine_id: str
    runtime_root: str
    root_sources: Mapping[str, bytes]
    display_sources: Mapping[str, bytes]
    policy: bytes
    changed_root: tuple[str, ...]
    changed_display: tuple[str, ...]
    root_refs: tuple[SourceRef, ...]
    display_refs: tuple[ManifestRef, ...]
    canonical_entries: tuple[tuple[str, str], ...]
    external_refs: Mapping[str, SourceRef]
    unchanged_root: int
    unchanged_display: int

    def review(self) -> Record:
        """JSON-domain review for the ordinary cold metadata/Task producer."""
        return {
            "schema": "xar.rich-decision-cold-graph-composition/v1",
            "machine_id": self.machine_id, "runtime_root": self.runtime_root,
            "root_source_count": len(self.root_sources),
            "display_leaf_count": len(self.display_sources),
            "manifest_source_rows": len(self.display_refs),
            "canonical_source_count": len(self.canonical_entries),
            "external_source_count": len(self.external_refs),
            "root_changed": list(self.changed_root),
            "display_changed": list(self.changed_display),
            "unchanged_root": self.unchanged_root,
            "unchanged_source_leaves": self.unchanged_display,
            "files": [{**_ref(PureWindowsPath(self.runtime_root), name, raw), "relative_path": name}
                      for name, raw in sorted(self.display_sources.items())],
            "manifest_files": list(self.display_refs),
            "root_files": list(self.root_refs),
            "source_graph_bytes": sum(map(len, self.display_sources.values())),
            "capture_live_qualified": False,
            "runtime_deployed": False,
            "metadata_must_be_derived_after_this_delta": True,
        }


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _record(value: object) -> Record:
    _require(isinstance(value, dict), "JSON object required")
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: Record = {}
    for key, item in value.items():
        _require(isinstance(key, str), "string JSON keys required")
        if isinstance(key, str):
            result[key] = item
    return result


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("JSON list required")
    return list(value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("nonempty text required")
    return value


def _decode(raw: bytes) -> Record:
    _require(type(raw) is bytes and len(raw) <= 131072, "bounded JSON bytes required")
    value: object = json.loads(raw)
    return _record(value)


def _encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _root(value: str) -> PureWindowsPath:
    _require(isinstance(value, str), "Windows runtime path required")
    path = PureWindowsPath(value)
    _require(path.is_absolute() and ".." not in path.parts, "absolute contained runtime path required")
    return path


def _relative(value: str) -> str:
    _require(isinstance(value, str) and "\\" not in value, "canonical forward relative path required")
    path = PureWindowsPath(value)
    _require(bool(value) and not path.is_absolute() and not path.drive
             and ".." not in path.parts and "." not in value.split("/")
             and path.as_posix() == value, "contained canonical relative path required")
    return value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ref(root: PureWindowsPath, name: str, raw: bytes) -> SourceRef:
    return {"path": str(root / name), "bytes": len(raw), "sha256": _sha(raw)}


def _parse_ref(value: object) -> SourceRef:
    row = _record(value)
    _require(set(row) in ({"path", "bytes", "sha256"}, {"path", "bytes", "sha256", "relative_path"}), "complete source ref required")
    path, size, digest = row["path"], row["bytes"], row["sha256"]
    _require(type(size) is int and 0 < size <= 1048576, "exact bounded integer byte count required")
    _require(isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest) is not None,
             "canonical SHA256 required")
    if type(size) is not int or not isinstance(digest, str):
        raise ValueError("source ref type differs")
    return {"path": _text(path), "bytes": size, "sha256": digest}


def _same_ref(row: SourceRef, expected: SourceRef) -> None:
    _require(PureWindowsPath(row["path"]) == PureWindowsPath(expected["path"])
             and row["bytes"] == expected["bytes"] and row["sha256"] == expected["sha256"],
             "source path/bytes/SHA differs")


def _sources(value: Mapping[str, bytes], *, root_only: bool) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    folded: set[str] = set()
    for name, raw in value.items():
        _relative(name)
        _require(not root_only or name.endswith(".py") and ("/" not in name or name in CREATOR),
                 "root source leaf required")
        _require(type(raw) is bytes and 0 < len(raw) <= 1048576, "bounded immutable source bytes required")
        _require(name.casefold() not in folded, "case-alias source path")
        folded.add(name.casefold())
        if name.endswith(".py"):
            compile(raw, name, "exec")
        result[name] = raw
    return result


def _entries(value: object, sources: Mapping[str, bytes], root: PureWindowsPath,
             names: set[str]) -> None:
    rows = _list(value)
    seen: set[str] = set()
    for value_row in rows:
        row = _list(value_row)
        _require(len(row) == 2, "entry path/SHA pair required")
        path, digest = _text(row[0]), _text(row[1])
        name = PureWindowsPath(path).relative_to(root).as_posix()
        _require(name in names and name not in seen, "source entry set differs")
        _require(PureWindowsPath(path) == root / name and digest == _sha(sources[name]),
                 "source entry pin differs")
        seen.add(name)
    _require(seen == names, "complete source entry set required")


def _external(raw: bytes) -> tuple[str, ast.Assign, dict[str, tuple[int, str]]]:
    text = raw.decode("utf-8")
    tree = ast.parse(text)
    rows = [node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "_C23_EXTERNAL_IMPORT_PINS"
                    for target in node.targets)]
    _require(len(rows) == 1, "one frozen external import pin assignment required")
    value: object = ast.literal_eval(rows[0].value)
    data = _record(value)
    pins: dict[str, tuple[int, str]] = {}
    for name, pair in data.items():
        _require(re.fullmatch("[A-Za-z_][A-Za-z0-9_]*", name) is not None,
                 "external module name differs")
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("external byte/SHA tuple required")
        size, digest = pair
        if type(size) is not int or not isinstance(digest, str):
            raise ValueError("external pin type differs")
        _parse_ref({"path": name, "bytes": size, "sha256": digest})
        pins[name] = (size, digest)
    return text, rows[0], pins


def compose_rich_graph(
    root_sources: Mapping[str, bytes], display_sources: Mapping[str, bytes],
    policy_bytes: bytes, qualified_sources: Mapping[str, bytes], *,
    runtime_root: str, machine_id: str,
) -> RichGraph:
    """Validate retargeted 44/18 and return 45/19; caller derives owner/Task refs.

    Existing runtime-import refs remain; contract is a guarded complete entry.
    """
    root = _root(runtime_root)
    _require(re.fullmatch("[a-z0-9][a-z0-9-]{2,127}", machine_id) is not None,
             "explicit stable machine ID required")
    roots = _sources(root_sources, root_only=True)
    display = _sources(display_sources, root_only=False)
    _require(len(roots) == 44 and CANONICAL <= roots.keys()
             and {FEED, QUEUE, OUTER} <= roots.keys(), "exact predecessor root44 required")
    _require(len(display) == 18 and {MANIFEST, PROVIDER, FEED,
             PRESENTATION + "decision_text_view.py",
             PRESENTATION + "decision_text_publisher.py"} <= display.keys(),
             "exact predecessor display18 required")
    _require(CONTRACT not in roots and PRESENTATION + CONTRACT not in display,
             "rich graph already applied")
    for name in roots.keys() & display.keys():
        _require(roots[name] == display[name], "overlapping graph source bytes differ")
    _require(set(qualified_sources) == set(QUALIFIED), "exact qualified contract/view/publisher required")
    for name, (size, digest) in QUALIFIED.items():
        raw = qualified_sources[name]
        _require(type(raw) is bytes and len(raw) == size and _sha(raw) == digest,
                 "Q02 qualified source differs: " + name)
    policy = _decode(policy_bytes)
    _require(policy.get("machine_id") == machine_id, "policy machine differs")
    _entries(policy.get("entry_source_pins"), roots, root, set(roots))
    _entries(policy.get("canonical_entry_source_pins"), roots, root, set(CANONICAL))
    text, assignment, external = _external(roots[OUTER])
    refs = _record(policy.get("external_import_source_pins"))
    _require(set(refs) == set(external) and FEED.removesuffix(".py") in external,
             "frozen external policy set differs")
    for name, (size, digest) in external.items():
        leaf = name + ".py"
        _require(leaf in roots and (len(roots[leaf]), _sha(roots[leaf])) == (size, digest),
                 "frozen external source differs")
        _same_ref(_parse_ref(refs[name]), _ref(root, leaf, roots[leaf]))
    manifest = _decode(display[MANIFEST])
    _require(manifest.get("machine_id") == machine_id
             and manifest.get("schema") == "xar.display-source-pins-with-frozen-dependency/v1",
             "manifest identity/schema differs")
    rows = _list(manifest.get("files"))
    _require(len(rows) == 18, "predecessor manifest18 required")
    seen: set[str] = set()
    external_rows: list[ManifestRef] = []
    for value in rows:
        row = _record(value)
        name = _text(row.get("relative_path"))
        _require(name not in seen and name != MANIFEST, "duplicate/self manifest row")
        seen.add(name)
        ref = _parse_ref(row)
        if name.startswith("@frozen-host/"):
            _require(name == "@frozen-host/tools/ck3_capture_closed_receipt.py",
                     "unexpected external display dependency")
            _require(PureWindowsPath(ref["path"]).is_absolute() and (ref["bytes"], ref["sha256"]) == (8175,
                "bf5552199a53bea1909fb8271873740b47b06e04f6856998005296b83b495151"),
                "frozen external validator differs")
            external_rows.append({**ref, "relative_path": name})
        else:
            _require(name in display, "manifest source absent")
            _same_ref(ref, _ref(root, name, display[name]))
    _require(len(external_rows) == 1 and seen - {external_rows[0]["relative_path"]}
             == set(display) - {MANIFEST}, "complete predecessor manifest required")
    provider = _decode(display[PROVIDER])
    _require(provider.get("machine_id") == machine_id
             and provider.get("schema") == "xar.p51.decision-provider-source/v1",
             "provider identity/schema differs")
    provided = _record(provider.get("sources"))
    _require(set(provided) == {"decision_text_publisher", "decision_text_view",
             "decision_text_admission", "automatic_continuity"}, "predecessor provider4 required")
    for name, value in provided.items():
        leaf = PRESENTATION + name + ".py"
        _require(leaf in display, "provider source missing")
        _same_ref(_parse_ref(value), _ref(root, leaf, display[leaf]))
    roots[QUEUE] = transform_queue(roots[QUEUE])
    roots[FEED] = transform_feed(roots[FEED])
    display[FEED] = roots[FEED]
    roots[CONTRACT] = qualified_sources[CONTRACT]
    for name, raw in qualified_sources.items():
        display[PRESENTATION + name] = raw
    external[FEED.removesuffix(".py")] = (len(roots[FEED]), _sha(roots[FEED]))
    external[CONTRACT.removesuffix(".py")] = (len(roots[CONTRACT]), _sha(roots[CONTRACT]))
    _require(assignment.end_lineno is not None, "external pin source span missing")
    lines = text.splitlines(keepends=True)
    roots[OUTER] = ("".join(lines[:assignment.lineno - 1])
        + "_C23_EXTERNAL_IMPORT_PINS=" + repr(external) + "\n"
        + "".join(lines[assignment.end_lineno:])).encode("utf-8")
    compile(roots[OUTER], OUTER, "exec")
    next_external = {name: _ref(root, name + ".py", roots[name + ".py"]) for name in external}
    policy["entry_source_pins"] = [[str(root / name), _sha(raw)] for name, raw in sorted(roots.items())]
    policy["canonical_entry_source_pins"] = [[str(root / name), _sha(roots[name])]
                                            for name in sorted(CANONICAL)]
    policy["external_import_source_pins"] = next_external
    provider["sources"] = {name.removesuffix(".py"): _ref(root, PRESENTATION + name, display[PRESENTATION + name])
        for name in ("decision_text_publisher.py", "decision_text_view.py",
                     "decision_text_admission.py", "automatic_continuity.py", CONTRACT)}
    display[PROVIDER] = _encode(provider)
    next_rows: list[ManifestRef] = [{**_ref(root, name, raw), "relative_path": name}
                                    for name, raw in sorted(display.items()) if name != MANIFEST]
    next_rows.extend(external_rows)
    manifest["files"] = next_rows
    display[MANIFEST] = _encode(manifest)
    _require(len(roots) == 45 and len(display) == 19 and len(next_rows) == 19,
             "exact rich graph45/19 required")
    changed_root = tuple(sorted(name for name, raw in roots.items() if root_sources.get(name) != raw))
    changed_display = tuple(sorted(name for name, raw in display.items() if display_sources.get(name) != raw))
    return RichGraph(machine_id, str(root), MappingProxyType(roots), MappingProxyType(display),
        _encode(policy), changed_root, changed_display,
        tuple(_ref(root, name, raw) for name, raw in sorted(roots.items())), tuple(next_rows),
        tuple((str(root / name), _sha(roots[name])) for name in sorted(CANONICAL)),
        MappingProxyType(next_external), len(root_sources) - len(set(root_sources) & set(changed_root)),
        len(display_sources) - len(set(display_sources) & set(changed_display)))
