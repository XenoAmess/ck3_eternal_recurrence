"""Optional exact-three retirement of the superseded first-four implementation.

This contract preserves source bytes as non-executable .py.source artifacts.
It supplies no native, SDK, product, or live qualification.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess


SCHEMA = "ck3-exact-three-source-archive-relocations-v1"
ARCHIVE = "promo/ck3_faith_and_power/episode02/research/first-four-integrated-5608ccf35/"
EXACT_RELOCATIONS = {
    "tools/ck3_mod_acceptance_cases/faith_e02_first_four_integrated_adapter.py": ARCHIVE + "faith_e02_first_four_integrated_adapter.py.source",
    "tools/faith_e02_first_four_integrated_queue.py": ARCHIVE + "faith_e02_first_four_integrated_queue.py.source",
    "tools/test_faith_e02_first_four_integrated_case.py": ARCHIVE + "test_faith_e02_first_four_integrated_case.py.source",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def signature(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class ArchiveRelocationContext:
    """One validator result shared by apply_delta and changed-chain pin checks."""

    def __init__(self, root, commit, delta_pin, rows, selected_pins):
        self.root = root
        self.commit = commit
        self.delta_pin = delta_pin
        self.rows = tuple(rows)
        self.selected_pins = tuple(selected_pins)

    def retired_paths(self, root, commit, delta_path=None):
        require(root.resolve() == self.root and commit == self.commit,
                "Archive relocation context belongs to another Root/commit")
        if delta_path is not None:
            require(signature(Path(delta_path).read_bytes()) == self.delta_pin,
                    "Archive relocation context belongs to another delta")
        return frozenset(row["from"] for row in self.rows)

    def evidence(self):
        return {"schema": SCHEMA, "source_commit": self.commit,
                "relocations": list(self.rows), "selected_source_count": len(self.selected_pins),
                "selected_source_pins_digest": signature(json.dumps(self.selected_pins, sort_keys=True).encode()),
                "scope": "byte-preserving retired source only; no business or native qualification"}


def _selected_sources(root, products_path, product, case_id, case_inputs, binder_command):
    catalog = json.loads(products_path.read_text(encoding="utf-8-sig"))
    cases = [row for row in catalog["products"][product]["cases"] if row["id"] == case_id]
    require(len(cases) == 1, "Archive relocation needs exactly one selected public case")
    case = cases[0]
    # Search current selected data, not unselected archived product entries.
    values = [json.dumps(case, ensure_ascii=True)]
    selected = set((root / "ck3_autonomous_player/src").rglob("*.py"))
    selected.update((root / "tools").glob("ck3_mod_acceptance*.py"))
    selected.add(root / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
    selected.add(root / "promo/ck3_native_war_ai/integration/recorder_job.py")
    adapter = case.get("adapter")
    require(isinstance(adapter, dict), "Archive relocation needs a selected implemented case adapter")
    if "module" in adapter:
        adapter_path = root / Path(*adapter["module"].split(".")).with_suffix(".py")
    else:
        relative = Path(adapter["path"])
        adapter_path = relative if relative.is_absolute() else products_path.parent / relative
    require(adapter_path.is_file(), "Selected adapter source is unavailable after archival")
    selected.add(adapter_path)
    if adapter.get("config"):
        relative = Path(adapter["config"])
        path = root / relative if relative.parts[0] == "tools" else products_path.parent / relative
        values.append(path.read_text(encoding="utf-8-sig"))
    for path in (case_inputs, binder_command):
        if path is not None and path.exists():
            values.append(path.read_text(encoding="utf-8-sig"))
    excluded = {"ck3_mod_acceptance_build_runtime.py", "ck3_mod_acceptance_freeze_sources.py",
                "ck3_mod_acceptance_archive_relocations.py"}
    selected = {path.resolve() for path in selected if path.is_file() and path.name not in excluded}
    return selected, values


def _check_selected_references(root, selected, values):
    tokens = set()
    for old in EXACT_RELOCATIONS:
        tokens.update((old, Path(old).name, Path(old).stem, old[:-3].replace("/", ".")))

    def check(value):
        normalized = value.replace("\\", "/")
        require(not any(re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", normalized) for token in tokens),
                "Retired implementation remains a selected runtime reference: " + value[:180])

    for value in values:
        check(value)
    pending = list(selected)
    visited = set()
    pins = []
    search = (root, root / "tools", root / "ck3_autonomous_player/src",
              root / "tools/ck3_mod_acceptance_cases")
    while pending:
        source = pending.pop().resolve()
        if source in visited:
            continue
        visited.add(source)
        check(source.name)
        raw = source.read_bytes()
        tree = ast.parse(raw.decode("utf-8-sig"), filename=str(source))
        pins.append({"path": str(source), **signature(raw)})
        for node in ast.walk(tree):
            candidates = []
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [item.name for item in node.names]
                if isinstance(node, ast.ImportFrom) and node.module:
                    names += [node.module] + [node.module + "." + item.name for item in node.names]
                for name in names:
                    check(name)
                    relative = Path(*name.split("."))
                    bases = list(search) + [source.parent]
                    if isinstance(node, ast.ImportFrom) and node.level:
                        bases.append(source.parents[node.level - 1])
                    candidates.extend(base / relative.with_suffix(".py") for base in bases)
                    candidates.extend(base / relative / "__init__.py" for base in bases)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                check(node.value)
                if node.value.endswith(".py"):
                    relative = Path(node.value)
                    candidates += [relative] if relative.is_absolute() else [base / relative for base in (*search, source.parent)]
            pending.extend(path for path in candidates if path.is_file() and path.resolve().is_relative_to(root))
    return sorted(pins, key=lambda row: row["path"])


def validate_archive_relocations(delta_path, source, root, commit, products_path,
                                 product, case_id, case_inputs=None, binder_command=None):
    """Validate the optional fixed mapping using current before/after bytes.

    apply_delta still validates the complete committed diff and every row. A
    historical archive receipt, machine, or earlier revision never substitutes
    for these exact current signatures.
    """
    raw = Path(delta_path).read_bytes()
    delta = json.loads(raw.decode("utf-8-sig"))
    if "archive_relocations" not in delta:
        return None
    contract = delta["archive_relocations"]
    require(isinstance(contract, dict) and set(contract) == {"schema", "relocations"}
            and contract["schema"] == SCHEMA, "Unknown or malformed archive relocation contract")
    rows = contract["relocations"]
    require(isinstance(rows, list) and len(rows) == 3
            and all(isinstance(row, dict) and set(row) == {"from", "to"} for row in rows),
            "Archive relocation requires exactly three explicit mappings")
    mapping = {row["from"]: row["to"] for row in rows}
    require(len(mapping) == 3 and mapping == EXACT_RELOCATIONS,
            "Only the reviewed exact-three archive relocation is supported")
    changes = delta["changes"]
    require(len(changes) == len({row["path"] for row in changes}), "Duplicate complete-diff path")
    changed = {row["path"]: row for row in changes}
    root = root.resolve()
    before_tree = subprocess.run(["git", "-C", str(root), "ls-tree", "-z",
                                  delta["base_source_commit"], "--", *EXACT_RELOCATIONS.values()],
                                 check=True, capture_output=True)
    require(before_tree.stdout == b"", "Archive destination already exists in the actual base commit")
    evidence = []
    for old, new in EXACT_RELOCATIONS.items():
        require(old in changed and new in changed, "Archive relocation requires all six complete-diff paths")
        before = source["files"].get(old)
        require(before is not None and changed[old]["before"] == before and changed[old]["after"] is None,
                "Retired source differs from the frozen global source index")
        require(new not in source["files"] and changed[new]["before"] is None,
                "Archive destination must be a newly added path, never an overwrite")
        original = root / old
        target = root / new
        require(not original.exists() and not original.is_symlink(), "Retired source still exists")
        require(target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(root),
                "Archive destination must be a contained ordinary source artifact")
        after = signature(target.read_bytes())
        require(after == before == changed[new]["after"], "Archive relocation must preserve exact current source bytes")
        evidence.append({"from": old, "to": new, **after})
    selected, values = _selected_sources(root, products_path.resolve(), product, case_id, case_inputs, binder_command)
    pins = _check_selected_references(root, selected, values)
    return ArchiveRelocationContext(root, commit, signature(raw), evidence, pins)
