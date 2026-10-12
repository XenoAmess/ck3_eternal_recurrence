"""Build the existing normal-exit inventory from an actual public preparation.

This creates static source metadata only. It does not launch or inspect a
process, submit an exit request, or qualify a future normal exit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_new(path, value):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return pin(path)


def project_profile(args, runtime, manifest, runtime_manifest, destination):
    """Project existing field meanings; the target record grants no launch authority."""
    state = args.state_dir.resolve()
    startup_path = state / "preparation.json"
    startup = json.loads(startup_path.read_bytes())
    if (startup.get("schema") != "ck3-mod-acceptance-profile-startup-evidence-v1"
            or Path(startup["profile_dir"]).resolve() != state / "profile"):
        raise ValueError("normal exit requires the actual public prepared profile")
    preparation_ref = startup["preparation"]
    preparation_path = Path(preparation_ref["path"]).resolve()
    actual_preparation = pin(preparation_path)
    if any(actual_preparation[key] != preparation_ref[key] for key in ("bytes", "sha256")):
        raise ValueError("actual public profile preparation bytes changed")
    preparation = json.loads(preparation_path.read_bytes())
    if (preparation.get("schema") != "ck3-mod-acceptance-prepared-fixture-v1"
            or Path(preparation["state_dir"]).resolve() != state
            or Path(preparation["profile_dir"]).resolve() != state / "profile"
            or preparation["game_version"] != manifest["game"]["version"]
            or preparation["exe_sha256"].lower() != manifest["game"]["exe_sha256"].lower()):
        raise ValueError("public preparation and selected runtime identities differ")
    native = {}
    for name, path in (("dll", args.bridge_dll), ("injector", args.bridge_injector)):
        row = manifest["native"][name]
        selected = Path(runtime["paths"][row["path_key"]]).resolve()
        if path.resolve() != selected:
            raise ValueError("normal-exit projection differs from selected native path")
        native[name] = {"path": str(selected), "sha256": row["sha256"].lower()}
    game_dir = args.game_dir.resolve()
    if game_dir != Path(runtime["game_dir"]).resolve():
        raise ValueError("normal-exit projection differs from selected game directory")
    guard = {"target": {"executable": str(game_dir / "binaries" / "ck3.exe"),
                        "executable_sha256": manifest["game"]["exe_sha256"].lower()},
             "static_source_binding_only": True, "launch_authority": False,
             "runtime_manifest": runtime_manifest, "public_preparation": actual_preparation}
    guard_path = destination / "normal-exit-target-binding.json"
    profile = {"schema_version": 1, "guard_profile": str(guard_path),
               "guard_profile_sha256": None, "userdir": str(state / "profile"),
               "state_directory": str(state), "evidence_directory": str(args.output.resolve().parent),
               "game_version": preparation["game_version"], **native}
    return profile, guard


def create_profile(args, runtime, manifest, runtime_manifest, destination, builder):
    """Use the unmodified inventory builder and verifier on this prepared userdir."""
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("normal-exit static binding already exists; do not replay")
    profile, guard = project_profile(args, runtime, manifest, runtime_manifest, destination)
    destination.mkdir()
    profile["guard_profile_sha256"] = write_new(profile["guard_profile"], guard)["sha256"]
    profile["guard"] = guard
    inventory, projection = builder.build_inventory(profile, args.game_dir / "game")
    userdir = Path(profile["userdir"])
    inventory_path = userdir / builder.INVENTORY_BASENAME
    inventory_ref = write_new(inventory_path, inventory)
    with (userdir / "normal-exit-profile-binding-projection-v1.json").open("xb") as stream:
        stream.write(projection)
    profile["normal_exit_source_inventory"] = {key: inventory_ref[key] for key in ("path", "sha256")}
    verification = builder.verify_source_inventory_v1(profile["normal_exit_source_inventory"], profile)
    del profile["guard"]
    profile_ref = write_new(destination / "normal-exit-managed-profile.json", profile)
    write_new(destination / "RESULT.actual.json", {"profile": profile_ref,
        "inventory": inventory_ref, "verification": verification,
        "runtime_manifest": runtime_manifest, "game_started": False,
        "normal_exit_qualified": False, "business_pass": False})
    return profile_ref


def load_builder(path):
    spec = importlib.util.spec_from_file_location("_actual_normal_exit_inventory_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
