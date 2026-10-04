"""Official API HTTP fallback for exact598 runs/jobs; no credentials or mutations."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path("C:/workspace/ck3_lyd_runtime_20261004")
COMMIT = "598d7aee3159ee386fe6190b114efd500095395f"
API = "https://api.github.com/repos/XenoAmess/ck3_eternal_recurrence"


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
    requests = []
    def get(name, url):
        start = datetime.now(timezone.utc).isoformat()
        row = {"name": name, "url": url, "method": "GET", "started_at_utc": start, "transport": "Python313 stdlib urllib HTTPS GET", "authenticated": False}
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "CK3-LYD-readonly-evidence", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
            with urllib.request.urlopen(request, timeout=25) as response:
                raw = response.read()
                row.update(http_status=response.status, response_headers=dict(response.headers.items()), final_url=response.url)
            (out / (name + ".raw.json")).write_bytes(raw)
            row.update(status="HTTP_READ_SUCCEEDED", path=name + ".raw.json", bytes=len(raw), sha256=digest(out / (name + ".raw.json")))
            data = json.loads(raw)
        except Exception as exc:
            data = None
            row.update(status="ENVIRONMENT_HTTP_QUERY_FAILED", exception_type=type(exc).__name__, message=str(exc))
        row["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        (out / (name + ".request-receipt.json")).write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return row, data
    record, listing = get("all-runs", API + "/actions/runs?head_sha=" + COMMIT + "&per_page=100")
    requests.append(record)
    summaries = []
    if listing is not None:
        runs = listing["workflow_runs"]
        if listing["total_count"] > 100 or any(row["head_sha"] != COMMIT for row in runs):
            raise ValueError("exact commit complete run listing required")
        def jobs(run):
            record, data = get("jobs-" + str(run["id"]), API + "/actions/runs/" + str(run["id"]) + "/jobs?per_page=100")
            return run, record, data
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs_records = list(pool.map(jobs, runs))
        for run, record, data in jobs_records:
            requests.append(record)
            if data is not None and data["total_count"] > 100:
                raise ValueError("complete jobs listing required")
            summaries.append({"id": run["id"], "workflow_name": run["name"], "head_sha": run["head_sha"], "status": run["status"], "conclusion": run["conclusion"], "url": run["html_url"], "path": run["path"],
                              "jobs": [{key: row.get(key) for key in ("id", "name", "status", "conclusion", "started_at", "completed_at", "html_url", "head_sha")} for row in data["jobs"]] if data is not None else None})
    failures = [row for row in requests if row["status"] != "HTTP_READ_SUCCEEDED"]
    terminal = bool(summaries) and not failures and all(row["status"] == "completed" and row["jobs"] and all(job["status"] == "completed" and job["head_sha"] == COMMIT for job in row["jobs"]) for row in summaries)
    prior_roots = [ROOT / "ci-readonly-598d7aee-001", ROOT / "ci-readonly-598d7aee-jobs-001", ROOT / "ci-readonly-598d7aee-jobs-002"]
    prior = [{"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)} for directory in prior_roots for path in sorted(directory.glob("*")) if path.is_file()]
    sources = []
    for source in (Path(__file__).resolve(), ROOT / "ci_jobs_588492d_readonly.py", ROOT / "ci_jobs_598d7aee_readonly.py"):
        target = out / "source" / source.name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(source.read_bytes())
        sources.append({"path": target.relative_to(out).as_posix(), "sha256": digest(target), "bytes": target.stat().st_size, "original": str(source)})
    report = {"schema": "ck3.lyd.exact598-ci-closed-http-receipt.v1", "commit": COMMIT, "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "runs": summaries,
              "status": "ALL_OFFICIAL_RUNS_AND_JOBS_TERMINAL" if terminal else "ENVIRONMENT_QUERY_FAILED" if failures else "OFFICIAL_RUNS_PENDING", "all_terminal": terminal,
              "requests": requests, "previous_exact_query_artifacts": prior, "source_helpers": sources, "github_triggered": False, "workflow_retried": False, "tracked_written": False, "game_called": False,
              "boundary": "Exact official GitHub API GET results; L0 job states are separate from all product/CK3 live acceptance."}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = [{"path": path.relative_to(out).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)} for path in sorted(out.rglob("*")) if path.is_file()]
    (out / "index.json").write_text(json.dumps({"schema": "ck3.lyd.ci-closed-receipt-index.v1", "files": index, "self_boundary": "index excludes itself"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out / "report.json"), "report_sha256": digest(out / "report.json"), "index_sha256": digest(out / "index.json"), "status": report["status"], "runs": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
