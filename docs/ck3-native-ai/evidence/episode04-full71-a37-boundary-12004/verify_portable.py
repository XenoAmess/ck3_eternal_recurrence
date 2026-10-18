from __future__ import annotations
import hashlib
import io
import json
import pathlib
import sys
import zipfile

def need(value, message):
    if not value:
        raise ValueError(message)

def verify_bytes(data, index):
    with zipfile.ZipFile(io.BytesIO(data), "r") as z:
        need(set(z.namelist()) == set(index["originals"]), "archive member set")
        payload = {name: z.read(name) for name in z.namelist()}
    for name, expected in index["originals"].items():
        raw = payload[name]
        need(len(raw) == expected["bytes"] and hashlib.sha256(raw).hexdigest() == expected["sha256"], name + " pin")
        machine = json.loads(raw).get("machine_id")
        if machine is not None:
            need(machine == index["machine_id"], name + " machine")
    media = json.loads(payload["full71-purpose-close.json"])
    old = json.loads(payload["a37-old-failure-preservation.json"])
    new = json.loads(payload["a37-sourcebound-recovery-prepared.json"])
    need(media["status"] == "PURPOSE_CLOSED_MEDIA_BYTES_IMMUTABLE" and media["technical_qa"] == "GREEN", "media status")
    need(media["human_full_1x"] is False and media["signoff"] is False and media["formal_dynamic_credit"] is False, "media limits")
    need(media["pts_exit"] == media["strict_decode_exit"] == 0, "technical exits")
    need(old["compiler_error"]["code"] == "C2039" and old["compiler_error"]["missing_member"] == "capture_enabled", "compiler error")
    need(old["original_standard_producer_result_absent"] is True and old["original_floor_failure"] == "RuntimeError: volume free floor reached: C:/", "old RED")
    need(new["status"] == "SOURCE_BOUND_RECOVERY_PLAN_PREPARED_NO_BUILD" and new["actual_bridge_compile_and_DLL_link_required"] is True, "new NOT RUN")
    need(media["source_head_at_admission"] == old["source_head"] == "fd5c7ea5a8e48076aab35ad422af4e91f1ac1011", "old source")
    need(new["source_head"] == "bc4604bed4eb8558b3f4e0e554a642aa69a4ba2f", "new source")
    return True

def main():
    root = pathlib.Path(__file__).resolve().parent
    idx = json.loads((root / "index.json").read_bytes())
    data = (root / "evidence.zip").read_bytes()
    need(len(data) == idx["zip"]["bytes"] and hashlib.sha256(data).hexdigest() == idx["zip"]["sha256"], "zip pin")
    verify_bytes(data, idx)
    print("PASS: Full71 technical QA and a37 failed/prepared boundaries verified")

if __name__ == "__main__":
    main()
