"""Portable synthetic feed regressions; no Game, SDK, desktop or process calls."""
import json
from pathlib import Path

import pytest

import decision_observation_feed as feed


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_results_from_new_prefixes_preserve_existing_feed_names(tmp_path):
    target = tmp_path / "responses"
    target.mkdir()
    old = target / "cold38-0001-1-result.json"
    old.write_bytes(b"synthetic original P08")
    for prefix in ("p11", "p12"):
        root = tmp_path / f"{prefix}-responses"
        root.mkdir()
        source = write(root / "0001-1-result.json", {"synthetic": prefix})
        output = feed.relay_compact(source, {"synthetic": prefix}, feed_root=target)
        assert output.name == f"{prefix}-responses-0001-1-result.json"
        assert json.loads(output.read_text(encoding="utf-8"))["source_ref"] == str(source.resolve())
        with pytest.raises(FileExistsError):
            feed.relay_compact(source, {"synthetic": "duplicate"}, feed_root=target)
    assert old.read_bytes() == b"synthetic original P08"


def test_callback_uses_explicit_prefix_context_and_preserves_old_plan(tmp_path):
    target, output = tmp_path / "responses", tmp_path / "p11-responses"
    target.mkdir()
    output.mkdir()
    old = target / "0005-0-plan.json"
    old.write_bytes(b"synthetic original P08 plan")
    write(tmp_path / "CURRENT-REQUEST.json", {"sequence": 139, "tool": "stale"})
    context = write(tmp_path / "CURRENT-REQUEST-P11.json", {"sequence": 5, "tool": "ck3_auto_turn"})
    launch = write(tmp_path / "launch.json", {"pid": 10, "creation_date": "synthetic"})
    arguments = dict(current_request_path=context, game_launch_receipt=launch,
                     response_root=output, feed_root=target)
    observation = {"plan": {"selected_step": "synthetic-option", "reason": "actual synthetic plan"},
                   "selected_step": "synthetic-option"}
    feed.publish_before_submit(observation, **arguments)
    row = json.loads((output / "0005-0-plan.json").read_text(encoding="utf-8"))
    assert row["request"]["parent_sequence"] == 5
    assert row["result"]["structured_content"]["status"] == "planned"
    assert (target / "p11-responses-0005-0-plan.json").is_file()
    assert old.read_bytes() == b"synthetic original P08 plan"
    with pytest.raises(FileExistsError):
        feed.publish_before_submit(observation, **arguments)


def test_atomic_collision_keeps_competing_original(monkeypatch, tmp_path):
    source_root, target = tmp_path / "p11-responses", tmp_path / "responses"
    source_root.mkdir()
    target.mkdir()
    source = write(source_root / "0001-1-result.json", {"synthetic": True})
    link = feed.os.link
    def competing_publish(temporary, destination):
        destination.write_bytes(b"synthetic competing publisher")
        link(temporary, destination)
    monkeypatch.setattr(feed.os, "link", competing_publish)
    with pytest.raises(FileExistsError):
        feed.relay_compact(source, {"synthetic": True}, feed_root=target)
    assert (target / "p11-responses-0001-1-result.json").read_bytes() == b"synthetic competing publisher"
    assert not list(target.glob("*.pending"))


def test_rejected_context_writes_no_plan_and_errors_claim_no_outcome(tmp_path):
    target, output = tmp_path / "responses", tmp_path / "p11-responses"
    target.mkdir()
    output.mkdir()
    context = write(tmp_path / "CURRENT-REQUEST-P11.json", {"sequence": 1, "tool": "semantic"})
    launch = write(tmp_path / "launch.json", {"pid": 10, "creation_date": "synthetic"})
    with pytest.raises(ValueError):
        feed.publish_before_submit({"plan": {"selected_step": "synthetic"}, "selected_step": "synthetic"},
            current_request_path=context, game_launch_receipt=launch, response_root=output, feed_root=target)
    assert not list(output.iterdir()) and not list(target.iterdir())
    projected = feed.error_projection({"client_error": "synthetic unknown outcome"})
    assert projected["result"]["is_error"] is True
    assert projected["result"]["structured_content"]["outcome_verified"] is False
    assert projected["result"]["structured_content"]["original_request_replayed"] is False
