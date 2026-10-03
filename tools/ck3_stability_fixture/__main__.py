"""CLI for existing-owner UI assistance and closed-save continuity inspection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .chain import verify_chain
from .evidence import load_json, sha256, write_new
from .pixels import PixelRouter
from .runner import assist


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    route = sub.add_parser("route", help="read-only routing of an existing, original image")
    route.add_argument("--profile", type=Path, required=True)
    route.add_argument("--image", type=Path, required=True)
    route.add_argument("--output", type=Path, required=True)
    live = sub.add_parser("assist", help="bounded desktop fallback under original operator custody")
    live.add_argument("--profile", type=Path, required=True)
    live.add_argument("--execute", action="store_true", help="explicitly send reviewed keys; default is capture/route only")
    live.add_argument("--max-actions", type=int, default=1)
    live.add_argument("--timeout", type=float, default=60)
    chain = sub.add_parser("verify-chain", help="inspect only closed normal-save chains; never grade stability")
    chain.add_argument("--manifest", type=Path, required=True)
    chain.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "route":
            result = PixelRouter(load_json(args.profile)["routing"]).route(args.image)
            result["source"] = {"path": str(args.image), "sha256": sha256(args.image)}
            write_new(args.output, result)
        elif args.command == "verify-chain":
            result = verify_chain(load_json(args.manifest))
            write_new(args.output, result)
        else:
            from .windows import OwnedWindowsBackend
            profile = load_json(args.profile)
            profile["profile_source"] = {"path": str(args.profile.resolve()), "sha256": sha256(args.profile)}
            result = assist(profile, OwnedWindowsBackend(), execute=args.execute,
                            max_actions=args.max_actions, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False))
        return 2 if result.get("status") == "NEEDS_OPERATOR" else 0
    except Exception as error:
        result = {"status": "NEEDS_OPERATOR", "error": f"{type(error).__name__}: {error}",
                  "business_result": "NOT_VERIFIED", "stability_result": "NOT_GRADED"}
        if args.command in {"route", "verify-chain"} and not args.output.exists():
            write_new(args.output, result)
        print(json.dumps(result, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
