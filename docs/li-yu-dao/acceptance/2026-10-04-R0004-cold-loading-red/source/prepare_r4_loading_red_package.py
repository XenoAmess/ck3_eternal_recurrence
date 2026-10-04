"""Exact-byte external projection of closed R4; no game, CI or checkout actions."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

BASE = Path(r"C:/workspace/ck3_lyd_runtime_20261004")
RUN = BASE / "live-attempt-004"
KEEPER = BASE / "screen-lease-live-r0004"
CI = BASE / "ci-closed-01b4dda3-001"
OUT = BASE / "r4-loading-red-package-001/permanent-projection-001"
COMMIT = "01b4dda39505929c1245de699e67862f4130a02e"
TREE = "a86935a77eb31d70e7c95ba5ae564e0fb66f3d9a"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def write(name: str, data) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


COPIED = {}


def copy(source: Path, name: str) -> dict:
    source = source.resolve()
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    before = digest(source)
    with source.open("rb") as original, target.open("xb") as projected:
        for block in iter(lambda: original.read(1024 * 1024), b""):
            projected.write(block)
    assert digest(target) == before == digest(source), str(source)
    entry = {"source": str(source), "projection": name, "bytes": target.stat().st_size,
             "sha256": before, "mode": "exact-byte-copy"}
    COPIED[str(source)] = entry
    return entry


def classify_error(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        if "[E]" not in line:
            continue
        category = "UNCLASSIFIED_ENGINE_E"
        domain = "unresolved"
        if "Unknown trigger:" in line:
            if "lyd_c2_consent_triggers.txt" in line:
                category, domain = "PRODUCT_UNKNOWN_TRIGGER", "production"
            elif "lyd_r4_fixture_effects.txt" in line:
                category, domain = "FIXTURE_UNKNOWN_TRIGGER", "i2-fixture"
        elif "Script system error!" in line or "PostValidate of effect 'create_character'" in line:
            category, domain = "FIXTURE_CREATE_CHARACTER_VALIDATION", "i2-fixture"
        elif "Variable '" in line:
            variable = re.search(r"Variable '([^']+)'", line).group(1)
            domain = "i2-fixture" if variable.startswith("lyd_r4_") else "production"
            category = "VARIABLE_USED_NEVER_SET" if "used but is never set" in line else "VARIABLE_SET_NEVER_USED"
        rows.append({"line": number, "category": category, "domain": domain, "raw_header": line})
    counts = Counter((row["category"], row["domain"]) for row in rows)
    assert len(rows) == 63 and not any(row["category"] == "UNCLASSIFIED_ENGINE_E" for row in rows)
    return {"source": str(path), "source_sha256": digest(path), "source_bytes": path.stat().st_size,
            "E_header_count": len(rows), "counts": [{"category": a, "domain": b, "entries": n}
                  for (a, b), n in sorted(counts.items())], "entries": rows,
            "boundary": "Counts are actual error.log headers, not deduplicated signatures or repeated game.log copies. Variables remain native E diagnostics, not automatically exempt warnings."}


def setting_value(text: str, key: str):
    match = re.search(r'"' + re.escape(key) + r'"\s*=\s*\{([^}]+)\}', text)
    if not match:
        return None
    value = re.search(r'(?:value|enabled)\s*=\s*("[^"]*"|[^\s]+)', match.group(1))
    return value.group(1).strip('"') if value else None


def omission_reason(path: Path) -> str:
    name = path.as_posix().lower()
    if "screen-lease-live-r0004" in name:
        return "Large/repeated keeper or bus polling detail retained externally; projected FINAL/CAS provides closure and this index preserves exact original bytes identity."
    if "/shadercache/" in name:
        return "Generated graphics cache is not product behavior evidence; original retained externally."
    if path.suffix.lower() == ".zip":
        return "Distribution archive retained externally; exact loaded source and original manifest are projected."
    if "/userdir/account/" in name or "/userdir/player/" in name:
        return "Generated user-profile data retained externally; no campaign identity was read back."
    if "/userdir/" in name:
        return "Auxiliary userdir/cache output retained externally; key original settings, mounts, logs and lifecycle are projected."
    return "Supporting or duplicated preparation/raw artifact retained externally; direct necessary proof projected with original path/hash retained here."


def main():
    OUT.mkdir()
    prepared = read(RUN / "PREPARED.json")
    assert prepared["source_revision"] == COMMIT and prepared["source_git_objects"]["mod_li_yu_dao"] == TREE
    payloads = (("production", "production_payload", 34), ("fixture", "fixture_payload", 7),
                ("i2-fixture", "i2_fixture_payload", 7))
    for folder, field, expected in payloads:
        assert len(prepared[field]) == expected
        actual = {p.relative_to(RUN / "content" / folder).as_posix() for p in (RUN / "content" / folder).rglob("*") if p.is_file()}
        assert actual == {row["path"] for row in prepared[field]}
        for row in prepared[field]:
            source = RUN / "content" / folder / row["path"]
            assert source.stat().st_size == row["bytes"] and digest(source) == row["sha256"]
            copy(source, "inputs/" + folder + "/" + row["path"])
    for field, target in (("production_manifest", "inputs/production.manifest.json"),
                          ("fixture_render_report", "inputs/entry-fixture-render-report.json"),
                          ("i2_fixture_render_report", "inputs/i2-fixture-render-report.json")):
        source = Path(prepared[field])
        pin_field = {"production_manifest": "production_manifest_sha256", "fixture_render_report": "fixture_render_report_sha256",
                     "i2_fixture_render_report": "i2_fixture_render_sha256"}[field]
        assert digest(source) == prepared[pin_field]
        copy(source, target)
    copy(RUN / "PREPARED.json", "inputs/PREPARED.json")
    for path in sorted((RUN / "userdir/mod").glob("*")):
        if path.is_file():
            copy(path, "inputs/userdir-mod/" + path.name)
    for name in ("dlc_load.json", "pdx_settings.txt", "tutorial.txt"):
        copy(RUN / "userdir" / name, "inputs/" + name)

    for path in sorted(RUN.glob("*")):
        if path.is_file() and path.suffix.lower() in {".json", ".txt"} and path.name not in {
            "PREPARED.json", "screen-prelaunch-all-notices.stdout.json", "ck3-stdout.txt"
        }:
            copy(path, "run/" + path.name)
    for path in sorted((RUN / "userdir/logs").glob("*")):
        if path.is_file():
            copy(path, "logs/post-exit/" + path.name)
    for name in ("report.json", "error.log", "debug.log", "game.log", "setup.log", "system.log"):
        copy(RUN / "loading-red-before-exit" / name, "logs/pre-exit/" + name)
    copy(KEEPER / "FINAL.json", "lifecycle/keeper-FINAL.raw.json")
    for path in sorted((RUN / "steam-fresh-002").glob("*")):
        if path.is_file():
            copy(path, "offline/" + path.name)
    for name in ("first-load.png", "loaded-lobby.png", "after-normal-close.png", "exited-desktop.png"):
        copy(RUN / name, "screens/" + name)
    for path in sorted(CI.rglob("*")):
        if path.is_file():
            copy(path, "ci/" + path.relative_to(CI).as_posix())
    for name in ("prepare_r0004.py", "live_control_r0004.py", "screen_lease_entry_r0004.py", "r4_prelaunch_review.py",
                 "r4_focus_capture.py", "r4_normal_loading_exit.py", "record_r4_status.py"):
        copy(BASE / name, "source/helpers/" + name)
    copy(Path(__file__).resolve(), "source/prepare_r4_loading_red_package.py")

    errors = classify_error(RUN / "userdir/logs/error.log")
    write("error-classification.json", errors)
    keeper = read(KEEPER / "FINAL.json")
    release = read(RUN / "screen-release-completed.json")
    exit_readback = read(RUN / "normal-exit-processes-001.json")
    allocator = read(RUN / "allocator-completed-red.stdout.txt")
    assert keeper["thread_exited"] and keeper["failure"] is None and keeper["last_sequence"] == 2686
    assert release["event"]["sequence"] == 2687 and release["task"]["resources"] == []
    assert not exit_readback["ck3_processes"] and exit_readback["pid_19184_present"] is False
    assert allocator["status"] == "completed-red" and allocator["sequence"] == 4
    settings = (RUN / "userdir/pdx_settings.txt").read_text(encoding="utf-8-sig")
    setting_readback = {key: setting_value(settings, key) for key in ("language", "display_mode", "windowed_resolution", "autosave", "cloud_save")}
    ci = read(CI / "FINAL-CI-RECEIPT.json")
    assert ci["commit"] == COMMIT and ci["all_success"]
    report = {
        "schema": "ck3.lyd.r4-loading-red-report.v1", "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit": COMMIT, "lyd_tree": TREE, "overall": "NATIVE_LOADING_RED", "official_L0": "PASS",
        "production_cold_load": "RED_UNKNOWN_TRIGGERS", "fixture_cold_load": "RED_UNKNOWN_TRIGGER_AND_CREATE_CHARACTER_POSTVALIDATE",
        "variable_usage_E": "RECORDED_SEPARATELY_NOT_EXEMPTED", "error_classification": errors,
        "input_counts": {"production": 34, "entry_fixture": 7, "i2_fixture": 7},
        "input_provenance": "Actual mounted content matched every PREPARED SHA; I2 fixture is candidate-001 as actually loaded, not later candidate-002 repair.",
        "actual_pid": 19184, "actual_process_create_time": 1791105678.3486943, "actual_hwnd": 2295626,
        "native_played_character_id": None, "campaign_started": False, "native_attached": False, "native_tool_calls": 0,
        "root_mouse_or_keyboard_input": False,
        "foreground_actions": {"SetForegroundWindow_attempts": 2, "status": "OPERATOR_REPORTED_FAILED_NO_SUCCESS",
             "raw_tool_output_in_package": False, "boundary": "Two failures reported by root tool output; no independent stdout/stderr or successful focus receipt exists locally. Source helper is preserved; no synthetic execution receipt created."},
        "loading_complete": "NOT_PROVEN", "loaded_lobby_filename_boundary": "Actual PNG is Steam foreground obscuring CK3; filename does not prove CK3 lobby loaded.",
        "not_run": ["ordinary Robert campaign identity", "formal I2 proposal/consent/cancel/reject/apply flow", "D+1", "D+30", "save/reload", "native typed decision/interaction initiation"],
        "lifecycle": {"status": "CLOSED", "close": "posted WM_CLOSE; later independent process exit confirmed; no kill",
             "keeper_sequence": 2686, "cas_sequence": 2687, "cas_resources": [], "allocator_status": allocator["status"],
             "allocator_run_id": allocator["run_id"], "allocator_execution_id": allocator["execution_id"], "allocator_sequence": 4,
             "campaign_save": "NOT_STARTED; no save/flush credit"},
        "requested_settings": prepared["settings_requested"], "post_exit_settings_file_readback": setting_readback,
        "autosave_requested_actual_mismatch": setting_readback["autosave"] != prepared["settings_requested"]["autosave"],
        "pre_post_error_equal": digest(RUN / "loading-red-before-exit/error.log") == digest(RUN / "userdir/logs/error.log"),
        "copied_originals": list(COPIED.values()),
        "generator_side_effects": {"tracked_written": False, "game_called": False, "ci_queried": False,
                                   "originals_modified": False, "png_resized_or_edited": False},
    }
    write("report.json", report)

    roots = [("actual-run", RUN), ("keeper", KEEPER), ("production-build", Path(prepared["production_input"])),
             ("entry-fixture-candidate", Path(prepared["fixture_input"]).parents[1]),
             ("i2-fixture-candidate", Path(prepared["i2_fixture_render_report"]).parent), ("official-ci", CI)]
    extra_files = [Path(prepared["production_manifest"]), Path(prepared["production_zip"])] + [BASE / name for name in
        ("prepare_r0004.py", "live_control_r0004.py", "screen_lease_entry_r0004.py", "r4_prelaunch_review.py", "r4_focus_capture.py",
         "r4_normal_loading_exit.py", "record_r4_status.py", "prepare_r4_loading_red_package.py")]
    inventory = {}
    for label, root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                key = str(path.resolve())
                inventory[key] = {"root_label": label, "relative_path": path.relative_to(root).as_posix(), "source": key,
                    "bytes": path.stat().st_size, "sha256": digest(path), "projected": key in COPIED,
                    "projection": COPIED.get(key, {}).get("projection"), "omission_reason": None if key in COPIED else omission_reason(path)}
    for path in extra_files:
        key = str(path.resolve())
        inventory[key] = {"root_label": "explicit-auxiliary", "relative_path": path.name, "source": key,
             "bytes": path.stat().st_size, "sha256": digest(path), "projected": key in COPIED,
             "projection": COPIED.get(key, {}).get("projection"), "omission_reason": None if key in COPIED else omission_reason(path)}
    write("full-external-index.json", {"schema": "ck3.lyd.r4-original-source-index.v1", "roots": [{"label": label, "path": str(path)} for label, path in roots],
          "files": list(inventory.values()), "boundary": "All files in named actual R4 roots plus explicit auxiliaries are hash-indexed, including every omission. Historical other runs and whole-repository/game binaries are outside this index scope; originals remain untouched."})

    counts = {(row["category"], row["domain"]): row["entries"] for row in errors["counts"]}
    with (OUT / "REPORT.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("# 礼与道 R0004：冷加载失败，未进入正式流程\n\n")
        stream.write(f"本轮结论为 **NATIVE_LOADING_RED**。实际冻结提交 `{COMMIT}`，产品树 `{TREE}`；CK3 1.20.0.3 / build 25652598。两套[官方 L0 CI](ci/README.md)已成功，但实际冷加载出现产品与夹具错误，不能据静态成功给实机通过。\n\n")
        stream.write("实际加载输入为 34 个生产文件、7 个普通入口夹具文件和 7 个 I2 输入夹具文件，逐项匹配[原 PREPARED 哈希](inputs/PREPARED.json)。生产 [manifest](inputs/production.manifest.json) 与两份夹具渲染报告原样保存；I2 使用实际加载的 candidate-001，后来的修复候选未混入。\n\n")
        stream.write("## 实际报错\n\n")
        stream.write(f"[退出后的 error.log](logs/post-exit/error.log)共 **{errors['E_header_count']} 个 `[E]` header**、{errors['source_bytes']} bytes，SHA `{errors['source_sha256']}`。分层详情在[分类账](error-classification.json)，计数不把 game.log 复本再加一次，不把重复实例当独立根因。\n\n")
        stream.write("| 层次 | 实际条目 | 判定 |\n| --- | ---: | --- |\n")
        stream.write(f"| 产品 unknown trigger | {counts['PRODUCT_UNKNOWN_TRIGGER', 'production']} | `has_same_core_doctrines` 两条及 `divergence…` 两条，来自生产 consent trigger；产品冷加载 RED |\n")
        stream.write(f"| I2 夹具 unknown trigger | {counts['FIXTURE_UNKNOWN_TRIGGER', 'i2-fixture']} | 夹具里的 `has_same_core_doctrines` 未被引擎识别 |\n")
        stream.write(f"| I2 夹具 create_character 验证 | {counts['FIXTURE_CREATE_CHARACTER_VALIDATION', 'i2-fixture']} | 两个定义同时指定 employer/location：各一条 Script system error 和 PostValidate；没有 NPC 实际创建信用 |\n")
        stream.write(f"| 产品变量 used-never-set | {counts['VARIABLE_USED_NEVER_SET', 'production']} | 五个 c3 变量各记录两轮；native E，未豁免 |\n")
        stream.write(f"| 产品变量 set-never-used | {counts['VARIABLE_SET_NEVER_USED', 'production']} | c2/c3 原生使用检查，单独保留 |\n")
        stream.write(f"| I2 夹具变量 set-never-used | {counts['VARIABLE_SET_NEVER_USED', 'i2-fixture']} | r4 输入/观察变量，单独保留 |\n\n")
        stream.write("产品 unknown trigger 是生产定义在实际引擎加载时被拒绝，不归入夹具豁免。夹具 employer/location 是定义 PostValidate 失败，不能说 setup 已运行。变量使用条目发生于原生脚本使用检查；它们没有证明实际操作中出现 unset/退款等结果，也没有证据允许忽略。后续修复须另绑新输入，本轮原件不改写。\n\n")
        stream.write("## 执行与界限\n\n")
        stream.write("[实际 launch](run/launch.json)启动 PID 19184/create_time 1791105678.3486943，窗口 HWND 2295626。没有进入 campaign，没有 native attach 或 MCP 游戏调用，没有鼠标/键盘输入。普通 Robert 身份、正式 I2 议案/同意/取消/拒绝/落实、D+1、D+30、保存重载全部 **NOT_RUN**；不得沿用 R3 的实际角色 ID。\n\n")
        stream.write("`loaded-lobby.png` 是原始命名，[实际画面](screens/loaded-lobby.png)中 Steam 处于前景并遮挡 CK3；[元数据](run/loaded-lobby.json)同样记录 Steam foreground，不能证明大厅或加载完成。root 报告两次 SetForegroundWindow 都失败；本地未留独立原始命令 stdout/stderr，也没有成功 focus receipt，因此仅保留[实际 helper 源](source/helpers/r4_focus_capture.py)和此明确证据边界，不制造成功或失败执行回执。\n\n")
        stream.write("启动前[新鲜 Steam 位移原图](offline/steam-moved.png)、[原 freshness receipt](offline/steam-frame-freshness.json)与[root 离线审阅](run/offline-reviewed.json)绑定同一 moved hash，实际标签为离线模式；它们不替代 CK3 加载完成证据。\n\n")
        stream.write("[退出后实际设置文件](inputs/pdx_settings.txt)读到简中、windowed、1600x900、cloud_save=no；autosave=YEARLY，与请求 NEVER 不符。这里仅记录设置文件真实值，未取得 campaign 中的设置 UI 验收。\n\n")
        stream.write("## 生命周期闭合\n\n")
        stream.write("root 于 09:31:52 UTC [posted WM_CLOSE](run/normal-close-request.json)；该请求本身不算退出，随后 09:33:26 UTC [独立进程读回](run/normal-exit-processes-001.json)确认 CK3 列表为空、PID 19184 不存在。没有 process kill，未开 campaign，也没有存档/flush 信用。\n\n")
        stream.write("[keeper FINAL](lifecycle/keeper-FINAL.raw.json) thread_exited=true，failure/entry_error=null，序列 2686；其中 screen_released=false 是 keeper 停止时的原值。[后续 CAS 2687](run/screen-release-completed.json)实际 resources=[]、done、dirty_entries=0。分配器[实际 completed-red 回执](run/allocator-completed-red.stdout.txt)绑定 R0004 / execution 84425881-d38d-4595-a106-9f08799633c2 / sequence 4，于 09:33:52 UTC 写入。\n\n")
        stream.write("## 永久投影与省略\n\n")
        stream.write("本包只逐字节复制必要源文件、原日志、回执、PNG 和 35 文件官方 CI 包；不裁图、不编辑原日志，不复制 DLL/EXE、ZIP、shadercache 或大量 keeper/poll journal。[全部外置索引](full-external-index.json)记录命名 R4 根中的每一个原文件及省略理由；全部原件保留在各自 external 原路径。根目录[JSON 报告](report.json)和 index 绑定投影原字节。本包生成未修改 checkout，未调用游戏、Steam 或 CI。\n")

    files = sorted(path for path in OUT.rglob("*") if path.is_file())
    write("index.json", {"schema": "ck3.lyd.r4-projection-index.v1", "files": [{"path": path.relative_to(OUT).as_posix(),
        "bytes": path.stat().st_size, "sha256": digest(path)} for path in files], "self_boundary": "index excludes itself"})
    # Verify every copied original still equals the projection after full-index reading.
    for entry in COPIED.values():
        assert digest(Path(entry["source"])) == digest(OUT / entry["projection"]) == entry["sha256"]
    files = [path for path in OUT.rglob("*") if path.is_file()]
    print(json.dumps({"directory": str(OUT), "files": len(files), "bytes": sum(path.stat().st_size for path in files),
        "report_sha256": digest(OUT / "REPORT.md"), "index_sha256": digest(OUT / "index.json"),
        "full_original_files": len(inventory), "original_bytes": sum(row["bytes"] for row in inventory.values()),
        "omitted_files": sum(not row["projected"] for row in inventory.values()), "classification": errors["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
