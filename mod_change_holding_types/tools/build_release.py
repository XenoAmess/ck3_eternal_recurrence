"""Build or verify the maintained holding conversion release through shared tools."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from product import REPO, spec

sys.path.insert(0, str(REPO / "tools"))
import independent_mod_release as release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--output", type=Path)
    modes.add_argument("--verify", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--workshop-item-id")
    parser.add_argument("--git-tag")
    parser.add_argument("--release-localization", action="store_true")
    args = parser.parse_args()
    try:
        product = spec(args.release_localization)
        if args.verify:
            if args.manifest is None:
                raise ValueError("--verify requires --manifest")
            print(json.dumps({"verified_files": release.verify_manifest(product, args.verify, args.manifest)}, ensure_ascii=False, indent=2))
        else:
            if args.manifest:
                raise ValueError("--manifest requires --verify")
            revision = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            if args.check:
                print(json.dumps(release.check_reproducible(product, revision, args.workshop_item_id), ensure_ascii=False, indent=2))
            else:
                staging, manifest, archive, payload = release.build(product, args.output, revision, args.workshop_item_id, git_tag=args.git_tag)
                print(json.dumps({"staging": str(staging), "manifest": str(manifest), "archive": str(archive), "file_count": len(payload["files"])}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"CHT RELEASE FAILED: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
