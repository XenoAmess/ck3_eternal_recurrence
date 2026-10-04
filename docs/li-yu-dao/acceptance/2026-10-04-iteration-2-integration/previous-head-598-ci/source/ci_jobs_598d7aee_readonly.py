"""Fresh exact-commit official GitHub runs/jobs; read-only external evidence."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path("C:/workspace/ck3_lyd_runtime_20261004")
REPO = "XenoAmess/ck3_eternal_recurrence"
COMMIT = "598d7aee3159ee386fe6190b114efd500095395f"


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", default=COMMIT)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--watch-run", type=int)
    args = parser.parse_args()
    if args.commit != COMMIT:
        raise ValueError("this helper is frozen to the requested exact598d7aee commit")
    output = args.output.resolve()
    if ROOT.resolve() not in output.parents:
        raise ValueError("output must remain in external task tree")
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    commands = []
    def command(name, argv, *, timeout=30):
        completed = subprocess.run(argv, capture_output=True, timeout=timeout, check=False, stdin=subprocess.DEVNULL)
        paths = {}
        for kind, data in (("stdout", completed.stdout), ("stderr", completed.stderr)):
            path = output / (name + "." + kind + ".txt")
            path.write_bytes(data)
            paths[kind] = {"path": path.name, "bytes": len(data), "sha256": sha(path)}
        record = {"name": name, "argv": argv, "returncode": completed.returncode, **paths}
        if completed.returncode == 0 and completed.stdout.strip():
            record["json"] = json.loads(completed.stdout.decode("utf-8-sig"))
        return record

    if args.watch_run:
        # gh watch reads remote state; it does not request or rerun a workflow.
        argv = ["gh", "run", "watch", str(args.watch_run), "--repo", REPO, "--interval", "60", "--exit-status"]
        (output / "watch.argv.json").write_text(json.dumps(argv, indent=2) + "\n", encoding="utf-8")
        with (output / "watch.stdout.txt").open("xb") as stdout, (output / "watch.stderr.txt").open("xb") as stderr:
            completed = subprocess.run(argv, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, check=False)
        commands.append({"name": "watch", "argv": argv, "returncode": completed.returncode,
                         "stdout": {"path": "watch.stdout.txt", "bytes": (output / "watch.stdout.txt").stat().st_size, "sha256": sha(output / "watch.stdout.txt")},
                         "stderr": {"path": "watch.stderr.txt", "bytes": (output / "watch.stderr.txt").stat().st_size, "sha256": sha(output / "watch.stderr.txt")}})
    all_runs = command("all-runs", ["gh", "api", "repos/" + REPO + "/actions/runs?head_sha=" + args.commit + "&per_page=100"])
    commands.append(all_runs)
    if all_runs["returncode"] != 0:
        (output / "report.json").write_text(json.dumps({"schema": "ck3.lyd.exact598d7aee-ci-query-failure.v1", "started_at_utc": started,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "commit": args.commit, "commands": commands,
            "status": "ENVIRONMENT_QUERY_FAILED_CI_STATE_UNKNOWN", "github_triggered": False, "tracked_written": False, "game_called": False}, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("official run API read failed; raw stdout/stderr retained")
    runs = all_runs["json"]["workflow_runs"]
    if all_runs["json"]["total_count"] > 100 or any(row["head_sha"] != args.commit for row in runs):
        raise ValueError("exact commit run query must be complete and identity-correct")
    def jobs(row):
        return command("jobs-" + str(row["id"]), ["gh", "run", "view", str(row["id"]), "--repo", REPO,
                       "--json", "databaseId,headSha,status,conclusion,url,workflowName,jobs"])
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(jobs, runs))
    commands.extend(records)
    summaries = []
    for record in records:
        if record["returncode"] != 0:
            raise RuntimeError("official jobs read failed; original read outputs retained")
        row = record["json"]
        if row["headSha"] != args.commit:
            raise ValueError("actual run head differs from requested commit")
        summaries.append({key: row[key] for key in ("databaseId", "headSha", "status", "conclusion", "url", "workflowName")}
                         | {"jobs": [{key: job.get(key) for key in ("databaseId", "name", "status", "conclusion", "startedAt", "completedAt", "url")} for job in row["jobs"]]})
    sources = []
    for source in (Path(__file__).resolve(), ROOT / "ci_jobs_588492d_readonly.py"):
        data = source.read_bytes()
        target = output / "source" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        sources.append({"original_path": str(source), "path": target.relative_to(output).as_posix(), "bytes": len(data), "sha256": sha(target)})
    prior = ROOT / "ci-readonly-598d7aee-001"
    prior_refs = [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path), "boundary": "root's earlier query preserved unchanged; may include pending states"} for path in sorted(prior.glob("*")) if path.is_file()]
    all_terminal = bool(summaries) and all(row["status"] == "completed" and all(job["status"] == "completed" for job in row["jobs"]) for row in summaries)
    report = {"schema": "ck3.lyd.exact598d7aee-ci-jobs-readonly.v1", "started_at_utc": started, "queried_at_utc": datetime.now(timezone.utc).isoformat(), "commit": args.commit,
              "all_runs_and_jobs_terminal": all_terminal, "status": "ALL_OFFICIAL_RUNS_TERMINAL" if all_terminal else "OFFICIAL_RUNS_PENDING", "run_summaries": summaries,
              "commands": commands, "source_helpers": sources, "earlier_root_queries": prior_refs,
              "read_only": {"github_triggered": False, "workflow_retried": False, "checkout_mutated": False, "tracked_written": False, "game_called": False},
              "boundary": "Remote official GitHub run/job state for exact commit only. L0 success is not CK3/live acceptance; run name and each job outcome retained separately."}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = [{"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)} for path in sorted(output.rglob("*")) if path.is_file()]
    (output / "index.json").write_text(json.dumps({"schema": "ck3.lyd.ci-readonly-hash-index.v1", "files": index, "self_boundary": "index excludes itself"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output / "report.json"), "report_sha256": sha(output / "report.json"), "index_sha256": sha(output / "index.json"),
                      "status": report["status"], "runs": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
