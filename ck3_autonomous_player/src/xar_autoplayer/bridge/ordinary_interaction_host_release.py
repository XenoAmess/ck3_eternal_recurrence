"""Host-only next-intent permits from a pinned ROOT readback verifier.

No MCP tool registers this API. A permit records operator-verified provenance
for one new intent. It neither retries an old request nor grants business PASS.
ROOT must provision an immutable verifier registry/bundle; no verifier is
trusted by default. Timeout evidence remains explicitly distinct from a native
command receipt.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import struct


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _closed(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{name} must be a closed object")
    return value


def _read_ref(ref):
    _closed(ref, {"path", "sha256"}, "immutable evidence reference")
    if not isinstance(ref["path"], str) or not Path(ref["path"]).is_absolute():
        raise ValueError("evidence reference requires an absolute path")
    if not isinstance(ref["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]) is None:
        raise ValueError("evidence reference requires exact SHA-256")
    raw = Path(ref["path"]).read_bytes()
    if _sha(raw) != ref["sha256"]:
        raise ValueError("immutable evidence bytes changed")
    return raw


def _write_once(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _fact_identity(claim, manifest):
    provenance = claim.get("host_provenance")
    if (not isinstance(provenance, dict)
            or provenance.get("process_create_time") != claim["action_identity"].get("process_create_time")
            or claim["action_identity"].get("process_create_time") is None):
        raise ValueError("consumption release requires the actual host-bound process creation/profile provenance")
    if manifest["claim_request_id"] != claim["request_id"] or manifest["action_identity"] != claim["action_identity"]:
        raise ValueError("consumption evidence changed claim identity")
    packet = _read_ref(manifest["packet"])
    if len(packet) < 5 or struct.unpack("<I", packet[:4])[0] != len(packet) - 4:
        raise ValueError("claim packet is not the actual length-prefixed protocol packet")
    request = json.loads(packet[4:].decode("utf-8"))
    identity, binding = claim["action_identity"], claim["binding"]
    expected = {"request_id": claim["request_id"], "step": "initiate-character-interaction-ordinary-v1",
                "interaction_key": identity["interaction_key"], "recipient_id": identity["recipient_id"],
                "expected_player_character_id": identity["actor_id"], "expected_game_pid": identity["game_pid"],
                "expected_connection_generation": binding["connection_generation"],
                "expected_revision": binding["native_revision"]}
    for key, value in expected.items():
        if type(request.get(key)) is not type(value) or request[key] != value:
            raise ValueError(f"consumption evidence packet changed {key}")
    if manifest["native_result"] is None:
        if manifest["unknown"] is None:
            raise ValueError("timeout requires explicit host unknown evidence, never a fabricated native receipt")
        unknown = json.loads(_read_ref(manifest["unknown"]).decode("utf-8"))
        _closed(unknown, {"schema", "request_id", "claim_path", "error_type", "error", "native_result_available"}, "host unknown sidecar")
        if (unknown["schema"] != "ck3-ordinary-interaction-host-unknown-v1"
                or unknown["request_id"] != claim["request_id"] or unknown["native_result_available"] is not False):
            raise ValueError("host unknown evidence is not bound to this request")
    else:
        native = json.loads(_read_ref(manifest["native_result"]).decode("utf-8"))
        if native.get("request_id") != claim["request_id"]:
            raise ValueError("native receipt is not bound to this request")
        if manifest["unknown"] is not None:
            _read_ref(manifest["unknown"])


class OrdinaryClaimReleaseHost:
    """ROOT constructs this with its own frozen registry; public callers cannot."""
    def __init__(self, root_registry_path: Path, pinned_registry_sha256: str):
        self.registry_ref = {"path": str(root_registry_path.resolve()), "sha256": pinned_registry_sha256}
        registry = json.loads(_read_ref(self.registry_ref).decode("utf-8"))
        _closed(registry, {"schema", "verifiers"}, "ROOT verifier registry")
        if registry["schema"] != "ck3-ordinary-interaction-root-verifier-registry-v1" or not isinstance(registry["verifiers"], dict):
            raise ValueError("ROOT verifier registry is malformed")
        self.registry = registry

    def release(self, claim_path: Path, evidence_manifest_path: Path, *, verifier_id: str,
                operator_id: str, next_intent_id: str) -> Path:
        # Re-read every immutable input before using the pinned host trust seam.
        _read_ref(self.registry_ref)
        for value in (operator_id, next_intent_id):
            if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", value) is None:
                raise ValueError("operator and next intent require explicit portable identities")
        entry = self.registry["verifiers"].get(verifier_id)
        _closed(entry, {"bundle_index", "entrypoint"}, "trusted verifier entry")
        index_raw = _read_ref(entry["bundle_index"])
        index = json.loads(index_raw.decode("utf-8"))
        _closed(index, {"schema", "verifier_id", "entrypoint", "files"}, "frozen verifier bundle")
        if (index["schema"] != "ck3-ordinary-interaction-consumption-verifier-bundle-v1"
                or index["verifier_id"] != verifier_id or index["entrypoint"] != entry["entrypoint"]
                or not isinstance(index["files"], list) or not index["files"]):
            raise ValueError("verifier bundle does not match ROOT's frozen entry")
        bundle_dir = Path(entry["bundle_index"]["path"]).parent.resolve()
        files = {}
        for item in index["files"]:
            _closed(item, {"path", "sha256"}, "verifier bundle file")
            relative = Path(item["path"])
            target = (bundle_dir / relative).resolve()
            if relative.is_absolute() or bundle_dir not in target.parents or item["path"] in files:
                raise ValueError("verifier bundle paths must be unique and inside its frozen directory")
            files[item["path"]] = _read_ref({"path": str(target), "sha256": item["sha256"]})
        if not isinstance(entry["entrypoint"], str) or entry["entrypoint"].count(":") != 1:
            raise ValueError("trusted verifier entrypoint is malformed")
        filename, function_name = entry["entrypoint"].split(":")
        if filename not in files or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", function_name) is None:
            raise ValueError("trusted verifier entrypoint is absent from the frozen bundle")
        claim_bytes = claim_path.read_bytes()
        claim = json.loads(claim_bytes.decode("utf-8"))
        manifest_bytes = evidence_manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        _closed(manifest, {"schema", "claim_request_id", "action_identity", "packet", "native_result", "unknown",
                           "before_artifact", "after_artifact", "independent_report"}, "consumption manifest")
        if manifest["schema"] != "ck3-ordinary-interaction-consumption-manifest-v1":
            raise ValueError("consumption manifest schema is malformed")
        _fact_identity(claim, manifest)
        artifacts = {key: (_read_ref(manifest[key]) if manifest[key] is not None else None)
                     for key in ("packet", "native_result", "unknown", "before_artifact", "after_artifact", "independent_report")}
        # No supplied callback/lambda or boolean can cross this boundary. ROOT's
        # exact audited source parses the actual immutable observation bytes.
        namespace = {"__file__": str(bundle_dir / filename), "__name__": "_root_ordinary_consumption_verifier"}
        exec(compile(files[filename], str(bundle_dir / filename), "exec"), namespace)
        verifier = namespace.get(function_name)
        if not callable(verifier):
            raise ValueError("frozen ROOT verifier entrypoint is not callable")
        facts = verifier(claim=claim, manifest=manifest, artifacts=artifacts)
        _closed(facts, {"schema", "claim_request_id", "action_identity", "packet_sha256", "native_result_sha256",
                        "unknown_sha256", "before_artifact_sha256", "after_artifact_sha256", "consumption"}, "independent consumption facts")
        if facts != json.loads(artifacts["independent_report"].decode("utf-8")):
            raise ValueError("frozen verifier output differs from the preserved independent report")
        expected = {"schema": "ck3-ordinary-interaction-independent-consumption-v1",
                    "claim_request_id": claim["request_id"], "action_identity": claim["action_identity"],
                    **{key + "_sha256": (manifest[key]["sha256"] if manifest[key] is not None else None)
                       for key in ("packet", "native_result", "unknown", "before_artifact", "after_artifact")}}
        for key, value in expected.items():
            if type(facts.get(key)) is not type(value) or facts[key] != value:
                raise ValueError(f"independent consumption facts changed {key}")
        consumption = facts["consumption"]
        if not isinstance(consumption, dict):
            raise ValueError("independent consumption facts lack a typed observation")
        if consumption.get("kind") == "event_instance":
            _closed(consumption, {"kind", "before_instance_id", "after_instance_id", "event_definition_key", "source_key", "root_character_id"}, "event consumption facts")
            if (type(consumption["after_instance_id"]) is not int or consumption["after_instance_id"] <= 0
                    or consumption["after_instance_id"] == consumption["before_instance_id"]
                    or type(consumption["root_character_id"]) is not int
                    or consumption["root_character_id"] != claim["action_identity"]["actor_id"]
                    or not isinstance(consumption["event_definition_key"], str)
                    or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[0-9]+", consumption["event_definition_key"]) is None
                    or consumption["source_key"] != consumption["event_definition_key"]):
                raise ValueError("event consumption facts lack a new source/root-bound actual instance")
        elif consumption.get("kind") == "save_round_delta":
            _closed(consumption, {"kind", "field_name", "before_value", "after_value", "actor_id", "recipient_id", "interaction_key"}, "save consumption facts")
            identity = claim["action_identity"]
            if (not isinstance(consumption["field_name"], str) or not consumption["field_name"]
                    or type(consumption["before_value"]) not in (int, str, type(None))
                    or type(consumption["after_value"]) not in (int, str)
                    or consumption["before_value"] == consumption["after_value"]
                    or any(type(consumption[key]) is not type(identity[key]) or consumption[key] != identity[key]
                           for key in ("actor_id", "recipient_id", "interaction_key"))):
                raise ValueError("save consumption facts lack a bound actual round/nonce delta")
        else:
            raise ValueError("ACK, CanSend, absent incoming interaction, or arbitrary assertions do not prove consumption")
        # Evidence is checked again after verifier execution to prevent mutable
        # bytes from being silently reinterpreted during a release.
        _read_ref(self.registry_ref)
        for ref in (entry["bundle_index"], *[manifest[key] for key in artifacts if manifest[key] is not None]):
            _read_ref(ref)
        for item in index["files"]:
            _read_ref({"path": str(bundle_dir / item["path"]), "sha256": item["sha256"]})
        if claim_path.read_bytes() != claim_bytes or evidence_manifest_path.read_bytes() != manifest_bytes:
            raise ValueError("claim or consumption manifest changed during host verification")
        permit = claim_path.with_suffix(".release.json")
        _write_once(permit, {"schema": "ck3-ordinary-interaction-next-intent-permit-v1",
            "claim_path": str(claim_path), "claim_sha256": _sha(claim_bytes),
            "claim_request_id": claim["request_id"], "action_identity": claim["action_identity"],
            "old_connection_generation": claim["binding"]["connection_generation"],
            "manifest": {"path": str(evidence_manifest_path.resolve()), "sha256": _sha(manifest_bytes)},
            "registry": self.registry_ref, "verifier_id": verifier_id, "verifier_bundle": entry["bundle_index"],
            "operator_id": operator_id, "next_intent_id": next_intent_id,
            "released_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "operator_verified_consumption_for_one_new_intent", "business_acceptance_credit": False})
        return permit


def consume_next_intent_permit(previous_claim_path: Path, identity: dict, next_binding: dict, request_id: str) -> dict:
    """Consume before the next claim/send. A crash never restores this permit."""
    permit_path = previous_claim_path.with_suffix(".release.json")
    permit_bytes = permit_path.read_bytes()
    permit = json.loads(permit_bytes.decode("utf-8"))
    _closed(permit, {"schema", "claim_path", "claim_sha256", "claim_request_id", "action_identity",
        "old_connection_generation", "manifest", "registry", "verifier_id", "verifier_bundle",
        "operator_id", "next_intent_id", "released_at_utc", "scope", "business_acceptance_credit"}, "next-intent permit")
    previous_raw = previous_claim_path.read_bytes()
    previous = json.loads(previous_raw.decode("utf-8"))
    if (permit["schema"] != "ck3-ordinary-interaction-next-intent-permit-v1"
            or permit["claim_path"] != str(previous_claim_path) or permit["claim_sha256"] != _sha(previous_raw)
            or permit["claim_request_id"] != previous["request_id"] or request_id == previous["request_id"]
            or permit["action_identity"] != identity or previous["action_identity"] != identity
            or permit["old_connection_generation"] != previous["binding"]["connection_generation"]
            or permit["scope"] != "operator_verified_consumption_for_one_new_intent"
            or permit["business_acceptance_credit"] is not False):
        raise ValueError("next-intent permit does not match the old claim and new intent")
    manifest = json.loads(_read_ref(permit["manifest"]).decode("utf-8"))
    _fact_identity(previous, manifest)
    for key in ("before_artifact", "after_artifact", "independent_report"):
        _read_ref(manifest[key])
    _read_ref(permit["registry"])
    index = json.loads(_read_ref(permit["verifier_bundle"]).decode("utf-8"))
    bundle_dir = Path(permit["verifier_bundle"]["path"]).parent.resolve()
    for item in index["files"]:
        target = (bundle_dir / item["path"]).resolve()
        if bundle_dir not in target.parents:
            raise ValueError("verifier bundle path escaped during permit consumption")
        _read_ref({"path": str(target), "sha256": item["sha256"]})
    _write_once(permit_path.with_suffix(".consumed.json"), {"schema": "ck3-ordinary-interaction-permit-consumption-v1",
        "permit_path": str(permit_path), "permit_sha256": _sha(permit_bytes), "new_request_id": request_id,
        "next_intent_id": permit["next_intent_id"], "old_connection_generation": permit["old_connection_generation"],
        "new_connection_generation": next_binding["connection_generation"], "new_binding": next_binding,
        "action_identity": identity, "business_acceptance_credit": False})
    return {"permit_path": str(permit_path), "permit_sha256": _sha(permit_bytes),
            "next_intent_id": permit["next_intent_id"], "parent_claim_path": str(previous_claim_path),
            "parent_claim_sha256": _sha(previous_raw)}
