"""Fresh-frame, opaque-token control with positive postconditions."""

from __future__ import annotations

from collections.abc import Callable
import copy
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import math
from pathlib import Path
import secrets
import time
import uuid

from ..environment import sha256_file, write_json_atomic
from ..errors import AgentError
from ..vision.classifier import (
    ControlSpec,
    UiContract,
    require_canonical_phase_b_contract,
)
from ..vision.model import Observation, OcrSpan, StableObservation, VisibleControl
from ..vision.ocr import matching_spans, ocr_spans
from ..vision.window import BoundGameWindow, ForegroundLossError


_INPUT_MOUSE = 0
_INPUT_KEYBOARD = 1
_MOUSEEVENTF_LEFTDOWN = 0x0002
_MOUSEEVENTF_LEFTUP = 0x0004
_MOUSEEVENTF_RIGHTDOWN = 0x0008
_MOUSEEVENTF_RIGHTUP = 0x0010
_KEYEVENTF_KEYUP = 0x0002
_KEYEVENTF_SCANCODE = 0x0008


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    )


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    )


class _INPUT_VALUE(ctypes.Union):
    _fields_ = (("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT))


class _INPUT(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = (("type", wintypes.DWORD), ("value", _INPUT_VALUE))


def _prepare_left_click_batch(
    hold_seconds: float = 0.0,
) -> Callable[[], tuple[int, int]]:
    """Prepare an immediate or deliberately held left click."""
    if (
        isinstance(hold_seconds, bool)
        or not isinstance(hold_seconds, (int, float))
        or not math.isfinite(float(hold_seconds))
        or not 0 <= float(hold_seconds) <= 0.25
    ):
        raise AgentError("visible click hold duration is invalid")
    hold_seconds = float(hold_seconds)
    records = (_INPUT * 2)()
    records[0].type = _INPUT_MOUSE
    records[0].mi.dwFlags = _MOUSEEVENTF_LEFTDOWN
    records[1].type = _INPUT_MOUSE
    records[1].mi.dwFlags = _MOUSEEVENTF_LEFTUP

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send_input = user32.SendInput
    send_input.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
    send_input.restype = wintypes.UINT

    def submit() -> tuple[int, int]:
        if hold_seconds:
            sent_down = int(send_input(1, records, ctypes.sizeof(_INPUT)))
            if sent_down != 1:
                return sent_down, int(ctypes.get_last_error())
            time.sleep(hold_seconds)
            sent_up = int(
                send_input(
                    1,
                    ctypes.cast(
                        ctypes.byref(records, ctypes.sizeof(_INPUT)),
                        ctypes.POINTER(_INPUT),
                    ),
                    ctypes.sizeof(_INPUT),
                )
            )
            error = ctypes.get_last_error() if sent_up != 1 else 0
            return sent_down + sent_up, int(error)
        sent = int(send_input(2, records, ctypes.sizeof(_INPUT)))
        error = ctypes.get_last_error() if sent != 2 else 0
        return sent, int(error)

    return submit


def _prepare_right_click_batch() -> Callable[[], tuple[int, int]]:
    """Prepare one right-button down/up SendInput batch."""
    records = (_INPUT * 2)()
    records[0].type = _INPUT_MOUSE
    records[0].mi.dwFlags = _MOUSEEVENTF_RIGHTDOWN
    records[1].type = _INPUT_MOUSE
    records[1].mi.dwFlags = _MOUSEEVENTF_RIGHTUP
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send_input = user32.SendInput
    send_input.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
    send_input.restype = wintypes.UINT

    def submit() -> tuple[int, int]:
        sent = int(send_input(2, records, ctypes.sizeof(_INPUT)))
        error = ctypes.get_last_error() if sent != 2 else 0
        return sent, int(error)

    return submit


def _prepare_key_press_batch(scan_code: int) -> Callable[[], tuple[int, int]]:
    """Prepare one scan-code key-down/key-up SendInput batch."""
    if type(scan_code) is not int or not 1 <= scan_code <= 0xFF:
        raise AgentError("visible key scan code is invalid")
    records = (_INPUT * 2)()
    records[0].type = _INPUT_KEYBOARD
    records[0].ki.wScan = scan_code
    records[0].ki.dwFlags = _KEYEVENTF_SCANCODE
    records[1].type = _INPUT_KEYBOARD
    records[1].ki.wScan = scan_code
    records[1].ki.dwFlags = _KEYEVENTF_SCANCODE | _KEYEVENTF_KEYUP

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send_input = user32.SendInput
    send_input.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
    send_input.restype = wintypes.UINT

    def submit() -> tuple[int, int]:
        sent = int(send_input(2, records, ctypes.sizeof(_INPUT)))
        error = ctypes.get_last_error() if sent != 2 else 0
        return sent, int(error)

    return submit


def _prepare_key_chord_batch(
    modifier_scan_code: int, scan_code: int
) -> Callable[[], tuple[int, int]]:
    """Prepare one modifier+key scan-code chord in a single SendInput batch."""
    if (
        type(modifier_scan_code) is not int
        or not 1 <= modifier_scan_code <= 0xFF
        or type(scan_code) is not int
        or not 1 <= scan_code <= 0xFF
        or modifier_scan_code == scan_code
    ):
        raise AgentError("visible key chord scan codes are invalid")
    records = (_INPUT * 4)()
    for record in records:
        record.type = _INPUT_KEYBOARD
    records[0].ki.wScan = modifier_scan_code
    records[0].ki.dwFlags = _KEYEVENTF_SCANCODE
    records[1].ki.wScan = scan_code
    records[1].ki.dwFlags = _KEYEVENTF_SCANCODE
    records[2].ki.wScan = scan_code
    records[2].ki.dwFlags = _KEYEVENTF_SCANCODE | _KEYEVENTF_KEYUP
    records[3].ki.wScan = modifier_scan_code
    records[3].ki.dwFlags = _KEYEVENTF_SCANCODE | _KEYEVENTF_KEYUP

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send_input = user32.SendInput
    send_input.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
    send_input.restype = wintypes.UINT

    def submit() -> tuple[int, int]:
        sent = int(send_input(4, records, ctypes.sizeof(_INPUT)))
        error = ctypes.get_last_error() if sent != 4 else 0
        return sent, int(error)

    return submit


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class _IssuedControl:
    observation: Observation
    spec: ControlSpec
    span: OcrSpan
    issued_monotonic: float
    stable_observation: StableObservation | None = None


@dataclass(frozen=True)
class _InternalControlLease:
    purpose: str
    parent_authority_sha256: str
    claims_sha256: str
    token_sha256: str
    issued_monotonic: float
    expires_monotonic: float
    signature: str


class VisibleUiDriver:
    TOKEN_TTL_SECONDS = 5.0
    TARGET_PATCH_PADDING = 12
    PHASE_B_ALLOWED_CONTROLS = frozenset({"main_menu.new_game"})

    def __init__(
        self,
        window: BoundGameWindow,
        contract: UiContract,
        artifacts: Path,
        *,
        expected_game_version: str,
        expected_language: str,
        expected_contract_sha256: str,
        durable_event_callback: Callable[[dict[str, object]], str],
        allowed_controls: frozenset[str] | None = None,
    ) -> None:
        if contract.resolution != (2560, 1440):
            raise AgentError(f"unsupported UI resolution: {contract.resolution}")
        if (
            contract.game_version != expected_game_version
            or contract.language != expected_language
        ):
            raise AgentError("UI contract game version or language differs")
        registered = frozenset(item.control_id for item in contract.controls)
        if allowed_controls is None:
            require_canonical_phase_b_contract(contract, expected_contract_sha256)
            allowed_controls = self.PHASE_B_ALLOWED_CONTROLS
        elif (
            contract.source_sha256 != expected_contract_sha256
            or not allowed_controls
            or registered != allowed_controls
        ):
            raise AgentError("visible UI action contract or explicit allowlist differs")
        if not registered <= allowed_controls:
            raise AgentError(
                f"UI contract exceeds the action allowlist: {sorted(registered)!r}"
            )
        self.window = window
        self.contract = contract
        self.artifacts = artifacts.resolve()
        if (
            self.artifacts.name != "artifacts"
            or self.artifacts.parent.parent.name != "runs"
            or not self.artifacts.is_dir()
        ):
            raise AgentError("UI artifacts must be an existing state/runs/<id>/artifacts")
        if not callable(durable_event_callback):
            raise AgentError("visible UI driver requires a durable main-chain callback")
        self._durable_event_callback = durable_event_callback
        self._contract_sha256 = expected_contract_sha256
        self._secret = secrets.token_bytes(32)
        self._session_nonce = secrets.token_hex(16)
        self._issued: dict[str, _IssuedControl] = {}
        self._sequence = 0
        self._capture_sequence = 0
        self._input_budget_consumed = False
        self._consumed_internal_leases: set[str] = set()

    def _emit_durable_event(self, event: dict[str, object]) -> str:
        # The callback receives an immutable-by-ownership snapshot: retaining
        # or mutating nested target/binding objects cannot alter the action
        # receipt or a later event payload.
        digest = self._durable_event_callback(copy.deepcopy(event))
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise AgentError("durable UI event callback returned an invalid digest")
        return digest

    @staticmethod
    def _observation_evidence(observation: Observation) -> dict[str, object]:
        return {
            "observation_id": observation.observation_id,
            "frame_id": observation.frame_id,
            "captured_at": observation.captured_at,
            "capture_sequence": observation.capture_sequence,
            "captured_monotonic": observation.captured_monotonic,
            "screenshot": observation.screenshot,
            "screenshot_sha256": observation.screenshot_sha256,
            "observation": observation.audit_path,
            "screen": observation.screen,
            "pid": observation.pid,
            "hwnd": observation.hwnd,
            "client_rect": list(observation.client_rect),
        }

    @property
    def registered_capabilities(self) -> frozenset[str]:
        return frozenset(item.control_id for item in self.contract.controls)

    def _artifact_stem(self, kind: str) -> str:
        self._sequence += 1
        return f"{self._sequence:05d}-{kind}-{uuid.uuid4().hex}"

    def _token(
        self, observation_id: str, frame_id: str, spec: ControlSpec, span: OcrSpan
    ) -> str:
        payload = json.dumps(
            {
                "session_nonce": self._session_nonce,
                "observation_id": observation_id,
                "frame_id": frame_id,
                "control_id": spec.control_id,
                "bbox": span.bbox,
                "text": span.normalized,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    def _internal_lease_claims(
        self,
        *,
        purpose: str,
        action_id: str,
        caller_token_sha256: str,
        parent_authority_sha256: str,
        binding: dict[str, object],
        action_deadline: float,
        observation: Observation,
        spec: ControlSpec,
        span: OcrSpan,
        target: dict[str, object],
        issued_monotonic: float,
        expires_monotonic: float,
    ) -> dict[str, object]:
        matching_controls = [
            control
            for control in observation.controls
            if control.control_id == spec.control_id
            and control.bbox == span.bbox
            and control.center == span.center
        ]
        if len(matching_controls) != 1:
            stage = "fresh" if purpose.startswith("fresh_") else "hover"
            raise AgentError(
                f"{stage} visible control lease lacks one exact observation control"
            )
        source_token = matching_controls[0].token
        expected_source_token = self._token(
            observation.observation_id, observation.frame_id, spec, span
        )
        if (
            not isinstance(source_token, str)
            or len(source_token) != 64
            or any(character not in "0123456789abcdef" for character in source_token)
            or not hmac.compare_digest(source_token, expected_source_token)
        ):
            raise AgentError("visible control lease source token is invalid")
        return {
            "protocol_version": 2,
            "purpose": purpose,
            "action_id": action_id,
            "control_id": spec.control_id,
            "caller_token_sha256": caller_token_sha256,
            "contract_sha256": self._contract_sha256,
            "binding": copy.deepcopy(binding),
            "action_deadline_monotonic": action_deadline,
            "parent_authority_sha256": parent_authority_sha256,
            "observation": self._observation_evidence(observation),
            "source_control_token_sha256": hashlib.sha256(
                source_token.encode("ascii")
            ).hexdigest(),
            "target": copy.deepcopy(target),
            "issued_monotonic": issued_monotonic,
            "expires_monotonic": expires_monotonic,
        }

    @staticmethod
    def _canonical_claims(claims: dict[str, object]) -> bytes:
        return json.dumps(
            claims, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def _issue_internal_lease(
        self,
        *,
        purpose: str,
        action_id: str,
        caller_token_sha256: str,
        parent_authority_sha256: str,
        binding: dict[str, object],
        action_deadline: float,
        observation: Observation,
        spec: ControlSpec,
        span: OcrSpan,
        target: dict[str, object],
    ) -> _InternalControlLease:
        if purpose not in {
            "fresh_target_pointer_move",
            "hover_verified_left_click_batch",
        }:
            raise AgentError("visible control lease stage is invalid")
        stage = "fresh" if purpose.startswith("fresh_") else "hover"
        if observation.screen != spec.screen:
            raise AgentError(f"{stage} visible control lease screen differs")
        issued_monotonic = float(observation.captured_monotonic)
        expires_monotonic = issued_monotonic + self.TOKEN_TTL_SECONDS
        if (
            not math.isfinite(issued_monotonic)
            or issued_monotonic < 0
            or not math.isfinite(expires_monotonic)
        ):
            raise AgentError(f"{stage} visible control lease clock is invalid")
        claims = self._internal_lease_claims(
            purpose=purpose,
            action_id=action_id,
            caller_token_sha256=caller_token_sha256,
            parent_authority_sha256=parent_authority_sha256,
            binding=binding,
            action_deadline=action_deadline,
            observation=observation,
            spec=spec,
            span=span,
            target=target,
            issued_monotonic=issued_monotonic,
            expires_monotonic=expires_monotonic,
        )
        payload = self._canonical_claims(claims)
        claims_sha256 = hashlib.sha256(payload).hexdigest()
        signature = hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        return _InternalControlLease(
            purpose=purpose,
            parent_authority_sha256=parent_authority_sha256,
            claims_sha256=claims_sha256,
            token_sha256=hashlib.sha256(signature.encode("ascii")).hexdigest(),
            issued_monotonic=issued_monotonic,
            expires_monotonic=expires_monotonic,
            signature=signature,
        )

    @staticmethod
    def _lease_evidence(
        lease: _InternalControlLease, consumed_monotonic: float | None
    ) -> dict[str, object]:
        return {
            "purpose": lease.purpose,
            "parent_authority_sha256": lease.parent_authority_sha256,
            "claims_sha256": lease.claims_sha256,
            "token_sha256": lease.token_sha256,
            "issued_monotonic": lease.issued_monotonic,
            "expires_monotonic": lease.expires_monotonic,
            "consumed_monotonic": consumed_monotonic,
        }

    def _require_internal_lease(
        self,
        lease: _InternalControlLease,
        *,
        purpose: str,
        action_id: str,
        caller_token_sha256: str,
        parent_authority_sha256: str,
        binding: dict[str, object],
        observation: Observation,
        spec: ControlSpec,
        span: OcrSpan,
        target: dict[str, object],
        action_deadline: float,
        checkpoint: str,
        consume: bool,
    ) -> float:
        stage = "fresh" if purpose.startswith("fresh_") else "hover"
        claims = self._internal_lease_claims(
            purpose=purpose,
            action_id=action_id,
            caller_token_sha256=caller_token_sha256,
            parent_authority_sha256=parent_authority_sha256,
            binding=binding,
            action_deadline=action_deadline,
            observation=observation,
            spec=spec,
            span=span,
            target=target,
            issued_monotonic=lease.issued_monotonic,
            expires_monotonic=lease.expires_monotonic,
        )
        payload = self._canonical_claims(claims)
        expected_claims_sha256 = hashlib.sha256(payload).hexdigest()
        expected_signature = hmac.new(
            self._secret, payload, hashlib.sha256
        ).hexdigest()
        expected_token_sha256 = hashlib.sha256(
            expected_signature.encode("ascii")
        ).hexdigest()
        if (
            lease.purpose != purpose
            or lease.parent_authority_sha256 != parent_authority_sha256
            or lease.claims_sha256 != expected_claims_sha256
            or lease.token_sha256 != expected_token_sha256
            or not hmac.compare_digest(lease.signature, expected_signature)
        ):
            raise AgentError(f"{stage} visible control lease binding differs")
        checked = time.monotonic()
        if checked < lease.issued_monotonic or checked > lease.expires_monotonic:
            raise AgentError(f"{stage} visible control lease expired {checkpoint}")
        if checked > action_deadline:
            raise AgentError(f"visible action deadline expired {checkpoint}")
        if consume:
            if lease.token_sha256 in self._consumed_internal_leases:
                raise AgentError(f"{stage} visible control lease was already consumed")
            self._consumed_internal_leases.add(lease.token_sha256)
        return checked

    def _capture_observation_with_image(
        self, expected_screen: str | None = None
    ) -> tuple[Observation, object]:
        self._issued.clear()
        capture_started_at = _now()
        captured_monotonic = time.monotonic()
        self._capture_sequence += 1
        try:
            image = self.window.capture()
        except ForegroundLossError as error:
            raise error.with_context(
                capture_sequence=self._capture_sequence,
                expected_screen=expected_screen,
            ) from error
        spans = ocr_spans(image)
        screen, confidence, reasons, anchors = self.contract.classify(spans, image)
        observation_id = uuid.uuid4().hex
        frame_id = uuid.uuid4().hex
        stem = self._artifact_stem("frame")
        screenshot = self.artifacts / f"{stem}.png"
        observation_path = self.artifacts / f"{stem}.observation.json"
        screenshot_ref = f"artifacts/{screenshot.name}"
        observation_ref = f"artifacts/{observation_path.name}"
        image.save(screenshot)
        controls: list[VisibleControl] = []
        for spec in self.contract.controls_for(screen):
            matches = matching_spans(
                spans,
                spec.text,
                self.contract.resolution,
                spec.region,
                contains=spec.contains,
            )
            if len(matches) != 1:
                reasons = (*reasons, f"{spec.control_id} matches={len(matches)}")
                screen = "unknown"
                confidence = 0.0
                controls = []
                break
            span = matches[0]
            token = self._token(observation_id, frame_id, spec, span)
            control = VisibleControl(
                control_id=spec.control_id,
                label=spec.label,
                token=token,
                bbox=span.bbox,
                center=span.center,
            )
            controls.append(control)
        observation = Observation(
            observation_id=observation_id,
            frame_id=frame_id,
            captured_at=_now(),
            screen=screen,
            pid=self.window.pid,
            hwnd=self.window.hwnd,
            client_rect=self.window.client_rect,
            screenshot=screenshot_ref,
            screenshot_sha256=sha256_file(screenshot),
            spans=spans,
            anchors=anchors,
            controls=tuple(controls),
            confidence=confidence,
            unknown_reasons=reasons,
            capture_sequence=self._capture_sequence,
            captured_monotonic=captured_monotonic,
            audit_path=observation_ref,
        )
        for control in controls:
            spec = self.contract.control(control.control_id)
            span = next(item for item in spans if item.bbox == control.bbox)
            self._issued[control.token] = _IssuedControl(
                observation=observation,
                spec=spec,
                span=span,
                issued_monotonic=time.monotonic(),
                stable_observation=None,
            )
        write_json_atomic(
            observation_path,
            {
                **observation.to_audit_json(),
                "private_audit": {
                    **observation.to_audit_json()["private_audit"],
                    "capture_started_at": capture_started_at,
                },
            },
        )
        return observation, image

    def _capture_observation(
        self, expected_screen: str | None = None
    ) -> Observation:
        observation, _image = self._capture_observation_with_image(expected_screen)
        return observation

    def capture_once(self, expected_screen: str | None = None) -> Observation:
        """Capture one persisted visible frame without requiring a known screen."""
        return self._capture_observation(expected_screen)

    def _target_patch_bbox(
        self, bbox: tuple[int, int, int, int]
    ) -> tuple[int, int, int, int]:
        left, top, right, bottom = bbox
        width, height = self.contract.resolution
        padding = self.TARGET_PATCH_PADDING
        return (
            max(0, left - padding),
            max(0, top - padding),
            min(width, right + padding),
            min(height, bottom + padding),
        )

    @staticmethod
    def _memory_image_sha256(image: object) -> str:
        mode = str(getattr(image, "mode", ""))
        size = tuple(getattr(image, "size", ()))
        tobytes = getattr(image, "tobytes", None)
        if not mode or len(size) != 2 or not callable(tobytes):
            raise AgentError("target patch is not a concrete raster image")
        digest = hashlib.sha256()
        digest.update(f"{mode}:{size[0]}x{size[1]}\0".encode("ascii"))
        digest.update(tobytes())
        return digest.hexdigest()

    def observe_stable(
        self,
        expected_screen: str,
        timeout_seconds: float,
        *,
        stable_frames: int = 2,
        absolute_deadline_monotonic: float | None = None,
    ) -> StableObservation:
        if stable_frames != 2:
            raise AgentError("Phase-B visible states require exactly two stable frames")
        deadline = time.monotonic() + timeout_seconds
        if absolute_deadline_monotonic is not None:
            if (
                isinstance(absolute_deadline_monotonic, bool)
                or not isinstance(absolute_deadline_monotonic, (int, float))
                or not math.isfinite(float(absolute_deadline_monotonic))
            ):
                raise AgentError("visible observation deadline must be finite")
            # The relative timeout is only a convenience for callers.  An
            # already-established action deadline must never be re-based if
            # this thread is descheduled between computing the remaining time
            # and entering the observation loop.
            deadline = min(deadline, float(absolute_deadline_monotonic))
        prior: Observation | None = None
        hits = 0
        last: Observation | None = None
        while time.monotonic() < deadline:
            last = self._capture_observation(expected_screen)
            if time.monotonic() >= deadline:
                break
            if last.screen != expected_screen:
                hits = 0
                prior = None
            else:
                stable = prior is not None
                if stable:
                    prior_anchors = {
                        item.anchor_id: item.center for item in prior.anchors
                    }
                    if set(prior_anchors) != {
                        item.anchor_id for item in last.anchors
                    }:
                        stable = False
                    for anchor in last.anchors:
                        old = prior_anchors.get(anchor.anchor_id)
                        if old is None or abs(old[0] - anchor.center[0]) > 15 or abs(
                            old[1] - anchor.center[1]
                        ) > 15:
                            stable = False
                            break
                    prior_controls = {item.control_id: item.center for item in prior.controls}
                    if set(prior_controls) != {
                        item.control_id for item in last.controls
                    }:
                        stable = False
                    for control in last.controls:
                        old = prior_controls.get(control.control_id)
                        if old is None or abs(old[0] - control.center[0]) > 15 or abs(
                            old[1] - control.center[1]
                        ) > 15:
                            stable = False
                            break
                    if (
                        last.capture_sequence != prior.capture_sequence + 1
                        or last.captured_monotonic <= prior.captured_monotonic
                        or last.captured_monotonic - prior.captured_monotonic > 10
                    ):
                        stable = False
                hits = hits + 1 if stable else 1
                if hits >= stable_frames:
                    if prior is None:
                        raise AgentError("stable visible state lacks its first frame")
                    accepted = StableObservation(expected_screen, (prior, last))
                    for control in last.controls:
                        issued = self._issued.get(control.token)
                        if issued is None:
                            raise AgentError("stable visible control token disappeared")
                        self._issued[control.token] = _IssuedControl(
                            issued.observation,
                            issued.spec,
                            issued.span,
                            issued.issued_monotonic,
                            accepted,
                        )
                    return accepted
                prior = last
            time.sleep(0.5)
        detail = last.unknown_reasons if last is not None else ("no frame",)
        raise AgentError(
            f"visible UI timeout waiting for {expected_screen}: {detail!r}"
        )

    def click_visible_control(
        self,
        control_token: str,
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        if self._input_budget_consumed:
            raise AgentError("visible UI driver input budget is already consumed")
        # A malformed, expired, or rejected invocation still consumes the
        # driver's only capability.  A fresh token must never become a retry.
        self._input_budget_consumed = True
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or float(timeout_seconds) <= 0
        ):
            raise AgentError("visible action timeout must be finite and positive")
        issued = self._issued.pop(control_token, None)
        if issued is None:
            raise AgentError("unknown, stale, or already consumed control token")
        admission_checked = time.monotonic()
        admission_age = admission_checked - issued.issued_monotonic
        if (
            not math.isfinite(admission_checked)
            or not math.isfinite(issued.issued_monotonic)
            or not math.isfinite(admission_age)
            or admission_age < 0
            or admission_age > self.TOKEN_TTL_SECONDS
        ):
            raise AgentError("visible control token expired")
        action_deadline = admission_checked + float(timeout_seconds)
        if issued.stable_observation is None:
            raise AgentError("visible control was not issued by a stable two-frame state")
        before, spec, old_span = (
            issued.observation,
            issued.spec,
            issued.span,
        )
        before_stable = issued.stable_observation
        binding = self.window.audit_binding()
        action_id = uuid.uuid4().hex
        action_path = self.artifacts / f"{self._artifact_stem('action')}.json"
        action_ref = f"artifacts/{action_path.name}"
        token_hash = hashlib.sha256(control_token.encode("ascii")).hexdigest()
        authorization: dict[str, object] = {
            "protocol_version": 2,
            "action_admitted_monotonic": admission_checked,
            "action_timeout_seconds": float(timeout_seconds),
            "action_deadline_monotonic": action_deadline,
            "caller_token_issued_monotonic": issued.issued_monotonic,
            "fresh_move_lease": None,
            "hover_click_lease": None,
        }
        result: dict[str, object] = {
            "format_version": 2,
            "action_id": action_id,
            "planned_at": _now(),
            "kind": "click_visible_control",
            "control_id": spec.control_id,
            "control_token_sha256": token_hash,
            "before_observation_id": before.observation_id,
            "expected_post_screen": spec.post_screen,
            "status": "planned",
            "input_may_have_occurred": False,
            "risk": spec.risk,
            "policy_boundary": "no caller-supplied coordinates or postconditions",
            "contract_sha256": self._contract_sha256,
            "receipt_artifact": action_ref,
            "input_budget": {"limit": 1, "consumed": 1},
            "binding": binding,
            "before_stable_observation": before_stable.to_audit_evidence(),
            "target": {
                "issued": {
                    "text": old_span.text,
                    "normalized": old_span.normalized,
                    "bbox": list(old_span.bbox),
                    "center": list(old_span.center),
                }
            },
            "pointer_input_may_have_occurred": False,
            "button_click_may_have_occurred": False,
            "send_input": {"requested": 2, "accepted": None, "last_error": None},
            "durable_events": {},
            "authorization": authorization,
        }
        input_armed = False
        click_submission_started = False
        planned_event_written = False
        durable_event_callback_failed = False
        confirmed_receipt_written = False
        try:
            write_json_atomic(action_path, result)
            planned_digest = self._emit_durable_event(
                {
                    "kind": "ui_action_planned",
                    "action_id": action_id,
                    "control_id": spec.control_id,
                    "token_sha256": token_hash,
                    "contract_sha256": self._contract_sha256,
                    "receipt_artifact": action_ref,
                    "before_frame_ids": [
                        frame.frame_id for frame in before_stable.frames
                    ],
                }
            )
            planned_event_written = True
            result["durable_events"]["planned"] = planned_digest
            write_json_atomic(action_path, result)
            self.window.require_foreground()
            fresh = self._capture_observation(spec.screen)
            result["fresh_observation_id"] = fresh.observation_id
            result["fresh_observation"] = self._observation_evidence(fresh)
            if fresh.screen != before.screen or fresh.screen != spec.screen:
                raise AgentError(
                    f"screen changed before input: {before.screen} -> {fresh.screen}"
                )
            matches = matching_spans(
                fresh.spans,
                spec.text,
                self.contract.resolution,
                spec.region,
                contains=spec.contains,
            )
            if len(matches) != 1:
                raise AgentError(f"fresh visible target is not unique: {len(matches)}")
            target = matches[0]
            if abs(target.center[0] - old_span.center[0]) > 15 or abs(
                target.center[1] - old_span.center[1]
            ) > 15:
                raise AgentError("visible target moved beyond the fresh-frame tolerance")
            self.window.require_unobscured(target.center)
            click_point = spec.click_point_px or (
                target.center[0] + spec.click_offset_px[0],
                target.center[1] + spec.click_offset_px[1],
            )
            if not (
                0 <= click_point[0] < self.contract.resolution[0]
                and 0 <= click_point[1] < self.contract.resolution[1]
            ):
                raise AgentError("visible control click point is outside the client")
            self.window.require_unobscured(click_point)

            import pyautogui

            pyautogui.FAILSAFE = True
            submit_left_click = _prepare_left_click_batch(spec.click_hold_seconds)
            screen_point = (
                self.window.client_rect[0] + click_point[0],
                self.window.client_rect[1] + click_point[1],
            )
            result["target"]["fresh"] = {
                "text": target.text,
                "normalized": target.normalized,
                "bbox": list(target.bbox),
                "center": list(target.center),
                "screen_point": list(screen_point),
            }
            fresh_target = result["target"]["fresh"]
            if not isinstance(fresh_target, dict):
                raise AgentError("fresh visible target evidence is malformed")
            fresh_lease = self._issue_internal_lease(
                purpose="fresh_target_pointer_move",
                action_id=action_id,
                caller_token_sha256=token_hash,
                parent_authority_sha256=token_hash,
                binding=binding,
                action_deadline=action_deadline,
                observation=fresh,
                spec=spec,
                span=target,
                target=fresh_target,
            )
            authorization["fresh_move_lease"] = self._lease_evidence(
                fresh_lease, None
            )
            self._require_internal_lease(
                fresh_lease,
                purpose="fresh_target_pointer_move",
                action_id=action_id,
                caller_token_sha256=token_hash,
                parent_authority_sha256=token_hash,
                binding=binding,
                observation=fresh,
                spec=spec,
                span=target,
                target=fresh_target,
                action_deadline=action_deadline,
                checkpoint="before input arming",
                consume=False,
            )

            # This is the authoritative write-ahead boundary.  It is emitted
            # through the caller's fsync-backed main run chain before even the
            # hover cursor move.  Its conservative click flag remains true if
            # an asynchronous termination prevents a terminal receipt.
            result["status"] = "input_attempting"
            result["input_may_have_occurred"] = True
            result["pointer_input_may_have_occurred"] = True
            result["button_click_may_have_occurred"] = True
            result["input_attempted_at"] = _now()
            write_json_atomic(action_path, result)
            # Once WAL publication starts, an exception cannot tell us
            # whether the fsync-backed callback failed before or after the
            # record became durable.  Keep the receipt conservative and never
            # downgrade this latch in the error path.
            input_armed = True
            try:
                armed_digest = self._emit_durable_event(
                    {
                        "kind": "ui_input_armed",
                        "action_id": action_id,
                        "control_id": spec.control_id,
                        "contract_sha256": self._contract_sha256,
                        "receipt_artifact": action_ref,
                        "binding": binding,
                        "target": result["target"],
                        "fresh_move_lease_sha256": fresh_lease.token_sha256,
                        "pointer_input_may_have_occurred": True,
                        "button_click_may_have_occurred": True,
                    }
                )
            except Exception:
                durable_event_callback_failed = True
                raise
            result["durable_events"]["armed"] = armed_digest
            write_json_atomic(action_path, result)
            fresh_consumed = self._require_internal_lease(
                fresh_lease,
                purpose="fresh_target_pointer_move",
                action_id=action_id,
                caller_token_sha256=token_hash,
                parent_authority_sha256=token_hash,
                binding=binding,
                observation=fresh,
                spec=spec,
                span=target,
                target=fresh_target,
                action_deadline=action_deadline,
                checkpoint="before pointer input",
                consume=True,
            )
            authorization["fresh_move_lease"] = self._lease_evidence(
                fresh_lease, fresh_consumed
            )

            pyautogui.moveTo(*screen_point, duration=spec.pointer_move_seconds)
            time.sleep(0.35)

            # Hover can change UI or another window can steal focus. Recapture,
            # reclassify and relocate immediately before the input batch.
            hover, hover_image = self._capture_observation_with_image(spec.screen)
            result["hover_observation_id"] = hover.observation_id
            result["hover_observation"] = self._observation_evidence(hover)
            if hover.screen != before.screen:
                raise AgentError(
                    f"screen changed during hover: {before.screen} -> {hover.screen}"
                )
            hover_matches = matching_spans(
                hover.spans,
                spec.text,
                self.contract.resolution,
                spec.region,
                contains=spec.contains,
            )
            if len(hover_matches) != 1:
                raise AgentError(
                    f"hover visible target is not unique: {len(hover_matches)}"
                )
            hover_target = hover_matches[0]
            if (
                abs(hover_target.center[0] - target.center[0])
                > spec.hover_tolerance_px
                or abs(hover_target.center[1] - target.center[1])
                > spec.hover_tolerance_px
            ):
                raise AgentError("visible target moved during hover verification")
            self.window.require_cursor_target(click_point)

            # Retain the authenticated hover pixels in memory. No caller can
            # choose this rectangle and no file needs to be read in the final
            # input critical section.
            patch_bbox = self._target_patch_bbox(hover_target.bbox)
            hover_patch = hover_image.crop(patch_bbox)
            expected_patch_sha256 = self._memory_image_sha256(hover_patch)
            result["target"]["hover"] = {
                "text": hover_target.text,
                "normalized": hover_target.normalized,
                "bbox": list(hover_target.bbox),
                "center": list(hover_target.center),
                "patch_bbox": list(patch_bbox),
                "patch_sha256": expected_patch_sha256,
            }
            hover_target_evidence = result["target"]["hover"]
            if not isinstance(hover_target_evidence, dict):
                raise AgentError("hover visible target evidence is malformed")
            hover_lease = self._issue_internal_lease(
                purpose="hover_verified_left_click_batch",
                action_id=action_id,
                caller_token_sha256=token_hash,
                parent_authority_sha256=fresh_lease.token_sha256,
                binding=binding,
                action_deadline=action_deadline,
                observation=hover,
                spec=spec,
                span=hover_target,
                target=hover_target_evidence,
            )
            authorization["hover_click_lease"] = self._lease_evidence(
                hover_lease, None
            )
            self._require_internal_lease(
                hover_lease,
                purpose="hover_verified_left_click_batch",
                action_id=action_id,
                caller_token_sha256=token_hash,
                parent_authority_sha256=fresh_lease.token_sha256,
                binding=binding,
                observation=hover,
                spec=spec,
                span=hover_target,
                target=hover_target_evidence,
                action_deadline=action_deadline,
                checkpoint="before final guards",
                consume=False,
            )

            # Everything durable is committed before entering this critical
            # section. The final capture has no OCR or artifact write. Its
            # capture guards authenticate the process/HWND and foreground on
            # both sides; the cursor guard repeats those checks and verifies
            # WindowFromPoint immediately before the SendInput batch.
            final_patch = self.window.capture_patch(patch_bbox)
            final_patch_sha256 = self._memory_image_sha256(final_patch)
            result["target"]["final_patch_sha256"] = final_patch_sha256
            if (
                not spec.allow_dynamic_pixels
                and not hmac.compare_digest(
                    final_patch_sha256, expected_patch_sha256
                )
            ):
                raise AgentError("visible target pixels changed immediately before input")
            self.window.require_cursor_target(click_point)
            hover_consumed = self._require_internal_lease(
                hover_lease,
                purpose="hover_verified_left_click_batch",
                action_id=action_id,
                caller_token_sha256=token_hash,
                parent_authority_sha256=fresh_lease.token_sha256,
                binding=binding,
                observation=hover,
                spec=spec,
                span=hover_target,
                target=hover_target_evidence,
                action_deadline=action_deadline,
                checkpoint="at input submission",
                consume=True,
            )
            authorization["hover_click_lease"] = self._lease_evidence(
                hover_lease, hover_consumed
            )
            click_submission_started = True
            accepted, last_error = submit_left_click()
            # Pixel evidence is persisted only after the input batch returns.
            # Nothing may perform file I/O between the final guard and
            # SendInput; the durable armed event remains the crash boundary.
            hover_patch_path = self.artifacts / f"{action_path.stem}.hover-patch.png"
            final_patch_path = self.artifacts / f"{action_path.stem}.final-patch.png"
            hover_patch.save(hover_patch_path)
            final_patch.save(final_patch_path)
            result["target"]["hover_patch_artifact"] = {
                "path": f"artifacts/{hover_patch_path.name}",
                "sha256": sha256_file(hover_patch_path),
                "pixel_sha256": expected_patch_sha256,
            }
            result["target"]["final_patch_artifact"] = {
                "path": f"artifacts/{final_patch_path.name}",
                "sha256": sha256_file(final_patch_path),
                "pixel_sha256": final_patch_sha256,
            }
            result["send_input"] = {
                "requested": 2,
                "accepted": accepted,
                "last_error": last_error,
            }
            if accepted != 2:
                raise AgentError(
                    f"Win32 SendInput accepted {accepted}/2 click records; "
                    f"last_error={last_error}"
                )

            postcondition_remaining = action_deadline - time.monotonic()
            if postcondition_remaining <= 0:
                raise AgentError("visible action deadline expired before postcondition")
            after = self.observe_stable(
                spec.post_screen,
                postcondition_remaining,
                stable_frames=2,
                absolute_deadline_monotonic=action_deadline,
            )
            result["result_observation_id"] = after.observation_id
            result["after_stable_observation"] = after.to_audit_evidence()
            result["binding_after"] = self.window.audit_binding()
            result["status"] = "confirmed"
            result["finished_at"] = _now()
            write_json_atomic(action_path, result)
            confirmed_receipt_written = True
            try:
                finished_digest = self._emit_durable_event(
                    {
                        "kind": "ui_action_finished",
                        "action_id": action_id,
                        "status": "confirmed",
                        "receipt_artifact": action_ref,
                        "result_frame_ids": [frame.frame_id for frame in after.frames],
                        "send_input": result["send_input"],
                        "hover_click_lease_sha256": hover_lease.token_sha256,
                    }
                )
            except Exception:
                durable_event_callback_failed = True
                raise
            result["durable_events"]["finished"] = finished_digest
            write_json_atomic(action_path, result)
            return {"action": result, "observation": after.to_policy_json()}
        except Exception as error:
            # A confirmed receipt already binds the successful SendInput and
            # two-frame postcondition.  If terminal WAL publication reports an
            # error, it may nevertheless have committed.  Preserve that
            # receipt and never emit a duplicate terminal event.
            if confirmed_receipt_written:
                if isinstance(error, AgentError):
                    raise
                raise AgentError(f"visible UI action failed: {error}") from error
            result["status"] = (
                "failed_after_possible_input"
                if input_armed
                else "rejected_before_input"
            )
            result["input_may_have_occurred"] = input_armed
            result["pointer_input_may_have_occurred"] = input_armed
            result["button_click_may_have_occurred"] = click_submission_started
            result["error"] = f"{type(error).__name__}: {error}"
            result["finished_at"] = _now()
            write_json_atomic(action_path, result)
            if planned_event_written and not durable_event_callback_failed:
                try:
                    finished_event: dict[str, object] = {
                        "kind": "ui_action_finished",
                        "action_id": action_id,
                        "status": result["status"],
                        "receipt_artifact": action_ref,
                        "input_may_have_occurred": input_armed,
                        "button_click_may_have_occurred": click_submission_started,
                    }
                    fresh_evidence = authorization.get("fresh_move_lease")
                    hover_evidence = authorization.get("hover_click_lease")
                    if isinstance(fresh_evidence, dict):
                        finished_event["fresh_move_lease_sha256"] = fresh_evidence.get(
                            "token_sha256"
                        )
                    if isinstance(hover_evidence, dict):
                        finished_event["hover_click_lease_sha256"] = hover_evidence.get(
                            "token_sha256"
                        )
                    finished_digest = self._emit_durable_event(finished_event)
                    result["durable_events"]["finished"] = finished_digest
                    write_json_atomic(action_path, result)
                except Exception as event_error:
                    result["durable_event_error"] = (
                        f"{type(event_error).__name__}: {event_error}"
                    )
                    write_json_atomic(action_path, result)
            if isinstance(error, AgentError):
                raise
            raise AgentError(f"visible UI action failed: {error}") from error
