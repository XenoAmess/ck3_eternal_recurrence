# 本机项目 EXE 永久排除与构建登记

2026-10-05，项目所有者明确授权现在及后续对本项目构建的 EXE 使用永久 Windows Defender 排除。授权范围是有项目构建来源的完整 EXE 文件路径。排除设置不代替构建测试、运行信任或误报裁定；第三方工具、解释器、Steam、CK3 本体、DLL、整个目录及全机扩展名不由此纳入。

## 已实际登记的 238 个路径

Root 通过系统 UAC 确认取得管理员 token，在同一个管理员 Python/WMI 会话内读取设置、追加缺失路径并再次读取。最终回执时间为 `2026-10-04T19:07:43.454021+00:00`：238 个项目 EXE 路径全部存在，原有 128 个保持，新增 110 个；既有 ExclusionPath 保留，ExclusionExtension 和 ExclusionProcess 未变。此事实来自实际设置回执，不是静态清单或调用 ACK。

本机外置证据根为 `C:/ck3-war-episode04-research-20261004-a01/`，原字节永久保留：

| 证据（相对该根） | SHA-256 |
| --- | --- |
| `defender-project-exe-inventory-a01/confirmed-project-exes-worktrees-a02.json`：238 个实际项目 PE EXE、236 个不同内容哈希 | `219cff2e0c2fad554084a374934ec6ef1cbf98b0edc7d9ac33cb46b1511618ea` |
| `apply_defender_worktrees_a02.py`：管理员实际执行方法及输入 pin | `05de76c91559dde31b734a6f54d200201af6f10252d71e6789e2095b14a87b18` |
| `defender-project-worktrees-a02/before.json` | `7a05bf6d08a13390d1579bb58e052ae235b88e4b95b61ec4b68908f85b45090e` |
| `defender-project-worktrees-a02/after.json` | `379e7bf1f8c90f652279d713f7e1e4bd9a89b5e9638c69787930046f058d3c0d` |
| `defender-project-worktrees-a02/result.json`：admin=true、setting_success=true、missing_after=[] | `61850c13118bf8e317a65968de0bab1915e0d3969b7a4d9d95bb5d34d2ee3edf` |

清单中的每条路径经过项目 CMake target 或实际 CL/link 输出来源、DOS/PE header、非 DLL 及稳定字节检查。254 个文件名候选中，16 个第三方 CMake CompilerId 探测程序被排除。已隔离且当前不存在的旧 injector 仅保留历史身份，不恢复它们，也不把永久排除写成误报已裁定。

## COM 返回值与权限视角纠正

真实 `service.ExecMethod('MSFT_MpPreference', 'Add', params)` 调用已经写入首批 128 个路径，但返回 None；Root 随后的返回对象解码错误不能改写成“未生效”。后来使用 `cls.ExecMethod_('Add', params)` 同样返回 None，管理员实际 after 仍完整验证 238 个。helper 采用后一个已实际验证的方法。

普通 token 的 WMI 视角曾把 ExclusionPath/Extension/Process 隐藏为空数组。空数组不能证明设置不存在，也不能覆盖管理员 before。生产 helper 因此在普通 token 下明确返回 `settings_failed` 与 `admin_required_for_verified_readback=true`，before/after 为 null，且不连接 WMI、不尝试 Add。验收必须使用同一管理员 token/client 的实际前后读回。

None 被记录为 `return_object_absent=true`、`return_value_available=false`，不伪造 ReturnValue=0。无返回值或返回解码异常时，先 fresh readback 该路径及已观察的旧项，再考虑下一个不同路径。调用异常后也先 fresh readback：完整生效可标 verified，但保留异常事实；部分生效列出已存在/缺失路径并停止。任何情形都不自动重发 Add。正常返回值也必须以最终实际读回验收。

## 本次接入的构建范围

[公共 helper](../../tools/register_project_exe_exclusions.py) 默认关闭。只有此机此 repository 的 Git-local `xar.defenderProjectExeExclusions=true` 启用登记；linked worktrees 读取同一个 local config，其他 clone/机器及 CI 不自动继承授权。2026-10-05 本机从“键未设置”改为 true 并实际读回；配置回执位于上述根的 `defender-integration-a01/evidence-and-local-config.json`。生产代码不写死本机授权。

```text
git config --local xar.defenderProjectExeExclusions true
git config --local --bool --get xar.defenderProjectExeExclusions
```

成功构建后、运行所产夹具前接入以下 6 个真实 producer：

| 入口 | 已声明输出来源 |
| --- | --- |
| [run_native_msvc.py](../../tools/run_native_msvc.py) | CMake File API codemodel-v2 的实际 selected-target closure 与 EXECUTABLE artifacts |
| [build_fresh.py](../../ck3_autonomous_player/native_bridge/tools/build_fresh.py) | configure 前请求 codemodel；成功 build 后按实际四个 focused targets 或 all 登记 |
| [check_native_army_routes_ci.py](../../tools/check_native_army_routes_ci.py) | 实际成功 CL `/Fe` |
| [run_battle_active_counter_fixture.py](../../tools/run_battle_active_counter_fixture.py) | 实际 CL `/c` 源/对象链及 link `/OUT:` |
| [run_projected_contact_scope_fixture.py](../../tools/run_projected_contact_scope_fixture.py) | 同上；启用登记时重编 3 个已声明 unit，保留其 actual producer；默认关闭仍允许既有对象 reuse |
| [realm_law_action_mailbox fixture](../../ck3_autonomous_player/native_bridge/tools/test_ck3_12002_realm_law_action_mailbox.py) | 两个既有并行 configuration 各自实际成功 CL `/Fe`；当前 worker 初始化 COM |

CMake 只接受本 checkout native_bridge，或明确命名的外置 candidate；核对 source/build identity、目标及文件当前 hash。Direct CL/link 只接受实际成功命令的绝对输出操作数及每个实际 source/object 的 pin；外置或不同 source root 必须由 caller 明确命名。它们均不扫描输出目录，不把 CompilerId、任意 EXE 文件名或任意目录自动加入。

返回状态是 `disabled|verified|settings_failed`。开启登记后，普通 token 的新构建仍可能编译成功，但登记报 admin-required 并整体非零；报告保留 `build_succeeded` 和独立登记 receipt。hook 不自动触发 UAC。因此本次接入不等于“全部未来 EXE 自动登记完成”。

另外 161 个旧研究生产器尚未接入这 6 个入口：153 个 direct CL `/Fe`、6 个 direct link `/OUT:`、1 个项目测试 EXE 的 direct CMake、1 个 DLL-only CMake。160 个实际产出项目 EXE；27 个只借用 run_native_msvc 的环境初始化，实际不调用其成功 build hook。后续运行它们时，须逐条接入 helper，或由 caller 冻结实际成功命令/target manifest 再显式管理员登记；不能把导入 MSVC 环境视为已覆盖。完整 source 分组见外置 `defender-project-exe-inventory-a01/research-entry-readonly-a01/research-exe-producers-a02.json`，SHA `2f88d0117f2ea12e23d35a753b3032ac46884a64770d3c9cbe6fd1936a8db68a`；摘要 `GROUPS-a02.md` SHA `ca209a9850afc493c6fa69f6654ef19bcf8add112352fd6e1102c3da74825b11`。

旧环境调用方确实按文件路径载入 MSVC module，例如 [feast-costs producer](../../ck3_autonomous_player/native_bridge/research/run_ck3_12002_activity_feast_costs_tests.py) 第 12–15 行（未修改 source SHA `80c73e34b09adf3acb5067aaaef49bb9bd4294b140df1ee0a65e81a5098abb65`）。新 run_native_msvc 显式加入自己的 tools 目录后才导入 sibling helper，保持这种加载方式可用；隔离 import 回归只验证环境接口仍可加载，并不登记其自行编译的 EXE。

## 新输出的显式 native UAC 登记

构建 hook 将冻结 manifest 和失败 receipt 留在该次 build 的 `defender-exe-exclusions/<new-attempt>/`。选取其中精确 `manifest.json`，另给一个尚不存在的 receipt 路径。原失败 receipt 保持原样。直接在已有管理员终端执行本仓库 venv 的 helper CLI 也可完成同一过程：

```text
tools\.venv\Scripts\python.exe -B -X utf8 tools\register_project_exe_exclusions.py --manifest C:\actual-build\defender-exe-exclusions\actual-attempt\manifest.json --receipt C:\actual-build\defender-exe-exclusions\admin-attempt\receipt.json
```

上面的路径需替换为该次实际 manifest 和新的 receipt。从普通 token 发起时，可将下面 Python 保存到新外置 attempt 的 `register_uac.py`，用本仓库 venv 解释器执行并传这两个实际路径。该脚本仅在被明确执行时通过原生 ShellExecuteEx/runas 提出系统 UAC，Python 窗口隐藏；取消会报错，既不绕过确认也不更改策略。本次代码/文档集成没有执行此脚本或提出 UAC。

```python
import json
from pathlib import Path
import subprocess
import sys
import pythoncom
import win32api
import win32event
import win32process
from win32com.shell import shell, shellcon

repo = Path("D:/workspace/ck3_eternal_recurrence")
manifest = Path(sys.argv[1]).resolve(strict=True)
receipt = Path(sys.argv[2]).resolve()
if receipt.exists():
    raise FileExistsError(receipt)
pythoncom.CoInitialize()
handle = None
try:
    child = shell.ShellExecuteEx(
        fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
        lpVerb="runas", lpFile=str(repo / "tools/.venv/Scripts/python.exe"),
        lpParameters=subprocess.list2cmdline([
            "-B", "-X", "utf8", str(repo / "tools/register_project_exe_exclusions.py"),
            "--manifest", str(manifest), "--receipt", str(receipt)]),
        lpDirectory=str(repo), nShow=0)
    handle = child["hProcess"]
    if win32event.WaitForSingleObject(handle, 60000) != win32event.WAIT_OBJECT_0:
        raise TimeoutError("Administrator helper still running; preserve attempt, do not resubmit")
    exit_code = win32process.GetExitCodeProcess(handle)
    result = json.loads(receipt.read_text(encoding="utf-8"))
    if exit_code or result.get("status") != "verified" or not result.get("admin_token"):
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    print(json.dumps({"exit_code": exit_code, "receipt": str(receipt),
                      "status": result["status"]}, ensure_ascii=False))
finally:
    if handle is not None:
        win32api.CloseHandle(handle)
    pythoncom.CoUninitialize()
```

```text
tools\.venv\Scripts\python.exe -B -X utf8 C:\actual-attempt\register_uac.py C:\actual-build\defender-exe-exclusions\actual-attempt\manifest.json C:\actual-build\defender-exe-exclusions\admin-attempt\receipt.json
```

ShellExecuteEx 的启动成功只证明进程启动；上面另外要求 child exit 0、exact new receipt status=verified 和 admin_token=true。登记 helper 重核 manifest、source/target/output byte pins并在同管理员 client 内读回。超时、取消、partial mutation 或源/输出改变都保留回执，禁止盲重试。

## 验证与方法来源

外置公共 helper 包 `defender-exe-hook-a01/ROOT-DELIVERY-a08.json` SHA `d202d9ea8682118318683462cd5bfb70ccbbaf8f18efb6b9c43c0af65613b08c`；五入口包 `defender-build-wrappers-a01/ROOT-DELIVERY.json` SHA `d7d22fd1c0fb1903e2a626acd5cff2a238e5c29a5c1ecdf6577fc30cd5469f3d`。历史验证、失败 attempts、原始 source 及素材均保留。本次主树集成的 34 项 helper/provenance fake-WMI 测试、追加 1 项隔离动态 import 回归、五 wrapper 的 21 个 fake adapter 场景及 Python-only 全树校验均通过，回执位于外置 `defender-integration-a01/`。8 个实施文件与文档 Python 示例语法检查通过；示例未执行。不实际运行 compiler、生成 EXE、连接 WMI、改 Defender、操作 CK3 或修改冻结 Cf。

官方方法来源：[Microsoft exclusions](https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-exclusions-configure)、[MSFT_MpPreference Add](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/defender/add-msft-mppreference)、[CMake File API](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html)、[ShellExecuteExW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shellexecuteexw)、[SHELLEXECUTEINFO](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-shellexecuteinfow)。实际 None/权限视角由上述本机证据纠正，不能只按 ReturnValue 的文档预期推断。
