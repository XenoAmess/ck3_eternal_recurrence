"""Root-owned entry for one existing public CK3 host and one client-window take.

The actor neither initializes the scenario nor advances a day nor closes CK3.
Every UI control has an attempt-unique public prefix and CaseClient output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import window_take as film


def selection_for(spec):
    from ck3_mod_acceptance import Selection
    selected = Selection(spec.runtime, spec.products, spec.product_key,
                         spec.case_key, spec.context, spec.prepared)
    film.need(selected.run_dir.resolve() == spec.live and
              selected.state_dir.resolve() == spec.state_dir,
              "selected public run/state differs from actual take")
    return selected


def ui_prepare(spec, *, select):
    """One legal native Army selection, or read-only query of current pane."""
    from ck3_mod_acceptance_client import CaseClient
    from ck3_mod_acceptance_full_army import FullArmyResultClient
    film.need(spec.content_kind == "army-supply" and not spec.ui_output.exists(),
              "fresh Army UI attempt/output required")
    selected = selection_for(spec)
    client = CaseClient(selected, output=spec.ui_output)
    outcome = {"machine_id": spec.machine_id, "run_id": spec.live.name,
               "army_id": spec.army_id, "selection_submissions": 0,
               "ui_visible_verified": False, "video_or_supply_value_approved": False}
    try:
        client.read_report()
        client.guard(reserve=spec.reserve())
        client.retain_process()
        context = selected.adapter_context(client.output)
        wrapped = FullArmyResultClient(client, prefix=spec.ui_query_prefix)
        first = wrapped.snapshot()
        actor = context["saved_campaign"]["player_id"]
        matches = [a for a in first["player_armies"] if a.get("army_id") == spec.army_id and
                   a.get("owner_character_id") == actor and a.get("controllable") is True]
        film.need(len(matches) == 1 and first["map_ready"] is True and first["paused"] is True,
                  "chosen Army ID is not a current controllable owned army")
        outcome.update(actor_id=actor, before_date_raw=first["date_raw"])
        if select:
            claim = film.write_once(client.output / "army-select.once-claim.json", {
                "machine_id": spec.machine_id, "run_id": spec.live.name,
                "army_id": spec.army_id, "date_raw": first["date_raw"],
                "status": "selection_claimed_result_unknown_no_replay"})
            name = "select-army-once"
            rows = wrapped.execute_plan([{"id": name, "tool": "ck3_select_army_ui_v1",
                "args": {"subject_army_id": spec.army_id,
                         "expected_revision": first["revision"]},
                "fresh_revision": False}], name)
            outcome["selection_claim"] = claim
            outcome["selection_submissions"] = 1
            outcome["selection_ack"] = rows[0]
            film.need(rows[0].get("ok") is True and not rows[0].get("error") and
                      rows[0]["result"].get("accepted") is True,
                      "native Army select result unknown/denied; never replay")
        for index in range(1, 6 if select else 2):
            current = wrapped.snapshot()
            film.need(current["date_raw"] == first["date_raw"] and
                      current["played_character"]["character_id"] == actor,
                      "Army window readback crossed date or player")
            name = "independent-army-window-" + str(index)
            row = wrapped.execute_plan([{"id": name,
                "tool": "ck3_query_ingame_ui_window_v1",
                "args": {"window_kind": "army", "expected_revision": current["revision"]},
                "fresh_revision": False}], name)[0]
            film.need(row.get("ok") is True and not row.get("error"),
                      "independent native Army window readback failed")
            ui = row["result"]
            outcome["last_independent_window"] = ui
            if ui.get("effective_visible") is True:
                film.need(ui.get("window_kind") == "army" and
                          ui.get("subject_id_available") is True and
                          ui.get("current_subject_id") == spec.army_id and
                          ui.get("owner_character_id_available") is True and
                          ui.get("owner_character_id") == actor and
                          ui.get("verification_pending") is False and
                          ui.get("date_raw") == first["date_raw"] and
                          ui.get("paused") is True and
                          ui.get("tree", {}).get("truncated") is False,
                          "visible ArmyWindow subject/date/owner differs")
                outcome["ui_visible_verified"] = True
                break
            time.sleep(0.25)
        outcome["status"] = "ARMY_WINDOW_VISIBLE_ROOT_FRAME_PENDING" if outcome["ui_visible_verified"] else \
                            "ARMY_WINDOW_NOT_VISIBLE_NO_START"
        client.checkpoint("army-window-setup-result", outcome)
        return outcome
    finally:
        client.close_handle()


def run_take(spec, reviewed_frame):
    from ck3_mod_acceptance_client import CaseClient
    film.need(not spec.output.exists(), "fresh film CaseClient output required")
    selected = selection_for(spec)
    client = CaseClient(selected, output=spec.output)
    result = {"machine_id": spec.machine_id, "run_id": spec.live.name,
              "status": "ENTERED", "new_game_process": False,
              "game_actions_submitted": 0, "business_or_video_approved": False}
    take = None
    primary = None
    try:
        client.read_report()
        client.guard(reserve=spec.reserve())
        client.retain_process()
        context = selected.adapter_context(client.output)
        take = film.start(spec, context, client, reviewed_frame=reviewed_frame)
        result["actual_canonical_recorder_started"] = True
        closing = take
        take = None
        result["recording_terminal"] = film.stop(closing)
        terminal = film.read(result["recording_terminal"]["path"])
        result["status"] = "WINDOW_TAKE_TERMINAL_PENDING_MEDIA_REVIEW" if (
            terminal.get("state") == "NORMAL_TREE_EMPTY" and
            terminal.get("hard_terminal_wall_seconds_met") is True and
            terminal.get("recorder_finish_error") is None and
            terminal.get("secondary_cleanup_error") is None) else "WINDOW_TAKE_RED_RETAINED_NO_REPLAY"
    except BaseException as error:
        primary = error
        result["status"] = "WINDOW_TAKE_RED_RETAINED_NO_REPLAY"
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if take is not None:
            try:
                result["recording_terminal"] = film.stop(take, primary_error=primary)
            except BaseException as error:
                result["recording_cleanup_error"] = repr(error)
        try:
            client.checkpoint("window-take-actor-result", result)
        finally:
            client.close_handle()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("source-check", "ui-prepare", "prepare-frame", "review", "film"))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--reviewed-frame", type=Path)
    parser.add_argument("--select-army-once", action="store_true")
    parser.add_argument("--root-reviewed-no-hover", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.operation == "source-check":
        film.need(args.repo_root is not None, "explicit repository root required for source-only check")
        film.bind_repo(args.repo_root)
        import capture_recorder, recorder_job
        from ck3_live_run_id import current_machine_id
        print(json.dumps({"machine_id": current_machine_id(), "observed_at_utc": film.utc(),
            "module": film.pin(film.__file__),
            "canonical_recorder": film.pin(capture_recorder.__file__),
            "canonical_recorder_job": film.pin(recorder_job.__file__),
            "SDK_calls": 0, "desktop_calls": 0}, ensure_ascii=False))
        return 0
    film.need(args.config is not None, "exact actual take config required")
    spec = film.TakeSpec(args.config)
    if args.operation == "ui-prepare":
        film.need(args.execute, "one native UI route requires explicit Root execute")
        result = ui_prepare(spec, select=args.select_army_once)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ui_visible_verified"] else 2
    if args.operation == "prepare-frame":
        film.need(args.execute and args.output is not None, "Root original frame output required")
        print(json.dumps(film.prepare_only(spec, args.output), ensure_ascii=False))
        return 0
    if args.operation == "review":
        film.need(args.execute and args.capture is not None, "Root direct original frame review required")
        print(json.dumps(film.review(spec, args.capture,
            content=spec.content_kind, no_hover=args.root_reviewed_no_hover), ensure_ascii=False))
        return 0
    film.need(args.execute and args.reviewed_frame is not None, "Root exact review receipt required")
    result = run_take(spec, args.reviewed_frame)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "WINDOW_TAKE_TERMINAL_PENDING_MEDIA_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
