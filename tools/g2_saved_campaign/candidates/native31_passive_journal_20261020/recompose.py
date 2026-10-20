"""Recompose the preserved Native31 source in RAM; never build or deploy it."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Literal, TypedDict

SCHEMA_V1 = "xar.native31.public-source-package/v1"
FROZEN_COMMIT_V1 = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"
COMPOSER_V1 = "historical_inputs/prepare_producer.py"
CANDIDATE_V1 = "historical_inputs/candidate-package.json"
MACRO_V1 = "native/cmake/native30-runtime-source-macro-restore.cmake"


@dataclass(frozen=True)
class FilePinV1:
    name: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class BaselinePinV1:
    name: str
    blob: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class QualificationV1:
    original_producer_postcheck: Literal["FAILED"] = "FAILED"
    artifact_qualification: Literal["OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"] = "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
    clean_native_build_verified: Literal[False] = False
    runtime_admission_granted: Literal[False] = False
    game_calls_by_packaging: Literal[0] = 0


@dataclass(frozen=True)
class ManifestV1:
    machine_id: str
    observed_at_utc: str
    source_inputs: tuple[FilePinV1, ...]
    evidence_inputs: tuple[FilePinV1, ...]
    baseline_inputs: tuple[BaselinePinV1, ...]
    expected_outputs: tuple[FilePinV1, ...]
    qualification: QualificationV1


class FilePinJSONV1(TypedDict):
    name: str
    bytes: int
    sha256: str


class VerificationReportV1(TypedDict):
    machine_id: str
    observed_at_utc: str
    source_machine_id: str
    status: Literal["SOURCE_BYTES_RECOMPOSED_ONLY"]
    outputs: list[FilePinJSONV1]
    build_calls: Literal[0]
    game_calls: Literal[0]
    runtime_admission_granted: Literal[False]


SOURCE_PINS_V1 = (
    FilePinV1("historical_inputs/prepare_producer.py", 4565, "2e43be2687d498b021af8d02a511435f7fbc8afb1c9be6d4e08b6c17e3748aef"),
    FilePinV1("historical_inputs/candidate-package.json", 46983, "8db93e15993129f483febb9672c40b017f2ffca0b560124fd0955b94c332a7c3"),
    FilePinV1("historical_inputs/production_producer.py", 13210, "ef08dd9241d9f631372c5b459a8d3bdd5571606958b32838bab2f77a3a9d9451"),
    FilePinV1("native/include/xar_bridge/native_time_command_observer_12004.hpp", 4176, "f0beb8ff286bcda8854fcfe74529ae47943f67db206b8b7855d1081ec8254e11"),
    FilePinV1("native/src/native_time_command_observer_12004.cpp", 14322, "a0973832477b55bda0bc6917854fd5ec595209ab8b356f2bb07a5bd35aaaad7a"),
    FilePinV1("native/src/native_time_command_observer_12004_install.cpp", 9790, "95888a0ca45293704dedc8915edf817c5dabb12af42c93b4f536f080994ed545"),
    FilePinV1("native/tests/native31_core_test.cpp", 10331, "65c8a0b9fc798f2ce9e50273d5d1086891abb14a45304c7feb48610769ef3ffa"),
    FilePinV1("native/tests/native31_installer_fixture.cpp", 28985, "bb1913f8ef69f94b9c80af73c4ab106c8a93ade4a5a590788ccb42f5fb73ce9c"),
    FilePinV1("native/cmake/native30-runtime-source-macro-restore.cmake", 807, "e99511202bab46b24e37b9cf4b1e9d31eb6e9ce3612bf8f078dba131f05d2e02"),
    FilePinV1("cold/observer_journal_v1.py", 17063, "f77710b050f839da36c308a1da66a8aec79fa0ec8bec167100f62c688a029712"),
    FilePinV1("cold/native31_mcp_extension_v1.py", 1876, "9c56a270f8029360de26560ded0cb3f7938749684f65921b9245f30ee49004a0"),
    FilePinV1("cold/native31_source28_binding.py", 7998, "917e4f6f3e07b333b4d74099ee8f6ea16ccd0de6debf58adddc86fbe8ca2fc5a"),
    FilePinV1("cold/test_observer_journal_v1.py", 12205, "b4b78478e6038c971e19565599e87c0fd04c480f954d5b98a01575ab329b3062"),
)
EVIDENCE_PINS_V1 = (
    FilePinV1("evidence/SOURCE-RECEIPT01.json", 5453, "1379532ef4fd072d4e4330f17661dea153d8dfd8aa1a7141e9ff68070a205b10"),
    FilePinV1("evidence/SOURCE-OVERLAY-RESULT01.json", 2225, "d7d1d5eb6c1c555dc580c2f229db63a17c66770450f014b4eee77274c0e44d77"),
    FilePinV1("evidence/FAILED-production-1792513602860687000.json", 209, "bcc9d3411150497df2ead9105b9387fb54a37e9f315e24b2c0ba42635f68308f"),
    FilePinV1("evidence/PRODUCTION-RESULT01.json", 13172, "8f8a6462d34556337a73ccc29a080c29efc15e58f932b96cc3bc7f5094594957"),
    FilePinV1("evidence/POSTCHECK01.json", 25064, "c1576149a48e292c6b192cec63beb41193bc5cef964b7aabc524567d5be6238c"),
    FilePinV1("evidence/FIXTURES-RESULT01.json", 11911, "6d90f7cf29d268340c400949a70f771081b6a306811e25432b4ca46ce4c5bad3"),
    FilePinV1("evidence/QUALIFICATION02.json", 3828, "7592b69fc57e98c2e96375dcc794087489865df9d3a5ab5b70810231d77aa6b6"),
)
BASELINE_PINS_V1 = (
    BaselinePinV1("src/bridge.cpp", "f96ac18c2be47a0a6fc1ed3e8642b5a084053efb", 1605122, "975cad765a74c388cfa9dd5849d82b0dbe3091e4b6aa39273138a50279970a7e"),
    BaselinePinV1("src/ck3_12002_commands.cpp", "b6603bf6b3bb851efd25df963e44a2feb566560d", 7628, "8d5806d2b57dc8d115bc6cb52ca7e4b6374e6be4b546ab813ea3b3b889324c2a"),
    BaselinePinV1("CMakeLists.txt", "3a5b0f9506e3aacbc74879bde20486845562a82f", 453519, "abeae6aec614db664faca9dfc6fb4f115f20865fa0faf6deebee15d690e2445f"),
)
OUTPUT_PINS_V1 = (
    FilePinV1("native/src/bridge.cpp", 1606472, "661e73ca1002334e039ad234ae142937cd24f128d3399a9b0ad154adc1c11719"),
    FilePinV1("native/src/ck3_12002_commands.cpp", 8431, "d5a18e67954b215d110cc256f26b5577bb7a0c2ea46b8f0122b817a120cc5c74"),
    FilePinV1("native/CMakeLists.txt", 454163, "d60a14197e678f39854e57469e39c3623e287bb95cb62d3bf4cef954af995551"),
    FilePinV1("native/include/xar_bridge/native_time_command_observer_12004.hpp", 4176, "f0beb8ff286bcda8854fcfe74529ae47943f67db206b8b7855d1081ec8254e11"),
    FilePinV1("native/src/native_time_command_observer_12004.cpp", 14322, "a0973832477b55bda0bc6917854fd5ec595209ab8b356f2bb07a5bd35aaaad7a"),
    FilePinV1("native/src/native_time_command_observer_12004_install.cpp", 9790, "95888a0ca45293704dedc8915edf817c5dabb12af42c93b4f536f080994ed545"),
    FilePinV1("native/tests/native31_core_test.cpp", 10331, "65c8a0b9fc798f2ce9e50273d5d1086891abb14a45304c7feb48610769ef3ffa"),
    FilePinV1("native/tests/native31_installer_fixture.cpp", 28985, "bb1913f8ef69f94b9c80af73c4ab106c8a93ade4a5a590788ccb42f5fb73ce9c"),
    FilePinV1("native/cmake/native30-runtime-source-macro-restore.cmake", 807, "e99511202bab46b24e37b9cf4b1e9d31eb6e9ce3612bf8f078dba131f05d2e02"),
    FilePinV1("cold/observer_journal_v1.py", 17063, "f77710b050f839da36c308a1da66a8aec79fa0ec8bec167100f62c688a029712"),
    FilePinV1("cold/native31_mcp_extension_v1.py", 1876, "9c56a270f8029360de26560ded0cb3f7938749684f65921b9245f30ee49004a0"),
    FilePinV1("cold/native31_source28_binding.py", 7998, "917e4f6f3e07b333b4d74099ee8f6ea16ccd0de6debf58adddc86fbe8ca2fc5a"),
    FilePinV1("cold/test_observer_journal_v1.py", 12205, "b4b78478e6038c971e19565599e87c0fd04c480f954d5b98a01575ab329b3062"),
)


class MissingFrozenBaselineV1(RuntimeError):
    """A shallow clone needs its operator to obtain the immutable objects."""


def _object_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("JSON text key required")
        result[key] = item
    return result


def _fields_v1(value: object, expected: set[str]) -> dict[str, object]:
    obj = _object_v1(value)
    if set(obj) != expected:
        raise ValueError("JSON fields differ")
    return obj


def _text_v1(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("nonempty text required")
    return value


def _utc_v1(value: object) -> str:
    text = _text_v1(value)
    stamp = datetime.fromisoformat(text)
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError("explicit UTC observation time required")
    return text


def _positive_v1(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("exact positive integer required")
    return value


def _hex_v1(value: object, size: int) -> str:
    text = _text_v1(value)
    if len(text) != size or any(c not in "0123456789abcdef" for c in text):
        raise ValueError("canonical lowercase hex required")
    return text


def _name_v1(value: object) -> str:
    text = _text_v1(value)
    path = PurePosixPath(text)
    if path.is_absolute() or "\\" in text or ":" in text or str(path) != text or any(
            part in (".", "..", "") for part in text.split("/")):
        raise ValueError("canonical relative source path required")
    return text


def _file_pin_v1(value: object) -> FilePinV1:
    obj = _fields_v1(value, {"name", "bytes", "sha256"})
    return FilePinV1(_name_v1(obj["name"]), _positive_v1(obj["bytes"]),
                     _hex_v1(obj["sha256"], 64))


def _file_pins_v1(value: object) -> tuple[FilePinV1, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("nonempty JSON pin array required")
    result = tuple(_file_pin_v1(item) for item in value)
    if len({item.name for item in result}) != len(result):
        raise ValueError("duplicate file pin")
    return result


def decode_manifest_v1(raw: bytes) -> ManifestV1:
    value: object = json.loads(raw)
    obj = _fields_v1(value, {"schema", "frozen_commit", "machine_id", "observed_at_utc",
        "source_inputs", "evidence_inputs", "baseline_inputs", "expected_outputs", "qualification"})
    if obj["schema"] != SCHEMA_V1 or obj["frozen_commit"] != FROZEN_COMMIT_V1:
        raise ValueError("immutable source schema/baseline differs")
    baseline = obj["baseline_inputs"]
    if not isinstance(baseline, list) or not baseline:
        raise ValueError("nonempty baseline JSON array required")
    rows: list[BaselinePinV1] = []
    for item in baseline:
        row = _fields_v1(item, {"name", "blob", "bytes", "sha256"})
        rows.append(BaselinePinV1(_name_v1(row["name"]), _hex_v1(row["blob"], 40),
            _positive_v1(row["bytes"]), _hex_v1(row["sha256"], 64)))
    qual = _fields_v1(obj["qualification"], {"original_producer_postcheck", "artifact_qualification",
        "clean_native_build_verified", "runtime_admission_granted", "game_calls_by_packaging"})
    if (qual["original_producer_postcheck"] != "FAILED"
            or qual["artifact_qualification"] != "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
            or qual["clean_native_build_verified"] is not False
            or qual["runtime_admission_granted"] is not False
            or type(qual["game_calls_by_packaging"]) is not int or qual["game_calls_by_packaging"] != 0):
        raise ValueError("historical qualification boundary differs")
    manifest = ManifestV1(_text_v1(obj["machine_id"]), _utc_v1(obj["observed_at_utc"]),
        _file_pins_v1(obj["source_inputs"]), _file_pins_v1(obj["evidence_inputs"]),
        tuple(rows), _file_pins_v1(obj["expected_outputs"]), QualificationV1())
    if (manifest.source_inputs != SOURCE_PINS_V1 or manifest.evidence_inputs != EVIDENCE_PINS_V1
            or manifest.baseline_inputs != BASELINE_PINS_V1 or manifest.expected_outputs != OUTPUT_PINS_V1):
        raise ValueError("immutable input/output pins differ")
    return manifest


def _require_manifest_v1(manifest: ManifestV1) -> None:
    _text_v1(manifest.machine_id)
    _utc_v1(manifest.observed_at_utc)
    qual = manifest.qualification
    if (type(qual) is not QualificationV1 or qual.original_producer_postcheck != "FAILED"
            or qual.artifact_qualification != "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
            or qual.clean_native_build_verified is not False or qual.runtime_admission_granted is not False
            or type(qual.game_calls_by_packaging) is not int or qual.game_calls_by_packaging != 0):
        raise ValueError("exact historical qualification model required")
    if (manifest.source_inputs != SOURCE_PINS_V1 or manifest.evidence_inputs != EVIDENCE_PINS_V1
            or manifest.baseline_inputs != BASELINE_PINS_V1 or manifest.expected_outputs != OUTPUT_PINS_V1
            or manifest.qualification != QualificationV1()):
        raise ValueError("immutable manifest model differs")


def file_pin_json_v1(pin: FilePinV1) -> FilePinJSONV1:
    return {"name": pin.name, "bytes": pin.bytes, "sha256": pin.sha256}


def encode_manifest_v1(manifest: ManifestV1) -> bytes:
    _require_manifest_v1(manifest)
    qual = manifest.qualification
    obj: dict[str, object] = {"schema": SCHEMA_V1, "frozen_commit": FROZEN_COMMIT_V1,
        "machine_id": manifest.machine_id, "observed_at_utc": manifest.observed_at_utc,
        "source_inputs": [file_pin_json_v1(p) for p in manifest.source_inputs],
        "evidence_inputs": [file_pin_json_v1(p) for p in manifest.evidence_inputs],
        "baseline_inputs": [{"name": p.name, "blob": p.blob, "bytes": p.bytes, "sha256": p.sha256}
                            for p in manifest.baseline_inputs],
        "expected_outputs": [file_pin_json_v1(p) for p in manifest.expected_outputs],
        "qualification": {"original_producer_postcheck": qual.original_producer_postcheck,
            "artifact_qualification": qual.artifact_qualification,
            "clean_native_build_verified": qual.clean_native_build_verified,
            "runtime_admission_granted": qual.runtime_admission_granted,
            "game_calls_by_packaging": qual.game_calls_by_packaging}}
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _verified_v1(data: bytes, size: int, sha256: str) -> bytes:
    if type(data) is not bytes or len(data) != size or hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("immutable source bytes differ")
    return data


def read_verified_inputs_v1(root: Path, manifest: ManifestV1) -> dict[str, bytes]:
    _require_manifest_v1(manifest)
    base = root.resolve(strict=True)
    result: dict[str, bytes] = {}
    for pin in (*manifest.source_inputs, *manifest.evidence_inputs):
        path = (base / pin.name).resolve(strict=True)
        if base not in path.parents:
            raise ValueError("source path escaped package")
        result[pin.name] = _verified_v1(path.read_bytes(), pin.bytes, pin.sha256)
    return result


def read_git_baseline_v1(repo: Path, manifest: ManifestV1) -> dict[str, bytes]:
    _require_manifest_v1(manifest)
    result: dict[str, bytes] = {}
    for pin in manifest.baseline_inputs:
        done = subprocess.run(["git", "cat-file", "blob", pin.blob], cwd=repo,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if done.returncode != 0:
            raise MissingFrozenBaselineV1(
                "immutable Native31 Git blob unavailable: " + pin.blob
                + "; obtain commit " + FROZEN_COMMIT_V1
                + " explicitly from an authorized history source; no network or HEAD fallback is attempted")
        result[pin.name] = _verified_v1(done.stdout, pin.bytes, pin.sha256)
    return result


def _byte_map_v1(value: object) -> dict[str, bytes]:
    obj = _object_v1(value)
    result: dict[str, bytes] = {}
    for key, item in obj.items():
        if type(item) is not bytes:
            raise ValueError("legacy composer must return immutable source bytes")
        result[_name_v1(key)] = item
    return result


def recompose_source_v1(manifest: ManifestV1, baseline: Mapping[str, bytes],
                        files: Mapping[str, bytes]) -> dict[str, bytes]:
    """Pure RAM; the pinned legacy composer is the sole dynamic boundary."""
    _require_manifest_v1(manifest)
    expected = {pin.name for pin in manifest.source_inputs}
    if not expected <= set(files) or set(baseline) != {p.name for p in manifest.baseline_inputs}:
        raise ValueError("required input set differs")
    for pin in manifest.source_inputs:
        _verified_v1(files[pin.name], pin.bytes, pin.sha256)
    inputs = {pin.name: _verified_v1(baseline[pin.name], pin.bytes, pin.sha256)
              for pin in manifest.baseline_inputs}
    inputs["cmake/native30-runtime-source-macro-restore.cmake"] = files[MACRO_V1]
    package = _object_v1(json.loads(files[CANDIDATE_V1]))
    if (package.get("frozen_commit") != FROZEN_COMMIT_V1 or package.get("compiled") is not False
            or package.get("producer") != files[COMPOSER_V1].decode("utf-8")):
        raise ValueError("frozen candidate identity differs")
    leaves_obj = _object_v1(package.get("leaves"))
    leaves: dict[str, str] = {}
    for name, value in leaves_obj.items():
        leaves[_name_v1(name)] = _text_v1(value)
    namespace: dict[str, object] = {}
    # Its exact SHA/size was validated above; it imports hashlib and defines
    # composition functions only. Historical native producer is never executed.
    exec(compile(files[COMPOSER_V1], COMPOSER_V1, "exec"), namespace)
    compose: object = namespace.get("compose")
    if not callable(compose):
        raise ValueError("pinned legacy compose callable missing")
    produced: object = compose(inputs, leaves)
    generated = _byte_map_v1(produced)
    out: dict[str, bytes] = {}
    for pin in manifest.expected_outputs:
        if pin.name in files:
            data = files[pin.name]
        elif pin.name.startswith("native/"):
            data = generated[pin.name[len("native/"):]]
        else:
            raise ValueError("unsupported source output")
        out[pin.name] = _verified_v1(data, pin.bytes, pin.sha256)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        manifest = decode_manifest_v1((root / "MANIFEST.json").read_bytes())
        files = read_verified_inputs_v1(root, manifest)
        output = recompose_source_v1(manifest, read_git_baseline_v1(args.repo, manifest), files)
        helper = args.repo / "tools/ck3_live_run_id.py"
        machine = subprocess.run([sys.executable, "-B", str(helper), "machine"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True).stdout.strip()
        if not machine:
            raise ValueError("actual machine identity unavailable")
        report: VerificationReportV1 = {"machine_id": machine,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_machine_id": manifest.machine_id, "status": "SOURCE_BYTES_RECOMPOSED_ONLY",
            "outputs": [file_pin_json_v1(p) for p in manifest.expected_outputs],
            "build_calls": 0, "game_calls": 0, "runtime_admission_granted": False}
        if len(output) != len(manifest.expected_outputs):
            raise ValueError("source output count differs")
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ValueError, OSError, MissingFrozenBaselineV1, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

