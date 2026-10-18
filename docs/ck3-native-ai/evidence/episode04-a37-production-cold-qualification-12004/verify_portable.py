from __future__ import annotations
import hashlib
import io
import json
import pathlib
import zipfile

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def verify_bytes(raw, index):
    with zipfile.ZipFile(io.BytesIO(raw), "r") as z:
        need(set(z.namelist()) == set(index["originals"]), "member set")
        objects = {}
        for name in z.namelist():
            body = z.read(name)
            p = index["originals"][name]
            need(len(body) == p["bytes"] and hashlib.sha256(body).hexdigest() == p["sha256"], name + " sha")
            objects[name] = json.loads(body)
            if "machine_id" in objects[name]:
                need(objects[name]["machine_id"] == index["machine_id"], name + " machine")
    q = objects["production-qualification.json"]
    c = objects["build-completion.json"]
    need(c["exit_code"] == 0 and c["production_bytes_and_SYSTEM_verified"] is True, "completion")
    need(c["focused_cold_executed"] is False, "completion ordering")
    need(q["status"] == "PRODUCTION_BYTES_SYSTEM_AND_MINIMAL_COLD_VERIFIED", "qual status")
    need(q["source_head"] == q["runtime_source_head"] == q["native_build_source_head"] == c["source_head"] == index["source_head"], "source")
    need(q["build_completion"]["bytes"] == index["originals"]["build-completion.json"]["bytes"] and q["build_completion"]["sha256"] == index["originals"]["build-completion.json"]["sha256"], "completion binding")
    need(q["capacity"] == c["capacity"] and len(q["outputs"]) == 7 and q["county_case_count"] == 2, "capacity/outputs")
    need(q["production_bytes_qualified"] is True and q["focused_cold_qualified"] is True, "cold qualification")
    need(q["live_CK3_qualified"] is False and q["CK3_actual_ADD_observed"] is False and q["gameplay_qualified"] is False, "gameplay boundary")
    for key, name in index["child_bindings"].items():
        need(q[key]["bytes"] == index["originals"][name]["bytes"] and q[key]["sha256"] == index["originals"][name]["sha256"], key + " binding")
    for name in ("county-cold-step.json", "county-wire-step.json", "worker-cold-step.json"):
        need(objects[name]["exit_code"] == 0, name + " exit")
    need(objects["county-strict-wire.json"]["status"] == "PASS_ACTUAL_NATIVE_COUNTY_PRIMARY_OWNER_WIRE", "county wire")
    w = objects["worker-focused-result.json"]
    need(w["status"] == "PASS" and w["case_count"] == 2 and all(x["status"] == "PASS" for x in w["cases"]), "worker cases")
    return True

def main():
    root = pathlib.Path(__file__).resolve().parent
    index = json.loads((root / "index.json").read_bytes())
    raw = (root / "evidence.zip").read_bytes()
    need(len(raw) == index["zip"]["bytes"] and hashlib.sha256(raw).hexdigest() == index["zip"]["sha256"], "zip")
    verify_bytes(raw, index)
    print("PASS: a37 production and focused cold, no live CK3/ADD")

if __name__ == "__main__":
    main()
