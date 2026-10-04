"""External-only R0004 production/regular-entry preparation. No live actions."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import prepare_userdir as existing

BASE = Path(__file__).resolve().parent
REPO = Path("C:/workspace/ck3_eternal_recurrence")
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III")
HEAD = sys.argv[1]
if not re.fullmatch(r"[0-9a-f]{40}", HEAD):
    raise ValueError("Supply the exact frozen clean commit")
TASK = "ck3-lyd-live-005-20261004"
RUN = BASE / "live-attempt-004"
STAGING = BASE / "build-formal-i2-r0004"
FIXTURE_ROOT = BASE / "r3-entry-fixture-candidate-002"
FIXTURE = FIXTURE_ROOT / "generated/mod_li_yu_dao_r3_entry_fixture"
AUDIT = BASE / "prepare-r0004-audit-001"
I2_ROOT = BASE / "r4-i2-fixture-candidate-001"
I2_FIXTURE = I2_ROOT / "generated/mod_li_yu_dao_r4_i2_fixture"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def snapshot(directory: Path) -> list[dict]:
    return [{"path": path.relative_to(directory).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)}
            for path in sorted(directory.rglob("*")) if path.is_file()]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def command(name: str, argv: list[str]) -> str:
    result = subprocess.run(argv, cwd=REPO, capture_output=True, encoding="utf-8", errors="replace", check=False)
    (AUDIT / (name + ".stdout.txt")).write_text(result.stdout, encoding="utf-8", newline="\n")
    (AUDIT / (name + ".stderr.txt")).write_text(result.stderr, encoding="utf-8", newline="\n")
    write_json(AUDIT / (name + ".command.json"), {"argv": argv, "cwd": str(REPO), "returncode": result.returncode,
                                                "stdout_sha256": sha(AUDIT / (name + ".stdout.txt")), "stderr_sha256": sha(AUDIT / (name + ".stderr.txt"))})
    if result.returncode:
        raise RuntimeError(name + " failed; preserved stdout/stderr")
    return result.stdout


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
for target in (RUN, STAGING, AUDIT, STAGING.with_name(STAGING.name + ".manifest.json"), STAGING.with_name(STAGING.name + ".zip"), BASE / "live_control_r0004.py", BASE / "screen_lease_entry_r0004.py"):
    if target.exists():
        raise RuntimeError("fresh R0004 target already exists: " + str(target))
AUDIT.mkdir()
actual_head = command("source-head-before", ["git", "rev-parse", "HEAD"]).strip()
status_before = command("source-status-before", ["git", "status", "--porcelain"])
if actual_head != HEAD or status_before:
    raise RuntimeError("preparation requires the assigned exact clean checkout")
source_objects = {relative: command("object-" + relative.replace("/", "-"), ["git", "rev-parse", "HEAD:" + relative]).strip()
                  for relative in ("mod_li_yu_dao", "tools/extract_auto_upgrade_buildings.py", ".github/workflows/li-yu-dao-static.yml")}
render_path = FIXTURE_ROOT / "fixture-render-report.json"
render = json.loads(render_path.read_text(encoding="utf-8"))
fixture_source = snapshot(FIXTURE)
expected_fixture = render["output_sha256"]
if len(fixture_source) != 7 or {row["path"]: row["sha256"] for row in fixture_source} != expected_fixture:
    raise RuntimeError("fixture candidate002 inventory/hash differs from its frozen render report")
for row in fixture_source:
    raw = (FIXTURE / row["path"]).read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("fixture runtime lacks BOM: " + row["path"])
    if b"lyd_np_" in raw or b"create_character" in raw or b"create_title" in raw or b"detach_rite_to_new_faith" in raw:
        raise RuntimeError("regular-entry fixture contains native-probe payload")
launcher_path = GAME / "launcher/launcher-settings.json"
launcher = json.loads(launcher_path.read_text(encoding="utf-8-sig"))
exe = GAME / "binaries/ck3.exe"
exe_sha = sha(exe)
if launcher.get("rawVersion") != "1.20.0.3" or exe_sha != existing.EXPECTED_EXE:
    raise RuntimeError("actual launcher or executable is not the assigned exact 1.20.0.3 build")
app_manifest = GAME.parent.parent / "appmanifest_1158310.acf"
build_ids = re.findall(r'"buildid"\s*"([0-9]+)"', app_manifest.read_text(encoding="utf-8"))
if build_ids != ["25652598"]:
    raise RuntimeError("Steam app manifest build ID changed")
native_corpus = []
for relative, expected in render["native_sources_sha256"].items():
    path = GAME / "game" / relative
    actual = sha(path)
    if actual != expected:
        raise RuntimeError("fixture primary native corpus changed: " + relative)
    native_corpus.append({"path": str(path), "relative_path": relative, "bytes": path.stat().st_size, "sha256": actual})
robert_history = GAME / "game/history/characters/norman.txt"
native_corpus.append({"path": str(robert_history), "relative_path": "history/characters/norman.txt", "bytes": robert_history.stat().st_size, "sha256": sha(robert_history)})
build_text = command("production-build", [sys.executable, "-B", str(REPO / "mod_li_yu_dao/tools/build_release.py"), "--output", str(STAGING)])
build = json.loads(build_text)
manifest_path = Path(build["manifest"])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if build["file_count"] != 34 or manifest["git_sha"] != HEAD:
    raise RuntimeError("production build inventory or revision differs from assigned34-file HEAD")
spec = importlib.util.spec_from_file_location("lyd_r3_builder_readonly", REPO / "mod_li_yu_dao/tools/build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
builder.verify_manifest(STAGING, manifest_path)
RUN.mkdir()
production, fixture, userdir = RUN / "content/production", RUN / "content/fixture", RUN / "userdir"
shutil.copytree(STAGING, production)
shutil.copytree(FIXTURE, fixture)
builder.verify_manifest(production, manifest_path)
if snapshot(fixture) != fixture_source:
    raise RuntimeError("mounted fixture bytes differ from reviewed candidate002")
i2_render_path = I2_ROOT / "fixture-render-report.json"
i2_render = json.loads(i2_render_path.read_text(encoding="utf-8"))
i2_source = snapshot(I2_FIXTURE)
if len(i2_source) != 7 or {row["path"]: row["sha256"] for row in i2_source} != i2_render["outputs"]:
    raise RuntimeError("I2 fixture differs from reviewed render hashes")
i2_mounted = RUN / "content/i2-fixture"
shutil.copytree(I2_FIXTURE, i2_mounted)
if snapshot(i2_mounted) != i2_source:
    raise RuntimeError("I2 fixture mount differs")
for row in i2_source:
    if not (i2_mounted / row["path"]).read_bytes().startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("I2 fixture lacks BOM")
for relative in ("logs", "save games", "mod", "player/game_rules"):
    (userdir / relative).mkdir(parents=True, exist_ok=True)
enabled = []
for name, payload in (("production", production), ("fixture", fixture), ("i2_fixture", i2_mounted)):
    descriptor = (payload / "descriptor.mod").read_text(encoding="utf-8-sig").rstrip()
    if re.search(r"\b(?:remote_file_id|path)\s*=", descriptor):
        raise RuntimeError("inner descriptor carries forbidden Workshop or path fields")
    outer = userdir / ("mod/lyd_" + name + ".mod")
    existing.write(outer, descriptor + '\npath="' + payload.as_posix() + '"\n', bom=True)
    enabled.append("mod/lyd_" + name + ".mod")
write_json(userdir / "dlc_load.json", {"enabled_mods": enabled, "disabled_dlcs": []})
existing.write(userdir / "pdx_settings.txt", existing.render_settings())
existing.write(userdir / "tutorial.txt", 'last_lesson_chain="reactive_advice"\ncompleted_lessons={}\n')
existing.write(userdir / "player/game_rules/presets.txt", 'game_rules_preset={\n name="LastAppliedRules"\n setting={}\n ironman=no\n}\n')
template = {"schema_version": 1, "guard_profile": "<FRESH_LIVE_GUARD.json>", "guard_profile_sha256": "<SHA256_OF_FRESH_GUARD>",
            "userdir": str(userdir), "state_directory": str(RUN / "native-state"), "evidence_directory": str(RUN / "native-evidence"),
            "game_version": "1.20.0.3", **{key: {"path": str(path), "sha256": sha(path)} for key, (path, expected) in existing.ARTIFACTS.items()}}
if any(template[key]["sha256"] != expected for key, (path, expected) in existing.ARTIFACTS.items()):
    raise RuntimeError("reviewed native artifacts changed; preparation does not inject or attach")
write_json(RUN / "native-profile.template.json", template)
live_source = (BASE / "live_control_r0002.py").read_text(encoding="utf-8")
live_source = existing.once(live_source, "RUN = BASE / 'live-attempt-002'", "RUN = BASE / 'live-attempt-004'")
live_source = existing.once(live_source, "'ck3-lyd-live-003-20261004'", repr(TASK))
live_source = live_source.replace("'LYD-iteration1-isolated-live'", "'LYD-formal-R0004-isolated-live'")
live_source = live_source.replace("    argv = prepared['launch_argv']", "    current_head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()\n    current_status = subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True)\n    if current_head != prepared['source_revision'] or current_status:\n        raise RuntimeError('prepared source revision is no longer the clean frozen checkout')\n    argv = prepared['launch_argv']")
lease_source = (BASE / "screen_lease_entry_r0002.py").read_text(encoding="utf-8")
lease_source = existing.once(lease_source, 'OWNER_HEAD = "7fd082eab7626239ecb88702d0ebae71f938b259"', 'OWNER_HEAD = "' + HEAD + '"')
lease_source = existing.once(lease_source, 'TASK_ID = "ck3-lyd-live-003-20261004"', 'TASK_ID = "' + TASK + '"')
lease_source = lease_source.replace('BASE / "screen-lease-live-001"', 'BASE / "screen-lease-live-r0004"')
lease_source = lease_source.replace("LYD-live-001", "LYD-formal-R0004")
bus_source = REPO / "tools/codex_task_bus.py"
bus_sha = sha(bus_source).upper()
installed_bus = Path("C:/workspace/.codex-task-bus/bin/codex_task_bus.py")
if sha(installed_bus).upper() != bus_sha:
    raise RuntimeError("installed/source task bus hashes differ")
lease_source = re.sub(r'CLI_SHA = "[0-9A-F]+"', 'CLI_SHA = "' + bus_sha + '"', lease_source, count=1)
helpers = []
for name, source_text in (("live_control_r0004.py", live_source), ("screen_lease_entry_r0004.py", lease_source)):
    ast.parse(source_text, filename=name)
    target = BASE / name
    existing.write(target, source_text)
    helpers.append({"path": str(target), "bytes": target.stat().st_size, "sha256": sha(target), "executed": False})
after_head = command("source-head-after", ["git", "rev-parse", "HEAD"]).strip()
after_status = command("source-status-after", ["git", "status", "--porcelain"])
if after_head != HEAD or after_status:
    raise RuntimeError("checkout changed during preparation")
receipt = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(), "runtime_status": "NOT_RUN", "source_revision": HEAD,
           "source_git_objects": source_objects, "source_clean_before_and_after": True, "interpreter": sys.executable,
           "output": str(RUN), "userdir": str(userdir), "mount_order": enabled,
           "production_input": str(STAGING), "production_manifest": str(manifest_path), "production_manifest_sha256": sha(manifest_path),
           "production_zip": build["archive"], "production_zip_sha256": build["zip_sha256"],
           "production_payload": snapshot(production), "fixture_payload": snapshot(fixture), "i2_fixture_payload": snapshot(i2_mounted),
            "i2_fixture_render_report": str(i2_render_path), "i2_fixture_render_sha256": sha(i2_render_path),
            "i2_fixture_contract": {"separate_test_input": True, "creates_two_real_scholars": True, "detaches_existing_jingshu": True, "seeds_consent": False, "qualification_and_resources": "explicit player fixture decisions only", "cooldown_reset": "explicit acceptance action; not natural expiry"},
           "fixture_input": str(FIXTURE), "fixture_render_report": str(render_path), "fixture_render_report_sha256": sha(render_path),
           "fixture_candidate": "r3-entry-fixture-candidate-002", "fixture_contract": {"target": "current played Character only, original faith:confucian_faith.main_rite", "native_probe_mounted": False, "creates_faith_rite_title_npc": False},
           "game": {"root": str(GAME), "raw_version": launcher["rawVersion"], "executable": str(exe), "executable_bytes": exe.stat().st_size, "executable_sha256": exe_sha,
                    "launcher_settings": str(launcher_path), "launcher_settings_sha256": sha(launcher_path), "app_manifest": str(app_manifest), "app_manifest_sha256": sha(app_manifest), "build_id": build_ids[0]},
           "native_corpus": native_corpus, "launch_argv": [str(exe), "-debug_mode", "-gdpr-compliant", "-userdir=" + str(userdir)], "launch_cwd": str(exe.parent),
           "entry": {"bookmark_date": "1066.9.15", "character_name": "Robert Guiscard", "historical_character_key": "1128", "native_character_id": None, "identity_status": "REQUIRES_INDEPENDENT_LIVE_READBACK", "new_normal_campaign": True},
           "settings_requested": {"language": "l_simp_chinese", "autosave": "NEVER", "cloud_save": False, "display_mode": "windowed", "windowed_resolution": "1600x900"},
           "settings_status": "REQUIRES_GAME_SETTINGS_READBACK; requested dimensions are not desktop-click coordinates", "root_screen_task": TASK,
           "root_action_helpers": helpers, "task_bus_source_sha256": bus_sha, "helper_actions_executed": False,
           "prepared_files": snapshot(RUN), "real_documents_written": False, "workshop_cache_written": False,
           "game_launched": False, "steam_input": False, "screen_task_registered": False, "lease_started": False, "native_injected": False, "tracked_written": False}
write_json(RUN / "PREPARED.json", receipt)
print(json.dumps({"status": "PREPARED_ONLY", "live": "NOT_RUN", "source_revision": HEAD, "prepared": str(RUN / "PREPARED.json"),
                  "production_files": len(receipt["production_payload"]), "fixture_files": len(receipt["fixture_payload"]), "mount_order": enabled,
                  "entry": receipt["entry"], "helpers": helpers}, ensure_ascii=False, indent=2))
