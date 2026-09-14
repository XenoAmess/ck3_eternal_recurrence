"""Fail when tracked project content reintroduces the forbidden Windows shell."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ENGINE_NAME = "power" + "shell"
SHORT_ENGINE_NAME = "pw" + "sh"
FORBIDDEN_SUFFIXES = tuple("." + value for value in ("ps" + "1", "psm" + "1", "psd" + "1"))
FORBIDDEN_REFERENCES = (
    ENGINE_NAME,
    SHORT_ENGINE_NAME,
    *FORBIDDEN_SUFFIXES,
)
STRUCTURED_AUTOMATION_SUFFIXES = {".json", ".toml", ".yaml", ".yml"}
LEGACY_COMMANDS = (
    "Start" + "-Process",
    "Get" + "-ChildItem",
    "Get" + "-FileHash",
    "Join" + "-Path",
    "New" + "-Item",
    "Set" + "-Location",
    "Remove" + "-Item",
    "Copy" + "-Item",
    "Test" + "-Path",
    "Resolve" + "-Path",
    "Where" + "-Object",
    "Select" + "-Object",
    "ForEach" + "-Object",
    "ConvertTo" + "-Json",
    "Set" + "-Content",
    "Get" + "-Date",
    "Get" + "-Command",
    "Select" + "-String",
    "Write" + "-Host",
    "Out" + "-Null",
)
legacy_command_pattern = "|".join(re.escape(command) for command in LEGACY_COMMANDS)
LEGACY_FENCE_TOKENS = re.compile(
    r"(?im)(?:^\s*\$[A-Za-z][A-Za-z0-9_]*\s*=|^\s*&\s|`\s*$|\$env:|"
    + r"\$LAST" + r"EXITCODE|\b(?:" + legacy_command_pattern + r")\b)"
)
LEGACY_TEXT_VARIABLE = re.compile(
    r"(?<![A-Za-z0-9_$])\$[A-Za-z][A-Za-z0-9_]*(?![A-Za-z0-9_$])"
)


def project_files() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]


def decode_text(path: Path) -> str | None:
    raw = path.read_bytes()
    if b"\0" in raw:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def fenced_block_findings(relative: str, text: str) -> list[str]:
    if not relative.casefold().endswith(".md"):
        return []
    findings: list[str] = []
    fence_start: int | None = None
    fence_language = ""
    body: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        if fence_start is None and line.lstrip().startswith("```"):
            fence_start = number
            fence_language = line.lstrip()[3:].strip().casefold()
            body = []
        elif fence_start is not None and line.lstrip().startswith("```"):
            content = "\n".join(body)
            legacy_variable = (
                fence_language in {"", "bat", "cmd", "text"}
                and LEGACY_TEXT_VARIABLE.search(content)
            )
            if LEGACY_FENCE_TOKENS.search(content) or legacy_variable:
                findings.append(f"{relative}:{fence_start}: legacy shell syntax in fenced block")
            fence_start = None
            fence_language = ""
            body = []
        elif fence_start is not None:
            body.append(line)
    if fence_start is not None:
        findings.append(f"{relative}:{fence_start}: unclosed fenced block")
    return findings


def validate(paths: list[str]) -> list[str]:
    findings: list[str] = []
    for relative in paths:
        normalized = relative.replace("\\", "/")
        if normalized.casefold().endswith(FORBIDDEN_SUFFIXES):
            findings.append(f"{normalized}: forbidden script extension")
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        text = decode_text(path)
        if text is None:
            continue
        if normalized != "AGENTS.md":
            folded = text.casefold()
            for reference in FORBIDDEN_REFERENCES:
                if reference.casefold() in folded:
                    findings.append(f"{normalized}: forbidden shell reference {reference!r}")
            if path.suffix.casefold() in STRUCTURED_AUTOMATION_SUFFIXES and LEGACY_FENCE_TOKENS.search(text):
                findings.append(f"{normalized}: legacy shell syntax in structured automation content")
        findings.extend(fenced_block_findings(normalized, text))
    return findings


def main() -> int:
    findings = validate(project_files())
    for finding in findings:
        print(finding)
    if findings:
        print(f"PYTHON-ONLY RED: {len(findings)} violation(s)")
        return 1
    print("PYTHON-ONLY GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
