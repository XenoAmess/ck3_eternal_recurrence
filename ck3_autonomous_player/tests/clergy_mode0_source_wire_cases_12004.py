"""No-main export for one new 03e native wire ->58e strict consumer compound."""

from __future__ import annotations

from copy import deepcopy
import datetime
import hashlib
import importlib
import json
from pathlib import Path
import sys


def _pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def run_actual_clergy_source_wire_cases(
    wire_path: str, report_path: str, query_frame_receipt_path: str,
    repo: str | None = None, *, report_root: str,
) -> dict:
    """Use the actual serialized command_result; mutations claim decoder credit only."""
    repo_root = Path(repo).resolve() if repo is not None else Path(__file__).resolve().parents[2]
    source_root = repo_root / "ck3_autonomous_player/src"
    destination = Path(report_path).resolve()
    owned_report_root = Path(report_root).resolve()
    if (owned_report_root.is_relative_to(repo_root)
            or destination.is_relative_to(repo_root)
            or not destination.is_relative_to(owned_report_root)):
        raise ValueError("The report must stay in the explicitly owned external report root")
    sys.path.insert(0, str(source_root))
    import xar_autoplayer.bridge as bridge
    bridge.__path__.insert(0, str(source_root / "xar_autoplayer/bridge"))
    names = ("xar_autoplayer.bridge.player_clergy_mode0_source_12004",
             "xar_autoplayer.bridge.player_clergy_appointment_private_transport")
    for name in names:
        sys.modules.pop(name, None)
    decoder, transport = (importlib.import_module(name) for name in names)
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    loaded = [_pin(Path(module.__file__).resolve()) for module in (decoder, transport)]
    assert all(Path(item["path"]).is_relative_to(source_root) for item in loaded)
    actual_path = Path(wire_path).resolve()
    actual = json.loads(actual_path.read_text(encoding="utf-8-sig"))
    assert actual["type"] == "command_result" and actual["ok"] is True
    result = actual["result"]
    clergy = result["player_clergy_appointment"]
    packet = result[decoder.FIELD_NAME]
    assert isinstance(packet, dict), "The new actual wire must carry the producer's owned packet"
    actual_source_before = deepcopy(packet)
    # The future native execution owner must record the actual existing query
    # frame. No public revision or admission flag is guessed from the packet.
    frame_receipt_path = Path(query_frame_receipt_path).resolve()
    frame_receipt = json.loads(frame_receipt_path.read_text(encoding="utf-8-sig"))
    query_frame = frame_receipt["query_frame"]
    public_revision = query_frame["public_revision"]
    assert type(public_revision) is int and 0 < public_revision < (1 << 64)
    for key in ("native_revision", "capture_epoch"):
        assert type(query_frame[key]) is int and 0 < query_frame[key] < (1 << 64)
    for key in ("date_raw", "owner_character_id", "candidate_character_id"):
        assert type(query_frame[key]) is int and -(1 << 31) <= query_frame[key] < (1 << 31)
    assert query_frame["native_revision"] == result["snapshot_revision"]
    assert query_frame["date_raw"] == result["date_raw"]
    assert query_frame["owner_character_id"] == clergy["owner_character_id"]
    assert query_frame["candidate_character_id"] == clergy["candidate_character_id"]
    assert query_frame["capture_epoch"] == clergy["capture_epoch"]
    assert query_frame["paused"] is True and query_frame["map_ready"] is True
    assert query_frame["played_character_alive"] is True
    snapshot = {
        "snapshot_id": None, "revision": public_revision,
        "native_revision": query_frame["native_revision"], "date_raw": query_frame["date_raw"],
        "paused": query_frame["paused"], "map_ready": query_frame["map_ready"],
        "played_character": {"character_id": query_frame["owner_character_id"],
                             "alive": query_frame["played_character_alive"]},
        "diagnostics": {"hello": {"expected_ck3_version": result["game_version"],
                                   "expected_ck3_sha256": result["executable_sha256"]}},
    }
    report = {
        "schema": "xar.native71.focused-clergy-mode0-source-wire-proof.v1",
        "owner": "continuation-58e", "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "wire": _pin(actual_path), "loaded_sources": loaded,
        "actual_query_frame_receipt": _pin(frame_receipt_path), "query_frame": deepcopy(query_frame),
        "native_packet_fabricated": False, "old_clergy62_or_M4_cases_replayed": False,
        "new_native_or_Game_query_invocations": 0, "status": "RED", "checks": [],
    }

    class WireDriver:
        allow_private_player_clergy_appointment_query = True
        command_timeout_seconds = 1.0
        query_player_clergy_appointment_private_v1 = NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1

        def __init__(self, body):
            self.body = body
            self.frame = deepcopy(snapshot)
            self.endpoint = self
            self.state = self
            self.sent = []
            self.snapshot_reads = 0

        def take_snapshot(self):
            self.snapshot_reads += 1
            return deepcopy(self.frame)

        def send(self, request):
            self.sent.append(deepcopy(request))

        def wait_for_command_result(self, request_id, timeout):
            assert len(self.sent) == 1
            assert self.sent[0]["request_id"] == request_id
            # Only the outer request_id is rebound for the transport fixture.
            # The complete result body is the actual native serializer output.
            response = deepcopy(self.body)
            response["request_id"] = request_id
            return response

    def query(body):
        driver = WireDriver(body)
        output = driver.query_player_clergy_appointment_private_v1(
            expected_revision=public_revision,
            candidate_character_id=clergy["candidate_character_id"])
        assert len(driver.sent) == 1 and driver.snapshot_reads == 2
        request = driver.sent[0]
        assert request["step"] == transport.STEP
        assert request["expected_revision"] == result["snapshot_revision"]
        assert request["expected_public_revision"] == public_revision
        assert request["candidate_character_id"] == clergy["candidate_character_id"]
        return output

    def base_fields(output):
        return {key: value for key, value in output.items()
                if key not in (decoder.FIELD_NAME, decoder.FIELD_NAME + "_error")}

    try:
        normalized = decoder.normalize_player_clergy_mode0_source_12004(
            packet, snapshot=snapshot, clergy=clergy)
        assert normalized == packet and normalized is not packet
        observed = query(actual)
        assert observed[decoder.FIELD_NAME] == packet and decoder.FIELD_NAME + "_error" not in observed
        assert observed.get("native_can_fire") == clergy.get("native_can_fire")
        assert type(observed.get("native_can_fire")) is type(clergy.get("native_can_fire"))
        report["checks"].append({"name": "actual_native_same_response_decoder_and_existing_driver_query",
                                 "query_invocations": 1, "aggregate_native_can_fire": clergy.get("native_can_fire"),
                                 "actual_source_packet": deepcopy(packet)})

        frame = normalized["source_read_frame"]
        assert frame["frame_identity"] is None and frame["snapshot_identity"] is None and frame["ready"] is False
        assert frame["native_revision"] == result["snapshot_revision"]
        assert frame["proof_epoch"] == clergy["capture_epoch"]
        assert all(normalized["sourceproof"][key] is False for key in (
            "native_callee_invocation_observed", "natural_return_witness", "native_calls_added"))
        assert normalized["generic_trigger"]["source_value_ready"] is False
        assert normalized["generic_trigger"]["raw_al"] is None
        report["checks"].append({"name": "actual_unknown_identity_dynamic_byte_and_natural_witness_preserved",
                                 "source_read_frame": deepcopy(frame), "source_ready": normalized["sourceproof"]["source_ready"]})

        normalized["inputs"]["raw_al"] = 254
        assert result[decoder.FIELD_NAME] == actual_source_before
        report["checks"].append({"name": "normalized_owned_copy_does_not_mutate_actual_wire"})

        legacy = deepcopy(actual)
        legacy["result"].pop(decoder.FIELD_NAME)
        legacy_output = query(legacy)
        assert decoder.FIELD_NAME not in legacy_output and decoder.FIELD_NAME + "_error" not in legacy_output
        assert legacy_output == base_fields(observed)
        report["checks"].append({"name": "derived_legacy_absence_preserves_entire_base_query", "derived_mutation": True})

        explicit_null = deepcopy(actual)
        explicit_null["result"][decoder.FIELD_NAME] = None
        null_output = query(explicit_null)
        assert null_output[decoder.FIELD_NAME] is None and decoder.FIELD_NAME + "_error" not in null_output
        assert base_fields(null_output) == legacy_output
        report["checks"].append({"name": "derived_explicit_null_stays_distinct_from_absence", "derived_mutation": True})

        for byte in (0, 2, 255):
            changed = deepcopy(packet)
            changed["inputs"].update(raw_al=byte, final_raw_al=byte, initial_raw_al=255,
                                     position_raw_al=2, branch="final_raw_al", unavailable_input="")
            changed["generic_trigger"].update(raw_al=byte, evaluation_flag_raw_u8=byte)
            copied = decoder.normalize_player_clergy_mode0_source_12004(
                changed, snapshot=snapshot, clergy=clergy)
            assert copied["inputs"]["raw_al"] == byte and type(copied["inputs"]["raw_al"]) is int
            assert copied["generic_trigger"]["raw_al"] == byte and type(copied["generic_trigger"]["raw_al"]) is int
        report["checks"].append({"name": "derived_raw_zero_two_and_255_remain_bytes_without_bool_coercion",
                                 "derived_mutation": True, "native_return_credit": False})

        changed = deepcopy(packet)
        changed["inputs"].update(owner_id_raw32=0xFF000005, incumbent_id_raw32=0xFFFFFFFF,
                                 compared_id_raw32=0)
        changed["generic_trigger"].update(scope_root_word=65535, scope_full_id_payload=(1 << 64) - 1)
        copied = decoder.normalize_player_clergy_mode0_source_12004(changed, snapshot=snapshot, clergy=clergy)
        assert copied["inputs"]["owner_id_raw32"] == 0xFF000005
        assert copied["generic_trigger"]["scope_full_id_payload"] == (1 << 64) - 1
        generation = deepcopy(packet)
        generation_clergy = deepcopy(clergy)
        for key, value in (("owner_character_id", 0x7F000005), ("candidate_character_id", 0x7E000010)):
            generation[key] = generation_clergy[key] = value
        generation_copy = decoder.normalize_player_clergy_mode0_source_12004(
            generation, snapshot=snapshot, clergy=generation_clergy)
        assert generation_copy["owner_character_id"] == 0x7F000005
        assert generation_copy["candidate_character_id"] == 0x7E000010
        report["checks"].append({"name": "derived_full_generation_and_unsigned_operand_payloads_preserved",
                                 "derived_mutation": True})

        def rejected(name, mutate):
            changed = deepcopy(actual)
            mutate(changed["result"][decoder.FIELD_NAME])
            try:
                decoder.normalize_player_clergy_mode0_source_12004(
                    changed["result"][decoder.FIELD_NAME], snapshot=snapshot, clergy=clergy)
            except ValueError as error:
                output = query(changed)
                assert output[decoder.FIELD_NAME] is None and isinstance(output[decoder.FIELD_NAME + "_error"], str)
                assert base_fields(output) == legacy_output
                report["checks"].append({"name": name, "derived_mutation": True, "rejected": True,
                                         "base_and_aggregate_preserved": True, "error": str(error)})
            else:
                raise AssertionError(name + " accepted malformed optional source")

        rejected("byte_bool_rejected_without_erasing_aggregate", lambda p: p["inputs"].update(initial_raw_al=True))
        rejected("byte_256_rejected_without_erasing_aggregate", lambda p: p["inputs"].update(initial_raw_al=256))
        rejected("full_owner_generation_mismatch_rejected", lambda p: p.update(owner_character_id=p["owner_character_id"] ^ 0x01000000))
        rejected("another_native_revision_rejected", lambda p: p["source_read_frame"].update(native_revision=p["source_read_frame"]["native_revision"] + 1))
        rejected("query_counter_as_original_identity_rejected", lambda p: p["source_read_frame"].update(frame_identity=p["source_read_frame"]["query_sequence"]))
        rejected("natural_invocation_credit_rejected", lambda p: p["sourceproof"].update(natural_return_witness=True))
        rejected("borrowed_scope_pointer_rejected", lambda p: p["generic_trigger"].update(scope_identity=123))
        report["status"] = "GREEN"
        report["scope"] = "One fresh actual native source packet through the existing query; derived mutations grant strict-decoder credit only"
    except Exception as error:
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
