"""Portable pure recipe and linked-byte guard tests; no compiler or Game I/O."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import producer


class RecipeTests(unittest.TestCase):
    def compile_args(self, name: str) -> list[str]:
        args = ["cl.exe", "/DXAR_CK3_ENABLE_NATIVE_TIME_OBSERVER31=1", "/I" + str(producer.PREP / "include"), "/c", producer.old_source(name), "/Fo" + str(producer.OLD / "obj" / ("native31-" + name + ".obj")), "/Fd" + str(producer.OLD / "obj" / ("native31-" + name + ".pdb"))]
        if name == "bridge":
            args.extend(("-DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1", "-DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1"))
        return args

    def link_args(self) -> list[str]:
        # Existing direct bridge was already replaced in Native31's sealed RSP.
        args = [str(Path("D:/old") / (str(i) + ".obj")) for i in range(335)]
        args.extend(str(producer.OLD / "obj" / ("native31-" + name + ".obj")) for name in producer.TU_NAMES)
        args.extend(("D:/old/protocol.lib", "D:/old/runtime.lib", "kernel32.lib", "/DLL", "/INCREMENTAL:NO", "/MANIFEST:EMBED"))
        args.extend(prefix + str(producer.OLD / "bin" / ("xar_ck3_bridge" + suffix)) for prefix, suffix in (("/OUT:", ".dll"), ("/IMPLIB:", ".lib"), ("/MAP:", ".map")))
        args.append("/PDB:" + str(producer.OLD / "bin/xar_ck3_bridge.pdb"))
        return args

    def test_all_four_sources_first_include_and_overlay(self) -> None:
        for name in producer.TU_NAMES:
            with self.subTest(name=name):
                old = self.compile_args(name)
                result = producer.adapt_compile(name, old, producer.ROOT)
                self.assertEqual(result.source, producer.SOURCE_PINS[name][0])
                self.assertEqual(result.object_cap, producer.OBJECT_CAPS[producer.TU_NAMES.index(name)])
                self.assertLess(result.argv.index("/I" + str(producer.N32 / "native/include")), result.argv.index("/I" + str(producer.PREP / "include")))
                self.assertIn("/DXAR_CK3_ENABLE_NATIVE_TIME_OBSERVER31=1", result.argv)
                self.assertEqual(len(result.argv), len(old) + 1)

    def test_missing_duplicate_wrong_tu_and_debug_rejected(self) -> None:
        base = self.compile_args("commands")
        mutations = [base[:-1], base + [base[-1]], base + ["/Zi"], base + ["-DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1"]]
        for args in mutations:
            with self.subTest(args=args), self.assertRaises(ValueError):
                producer.adapt_compile("commands", args, producer.ROOT)
        with self.assertRaises(ValueError):
            producer.adapt_compile("unknown", base, producer.ROOT)

    def test_link_preserves_335_objects_two_archives_and_library_order(self) -> None:
        old = self.link_args()
        result, reused = producer.adapt_link(old, producer.ROOT)
        self.assertEqual(len(reused), 337)
        self.assertEqual([str(x) for x in reused], old[:335] + [str(Path("D:/old/protocol.lib")), str(Path("D:/old/runtime.lib"))])
        self.assertEqual(result[-1], "/DEBUG:NONE")
        self.assertFalse(any(x.startswith("/PDB:") for x in result))
        for name in producer.TU_NAMES:
            self.assertEqual(result.count(str(producer.ROOT / "obj" / ("native32-" + name + ".obj"))), 1)
        self.assertLess(result.index("D:/old/protocol.lib"), result.index("D:/old/runtime.lib"))

    def test_link_missing_duplicate_force_and_changed_output_rejected(self) -> None:
        base = self.link_args()
        variants = [base[1:], base + [base[0]], base + ["/FORCE"], base + ["/WHOLEARCHIVE:x.lib"], ["/OUT:D:/unexpected.dll" if x.startswith("/OUT:") else x for x in base]]
        for args in variants:
            with self.subTest(args=args), self.assertRaises(ValueError):
                producer.adapt_link(args, producer.ROOT)

    def test_json_wrong_types_bool_and_empty(self) -> None:
        values: tuple[object, ...] = (None, True, 1, {}, ["ok", 1])
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                producer.string_list(value)
        self.assertEqual(producer.string_list([]), [])
        with self.assertRaises(ValueError):
            producer.object_map({1: "wrong"})

    def test_exact_execution_scope_rejects_bool_missing_extra_and_other_source(self) -> None:
        scope: dict[str, object] = {
            "schema": "xar.native32.offline-production-execution/v1", "machine_id": producer.MACHINE,
            "status": "ADMITTED", "owner": "Root", "build_root": str(producer.ROOT),
            "plan_sha256": "a" * 64, "producer_sha256": "b" * 64,
            "phase_hard_bytes": producer.HARD, "review_at_utc": producer.DEADLINE.isoformat(),
            "root_direct_execution_release": True, "four_TUs_sequential": True,
            "Game_calls_allowed": False, "DLL_loads_allowed": False, "deployment_allowed": False,
        }
        value = {"Native32_production_execution": scope}
        self.assertEqual(producer.validate_admission(value, "a" * 64, "b" * 64), scope)
        variants = [{**scope, "phase_hard_bytes": True}, {**scope, "root_direct_execution_release": 1}, {**scope, "unknown": False}, {**scope, "plan_sha256": "c" * 64}, {k: v for k, v in scope.items() if k != "DLL_loads_allowed"}]
        for item in variants:
            with self.subTest(item=item), self.assertRaises(ValueError):
                producer.validate_admission({"Native32_production_execution": item}, "a" * 64, "b" * 64)

    def test_pinned_identity_cannot_be_rebased_after_hashing(self) -> None:
        item = producer.FilePin(path="D:/source.obj", bytes=30, sha256="a" * 64, device="1", file_id="2", mtime_ns="4")
        expected = (1, 2, 30, 4)
        with patch.object(producer, "identity", return_value=expected):
            before = producer.pinned_input_identities([item])
        self.assertEqual(before, {Path(item["path"]): expected})
        with patch.object(producer, "identity", return_value=(1, 2, 31, 5)), self.assertRaises(ValueError):
            producer.pinned_input_identities([item])
        self.assertEqual(before, {Path(item["path"]): expected})

    def test_unknown_schema_helpers_do_not_execute(self) -> None:
        spec = importlib.util.spec_from_file_location("native32_import_only", Path(producer.__file__))
        self.assertIsNotNone(spec)
        if spec is None or spec.loader is None:
            self.fail("module loader unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        with patch.object(Path, "open", side_effect=AssertionError("import performed file open")), patch("subprocess.Popen", side_effect=AssertionError("import executed a child")):
            spec.loader.exec_module(module)

    def synthetic_link(self) -> tuple[bytes, bytes, str]:
        names = ["?" + name + "@time_observer31@fixture" for name in ("ForwardExecute", "ForwardAppend", "Enter", "DiagnosticFrame")] + ["?target@fixture"]
        strings = bytearray(b"\0\0\0\0")
        symbol_names: list[bytes] = []
        for name in names:
            symbol_names.append(b"\0" * 4 + struct.pack("<I", len(strings)))
            strings.extend(name.encode() + b"\0")
        struct.pack_into("<I", strings, 0, len(strings))
        obj = bytearray(512)
        raw_base, rel_base, sym_base = 180, 212, 252
        struct.pack_into("<HHIIIHH", obj, 0, 0x8664, 4, 0, sym_base, 5, 0, 0)
        image = bytearray(2048)
        struct.pack_into("<I", image, 60, 128)
        struct.pack_into("<H", image, 134, 1)
        struct.pack_into("<H", image, 148, 240)
        struct.pack_into("<Q", image, 176, 0x180000000)
        struct.pack_into("<IIII", image, 400, 1024, 4096, 1024, 512)
        lines: list[str] = []
        for index in range(4):
            struct.pack_into("<8sIIIIIIHHI", obj, 20 + index * 40, b".text\0\0\0", 0, 0, 8, raw_base + index * 8, rel_base + index * 10, 0, 1, 0, 0x60000020)
            obj[raw_base + index * 8:raw_base + (index + 1) * 8] = b"\xe8\0\0\0\0\xc3\x90\x90"
            struct.pack_into("<IIH", obj, rel_base + index * 10, 1, 4, 4)
            struct.pack_into("<8sIhHBB", obj, sym_base + index * 18, symbol_names[index], 0, index + 1, 0x20, 2, 0)
            rva = 4096 + index * 16
            at = 512 + index * 16
            image[at:at + 8] = b"\xe8" + struct.pack("<i", 4352 - (rva + 5)) + b"\xc3\x90\x90"
            lines.append(f" 0001:00000000 {names[index]} {0x180000000 + rva:016x} f fixture.obj")
        struct.pack_into("<8sIhHBB", obj, sym_base + 72, symbol_names[4], 0, 0, 0x20, 2, 0)
        obj[sym_base + 90:sym_base + 90 + len(strings)] = strings
        lines.append(f" 0001:00000100 {names[4]} {0x180000000 + 4352:016x} f fixture.obj")
        return bytes(obj), bytes(image), "\n".join(lines)

    def test_actual_coff_decoder_checks_bytes_and_relocation_destinations(self) -> None:
        obj, image, text = self.synthetic_link()
        def read(path: Path) -> bytes:
            return obj if path.name == "core.obj" else image
        with patch.object(Path, "read_bytes", read):
            proof = producer.core_link_proof(Path("core.obj"), Path("test.dll"), text)
        self.assertEqual(len(proof), 4)
        self.assertTrue(all(item["verified_target_relocations"] == 1 for item in proof))
        for position in (517, 513):
            damaged = bytearray(image)
            damaged[position] ^= 1
            def bad_read(path: Path) -> bytes:
                return obj if path.name == "core.obj" else bytes(damaged)
            with self.subTest(position=position), patch.object(Path, "read_bytes", bad_read), self.assertRaises(ValueError):
                producer.core_link_proof(Path("core.obj"), Path("test.dll"), text)


if __name__ == "__main__":
    unittest.main()
