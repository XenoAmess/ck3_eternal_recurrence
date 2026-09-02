#!/usr/bin/env python3
"""Shared handling for authorized CK3 agreements and in-game notices.

The project owner permanently authorizes acceptance of any agreement/consent
shown inside CK3 and confirmation, continuation, or dismissal of CK3 in-game
notices.  Purchase, payment, order, checkout, or store actions remain forbidden.
This module is runner-neutral: callers supply their existing OCR, click and
screen-grab adapters and an isolated ``-userdir``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time


LEGAL_CONSENT_PROFILE_SUFFIX = Path("account/PDX/SDK/ck3/account.json")
LEGAL_MODAL_HEADER_REGION = (0.10, 0.02, 0.90, 0.32)
LEGAL_AUTHORIZATION_VERSION = "2026-09-03-any-ck3-agreement-and-notice-v2"
LEGAL_AUTHORIZATION_TEXT = (
    "Project owner permanently authorizes accepting any agreement or consent "
    "shown inside CK3 and confirming, continuing, closing, or dismissing CK3 "
    "in-game notices; purchase, payment, order, checkout, and store actions "
    "are not authorized."
)
LEGAL_ORIGIN_TERMS = (
    "paradox",
    "crusader kings iii",
    "crusader kings 3",
    "ck3",
)
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
LEGAL_PROTOCOL_CATEGORY_TERMS = (
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
LEGAL_PURCHASE_TERMS = (
    "purchase",
    "buy now",
    "buy",
    "payment",
    "paid content",
    "place order",
    "checkout",
    "add to cart",
    "shopping cart",
    "store page",
    "open store",
    "购买",
    "买入",
    "付款",
    "付费",
    "支付",
    "下单",
    "订单",
    "结账",
    "购物车",
    "商店页面",
    "前往商店",
)
# Compatibility export retained for runners which imported the old denylist.
LEGAL_DENIED_TERMS = LEGAL_PURCHASE_TERMS
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
LEGAL_NOTIFICATION_HINTS = (
    "notification",
    "notice",
    "message",
    "announcement",
    "news",
    "通知",
    "提示",
    "消息",
    "公告",
)
LEGAL_ACCEPT_BUTTONS = (
    "我同意",
    "接受",
    "I Agree",
    "Accept",
    "确认",
    "Confirm",
    "继续",
    "Continue",
    "好的",
    "OK",
)
LEGAL_NOTIFICATION_BUTTONS = (
    "关闭",
    "Close",
    "确认",
    "Confirm",
    "继续",
    "Continue",
    "好的",
    "OK",
)
LEGAL_SAFE_ACTION_TERMS = (
    "close",
    "confirm",
    "continue",
    "ok",
    "关闭",
    "确认",
    "继续",
    "好的",
)
LEGAL_PURCHASE_BUTTONS = (
    "Buy Now",
    "Purchase",
    "Pay Now",
    "Place Order",
    "Checkout",
    "Add to Cart",
    "Open Store",
    "购买",
    "立即购买",
    "付款",
    "支付",
    "下单",
    "结账",
    "加入购物车",
    "前往商店",
)


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


def _matching_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for term in terms:
        if term.isascii():
            pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
            matched = re.search(pattern, text) is not None
        else:
            matched = term in text
        if matched:
            matches.append(term)
    return matches


def diagnose_legal_modal(
    rows: list[str], *, ck3_context_confirmed: bool = False
) -> dict[str, object]:
    """Normalize OCR rows and expose the exact token-based classification input."""

    normalized_rows = [" ".join(str(row).split()) for row in rows if str(row).strip()]
    normalized_text = " ".join(normalized_rows).casefold()
    origin_terms = _matching_terms(normalized_text, LEGAL_ORIGIN_TERMS)
    game_context = ck3_context_confirmed or bool(origin_terms)
    purchase_terms = _matching_terms(normalized_text, LEGAL_PURCHASE_TERMS)
    allowed = _matching_terms(normalized_text, LEGAL_ALLOWED_TERMS)
    hints = _matching_terms(normalized_text, LEGAL_DOCUMENT_HINTS)
    categories = _matching_terms(normalized_text, LEGAL_PROTOCOL_CATEGORY_TERMS)
    notification_hints = _matching_terms(normalized_text, LEGAL_NOTIFICATION_HINTS)
    safe_action_terms = _matching_terms(normalized_text, LEGAL_SAFE_ACTION_TERMS)
    agreement_semantics = bool(allowed or hints)
    if not game_context:
        classification_state = "not_ck3_or_paradox"
    elif purchase_terms:
        classification_state = "purchase_forbidden"
    elif agreement_semantics or categories:
        classification_state = "authorized_agreement"
    elif safe_action_terms:
        classification_state = "authorized_notification"
    else:
        classification_state = "not_recognized_modal"
    return {
        "normalized_rows": normalized_rows,
        "normalized_text": normalized_text,
        "ck3_context_confirmed": ck3_context_confirmed,
        "origin_terms": origin_terms,
        "game_context_recognized": game_context,
        "allowed_terms": allowed,
        "denied_terms": purchase_terms,
        "purchase_terms": purchase_terms,
        "legal_document_hints": hints,
        "protocol_category_terms": categories,
        "notification_hints": notification_hints,
        "safe_action_terms": safe_action_terms,
        "classification_state": classification_state,
        "evidence_required": bool(
            game_context
            and (
                purchase_terms
                or agreement_semantics
                or categories
                or safe_action_terms
            )
        ),
        "authorization_text": LEGAL_AUTHORIZATION_TEXT,
        "authorization_version": LEGAL_AUTHORIZATION_VERSION,
    }


def persist_preclassification_evidence(
    image: object,
    rows: list[str],
    ui_dir: Path,
    index: int,
    *,
    ck3_context_confirmed: bool = False,
) -> dict[str, object]:
    """Persist the exact frame and OCR inputs before any legal classification."""

    diagnostics = diagnose_legal_modal(
        rows, ck3_context_confirmed=ck3_context_confirmed
    )
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
    rows: list[str], *, ck3_context_confirmed: bool = False
) -> dict[str, object] | None:
    """Classify an OCR header, returning ``None`` when no legal modal exists."""

    diagnostics = diagnose_legal_modal(
        rows, ck3_context_confirmed=ck3_context_confirmed
    )
    cleaned = diagnostics["normalized_rows"]
    joined = diagnostics["normalized_text"]
    assert isinstance(cleaned, list)
    assert isinstance(joined, str)
    if not diagnostics["game_context_recognized"]:
        return None
    purchase_terms = diagnostics["purchase_terms"]
    assert isinstance(purchase_terms, list)
    if purchase_terms:
        raise TypedTerminalError(
            "PurchaseActionNotAuthorized",
            "ck3_modal",
            f"CK3 modal contains forbidden purchase/action tokens: {purchase_terms}",
            diagnostics=diagnostics,
        )
    allowed = diagnostics["allowed_terms"]
    assert isinstance(allowed, list)
    hints = diagnostics["legal_document_hints"]
    assert isinstance(hints, list)
    categories = diagnostics["protocol_category_terms"]
    assert isinstance(categories, list)
    notification_hints = diagnostics["notification_hints"]
    assert isinstance(notification_hints, list)
    safe_action_terms = diagnostics["safe_action_terms"]
    assert isinstance(safe_action_terms, list)
    if not allowed and not hints and not categories:
        if not safe_action_terms:
            return None
        title = cleaned[0] if cleaned else ""
        return {
            "modal_kind": "notification",
            "title": title,
            "version": None,
            "allowed_terms": [],
            "denied_terms": [],
            "protocol_category_terms": categories,
            "notification_hints": notification_hints,
            "safe_action_terms": safe_action_terms,
            "authorization_text": LEGAL_AUTHORIZATION_TEXT,
            "authorization_version": LEGAL_AUTHORIZATION_VERSION,
        }
    if not cleaned:
        return None
    title = next(
        (
            row
            for row in cleaned
            if any(term in row.casefold() for term in (*allowed, *hints))
        ),
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
        "modal_kind": "agreement",
        "title": title,
        "version": version,
        "allowed_terms": allowed,
        "denied_terms": [],
        "protocol_category_terms": categories,
        "notification_hints": notification_hints,
        "safe_action_terms": safe_action_terms,
        "authorization_text": LEGAL_AUTHORIZATION_TEXT,
        "authorization_version": LEGAL_AUTHORIZATION_VERSION,
    }


def validate_legal_consent_source(
    source: Path, contract: dict[str, object]
) -> dict[str, object]:
    expected = {
        "source_profile_relative_path": LEGAL_CONSENT_PROFILE_SUFFIX.as_posix(),
        "source_sha256": "8933437F2000BB639D588A541B798F97C6D87BA7D891613FAC23D1812AB9EB28",
        "authorization_text": LEGAL_AUTHORIZATION_TEXT,
        "authorization_version": LEGAL_AUTHORIZATION_VERSION,
        "authorized_document_kinds": [
            "any CK3/Paradox in-game agreement, consent, terms, or policy",
            "privacy, telemetry, advertising, marketing, personalization, and data-sharing agreements",
            "CK3 in-game notifications via confirm, continue, close, or dismiss controls",
        ],
        "explicitly_not_authorized": [
            "purchase",
            "payment",
            "paid order",
            "checkout",
            "store action",
        ],
        "accepted_marker_present": False,
        "allow_exact_semantic_modal_acceptance": True,
        "allow_all_ck3_agreements_and_notifications": True,
        "forbid_purchase_payment_order_checkout_store_actions": True,
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
    if not normalized:
        return False
    return not _matching_terms(normalized.replace("-", " "), LEGAL_PURCHASE_TERMS)


def accept_authorized_legal_modal(
    acceptance: object,
    image_grab: object,
    userdir: Path,
    ui_dir: Path,
    image: object,
    rows: list[str],
    index: int,
    stage_artifacts: list[dict[str, object]],
    *,
    ck3_context_confirmed: bool = False,
) -> dict[str, object]:
    """Handle one authorized CK3 modal and preserve its evidence."""

    classification = classify_authorized_legal_modal(
        rows, ck3_context_confirmed=ck3_context_confirmed
    )
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
    modal_kind = str(classification.get("modal_kind"))
    ui_dir.mkdir(parents=True, exist_ok=True)
    before_path = ui_dir / f"legal_consent_{index:02d}_before.png"
    image.save(before_path)
    stage_artifacts.append(
        {"stage": "legal_consent_before", "path": before_path.name}
    )
    before_state = account_legal_state(userdir)
    for forbidden_label in LEGAL_PURCHASE_BUTTONS:
        forbidden_point = acceptance.find_ocr_text(
            image,
            forbidden_label,
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        )
        if forbidden_point is not None:
            diagnostics = diagnose_legal_modal(
                rows, ck3_context_confirmed=ck3_context_confirmed
            )
            diagnostics["forbidden_control_label"] = forbidden_label
            raise TypedTerminalError(
                "PurchaseActionNotAuthorized",
                "ck3_modal",
                f"forbidden purchase control is visible: {forbidden_label}",
                diagnostics=diagnostics,
            )
    accept_point = None
    button_label = None
    button_labels = (
        LEGAL_ACCEPT_BUTTONS
        if modal_kind == "agreement"
        else LEGAL_NOTIFICATION_BUTTONS
    )
    for label in button_labels:
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
        f"authorized CK3 {modal_kind} #{index}: {classification['title']}",
    )
    deadline = time.monotonic() + 20
    after_image = None
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        after_image = image_grab.grab()
        after_rows = [
            str(row[0])
            for row in acceptance.ocr_results(
                after_image, acceptance.FULL_SCREEN_REGION
            )
        ]
        try:
            remaining = classify_authorized_legal_modal(
                after_rows, ck3_context_confirmed=ck3_context_confirmed
            )
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
    after_state = account_legal_state(userdir)
    new_markers = newly_persisted_legal_markers(before_state, after_state)
    if modal_kind == "agreement":
        marker_deadline = time.monotonic() + 15
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
    if modal_kind == "agreement" and not allowed_new_markers:
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
        "authorization_text": LEGAL_AUTHORIZATION_TEXT,
        "authorization_version": LEGAL_AUTHORIZATION_VERSION,
        "real_profile_modified": False,
    }


__all__ = [
    "LEGAL_ACCEPT_BUTTONS",
    "LEGAL_ALLOWED_TERMS",
    "LEGAL_AUTHORIZATION_TEXT",
    "LEGAL_AUTHORIZATION_VERSION",
    "LEGAL_CONSENT_PROFILE_SUFFIX",
    "LEGAL_DENIED_TERMS",
    "LEGAL_MODAL_HEADER_REGION",
    "LEGAL_NOTIFICATION_BUTTONS",
    "LEGAL_PURCHASE_BUTTONS",
    "LEGAL_PURCHASE_TERMS",
    "LEGAL_SAFE_ACTION_TERMS",
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
