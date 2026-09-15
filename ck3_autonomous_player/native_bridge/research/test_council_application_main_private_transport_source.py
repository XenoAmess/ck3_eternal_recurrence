#!/usr/bin/env python3
"""Check the controlled Council transport cannot advertise or submit by default."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPTION = "XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def main() -> int:
    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8-sig")
    bridge = (ROOT / "src/bridge.cpp").read_text(encoding="utf-8")
    transport = (
        ROOT / "src/council_application_main_private_transport_v1.cpp"
    ).read_text(encoding="utf-8")
    adapter = (ROOT / "src/game_adapter.cpp").read_text(encoding="utf-8")

    require(
        f'{OPTION}\n  "Enable the unadvertised Council application-main controlled acceptance transport"\n  OFF'
        in cmake,
        "private candidate option is not default OFF",
    )
    require(f"#if defined({OPTION})" in bridge, "worker route is not gated")
    require(
        "IsCouncilApplicationMainPrivateStepV1(step)" in bridge,
        "private worker admission is missing",
    )
    require(
        "ConfigureCouncilApplicationMainPrivateTransportV1(" in bridge,
        "private runtime configuration is missing",
    )
    require(
        "PollCouncilApplicationMainPrivateTransportV1(" in bridge,
        "nonblocking worker poll is missing",
    )
    require(
        "SerializeCouncilApplicationMainResultEnvelopeV1" not in bridge,
        "Council worker was registered on the public bridge",
    )
    require(
        "private-query-council-composition-candidates-v1" not in adapter
        and "private-assign-councillor-v1" not in adapter
        and "game.action.assign-councillor-v1" not in adapter,
        "Council transport or action was advertised",
    )

    # The existing one-shot probe's synchronous wait caused R692 RED. The
    # candidate transport must let the application-main pump run independently.
    require(
        "WaitForMainThreadQueryV1" not in transport
        and "CancelMainThreadQueryV1" not in transport,
        "private route can block or cancel the application-main executor",
    )
    require(
        "CouncilApplicationMainActionRuntimeReadyV1(transport.shared)" in transport
        and "action_admitted && evaluate_action_gates != nullptr" in transport
        and "adapter.helper_override = nullptr" in transport,
        "private action admission or exact helper binding is incomplete",
    )
    print("Council private transport source contract GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
