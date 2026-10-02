"""Issue the H2743 title-prestate read-only addendum once via fixed WAR sync."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DRAFT = ROOT / "docs/ck3-native-ai/research/h2743-title-prestate-addendum-draft-20260928.json"
WAR = Path("C:/Users/1/OneDrive/WAR/H2743-EXIT-READONLY-V3-20260928")
REQUEST = WAR / "REQUEST-TITLE-PRESTATE-ADDENDUM-v1.json"
RECEIPT = WAR / "REQUEST-TITLE-PRESTATE-ADDENDUM-v1.issued.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> None:
    if not WAR.is_dir() or not (WAR / "REQUEST.json").exists():
        raise RuntimeError("the fixed H2743 WAR folder is unavailable")
    if REQUEST.exists() or RECEIPT.exists():
        raise RuntimeError("addendum or receipt already exists; never overwrite")
    draft_bytes = DRAFT.read_bytes()
    request = json.loads(draft_bytes)
    if (request.get("schema") != "xar.ck3.war.h2743.title-prestate-readonly-addendum.draft.v1"
            or request.get("status") != "draft_not_sent"):
        raise RuntimeError("reviewed addendum draft identity differs")
    issued_at = datetime.now(timezone.utc).isoformat()
    request["schema"] = "xar.ck3.war.h2743.title-prestate-readonly-addendum.request.v1"
    request["status"] = "sent_from_receiver_machine"
    request["issued_at_utc"] = issued_at
    request_bytes = (json.dumps(request, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with REQUEST.open("xb") as output:
        output.write(request_bytes)
    if REQUEST.read_bytes() != request_bytes:
        raise RuntimeError("addendum byte readback mismatch")
    receipt = {
        "schema": "xar.ck3.war.h2743.title-prestate-addendum-issued.v1",
        "status": "local_exact_bytes_written_and_read_back",
        "issued_at_utc": issued_at,
        "draft_path": str(DRAFT),
        "draft_sha256": sha256(draft_bytes),
        "request_path": str(REQUEST),
        "request_bytes": len(request_bytes),
        "request_sha256": sha256(request_bytes),
        "source_machine_ack_observed": False,
        "source_machine_response_observed": False,
    }
    receipt_bytes = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with RECEIPT.open("xb") as output:
        output.write(receipt_bytes)
    if RECEIPT.read_bytes() != receipt_bytes or REQUEST.read_bytes() != request_bytes:
        raise RuntimeError("post-issue request or receipt readback mismatch")
    print(json.dumps({"request_sha256": receipt["request_sha256"],
                      "request_bytes": receipt["request_bytes"],
                      "receipt_sha256": sha256(receipt_bytes),
                      "receipt_path": str(RECEIPT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
