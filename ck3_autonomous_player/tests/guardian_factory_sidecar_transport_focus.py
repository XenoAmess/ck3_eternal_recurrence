"""One new SDK request -> native parser/completion -> private capture regression."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    executable, transport_path, helper_path, support_src, output = map(Path, sys.argv[1:])
    sys.path.insert(0, str(support_src))
    transport = load("xar_autoplayer.bridge.current_first_heir_relationship_private_transport", transport_path)
    helper = load("xar_autoplayer.bridge.guardian_factory_capture_private_v1", helper_path)
    output.mkdir(parents=True, exist_ok=False)
    snapshot = {
        "native_revision": 2, "revision": 1, "date_raw": 53290128,
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "played_character_id": 29829, "played_character_alive": True,
        "snapshot_id": "fixture-native:2",
    }
    raw_family = {"ok": True, "result": {
        "step": transport.STEP, "accepted": True, "private_build": True,
        "read_only": True, "advertised": False, "native_revision": 2,
        "subject_source": "public_campaign_root_primary_first_heir",
        "heir_character_id": 38822, "status": "available",
        "unavailable_reason": None, "bilateral_verified": True,
        "betrothed_character_id": None, "primary_spouse_character_id": 38718,
        "spouse_character_ids": [38718],
    }}

    class Endpoint:
        def __init__(self, driver):
            self.driver = driver
            self.calls = 0

        def send(self, frame):
            self.calls += 1
            if self.calls != 1:
                raise AssertionError("one new native boundary invocation only")
            sidecar = Path(frame["guardian_factory_sidecar_path"])
            assert "\\" not in frame["guardian_factory_sidecar_path"]
            assert sidecar.is_absolute()
            old_frame = {**frame, "guardian_factory_sidecar_path": str(sidecar)}
            # Same compact UTF-8 encoding as the production endpoint. These
            # fixture input bytes are not claimed as a live pipe write.
            paths = [output / name for name in ("old-request.json", "fixed-request.json", "family-frame.json")]
            for path, value in zip(paths, (old_frame, frame, raw_family)):
                payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                path.write_bytes(payload)
            packet_payload = paths[1].read_bytes()
            (output / "fixture-request.packet").write_bytes(struct.pack("<I", len(packet_payload)) + packet_payload)
            result = subprocess.run([str(executable), *(str(path) for path in paths)],
                                    check=False, capture_output=True, text=True, encoding="utf-8")
            (output / "native.stdout.log").write_text(result.stdout, encoding="utf-8")
            (output / "native.stderr.log").write_text(result.stderr, encoding="utf-8")
            assert result.returncode == 0, (result.returncode, result.stderr)
            self.driver.reply = json.loads(result.stdout)

    class Driver:
        allow_private_current_first_heir_relationship_query = True

        def __init__(self):
            self.endpoint = Endpoint(self)
            self.state = self
            self.reply = None

        def diagnostics(self):
            return {"connected": True, "bridge_pid": 1337}

        def take_internal_semantic_snapshot(self):
            return deepcopy(snapshot)

        def _execute_campaign_root_context_v1_query(self, *, expected_revision):
            assert expected_revision == 1
            return {"status": "available", "query_sequence": 1,
                    "held_title_partition": [{"primary": True, "first_heir_character_id": 38822}]}

        def wait_for_command_result(self, request_id, timeout_seconds):
            return deepcopy(self.reply)

        def query_current_first_heir_relationship_private_v1(self, **arguments):
            return transport.query_current_first_heir_relationship_private_v1(self, **arguments)

    driver = Driver()
    capture = output / "capture"
    receipt = helper.capture_with_runtime_owner_driver(
        driver, owned_game_pid=1337, output_directory=capture, timeout_seconds=1)
    assert receipt["status"] == "DISCOVERY_UNAVAILABLE"
    assert receipt["actual_factory_found_count"] == 0
    assert receipt["guardian_membership_observed"] is False
    assert receipt["guardian_pair_ready"] is False
    assert receipt["G2_outcome_credit"] == 0
    assert driver.endpoint.calls == 1
    held_raw = json.loads((capture / "guardian-family-command-result.json").read_text(encoding="utf-8"))
    assert held_raw["result"] == raw_family["result"]
    diagnostic = held_raw["guardian_factory_discovery_v1"]
    assert diagnostic["path_parsed"] and diagnostic["job_created"]
    assert diagnostic["completion_attempted"] and diagnostic["sidecar_written"]
    assert diagnostic["job_executed"] is False
    assert diagnostic["job_frame_observed"] is False
    assert diagnostic["metadata_copied"] is False
    assert diagnostic["error"] is None
    family = json.loads((capture / "family-result.json").read_text(encoding="utf-8"))
    assert family["status"] == "available" and family["primary_spouse_character_id"] == 38718
    assert "guardian_factory_discovery_v1" not in family
    sidecar = json.loads((capture / "guardian-two-factory-source.json").read_text(encoding="utf-8"))
    assert [row["key"] for row in sidecar["factories"]] == ["has_relation_guardian", "has_relation_ward"]
    assert sidecar["qualified"] is False
    assert receipt["native_command_result_path"] == str(capture / "guardian-family-command-result.json")
    print("guardian_sidecar_transport_boundary GREEN; native_invocations=1; metadata_fixture_replays=0; Game=0")


if __name__ == "__main__":
    main()
