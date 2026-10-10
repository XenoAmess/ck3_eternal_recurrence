"""Keep the focused serializer fixture bound to its production function."""
from pathlib import Path
import hashlib
import json


def main() -> None:
    native = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/native_bridge"
    production = (native / "src/ingame_decision_item_v1.cpp").read_text(encoding="utf-8")
    fixture = (native / "tests/keyed_query_completion_diagnostics_v1_test.cpp").read_text(encoding="utf-8")
    signature = "std::string SerializeIngameDecisionItemV1("
    start = production.index(signature)
    end = production.index("bool ExecuteIngameDecisionItemActionV1(", start)
    actual = production[start:end].strip()
    projected = fixture.split("namespace reviewed_candidate {\n", 1)[1].split("\n}}\n", 1)[0] + "\n}"
    if projected != actual:
        raise ValueError("Focused serializer fixture differs from production; refresh its exact function projection")
    print(json.dumps({"serializer_projection_matches_production": True,
                      "normalized_function_sha256": hashlib.sha256(actual.encode("utf-8")).hexdigest(),
                      "worker_or_live_qualification": False}))


if __name__ == "__main__":
    main()
