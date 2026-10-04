"""Close existing exact-commit official CI observations without more API calls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

OUT = Path(r"C:/workspace/ck3_lyd_runtime_20261004/ci-closed-01b4dda3-001")
COMMIT = "01b4dda39505929c1245de699e67862f4130a02e"
TREE = "a86935a77eb31d70e7c95ba5ae564e0fb66f3d9a"


def record(path):
    data = path.read_bytes()
    return {"path": path.relative_to(OUT).as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write_new(name, data):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    observations = sorted((OUT / "observations").glob("*/report.json"))
    assert observations
    report = json.loads(observations[-1].read_text(encoding="utf-8"))
    assert report["commit"] == COMMIT and report["lyd_tree"] == TREE and report["all_terminal"]
    for path in observations:
        index_path = path.parent / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        for entry in index["files"]:
            actual = record(path.parent / entry["path"])
            assert actual["bytes"] == entry["bytes"] and actual["sha256"] == entry["sha256"]
    history = [{"report": record(path), "status": json.loads(path.read_text())["status"]} for path in observations]
    write_new("FINAL-CI-RECEIPT.json", {
        "schema": "ck3.lyd.exact01b4dda3-ci-closed.v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "commit": COMMIT, "lyd_tree": TREE,
        "terminal_observation": record(observations[-1]), "runs": report["runs"], "all_success": report["all_success"],
        "history": history, "all_observation_hashes_verified": True,
        "l0_status": "OFFICIAL_L0_SUCCESS" if report["all_success"] else "OFFICIAL_L0_TERMINAL_NON_SUCCESS",
        "live_acceptance": "NOT_COVERED", "github_triggered": False, "workflow_retried": False,
        "tracked_written": False, "game_called": False, "network_calls_in_finalization": 0,
    })
    with (OUT / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("# Exact I2 official CI closure\n\n")
        stream.write(f"Commit `{COMMIT}`; LYD source tree `{TREE}`. The final fresh official GitHub API observation establishes both required official workflows and their jobs in terminal state.\n\n")
        for run in report["runs"]:
            stream.write(f"- [{run['workflow_name']}]({run['url']}): `{run['status']} / {run['conclusion']}`; exact head `{run['head_sha']}`.\n")
            for job in run["jobs"]:
                stream.write(f"  - [{job['name']} job {job['id']}]({job['html_url']}): `{job['status']} / {job['conclusion']}`, completed `{job['completed_at']}`.\n")
        stream.write("\n[Final receipt](FINAL-CI-RECEIPT.json) links each preserved observation and its exact hash. Raw run listings, job listings, HTTP response headers/receipts, reused helper bytes, and exact-commit workflow/tree git object receipts are retained under observations. The first LYD job-detail TLS timeout remains an environment query failure; subsequent terminal evidence does not rewrite it.\n\n")
        stream.write("This is official L0 CI evidence only. It gives no CK3/native build or product live acceptance credit. No workflow trigger, rerun, game call, or tracked edit occurred.\n")
    source = Path(__file__).resolve()
    (OUT / "finalize-source.py").write_bytes(source.read_bytes())
    paths = sorted(path for path in OUT.rglob("*") if path.is_file())
    write_new("index.json", {"schema": "ck3.lyd.exact01b4dda3-ci-final-index.v1",
                             "files": [record(path) for path in paths], "self_boundary": "index excludes itself"})
    files = [path for path in OUT.rglob("*") if path.is_file()]
    print(json.dumps({"directory": str(OUT), "files": len(files), "bytes": sum(path.stat().st_size for path in files),
                      "receipt": record(OUT / "FINAL-CI-RECEIPT.json"), "index": record(OUT / "index.json"),
                      "all_success": report["all_success"]}))


if __name__ == "__main__":
    main()
