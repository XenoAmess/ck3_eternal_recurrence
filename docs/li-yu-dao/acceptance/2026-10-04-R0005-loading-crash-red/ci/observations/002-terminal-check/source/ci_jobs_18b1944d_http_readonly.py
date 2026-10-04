"""Read official exact I3/I4 commit runs/jobs once; preserve raw bytes, never trigger CI."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(r"C:/workspace/ck3_lyd_runtime_20261004")
REPO = Path(r"C:/workspace/ck3_eternal_recurrence")
COMMIT = "18b1944d1784d3e4ec57189c016335ef135b9b34"
LYD_TREE = "77f74591f299874efcd20c2672f143c362e54caa"
API = "https://api.github.com/repos/XenoAmess/ck3_eternal_recurrence"
WORKFLOWS = (".github/workflows/li-yu-dao-static.yml", ".github/workflows/static-ci.yml")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if ROOT.resolve() not in out.parents:
        raise ValueError("external output only")
    out.mkdir(parents=True, exist_ok=False)
    sources = []
    for source in (Path(__file__).resolve(),):
        target = out / "source" / source.name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(source.read_bytes())
        sources.append({"path": target.relative_to(out).as_posix(), "original": str(source),
                        "bytes": target.stat().st_size, "sha256": digest(target)})
    git_receipts = []
    for name, command in (("lyd-tree", ["git", "rev-parse", COMMIT + ":mod_li_yu_dao"]),
                          *[("workflow-" + str(number), ["git", "show", COMMIT + ":" + path])
                            for number, path in enumerate(WORKFLOWS, 1)]):
        result = subprocess.run(command, cwd=REPO, capture_output=True, check=False)
        (out / (name + ".git.stdout")).write_bytes(result.stdout)
        (out / (name + ".git.stderr")).write_bytes(result.stderr)
        git_receipts.append({"command": command, "returncode": result.returncode,
                             "stdout": name + ".git.stdout", "stdout_sha256": digest(out / (name + ".git.stdout")),
                             "stderr": name + ".git.stderr", "stderr_sha256": digest(out / (name + ".git.stderr"))})
        assert result.returncode == 0
        if name == "lyd-tree":
            assert result.stdout.decode().strip() == LYD_TREE

    def get(name, url):
        row = {"name": name, "url": url, "method": "GET", "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "transport": "Python313 stdlib urllib HTTPS GET", "authenticated": False}
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "CK3-LYD-readonly-evidence",
                       "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
            with urllib.request.urlopen(request, timeout=25) as response:
                raw = response.read()
                row.update(http_status=response.status, response_headers=dict(response.headers.items()), final_url=response.url)
            path = out / (name + ".raw.json")
            path.write_bytes(raw)
            row.update(status="HTTP_READ_SUCCEEDED", path=path.name, bytes=len(raw), sha256=digest(path))
            data = json.loads(raw)
        except Exception as error:
            data = None
            row.update(status="ENVIRONMENT_HTTP_QUERY_FAILED", exception_type=type(error).__name__, message=str(error))
        row["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        (out / (name + ".request-receipt.json")).write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return row, data

    record, listing = get("all-runs", API + "/actions/runs?head_sha=" + COMMIT + "&per_page=100")
    requests = [record]
    summaries = []
    if listing is not None:
        listed_runs = listing["workflow_runs"]
        runs = [run for run in listed_runs if run["path"] in WORKFLOWS]
        assert listing["total_count"] <= 100 and all(row["head_sha"] == COMMIT for row in listed_runs)
        def jobs(run):
            receipt, data = get("jobs-" + str(run["id"]), API + "/actions/runs/" + str(run["id"]) + "/jobs?per_page=100")
            return run, receipt, data
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(jobs, runs))
        for run, receipt, data in results:
            requests.append(receipt)
            assert data is None or data["total_count"] <= 100
            summaries.append({"id": run["id"], "workflow_name": run["name"], "head_sha": run["head_sha"],
                "status": run["status"], "conclusion": run["conclusion"], "url": run["html_url"], "path": run["path"],
                "jobs": [{key: row.get(key) for key in ("id", "name", "status", "conclusion", "started_at", "completed_at", "html_url", "head_sha")}
                         for row in data["jobs"]] if data is not None else None})
    failures = [row for row in requests if row["status"] != "HTTP_READ_SUCCEEDED"]
    workflows_present = set(WORKFLOWS).issubset({row["path"] for row in summaries})
    terminal = workflows_present and not failures and all(row["status"] == "completed" and row["jobs"] and
        all(job["status"] == "completed" and job["head_sha"] == COMMIT for job in row["jobs"]) for row in summaries)
    success = terminal and all(row["conclusion"] == "success" and all(job["conclusion"] == "success" for job in row["jobs"]) for row in summaries)
    report = {"schema": "ck3.lyd.exact18b1944d-ci-readonly-receipt.v1", "commit": COMMIT, "lyd_tree": LYD_TREE,
              "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "runs": summaries, "requests": requests,
              "required_workflows_present": workflows_present, "only_required_workflows_evaluated": list(WORKFLOWS), "all_terminal": bool(terminal), "all_success": bool(success),
              "status": "OFFICIAL_L0_SUCCESS" if success else "OFFICIAL_L0_TERMINAL_NON_SUCCESS" if terminal else
                        "ENVIRONMENT_QUERY_FAILED_CI_STATE_UNKNOWN" if failures else "OFFICIAL_RUNS_PENDING",
              "source_helpers": sources, "exact_commit_git_object_receipts": git_receipts,
              "github_triggered": False, "workflow_retried": False, "tracked_written": False, "game_called": False,
              "boundary": "Only official exact-commit L0 CI runs/jobs; no product live acceptance credit."}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = [{"path": path.relative_to(out).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}
             for path in sorted(out.rglob("*")) if path.is_file()]
    (out / "index.json").write_text(json.dumps({"schema": "ck3.lyd.ci-observation-index.v1", "files": index,
         "self_boundary": "index excludes itself"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out / "report.json"), "report_sha256": digest(out / "report.json"),
          "index_sha256": digest(out / "index.json"), "status": report["status"], "runs": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
