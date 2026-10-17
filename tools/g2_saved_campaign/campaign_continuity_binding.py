"""Bind a newly loaded feeder to its own campaign without writing the ledger."""
from pathlib import Path


def bind_campaign_continuity(
    feeder, *, campaign_root, runtime_root, sdk_prefix, launch, ledger_state,
    first_control_sequence, validate_first_control, game_binding,
):
    """Validate the existing FULL first, then bind the exact current Game ledger.

    ``validate_first_control`` is the existing request prevalidator. The caller
    supplies the official ``game_binding`` function. Neither callback submits a
    game action. The normal ledger transition still checks frame and counters.
    Only the newly loaded feeder module is changed; no file or ledger is written.
    """
    if type(first_control_sequence) is not int or first_control_sequence < 1:
        raise ValueError("actual first control sequence required")
    validate_first_control(first_control_sequence)
    campaign = Path(campaign_root).resolve()
    runtime = Path(runtime_root).resolve()
    if (runtime.parent != campaign or not isinstance(sdk_prefix, str)
            or not sdk_prefix.startswith("p") or not sdk_prefix[1:].isdigit()
            or Path(feeder.N).resolve() != runtime
            or Path(feeder.Q).resolve() != runtime / (sdk_prefix + "-queue")):
        raise ValueError("feeder runtime and explicit campaign binding differ")
    if not isinstance(launch, dict) or not isinstance(ledger_state, dict):
        raise ValueError("actual Game launch and existing campaign ledger required")
    expected = game_binding(launch)
    if (not isinstance(expected, dict) or set(expected) != {"pid", "creation_date"}
            or type(expected.get("pid")) is not int or expected["pid"] < 1
            or not isinstance(expected.get("creation_date"), str) or not expected["creation_date"]
            or ledger_state.get("game_binding") != expected):
        raise ValueError("campaign ledger and actual Game generation differ")
    ledger_path = campaign / "ROOT-CONTINUITY-WINDOW.json"
    feeder.CONTINUITY_WINDOW = ledger_path
    return ledger_path
