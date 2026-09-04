#!/usr/bin/env python3
"""Visible desktop adapter for the exact-build CK3 Switch Character UI."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Final, Mapping

from zg361_phase2_cross_cycle_endgame_action_cell import (
    PRODUCTION_SUBJECT_TRANSITION_MODE,
)
from zg361_phase2_cross_cycle_endgame_switch_ui import _fail


class DesktopSwitchCharacterUiDriver:
    """Reuse the acceptance runner's foreground, OCR and click primitives."""

    _FULL_SCREEN: Final = (0.0, 0.0, 1.0, 1.0)
    _SURFACE_TOKENS: Final = {
        "pause_switch": ("Switch Character", "切换角色"),
        "any_ruler": ("Play as any Ruler", "任一统治者"),
        "select_on_map": (
            "Choose a Character on the Map",
            "选择地图上的一个角色",
        ),
    }

    def __init__(
        self,
        desktop: object,
        *,
        timeout_seconds: float = 20.0,
        poll_interval_seconds: float = 0.25,
    ) -> None:
        if timeout_seconds <= 0 or poll_interval_seconds < 0:
            raise ValueError("desktop UI wait bounds are invalid")
        self.desktop = desktop
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    def _foreground(self, expected_pid: int) -> tuple[int, int]:
        if self.desktop.focus_ck3() is not True:
            _fail("ck3_foreground_unavailable", expected_ck3_pid=expected_pid)
        hwnd = self.desktop.win32gui.GetForegroundWindow()
        _thread, pid = self.desktop.win32process.GetWindowThreadProcessId(hwnd)
        if pid != expected_pid:
            _fail(
                "ck3_foreground_pid_mismatch",
                expected_ck3_pid=expected_pid,
                foreground_pid=pid,
                foreground_title=self.desktop.win32gui.GetWindowText(hwnd),
            )
        return int(hwnd), int(pid)

    @staticmethod
    def _matching_text(rows: object, alternatives: tuple[str, ...]) -> str | None:
        if not isinstance(rows, list):
            return None
        folded = tuple(value.casefold() for value in alternatives)
        for row in rows:
            text = row.get("text") if isinstance(row, Mapping) else None
            if not isinstance(text, str):
                continue
            observed = text.casefold()
            if any(token in observed for token in folded):
                return text
        return None

    def _observe_surface(
        self,
        surface: str,
        *,
        expected_pid: int,
        evidence_directory: Path,
    ) -> dict[str, object]:
        alternatives = self._SURFACE_TOKENS[surface]
        deadline = time.monotonic() + self.timeout_seconds
        previous: str | None = None
        stable = 0
        frames = 0
        while time.monotonic() < deadline:
            _hwnd, foreground_pid = self._foreground(expected_pid)
            image = self.desktop.ImageGrab.grab()
            rows = self.desktop.ocr_box_results(image, self._FULL_SCREEN)
            matched = self._matching_text(rows, alternatives)
            frames += 1
            if matched is not None and matched == previous:
                stable += 1
            elif matched is not None:
                stable = 1
            else:
                stable = 0
            previous = matched
            if stable >= 2:
                path = evidence_directory / f"ui-{surface}.png"
                image.save(path)
                return {
                    "surface": surface,
                    "matched_text": matched,
                    "expected_tokens": list(alternatives),
                    "stable_observations": stable,
                    "frames": frames,
                    "foreground_pid": foreground_pid,
                    "screenshot": str(path.resolve()),
                }
            if self.poll_interval_seconds:
                time.sleep(self.poll_interval_seconds)
        _fail(
            "switch_ui_surface_not_observed",
            surface=surface,
            expected_tokens=list(alternatives),
            expected_ck3_pid=expected_pid,
            frames=frames,
        )

    def _wait_surface_absent(
        self,
        surface: str,
        *,
        expected_pid: int,
        evidence_directory: Path,
    ) -> dict[str, object]:
        alternatives = self._SURFACE_TOKENS[surface]
        deadline = time.monotonic() + self.timeout_seconds
        stable = 0
        frames = 0
        while time.monotonic() < deadline:
            self._foreground(expected_pid)
            image = self.desktop.ImageGrab.grab()
            rows = self.desktop.ocr_box_results(image, self._FULL_SCREEN)
            matched = self._matching_text(rows, alternatives)
            frames += 1
            stable = stable + 1 if matched is None else 0
            if stable >= 2:
                path = evidence_directory / f"ui-{surface}-dismissed.png"
                image.save(path)
                return {
                    "surface": surface,
                    "absent": True,
                    "stable_observations": stable,
                    "frames": frames,
                    "screenshot": str(path.resolve()),
                }
            if self.poll_interval_seconds:
                time.sleep(self.poll_interval_seconds)
        _fail(
            "switch_ui_surface_did_not_change",
            surface=surface,
            expected_ck3_pid=expected_pid,
            frames=frames,
        )

    def _press(self, key: str, *, expected_pid: int) -> dict[str, object]:
        _hwnd, foreground_pid = self._foreground(expected_pid)
        self.desktop.pyautogui.press(key)
        return {
            "submitted": True,
            "key": key.upper(),
            "foreground_pid": foreground_pid,
        }

    def _click_client_center(
        self,
        *,
        expected_pid: int,
    ) -> dict[str, object]:
        hwnd, foreground_pid = self._foreground(expected_pid)
        left, top, right, bottom = self.desktop.win32gui.GetClientRect(hwnd)
        origin = self.desktop.win32gui.ClientToScreen(hwnd, (left, top))
        opposite = self.desktop.win32gui.ClientToScreen(hwnd, (right, bottom))
        width = int(opposite[0]) - int(origin[0])
        height = int(opposite[1]) - int(origin[1])
        if width <= 0 or height <= 0:
            _fail(
                "ck3_client_rect_invalid",
                hwnd=hwnd,
                origin=list(origin),
                opposite=list(opposite),
            )
        center = (
            int(origin[0]) + width // 2,
            int(origin[1]) + height // 2,
        )
        self.desktop.deliberate_click(
            center,
            "native title-bounds target at current CK3 client centre",
        )
        return {
            "submitted": True,
            "foreground_pid": foreground_pid,
            "client_rect_screen": [
                int(origin[0]),
                int(origin[1]),
                int(opposite[0]),
                int(opposite[1]),
            ],
            "derived_client_center": list(center),
            "coordinate_source": (
                "current_ck3_client_rect_center_after_exact_native_"
                "title_bounds_navigation"
            ),
            "caller_coordinate_used": False,
        }

    def switch_to_centered_title(
        self,
        *,
        expected_ck3_pid: int,
        evidence_directory: Path,
    ) -> Mapping[str, object]:
        evidence_directory.mkdir(parents=True, exist_ok=True)
        actions: list[dict[str, object]] = []
        actions.append(self._press("escape", expected_pid=expected_ck3_pid))
        pause = self._observe_surface(
            "pause_switch",
            expected_pid=expected_ck3_pid,
            evidence_directory=evidence_directory,
        )
        actions.append(self._press("3", expected_pid=expected_ck3_pid))
        any_ruler = self._observe_surface(
            "any_ruler",
            expected_pid=expected_ck3_pid,
            evidence_directory=evidence_directory,
        )
        actions.append(self._press("tab", expected_pid=expected_ck3_pid))
        select_on_map = self._observe_surface(
            "select_on_map",
            expected_pid=expected_ck3_pid,
            evidence_directory=evidence_directory,
        )
        click = self._click_client_center(expected_pid=expected_ck3_pid)
        selected = self._wait_surface_absent(
            "select_on_map",
            expected_pid=expected_ck3_pid,
            evidence_directory=evidence_directory,
        )
        actions.append(self._press("enter", expected_pid=expected_ck3_pid))
        return {
            "schema_version": 1,
            "kind": "zg361_phase2_official_switch_character_ui_submission_v1",
            "result": "GREEN",
            "transition_mode": PRODUCTION_SUBJECT_TRANSITION_MODE,
            "expected_ck3_pid": expected_ck3_pid,
            "official_ui_switch_submitted": True,
            "native_title_center_click": True,
            "caller_coordinate_used": False,
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
            "business_postcondition_observed": False,
            "action_ack_only": True,
            "semantic_shortcuts": {
                "pause_menu": "ESCAPE",
                "switch_character": "3",
                "any_ruler": "TAB",
                "start_selected_character": "RETURN",
            },
            "surface_observations": [pause, any_ruler, select_on_map, selected],
            "title_center_click": click,
            "key_submissions": actions,
        }


__all__ = ["DesktopSwitchCharacterUiDriver"]
