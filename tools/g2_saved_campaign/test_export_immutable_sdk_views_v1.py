"""Small actual-NTFS fixture; no production source view, Game or SAVE access."""
from argparse import Namespace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

import export_immutable_sdk_views_v1 as exporter


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args]).decode().strip()


@pytest.fixture(scope="module")
def frozen(tmp_path_factory):
    if os.name != "nt":
        pytest.skip("qualification requires actual Windows NTFS")
    root = tmp_path_factory.mktemp("immutable-ntfs")
    repo = root / "repo"
    repo.mkdir()
    template = root / "empty-template"
    template.mkdir()
    git(repo, "init", "--quiet", "--template=" + str(template))
    git(repo, "config", "user.name", "Source fixture")
    git(repo, "config", "user.email", "source-fixture@example.invalid")
    prefix = repo / "ck3_autonomous_player/src/xar_autoplayer"
    write(prefix / "same.py", b"SAME = 1\n")
    write(prefix / "change.py", b"VERSION = 1\n")
    git(repo, "add", ".")
    git(repo, "commit", "--quiet", "-m", "old source")
    old = git(repo, "rev-parse", "HEAD")
    # These are fixture working-tree leaves, never a frozen or hardlinked input.
    (prefix / "change.py").write_bytes(b"VERSION = 2\n")
    write(prefix / "new.py", b"NEW = True\n")
    git(repo, "add", ".")
    git(repo, "commit", "--quiet", "-m", "new source")
    new = git(repo, "rev-parse", "HEAD")
    base = root / "frozen"
    rows = []
    for relative, item in exporter.tree(repo, old).items():
        raw = subprocess.check_output(["git", "-C", str(repo), "cat-file", "blob", item["git_blob_sha1"]])
        sha = write(base / relative, raw)
        rows.append(dict(relative=relative, bytes=len(raw), sha256=sha, git_blob_sha1=item["git_blob_sha1"]))
    machine = exporter.current_machine_id()
    native = root / "NATIVE.json"
    native_sha = write(native, dict(machine_id=machine, native_build_label="fixture-only", native_dll_sha256="a" * 64))
    manifest = root / "BASE-FREEZE.json"
    manifest_sha = write(manifest, dict(schema="root.ck3.final-sdk-source-freeze/v1",
        status="FINAL_SOURCE_FROZEN", machine_id=machine, source_root=str(base.resolve()),
        files=rows, source_file_count=len(rows), source_bytes=sum(x["bytes"] for x in rows),
        business_source_commit=old, git_head=new, native_build_label="fixture-only", native_dll_sha256="a" * 64))
    identity = exporter.ntfs_identity(base / "xar_autoplayer/same.py")
    require_ntfs = identity["filesystem"].upper() == "NTFS"
    assert require_ntfs
    return dict(root=root, repo=repo, old=old, new=new, base=base, manifest=manifest,
                manifest_sha=manifest_sha, native=native, native_sha=native_sha, machine=machine)


def arguments(frozen, label, **card_changes):
    root = frozen["root"]
    source, reference, output = (root / (label + x) for x in ("-src", "-ref", "-out"))
    card = dict(schema=exporter.CARD_SCHEMA, status="ADMITTED", machine_id=frozen["machine"],
        review_at_utc=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        business_source_commit=frozen["new"], runtime_source_commit=frozen["new"],
        base_freeze_sha256=frozen["manifest_sha"], native_pin_sha256=frozen["native_sha"],
        sdk_generation="P37-FIXTURE", base_source_root=str(frozen["base"].resolve()),
        source_destination=str(source.resolve()), reference_destination=str(reference.resolve()),
        output_root=str(output.resolve()), approved_output_roots=[str(root.resolve())],
        metadata_reserve_bytes=128 * 1024, filesystem_metadata_reserve_bytes=65536,
        new_allocation_limit_bytes=256 * 1024, disk_reserve_bytes=0)
    card.update(card_changes)
    card_path = root / (label + "-CARD.json")
    card_sha = write(card_path, card)
    return Namespace(machine_id=frozen["machine"], business_source_repo=frozen["repo"],
        runtime_source_repo=frozen["repo"], business_source_commit=frozen["new"],
        runtime_source_commit=frozen["new"], base_freeze=frozen["manifest"], base_freeze_sha256=frozen["manifest_sha"],
        native_pin=frozen["native"], native_pin_sha256=frozen["native_sha"], capacity_card=card_path,
        capacity_card_sha256=card_sha, sdk_generation="P37-FIXTURE", source_destination=source,
        reference_destination=reference, output_root=output)


def test_actual_ntfs_pair_and_complete_manifests(frozen):
    args = arguments(frozen, "positive")
    before = {p: p.read_bytes() for p in frozen["base"].rglob("*.py")}
    result = exporter.export_views(args)
    old_same = exporter.ntfs_identity(frozen["base"] / "xar_autoplayer/same.py")
    assert result["status"] == "SOURCE_READY_NOT_LOADED"
    assert result["game_sdk_native_obs_calls"] == 0
    assert result["new_unique_file_count"] == 4
    assert result["existing_shared_unique_file_count"] == 1
    assert result["filesystem_metadata_allocation_bytes"] is None
    for destination in (args.source_destination, args.reference_destination):
        same = exporter.ntfs_identity(destination / "xar_autoplayer/same.py")
        assert exporter.identity_key(same) == exporter.identity_key(old_same)
        assert same["links"] >= 3
        assert (destination / "xar_autoplayer/change.py").read_bytes() == b"VERSION = 2\n"
    changed_ids = [exporter.identity_key(exporter.ntfs_identity(p / "xar_autoplayer/change.py"))
                   for p in (frozen["base"], args.source_destination, args.reference_destination)]
    assert len(set(changed_ids)) == 3
    manifests = [json.loads((args.output_root / name).read_bytes())
                 for name in ("SOURCE-FREEZE.json", "REFERENCE-FREEZE.json")]
    canonical = exporter.tree(frozen["repo"], frozen["new"])
    for document in manifests:
        assert document["runtime_admitted"] is False
        assert {r["relative"]: r["git_blob_sha1"] for r in document["files"]} == {
            r: item["git_blob_sha1"] for r, item in canonical.items()}
    assert {p: p.read_bytes() for p in before} == before


def test_existing_output_and_card_reject_before_writes(frozen):
    args = arguments(frozen, "existing")
    args.source_destination.mkdir()
    with pytest.raises(ValueError, match="outputs must be absent"):
        exporter.export_views(args)
    assert not args.output_root.exists()
    args = arguments(frozen, "wrong-machine", machine_id="foreign-machine")
    with pytest.raises(ValueError, match="capacity card"):
        exporter.export_views(args)
    assert not args.output_root.exists()
    args = arguments(frozen, "budget", new_allocation_limit_bytes=0)
    with pytest.raises(ValueError, match="forecast"):
        exporter.export_views(args)
    assert not args.output_root.exists()


def test_bad_old_sha_retains_attempt_and_old_bytes(frozen):
    value = json.loads(frozen["manifest"].read_bytes())
    for row in value["files"]:
        if row["relative"].endswith("same.py"):
            row["sha256"] = "b" * 64
    altered = dict(frozen)
    altered["manifest"] = frozen["root"] / "BAD-BASE-FREEZE.json"
    altered["manifest_sha"] = write(altered["manifest"], value)
    args = arguments(altered, "bad-sha")
    old = (frozen["base"] / "xar_autoplayer/same.py").read_bytes()
    with pytest.raises(ValueError, match="frozen base content differs"):
        exporter.export_views(args)
    assert (args.output_root / "ATTEMPT.json").is_file()
    assert json.loads((args.output_root / "FAILED.json").read_bytes())["status"] == "FAILED_RETAINED_NOT_ADOPTED"
    assert not (args.output_root / "COMPLETE.json").exists()
    assert (frozen["base"] / "xar_autoplayer/same.py").read_bytes() == old


def test_link_collision_never_copies_or_overwrites(frozen, monkeypatch):
    args = arguments(frozen, "collision")
    original_link = exporter.os.link

    def collision(source, target):
        write(Path(target), b"intervening fixture owner\n")
        return original_link(source, target)

    monkeypatch.setattr(exporter.os, "link", collision)
    with pytest.raises(FileExistsError):
        exporter.export_views(args)
    same = args.source_destination / "xar_autoplayer/same.py"
    assert same.read_bytes() == b"intervening fixture owner\n"
    assert (frozen["base"] / "xar_autoplayer/same.py").read_bytes() == b"SAME = 1\n"
    assert (args.output_root / "FAILED.json").exists()
