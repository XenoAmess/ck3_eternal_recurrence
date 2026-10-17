"""One bounded source-only check; no run, capture, provider, media or game."""
import argparse
import ast
from datetime import datetime, timezone
from importlib import metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "src"))

from faith_power_promo.components import registry
from faith_power_promo.composer import compose
from faith_power_promo.evidence import binding, build_evidence_index
from xar_promo.pipeline import PipelineComposer
from xar_promo.pipeline_commands import handle_plan
from xar_promo.project import load_document


def command(*arguments):
    result = subprocess.run([sys.executable, "-B", *arguments], check=True,
                            capture_output=True, text=True, encoding="utf-8")
    return {"argv": [sys.executable, "-B", *arguments], "exit_code": result.returncode,
            "stdout": result.stdout.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    observed_at = datetime.now(timezone.utc).isoformat()
    machine = command(str(ROOT / "tools/ck3_live_run_id.py"), "machine")
    observer = {"machine_id": machine["stdout"], "observed_at_utc": observed_at,
                "evidence_source": "verify_authoring.py; tools/ck3_live_run_id.py machine; installed wheel direct_url.json"}
    config_path = HERE.parent / "promo-project.json"
    plan_path = HERE.parent / "pilot-plan.json"
    document = load_document(config_path)
    assert document.config.project_id == "ck3-faith-and-power"
    assert all(chapter.state == "planned" and not chapter.cues for chapter in document.config.chapters)
    index = build_evidence_index(plan_path, observer=observer)
    assert len(index["pilots"]) == 2 and len(index["claims"]) == 4
    assert not index["chains"] and not index["render_ready"]
    assert all(row["native_chain"] is None and row["raw_timecodes"] is None for row in index["pilots"])
    protocol_parameters = list(inspect.signature(PipelineComposer.__call__).parameters)[1:]
    assert list(inspect.signature(compose).parameters) == protocol_parameters
    planned_workdir = ROOT.parent / f"faith-power-source-only-no-media-{observed_at.replace(':', '').replace('.', '')}"
    assert not planned_workdir.exists()
    outcome = handle_plan(config_path, workdir=planned_workdir, registry=registry(), composer=compose)
    assert outcome.exit_status == 2 and outcome.failure and "No native run" in outcome.failure.message
    assert not planned_workdir.exists()
    try:
        compose(document.config, None, config_path=config_path, run_path=None,
                workdir=planned_workdir, adapter_factory=lambda: None,
                preset_factory=lambda: None, validate_only=False)
    except ValueError as error:
        assert "only source planning" in str(error)
    else:
        raise AssertionError("Unqualified media build should have been rejected")
    python_sources = sorted(HERE.rglob("*.py"))
    for source in python_sources:
        ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
    distribution = metadata.distribution("xar-promo-toolchain")
    direct_url = json.loads(distribution.read_text("direct_url.json"))
    assert distribution.version == "0.3.0"
    assert direct_url["archive_info"]["hashes"]["sha256"] == "f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c"
    receipt = {
        "schema": "ck3-faith-power-source-only-verification-v1", **observer,
        "status": "PASS-source-authoring-only; CAPTURE_PENDING; RENDER_UNQUALIFIED",
        "python": {"executable": sys.executable, "version": sys.version},
        "toolchain": {"installed_version": distribution.version, "direct_url": direct_url,
                      "commands": [command("-m", "xar_promo", "--version"),
                                   command("-m", "xar_promo", "--help"),
                                   command("-m", "xar_promo", "plan", "--help"),
                                   command("-m", "xar_promo", "start-run", "--help"),
                                   command("-m", "xar_promo", "preserve", "--help"),
                                   command("-m", "xar_promo", "validate", "--help")]},
        "project_config": binding(config_path), "pilot_plan": binding(plan_path),
        "source_only_index": index,
        "composer": {"installed_protocol_signature_matches": True,
                     "unbound_plan_exit_status": outcome.exit_status,
                     "unbound_plan_diagnostic": outcome.failure.message,
                     "build_guard_verified": True, "workdir_created": False,
                     "bound_capture_plan_exercised": False},
        "python_sources": [binding(path) for path in python_sources],
        "production_run_created": False, "recording_performed": False,
        "tts_invoked": False, "media_rendered": False, "business_result_verified": False,
        "human_1x_review_performed": False,
    }
    encoded = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.receipt:
        with args.receipt.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
    print(json.dumps({"status": receipt["status"], **observer,
                      "receipt": None if not args.receipt else str(args.receipt.resolve()),
                      "pilot_count": len(index["pilots"]), "claim_count": len(index["claims"]),
                      "toolchain_version": distribution.version,
                      "expected_unbound_composer_status": outcome.exit_status,
                      "created_media_or_run": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
