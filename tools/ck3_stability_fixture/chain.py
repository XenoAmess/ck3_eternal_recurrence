"""Offline accounting for closed normal-save continuations, never stability GREEN."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
import zipfile

from .evidence import checked_file, load_json, require, sha256

PACKAGE = Path(__file__).resolve().parents[2] / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(PACKAGE))
from xar_autoplayer.ck3_save_artifacts import inspect_ck3_save_artifact_v1, require_seedable_ck3_save_v1


def game_date(value: str) -> tuple[int, int, int]:
    require(bool(re.fullmatch(r"[1-9]\d*\.[1-9]\d?\.[1-9]\d?", value)), "unsupported saved date")
    year, month, day = map(int, value.split("."))
    require(1 <= month <= 12 and 1 <= day <= 31, "saved date out of range")
    return year, month, day


def closed_save(reference: dict) -> dict:
    path = checked_file(reference)
    artifact = inspect_ck3_save_artifact_v1(path, profile_dir=path.parent)
    require_seedable_ck3_save_v1(artifact)
    require(artifact["format"] == "zip-ck3", "closed-chain scanner currently supports text ZIP saves only")
    with zipfile.ZipFile(path) as archive:
        require(len([m for m in archive.infolist() if m.filename == "gamestate"]) == 1,
                "unique gamestate member required")
        raw = archive.read("gamestate")
    text = raw.decode("utf-8", errors="strict")
    # Inspect explicit top-level player records and metadata. Do not search a
    # character portrait nested in history and call it the current player.
    dates = re.findall(r"(?m)^\tmeta_date=(\d+\.\d+\.\d+)\r?$", text)
    versions = re.findall(r'(?m)^\tversion="([^"\r\n]+)"\r?$', text)
    count = re.findall(r"(?m)^\tmeta_number_of_players=(\d+)\r?$", text)
    played = re.findall(r"(?m)^played_character=\{\r?\n(.*?)^\}\r?$", text, re.DOTALL)
    current = re.findall(r"(?m)^currently_played_characters=\{([^}]*)\}", text)
    require(len(dates) == len(versions) == len(count) == len(played) == len(current) == 1,
            "closed save metadata/player records missing or ambiguous")
    require(count == ["1"], "single played-character test required")
    actor = re.findall(r"(?m)^\tcharacter=(\d+)\r?$", played[0])
    player = re.findall(r"(?m)^\tplayer=(\d+)\r?$", played[0])
    require(len(actor) == 1 and player == ["1"] and current[0].split() == actor and int(actor[0]) > 0,
            "saved played/current character binding differs")
    game_date(dates[0])
    require(sha256(path) == reference["sha256"].lower(), "closed save changed during inspection")
    return {"file": artifact, "gamestate_sha256": hashlib.sha256(raw).hexdigest(),
            "date": dates[0], "version": versions[0], "actor": int(actor[0]), "player": 1}


def verify_chain(manifest: dict) -> dict:
    require(manifest["schema"] == "ck3.stability-save-chain.v1", "unsupported chain schema")
    require(manifest.get("closed_only") is True, "chain scanner requires closed attempts; never inspect a live save")
    start = game_date(manifest["start_date"])
    years = manifest.get("target_years", 100)
    require(type(years) is int and years > 0, "positive target years required")
    target = (start[0] + years, start[1], start[2])
    previous, previous_hash, seen, epochs = start, None, set(), []
    for epoch in manifest["epochs"]:
        run_id = epoch["run_id"]
        require(run_id not in seen, "duplicate epoch ID")
        seen.add(run_id)
        retired = load_json(checked_file(epoch["retirement"]))
        require(retired["schema"] == "ck3.stability-normal-retirement.v1" and retired["run_id"] == run_id,
                "retirement belongs to another epoch")
        for flag in ("normal_save_then_exit", "process_inventory_empty", "keeper_stopped", "screen_released"):
            require(retired.get(flag) is True, f"retirement lacks actual {flag}")
        require(type(retired.get("exit_code")) is int and retired["exit_code"] == 0
                and type(retired.get("pid")) is int and retired["pid"] > 0,
                "normal successful process retirement required")
        require(retired.get("save_sha256") == epoch["end"]["sha256"], "retired save differs")
        require(retired.get("evidence"), "retirement needs preserved UI/process/lease evidence")
        for reference in retired["evidence"]:
            checked_file(reference)
        before, after = closed_save(epoch["load"]), closed_save(epoch["end"])
        require(game_date(before["date"]) == previous, "continuation start date differs")
        if previous_hash is not None:
            require(epoch["load"]["sha256"] == previous_hash, "normal-save parent hash differs")
        require(game_date(after["date"]) >= previous, "saved date moved backward")
        require(before["version"] == after["version"] == manifest["game_version"], "exact game version differs")
        require(epoch.get("natural_progress_evidence"), "normal-save dates alone do not prove natural gameplay")
        for reference in epoch["natural_progress_evidence"]:
            checked_file(reference)
        if before["actor"] != after["actor"]:
            require(epoch.get("natural_succession_evidence"), "changed actor requires actual natural succession evidence")
            for reference in epoch["natural_succession_evidence"]:
                checked_file(reference)
        epochs.append({"run_id": run_id, "load": before, "end": after,
                       "retirement_sha256": epoch["retirement"]["sha256"],
                       "natural_progress_evidence": epoch["natural_progress_evidence"]})
        previous, previous_hash = game_date(after["date"]), epoch["end"]["sha256"]
    reached = bool(epochs) and previous >= target
    return {"schema": "ck3.stability-save-chain-report.v1", "status":
            "CLOSED_CHAIN_TARGET_REACHED" if reached else "CLOSED_CHAIN_INCOMPLETE",
            "start_date": manifest["start_date"], "target_date": ".".join(map(str, target)),
            "closed_end_date": ".".join(map(str, previous)), "epochs": epochs,
            "gameplay_evidence_review": "REQUIRED", "stability_result": "NOT_GRADED",
            "boundary": "CRC/date/player/hash continuity verified; referenced gameplay evidence requires operator review"}
