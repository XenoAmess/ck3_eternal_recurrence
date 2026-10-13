"""Guard the production cold-start dependency for the common Sway end observer.

The execution installer creates the shared observer session. The common-end
recorder binds that session once, so its setup must follow the execution install.
This source check does not install hooks or establish runtime qualification.
"""

from pathlib import Path
import unittest


class SwayCommonEndStartupOrder12004Test(unittest.TestCase):
    def test_execution_session_precedes_common_end_configuration(self) -> None:
        bridge_path = (
            Path(__file__).resolve().parents[2]
            / "native_bridge"
            / "src"
            / "Bridge.cpp"
        )
        source = bridge_path.read_text(encoding="utf-8-sig")
        common_declaration = source.index(
            "SwayCommonTerminationCallsiteObserver12004Environment"
        )
        branch_start = source.rfind(
            "#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)",
            0,
            common_declaration,
        )
        self.assertGreaterEqual(branch_start, 0)
        branch_end = source.index("#endif", common_declaration)
        startup = source[branch_start:branch_end]

        execution = "InstallSwayCompletionExecution12004("
        common = "BuildSwayCommonTerminationObserverEnvironment12004("
        attach = "SetCommonNativeEndObserverAttached12004("
        termination = "InstallSwayCompletionTermination12004("
        for call in (execution, common, attach, termination):
            self.assertEqual(startup.count(call), 1, call)
        self.assertLess(
            startup.index(execution),
            startup.index(common),
            "Execution installation must create the session before common-end "
            "configuration consumes its one-shot recorder binding.",
        )
        self.assertLess(startup.index(common), startup.index(attach))
        self.assertLess(startup.index(attach), startup.index(termination))


if __name__ == "__main__":
    unittest.main()
