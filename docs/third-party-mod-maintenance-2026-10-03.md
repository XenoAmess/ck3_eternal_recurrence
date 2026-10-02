# 两个三方独立维护版的构建、验收与发布方法

2026-10-03。适用于上游 Workshop `3600021457` 与 `3337428403` 的首次独立维护。本文只记录本仓已有方法和当日环境只读检查；两个产品的功能分析、适配差异、测试计划与报告分别归各自 `mod_<product>/docs/`。本文没有下载、启动 CK3、操作桌面、切换 Steam、上传 Workshop 或证明两个产品已通过验收。

## 可复用的 Auto Upgrade Buildings 做法

[上游冻结](auto-upgrade-buildings-upstream.md) 把下载原件与维护源码分开：原始树保存不变，逐文件记录相对路径、字节数和 SHA-256，另算规范化 tree SHA-256；维护源码删除内层 descriptor 的 `remote_file_id`。来源 item ID 只记录在文档，独立维护版创建新 item，后续只更新维护版 ID。

[维护记录](auto-upgrade-buildings-maintenance.md) 从真实游戏定义诊断变化，分别保存上游基线、维护判断、修复、静态门禁、外置实机夹具和失败 attempt。建筑产品的具体链数、作用域和费用策略不能复制为其他产品结论，但下面这些边界适用：

- 没有旧存档迁移时，保留玩家存档使用的事件 ID、flag、变量与稳定标识；内部实现可改为独立命名空间。
- 只上传明确 runtime allowlist 的 production staging。源码工具、docs、夹具、失败日志和原始来源不进入 staging。
- 发布 manifest 记录产品、版本、完整 Git commit/tag、维护版 item ID 和逐文件 size/SHA。ZIP 固定时间、路径顺序和压缩参数；两个临时构建的 manifest/ZIP bytes 必须相等。
- 实机使用独立 `-userdir`、生产 staging 加外置 fixture，核验实际加载顺序、运行前后产品及 fixture 树、日志、真实用户与 Steam 存储不变。验收数值由原生状态、脚本 PASS/FAIL marker、存档或 MCP 回读成立。
- 历史 CK3 1.19 报告只能作为方法参考，不能外推为此次 1.20 实机通过。

参考实现为 [build_auto_upgrade_buildings_release.py](../tools/build_auto_upgrade_buildings_release.py)。其 `--check` 做双构建；`--release` 要求产品源码 clean 且预期 tag 指向 HEAD；`--verify <tree> --manifest <manifest>` 校验产物，`--workshop-cache` 才允许该产品合同明示的 Launcher descriptor ID 注入差异。原生 uploader 没有注入 ID 时，缓存应严格逐字节匹配，不能先规范化再声称相等。

新产品根目录包含 `docs/`，所以 builder 的 source allowlist 必须明确承认该非运行时目录；不能照抄 Auto Upgrade Buildings 当前仅允许 `README.md` 的 `SOURCE_ONLY_FILES` 后，把用户要求的产品 docs 当异常。runtime allowlist 仍精确列文件。

本次新增共享 [independent_mod_release.py](../tools/independent_mod_release.py)，由两产品的薄 wrapper 提供自己的固定清单与源路径：

```python
from pathlib import Path
from independent_mod_release import ProductSpec, build, check_reproducible, verify_manifest

spec = ProductSpec(
    product_id="mod_example",
    source=Path("mod_example"),
    runtime_files=frozenset({"descriptor.mod", "events/example.txt"}),
    upstream_item_id="3600021457",
    tag_prefix="example-v",
)
staging, manifest_path, zip_path, payload = build(
    spec, Path("dist/attempt-01/mod_example"), revision="<full lowercase commit SHA>",
    workshop_item_id=None,
)
check_reproducible(spec, revision="<full lowercase commit SHA>")
verify_manifest(spec, staging, manifest_path)
```

`build` 的 output 是精确 staging 路径；已有 staging、manifest 或 ZIP 拒绝覆盖，新 attempt 使用新目录。`README.md`、`docs/**`、`tools/**` 是允许的 source-only 文件，永不复制；未审阅 runtime 额外文件拒绝。清单记录 descriptor 版本，正式 wrapper 可以在确认 clean 源和 exact tag 后传 `git_tag=product_tag(spec, version)`。此共享层不创建 tag、不猜生成器、不启动游戏、不上传；`verify_manifest` 对原生上传后的缓存按 exact bytes 校验，没有 descriptor 归一化豁免。

`<verified-python> tools/test_independent_mod_release.py` 已通过 9 项聚焦测试，涵盖源文档/工具隔离、固定 ZIP 时间/模式及 bytes 重现、未知源文件与身份泄露拒绝、UTF-8/BOM、同尺寸篡改/缺失/额外缓存文件、错误产品清单、路径冲突和不覆盖已有产物。它们证明构建投影合同，不能替代两个产品的机制及实机验收。

## 当前解释器与版本证据

当日只读依赖 probe：

| 项目 | 实测 |
| --- | --- |
| 选定实体 Python | `C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe` |
| Python | 3.13.15，64 位 |
| MCP SDK | `mcp==2.0.0` |
| 桌面依赖 | Pillow 12.3.0、pywin32 312、psutil 7.2.2、PyAutoGUI 0.9.54、comtypes 1.4.17 |
| Workshop 包 | editable 安装，指向本仓 `ck3_workshop_mcp/src/ck3_workshop_mcp/` |
| 本仓 `tools/.venv` | 当前不存在 |
| 实体 Python 中未安装的包 | requests、websocket-client、xar-promo-toolchain |

`requests` 不是当前原生发布/下载及匿名发布 verifier 的必要依赖；后者使用标准库 urllib。不要为无关能力安装宣传工具链或根据旧机器 `D:/workspace/...` 路径回落。需要依赖型 runner 时先按实际 import 补齐并记录所用解释器；缺包属于 environment RED。

当前游戏目录为 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/`。同机最新独立发布先例 More Tenets Slots (XA) v10 的当次目标是 CK3 `1.20.0.3 (Crozier)`、Steam build `25652598`、EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。两产品仍须重新读取本机 version/build/EXE hash，并由主任务核验最新公开版本；先例不替代当次 pin。

本执行器 `cmd.exe` 对带双引号的 `-c` 多行命令存在参数异常。可靠方式是把临时 Python script 放在 `C:/workspace/two-mod-maintenance-20261003/`，由无空格实体解释器路径执行；路径含空格的调用交给 Python `subprocess.run([...], shell=False)`，stdout/stderr 精确保全。自动化遵守仓库的 Python-only 合同。

## 实机入口可以复用什么

当前 [run_auto_upgrade_buildings_acceptance.py](../tools/run_auto_upgrade_buildings_acceptance.py) 仍 pin `EXPECTED_GAME_VERSION=1.19.0.6`，而且使用 RapidOCR 导航；[run_celestial_commerce_corruption_acceptance.py](../tools/run_celestial_commerce_corruption_acceptance.py) 也有 1.19 descriptor 合同和历史 OCR 操作。它们不是本次两个产品可直接执行的 1.20 runner。

新 runner 可复用这些具体接口，并写自己的 fixture 和后置断言：

| 接口 | 用途 |
| --- | --- |
| `tools/ck3_installation.py: configured_game_dir / configured_game_executable / installed_game_version` | 明确本机配置与游戏版本 |
| `tools/ck3_live_run_id.py: allocate_live_run_id / write_identity_receipt / record_live_run_status` | 独立产品 run 身份；新产品用 `external_mod=True` 或 CLI `allocate --external-mod <slug>` |
| `xar_autoplayer.locking.exclusive_launch_lock(game_exe)` | 按本机 exact EXE 的启动排他 |
| `tools/run_vivhite_acceptance.py: write_outer_descriptor / tree_snapshot / snapshot_digest` | 独立外层 descriptor 和树完整性 |
| `tools/run_terminal_acceptance.py: real_profile_snapshot / steam_userdata_root / steam_cloud_snapshot / verify_storage_stability` | 真实用户和 Steam 存储前后保护 |
| `tools/desktop_coordinate_map.py` | 原图与实时桌面尺寸独立换算，点击须写 receipt |
| `tools/desktop_steam_offline_recovery.py inspect / recover` | 桌面采集新鲜度取证，之后直接审阅新图的“离线模式” |

同机先例 `C:/workspace/ck3_mod_more_tenant_slots/dev_tools/live_session.py` 展示 production build、独立 userdir、warm `pdx_settings.txt`/shadercache 复制、task bus 屏幕独占及 30 秒 heartbeat、launch lock、只关闭本轮 PID。该脚本始终只记录 `launched-unverified` / `process-exited-unverified`；产品验收另由日志、存档、MCP 与截图报告成立。它的固定产品 build 和 `more_tenets_slots_xa_dev` 不能直接用于本次产品。

More Tenets Slots R0013 的实际回执是原图映射和已确认前台/英文布局的物理扫描码，存档证明来自游戏冷载后原生文本保存；没有 injected DLL、native pipe 或 MCP wire。因此该轮不能作为 native MCP 注入已在本机 1.20.0.3 通过的先例。

游戏原生 MCP 的可 import 入口是 `xar_autoplayer.bridge.native_driver.NativeHeadlessGameplayDriver`、`NativeNamedPipeServer` 和 `xar_autoplayer.bridge.mcp_server.create_server`；实体 Python 显式加入 `ck3_autonomous_player/src` 后可用官方 SDK `async with mcp.Client(create_server(driver))`。driver 先建立独立 pipe，再由受管 `runtime.launch` 启动。通用 `operator_mcp_server.py` 的 frozen-job handoff 不能生成游戏内部 GUI。Python 服务中存在 `ck3_query_frontend_gui_route_v1`、`ck3_inspect_frontend_gui_tree_v1`、`ck3_activate_frontend_new_game_v1` 与 `ck3_activate_frontend_start_1066_bookmark_character_v1`，但 `tools/list` 只证明服务暴露了接口；当前 DLL 的 live hello 必须实际公布其 required capability，才能调用。

本机较新的 .3 静态基线是 `_runtime/native-12003-nullscope-final-qualification.json`，冻结源码 `C:/cb123n2`，来源 base commit `641d54997877d4125049fb34bde85aeaa7664b93`，完整 native source tree SHA-256 `a0567c4ea859c6ceb6d8eb5101c77d01e285294752abc33b98175c4e922aee35`。该记录明确 `live_validation_executed=false`。早期 `C:/cb123` / `C:/cn123` 和 `_runtime/native-12003-final-qualification.json` 不应被写成最新基线；旧 `_runtime/native-c2-artifacts/artifact-binding.json` 更标为 `linked_full_build_red`。

本次为了固定 Robert 1128 的入口，用同一 n2 冻结源在全新 `C:/ctmr3` 构建，开启 `XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1`、`XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1`、`XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1`。外置证据根为 `C:/workspace/two-mod-maintenance-20261003/native-robert-12003-v2/`：

| 文件或证据 | 精确身份与范围 |
| --- | --- |
| `qualification.json` | SHA-256 `5f3ae9b8cb567e3ec9f7b250003c4995ea782eadaab2157fcfd33c39ef898678`；configure/build/dependency/source 门禁及限定的 11 项 CTest 通过，未执行 live |
| `public-frontend-unit.json` / `.log` | 当前 Python 消费者的 12 项 mock 测试通过，包含 Robert 精确 key、单次选择/开局及独立暂停后置读回合同 |
| `pins.json` | 新 DLL/injector、exact .3 EXE、源码 fingerprint 与三个编译开关；旧 n2 产物另已逐字节复验保持不变 |
| `C:/ctmr3/xar_ck3_bridge.dll` | 4,085,760 bytes；SHA-256 `55b53bb4eb3e71a6a23bcc97c8798fc0124c728e3a298552d11fef25ca918192` |
| `C:/ctmr3/xar_ck3_bridge_injector.exe` | 39,936 bytes；SHA-256 `a4688e442f454090fcac2cf18a3ea2e19cc84a93bb710dfb855a09a6cc760acd` |

上述静态通过不等于 .3 live frontend 可用。以下 native 行号都指 `C:/cb123n2/ck3_autonomous_player/native_bridge/src/` 下精确冻结副本，仓库链接用于查找对应实现。冻结 [ck3_12003_adapter.cpp](../ck3_autonomous_player/native_bridge/src/ck3_12003_adapter.cpp) 第 17–20 行继承 `Ck3_12002AdapterDescriptor().capabilities`；[ck3_12002_adapter.cpp](../ck3_autonomous_player/native_bridge/src/ck3_12002_adapter.cpp) 第 14–82 行没有 frontend 能力及上述开关分支。frontend 能力和两个开关条件实际位于 [ck3_11906_adapter.cpp](../ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp) 第 161–172 行，作用于 1.19.0.6 descriptor；Robert 开关只选择模型的固定人物 key。[bridge.cpp](../ck3_autonomous_player/native_bridge/src/bridge.cpp) 第 1775–1781 行直接枚举当前 descriptor 的能力生成 hello。因此编入函数和步骤映射不会把 frontend 能力加入 .3 descriptor，等待菜单就绪也不会改变该静态清单。

本次真实 `mod_change_holding_types` R0002 的证据根为 `C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0002/session/`。`002-diagnostics-result.json` 证明 pipe 已连接，hello 的 adapter 为 `ck3-1.20.0.3-msvc-x64`、`ready`、exact EXE 匹配，公布 `game.adapter.exact-build`，未公布 frontend 能力。`001-route-result.json` 的实际工具结果为 `isError=true`：`native DLL does not advertise required capability game.command.query-frontend-gui-route-v1`；`transport_ok=true` 只证明 MCP 通道正常。[native_driver.py](../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py#L9071) 第 9071–9076 行在向 DLL 提交前按 hello 拒绝，所以这次并未验证 C++ frontend executor 的 live 行为。`native-wire.jsonl` 保留了实际 DLL 握手与状态 wire。

本次可用路线应据此记录为：原生注入/握手通过，受管 .3 frontend 未注册而不可用；使用当次 fresh 原始截图与 `desktop_coordinate_map.py` 回执导航，再以实际地图 snapshot、暂停/时钟及 inbox marker 验证产品。每一项原生地图或 inbox 能力仍以本轮实际回读为准，不能由握手或静态测试外推。Robert 的正确 key 是 `bookmark_rags_to_riches_duke_robert`，本机官方 `00_bookmarks.txt` 对应 `history_id=1128`、`d_apulia`；Murchad 为 83355，不能替代指定 Robert 用例。

[MCP fixture harness](ck3-1.20.0.2-mcp-live-harness.md) 的 `ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py` 可消费显式干净 source、当前游戏目录、独立 state/pipe、DLL/injector、`--fixture-profile` 和自定义 plan，保留官方 MCP wire、session 与 native wire。产品生产 staging、外置 fixture 和 warm profile 必须先由协调者装入新 `state-dir/profile/`；该 runner 等到 playable 后才执行 plan，不能用它的 plan 导航前端。`--native-fixture-inbox` 或 write-inbox 步骤的 `native_run=true` 使用固定 `fixture-run-inbox-v1`，原生执行 `run xar_mcp_inbox.txt`，输入位置为隔离 `profile/run/xar_mcp_inbox.txt`。这一原生触发不依赖 mod_bridge；旧 GUI polling 路线才需要 mod_bridge。原生结果的 `native_executed=true` 仍须等待本轮新增长度之后的 debug marker 和产品断言，再恢复 no-op；它不是任意 console 命令入口。脚本名称带 12002 不证明 .3 ready，仍须在本次 exact .3 文件和 source binding 上执行实际实机并如实记录结果。

每个产品报告应记录 exact CK3 pin、源码/staging/fixture SHA、实际挂载、用例与 expected/actual、原生诊断和 marker、截图、失败分类及未覆盖项。功能型用例需要至少覆盖正常路径、拒绝条件、停用或不适用路径；涉及持久状态时补保存与独立冷重载。出现确定性 parser/validator 可覆盖子集时先做 Open Kaishek 离线预验，报告其 commit、profile、输入 SHA 和不支持项；未覆盖语义写 `not-applicable` 及原因，不能冒充实机通过。

## 本机 MCP 与 Steam 模式控制入口

本次只读检查未在当前 `C:/Users/Administrator/.codex/config.toml` 找到 `mcp_servers`，实际进程中也未找到 `operator_mcp_server.py`，所以不能声称主仓通用 operator HTTP 已在本机运行。

主仓通用入口是 [operator-mcp.md](operator-mcp.md) 和 `ck3_autonomous_player/operator_mcp_server.py --profile <仓库外 profile>`；其接口只执行 profile 冻结的 job。新 profile 必须先读 capabilities/status/preflight，当前身份、输入及输出通过后再 handoff。它不提供 Steam 在线/离线切换。

同机已存在可通过官方 in-memory MCP client 使用的独立套件入口：

```text
C:/workspace/ck3_damengsan_suite/.venv/Scripts/python.exe C:/workspace/ck3_damengsan_suite/tools/call_suite_operator_mcp.py --tool <tool> --arguments-file <JSON>
```

该 venv 实测 Python 3.13.15，已有 MCP 2.0.0、上述桌面依赖、websocket-client 1.9.2。这里可用的通用 Steam/窗口 tools 是 `suite_steam_status`、`suite_steam_footer_status`、`suite_ui_inspect`、`suite_foreground_ui_inspect`、`suite_steam_menu_open` 和 `suite_steam_mode_select`。无参数 tools 的 arguments 文件为 `{}`；模式参数为 `{"mode":"online"}` 或 `{"mode":"offline"}`。控件 Invoke 或 mode ACK 后必须重新读回实际状态并审阅当次新图。

套件自身的 CK3 prepare/launch、固定画布动作和 Workshop Console 下载受套件产品 allowlist、run/PID 与 build 合同限制，不拿来加载本次两个产品，也不照搬截图坐标。它的 `suite_steam_force_offline_restart` 会编辑本机 VDF，和以下最新官方菜单成功先例不同，不能凭名字当作已验证的本次恢复路线。

最新成功先例在同机 `C:/workspace/ck3_mod_more_tenant_slots/docs/workshop/publication-v10.md`，完整回执在 `artifacts/workshop-v10/steam-offline-verification.json`：2026-10-03 06:29（本地）恢复离线并直接审阅新图；CK3 为 0，窗口位移改变实际像素。官方“进入离线模式”此前无状态变化，实际闭环使用正常 Exit Steam、原生 Cancel 关闭已确认父进程不存在的七个孤儿 Crash Reporter、保全 crash 文件 SHA、保留 `-cef-disable-gpu` 重开客户端、官方菜单切换，8 秒后才从鲜图确认离线。见 [恢复实证](ck3-native-ai/desktop-steam-offline-recovery-2026-09-27.md)。没有 A/B 证明单一根因，后续也不能直接套用旧窗口/PID。

tenant slots 仓库没有常驻 online/offline Python helper：当前 `dev_tools/` 只有迁移、构建、localization/padding 与 live_session 工具。上述模式工具和框架 freshness 工具是可复用实现，截图及收据是该次成功证据。

## 原生下载与首次发布

主仓 [ck3_workshop_mcp](../ck3_workshop_mcp/README.md) 提供真实 Steamworks MCP，实体 Python 已可 import。通过 `call_tool` 调用官方 MCP client，无需配置常驻 server：

```text
<verified-python> -m ck3_workshop_mcp.call_tool --provider steam-native --tool workshop_native_symbols --arguments-file <symbols.json>
<verified-python> -m ck3_workshop_mcp.call_tool --provider steam-native --tool workshop_native_probe --arguments-file <probe.json>
<verified-python> -m ck3_workshop_mcp.call_tool --provider steam-native --tool workshop_native_download --arguments-file <download.json>
<verified-python> -m ck3_workshop_mcp.call_tool --provider steam-native --tool workshop_native_publish --arguments-file <publish.json>
```

symbols 参数只有 `dll_path`；probe 加 `app_id=1158310`。DLL 使用本机游戏 `binaries/steam_api64.dll`。只在当次子进程环境设置 `SteamAppId=1158310`、`SteamGameId=1158310`；不创建 appid 文件、不自动启动 Steam/CK3。symbols 仅审阅 PE，probe 会载入 DLL 访问现有授权会话。

[download 合同](workshop-native-download.md) 的参数为：

```json
{
  "dll_path": "C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/steam_api64.dll",
  "item_id": "<exact item ID>",
  "app_id": 1158310,
  "timeout_seconds": 300,
  "expected_cache_path": "<absolute path ending in the exact item ID>"
}
```

`expected_cache_path` 必须在下载前不存在；上游已有缓存或维护版缓存要先完整保全并移到明确旧目录。工具不会清理、移动或订阅；没有 freshness 要求时可省略该参数，由 Steam 回报安装路径。未订阅物品可能进入临时缓存，以上路径不是下载目标 setter。完成要求精确 callback `3406` 的 AppID/item ID 匹配且 EResult 1，随后 installed=true、needs_update/downloading/pending=false，GetItemInstallInfo 的目录存在。MCP envelope `ok=true` 仍可能业务 `result.ok=false`，必须检查内部结果。

首次 publish 的 MCP 参数为 `dll_path`、`plan_file`、全新 `receipt_file`。plan 包含 `operation_id`、`operation="create"`、`app_id=1158310`、`target_item_id=null`、title、description_path、content_path、preview_path、visibility `0`、tags、完整 change_note 与实际 legal agreement 状态。content_path 只指正式 staging。receipt 会在 Create 前持久化 intent、拿到新 ID 后先保存再提交内容；unknown callback 先回读并保留收据，不自动再次创建。

原生真实 create/update 已在 Auto Upgrade Buildings 完成；同机最新 download/update 成功先例是 More Tenets Slots v10，精确公开 Notes、CDN 媒体、fresh 46-file cache 和离线恢复分别验过。但每次新 item 仍须有自己的实际提交、匿名公开与缓存证据。

## 每个产品的发布闭环

每个独立维护版分别执行：

1. 把 `upstream.md`、`feature-analysis.md`、`compatibility-plan.md`、`test-plan.md` 和最初未运行状态写入产品 `docs/`，冻结原始来源及 exact 游戏 pin。
2. 按产品分析改动并完成静态门禁、可复现构建、新 fixture、受管离线实机；把 actual 证据及限制写入其 `test-report.md`。
3. 提交/标记冻结产品源码；正式 staging/manifest/ZIP 与待发布标题、完整 BBCode、完整 Steam Change Notes 各自冻结 size/字符数/行数/SHA。
4. 发布新的 Workshop item，保存创建 ID、receipt；canonical ID 只写用户目录外层 `.mod`，不进入仓库内层 descriptor。
5. 用 [verify_workshop_publication.py](../tools/verify_workshop_publication.py) 匿名精确回读 title/description 与 changelog entry 全文。CLI 为 `--item-id --title --description --change-notes --output`，含空格 title 通过 Python argv 传递。EResult 1 不证明 Notes 已公开；已有条目未替换时走登录 owner page 并重复匿名回读。
6. 使用新的 native download 回报路径与 frozen manifest 校验 exact inventory/size/SHA；预览媒体分别验其实际 CDN。上传后重建干净无内层 ID 的 staging。
7. 联网任务完成或终止立即恢复 Steam 离线并保存当次鲜图/审阅收据。每个产品 `docs/release-report.md` 回链所有实际证据。
8. 在根 `docs/release-changelogs/<product-key>/<version>.md` 保存永久 initial baseline，记 item、版本、发布日、tag/commit、玩家变化、兼容、限制、构建与实机/公开证据；产品 docs 可以回链该权威文件。changelog 与发布文档提交、推送 `master` 才完成 release。

以上步骤分别闭环两产品，不用一个产品的 GREEN、item、缓存或 Notes 替代另一个产品。
