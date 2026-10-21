"""Rebuild the production patch in RAM against exact Git blobs, never checkout."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
REPO = "C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree"
COMMIT = "0540c67b33c1a0c2b63cbf5906cef61ef22fba6d"
PREFIX = "promo/ck3_native_war_ai/episode-04-march-logistics/tools/"
BASES = {
    "capture_recorder.py": "a1384fea906d2c810ace78420087aea99b6a4ea29ddc0c8c61a163afd59699d3",
    "window_take.py": "5d5e403d9af9c453c677bb965e5ee1896c4ba6d74b1ba1ccaf26bb907692739b",
}


def apply_hunks(original: str, patch: str) -> str:
    source = original.splitlines(keepends=True)
    changes = patch.splitlines(keepends=True)
    output: list[str] = []
    cursor = 0
    index = 2
    while index < len(changes):
        header = re.match(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@", changes[index])
        if header is None:
            raise ValueError("Invalid patch hunk")
        start = max(0, int(header.group(1)) - 1)
        output.extend(source[cursor:start])
        cursor = start
        index += 1
        while index < len(changes) and not changes[index].startswith("@@"):
            line = changes[index]
            if line[0] in " -":
                if cursor >= len(source) or source[cursor] != line[1:]:
                    raise ValueError("Patch preimage differs")
                cursor += 1
            if line[0] in " +":
                output.append(line[1:])
            if line[0] not in " +-":
                raise ValueError("Unsupported patch member")
            index += 1
    output.extend(source[cursor:])
    return "".join(output)


def definition(source: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise ValueError("Missing definition: " + name)


def main() -> None:
    previous = HERE.parent / "camera-budget-a01"
    if (HERE / "capture_recorder.py").read_bytes() != (previous / "capture_recorder.py").read_bytes():
        raise ValueError("Recorder changed after the prior five fake-Job checks")
    old_window = (previous / "window_take.py").read_bytes()
    old_binding = b'from_capacity(spec.scene, spec.workdir / "raw.mkv", spec.raw_budget_bytes, cap)'
    new_binding = b'from_capacity(spec.workdir, spec.workdir / "raw.mkv", spec.raw_budget_bytes, cap)'
    if old_window.count(old_binding) != 1 or old_window.replace(old_binding, new_binding) != (HERE / "window_take.py").read_bytes():
        raise ValueError("Window delta is not solely the confirmed workdir binding")
    old_monitor = (previous / "capture_budget_monitor.py").read_text(encoding="utf-8")
    addition = "\n\ndef _raise_walk_error(error: OSError) -> None:\n    raise error\n"
    expected_monitor = old_monitor.replace("\n\n@dataclass(frozen=True)", addition + "\n\n@dataclass(frozen=True)")
    expected_monitor = expected_monitor.replace("os.walk(self.root, followlinks=False)",
                                               "os.walk(self.root, followlinks=False, onerror=_raise_walk_error)")
    if expected_monitor != (HERE / "capture_budget_monitor.py").read_text(encoding="utf-8"):
        raise ValueError("Monitor delta exceeds the fail-closed walk callback")
    patches: list[str] = []
    originals: dict[str, str] = {}
    pins: list[dict[str, object]] = []
    for name in ("capture_recorder.py", "window_take.py", "capture_budget_monitor.py"):
        before = b""
        if name in BASES:
            before = subprocess.check_output(["git", "--no-optional-locks", "--no-lazy-fetch",
                "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-C", REPO,
                "show", COMMIT + ":" + PREFIX + name])
            if hashlib.sha256(before).hexdigest() != BASES[name]:
                raise ValueError("Canonical source pin changed")
        after = (HERE / name).read_bytes()
        old = before.decode("utf-8")
        new = after.decode("utf-8")
        patch = "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile="a/" + PREFIX + name if before else "/dev/null", tofile="b/" + PREFIX + name))
        if apply_hunks(old, patch).encode("utf-8") != after:
            raise ValueError("RAM reconstructed bytes differ")
        patches.append(patch)
        originals[name] = old
        pins.append({"name": name, "bytes": len(after), "sha256": hashlib.sha256(after).hexdigest()})
    for name in ("ffmpeg_command", "inspect_owned_client", "validate_client_region", "require_same_source",
                 "finish", "abort", "close", "handle"):
        old_def = definition(originals["capture_recorder.py"], name)
        new_def = definition((HERE / "capture_recorder.py").read_text(), name)
        if ast.dump(old_def) != ast.dump(new_def):
            raise ValueError("Unrelated recorder behavior changed: " + name)
    old_start = definition(originals["window_take.py"], "start")
    new_start = definition((HERE / "window_take.py").read_text(), "start")
    new_start.body = [node for node in new_start.body if not (
        isinstance(node, ast.ImportFrom) and node.module == "capture_budget_monitor") and not (
        isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "budget_monitor"
                                            for target in node.targets))]
    for node in ast.walk(new_start):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "OwnedRecorder":
            node.keywords = [kw for kw in node.keywords if kw.arg != "budget_monitor"]
    if ast.dump(old_start) != ast.dump(new_start):
        raise ValueError("Non-budget window start behavior changed")
    with (HERE / "PRODUCTION-a03.patch").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("".join(patches))
    print(json.dumps({"base_commit": COMMIT, "RAM_patch_rebuild_exact": True,
        "protected_recorder_and_start_behavior_unchanged": True, "pins": pins}))


if __name__ == "__main__":
    main()
