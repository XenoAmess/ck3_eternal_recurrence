"""One bounded official CI log extraction; archives and credentials stay in RAM."""
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

REPO = Path(__file__).resolve().parents[2]
HEAD = "08f4757b47a4c11863a6c85b5d2cff4fbccaa0f6"
RUN = 39326816982
JOB = 118314695824
TITLE = "Test keyed query completion diagnostics without CK3"
EXCERPT = REPO / "_runtime/ci08f-step18-failed-excerpt01.txt"
PROOF = REPO / "docs/ck3-native-ai/evidence/ci08f-step18-bounded-log-download01.json"
MAX_ZIP = MAX_ENTRY = 512 * 1024
MAX_EXCERPT = 64 * 1024
MAX_PROOF = 8 * 1024
MAX_TOTAL = 96 * 1024


class Stop(Exception):
    def __init__(self, reason, **details):
        self.reason, self.details = reason, details


def require(ok, reason, **details):
    if not ok:
        raise Stop(reason, **details)


def pin(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(REPO).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def project():
    value = subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
                           timeout=10).stdout.decode().strip()
    if value.startswith("git@github.com:"):
        path = value[len("git@github.com:"):]
    else:
        parsed = urllib.parse.urlsplit(value)
        require(parsed.hostname == "github.com", "foreign_repository_host")
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path), "repository_identity")
    return path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def receive(url, token, cap, report):
    """Follow explicitly; a cross-host redirect permanently drops Authorization."""
    opener = urllib.request.build_opener(NoRedirect())
    authenticated = True
    deadline = time.monotonic() + 90
    for _ in range(5):
        require(time.monotonic() < deadline, "network_deadline")
        current = urllib.parse.urlsplit(url)
        require(current.scheme == "https" and current.hostname, "HTTPS_required")
        headers = {"User-Agent": "ck3-bounded-CI18-diagnostic-v1", "Accept-Encoding": "identity",
                   "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if authenticated:
            require(current.hostname == "api.github.com", "Authorization_host")
            headers["Authorization"] = "Bearer " + token
        try:
            response = opener.open(urllib.request.Request(url, headers=headers), timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        try:
            if response.code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                require(isinstance(location, str) and location, "missing_redirect")
                target = urllib.parse.urlsplit(urllib.parse.urljoin(url, location))
                require(target.scheme == "https" and target.hostname, "HTTPS_redirect_required")
                if target.hostname != current.hostname:
                    authenticated = False
                report["redirect_hosts"].append(target.hostname)
                url = target.geturl()
                continue
            require(response.code == 200, "HTTP_status", status=response.code)
            length = response.headers.get("Content-Length")
            if length is not None:
                require(length.isdecimal(), "invalid_Content_Length")
                length = int(length)
                require(length <= cap, "network_size_limit", advertised_bytes=length, cap_bytes=cap)
            output = io.BytesIO()
            while True:
                remaining = cap - output.tell()
                require(remaining > 0, "network_cap_reached", bytes_received=output.tell(), cap_bytes=cap)
                chunk = response.read(min(32768, remaining))
                if not chunk:
                    break
                output.write(chunk)
                require(time.monotonic() < deadline, "network_deadline")
                if length is not None and output.tell() == length:
                    break
            require(length is None or output.tell() == length, "truncated_HTTP_body")
            output.seek(0)
            return output
        finally:
            response.close()
    raise Stop("redirect_limit")


def exact_step(raw):
    with zipfile.ZipFile(raw) as archive:
        entries = archive.infolist()
        require(len(entries) <= 1024 and len({r.filename for r in entries}) == len(entries),
                "archive_structure_limit", entry_count=len(entries))
        selected = []
        for row in entries:
            name = row.filename.replace("\\", "/").rsplit("/", 1)[-1]
            match = re.fullmatch(r"([0-9]+)_(.*)\.txt", name)
            if match and match[2] == TITLE and not row.is_dir():
                selected.append(row)
        require(len(selected) == 1, "unique_step_title_required", matches=len(selected),
                archive_entry_count=len(entries))
        row = selected[0]
        require(not row.flag_bits & 1 and row.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                "unsupported_selected_entry")
        require(row.file_size <= MAX_ENTRY, "selected_entry_size_limit",
                entry_bytes=row.file_size, cap_bytes=MAX_ENTRY)
        with archive.open(row) as stream:
            body = stream.read(MAX_ENTRY)
            require(len(body) == row.file_size, "selected_entry_length")
        return body, {"basename": row.filename.replace("\\", "/").rsplit("/", 1)[-1],
                      "bytes": len(body), "compressed_bytes": row.compress_size,
                      "sha256": hashlib.sha256(body).hexdigest(), "archive_entry_count": len(entries)}


def excerpt(body):
    specific = list(re.finditer(
        rb"(?im)(fatal error [A-Z][0-9]+|error (?:[A-Z]+[0-9]+|LNK[0-9]+)|"
        rb"unresolved external|assertion failed|check failed|Traceback|CMake Error|FAILED:)", body))
    start = max(0, len(body) - MAX_EXCERPT)
    if specific and specific[-1].start() < start:
        start = max(0, specific[-1].start() - 8192)
    if start:
        boundary = body.find(b"\n", start, min(start + 4096, len(body)))
        if boundary >= 0:
            start = boundary + 1
    end = min(len(body), start + MAX_EXCERPT)
    selected = body[start:end]
    # Never retain an Authorization line or URL query if a producer logged one.
    selected, auth = re.subn(rb"(?im)(Authorization\s*:)[^\r\n]*", rb"\1 [REDACTED]", selected)
    selected, urls = re.subn(rb"https?://[^\s\"'<>?]+\?[^\s\"'<>]+",
                             b"[URL_QUERY_REDACTED]", selected)
    require(len(selected) <= MAX_EXCERPT, "excerpt_size_limit")
    return selected, {"source_start_byte": start, "source_end_byte": end,
                      "first_source_line": body[:start].count(b"\n") + 1,
                      "last_source_line": body[:end].count(b"\n") + 1,
                      "redactions": auth + urls, "selection": "last specific failure or final lines"}


def main():
    require(sys.argv[1:] == ["--execute"], "explicit_execute_required")
    require(not PROOF.exists() and not EXCERPT.exists(), "create_only_no_automatic_repeat")
    report = {"schema": "xar.bounded-ci08f-step18-log/v1",
              "machine_id": "xenoamess-full-tower-eb9d2c1186",
              "start_utc": datetime.now(timezone.utc).isoformat(),
              "head": HEAD, "run_id": RUN, "job_id": JOB, "step_number": 18,
              "step_title": TITLE, "redirect_hosts": [], "status": "FAILED_CLOSED",
              "limits": {"compressed_RAM": MAX_ZIP, "selected_entry_RAM": MAX_ENTRY,
                         "excerpt_disk": MAX_EXCERPT, "proof_disk": MAX_PROOF, "aggregate_disk": MAX_TOTAL},
              "helper": pin(Path(__file__)), "credential_or_signed_URL_retained": False,
              "storage_parent_sha256": "82cc455baee311d2b426718b144e908797dd4834c7c1a89ebd90151de9279df1",
              "storage_internal_sha256": "b511eab54787134cf0e4fadeb2a9a37e25264735a85a162e2c436f724c111c6b",
              "other_entries_inflated": 0, "whole_archive_written": False,
              "Native_Game_Task_CPP_calls": 0}
    stage = "identity"
    try:
        machine = subprocess.run([sys.executable, "-B", str(REPO/"tools/ck3_live_run_id.py"), "machine"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
                                 timeout=10).stdout.decode().strip()
        require(machine == report["machine_id"], "machine_identity")
        repository = project()
        stage = "authentication"
        credential = subprocess.run(["gh", "auth", "token", "--hostname", "github.com"],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
                                    timeout=15).stdout.strip()
        require(0 < len(credential) <= 512, "credential_size")
        token = credential.decode("ascii")
        stage = "job_metadata"
        metadata = receive(f"https://api.github.com/repos/{repository}/actions/jobs/{JOB}",
                           token, 64*1024, report)
        job = json.load(metadata)
        require(job["id"] == JOB and job["run_id"] == RUN and job["head_sha"] == HEAD
                and job["status"] == "completed" and job["conclusion"] == "failure", "job_identity")
        steps = [row for row in job["steps"] if row["number"] == 18 and row["name"] == TITLE]
        require(len(steps) == 1 and steps[0]["conclusion"] == "failure", "step_identity")
        report["step_observation"] = {key: steps[0].get(key) for key in
                                      ("number", "name", "status", "conclusion", "started_at", "completed_at")}
        stage = "archive_download"
        archive = receive(f"https://api.github.com/repos/{repository}/actions/runs/{RUN}/logs",
                          token, MAX_ZIP, report)
        token = credential = None
        report["archive_bytes"] = archive.getbuffer().nbytes
        report["archive_sha256"] = hashlib.sha256(archive.getbuffer()).hexdigest()
        stage = "unique_entry"
        body, report["selected_entry"] = exact_step(archive)
        stage = "excerpt"
        selected, report["window"] = excerpt(body)
        require(report["helper"]["bytes"] + len(selected) + MAX_PROOF <= MAX_TOTAL, "aggregate_reserve")
        with EXCERPT.open("xb") as stream:
            stream.write(selected)
        report["excerpt"] = pin(EXCERPT)
        report["status"] = "EXCERPT_RETAINED_CPP_STAGE_NOT_YET_CLASSIFIED"
    except Stop as error:
        report["failure"] = {"stage": stage, "reason": error.reason, **error.details}
    except BaseException as error:
        # Exception text can contain a signed redirect URL or a credential.
        report["failure"] = {"stage": stage, "exception_type": type(error).__name__}
    report.update(end_utc=datetime.now(timezone.utc).isoformat(),
                  producer_closed=True, future_writes=0, allocated_bytes=None)
    raw = (json.dumps(report, ensure_ascii=True, indent=2)+"\n").encode()
    require(len(raw) <= MAX_PROOF, "proof_size_limit")
    total = report["helper"]["bytes"] + (EXCERPT.stat().st_size if EXCERPT.exists() else 0) + len(raw)
    require(total <= MAX_TOTAL, "aggregate_disk_limit")
    with PROOF.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"status": report["status"], "failure": report.get("failure"),
                      "proof": pin(PROOF), "excerpt": report.get("excerpt"), "aggregate_bytes": total}))
    return 0 if report["status"].startswith("EXCERPT_RETAINED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
