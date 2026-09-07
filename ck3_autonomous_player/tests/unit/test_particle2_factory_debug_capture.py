from __future__ import annotations

import struct
import unittest
from pathlib import Path


AUTOPLAYER_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AUTOPLAYER_ROOT.parent
SOURCE = (
    AUTOPLAYER_ROOT
    / "native_bridge"
    / "research"
    / "particle2_factory_debug_capture.cpp"
)
CK3_EXE = REPO_ROOT / "Crusader Kings III" / "binaries" / "ck3.exe"
CMAKE = AUTOPLAYER_ROOT / "native_bridge" / "CMakeLists.txt"


EXPECTED_ANCHORS = {
    0x39C70A1: bytes.fromhex("E87A180C00"),
    0x3A86700: bytes.fromhex("4D85FF75084C8931E9FF"),
    0x3AAE920: bytes.fromhex("48895C241848894C2408"),
    0x3AAE9A8: bytes.fromhex("4C392E0F85D0020000"),
    0x3BE2340: bytes.fromhex("4055565741544155"),
    0x3BE23AE: bytes.fromhex("4881FA000200007335"),
    0x3BE23FA: bytes.fromhex("4885C00F84D5000000"),
    0x3BE2403: bytes.fromhex("4889384C8D6808"),
    0x3BE242E: bytes.fromhex("84C00F8480000000"),
    0x3BE2439: bytes.fromhex("4885DB7478"),
    0x3BE245A: bytes.fromhex("85C07555488D4528"),
    0x3BE1CE0: bytes.fromhex("48895C240848896C2410"),
    0x3BE1DE8: bytes.fromhex("80B8F9000000000F85EB000000"),
    0x3BFDC60: bytes.fromhex("4055415641574883EC20"),
    0x3BFDD25: bytes.fromhex("4885C0742345"),
    0x3BFDD38: bytes.fromhex("48837BF800"),
    0x3BE1E57: bytes.fromhex("4D85F674220F104424"),
    0x3BE2480: bytes.fromhex("85C074298B8598000000"),
    0x3BE24A8: bytes.fromhex("83F8017406488B5B30"),
    0x3BE24B6: bytes.fromhex("4584E47508"),
    0x3AAE9C1: bytes.fromhex("4885C00F84B7020000"),
    0x3A86761: bytes.fromhex("C744243002000000"),
    0x3A867A8: bytes.fromhex("4C8BE04885C07510"),
    0x3A8E080: bytes.fromhex("48895C24084889742418"),
    0x3A8E0C9: bytes.fromhex("C744243001000000"),
    0x3AD4C30: bytes.fromhex("48895C240848896C2418"),
    0x3B1C436: bytes.fromhex("4D85F60F8434090000"),
    0x3B1C479: bytes.fromhex("49837F10000F84E5070000"),
    0x3B1C4BE: bytes.fromhex("84C00F8447080000"),
    0x3B06F77: bytes.fromhex("48833E000F854B010000"),
    0x3B06F92: bytes.fromhex("FF5008"),
    0x3B06F95: bytes.fromhex("488B0848C70000000000"),
    0x3B07007: bytes.fromhex("488B064885C00F84"),
    0x3B1C501: bytes.fromhex("4D85F60F84A4070000"),
    0x3AD4DEC: bytes.fromhex("84C00F8506010000"),
    0x3AD4F05: bytes.fromhex("498BC6"),
    0x3A8E0ED: bytes.fromhex("488B084C8938488B1F"),
    0x3A867E4: bytes.fromhex("9048837D7F0075"),
    0x39C70A6: bytes.fromhex("488B4598498BF7"),
}


def _rva_offset(image: bytes, rva: int) -> int:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe : pe + 4] != b"PE\0\0":
        raise AssertionError("not a PE image")
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    section = pe + 24 + optional_size
    for index in range(section_count):
        offset = section + index * 40
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<IIII", image, offset + 8
        )
        if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
            return raw_pointer + (rva - virtual_address)
    raise AssertionError(f"RVA not mapped: 0x{rva:X}")


class Particle2FactoryDebugCaptureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_private_debugger_has_exact_tuple_and_state_chain(self) -> None:
        for token in (
            "CREATE_SUSPENDED",
            "DebugActiveProcess(process_info.dwProcessId)",
            "ResumeThread(process_info.hThread)",
            "kExpectedAttachEventSuspendCount = 2",
            "kEntryRva = 0x39C70A1",
            "kGraphicsRva = 0x3A86700",
            "kSourceEntryRva = 0x3AAE920",
            "kSourceCacheResultRva = 0x3AAE9A8",
            "kResolverEntryRva = 0x3BE2340",
            "kResolverSizeRva = 0x3BE23AE",
            "kResolverHeapResultRva = 0x3BE23FA",
            "kResolverBufferReadyRva = 0x3BE2403",
            "kResolverNormalizeResultRva = 0x3BE242E",
            "kResolverListHeadRva = 0x3BE2439",
            "kResolverCandidatePrimaryResultRva = 0x3BE245A",
            "kResolverCandidateSecondaryEntryRva = 0x3BE1CE0",
            "kResolverCandidateSecondaryStateRva = 0x3BE1DE8",
            "kResolverCandidateBackendCallbackEntryRva = 0x3BFDC60",
            "kResolverCandidateBackendPathResultRva = 0x3BFDD25",
            "kResolverCandidateBackendReadResultRva = 0x3BFDD38",
            "kResolverCandidateCallbackResultRva = 0x3BE1E57",
            "kResolverCandidateSecondaryResultRva = 0x3BE2480",
            "kResolverCandidateFinalResultRva = 0x3BE24A8",
            "kResolverSearchResultRva = 0x3BE24B6",
            "kSourceResolverResultRva = 0x3AAE9C1",
            "kSourceRva = 0x3A86761",
            "kVariantRva = 0x3A867A8",
            "kBackendEntryRva = 0x3A8E080",
            "kBackendCacheResultRva = 0x3A8E0C9",
            "kBackendCallbackEntryRva = 0x3AD4C30",
            "kBackendInitializerGlobalsRva = 0x3B1C436",
            "kBackendStageLoopRva = 0x3B1C479",
            "kBackendHlslResultRva = 0x3B1C4BE",
            "kBackendShaderCacheResultRva = 0x3B06F77",
            "kBackendShaderVcallEntryRva = 0x3B06F92",
            "kBackendShaderVcallResultRva = 0x3B06F95",
            "kBackendShaderGetterResultRva = 0x3B07007",
            "kBackendShaderResultRva = 0x3B1C501",
            "kBackendInitializerResultRva = 0x3AD4DEC",
            "kBackendCallbackOutputRva = 0x3AD4F05",
            "kBackendVcallResultRva = 0x3A8E0ED",
            "kBackendRva = 0x3A867E4",
            "kReturnRva = 0x39C70A6",
            'kExpectedSource[] = "gfx/FX/cw/particle2.shader"',
            'kExpectedVariant[] = "ParticleTexture"',
            "context.Rcx == context.Rbp - 0x68",
            "context.R14 + 0xA8",
            "context.Rbp + 0x77",
            "context.Rbp + 0x7F",
            "context.Rsi == capture.source_function_output_address",
            "context.Rbx == capture.source_function_view",
            "capture.source_cache_output",
            "capture.resolver_total_buffer_bytes",
            "capture.resolver_normalize_ok",
            "capture.resolver_list_head",
            "capture.resolver_search_output = context.R14",
            "CandidateRejected",
            "CandidateSelected",
            "candidate.secondary_state_f9",
            "candidate.backend_path_text",
            "candidate.backend_read_result",
            "candidate.secondary_callback_result_type_observed",
            "candidate.secondary_callback_result_type",
            "capture.source_resolver_output = context.Rax",
            "capture.backend_variant_confirm = context.R12",
            "capture.backend_cache_output",
            "capture.backend_initializer_resource_global",
            "capture.backend_initializer_graphics_global",
            "current.shader_vcall_output",
            "ClassifyBackendDetail",
            "capture.backend_vcall_output",
        ):
            self.assertIn(token, self.source)

    def test_target_code_and_data_are_never_patched(self) -> None:
        for forbidden in (
            "WriteProcessMemory",
            "VirtualProtect",
            "VirtualAlloc",
            "CreateRemoteThread",
            "LoadLibraryW",
            "XarCk3Bridge",
        ):
            self.assertNotIn(forbidden, self.source)
        self.assertIn("SetThreadContext", self.source)
        self.assertIn("context.Dr0 = address", self.source)
        self.assertIn("context.Dr7 = 1", self.source)

    def test_exact_build_and_durable_artifact_contract(self) -> None:
        self.assertRegex(self.source, r"kExpectedExeSize\s*=\s*95206008")
        self.assertIn(
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            self.source,
        )
        self.assertIn("output and output.tmp must be fresh", self.source)
        self.assertIn("MOVEFILE_WRITE_THROUGH", self.source)
        self.assertIn("FlushFileBuffers", self.source)
        self.assertIn("JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE", self.source)
        self.assertIn('\\"input_sent\\": false', self.source)
        self.assertIn('capture.reason = "cleanup-proof-incomplete"', self.source)
        self.assertIn("output parent must exist before launch", self.source)
        self.assertIn("DebugSetProcessKillOnExit(FALSE)", self.source)
        self.assertNotIn("DebugActiveProcessStop", self.source)
        self.assertIn('\\"policy\\": \\"terminate-after-capture\\"', self.source)
        self.assertIn("capture.diagnostic_termination_requested", self.source)
        self.assertIn("capture.native_continuation_claimed", self.source)
        self.assertIn("capture.exit_event_observed &&", self.source)
        self.assertIn("WaitForSingleObject(process_info.hProcess, 5000)", self.source)
        self.assertIn("capture.capture_event_continued", self.source)
        self.assertIn("std::vector<char> buffer(1 << 20)", self.source)
        self.assertNotIn("std::array<char, 1 << 20>", self.source)
        self.assertIn("self-test exact executable hash: GREEN", self.source)

    def test_state_machine_and_owned_stop_fail_closed(self) -> None:
        for token in (
            "NextAfterGraphics",
            "NextAfterSourceCache",
            "NextAfterResolverSize",
            "NextAfterResolverHeap",
            "NextAfterResolverNormalize",
            "NextAfterSource",
            "NextAfterVariant",
            "TargetRvaForStage",
            'capture.reason = "unexpected-owned-hardware-breakpoint"',
            'capture.reason = "debug-register-clear-failed"',
            'capture.reason = "capture-event-continue-failed"',
            'capture.reason = "source-detail-cross-check-failed"',
        ):
            self.assertIn(token, self.source)

    def test_private_self_test_is_wired_into_ctest(self) -> None:
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn("add_executable(xar_ck3_particle2_factory_debug_capture", cmake)
        self.assertIn(
            "xar_ck3_native_bridge_particle2_factory_debug_capture_self_test",
            cmake,
        )
        self.assertIn("xar_ck3_particle2_factory_debug_capture --self-test", cmake)

    def test_all_failure_classes_are_explicit(self) -> None:
        for classification in (
            "graphics-global-null",
            "source-lookup-null",
            "source-cache-hit",
            "source-resolver-null",
            "source-resolver-nonnull",
            "resolver-scratch-allocation-null",
            "resolver-path-preprocess-rejected",
            "resolver-registry-empty",
            "resolver-candidates-all-reject",
            "resolver-candidate-accepted",
            "variant-lookup-null",
            "backend-creation-null",
            "backend-initializer-global-null",
            "backend-hlsl-generation-null",
            "backend-shader-vcall-null",
            "backend-shader-acquisition-null",
            "backend-initializer-success",
            "all-nonnull",
            "unclassified",
        ):
            self.assertIn(classification, self.source)

    @unittest.skipUnless(CK3_EXE.is_file(), "exact CK3 executable is local-only")
    def test_frozen_executable_anchors(self) -> None:
        image = CK3_EXE.read_bytes()
        self.assertEqual(len(image), 95_206_008)
        for rva, expected in EXPECTED_ANCHORS.items():
            offset = _rva_offset(image, rva)
            self.assertEqual(image[offset : offset + len(expected)], expected)


if __name__ == "__main__":
    unittest.main()
