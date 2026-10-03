"""Anonymously verify frozen metadata, full notes, cover and gameplay media.

Uses public HTTP without cookies or authorization. The native preview query is
an input from the separate exact-item MCP call; this helper never loads Steam.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from urllib import error, parse, request

from product import PRODUCT_ID, REPO

sys.path.insert(0, str(REPO / "tools"))
from verify_workshop_publication import ITEM_API, verify_payloads
from PIL import Image

TITLE = "超人强：越超人越强"
TAGS = {"Gameplay", "Balance", "Events"}
APP_ID = 1158310
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SupermanQiangRelease/1.0"
HIGHLIGHT = re.compile(r'class=["\'][^"\']*\bhighlight_strip_item\b[^"\']*["\']', re.IGNORECASE)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identity(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "size": len(raw), "sha256": sha(raw)}


def fetch(url: str, output: Path, timeout: float, data: bytes | None = None) -> dict[str, object]:
    call = request.Request(url, data=data, headers={"User-Agent": USER_AGENT}, method="POST" if data is not None else "GET")
    try:
        with request.urlopen(call, timeout=timeout) as response:
            raw = response.read()
            result = {"requested_url": url, "final_url": response.url, "http_status": response.status,
                      "content_type": response.headers.get("Content-Type"), "request_cookie_or_authorization": False}
    except error.HTTPError as failure:
        raw = failure.read()
        result = {"requested_url": url, "http_status": failure.code, "request_cookie_or_authorization": False}
    output.write_bytes(raw)
    result["body"] = identity(output)
    if result["http_status"] != 200:
        raise ValueError(f"anonymous HTTP {result['http_status']}; preserved response at {output}")
    return result


def image_comparison(public: Path, source: Path) -> dict[str, object]:
    public_raw, source_raw = public.read_bytes(), source.read_bytes()
    with Image.open(BytesIO(public_raw)) as shown, Image.open(BytesIO(source_raw)) as selected:
        result = {"dimensions": list(shown.size), "expected_dimensions": list(selected.size),
                  "bytes_equal": public_raw == source_raw,
                  "decoded_pixels_equal": shown.size == selected.size and shown.convert("RGBA").tobytes() == selected.convert("RGBA").tobytes()}
    result["ok"] = result["bytes_equal"] and result["decoded_pixels_equal"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--owner-steam-id", required=True)
    parser.add_argument("--description", type=Path, required=True)
    parser.add_argument("--change-notes", type=Path, required=True)
    parser.add_argument("--thumbnail", type=Path, required=True)
    parser.add_argument("--native-previews", type=Path, required=True)
    parser.add_argument("--media", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args(argv)
    result: dict[str, object] = {"schema": "superman-qiang.publication.anonymous-readback.v1", "ok": False,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "product_id": PRODUCT_ID,
        "item_id": args.item_id, "steam_dll_loaded": False, "screen_calls": 0}
    output = args.output.expanduser().resolve()
    created_output = False
    try:
        if not args.item_id.isascii() or not args.item_id.isdecimal() or int(args.item_id) <= 0:
            raise ValueError("item ID must be a positive ASCII decimal string")
        if output.exists() or not output.parent.is_dir():
            raise ValueError("--output must be new under an existing parent")
        frozen = json.loads(args.native_previews.read_text(encoding="utf-8-sig"))
        if "result" in frozen:
            if frozen.get("ok") is not True:
                raise ValueError("native previews MCP transport did not succeed")
            frozen = frozen["result"]
        if frozen.get("ok") is not True or frozen.get("item_id") != args.item_id or frozen.get("app_id") != APP_ID:
            raise ValueError("native preview query is not successful for this exact item/AppID")
        previews = frozen["previews"]
        if len(previews) != len(args.media) or not previews:
            raise ValueError("ordered native preview count differs from supplied gameplay media")
        output.mkdir()
        created_output = True
        result["frozen_inputs"] = {"description": identity(args.description), "notes": identity(args.change_notes),
                                   "thumbnail": identity(args.thumbnail), "native_previews": identity(args.native_previews),
                                   "media": [identity(path) for path in args.media]}
        form = parse.urlencode({"itemcount": "1", "publishedfileids[0]": args.item_id}).encode("ascii")
        result["item_api_response"] = fetch(ITEM_API, output / "item-api.raw.json", args.timeout, form)
        api = json.loads((output / "item-api.raw.json").read_text(encoding="utf-8-sig"))
        item = api["response"]["publishedfiledetails"][0]
        result["item_identity"] = {"result_ok": item.get("result") == 1,
            "item_id_exact": str(item.get("publishedfileid")) == args.item_id,
            "app_id_exact": item.get("consumer_app_id") == APP_ID,
            "owner_exact": str(item.get("creator")) == args.owner_steam_id,
            "public_visibility": item.get("visibility") == 0,
            "tags_exact": {tag["tag"] for tag in item.get("tags", [])} == TAGS}
        if not all(result["item_identity"].values()):
            raise ValueError("public item identity/owner/visibility/tags do not match")
        changelog_url = f"https://steamcommunity.com/sharedfiles/filedetails/changelog/{args.item_id}?l=english&p=1"
        result["changelog_response"] = fetch(changelog_url, output / "changelog.raw.html", args.timeout)
        result["text_verification"] = verify_payloads(
            item_api=api,
            changelog_html=(output / "changelog.raw.html").read_text(encoding="utf-8-sig"),
            expected_title=TITLE,
            expected_description=args.description.read_text(encoding="utf-8-sig"),
            expected_change_notes=args.change_notes.read_text(encoding="utf-8-sig"),
        )
        page_url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={args.item_id}"
        result["item_page_response"] = fetch(page_url, output / "item-page.raw.html", args.timeout)
        result["dlc_and_required_mods"] = {
            "state": "not_observed",
            "verified": False,
            "source": "anonymous public page DOM/sidebar",
            "page_url": page_url,
            "public_page_html": identity(output / "item-page.raw.html"),
            "required_dlc_app_ids": None,
            "required_mod_item_ids": None,
            "reason": "The current native preview query and public metadata verifier expose no proven dependency fields. Observe the actual anonymous Required DLC / Required items sidebar and record its DOM rule, page SHA-256 and both ID arrays separately; absent fields do not establish empty dependencies.",
        }
        page = html.unescape((output / "item-page.raw.html").read_text(encoding="utf-8-sig")).replace("\\/", "/")
        result["highlight_strip_count"] = len(HIGHLIGHT.findall(page))
        result["highlight_strip_count_exact"] = result["highlight_strip_count"] == len(previews)
        result["main_preview_response"] = fetch(item["preview_url"], output / "main-preview.public", args.timeout)
        result["main_preview_comparison"] = image_comparison(output / "main-preview.public", args.thumbnail)
        media_reports = []
        for index, (preview, selected) in enumerate(zip(previews, args.media, strict=True)):
            if preview["index"] != index or preview["type"] != 0 or preview["original_filename"] != selected.name:
                raise ValueError("native media index/type/filename order does not match selected files")
            url = preview["url"]
            public = output / f"media-{index:02d}.public"
            response = fetch(url, public, args.timeout)
            media_reports.append({"index": index, "url": url, "response": response,
                "public_page_references_exact_cdn_path": parse.urlsplit(url).path in page,
                "comparison": image_comparison(public, selected)})
        result["media"] = media_reports
        result["metadata_notes_cover_media_ok"] = bool(result["text_verification"]["ok"] and result["highlight_strip_count_exact"]
            and result["main_preview_comparison"]["ok"]
            and all(m["public_page_references_exact_cdn_path"] and m["comparison"]["ok"] for m in media_reports))
        result["ok"] = result["metadata_notes_cover_media_ok"] and result["dlc_and_required_mods"]["verified"]
        result["status"] = "pending_dependency_observation" if result["metadata_notes_cover_media_ok"] else "failed_public_readback"
        result["visual_review"] = "pending; direct image inspection is an independent recorded step"
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, error.URLError) as failure:
        result["error"] = {"type": type(failure).__name__, "message": str(failure)}
    if created_output:
        report = output / "verification.json"
        if not report.exists():
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
