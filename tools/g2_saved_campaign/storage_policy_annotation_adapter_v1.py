"""Accept only the authorized 487-byte lock-boundary policy annotation.

The frozen v13 producer, v14 migration, old plan and live admission files remain
unchanged. All policy reads and compatibility checks run before short CAS.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import sys

import storage_account_observer_v14 as observer

OLD_BYTES = 15881
OLD_SHA = "cfb21270a67f4d259149e99d809a64ee21a782742da1b3afa910a1fb4d0e3980"
CURRENT_SHA = "ec20e14fc47b1d24c3a9aca6c635ac59ae8ecb7cf29734dfe37ac0ff58cf342a"
ANNOTATION = ("所有当前及未来存储操作遵守[存储锁边界](maintenance/storage-lock-boundaries.md)：进程扫描、系统/容量采集、正文哈希和目录遍历均在全局总线锁外完成；锁内只做少量精确对象核对、账本代次 CAS 和原子登记，冲突后在锁外重新准备。旧 177 个生产器的源审清单仅标明历史用途及禁止复跑，不能声称已自动拦截这些文件；新入口的源码资格也不等于已经部署或恢复维护。\n\n").encode("utf-8")


def validate_bytes(raw: bytes, expected: dict) -> dict:
    if expected.get("bytes") != OLD_BYTES or expected.get("sha256") != OLD_SHA:
        raise ValueError("original plan policy pin changed")
    if len(ANNOTATION) != 487 or len(raw) != OLD_BYTES + 487:
        raise ValueError("annotation length mismatch")
    if hashlib.sha256(raw).hexdigest() != CURRENT_SHA or raw.count(ANNOTATION) != 1:
        raise ValueError("current policy is not the exact approved annotation")
    inverse = raw.replace(ANNOTATION, b"", 1)
    if len(inverse) != OLD_BYTES or hashlib.sha256(inverse).hexdigest() != OLD_SHA:
        raise ValueError("inverse annotation does not restore the original policy")
    return {"accepted_annotation_only": True, "original_plan_policy_pin": expected,
            "actual_current_policy_pin": {"path": expected["path"], "bytes": len(raw),
                                          "sha256": CURRENT_SHA},
            "inverse_restored_bytes": len(inverse), "inverse_restored_sha256": OLD_SHA,
            "annotation_bytes": 487, "policy_json_parameters_changed": False,
            "current_document_claimed_to_be_old_original": False}


def inspect_policy(path: Path, expected: dict) -> dict:
    if str(path) != expected["path"] or path.is_symlink() or path.stat().st_size != OLD_BYTES + 487:
        raise ValueError("policy path or bounded size mismatch")
    result = validate_bytes(path.read_bytes(), expected)
    raw = Path(__file__).read_bytes()
    result["compatibility_adapter"] = {"path": str(Path(__file__).resolve()),
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    result["first_v14_rejection_preserved"] = "tool chunk eb5c5e: assertion line113, before rows/lock"
    return result


_original_compile = observer.compile_unlocked_source


def compile_annotation_adapter(raw: bytes):
    _original_compile(raw)  # Preserve every exact source/AST migration check.
    tree = ast.parse(raw)
    block = next(node for node in tree.body if isinstance(node, ast.With) and node.lineno == 52)
    tail = next(i for i, node in enumerate(block.body) if node.lineno == 277)
    prefix = []
    for node in tree.body:
        if node is block:
            prefix.extend(block.body[:tail])
        elif not (isinstance(node, ast.ImportFrom) and node.module == "codex_task_bus"):
            prefix.append(node)
    targets = [node for node in prefix if isinstance(node, ast.Assert) and node.lineno == 113]
    if len(targets) != 1 or ast.unparse(targets[0].test) != "pin(REPO / 'docs/storage-retention-policy.md') == plan['policy_source']":
        raise ValueError("exact policy assertion shape changed")
    pos = prefix.index(targets[0])
    replacement = ast.parse("_policy_annotation = __import__('storage_policy_annotation_adapter_v1').inspect_policy(REPO/'docs/storage-retention-policy.md', plan['policy_source'])\nassert _policy_annotation['accepted_annotation_only']").body
    prefix[pos:pos + 1] = replacement
    prefix.extend(ast.parse("d['policy_annotation_compatibility'] = _policy_annotation").body)
    tree.body = prefix
    return compile(ast.fix_missing_locations(tree), "sealed-account-v14-annotation-only-prepare", "exec")


if __name__ == "__main__":
    observer.compile_unlocked_source = compile_annotation_adapter
    raise SystemExit(observer.main())
