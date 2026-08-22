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


def _prepare_left_click_batch() -> Callable[[], tuple[int, int]]:
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

    def submit() -> tuple[int, int]:
        sent = int(send_input(2, records, ctypes.sizeof(_INPUT)))
        error = ctypes.get_last_error() if sent != 2 else 0
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
    ) -> None:
        if contract.resolution != (2560, 1440):
            raise AgentError(f"unsupported UI resolution: {contract.resolution}")
        if (
            contract.game_version != expected_game_version
            or contract.language != expected_language
        ):
            raise AgentError("UI contract game version or language differs")
        require_canonical_phase_b_contract(contract, expected_contract_sha256)
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

    def _capture_observation_with_image(self) -> tuple[Observation, object]:
        self._issued.clear()
        capture_started_at = _now()
        captured_monotonic = time.monotonic()
        self._capture_sequence += 1
        image = self.window.capture()
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
    ) -> StableObservation:
        if stable_frames != 2:
            raise AgentError("Phase-B visible states require exactly two stable frames")
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
        issued = self._issued.pop(control_token, None)
        if issued is None:
            raise AgentError("unknown, stale, or already consumed control token")
        if time.monotonic() - issued.issued_monotonic > self.TOKEN_TTL_SECONDS:
            raise AgentError("visible control token expired")
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
            fresh = self._capture_observation()
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

            import pyautogui

            pyautogui.FAILSAFE = True
            submit_left_click = _prepare_left_click_batch()
            screen_point = (
                self.window.client_rect[0] + target.center[0],
                self.window.client_rect[1] + target.center[1],
            )
            result["target"]["fresh"] = {
                "text": target.text,
                "normalized": target.normalized,
                "bbox": list(target.bbox),
                "center": list(target.center),
                "screen_point": list(screen_point),
            }

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
                        "pointer_input_may_have_occurred": True,
                        "button_click_may_have_occurred": True,
                    }
                )
            except Exception:
                durable_event_callback_failed = True
                raise
            result["durable_events"]["armed"] = armed_digest
            write_json_atomic(action_path, result)
            if time.monotonic() - issued.issued_monotonic > self.TOKEN_TTL_SECONDS:
                raise AgentError("visible control token expired immediately before input")

            pyautogui.moveTo(*screen_point, duration=0.2)
            time.sleep(0.35)

            # Hover can change UI or another window can steal focus. Recapture,
            # reclassify and relocate immediately before the input batch.
            hover, hover_image = self._capture_observation_with_image()
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
            result["target"]["hover"] = {
                "text": hover_target.text,
                "normalized": hover_target.normalized,
                "bbox": list(hover_target.bbox),
                "center": list(hover_target.center),
                "patch_bbox": list(patch_bbox),
                "patch_sha256": expected_patch_sha256,
            }

            # Everything durable is committed before entering this critical
            # section. The final capture has no OCR or artifact write. Its
            # capture guards authenticate the process/HWND and foreground on
            # both sides; the cursor guard repeats those checks and verifies
            # WindowFromPoint immediately before the SendInput batch.
            final_patch = self.window.capture_patch(patch_bbox)
            final_patch_sha256 = self._memory_image_sha256(final_patch)
            result["target"]["final_patch_sha256"] = final_patch_sha256
            if not hmac.compare_digest(final_patch_sha256, expected_patch_sha256):
                raise AgentError("visible target pixels changed immediately before input")
            self.window.require_cursor_target(hover_target.center)
            if time.monotonic() - issued.issued_monotonic > self.TOKEN_TTL_SECONDS:
                raise AgentError("visible control token expired at input submission")
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

            after = self.observe_stable(
                spec.post_screen,
                timeout_seconds,
                stable_frames=2,
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
                    finished_digest = self._emit_durable_event(
                        {
                            "kind": "ui_action_finished",
                            "action_id": action_id,
                            "status": result["status"],
                            "receipt_artifact": action_ref,
                            "input_may_have_occurred": input_armed,
                            "button_click_may_have_occurred": click_submission_started,
                        }
                    )
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
