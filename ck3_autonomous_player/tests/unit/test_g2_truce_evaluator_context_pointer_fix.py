from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "native_bridge" / "src" / "ck3_11906.cpp"
OBSERVER = ROOT / "native_bridge" / "src" / "raiktor_surrender_truce_v1.cpp"
FIXTURE = ROOT / "native_bridge" / "src" / "raiktor_surrender_truce_v1_test.cpp"
CMAKE = ROOT / "native_bridge" / "CMakeLists.txt"


class G2TruceEvaluatorContextPointerFixTests(unittest.TestCase):
    def test_private_adapter_loads_pointer_and_default_keeps_old_path(self) -> None:
        source = BRIDGE.read_text(encoding="utf-8")
        private_begin = source.index(
            "#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)",
            source.index("bool ReadRaiktorSurrenderTruceDuration("),
        )
        private_end = source.index("#endif", private_begin)
        block = source[private_begin:private_end]
        self.assertIn("LoadAt<void *>(effect_context, 0x28)", block)
        self.assertIn("if (evaluation_context == nullptr)", block)
        self.assertIn("DestroyWarEffectContext(bindings, effect_context)", block)
        self.assertIn(
            "static_cast<std::byte *>(effect_context) + 0x28", block
        )
        request = source.index(
            "const RaiktorSurrenderTruceRequestV1 request{",
            private_end,
        )
        self.assertIn(
            "effect_context, evaluation_context",
            source[request : request + 140],
        )

    def test_private_observer_accepts_only_non_null_opaque_context(self) -> None:
        source = OBSERVER.read_text(encoding="utf-8")
        validation = source[
            source.index("if (access.read_frame == nullptr") :
            source.index("RaiktorSurrenderTruceFrameV1 first;")
        ]
        self.assertIn("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1", validation)
        self.assertIn("request.evaluation_context == nullptr", validation)
        self.assertIn(
            "request.evaluation_context !=\n"
            "          reinterpret_cast<void *>(effect_context + 0x28)",
            validation,
        )

    def test_fixture_covers_null_no_go_and_stable_double_return(self) -> None:
        source = FIXTURE.read_text(encoding="utf-8")
        self.assertIn(
            "Store(effect_context, 0x28,\n"
            "          static_cast<void *>(evaluation_context.data()))",
            source,
        )
        self.assertIn("\"null evaluation context\"", source)
        self.assertIn("fixture.evaluator_calls != 0", source)
        self.assertIn("fixture.evaluator_boundary_count != 0", source)
        self.assertIn("capture.evaluator_first_days != 1825", source)
        self.assertIn("capture.evaluator_second_days != 1825", source)
        self.assertIn("fixture.evaluator_boundary_count != 3", source)
        self.assertIn('fixture.evaluator_boundaries[0].stage != "pre_call"', source)
        self.assertIn('fixture.evaluator_boundaries[1].stage != "post_call_1"', source)
        self.assertIn('fixture.evaluator_boundaries[2].stage != "post_call_2"', source)

    def test_private_build_option_remains_off_by_default(self) -> None:
        source = CMAKE.read_text(encoding="utf-8")
        option = source[
            source.index("XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1") :
            source.index(")", source.index("XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1"))
        ]
        self.assertTrue(option.rstrip().endswith("OFF"))


if __name__ == "__main__":
    unittest.main()
