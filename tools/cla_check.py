#!/usr/bin/env python3
"""Repository-owned, per-pull-request CLA status checker.

This script runs only from the trusted default branch under pull_request_target
or issue_comment. It reads GitHub metadata; it never downloads or executes pull
request content.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / ".github" / "cla-config.json"
NOREPLY_RE = re.compile(
    r"^(?:\d+\+)?(?P<login>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))@users\.noreply\.github\.com$",
    re.IGNORECASE,
)
COAUTHOR_RE = re.compile(
    r"^Co-authored-by:\s*(?P<name>.+?)\s*<(?P<email>[^>]+)>\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class ClaCheckError(RuntimeError):
    """Raised for a configuration or GitHub API failure."""


@dataclass(frozen=True)
class Evaluation:
    passed: bool
    required_users: tuple[str, ...]
    signed_users: tuple[str, ...]
    missing_users: tuple[str, ...]
    unresolved_authors: tuple[str, ...]
    override_label: str | None = None


class GitHubApi:
    def __init__(self, repository: str, token: str, api_url: str) -> None:
        if "/" not in repository:
            raise ClaCheckError("GITHUB_REPOSITORY must be OWNER/REPO")
        self.repository = repository
        self.token = token
        self.api_url = api_url.rstrip("/")

    def request(
        self, method: str, path_or_url: str, payload: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, str]]:
        url = (
            path_or_url
            if path_or_url.startswith("https://")
            else f"{self.api_url}{path_or_url}"
        )
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "project-causality-cla-check",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data, dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise ClaCheckError(
                f"GitHub API {method} {url} failed with HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ClaCheckError(f"GitHub API {method} {url} failed: {exc}") from exc

    def get_all(self, path: str) -> list[dict[str, Any]]:
        url: str | None = f"{self.api_url}{path}"
        items: list[dict[str, Any]] = []
        while url:
            data, headers = self.request("GET", url)
            if not isinstance(data, list):
                raise ClaCheckError(f"Expected a list from {url}")
            items.extend(data)
            url = next_link(headers.get("Link", ""))
        return items


def next_link(link_header: str) -> str | None:
    for item in link_header.split(","):
        match = re.match(r'\s*<([^>]+)>;\s*rel="([^"]+)"', item)
        if match and match.group(2) == "next":
            return match.group(1)
    return None


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaCheckError(f"Cannot load {path}: {exc}") from exc

    required = {
        "version",
        "document",
        "acceptance_statement",
        "status_context",
        "comment_marker",
        "exempt_users",
        "manual_override_labels",
        "require_commit_authors",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise ClaCheckError(f"CLA config is missing keys: {', '.join(missing)}")
    if not isinstance(config["exempt_users"], list) or not isinstance(
        config["manual_override_labels"], list
    ):
        raise ClaCheckError("CLA exemption and override settings must be lists")

    document = ROOT / str(config["document"])
    try:
        document_text = document.read_text(encoding="utf-8")
    except OSError as exc:
        raise ClaCheckError(f"Cannot read CLA document {document}: {exc}") from exc
    if str(config["acceptance_statement"]) not in document_text:
        raise ClaCheckError("The configured acceptance statement is absent from the CLA")
    return config


def noreply_login(email: str) -> str | None:
    match = NOREPLY_RE.fullmatch(email.strip())
    return match.group("login") if match else None


def is_bot_login(login: str) -> bool:
    return login.casefold().endswith("[bot]")


def add_user(users: dict[str, str], login: str | None) -> None:
    if login and not is_bot_login(login):
        users.setdefault(login.casefold(), login)


def collect_contributors(
    pull_request: dict[str, Any], commits: Iterable[dict[str, Any]], require_commits: bool
) -> tuple[dict[str, str], list[str]]:
    users: dict[str, str] = {}
    unresolved: set[str] = set()
    add_user(users, pull_request.get("user", {}).get("login"))
    if not require_commits:
        return users, []

    for commit in commits:
        sha = str(commit.get("sha", "unknown"))[:12]
        linked_author = (commit.get("author") or {}).get("login")
        commit_data = commit.get("commit") or {}
        raw_author = commit_data.get("author") or {}
        author_name = str(raw_author.get("name") or "unknown author")
        author_email = str(raw_author.get("email") or "")
        if linked_author:
            add_user(users, linked_author)
        else:
            inferred = noreply_login(author_email)
            if inferred:
                add_user(users, inferred)
            else:
                unresolved.add(f"{sha} ({author_name})")

        message = str(commit_data.get("message") or "")
        for match in COAUTHOR_RE.finditer(message):
            inferred = noreply_login(match.group("email"))
            if inferred:
                add_user(users, inferred)
            else:
                unresolved.add(f"{sha} co-author ({match.group('name').strip()})")
    return users, sorted(unresolved, key=str.casefold)


def signature_records(
    comments: Iterable[dict[str, Any]], acceptance_statement: str
) -> dict[str, str]:
    records: dict[str, str] = {}
    for comment in comments:
        login = (comment.get("user") or {}).get("login")
        body = str(comment.get("body") or "").replace("\r\n", "\n").strip()
        if login and body == acceptance_statement:
            records[login.casefold()] = str(comment.get("html_url") or "")
    return records


def evaluate(
    config: dict[str, Any],
    pull_request: dict[str, Any],
    commits: Iterable[dict[str, Any]],
    comments: Iterable[dict[str, Any]],
) -> Evaluation:
    labels = {
        str(label.get("name", "")).casefold()
        for label in pull_request.get("labels", [])
    }
    for configured in config["manual_override_labels"]:
        if str(configured).casefold() in labels:
            return Evaluation(True, (), (), (), (), str(configured))

    users, unresolved = collect_contributors(
        pull_request, commits, bool(config["require_commit_authors"])
    )
    exempt = {str(login).casefold() for login in config["exempt_users"]}
    required = {
        key: login for key, login in users.items() if key not in exempt
    }
    signatures = signature_records(comments, str(config["acceptance_statement"]))
    signed = [required[key] for key in required if key in signatures]
    missing = [required[key] for key in required if key not in signatures]
    return Evaluation(
        passed=not missing and not unresolved,
        required_users=tuple(sorted(required.values(), key=str.casefold)),
        signed_users=tuple(sorted(signed, key=str.casefold)),
        missing_users=tuple(sorted(missing, key=str.casefold)),
        unresolved_authors=tuple(unresolved),
    )


def render_comment(
    config: dict[str, Any], evaluation: Evaluation, cla_url: str
) -> str:
    marker = str(config["comment_marker"])
    if evaluation.override_label:
        return (
            f"{marker}\n"
            "### CLA check: passed by maintainer review ✅\n\n"
            f"The `{evaluation.override_label}` label records a manual CLA override. "
            "The maintainer is responsible for retaining the supporting evidence.\n\n"
            f"CLA: {cla_url}"
        )
    if evaluation.passed:
        signers = ", ".join(f"@{login}" for login in evaluation.signed_users)
        detail = f"Recorded signatures: {signers}." if signers else "No external signature is required."
        return (
            f"{marker}\n"
            "### CLA check: passed ✅\n\n"
            f"{detail}\n\nCLA: {cla_url}"
        )

    sections = [
        marker,
        "### CLA check: signature required ❌",
        "",
        f"Please read the [Contributor License Agreement]({cla_url}) and post "
        "this exact comment from each required GitHub account:",
        "",
        "```text",
        str(config["acceptance_statement"]),
        "```",
    ]
    if evaluation.missing_users:
        sections.extend(
            ["", "Missing signatures: " + ", ".join(f"@{u}" for u in evaluation.missing_users)]
        )
    if evaluation.unresolved_authors:
        sections.extend(
            [
                "",
                "Commit authors needing maintainer review:",
                *[f"- `{author}`" for author in evaluation.unresolved_authors],
                "",
                "Use a GitHub-linked author identity, or ask a maintainer to verify "
                "separate evidence and apply `cla:manual`.",
            ]
        )
    sections.extend(
        [
            "",
            "The check reruns automatically when a PR comment is created, edited, or deleted.",
        ]
    )
    return "\n".join(sections)


def upsert_bot_comment(
    api: GitHubApi,
    repository: str,
    pr_number: int,
    comments: list[dict[str, Any]],
    marker: str,
    body: str,
) -> None:
    existing = next(
        (
            comment
            for comment in comments
            if marker in str(comment.get("body") or "")
            and (comment.get("user") or {}).get("type") == "Bot"
        ),
        None,
    )
    if existing:
        if str(existing.get("body") or "") != body:
            api.request(
                "PATCH",
                f"/repos/{repository}/issues/comments/{existing['id']}",
                {"body": body},
            )
    else:
        api.request(
            "POST",
            f"/repos/{repository}/issues/{pr_number}/comments",
            {"body": body},
        )


def post_status(
    api: GitHubApi,
    repository: str,
    sha: str,
    context: str,
    state: str,
    description: str,
    target_url: str | None,
) -> None:
    payload: dict[str, Any] = {
        "state": state,
        "context": context,
        "description": description[:140],
    }
    if target_url:
        payload["target_url"] = target_url
    api.request("POST", f"/repos/{repository}/statuses/{sha}", payload)


def main() -> int:
    config = load_config()
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    pr_number_text = os.environ.get("CLA_PR_NUMBER", "")
    if not repository or not token or not pr_number_text.isdigit():
        raise ClaCheckError(
            "GITHUB_REPOSITORY, GITHUB_TOKEN, and numeric CLA_PR_NUMBER are required"
        )
    pr_number = int(pr_number_text)
    api = GitHubApi(
        repository,
        token,
        os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    pull_request, _ = api.request("GET", f"/repos/{repository}/pulls/{pr_number}")
    if pull_request.get("state") != "open":
        print(f"PR #{pr_number} is not open; no status update is needed.")
        return 0

    head_sha = str(pull_request["head"]["sha"])
    commits = api.get_all(
        f"/repos/{repository}/pulls/{pr_number}/commits?per_page=100"
    )
    comments = api.get_all(
        f"/repos/{repository}/issues/{pr_number}/comments?per_page=100"
    )
    evaluation = evaluate(config, pull_request, commits, comments)
    quoted_path = urllib.parse.quote(str(config["document"]), safe="/")
    cla_url = (
        f"https://github.com/{repository}/blob/{pull_request['base']['sha']}/{quoted_path}"
    )
    comment_body = render_comment(config, evaluation, cla_url)
    upsert_bot_comment(
        api,
        repository,
        pr_number,
        comments,
        str(config["comment_marker"]),
        comment_body,
    )

    if evaluation.passed:
        description = (
            f"Manual CLA review recorded by {evaluation.override_label}"
            if evaluation.override_label
            else "All required contributors signed CLA v" + str(config["version"])
        )
        state = "success"
    else:
        counts = []
        if evaluation.missing_users:
            counts.append(f"{len(evaluation.missing_users)} missing signature(s)")
        if evaluation.unresolved_authors:
            counts.append(f"{len(evaluation.unresolved_authors)} unresolved author(s)")
        description = "; ".join(counts) or "CLA review required"
        state = "failure"
    post_status(
        api,
        repository,
        head_sha,
        str(config["status_context"]),
        state,
        description,
        os.environ.get("CLA_RUN_URL") or None,
    )
    print(json.dumps(evaluation.__dict__, ensure_ascii=False, indent=2))
    return 0 if evaluation.passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClaCheckError as exc:
        print(f"CLA checker error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
