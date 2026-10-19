"""Create-only review material; never installs files or publishes a request."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

T = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime")


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    leaf_path = Path(__file__).with_name("succession3851_first_semantic_resume_v1.py")
    spec = importlib.util.spec_from_file_location("_succession3851_leaf", leaf_path)
    leaf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(leaf)
    assert pin(leaf_path)["sha256"] == "9ec92c2ed9f005c9a3fcdc0e523afa960ab2e3de37b57ecefa70c5aaa15f070c"
    original = (T / "root_p37_known_owner_recovery.py").read_bytes()
    transformed = leaf.transform_unused_known_owner(original)
    leaf.prepare_original_namespace(leaf.checked(leaf.FROZEN / "root_p37_automatic_natural_succession_handoff.py", leaf.SOURCE_SHA))
    # This root is review-only. It cannot be the running runtime or an ancestor.
    out = args.output_root.resolve()
    if out == T.resolve() or out in T.resolve().parents or T.resolve() in out.parents:
        raise ValueError("review root must be outside the runtime tree")
    out.mkdir(parents=True, exist_ok=False)
    files = {"root_p37_succession3851_resume.py": leaf_path.read_bytes(),
             "root_p37_known_owner_recovery.original.py": original,
             "root_p37_known_owner_recovery.py": transformed,
             "3852-1-result.json": (json.dumps({"sequence": 3852, "command": "recover_known_owner_1024",
                 "arguments": {"repair_kind": leaf.KIND}}, ensure_ascii=False, indent=2) + "\n").encode()}
    for name, raw in files.items():
        with (out / name).open("xb") as stream:
            stream.write(raw)
    review = {"schema": "xar.succession3851-review-ready/v1", "machine_id": leaf.MACHINE,
              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "create-only candidate; zero live writes/RPC; sole runtime installs only after checking unchanged pins",
              "source_package": {"path": str(leaf.FROZEN / "FROZEN.json"), "sha256": leaf.FROZEN_SHA},
              "original_Queue": {"path": str(T / "root_p37c7_sdk_queue.py"), "sha256": leaf.QUEUE_SHA},
              "producer": pin(__file__), "files": {name: pin(out / name) for name in files},
              "request_publish_authority": "Runtime sole owner, once at still-unused NEXT3852. Keep CURRENT-REQUEST3851 until original C6 relay ACK; local control consumes NEXT only.",
              "success_receipt": str(T / "p37-queue/SUCCESSION3851-RESUME-SETTLED.json"),
              "new_audit": str(T / "p37-queue/AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3852.json"),
              "next_FULL_gate": "Original camera contract remains; runtime obtains post-handoff frozen pair/Root primary review bound to final_semantic_response and final_frame before FULL."}
    with (out / "REVIEW.json").open("x", encoding="utf-8") as stream:
        json.dump(review, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(pin(out / "REVIEW.json")))


if __name__ == "__main__":
    main()
