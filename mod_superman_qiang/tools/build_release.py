"""Build Superman Qiang's exact allowlist with deterministic manifest and ZIP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from product import REPO, spec

sys.path.insert(0, str(REPO / "tools"))
import independent_mod_release as release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="temporary double build; compare exact manifest and ZIP")
    modes.add_argument("--output", type=Path, help="new external staging directory; existing artifacts are never replaced")
    modes.add_argument("--verify", type=Path, help="read-only verification of a staging tree")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--workshop-item-id")
    parser.add_argument("--git-tag")
    args = parser.parse_args()
    try:
        product = spec()
        if args.verify:
            if args.manifest is None:
                raise ValueError("--verify requires --manifest")
            if args.git_tag or args.workshop_item_id:
                raise ValueError("--verify uses identity recorded in --manifest")
            report = {"verified_files": release.verify_manifest(product, args.verify, args.manifest)}
        else:
            if args.manifest:
                raise ValueError("--manifest requires --verify")
            # The shared tools directory also has a validate_static.py; load
            # this product's validator after spec() adds the shared import path.
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from validate_static import validate

            validation = validate()
            if validation["errors"]:
                raise ValueError("static validation failed:\n" + "\n".join(validation["errors"]))
            revision = subprocess.run(
                ["git", "-C", str(REPO), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            if args.check:
                if args.git_tag:
                    raise ValueError("--git-tag requires --output")
                report = release.check_reproducible(product, revision, args.workshop_item_id)
            else:
                staging, manifest, archive, payload = release.build(
                    product, args.output, revision, args.workshop_item_id, git_tag=args.git_tag,
                )
                report = {
                    "staging": str(staging), "manifest": str(manifest), "archive": str(archive),
                    "file_count": len(payload["files"]), "git_sha": revision, "git_tag": payload["git_tag"],
                }
        print(json.dumps(report, ensure_ascii=True, indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"SXAD RELEASE FAILED: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
