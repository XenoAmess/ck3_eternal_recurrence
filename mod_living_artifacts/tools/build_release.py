"""Publish only the reviewed runtime allowlist, using the shared builder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from product import REPO, spec
from validate_static import validate

sys.path.append(str(REPO / "tools"))
from independent_mod_release import build, check_reproducible, verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True, help="CK3 game/ script root inside the installation")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--output", type=Path)
    mode.add_argument("--verify", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--workshop-item-id")
    parser.add_argument("--git-tag")
    args = parser.parse_args()
    try:
        product = spec()
        if args.verify is not None:
            if args.manifest is None:
                raise ValueError("--verify requires --manifest")
            count = verify_manifest(product, args.verify, args.manifest)
            result: dict[str, object] = {"status": "PASS", "verified_files": count}
        else:
            errors = validate(args.game, release=True)
            if errors:
                raise ValueError("\n".join(errors))
            revision = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            if args.check:
                result = {"status": "PASS", **check_reproducible(product, revision, args.workshop_item_id)}
            else:
                staging, manifest, archive, payload = build(product, args.output, revision, args.workshop_item_id, git_tag=args.git_tag)
                result = {"status": "PASS", "staging": str(staging), "manifest": str(manifest), "archive": str(archive), "file_count": len(frozenset(product.runtime_files)), "source_revision": revision, "scope": "formal_projection_only"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({"status": "FAIL", "reason": str(error)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
