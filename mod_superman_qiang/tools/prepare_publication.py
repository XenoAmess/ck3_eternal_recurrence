"""Freeze reviewed Workshop inputs without loading Steam or publishing.

The direct native MCP provider consumes the resulting plan and keeps its own
durable create/submit receipt. Steam mode, live acceptance and public readback
remain separate steps. Every output directory is new and preserved.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from product import PRODUCT_ID, PRODUCT_KEY, REPO, VERSION, spec

sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "ck3_workshop_mcp" / "src"))
import independent_mod_release as release
from ck3_workshop_mcp.steam_native import SteamNativeError, _prepare_plan

TITLE = "超人强：越超人越强"
TAGS = ["Gameplay", "Balance", "Events"]
APP_ID = 1158310


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def file_identity(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "size": len(raw), "sha256": digest(raw)}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def preview_snapshot(path: Path, item_id: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict) and "result" in payload:
        if payload.get("ok") is not True:
            raise ValueError("preview MCP transport did not succeed")
        payload = payload["result"]
    if not isinstance(payload, dict) or payload.get("ok", True) is not True:
        raise ValueError("preview query did not succeed")
    if str(payload.get("item_id")) != item_id or payload.get("app_id") != APP_ID:
        raise ValueError("preview query item/AppID differs from this update")
    if not isinstance(payload.get("previews"), list):
        raise ValueError("preview query has no ordered previews list")
    return {"item_id": item_id, "app_id": APP_ID, "previews": payload["previews"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--operation", choices=("create", "update"), required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--description", type=Path, default=REPO / "workshop/superman_qiang_description.bbcode")
    parser.add_argument("--change-notes", type=Path, default=REPO / "workshop/superman_qiang_change_notes.txt")
    parser.add_argument("--preview-snapshot", type=Path)
    parser.add_argument("--media", type=Path, action="append", default=[])
    parser.add_argument("--acceptance-report", type=Path, required=True, help="bind the previously reviewed live report; this helper does not judge live truth")
    args = parser.parse_args(argv)
    try:
        output = args.output.expanduser().resolve()
        if output.exists() or not output.parent.is_dir():
            raise ValueError("--output must be a new directory under an existing parent")
        staging = args.staging.expanduser().resolve()
        manifest_path = args.manifest.expanduser().resolve()
        count = release.verify_manifest(spec(), staging, manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if manifest["product_id"] != PRODUCT_ID or manifest["mod_version"] != VERSION:
            raise ValueError("manifest product/version differs from this product")
        if not manifest.get("git_tag"):
            raise ValueError("formal publication requires a tag-bound build")
        if "remote_file_id" in (staging / "descriptor.mod").read_text(encoding="utf-8-sig"):
            raise ValueError("canonical inner descriptor must not contain remote_file_id")
        if args.operation == "create" and (args.item_id or args.media or args.preview_snapshot):
            raise ValueError("create has no existing ID or additional preview edits")
        if args.operation == "create" and manifest.get("workshop_item_id") is not None:
            raise ValueError("create requires an unbound manifest")
        if args.operation == "update":
            if not args.item_id or not args.item_id.isascii() or not args.item_id.isdecimal() or int(args.item_id) <= 0:
                raise ValueError("update requires a positive --item-id")
            if manifest.get("workshop_item_id") not in (None, args.item_id):
                raise ValueError("manifest Workshop ID differs from this update")
        if bool(args.media) != bool(args.preview_snapshot):
            raise ValueError("additional media requires a fresh preview snapshot, and vice versa")
        if not args.dll.is_file():
            raise ValueError("--dll must identify the actual installed CK3 Steam DLL")
        acceptance_identity = file_identity(args.acceptance_report)
        description = normalized(args.description.read_text(encoding="utf-8-sig"))
        notes = normalized(args.change_notes.read_text(encoding="utf-8-sig"))
        if not description or not notes or TITLE not in description or TITLE not in notes:
            raise ValueError("reviewed description and full notes must contain the exact product title")
        if "initial baseline" not in notes:
            raise ValueError("1.0.0 notes must explicitly identify the initial baseline")
        preview = staging / "thumbnail.png"
        if not preview.is_file() or preview.stat().st_size >= 1024 * 1024:
            raise ValueError("staging thumbnail must exist and be under 1 MiB")
        snapshot = preview_snapshot(args.preview_snapshot, args.item_id) if args.preview_snapshot else None
        media = [file_identity(path.expanduser().resolve()) for path in args.media]
        plan: dict[str, object] = {
            "operation_id": args.operation_id,
            "operation": args.operation,
            "app_id": APP_ID,
            "target_item_id": args.item_id if args.operation == "update" else None,
            "title": TITLE,
            "description_path": str(output / "description.bbcode"),
            "content_path": str(staging),
            "preview_path": str(preview),
            "visibility": "public",
            "tags": TAGS,
            "change_note": notes,
            "workshop_legal_agreement_accepted": False,
        }
        if snapshot is not None:
            plan["expected_additional_previews"] = snapshot
            plan["additional_preview_files"] = media
        output.mkdir()
        (output / "description.bbcode").write_text(description, encoding="utf-8", newline="\n")
        (output / "change-notes.txt").write_text(notes, encoding="utf-8", newline="\n")
        # Pure local plan validation hashes content/media; no DLL is loaded.
        prepared = _prepare_plan(plan)
        write_json(output / "native-plan.json", plan)
        write_json(output / "native-arguments.json", {
            "dll_path": str(args.dll.resolve()),
            "plan_file": str(output / "native-plan.json"),
            "receipt_file": str(output / "native-receipt.json"),
        })
        freeze = {
            "schema": "superman-qiang.publication.frozen-inputs.v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "product_key": PRODUCT_KEY,
            "version": VERSION,
            "operation": args.operation,
            "operation_id": args.operation_id,
            "item_id": args.item_id,
            "git_sha": manifest["git_sha"],
            "git_tag": manifest["git_tag"],
            "runtime_file_count": count,
            "staging_manifest": file_identity(manifest_path),
            "acceptance_report": acceptance_identity,
            "native_payload_sha256": prepared.payload_sha256,
            "description": {**file_identity(output / "description.bbcode"), "characters": len(description), "lines": description.count("\n") + 1},
            "change_notes": {**file_identity(output / "change-notes.txt"), "characters": len(notes), "lines": notes.count("\n") + 1},
            "thumbnail": file_identity(preview),
            "media": media,
            "steam_dll_loaded": False,
            "steam_mode_changed": False,
            "published": False,
            "offline_restoration_required_after_online_window": True,
        }
        write_json(output / "frozen-inputs.json", freeze)
        print(json.dumps({"output": str(output), "runtime_files": count, "notes_characters": len(notes), "notes_lines": notes.count("\n") + 1, "notes_sha256": digest(notes.encode("utf-8")), "native_payload_sha256": prepared.payload_sha256, "published": False}, ensure_ascii=False))
    except (OSError, UnicodeError, ValueError, KeyError, SteamNativeError) as error:
        parser.exit(1, f"SXAD PUBLICATION PREPARATION FAILED: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
