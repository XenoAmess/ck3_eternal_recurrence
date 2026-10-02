"""Build/verify the maintained de jure conquest staging with shared release code."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from product import PRODUCT_ID, ROOT, SOURCE, TAG_PREFIX, VERSION, product_spec


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True, capture_output=True,
        text=True, encoding="utf-8",
    ).stdout.strip()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--verify", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / PRODUCT_ID)
    parser.add_argument("--workshop-item-id")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    try:
        spec = product_spec()
        from independent_mod_release import build, check_reproducible, verify_manifest
        if args.verify:
            if not args.manifest or args.check or args.release or args.workshop_item_id:
                raise ValueError("--verify requires --manifest and excludes build/release options")
            print(verify_manifest(spec, args.verify, args.manifest))
            return 0
        if args.manifest:
            raise ValueError("--manifest is only valid with --verify")
        revision = git("rev-parse", "HEAD")
        if args.check:
            if args.release:
                raise ValueError("--check and --release are separate modes")
            print(check_reproducible(spec, revision, args.workshop_item_id))
            return 0
        tag = None
        if args.release:
            if git("status", "--porcelain", "--untracked-files=all", "--", PRODUCT_ID):
                raise ValueError("formal release requires committed, clean product inputs")
            tag = TAG_PREFIX + VERSION
            if tag not in git("tag", "--points-at", "HEAD").splitlines():
                raise ValueError(f"formal release requires {tag} on HEAD")
        result = build(spec, args.output, revision, args.workshop_item_id, git_tag=tag)
        print(f"Staging: {result[0]}\nManifest: {result[1]}\nZIP: {result[2]}\nFiles: {len(result[3]['files'])}")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"DE JURE CONQUEST RELEASE FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
