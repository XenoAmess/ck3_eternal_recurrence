from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
action, *args = sys.argv[1:]
if action == "tree":
    root = Path(args[0])
    patterns = args[1:] or ["*"]
    for pattern in patterns:
        for p in root.rglob(pattern):
            if p.is_file():
                print(p)
elif action == "read":
    p = Path(args[0])
    start = int(args[1]) if len(args) > 1 else 1
    end = int(args[2]) if len(args) > 2 else 10000000
    for n, line in enumerate(p.read_text(encoding="utf-8-sig").splitlines(), 1):
        if start <= n <= end:
            print(f"{n}: {line}")
elif action == "search":
    root, needle = Path(args[0]), args[1]
    patterns = args[2:] or ["*.md", "*.json", "*.py"]
    for pattern in patterns:
        for p in root.rglob(pattern):
            if not p.is_file():
                continue
            try:
                lines = p.read_text(encoding="utf-8-sig").splitlines()
            except (UnicodeError, OSError):
                continue
            for n, line in enumerate(lines, 1):
                if needle.casefold() in line.casefold():
                    print(f"{p}:{n}:{line}")
elif action == "chapter":
    p = Path(args[0])
    obj = json.loads(p.read_text(encoding="utf-8-sig"))
    for chapter in obj.get("chapters", []):
        if chapter.get("id") == args[1]:
            print(json.dumps(chapter, ensure_ascii=False, indent=2))
elif action == "hash":
    for arg in args:
        p = Path(arg)
        if p.is_file():
            b = p.read_bytes()
            print(json.dumps({"path": str(p), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}, ensure_ascii=False))
        else:
            print(json.dumps({"path": str(p), "missing": True}))
elif action == "keys":
    obj = json.loads(Path(args[0]).read_text(encoding="utf-8-sig"))
    if isinstance(obj, dict):
        for k, v in obj.items():
            print(k, type(v).__name__, len(v) if isinstance(v, (dict, list, str)) else "")
    else:
        print(type(obj).__name__, len(obj))
elif action == "pick":
    obj = json.loads(Path(args[0]).read_text(encoding="utf-8-sig"))
    for key in args[1].split("/"):
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    print(json.dumps(obj, ensure_ascii=False, indent=2))
