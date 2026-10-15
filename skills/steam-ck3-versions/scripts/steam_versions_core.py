"""Portable, read-only Steam installation observations and CK3 branch matching."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time

APP_ID = "1158310"
SCHEMA = "steam-ck3-versions-v1"


class VersionError(RuntimeError):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_vdf(text):
    """Parse quoted/bare KeyValues without treating Windows paths as escapes."""
    tokens = []
    offset = 0
    while offset < len(text):
        if text[offset].isspace():
            offset += 1
        elif text.startswith("//", offset):
            end = text.find("\n", offset)
            offset = len(text) if end < 0 else end + 1
        elif text[offset] in "{}":
            tokens.append(text[offset])
            offset += 1
        elif text[offset] == '"':
            offset += 1
            value = []
            while offset < len(text) and text[offset] != '"':
                if text[offset] == "\\" and offset + 1 < len(text):
                    following = text[offset + 1]
                    if following in ('"', "\\"):
                        value.append(following)
                        offset += 2
                        continue
                value.append(text[offset])
                offset += 1
            if offset == len(text):
                raise VersionError("unterminated VDF quoted string")
            tokens.append("".join(value))
            offset += 1
        else:
            end = offset
            while end < len(text) and not text[end].isspace() and text[end] not in "{}":
                end += 1
            tokens.append(text[offset:end])
            offset = end

    def block(index, nested=False):
        result = {}
        while index < len(tokens):
            key = tokens[index]
            if key == "}":
                if not nested:
                    raise VersionError("unexpected VDF closing brace")
                return result, index + 1
            if key == "{" or index + 1 >= len(tokens):
                raise VersionError("missing VDF key/value")
            index += 1
            if tokens[index] == "{":
                value, index = block(index + 1, True)
            else:
                value = tokens[index]
                if value == "}":
                    raise VersionError("missing VDF value")
                index += 1
            if key in result:
                raise VersionError(f"duplicate VDF key: {key}")
            result[key] = value
        if nested:
            raise VersionError("unterminated VDF object")
        return result, index

    return block(0)[0]


def registry_steam_roots():
    if os.name != "nt":
        return []
    import winreg
    candidates = []
    sources = [(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
               (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
               (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath")]
    for hive, key, value in sources:
        try:
            with winreg.OpenKey(hive, key) as handle:
                candidates.append(Path(winreg.QueryValueEx(handle, value)[0]))
        except OSError:
            continue
    return candidates


def discover_installation(steam_dir=None, library=None):
    candidates = [Path(steam_dir)] if steam_dir else []
    if not steam_dir:
        if os.environ.get("STEAM_DIR"):
            candidates.append(Path(os.environ["STEAM_DIR"]))
        candidates.extend(registry_steam_roots())
    roots = {str(p.resolve()).casefold(): p.resolve() for p in candidates
             if (p / "steamapps").is_dir()}
    if len(roots) != 1:
        raise VersionError("Steam root not unique; supply --steam-dir explicitly")
    steam = next(iter(roots.values()))
    libraries = [steam]
    path = steam / "steamapps" / "libraryfolders.vdf"
    if path.is_file():
        folders = parse_vdf(path.read_text(encoding="utf-8-sig"))
        for key, value in folders.get("libraryfolders", folders).items():
            if not key.isdecimal():
                continue
            raw = value.get("path") if isinstance(value, dict) else value
            if isinstance(raw, str):
                libraries.append(Path(raw).resolve())
    if library:
        libraries = [Path(library).resolve()]
    manifests = {str(p.resolve()).casefold(): p.resolve() for root in libraries
                 for p in [root / "steamapps" / f"appmanifest_{APP_ID}.acf"] if p.is_file()}
    if len(manifests) != 1:
        raise VersionError("CK3 installed manifest not unique; supply --library explicitly")
    return {"steam_dir": str(steam), "manifest_path": str(next(iter(manifests.values())))}


def integer(value, field):
    try:
        result = int(value)
    except (ValueError, TypeError) as error:
        raise VersionError(f"invalid manifest integer {field}: {value!r}") from error
    if result < 0:
        raise VersionError(f"negative manifest integer {field}")
    return result


def observe_installation(installation, *, hash_exe=False):
    path = Path(installation["manifest_path"])
    raw = path.read_bytes()
    app = parse_vdf(raw.decode("utf-8-sig")).get("AppState", {})
    if str(app.get("appid")) != APP_ID:
        raise VersionError("installed manifest does not identify CK3")
    install_dir = app.get("installdir")
    if not isinstance(install_dir, str) or not install_dir:
        raise VersionError("CK3 installdir missing")
    common = (path.parent / "common").resolve()
    game = (common / install_dir).resolve()
    if common not in game.parents:
        raise VersionError("CK3 install path is outside its library common directory")
    user = app.get("UserConfig", {})
    if not isinstance(user, dict):
        raise VersionError("manifest UserConfig is not an object")
    branch = user.get("BetaKey", "public") or "public"
    fields = ("StateFlags", "buildid", "TargetBuildID", "BytesToDownload", "BytesDownloaded",
              "BytesToStage", "BytesStaged", "UpdateResult", "LastUpdated")
    numbers = {key: integer(app[key], key) for key in fields if key in app}
    launcher_path = game / "launcher" / "launcher-settings.json"
    if not launcher_path.is_file():
        launcher_path = game / "launcher-settings.json"
    launcher = {}
    if launcher_path.is_file():
        source = json.loads(launcher_path.read_text(encoding="utf-8-sig"))
        launcher = {"path": str(launcher_path), "raw_version": source.get("rawVersion"),
                    "display_version": source.get("version"), "sha256": sha256_file(launcher_path)}
    exe = game / "binaries" / "ck3.exe"
    executable = {"path": str(exe), "exists": exe.is_file()}
    if executable["exists"]:
        stat = exe.stat()
        executable.update(bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)
        if hash_exe:
            executable["sha256"] = sha256_file(exe)
    return {"observed_at_utc": utc_now(), "manifest_path": str(path),
            "manifest_sha256": hashlib.sha256(raw).hexdigest(), "app_id": APP_ID,
            "branch": branch, "numbers": numbers, "game_dir": str(game),
            "launcher": launcher, "executable": executable,
            "installed_depots": app.get("InstalledDepots", {})}


VERSION_PATTERN = re.compile(r"(?<![\w.])(\d+\.\d+(?:\.\d+){0,2})(?![\w.])")
STABLE_LABELS = {"none", "无", "無", "不参与测试", "不參與測試", "不参加任何测试活动",
                 "none - opt out of all beta programs", "public", "默认公开版本", "預設公開版本",
                 "default public version", "default public branch"}


def label_branch(label):
    if label.strip().casefold() in STABLE_LABELS:
        return "public"
    prefix = label.split(" - ", 1)[0].strip()
    if prefix.casefold() in STABLE_LABELS:
        return "public"
    return prefix if re.fullmatch(r"[A-Za-z0-9_.-]+", prefix) else None


def resolve_target(labels, target, rows=None):
    labels = list(dict.fromkeys(labels))
    rows_by_label = {row["label"]: row for row in (rows or [])}
    if target.casefold() in {"public", "none", "stable"}:
        matches = [label for label in labels if label_branch(label) == "public"]
    else:
        matches = [label for label in labels if label == target]
        if not matches:
            matches = [label for label in labels if label_branch(label) == target]
        if not matches and VERSION_PATTERN.fullmatch(target):
            matches = [label for label in labels if target in VERSION_PATTERN.findall(label)]
        if not matches and VERSION_PATTERN.fullmatch(target):
            matches = [label for label in labels if target in
                       VERSION_PATTERN.findall(" ".join(rows_by_label.get(label, {}).get("description_texts", [])))]
        if not matches:
            matches = [label for label in labels if rows_by_label.get(label, {}).get("row_text") == target]
    if len(matches) != 1:
        raise VersionError(f"target must match exactly one visible branch; matches={matches!r}")
    label = matches[0]
    branch = label_branch(label)
    if branch is None:
        raise VersionError("display label does not expose a branch identity; use a verified selector/profile")
    version = target if VERSION_PATTERN.fullmatch(target) else None
    advertised = list(dict.fromkeys(VERSION_PATTERN.findall(
        " ".join(rows_by_label.get(label, {}).get("description_texts", [])))))
    if VERSION_PATTERN.fullmatch(branch) and len(advertised) == 1:
        # CK3's actual table names branch "1.20.0" but explicitly describes
        # installed version "1.20.0.4". A branch key is not a game version.
        # Exact version requests still win over an incidental description.
        if target == branch or version is None:
            version = advertised[0]
    if version is None and VERSION_PATTERN.fullmatch(branch):
        version = branch
    return {"label": label, "branch": branch, "expected_version": version,
            "requested_target": target, "advertised_versions": advertised,
            "identity_source": "Steam table branch label and explicit description; must agree with manifest/installed readback"
            if label in rows_by_label else "visible_label_prefix; must agree with Steam manifest readback"}


def completion_problems(snapshot, branch, expected_version=None, expected_build=None):
    problems = []
    numbers = snapshot["numbers"]
    if snapshot["branch"] != branch:
        problems.append("manifest_branch_mismatch")
    if numbers.get("StateFlags") != 4:
        problems.append("steam_not_fully_installed_only_state")
    build = numbers.get("buildid", 0)
    if build <= 0:
        problems.append("installed_build_missing")
    if expected_build is not None and build != int(expected_build):
        problems.append("installed_build_mismatch")
    if numbers.get("TargetBuildID", 0) not in (0, build):
        problems.append("target_build_not_installed")
    for total, done in [("BytesToDownload", "BytesDownloaded"), ("BytesToStage", "BytesStaged")]:
        if numbers.get(total, 0) > numbers.get(done, 0):
            problems.append(f"incomplete_{total}")
    if not snapshot["executable"]["exists"]:
        problems.append("ck3_executable_missing")
    if expected_version:
        actual = str(snapshot["launcher"].get("raw_version") or "")
        if actual != expected_version:
            problems.append("installed_launcher_version_mismatch")
    return problems


def stable_identity(snapshot):
    return json.dumps({key: snapshot[key] for key in ("manifest_sha256", "branch", "numbers",
                      "launcher", "executable", "installed_depots")}, sort_keys=True)


def wait_installed(installation, branch, *, expected_version=None, expected_build=None,
                   timeout=3600, poll_seconds=2, settle_seconds=8, emit=None,
                   observe=observe_installation, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + timeout
    stable_since = None
    previous = None
    last = None
    while clock() < deadline:
        try:
            snapshot = observe(installation)
            problems = completion_problems(snapshot, branch, expected_version, expected_build)
            identity = stable_identity(snapshot)
            if identity != previous or last is None:
                if emit:
                    emit("download_observation", snapshot=snapshot, pending=problems)
                previous, stable_since = identity, None
            last = snapshot
            if not problems:
                if stable_since is None:
                    stable_since = clock()
                if clock() - stable_since >= settle_seconds:
                    final = observe(installation, hash_exe=True)
                    without_hash = json.loads(json.dumps(final))
                    without_hash["executable"].pop("sha256", None)
                    if (stable_identity(without_hash) == identity
                            and not completion_problems(final, branch, expected_version, expected_build)):
                        if emit:
                            emit("installed_verified", snapshot=final)
                        return final
                    stable_since = None
            else:
                stable_since = None
        except (OSError, ValueError, VersionError) as error:
            stable_since = None
            previous = None
            if emit:
                emit("manifest_temporarily_unreadable", error=str(error))
        sleep(min(poll_seconds, max(0, deadline - clock())))
    raise VersionError(f"download/install timed out without completion; last={last!r}")
