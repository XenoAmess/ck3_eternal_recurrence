"""Create two canonical SDK views using admitted, frozen NTFS blobs.

This is an explicit new export mode, not a modification of an old snapshot or
the original full-copy freezer. No fallback, cleanup, runtime import override,
Native connection or Game/SDK/OBS launch occurs. See the capacity-card contract in
validate_inputs(). A failed attempt is retained for its owner to review.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ck3_live_run_id import current_machine_id

CARD_SCHEMA = "xar.ck3.immutable-sdk-view-capacity/v1"
MAX_FILES = 2500
MAX_BYTES = 128 * 1024**2
PREFIX = "ck3_autonomous_player/src/"
REPARSE = 0x400


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc)


def read_json_pin(path, expected_sha):
    raw = Path(path).read_bytes()
    require(len(raw) <= 2 * 1024**2, "bounded JSON input required")
    require(hashlib.sha256(raw).hexdigest() == expected_sha, "JSON input pin differs")
    value = json.loads(raw)
    require(isinstance(value, dict), "JSON object required")
    return value, dict(path=str(Path(path).resolve()), bytes=len(raw), sha256=expected_sha)


def create_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    with Path(path).open("xb") as stream:
        stream.write(raw)
    return dict(path=str(Path(path).resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def commit(repo, revision):
    require(isinstance(revision, str) and len(revision) == 40 and
            all(x in "0123456789abcdef" for x in revision), "full commit required")
    require(git(repo, "rev-parse", revision + "^{commit}").decode().strip() == revision,
            "commit resolution differs")
    return revision


def checked_relative(value):
    require(isinstance(value, str) and "\\" not in value, "POSIX relative source path required")
    path = PurePosixPath(value)
    require(value == path.as_posix() and not path.is_absolute() and value not in ("", ".")
            and all(x not in (".", "..") for x in path.parts)
            and ":" not in value and "\x00" not in value, "unsafe source path")
    return path


def no_reparse(path):
    path = Path(path).absolute()
    for item in reversed((path, *path.parents)):
        if not item.exists() and not item.is_symlink():
            continue
        info = item.lstat()
        require(not stat.S_ISLNK(info.st_mode) and
                not getattr(info, "st_file_attributes", 0) & REPARSE,
                "reparse/symlink path refused: " + str(item))
    return path.resolve()


def tree(repo, revision):
    result = {}
    for line in git(repo, "ls-tree", "-rlz", revision, "ck3_autonomous_player/src").split(b"\0"):
        if not line:
            continue
        header, raw_path = line.split(b"\t", 1)
        mode, kind, object_id, size = header.decode("ascii").split()
        name = raw_path.decode("utf-8")
        require(kind == "blob" and mode in ("100644", "100755") and name.startswith(PREFIX),
                "ordinary tracked SDK blobs required")
        relative = checked_relative(name[len(PREFIX):]).as_posix()
        require(relative not in result and int(size) >= 0, "duplicate/invalid tree entry")
        result[relative] = dict(git_blob_sha1=object_id, bytes=int(size), git_mode=mode)
    require(0 < len(result) <= MAX_FILES and sum(v["bytes"] for v in result.values()) <= MAX_BYTES,
            "canonical SDK tree exceeds bounds")
    require(len({name.casefold() for name in result}) == len(result), "case-colliding NTFS paths refused")
    return result


def hash_file(path, size):
    sha = hashlib.sha256()
    blob = hashlib.sha1(b"blob " + str(size).encode() + b"\0")
    total = 0
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(chunk)
            require(total <= size, "frozen source grew")
            sha.update(chunk)
            blob.update(chunk)
    require(total == size, "frozen source size differs")
    return sha.hexdigest(), blob.hexdigest()


def ntfs_identity(path):
    """Actual Windows metadata, including allocation; never infer allocation from size."""
    require(os.name == "nt", "this exporter requires actual Windows NTFS metadata")
    from ctypes import wintypes as w
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)

    class Info(ctypes.Structure):
        _fields_ = [("attributes", w.DWORD), ("creation", w.FILETIME), ("access", w.FILETIME),
                    ("write", w.FILETIME), ("volume", w.DWORD), ("size_hi", w.DWORD),
                    ("size_lo", w.DWORD), ("links", w.DWORD), ("id_hi", w.DWORD), ("id_lo", w.DWORD)]

    class Standard(ctypes.Structure):
        _fields_ = [("allocation", ctypes.c_longlong), ("length", ctypes.c_longlong),
                    ("links", w.DWORD), ("delete_pending", w.BOOLEAN), ("directory", w.BOOLEAN)]

    def call(name, argtypes, restype):
        fn = getattr(kernel, name)
        fn.argtypes, fn.restype = argtypes, restype
        return fn

    def checked(ok):
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())

    full = str(no_reparse(path))
    volume_path = ctypes.create_unicode_buffer(32768)
    checked(call("GetVolumePathNameW", [w.LPCWSTR, w.LPWSTR, w.DWORD], w.BOOL)(full, volume_path, len(volume_path)))
    filesystem = ctypes.create_unicode_buffer(64)
    checked(call("GetVolumeInformationW", [w.LPCWSTR, w.LPWSTR, w.DWORD, ctypes.c_void_p,
                 ctypes.c_void_p, ctypes.c_void_p, w.LPWSTR, w.DWORD], w.BOOL)(
                     volume_path.value, None, 0, None, None, None, filesystem, len(filesystem)))
    require(filesystem.value.upper() == "NTFS", "same-volume NTFS is required")
    sectors, sector_bytes = w.DWORD(), w.DWORD()
    checked(call("GetDiskFreeSpaceW", [w.LPCWSTR, ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD),
                 ctypes.c_void_p, ctypes.c_void_p], w.BOOL)(volume_path.value, ctypes.byref(sectors),
                                                         ctypes.byref(sector_bytes), None, None))
    cluster = sectors.value * sector_bytes.value
    require(0 < cluster <= 65536, "bounded NTFS cluster size required")
    open_file = call("CreateFileW", [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p,
                                    w.DWORD, w.DWORD, w.HANDLE], w.HANDLE)
    handle = open_file(full, 0x80, 7, None, 3, 0x02000000 | 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info, standard = Info(), Standard()
        checked(call("GetFileInformationByHandle", [w.HANDLE, ctypes.POINTER(Info)], w.BOOL)(handle, ctypes.byref(info)))
        checked(call("GetFileInformationByHandleEx", [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL)(
            handle, 1, ctypes.byref(standard), ctypes.sizeof(standard)))
        require(not info.attributes & REPARSE and not standard.delete_pending, "unstable/reparse file refused")
        return dict(volume_serial=info.volume, file_id=f"{info.id_hi:08x}{info.id_lo:08x}",
                    allocation_bytes=standard.allocation, bytes=standard.length, links=info.links,
                    directory=bool(standard.directory), filesystem=filesystem.value, cluster_bytes=cluster)
    finally:
        call("CloseHandle", [w.HANDLE], w.BOOL)(handle)


def identity_key(value):
    return value["volume_serial"], value["file_id"]


def existing_parent(path):
    parent = Path(path).parent
    while not parent.exists():
        parent = parent.parent
    return parent


def validate_inputs(args):
    require(args.machine_id == current_machine_id(), "actual machine differs")
    require(sys.dont_write_bytecode, "run with -B/PYTHONDONTWRITEBYTECODE")
    business, host = no_reparse(args.business_source_repo), no_reparse(args.runtime_source_repo)
    canonical = commit(business, args.business_source_commit)
    host_commit = commit(host, args.runtime_source_commit)
    require(not git(host, "status", "--porcelain").strip() and
            git(host, "rev-parse", "HEAD").decode().strip() == host_commit, "fixed Host checkout differs/is dirty")
    base, base_pin = read_json_pin(args.base_freeze, args.base_freeze_sha256)
    native, native_pin = read_json_pin(args.native_pin, args.native_pin_sha256)
    card, card_pin = read_json_pin(args.capacity_card, args.capacity_card_sha256)
    require(card.get("schema") == CARD_SCHEMA and card.get("status") == "ADMITTED" and
            card.get("machine_id") == args.machine_id, "exact admitted capacity card required")
    expiry = datetime.fromisoformat(card["review_at_utc"].replace("Z", "+00:00"))
    require(expiry.tzinfo is not None and utc() < expiry, "capacity review expired")
    require(base.get("status") == "FINAL_SOURCE_FROZEN" and base.get("machine_id") == args.machine_id,
            "actual frozen base required")
    require(native.get("machine_id") == args.machine_id, "native pin belongs to another/unknown machine")
    require(base.get("git_head") == host_commit and native.get("native_build_label") == base.get("native_build_label")
            and native.get("native_dll_sha256") == base.get("native_dll_sha256"), "Host/native base binding differs")
    roots = [no_reparse(x) for x in (args.source_destination, args.reference_destination, args.output_root)]
    require(len(set(roots)) == 3 and not any(a.is_relative_to(b) for a in roots for b in roots if a != b),
            "new output roots must be disjoint")
    base_root = no_reparse(base["source_root"])
    require(base_root.is_dir() and not any(base_root.is_relative_to(r) or r.is_relative_to(base_root) for r in roots),
            "outputs cannot alias/contain the frozen base")
    require(all(not r.exists() for r in roots), "outputs must be absent; failed attempts are retained")
    for name, expected in dict(business_source_commit=canonical, runtime_source_commit=host_commit,
                               base_freeze_sha256=args.base_freeze_sha256, native_pin_sha256=args.native_pin_sha256,
                               sdk_generation=args.sdk_generation, base_source_root=str(base_root),
                               source_destination=str(roots[0]), reference_destination=str(roots[1]),
                               output_root=str(roots[2])).items():
        require(card.get(name) == expected, "capacity binding differs: " + name)
    approved = [no_reparse(p) for p in card["approved_output_roots"]]
    require(approved and all(any(r.is_relative_to(a) for a in approved) for r in roots), "output root not approved")
    base_tree = tree(business, commit(business, base["business_source_commit"]))
    new_tree = tree(business, canonical)
    rows = base.get("files")
    require(isinstance(rows, list) and len(rows) == len(base_tree) == base.get("source_file_count"), "base manifest set differs")
    indexed = {}
    for row in rows:
        relative = checked_relative(row["relative"]).as_posix()
        require(relative not in indexed and relative in base_tree and
                all(row.get(k) == base_tree[relative][k] for k in ("bytes", "git_blob_sha1")), "base canonical row differs")
        require(isinstance(row.get("sha256"), str) and len(row["sha256"]) == 64, "base SHA required")
        indexed[relative] = row
    require(sum(r["bytes"] for r in rows) == base.get("source_bytes"), "base logical size differs")
    base_identity = ntfs_identity(base_root)
    require(base_identity["directory"], "frozen base directory required")
    for root in roots:
        require(ntfs_identity(existing_parent(root))["volume_serial"] == base_identity["volume_serial"],
                "all output roots must be on the base NTFS volume")
    changed = [r for r, item in new_tree.items() if r not in base_tree or item != base_tree[r]]
    cluster = base_identity["cluster_bytes"]
    data_upper = 2 * sum(((new_tree[r]["bytes"] + cluster - 1) // cluster) * cluster for r in changed)
    reserve = card.get("metadata_reserve_bytes")
    filesystem_reserve = card.get("filesystem_metadata_reserve_bytes")
    limit = card.get("new_allocation_limit_bytes")
    disk_reserve = card.get("disk_reserve_bytes")
    require(all(type(x) is int and x >= 0 for x in (reserve, filesystem_reserve, limit, disk_reserve))
            and filesystem_reserve >= 65536 and reserve >= filesystem_reserve + 65536,
            "explicit data/metadata/disk budget required")
    require(data_upper + reserve <= limit, "new allocation forecast exceeds card")
    require(shutil.disk_usage(base_root).free > disk_reserve + data_upper + reserve, "fresh same-volume capacity insufficient")
    return dict(business=business, host_commit=host_commit, canonical=canonical, base=base, base_pin=base_pin,
                base_root=base_root, indexed=indexed, base_tree=base_tree, new_tree=new_tree, roots=roots,
                native=native, native_pin=native_pin, card=card, card_pin=card_pin, changed=changed,
                data_upper=data_upper, metadata_reserve=reserve, filesystem_reserve=filesystem_reserve,
                expiry=expiry)


def export_views(args):
    context = validate_inputs(args)  # all admission checks precede output creation
    source, reference, output = context["roots"]
    metadata_used = 0
    new_ids = {}

    def still_admitted():
        require(utc() < context["expiry"], "capacity review expired during export")
        unspent = max(0, context["data_upper"] - sum(new_ids.values())) + context["metadata_reserve"] - metadata_used
        require(shutil.disk_usage(context["base_root"]).free > context["card"]["disk_reserve_bytes"] + unspent,
                "same-volume capacity changed during export")

    def record(path, value):
        nonlocal metadata_used
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
        cluster = ntfs_identity(existing_parent(path))["cluster_bytes"]
        upper = ((len(raw) + cluster - 1) // cluster) * cluster
        still_admitted()
        # Reserve unknown directory/link/MFT bookkeeping separately; never call it measured.
        require(metadata_used + upper + context["filesystem_reserve"] <= context["metadata_reserve"],
                "metadata file budget exhausted")
        result = create_json(path, value)
        allocated = ntfs_identity(path)["allocation_bytes"]
        require(allocated <= upper, "metadata file allocation exceeds forecast")
        metadata_used += allocated
        return result

    output.mkdir(parents=True, exist_ok=False)
    record(output / "ATTEMPT.json", dict(machine_id=args.machine_id, at_utc=utc().isoformat(),
                status="STARTED_NOT_ADOPTED", capacity=context["card_pin"], base_freeze=context["base_pin"],
                business_source_commit=context["canonical"], output_roots=[str(p) for p in context["roots"]]))
    try:
        source.mkdir(parents=True, exist_ok=False)
        reference.mkdir(parents=True, exist_ok=False)
        all_rows = [[], []]
        shared_ids = {}
        # Even old leaves not reused as links cannot become an alias for a new changed leaf.
        old_ids = set()
        for relative, old_item in context["base_tree"].items():
            old_identity = ntfs_identity(context["base_root"] / relative)
            require(not old_identity["directory"] and old_identity["bytes"] == old_item["bytes"],
                    "old ordinary file metadata differs")
            old_ids.add(identity_key(old_identity))
        for relative, item in context["new_tree"].items():
            unchanged = relative not in context["changed"]
            original = context["base_root"] / relative
            before = None
            if unchanged:
                original = no_reparse(original)
                before = ntfs_identity(original)
                require(not before["directory"] and before["bytes"] == item["bytes"], "base ordinary file differs")
                sha, blob = hash_file(original, item["bytes"])
                require(sha == context["indexed"][relative]["sha256"] and blob == item["git_blob_sha1"],
                        "frozen base content differs from canonical blob")
                require(identity_key(ntfs_identity(original)) == identity_key(before), "base identity changed while reading")
                old_ids.add(identity_key(before))
            else:
                raw = git(context["business"], "cat-file", "blob", item["git_blob_sha1"])
                require(len(raw) == item["bytes"] and hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                        == item["git_blob_sha1"], "canonical changed blob differs")
                sha = hashlib.sha256(raw).hexdigest()
            for index, root in enumerate((source, reference)):
                still_admitted()
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                no_reparse(target.parent)
                if unchanged:
                    os.link(original, target)  # atomic create-only; never open this alias for writing
                else:
                    with target.open("xb") as stream:
                        stream.write(raw)
                actual = ntfs_identity(target)
                require(not actual["directory"] and actual["bytes"] == item["bytes"] and
                        hash_file(target, item["bytes"]) == (sha, item["git_blob_sha1"]), "new canonical output differs")
                key = identity_key(actual)
                if unchanged:
                    require(key == identity_key(before), "hardlink identity differs")
                    shared_ids[key] = actual["allocation_bytes"]
                else:
                    require(key not in new_ids and key not in old_ids, "changed blob aliases an existing file")
                    new_ids[key] = actual["allocation_bytes"]
                row = dict(relative=relative, bytes=item["bytes"], sha256=sha,
                           git_blob_sha1=item["git_blob_sha1"], git_mode=item["git_mode"],
                           storage_mode="existing_frozen_hardlink" if unchanged else "independent_new_blob",
                           file_identity=actual)
                if unchanged:
                    row["hardlink_source"] = dict(path=str(original), freeze_sha256=args.base_freeze_sha256,
                                                  identity_before=before)
                all_rows[index].append(row)
            require(sum(new_ids.values()) <= context["data_upper"], "actual new file allocation exceeds forecast")
        require(not (set(new_ids) & set(shared_ids)), "new/shared identity accounting overlaps")
        manifests = []
        for index, root in enumerate((source, reference)):
            manifest = dict(schema=context["base"].get("schema", "root.ck3.final-sdk-source-freeze/v1"),
                sdk_generation=args.sdk_generation, status="FINAL_SOURCE_FROZEN", machine_id=args.machine_id,
                at_utc=utc().isoformat(), source_root=str(root), files=all_rows[index],
                source_bytes=sum(r["bytes"] for r in all_rows[index]), source_file_count=len(all_rows[index]),
                git_head=context["host_commit"], runtime_source_repo=str(Path(args.runtime_source_repo).resolve()),
                business_source_commit=context["canonical"], business_source_repo=str(context["business"]),
                business_source_bytes_basis="canonical Git blobs; unchanged blobs bound to exact frozen NTFS file identity",
                native_build_label=context["native"]["native_build_label"],
                native_dll_sha256=context["native"]["native_dll_sha256"], clean_campaign=True,
                prior_campaign_state_or_credits_inherited=False, runtime_admitted=False,
                source_namespace=context["base"].get("source_namespace"), native_consumer_closure_review_pending=True,
                base_freeze=context["base_pin"], capacity_admission=context["card_pin"],
                reference_independent_physical_replica=False)
            manifests.append(record(output / ("SOURCE-FREEZE.json" if index == 0 else "REFERENCE-FREEZE.json"), manifest))
        receipt = dict(schema="xar.ck3.immutable-sdk-view-export/v1", machine_id=args.machine_id,
            at_utc=utc().isoformat(), status="SOURCE_READY_NOT_LOADED", manifests=manifests,
            business_source_commit=context["canonical"], changed_relative_paths=context["changed"],
            logical_bytes_each=sum(x["bytes"] for x in context["new_tree"].values()),
            new_unique_file_count=len(new_ids), existing_shared_unique_file_count=len(shared_ids),
            new_unique_file_allocation_bytes=sum(new_ids.values()),
            existing_shared_allocation_bytes_not_new_credit=sum(shared_ids.values()),
            metadata_json_allocation_bytes_before_completion=metadata_used,
            filesystem_metadata_allocation_bytes=None, metadata_budget_reserve_bytes=context["metadata_reserve"],
            filesystem_metadata_budget_reserve_bytes=context["filesystem_reserve"],
            forecast_new_data_allocation_bytes=context["data_upper"], capacity=context["card_pin"],
            game_sdk_native_obs_calls=0, old_content_write_operations=0)
        record(output / "COMPLETE.json", receipt)
        return receipt
    except BaseException as error:
        try:
            record(output / "FAILED.json", dict(machine_id=args.machine_id, at_utc=utc().isoformat(),
                        status="FAILED_RETAINED_NOT_ADOPTED", exception_type=type(error).__name__,
                        message=str(error), output_roots=[str(p) for p in context["roots"]]))
        except Exception as recording_error:
            error.add_note("failure receipt unavailable: " + str(recording_error))
        raise


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    for name in ("business-source-repo", "runtime-source-repo", "base-freeze", "native-pin", "capacity-card",
                 "source-destination", "reference-destination", "output-root"):
        result.add_argument("--" + name, type=Path, required=True)
    for name in ("business-source-commit", "runtime-source-commit", "base-freeze-sha256", "native-pin-sha256",
                 "capacity-card-sha256", "machine-id", "sdk-generation"):
        result.add_argument("--" + name, required=True)
    return result


if __name__ == "__main__":
    print(json.dumps(export_views(parser().parse_args()), ensure_ascii=False, indent=2))
