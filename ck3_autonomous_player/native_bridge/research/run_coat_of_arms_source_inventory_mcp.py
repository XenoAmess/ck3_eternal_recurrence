"""Capture installed CK3 CoA source candidates through the official MCP client.

This acceptance is deliberately read-only and does not launch or attach to CK3.
It proves the public typed MCP inventory surface against an exact installed build,
without upgrading physical files into entitlement, mount, registration, or winner
claims.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from mcp import Client

from xar_autoplayer.bridge.mcp_server import create_server


def _structured(result: object) -> dict[str, Any]:
    value = getattr(result, "structured_content", None)
    if not isinstance(value, dict):
        raise RuntimeError("MCP result has no structured object")
    return value


def _schema_receipt(tool: object) -> dict[str, object]:
    schema = getattr(tool, "input_schema", None)
    if not isinstance(schema, dict):
        raise RuntimeError("MCP tool has no input schema")
    return {
        "additionalProperties": schema.get("additionalProperties"),
        "required": schema.get("required"),
        "properties": sorted((schema.get("properties") or {}).keys()),
    }


async def collect(game_directory: Path) -> dict[str, object]:
    async with Client(create_server(object())) as client:
        listed = await client.list_tools()
        tools = {tool.name: tool for tool in listed.tools}
        name = "ck3_query_coat_of_arms_installed_dlc_sources_v1"
        if name not in tools:
            raise RuntimeError(f"required MCP tool is absent: {name}")
        result = await client.call_tool(
            name,
            {"game_directory": str(game_directory.resolve())},
        )
        if result.is_error:
            raise RuntimeError("installed DLC source MCP call returned an error")
        inventory = _structured(result)
        items = inventory.get("items")
        if not isinstance(items, list):
            raise RuntimeError("installed DLC source MCP result has no items")
        checks = {
            "closed_input_schema": (
                tools[name].input_schema.get("additionalProperties") is False
            ),
            "call_not_error": result.is_error is False,
            "exact_build_bound": inventory.get("ck3_build") == "1.19.0.6",
            "physical_inventory_only": (
                inventory.get("provenance", {}).get("installed_files_observed")
                is True
                and inventory.get("provenance", {}).get(
                    "store_entitlement_observed"
                )
                is False
                and inventory.get("provenance", {}).get("engine_mount_observed")
                is False
                and inventory.get("provenance", {}).get("resource_merge_applied")
                is False
            ),
            "descriptor_count_matches": (
                inventory.get("installed_descriptor_count") == len(items)
            ),
        }
        return {
            "schema": "ck3-coat-of-arms-source-inventory-mcp-acceptance-v1",
            "schema_version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "interaction_policy": {
                "official_mcp_client": True,
                "read_only": True,
                "launches_ck3": False,
                "uses_ocr": False,
                "uses_keyboard": False,
                "uses_mouse": False,
            },
            "tool": {
                "name": name,
                "input_schema": _schema_receipt(tools[name]),
            },
            "inventory": inventory,
            "checks": checks,
            "ok": all(checks.values()),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = asyncio.run(collect(args.game_directory))
    encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "output": str(args.output),
                "bytes": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest().upper(),
                "installed_descriptor_count": report["inventory"].get(
                    "installed_descriptor_count"
                ),
                "dlc_with_coa_candidates": report["inventory"].get(
                    "dlc_with_coa_candidates"
                ),
                "coa_txt_file_count": report["inventory"].get(
                    "coa_txt_file_count"
                ),
                "coa_dds_file_count": report["inventory"].get(
                    "coa_dds_file_count"
                ),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
