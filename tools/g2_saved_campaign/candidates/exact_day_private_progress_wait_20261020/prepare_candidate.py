"""Exact Source25 RAM transform; no runtime adoption or output writer."""
from __future__ import annotations

import ast
import difflib
import hashlib
from pathlib import Path
import subprocess

COMMIT = "9b791aae9bb1314162aa5cab923e6cca2892e6d8"
DRIVER_PATH = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
SIZE = 1644164
SHA256 = "4bb87a5519d0804fb668b7c1dfebc7901191e680e417c4238dc2b14d478ac28a"
OWN = Path(__file__).resolve().parent
HELPER = "exact_day_private_progress_wait_v1.py"
CHANGED = "NativeHeadlessGameplayDriver._wait_for_life_advance_change"
BEFORE = b'''            if self.state.snapshot_supported():
                self.state.wait_for_public_change(after_revision, timeout)
            changed = self.take_internal_semantic_snapshot()
'''
AFTER = b'''            if self.state.snapshot_supported():
                progress = getattr(self, "_exact_clock_wait_progress_v1", None)
                if progress is None:
                    self.state.wait_for_public_change(after_revision, timeout)
                else:
                    from .exact_day_private_progress_wait_v1 import wait_for_exact_day_receipt_v1
                    if not wait_for_exact_day_receipt_v1(
                        self.state, after_revision, timeout, before_snapshot, progress,
                    ):
                        self.state.wait_for_public_change(after_revision, timeout)
            changed = self.take_internal_semantic_snapshot()
'''


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read_input():
    raw = subprocess.run(["git", "show", COMMIT + ":" + DRIVER_PATH],
                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("exact immutable Source25 Driver differs")
    return raw


def function_nodes(raw):
    result = {}
    def visit(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + ".")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result[prefix + node.name] = node
    visit(ast.parse(raw).body)
    return result


def compose(raw):
    if pin(raw) != {"bytes": SIZE, "sha256": SHA256} or raw.count(BEFORE) != 1:
        raise ValueError("unique Source25 preimage differs")
    generated = raw.replace(BEFORE, AFTER, 1)
    if generated.count(AFTER) != 1 or generated.replace(AFTER, BEFORE, 1) != raw:
        raise ValueError("full Driver inverse failed")
    before, after = function_nodes(raw), function_nodes(generated)
    changed = {name for name in before.keys() | after.keys()
               if ast.dump(before.get(name)) != ast.dump(after.get(name))}
    if changed != {CHANGED}:
        raise ValueError("unowned Driver function changed: " + repr(changed))
    helper = (OWN / HELPER).read_bytes()
    for name, value in (("native_driver.py", generated), (HELPER, helper)):
        compile(value, name, "exec", dont_inherit=True)
    patch = "".join(difflib.unified_diff(raw.decode().splitlines(True),
        generated.decode().splitlines(True), fromfile="Source25/native_driver.py",
        tofile="candidate/native_driver.py", n=4)).encode()
    return {"native_driver.py": generated, HELPER: helper}, patch, sorted(changed)
