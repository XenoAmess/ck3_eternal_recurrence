#!/usr/bin/env python3
"""Generate a deterministic inventory and lightweight syntax census for a CK3 mod."""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import Counter
from pathlib import Path

IDENT = r"[A-Za-z_][A-Za-z0-9_.-]*"
ASSIGN_RE = re.compile(rf"(?m)(?<![\w$])({IDENT})\s*=")
BLOCK_RE = re.compile(rf"(?m)(?<![\w$])({IDENT})\s*=\s*\{{")
COMPARISON_RE = re.compile(r"(?<![=!<>])(?:!=|<=|>=|=|<|>|\?=)(?![=])")

def strip_comments(text: str) -> tuple[str, int]:
    out, comments = [], 0
    for line in text.splitlines(keepends=True):
        match = re.search(r"(?://|#)", line)
        if match:
            comments += 1
            line = line[:match.start()] + ("\n" if line.endswith("\n") else "")
        out.append(line)
    return "".join(out), comments

def census(data: bytes) -> dict:
    text = data.decode("utf-8-sig", errors="replace")
    clean, comment_lines = strip_comments(text)
    assignments = Counter(name.casefold() for name in ASSIGN_RE.findall(clean))
    blocks = Counter(name.casefold() for name in BLOCK_RE.findall(clean))
    return {
        "lines": len(text.splitlines()), "comment_lines": comment_lines,
        "bytes_utf8": len(data), "bom": data.startswith(b"\xef\xbb\xbf"),
        "constructs": {
            "blocks": clean.count("{"), "lists": clean.count("["),
            "comparisons": len(COMPARISON_RE.findall(clean)),
            "scope_references": len(re.findall(r"\b(?:ROOT|THIS|PREV|FROM|scope):", clean)),
            "scripted_variables": len(re.findall(r"@[A-Za-z_][A-Za-z0-9_.-]*|\$[^$\n]+\$", clean)),
            "strings": len(re.findall(r'"(?:\\.|[^"\\])*"', clean)),
        },
        "opcode_frequency": dict(sorted(assignments.items(), key=lambda kv: (-kv[1], kv[0]))),
        "block_frequency": dict(sorted(blocks.items(), key=lambda kv: (-kv[1], kv[0]))),
    }

def build_manifest(root: Path) -> dict:
    files = sorted((p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".gui"}), key=lambda p: p.relative_to(root).as_posix())
    entries, totals, opcode, blocks = [], Counter(), Counter(), Counter()
    for path in files:
        data = path.read_bytes(); rel = path.relative_to(root).as_posix(); info = census(data)
        entries.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), **info})
        totals.update(files=1, bytes_utf8=len(data), lines=info["lines"], comment_lines=info["comment_lines"])
        totals.update(info["constructs"]); opcode.update(info["opcode_frequency"]); blocks.update(info["block_frequency"])
    return {"schema": "open_kaishek.corpus-manifest.v1", "profile": "ck3-1.19.0.6/mod_zhongguo_style", "source": "mod_zhongguo_style (relative paths only; source contents are not embedded)", "file_extensions": [".txt", ".gui"], "files": entries, "totals": dict(totals), "opcode_frequency": dict(sorted(opcode.items(), key=lambda kv: (-kv[1], kv[0]))), "block_frequency": dict(sorted(blocks.items(), key=lambda kv: (-kv[1], kv[0])))}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir(): parser.error(f"corpus root does not exist: {root}")
    manifest = build_manifest(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Path.write_text delegates newline conversion to the host platform.
    # Emit explicit LF bytes so the checked-in manifest and its recorded hash
    # are identical on Windows and POSIX builders.
    payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.write_bytes(payload)
    print(f"wrote {manifest['totals'].get('files', 0)} files to {args.output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
