"""Verify reviewed CK3 1.20.0.2 migration modules against an EXE on disk.

This combines the actual per-domain ABI manifests. It reads the frozen PE once,
then checks native signatures, virtual tables, decoded instruction operands,
logical function spans and the constants used by the migrated C++ readers.
It does not discover a process, attach to CK3 or execute any native game code.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage, integer, occurrences


HERE = Path(__file__).resolve().parent
NATIVE_ROOT = HERE.parent
DEFAULT_INDEX = HERE / "ck3_1_20_0_2_migration_index.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalized_instruction(value: str) -> str:
    return " ".join(value.lower().split())


def constant_initializer(source: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*([^;]+);", source)
    if match is None:
        return None
    return re.sub(r"//[^\n]*", "", match[1]).strip()


def numeric_initializer(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None
    value = re.sub(r"(?:[uUlL]+)$", "", value.strip()).replace("'", "")
    try:
        return int(value, 0)
    except ValueError:
        return None


class OfflineVerifier:
    def __init__(self, exe: Path) -> None:
        self.data = exe.read_bytes()
        self.image = PeImage(self.data)
        self.sha256 = hashlib.sha256(self.data).hexdigest().upper()
        self.decoder = Cs(CS_ARCH_X86, CS_MODE_64)
        self.decoder.detail = True
        self.signature_cache: dict[bytes, list[int]] = {}

    def bytes_at(self, rva: int, count: int) -> bytes:
        offset = self.image.rva_to_offset(rva)
        return self.data[offset:offset + count]

    def verify_build(self, manifest: dict[str, Any]) -> tuple[list[str], int]:
        expected = manifest.get("build", {})
        wanted_sha = expected.get("sha256", manifest.get(
            "ck3_exe_sha256", manifest.get("executable_sha256")))
        failures = []
        count = 1
        if wanted_sha is None or self.sha256 != wanted_sha.upper():
            failures.append(f"executable SHA differs: expected {wanted_sha}, found {self.sha256}")
        actual = {"file_size": len(self.data), "pe_timestamp": self.image.timestamp,
                  "image_base": self.image.image_base,
                  "size_of_image": self.image.size_of_image}
        for name, value in actual.items():
            if name in expected:
                count += 1
                if value != integer(expected[name]):
                    failures.append(f"build {name} differs: expected {expected[name]}, found {value}")
        return failures, count

    def verify_instruction(self, check: dict[str, Any]) -> list[str]:
        rva = integer(check["rva"])
        label = check.get("purpose", check.get("meaning", check.get("name", hex(rva))))
        expected_bytes = bytes.fromhex(check["bytes"])
        failures = []
        if self.bytes_at(rva, len(expected_bytes)) != expected_bytes:
            return [f"instruction bytes differ: {label} at {hex(rva)}"]
        instruction = next(self.decoder.disasm(self.bytes_at(rva, 15), rva), None)
        if instruction is None:
            return [f"instruction cannot be decoded: {label} at {hex(rva)}"]
        if "instruction" in check:
            actual = normalized_instruction(f"{instruction.mnemonic} {instruction.op_str}")
            if actual != normalized_instruction(check["instruction"]):
                failures.append(f"instruction operands differ: {label}; found {actual}")
        if "rip_targets" in check:
            actual_targets = [instruction.address + instruction.size + operand.mem.disp
                              for operand in instruction.operands
                              if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP]
            if actual_targets != [integer(value) for value in check["rip_targets"]]:
                failures.append(f"instruction RIP target differs: {label}")
        return failures

    def verify_constants(self, source_file: str, constants: dict[str, Any]) -> list[str]:
        source = (NATIVE_ROOT / source_file).read_text(encoding="utf-8-sig")
        failures = []
        for name, expected in constants.items():
            actual = constant_initializer(source, name)
            expected_integer = numeric_initializer(expected)
            if actual is None:
                failures.append(f"source constant missing: {source_file}:{name}")
            elif expected_integer is not None:
                if numeric_initializer(actual) != expected_integer:
                    failures.append(f"source constant differs: {source_file}:{name}; found {actual}")
            elif " ".join(actual.split()) != " ".join(str(expected).split()):
                failures.append(f"source initializer differs: {source_file}:{name}; found {actual}")
        return failures

    def verify_module(self, entry: dict[str, Any]) -> dict[str, Any]:
        manifest_path = HERE / entry["manifest"]
        manifest = read_json(manifest_path)
        failures, build_count = self.verify_build(manifest)
        counts: Counter[str] = Counter({"build_identity": build_count})
        for anchor in manifest.get("signature_anchors", []):
            counts["unique_signatures"] += 1
            needle = bytes.fromhex(anchor["pattern"])
            if needle not in self.signature_cache:
                self.signature_cache[needle] = occurrences(self.data, needle)
            matches = self.signature_cache[needle]
            if len(matches) != 1:
                failures.append(f"signature {anchor['name']}: expected one match, found {len(matches)}")
            elif self.image.offset_to_rva(matches[0]) != integer(anchor["rva"]):
                failures.append(f"signature RVA differs: {anchor['name']}")
        for table in manifest.get("vtable_prefixes", []) + manifest.get("vtable_anchors", []):
            counts["vtable_prefixes"] += 1
            rva = integer(table["rva"])
            expected = [integer(value) for value in table["function_rvas"]]
            raw = self.bytes_at(rva, len(expected) * 8)
            actual = [struct.unpack_from("<Q", raw, index * 8)[0] - self.image.image_base
                      for index in range(len(expected))]
            if actual != expected:
                failures.append(f"vtable prefix differs: {table['name']} at {hex(rva)}")
        for field in ("semantic_checks", "instruction_checks", "instruction_evidence"):
            for check in manifest.get(field, []):
                counts["decoded_instructions"] += 1
                failures.extend(self.verify_instruction(check))
        for check in entry.get("extra_semantic_checks", []):
            counts["decoded_instructions"] += 1
            failures.extend(self.verify_instruction(check))
        ranges = manifest.get("logical_function_ranges", []) + manifest.get(
            "source_contract", {}).get("exact_function_spans", [])
        for function in ranges:
            counts["logical_function_spans"] += 1
            start = integer(function["start_rva"])
            end = integer(function["end_rva"])
            actual = hashlib.sha256(self.bytes_at(start, end - start)).hexdigest().upper()
            if actual != function["sha256"].upper():
                failures.append(f"logical function span differs: {function['name']}")
        for check in manifest.get("data_checks", []):
            counts["native_data"] += 1
            raw = self.bytes_at(integer(check["rva"]), struct.calcsize(check["format"]))
            actual = struct.unpack(check["format"], raw)[0]
            if actual != check["value"]:
                failures.append(f"native data differs: {check['purpose']}")
        for key in manifest.get("define_keys", []):
            counts["native_define_keys"] += 1
            expected_key = key["key"].encode("ascii") + b"\0"
            if self.bytes_at(integer(key["rva"]), len(expected_key)) != expected_key:
                failures.append(f"compiled define key differs: {key['key']}")
        if "feature_registry" in manifest:
            enum_rva = integer(manifest["source_constants"]["kLoadedFeatureEnumTableRva"])
            for feature in manifest["feature_registry"]:
                counts["native_feature_records"] += 1
                identifier, pointer = struct.unpack("<QQ", self.bytes_at(
                    integer(feature["compiled_record_rva"]), 16))
                key_rva = integer(feature["key_string_rva"])
                expected_key = feature["key"].encode("ascii") + b"\0"
                enum_identifier = struct.unpack("<I", self.bytes_at(
                    enum_rva + feature["native_index"] * 4, 4))[0]
                if (identifier != integer(feature["cstring_id"]) or
                        pointer - self.image.image_base != key_rva or
                        self.bytes_at(key_rva, len(expected_key)) != expected_key or
                        enum_identifier != identifier):
                    failures.append(f"compiled feature record differs: {feature['key']}")
            if entry.get("feature_definition_source_file"):
                source = (NATIVE_ROOT / entry["feature_definition_source_file"]).read_text(
                    encoding="utf-8-sig")
                block = re.search(r"\bkFeatureDefinitions\s*\{\{(.*?)\}\};", source, re.S)
                actual = [] if block is None else [
                    (int(identifier, 0), key) for identifier, key in re.findall(
                        r'\{\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\}', block[1])]
                expected = [(integer(feature["cstring_id"]), feature["key"])
                            for feature in manifest["feature_registry"]]
                counts["source_feature_records"] += len(expected)
                if actual != expected:
                    failures.append("migrated feature definitions differ from the native registry order")
        checked_groups: set[str] = set()
        for group in entry.get("constant_groups", []):
            field = group["field"]
            checked_groups.add(field)
            constants = manifest.get(field, {})
            counts["source_constants"] += len(constants)
            failures.extend(self.verify_constants(group["file"], constants))
        # Some domain manifests name their own source files or provide a
        # source-file -> constants map. Preserve that schema directly.
        for field, file_field in (("source_constants", "source_constants_file"),
                                  ("layout_constants", "layout_constants_file"),
                                  ("source_layout_constants", "source_layout_constants_file")):
            constants = manifest.get(field, {})
            if field in checked_groups or not constants:
                continue
            if all(isinstance(value, dict) for value in constants.values()):
                for source_file, group in constants.items():
                    counts["source_constants"] += len(group)
                    failures.extend(self.verify_constants(source_file, group))
            else:
                source_file = manifest.get(file_field, manifest.get("source_header"))
                if source_file is None:
                    failures.append(f"index does not name source file for {field}")
                else:
                    counts["source_constants"] += len(constants)
                    failures.extend(self.verify_constants(source_file, constants))
        for source_file, constants in entry.get("additional_source_constants", {}).items():
            counts["source_constants"] += len(constants)
            failures.extend(self.verify_constants(source_file, constants))
        binding_file = entry.get("binding_source_file", manifest.get("source_bindings_file"))
        binding_rvas = dict(manifest.get("binding_rvas", manifest.get("source_binding_rvas", {})))
        binding_rvas.update(entry.get("additional_binding_rvas", {}))
        if binding_file and binding_rvas:
            source = (NATIVE_ROOT / binding_file).read_text(encoding="utf-8-sig")
            for member, expected in binding_rvas.items():
                counts["source_binding_rvas"] += 1
                escaped = re.escape(member)
                assignment = re.search(
                    rf"\b\w+\.{escaped}\s*=(?!=)\s*([^;]+);", source)
                assigned_rva = None if assignment is None else re.search(
                    r"\b(?:base|image_base)\s*\+\s*(0x[0-9A-Fa-f]+)", assignment[1])
                macro = re.search(
                    rf"\bXAR_\w+_BIND\(\s*{escaped}\s*,\s*(0x[0-9A-Fa-f]+)\s*\)", source)
                actual = assigned_rva or macro
                if actual is None or int(actual[1], 0) != integer(expected):
                    failures.append(f"native source binding RVA differs: {member}")
        for literal in entry.get("source_literals", []):
            counts["source_literals"] += 1
            source = (NATIVE_ROOT / literal["file"]).read_text(encoding="utf-8-sig")
            if literal["value"] not in source:
                failures.append(f"source literal differs: {literal['file']}:{literal['value']}")
        # Hashes in a domain manifest freeze its reviewed implementation.
        # A domain listing source paths without hashes remains a path inventory.
        if isinstance(manifest.get("source_files"), dict):
            for source_file, expected in manifest["source_files"].items():
                counts["source_file_hashes"] += 1
                source_bytes = (NATIVE_ROOT / source_file).read_bytes()
                if entry.get("source_hash_policy") == "git-lf-with-bom":
                    source_bytes = source_bytes.replace(b"\r\n", b"\n")
                    expected = entry["source_git_lf_sha256"][source_file]
                actual = hashlib.sha256(source_bytes).hexdigest().upper()
                if actual != expected.upper():
                    failures.append(f"reviewed source file hash differs: {source_file}")
        return {"id": entry["id"], "manifest": entry["manifest"],
                "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "status": "RED" if failures else "GREEN", "checks": dict(counts),
                "readiness": manifest.get("readiness", "research"),
                "source_hash_policy": entry.get("source_hash_policy", "domain raw bytes"),
                "live_verified": manifest.get("live_verified", False), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--module", action="append", help="Check only the named indexed module")
    parser.add_argument("--output", type=Path, help="Write a machine-readable static verification result")
    args = parser.parse_args()
    index = read_json(args.index)
    verifier = OfflineVerifier(args.exe)
    if verifier.sha256 != index["executable_sha256"].upper():
        print("FAIL executable SHA does not match the migration index", file=sys.stderr)
        return 1
    modules = [entry for entry in index["modules"]
               if args.module is None or entry["id"] in args.module]
    if args.module is not None and set(args.module) - {entry["id"] for entry in modules}:
        parser.error("--module names an entry not present in the migration index")
    results = []
    for entry in modules:
        try:
            result = verifier.verify_module(entry)
        except (OSError, ValueError, TypeError, KeyError, struct.error) as error:
            result = {"id": entry["id"], "manifest": entry["manifest"], "status": "RED",
                      "checks": {}, "failures": [f"cannot verify module: {error}"]}
        results.append(result)
        print(f"{result['status']} {entry['id']}: " + ", ".join(
            f"{name}={count}" for name, count in result["checks"].items()))
        for failure in result["failures"]:
            print(f"  FAIL {failure}")
    totals: Counter[str] = Counter()
    for result in results:
        totals.update(result["checks"])
    failed = any(result["status"] != "GREEN" for result in results)
    report = {"schema_version": 1, "status": "RED" if failed else "GREEN",
              "executable_sha256": verifier.sha256, "modules_checked": len(results),
              "checks": dict(totals), "live_validation_executed": False,
              "native_functions_executed": False,
              "count_scope": "Manifest check records; shared native evidence can occur in multiple modules.",
              "unindexed_domains": index.get("unindexed_domains", []), "modules": results}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status']} offline migration ABI: {len(results)} modules; "
          "disk/static checks only, no live validation")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
