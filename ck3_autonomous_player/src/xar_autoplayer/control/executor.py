"""Fresh-frame, opaque-token control with positive postconditions."""

from __future__ import annotations

from collections.abc import Callable
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import time
import uuid

from ..environment import sha256_file, write_json_atomic
from ..errors import AgentError
from ..runtime import append_event
from ..vision.classifier import ControlSpec, UiContract
from ..vision.model import Observation, OcrSpan, VisibleControl
from ..vision.ocr import matching_spans, ocr_spans
from ..vision.window import BoundGameWindow


_INPUT_MOUSE = 0
_MOUSEEVENTF_LEFTDOWN = 0x0002
_MOUSEEVENTF_LEFTUP = 0x0004


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    )


class _INPUT_VALUE(ctypes.Union):
    _fields_ = (("mi", _MOUSEINPUT),)


class _INPUT(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = (("type", wintypes.DWORD), ("value", _INPUT_VALUE))


def _prepare_left_click_batch() -> Callable[[], None]:
    """Prepare one LEFTDOWN+LEFTUP SendInput call outside the final guard."""
    records = (_INPUT * 2)()
    records[0].type = _INPUT_MOUSE
    records[0].mi.dwFlags = _MOUSEEVENTF_LEFTDOWN
    records[1].type = _INPUT_MOUSE
    records[1].mi.dwFlags = _MOUSEEVENTF_LEFTUP

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send_input = user32.SendInput
    send_input.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
    send_input.restype = wintypes.UINT

    def submit() -> None:
        sent = int(send_input(2, records, ctypes.sizeof(_INPUT)))
        if sent != 2:
            error = ctypes.get_last_error()
            raise AgentError(
                f"Win32 SendInput accepted {sent}/2 click records; last_error={error}"
            )

    return submit


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class _IssuedControl:
    observation: Observation
    spec: ControlSpec
    span: OcrSpan
    issued_monotonic: float


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
    ) -> None:
        if contract.resolution != (2560, 1440):
            raise AgentError(f"unsupported UI resolution: {contract.resolution}")
        if (
            contract.game_version != expected_game_version
            or contract.language != expected_language
        ):
            raise AgentError("UI contract game version or language differs")
        registered = frozenset(item.control_id for item in contract.controls)
        if not registered <= self.PHASE_B_ALLOWED_CONTROLS:
            raise AgentError(
                f"UI contract exceeds the Phase B action allowlist: {sorted(registered)!r}"
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
        self.events = self.artifacts.parent / "ui-events.jsonl"
        self._secret = secrets.token_bytes(32)
        self._session_nonce = secrets.token_hex(16)
        self._issued: dict[str, _IssuedControl] = {}
        self._sequence = 0

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

    def _capture_observation_with_image(self) -> tuple[Observation, object]:
        self._issued.clear()
        capture_started_at = _now()
        image = self.window.capture()
        spans = ocr_spans(image)
        screen, confidence, reasons, anchors = self.contract.classify(spans)
        observation_id = uuid.uuid4().hex
        frame_id = uuid.uuid4().hex
        stem = self._artifact_stem("frame")
        screenshot = self.artifacts / f"{stem}.png"
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
            screenshot=str(screenshot),
            screenshot_sha256=sha256_file(screenshot),
            spans=spans,
            anchors=anchors,
            controls=tuple(controls),
            confidence=confidence,
            unknown_reasons=reasons,
        )
        for control in controls:
            spec = self.contract.control(control.control_id)
            span = next(item for item in spans if item.bbox == control.bbox)
            self._issued[control.token] = _IssuedControl(
                observation=observation,
                spec=spec,
                span=span,
                issued_monotonic=time.monotonic(),
            )
        write_json_atomic(
            self.artifacts / f"{stem}.observation.json",
            {
                **observation.to_audit_json(),
                "private_audit": {
                    **observation.to_audit_json()["private_audit"],
                    "capture_started_at": capture_started_at,
                },
            },
        )
        return observation, image

    def _capture_observation(self) -> Observation:
        observation, _image = self._capture_observation_with_image()
        return observation

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
    ) -> Observation:
        deadline = time.monotonic() + timeout_seconds
        prior: Observation | None = None
        hits = 0
        last: Observation | None = None
        while time.monotonic() < deadline:
            last = self._capture_observation()
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
                    for control in last.controls:
                        old = prior_controls.get(control.control_id)
                        if old is None or abs(old[0] - control.center[0]) > 15 or abs(
                            old[1] - control.center[1]
                        ) > 15:
                            stable = False
                            break
                hits = hits + 1 if stable else 1
                prior = last
                if hits >= stable_frames:
                    return last
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
        issued = self._issued.pop(control_token, None)
        if issued is None:
            raise AgentError("unknown, stale, or already consumed control token")
        if time.monotonic() - issued.issued_monotonic > self.TOKEN_TTL_SECONDS:
            raise AgentError("visible control token expired")
        before, spec, old_span = (
            issued.observation,
            issued.spec,
            issued.span,
        )
        action_id = uuid.uuid4().hex
        action_path = self.artifacts / f"{self._artifact_stem('action')}.json"
        token_hash = hashlib.sha256(control_token.encode("ascii")).hexdigest()
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
        }
        write_json_atomic(action_path, result)
        append_event(
            self.events,
            {
                "kind": "ui_action_planned",
                "action_id": action_id,
                "control_id": spec.control_id,
                "token_sha256": token_hash,
            },
        )
        input_may_have_occurred = False
        try:
            self.window.require_foreground()
            fresh = self._capture_observation()
            result["fresh_observation_id"] = fresh.observation_id
            if fresh.screen != before.screen:
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

            import pyautogui

            pyautogui.FAILSAFE = True
            submit_left_click = _prepare_left_click_batch()
            screen_point = (
                self.window.client_rect[0] + target.center[0],
                self.window.client_rect[1] + target.center[1],
            )
            pyautogui.moveTo(*screen_point, duration=0.2)
            time.sleep(0.35)

            # Hover can change UI or another window can steal focus. Recapture,
            # reclassify and relocate immediately before the input batch.
            hover, hover_image = self._capture_observation_with_image()
            result["hover_observation_id"] = hover.observation_id
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
            if abs(hover_target.center[0] - target.center[0]) > 3 or abs(
                hover_target.center[1] - target.center[1]
            ) > 3:
                raise AgentError("visible target moved during hover verification")
            self.window.require_cursor_target(hover_target.center)

            # Retain the authenticated hover pixels in memory. No caller can
            # choose this rectangle and no file needs to be read in the final
            # input critical section.
            patch_bbox = self._target_patch_bbox(hover_target.bbox)
            hover_patch = hover_image.crop(patch_bbox)
            expected_patch_sha256 = self._memory_image_sha256(hover_patch)

            result["status"] = "input_attempting"
            result["input_may_have_occurred"] = True
            result["input_attempted_at"] = _now()
            write_json_atomic(action_path, result)
            append_event(
                self.events,
                {"kind": "ui_input_attempting", "action_id": action_id},
            )

            # The receipt above is intentionally durable before the possible
            # input window. Re-check token freshness after that disk I/O so a
            # slow filesystem cannot turn an expired observation capability
            # into a click. From here to SendInput there is no OCR, sleep, or
            # artifact write.
            if time.monotonic() - issued.issued_monotonic > self.TOKEN_TTL_SECONDS:
                raise AgentError("visible control token expired immediately before input")

            # Everything durable is committed before entering this critical
            # section. The final capture has no OCR or artifact write. Its
            # capture guards authenticate the process/HWND and foreground on
            # both sides; the cursor guard repeats those checks and verifies
            # WindowFromPoint immediately before the SendInput batch.
            final_patch = self.window.capture_patch(patch_bbox)
            if not hmac.compare_digest(
                self._memory_image_sha256(final_patch), expected_patch_sha256
            ):
                raise AgentError("visible target pixels changed immediately before input")
            self.window.require_cursor_target(hover_target.center)
            if time.monotonic() - issued.issued_monotonic > self.TOKEN_TTL_SECONDS:
                raise AgentError("visible control token expired at input submission")
            input_may_have_occurred = True
            submit_left_click()

            after = self.observe_stable(
                spec.post_screen,
                timeout_seconds,
                stable_frames=2,
            )
            result["result_observation_id"] = after.observation_id
            result["status"] = "confirmed"
            result["finished_at"] = _now()
            write_json_atomic(action_path, result)
            append_event(
                self.events,
                {"kind": "ui_action_finished", "action_id": action_id, "status": "confirmed"},
            )
            return {"action": result, "observation": after.to_policy_json()}
        except Exception as error:
            result["status"] = (
                "failed_after_possible_input"
                if input_may_have_occurred
                else "rejected_before_input"
            )
            result["input_may_have_occurred"] = input_may_have_occurred
            result["error"] = f"{type(error).__name__}: {error}"
            result["finished_at"] = _now()
            write_json_atomic(action_path, result)
            append_event(
                self.events,
                {
                    "kind": "ui_action_finished",
                    "action_id": action_id,
                    "status": result["status"],
                },
            )
            if isinstance(error, AgentError):
                raise
            raise AgentError(f"visible UI action failed: {error}") from error
