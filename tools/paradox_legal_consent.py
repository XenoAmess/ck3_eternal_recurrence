#!/usr/bin/env python3
"""Shared allowlisted handling for necessary Paradox legal agreements.

The project owner authorizes acceptance only for a Paradox User Agreement,
EULA, Terms of Use, or an exact semantic equivalent.  Privacy, telemetry,
advertising, marketing, personalization and data-sharing prompts are outside
that authority.  This module is intentionally runner-neutral: callers supply
their existing OCR, click and screen-grab adapters and an isolated ``-userdir``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time


LEGAL_CONSENT_PROFILE_SUFFIX = Path("account/PDX/SDK/ck3/account.json")
LEGAL_MODAL_HEADER_REGION = (0.10, 0.02, 0.90, 0.32)
LEGAL_ALLOWED_TERMS = (
    "user agreement",
    "end user license agreement",
    "eula",
    "terms of use",
    "用户协议",
    "最终用户许可协议",
    "用户许可协议",
    "使用条款",
    "使用条件",
)
LEGAL_DENIED_TERMS = (
    "privacy",
    "telemetry",
    "advertising",
    "advertisement",
    "marketing",
    "personalized",
    "personalisation",
    "personalization",
    "data sharing",
    "隐私",
    "遥测",
    "广告",
    "营销",
    "个性化",
    "数据共享",
)
LEGAL_DOCUMENT_HINTS = (
    "agreement",
    "license",
    "terms",
    "consent",
    "policy",
    "协议",
    "许可",
    "条款",
    "同意",
    "政策",
)
LEGAL_VERSION_TERMS = (
    "last update",
    "last updated",
    "effective",
    "version",
    "更新",
    "生效",
    "版本",
)
LEGAL_ACCEPT_BUTTONS = ("好的", "我同意", "接受", "I Agree", "Accept", "OK")


class TypedTerminalError(RuntimeError):
    """A legal-consent boundary stopped without an unauthorized click."""

    def __init__(
        self,
        terminal: str,
        stage: str,
        detail: str,
        *,
        diagnostics: dict[str, object] | None = None,
    ) -> None:
        super().__init__(detail)
        self.terminal = terminal
        self.stage = stage
        self.diagnostics = diagnostics


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _legal_document_markers(payload: dict[str, object]) -> list[str]:
    viewed = payload.get("viewedLegalDocuments")
    if not isinstance(viewed, dict):
        return []
    markers: list[str] = []
    for bucket in ("online", "localOnly"):
        values = viewed.get(bucket, [])
        if isinstance(values, list):
            markers.extend(value for value in values if isinstance(value, str))
    return markers


def diagnose_legal_modal(rows: list[str]) -> dict[str, object]:
    """Normalize OCR rows and expose the exact token-based classification input."""

    normalized_rows = [" ".join(str(row).split()) for row in rows if str(row).strip()]
    normalized_text = " ".join(normalized_rows).casefold()
    paradox_present = "paradox" in normalized_text
    denied = [term for term in LEGAL_DENIED_TERMS if term in normalized_text]
    allowed = [term for term in LEGAL_ALLOWED_TERMS if term in normalized_text]
    hints = [term for term in LEGAL_DOCUMENT_HINTS if term in normalized_text]
    if not paradox_present:
        classification_state = "not_paradox"
    elif denied:
        classification_state = "denied"
    elif allowed:
        classification_state = "authorized_candidate"
    elif hints:
        classification_state = "ambiguous_legal"
    else:
        classification_state = "not_legal_modal"
    return {
        "normalized_rows": normalized_rows,
        "normalized_text": normalized_text,
        "paradox_token_present": paradox_present,
        "allowed_terms": allowed,
        "denied_terms": denied,
        "legal_document_hints": hints,
        "classification_state": classification_state,
        "evidence_required": bool(
            paradox_present and (allowed or denied or hints)
        ),
    }


def persist_preclassification_evidence(
    image: object,
    rows: list[str],
    ui_dir: Path,
    index: int,
) -> dict[str, object]:
    """Persist the exact frame and OCR inputs before any legal classification."""

    diagnostics = diagnose_legal_modal(rows)
    evidence: dict[str, object] = {
        "index": index,
        "raw_ocr_rows": [str(row) for row in rows],
        **diagnostics,
        "preclassification_screenshot": None,
        "preclassification_screenshot_sha256": None,
    }
    if not diagnostics["evidence_required"]:
        return evidence
    ui_dir.mkdir(parents=True, exist_ok=True)
    path = ui_dir / f"legal_consent_{index:02d}_preclassification.png"
    image.save(path)
    evidence.update(
        {
            "preclassification_screenshot": str(path.resolve()),
            "preclassification_screenshot_sha256": sha256(path),
        }
    )
    return evidence


def classify_authorized_legal_modal(
    rows: list[str],
) -> dict[str, object] | None:
    """Classify an OCR header, returning ``None`` when no legal modal exists."""

    diagnostics = diagnose_legal_modal(rows)
    cleaned = diagnostics["normalized_rows"]
    joined = diagnostics["normalized_text"]
    assert isinstance(cleaned, list)
    assert isinstance(joined, str)
    if not diagnostics["paradox_token_present"]:
        return None
    denied = diagnostics["denied_terms"]
    assert isinstance(denied, list)
    if denied:
        raise TypedTerminalError(
            "LegalConsentNotAuthorized",
            "legal_consent",
            f"legal modal header contains non-authorized category tokens: {denied}",
            diagnostics=diagnostics,
        )
    allowed = diagnostics["allowed_terms"]
    assert isinstance(allowed, list)
    if not allowed:
        if diagnostics["legal_document_hints"]:
            raise TypedTerminalError(
                "LegalConsentNotAuthorized",
                "legal_consent",
                "Paradox legal/consent modal does not match the authorized document kinds",
                diagnostics=diagnostics,
            )
        return None
    title = next(
        (row for row in cleaned if any(term in row.casefold() for term in allowed)),
        cleaned[0] if cleaned else "",
    )
    version = next(
        (
            row
            for row in cleaned
            if any(token in row.casefold() for token in LEGAL_VERSION_TERMS)
        ),
        None,
    )
    return {
        "title": title,
        "version": version,
        "allowed_terms": allowed,
        "denied_terms": denied,
    }


def validate_legal_consent_source(
    source: Path, contract: dict[str, object]
) -> dict[str, object]:
    expected = {
        "source_profile_relative_path": LEGAL_CONSENT_PROFILE_SUFFIX.as_posix(),
        "source_sha256": "8933437F2000BB639D588A541B798F97C6D87BA7D891613FAC23D1812AB9EB28",
        "authorized_document_kinds": [
            "User Agreement",
            "EULA",
            "Terms of Use",
            "semantic equivalents",
        ],
        "explicitly_not_authorized": [
            "privacy",
            "telemetry",
            "advertising",
            "marketing",
            "personalized content",
            "data sharing",
        ],
        "accepted_marker_present": False,
        "allow_exact_semantic_modal_acceptance": True,
        "real_profile_read_only": True,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise RuntimeError(f"manifest legal-consent contract mismatch for {key}")
    if not source.is_file():
        raise TypedTerminalError(
            "LegalConsentRequired",
            "preflight_legal_consent",
            "real-profile legal-consent source is absent",
        )
    source_parts = tuple(part.casefold() for part in source.resolve().parts)
    suffix_parts = tuple(
        part.casefold() for part in LEGAL_CONSENT_PROFILE_SUFFIX.parts
    )
    if source_parts[-len(suffix_parts) :] != suffix_parts:
        raise RuntimeError(
            "legal-consent source path is not the frozen CK3 account file"
        )
    observed_hash = sha256(source)
    if observed_hash != contract["source_sha256"]:
        raise RuntimeError(f"legal-consent source hash mismatch: {observed_hash}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"legal-consent source is invalid JSON: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise RuntimeError("legal-consent source root is not an object")
    markers = _legal_document_markers(payload)
    return {
        "source_path": str(source.resolve()),
        "source_sha256": observed_hash,
        "accepted_marker_present": False,
        "observed_legal_marker_count": len(markers),
        "real_profile_read_only": True,
    }


def account_legal_state(userdir: Path) -> dict[str, object]:
    root = Path(userdir).resolve()
    path = root / LEGAL_CONSENT_PROFILE_SUFFIX
    if not path.is_file():
        return {
            "path": str(path.resolve()),
            "relative_path": LEGAL_CONSENT_PROFILE_SUFFIX.as_posix(),
            "exists": False,
            "sha256": None,
            "markers": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("isolated userdir account.json root is not an object")
    return {
        "path": str(path.resolve()),
        "relative_path": LEGAL_CONSENT_PROFILE_SUFFIX.as_posix(),
        "exists": True,
        "sha256": sha256(path),
        "markers": sorted(_legal_document_markers(payload)),
    }


def newly_persisted_legal_markers(
    before: dict[str, object], after: dict[str, object]
) -> list[str]:
    before_markers = set(str(value) for value in before.get("markers", []))
    return sorted(
        str(value)
        for value in after.get("markers", [])
        if str(value) not in before_markers
    )


def _authorized_legal_marker(marker: str) -> bool:
    normalized = marker.casefold().replace("_", "-").replace(".", "-")
    if any(term.replace(" ", "-") in normalized for term in LEGAL_DENIED_TERMS):
        return False
    return any(
        token in normalized
        for token in (
            "user-agreement",
            "end-user-license-agreement",
            "eula",
            "terms-of-use",
        )
    )


def accept_authorized_legal_modal(
    acceptance: object,
    image_grab: object,
    userdir: Path,
    ui_dir: Path,
    image: object,
    rows: list[str],
    index: int,
    stage_artifacts: list[dict[str, object]],
) -> dict[str, object]:
    """Accept one exact legal modal and prove its isolated marker delta."""

    classification = classify_authorized_legal_modal(rows)
    if classification is None:
        raise TypedTerminalError(
            "LegalConsentNotAuthorized",
            "legal_consent",
            "visible modal is not an allowlisted Paradox legal agreement",
        )
    if not classification.get("title"):
        raise TypedTerminalError(
            "LegalConsentTitleMissing",
            "legal_consent",
            "allowlisted legal agreement has no recognized title",
        )
    if not classification.get("version"):
        raise TypedTerminalError(
            "LegalConsentVersionMissing",
            "legal_consent",
            "allowlisted legal agreement has no recognized version/effective date",
        )
    ui_dir.mkdir(parents=True, exist_ok=True)
    before_path = ui_dir / f"legal_consent_{index:02d}_before.png"
    image.save(before_path)
    stage_artifacts.append(
        {"stage": "legal_consent_before", "path": before_path.name}
    )
    before_state = account_legal_state(userdir)
    accept_point = None
    button_label = None
    for label in LEGAL_ACCEPT_BUTTONS:
        accept_point = acceptance.find_ocr_text(
            image, label, acceptance.FULL_SCREEN_REGION, contains=True
        )
        if accept_point is not None:
            button_label = label
            break
    if accept_point is None or button_label is None:
        raise TypedTerminalError(
            "LegalConsentControlNotFound",
            "legal_consent",
            "allowlisted legal agreement is visible but its accept control was not found",
        )
    acceptance.deliberate_click(
        accept_point,
        f"authorized Paradox legal agreement #{index}: {classification['title']}",
    )
    deadline = time.monotonic() + 20
    after_image = None
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        after_image = image_grab.grab()
        after_rows = [
            str(row[0])
            for row in acceptance.ocr_results(
                after_image, LEGAL_MODAL_HEADER_REGION
            )
        ]
        try:
            remaining = classify_authorized_legal_modal(after_rows)
        except TypedTerminalError as next_modal:
            if next_modal.terminal == "LegalConsentNotAuthorized":
                break
            raise
        if (
            remaining is None
            or remaining.get("title") != classification.get("title")
            or remaining.get("version") != classification.get("version")
        ):
            break
        time.sleep(0.25)
    else:
        raise TypedTerminalError(
            "LegalConsentAcceptanceTimeout",
            "legal_consent",
            "allowlisted legal agreement did not close after the authorized click",
        )
    assert after_image is not None
    after_path = ui_dir / f"legal_consent_{index:02d}_after.png"
    after_image.save(after_path)
    stage_artifacts.append(
        {"stage": "legal_consent_after", "path": after_path.name}
    )
    marker_deadline = time.monotonic() + 15
    after_state = account_legal_state(userdir)
    new_markers = newly_persisted_legal_markers(before_state, after_state)
    while not new_markers and time.monotonic() < marker_deadline:
        time.sleep(0.25)
        after_state = account_legal_state(userdir)
        new_markers = newly_persisted_legal_markers(before_state, after_state)
    unauthorized_new = [
        marker for marker in new_markers if not _authorized_legal_marker(marker)
    ]
    if unauthorized_new:
        raise TypedTerminalError(
            "LegalConsentMarkerNotAuthorized",
            "legal_consent",
            "agreement click persisted non-authorized marker(s): "
            + ", ".join(unauthorized_new),
        )
    allowed_new_markers = [
        marker for marker in new_markers if _authorized_legal_marker(marker)
    ]
    if not allowed_new_markers:
        raise TypedTerminalError(
            "LegalConsentMarkerNotPersisted",
            "legal_consent",
            "authorized agreement closed but no new allowlisted accepted marker "
            "was persisted in the isolated userdir",
        )
    return {
        **classification,
        "authorized_click": True,
        "button_label": button_label,
        "before_screenshot": str(before_path.resolve()),
        "before_screenshot_sha256": sha256(before_path),
        "after_screenshot": str(after_path.resolve()),
        "after_screenshot_sha256": sha256(after_path),
        "marker_path": after_state["path"],
        "marker_relative_path": after_state["relative_path"],
        "marker_sha256_before": before_state["sha256"],
        "marker_sha256_after": after_state["sha256"],
        "marker_delta": {
            "before": before_state["markers"],
            "after": after_state["markers"],
            "added": allowed_new_markers,
        },
        "new_accepted_markers": allowed_new_markers,
        "real_profile_modified": False,
    }


__all__ = [
    "LEGAL_ACCEPT_BUTTONS",
    "LEGAL_ALLOWED_TERMS",
    "LEGAL_CONSENT_PROFILE_SUFFIX",
    "LEGAL_DENIED_TERMS",
    "LEGAL_MODAL_HEADER_REGION",
    "TypedTerminalError",
    "_authorized_legal_marker",
    "accept_authorized_legal_modal",
    "account_legal_state",
    "classify_authorized_legal_modal",
    "diagnose_legal_modal",
    "newly_persisted_legal_markers",
    "persist_preclassification_evidence",
    "sha256",
    "validate_legal_consent_source",
]
