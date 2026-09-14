"""Print SHA-256 digests for one or more files without a shell-specific cmdlet."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.paths:
        resolved = path.expanduser().resolve()
        print(f"{sha256_file(resolved)}  {resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
