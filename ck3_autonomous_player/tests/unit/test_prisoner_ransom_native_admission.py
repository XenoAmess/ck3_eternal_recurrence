"""The formal ransom step must pass the connected native admission gate."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "native_bridge" / "src" / "bridge.cpp"
TRANSPORT = (
    ROOT
    / "native_bridge"
    / "include"
    / "xar_bridge"
    / "player_prisoner_collection_private_transport_v1.hpp"
)
MAILBOX = ROOT / "native_bridge" / "src" / "main_thread_query_mailbox_v1.cpp"


class PrisonerRansomNativeAdmissionTest(unittest.TestCase):
    def test_formal_step_reaches_its_native_handler(self) -> None:
        bridge = BRIDGE.read_text(encoding="utf-8")
        transport = TRANSPORT.read_text(encoding="utf-8")
        admission = bridge.split("} else if (!game.supports_step(step)", 1)[1].split(
            '"unsupported native gameplay step"', 1
        )[0]
        handler = bridge.split("kPlayerPrisonerRansomSubmitPrivateStepV1) {", 1)[1]
        self.assertIn(
            '"submit-player-prisoner-ransom-private-v1"', transport
        )
        self.assertIn(
            "#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)\n"
            "                   && step != xar::ck3_11906::\n"
            "                                  kPlayerPrisonerRansomSubmitPrivateStepV1\n"
            "#endif",
            admission,
        )
        self.assertIn("ExecutePlayerPrisonerRansomPrivateSubmitV1", handler)

    def test_formal_executor_is_registered_in_the_production_mailbox(self) -> None:
        bridge = BRIDGE.read_text(encoding="utf-8")
        mailbox = MAILBOX.read_text(encoding="utf-8")
        installer = bridge.split(
            "environment.permitted_executor_triquinquagintary =", 1
        )[1].split("installed_ =", 1)[0]
        self.assertIn(
            "#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)\n"
            "    environment.permitted_executor_quattuorquinquagintary =\n"
            "        &xar::ck3_11906::ExecutePlayerPrisonerRansomPrivateSubmitV1;\n"
            "#endif",
            installer,
        )
        self.assertIn(
            "mailbox.permitted_executor_quattuorquinquagintary =\n"
            "      environment.permitted_executor_quattuorquinquagintary;",
            mailbox,
        )
        self.assertIn(
            "executor != mailbox.permitted_executor_quattuorquinquagintary",
            mailbox,
        )


if __name__ == "__main__":
    unittest.main()
