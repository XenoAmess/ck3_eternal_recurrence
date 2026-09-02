#!/usr/bin/env python3
"""Validate explicit authority for the ZhongGuo phase-two video publication.

This is a read-only project adapter.  It never resolves credentials, contacts
the target, uploads bytes, or creates an authority document.  In particular,
the Steam Workshop item used to distribute the mod is not inferred to be a
video publication target.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.parse import urlparse


KIND = "zg361_phase2_publish_target_gate"
AUTHORITY_KIND = "zg361_phase2_publish_target_authority"
RECEIPT_KIND = "zg361_phase2_publish_receipt"


def _sha256(path: Path) -> dict[str, object]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest,
    }


def _timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _locator_prefix(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").casefold()
    return (
        parsed.scheme == "https"
        and bool(hostname)
        and hostname != "localhost"
        and not hostname.endswith(".invalid")
        and not hostname.endswith(".test")
        and hostname not in {"example.com", "example.org", "example.net"}
        and bool(parsed.path not in {"", "/"} or parsed.query)
    )


def validate_publish_target_authority(path: Path | None) -> dict[str, object]:
    """Return GREEN only for an explicit target, account and credential receipt."""

    result: dict[str, object] = {
        "schema_version": 1,
        "kind": KIND,
        "result": "RED",
        "status": "pending",
        "reason_code": "publish_target_pending",
        "authority": None,
        "target": None,
        "checks": {
            "authority_header": False,
            "target_named": False,
            "account_named": False,
            "locator_prefix_explicit": False,
            "upload_authorized": False,
            "authorization_attributed": False,
            "credential_reference_present": False,
            "credential_availability_verified": False,
            "receipt_contract_fixed": False,
        },
        "execution_attestation": {
            "credential_resolved": False,
            "network_used": False,
            "upload_performed": False,
        },
        "errors": [],
    }
    if path is None or not path.expanduser().resolve().is_file():
        result["errors"] = ["publish_target_authority_missing"]
        return result
    authority_path = path.expanduser().resolve()
    try:
        payload = json.loads(authority_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        result["errors"] = [f"publish_target_authority_invalid:{type(error).__name__}"]
        return result
    result["authority"] = _sha256(authority_path)
    if not isinstance(payload, Mapping):
        result["errors"] = ["publish_target_authority_root_invalid"]
        return result

    authorization = payload.get("authorization")
    authorization = authorization if isinstance(authorization, Mapping) else {}
    credentials = payload.get("credentials")
    credentials = credentials if isinstance(credentials, Mapping) else {}
    receipt = payload.get("publication_receipt")
    receipt = receipt if isinstance(receipt, Mapping) else {}
    checks = result["checks"]
    assert isinstance(checks, dict)
    checks.update(
        {
            "authority_header": payload.get("schema_version") == 1
            and payload.get("kind") == AUTHORITY_KIND,
            "target_named": _text(payload.get("target_id"))
            and _text(payload.get("platform")),
            "account_named": _text(payload.get("account_id")),
            "locator_prefix_explicit": _locator_prefix(payload.get("locator_prefix")),
            "upload_authorized": authorization.get("upload_authorized") is True,
            "authorization_attributed": _text(authorization.get("approved_by"))
            and _timestamp(authorization.get("approved_at")),
            "credential_reference_present": _text(credentials.get("reference")),
            "credential_availability_verified": credentials.get("availability_verified")
            is True
            and _timestamp(credentials.get("verified_at")),
            "receipt_contract_fixed": receipt.get("schema_version") == 1
            and receipt.get("kind") == RECEIPT_KIND
            and receipt.get("remote_verification_required") is True,
        }
    )
    if all(checks.values()):
        result["result"] = "GREEN"
        result["status"] = "authorized"
        result["reason_code"] = None
        result["target"] = {
            "target_id": payload["target_id"],
            "platform": payload["platform"],
            "account_id": payload["account_id"],
            "locator_prefix": payload["locator_prefix"],
            "credential_reference": credentials["reference"],
            "approved_by": authorization["approved_by"],
            "approved_at": authorization["approved_at"],
            "receipt_kind": receipt["kind"],
        }
    else:
        result["errors"] = [
            f"publish_target_check_failed:{name}"
            for name, passed in checks.items()
            if not passed
        ]
    return result


__all__ = [
    "AUTHORITY_KIND",
    "KIND",
    "RECEIPT_KIND",
    "validate_publish_target_authority",
]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--authority", type=Path)
    result.add_argument("--output", type=Path, required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    output = args.output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite report: {output}")
    if not output.parent.is_dir():
        raise FileNotFoundError(f"report parent does not exist: {output.parent}")
    report = validate_publish_target_authority(args.authority)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"report={output}")
    print(f"report_sha256={_sha256(output)['sha256']}")
    print(f"PUBLISH TARGET: {report['result']} [{report['reason_code']}]")
    return 0 if report["result"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
