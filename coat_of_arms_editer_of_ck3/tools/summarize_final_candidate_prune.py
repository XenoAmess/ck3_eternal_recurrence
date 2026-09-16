"""Validate and summarize the immutable seven-picture final-candidate prune run."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _candidate_row(directory: Path) -> dict[str, Any]:
    report = _load(directory / "report.json")
    if report.get("schema") != "ck3-coa-user-picture-final-candidate-prune-v1":
        raise ValueError(f"unexpected report schema: {directory}")
    source = (directory / report["output"]["sourceFile"]).read_bytes()
    preview = (directory / report["output"]["previewFile"]).read_bytes()
    receipt_gzip = (directory / report["necessity"]["completeReceiptFile"]).read_bytes()
    receipt = gzip.decompress(receipt_gzip)
    checks = {
        "sourceSha256": _sha256(source) == report["output"]["sourceSha256"],
        "previewSha256": _sha256(preview) == report["output"]["previewSha256"],
        "receiptSha256": _sha256(receipt) == report["necessity"]["completeReceiptSha256"],
        "receiptGzipSha256": _sha256(receipt_gzip)
        == report["necessity"]["completeReceiptGzipSha256"],
        "receiptBytes": len(receipt) == report["necessity"]["completeReceiptUtf8Bytes"],
        "receiptGzipBytes": len(receipt_gzip)
        == report["necessity"]["completeReceiptGzipBytes"],
        "sourceBytes": len(source) == report["counts"]["utf8BytesAfter"],
        "countEquation": report["counts"]["before"]
        == report["counts"]["after"] + report["counts"]["removed"],
        "necessityCount": report["counts"]["after"]
        == report["necessity"]["retainedInstancesMeasured"],
        "parseErrors": report["output"]["parseErrors"] == 0,
        "serializeParseExact": report["output"]["serializeParseExact"] is True,
        "zeroRegression": all(
            metric["final"][axis] <= metric["initial"][axis] + 1e-12
            for metric in report["metrics"]
            for axis in ("totalLoss", "edgeLoss")
        ),
        "validationResolutions": [metric["resolution"] for metric in report["metrics"]]
        == [96, 230, 512],
    }
    failed = sorted(key for key, passed in checks.items() if not passed)
    if failed:
        raise ValueError(f"{directory} failed: {', '.join(failed)}")
    drift = report["predecessorMetricReproduction"]
    return {
        "picture": directory.parent.name,
        "candidate": int(directory.name.removeprefix("candidate-")),
        "sourceRevision": report["sourceRevision"]["headCommit"],
        "before": report["counts"]["before"],
        "after": report["counts"]["after"],
        "removed": report["counts"]["removed"],
        "utf8BytesBefore": report["input"]["sourceUtf8Bytes"],
        "utf8BytesAfter": report["counts"]["utf8BytesAfter"],
        "fixedPointPasses": report["necessity"]["fixedPointPasses"],
        "evaluatedCandidates": report["necessity"]["evaluatedCandidates"],
        "elapsedMilliseconds": report["elapsedMilliseconds"],
        "predecessorMetricStatus": drift["status"],
        "predecessorTotalLossDelta": drift["totalLossDelta"],
        "predecessorEdgeLossDelta": drift["edgeLossDelta"],
        "checks": checks,
        "evidenceLevel": report["evidenceLevel"],
    }


def summarize(root: Path) -> tuple[dict[str, Any], str]:
    directories = sorted(root.glob("picture-*/candidate-*"))
    rows = [_candidate_row(directory) for directory in directories]
    pictures = sorted({row["picture"] for row in rows})
    if len(rows) != 21 or len(pictures) != 7:
        raise ValueError(f"expected 21 candidates across 7 pictures, got {len(rows)} / {len(pictures)}")
    revisions = sorted({row["sourceRevision"] for row in rows})
    if len(revisions) != 1:
        raise ValueError(f"candidate evidence spans revisions: {revisions}")
    before = sum(row["before"] for row in rows)
    after = sum(row["after"] for row in rows)
    bytes_before = sum(row["utf8BytesBefore"] for row in rows)
    bytes_after = sum(row["utf8BytesAfter"] for row in rows)
    drifted = [row for row in rows if row["predecessorMetricStatus"] != "exact"]
    by_picture = []
    for picture in pictures:
        items = [row for row in rows if row["picture"] == picture]
        by_picture.append({
            "picture": picture,
            "candidates": len(items),
            "before": sum(row["before"] for row in items),
            "after": sum(row["after"] for row in items),
            "removed": sum(row["removed"] for row in items),
            "utf8BytesBefore": sum(row["utf8BytesBefore"] for row in items),
            "utf8BytesAfter": sum(row["utf8BytesAfter"] for row in items),
        })
    summary = {
        "schema": "ck3-coa-user-picture-final-candidate-prune-summary-v1",
        "status": "browser-passed-native-mcp-pending",
        "artifactVersion": root.name,
        "predecessor": "../user-picture-corpus-v14-pareto-budget-1024/",
        "sourceRevision": revisions[0],
        "contract": {
            "prune": "metric-pareto-leave-one-out-fixed-point-v1",
            "assets": "decoded-exact-dds-mip-v1",
            "resolutions": [96, 230, 512],
            "numericLossTolerance": 1e-12,
            "allowedCumulativeTotalLossIncrease": 0,
            "allowedCumulativeEdgeLossIncrease": 0,
        },
        "totals": {
            "pictures": len(pictures),
            "candidates": len(rows),
            "before": before,
            "after": after,
            "removed": before - after,
            "instanceReductionRatio": (before - after) / before,
            "utf8BytesBefore": bytes_before,
            "utf8BytesAfter": bytes_after,
            "utf8BytesRemoved": bytes_before - bytes_after,
            "utf8ByteReductionRatio": (bytes_before - bytes_after) / bytes_before,
            "elapsedMilliseconds": sum(row["elapsedMilliseconds"] for row in rows),
            "evaluatedCandidates": sum(row["evaluatedCandidates"] for row in rows),
            "exactPredecessorMetrics": len(rows) - len(drifted),
            "driftedPredecessorMetrics": len(drifted),
            "maximumAbsolutePredecessorTotalLossDelta": max(
                abs(row["predecessorTotalLossDelta"]) for row in rows
            ),
            "maximumAbsolutePredecessorEdgeLossDelta": max(
                abs(row["predecessorEdgeLossDelta"]) for row in rows
            ),
        },
        "byPicture": by_picture,
        "candidates": rows,
        "evidenceLevel": {
            "browserFixedPointPrune": "passed",
            "completeNecessityReceipts": "passed",
            "serializeParse": "passed",
            "ck3ApplyCopyRoundTrip": "pending-mcp",
            "nativeSpatialPixelComparison": "pending-mcp",
        },
    }
    readme = f"""# 七图最终候选 v15：零退化固定点剪枝

本目录保留 v14 的 21 个 Pareto 候选经完整 DDS/mip 重新渲染后的固定点剪枝结果，未覆盖 v14。

- 状态：浏览器门禁通过；CK3 Apply/Copy 与原生空间像素对照仍待 MCP 验收。
- 来源 commit：`{revisions[0]}`。
- 合同：96/230/512px；总损失与边缘损失累计允许增加量均为 0；数值容差 `1e-12`。
- 实例：{before:,} → {after:,}，删除 {before - after:,}（{(before - after) / before:.2%}）。
- 代码：{bytes_before:,} → {bytes_after:,} UTF-8 bytes，减少 {bytes_before - bytes_after:,}（{(bytes_before - bytes_after) / bytes_before:.2%}）。
- 每个候选包含 `coat_of_arms.txt`、`preview-512.png`、摘要 `report.json` 与完整 `necessity-receipt.json.gz`。
- v14 有 {len(drifted)}/{len(rows)} 个候选的旧指标来自 32px fit-index，与完整 DDS 重渲染不完全一致；v15 门禁统一使用完整 DDS，并保留逐候选漂移量。

复现：

```text
cd coat_of_arms_editer_of_ck3
set COA_RUN_FINAL_CANDIDATE_PRUNE=true
set COA_PRUNE_ARTIFACT_ROOT=docs/coat-of-arms-fit-artifacts/user-picture-corpus-v15-pruned-budget-1024
pnpm exec playwright test e2e/user-picture-final-candidate-prune.spec.ts --workers=3
python tools/summarize_final_candidate_prune.py ../docs/coat-of-arms-fit-artifacts/user-picture-corpus-v15-pruned-budget-1024
```

`summary.json` 是汇总入口；逐候选报告提供源码、预览和完整必要性收据的 SHA-256。
"""
    return summary, readme


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary, readme = summarize(args.root)
    outputs = {
        args.root / "summary.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        args.root / "README.md": readme,
    }
    if args.check:
        for path, expected in outputs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                raise SystemExit(f"stale or missing generated summary: {path}")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
