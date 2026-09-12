"""Call one local Workshop MCP tool through the official in-memory client."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .server import create_server, create_service, default_state_directory


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="python -m ck3_workshop_mcp.call_tool")
    result.add_argument(
        "--provider",
        choices=("pdx-readonly", "pdx-cdp", "pdx-uia", "steamworks-readonly", "steam-native", "fake"),
        required=True,
    )
    result.add_argument("--cdp-url")
    result.add_argument("--state-dir", type=Path, default=default_state_directory())
    result.add_argument("--tool", required=True)
    result.add_argument("--arguments-file", type=Path, required=True)
    result.add_argument("--text-file", type=Path, help="Read exact UTF-8 text into the tool text argument")
    result.add_argument("--hwnd", type=int, help="Override a request's window handle after fresh discovery")
    return result


async def _call(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    try:
        from mcp import Client
    except ImportError as error:
        return {
            "ok": False,
            "error": {"type": type(error).__name__, "message": "mcp==2.0.0 is required"},
        }, 2
    try:
        raw_arguments = json.loads(args.arguments_file.read_text(encoding="utf-8-sig"))
        if not isinstance(raw_arguments, dict):
            raise ValueError("arguments file must contain one JSON object")
        if args.text_file:
            raw_arguments["text"] = args.text_file.read_text(encoding="utf-8-sig")
        if getattr(args, "hwnd", None) is not None:
            raw_arguments["hwnd"] = args.hwnd
        service = create_service(args.state_dir, args.provider)
        server = create_server(
            service,
            cdp_url=args.cdp_url if args.provider == "pdx-cdp" else None,
            enable_uia=args.provider == "pdx-uia",
            enable_native=args.provider == "steam-native",
        )
        async with Client(server) as client:
            response = await client.call_tool(args.tool, raw_arguments)
        payload = {
            "ok": not response.is_error,
            "tool": args.tool,
            "result": _jsonable(response.structured_content),
            "content": _jsonable(response.content),
        }
        return payload, 0 if not response.is_error else 1
    except Exception as error:
        return {
            "ok": False,
            "tool": args.tool,
            "error": {"type": type(error).__name__, "message": str(error)},
        }, 1


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _jsonable(model_dump(mode="json"))
    return str(value)


def main(argv: Sequence[str] | None = None) -> int:
    argument_parser = parser()
    try:
        args = argument_parser.parse_args(argv)
        if args.provider == "pdx-cdp" and not args.cdp_url:
            raise ValueError("--provider pdx-cdp requires --cdp-url")
        if args.provider != "pdx-cdp" and args.cdp_url:
            raise ValueError("--cdp-url is only valid with --provider pdx-cdp")
        payload, status = asyncio.run(_call(args))
    except BaseException as error:
        if isinstance(error, KeyboardInterrupt):
            payload, status = {
                "ok": False,
                "error": {"type": "KeyboardInterrupt", "message": "cancelled"},
            }, 130
        elif isinstance(error, SystemExit):
            raise
        else:
            payload, status = {
                "ok": False,
                "error": {"type": type(error).__name__, "message": str(error)},
            }, 2
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
