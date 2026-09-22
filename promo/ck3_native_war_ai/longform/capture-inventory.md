# 战争片既有素材与新拍入口盘点

2026-09-22；只读检查时工作区 HEAD 为 `4456c3adb31f70c3b09526f24c6e70e02e622f8b`。机器记录见 [capture-inventory.json](capture-inventory.json)。这是文件可访问性、媒体探测与有限画面检查，未启动 CK3、录制新素材、完整观看母带或签核成片。

**本轮选入战争片的既有实机素材为 0。游戏实装存在且 EXE 与研究版本一致；后续实际无启动预检发现旧 DLL 尚未满足本片正式前端入口的能力要求，未进入拍摄。** 可访问的《重整河山》受控验收素材保留在原处，本片不选；不因缺战争画面而混入它们。R01/R03 仍未绑定。

## 可访问但本片不选的素材

共同根目录：`D:/workspace/ck3_reclaim_promo_work/capture/reclaim-promo-acceptance-20260910-a02/`。

| ID／相对路径 | 本轮实测 bytes、SHA-256 | ffprobe 9.0.1 结果 | 来源与选用结论 |
|---|---|---|---|
| OLD-01 `raw-ck3-desktop.mkv` | 1,563,296,736；`49C53A3D6FF1A9CA058BC886FAB51B0F9C16ECAAA240DBB7DB6212798862FE48` | Matroska；1319.733 秒；H.264、2560×1440、30/1 fps、yuv420p；仅视频流 | 《重整河山》受控验收母带，有旧 capture report/timeline。能读媒体头并完成全文件哈希；只查看了既有相关抽帧，没有本轮全片解码或 1× 审片。本片不选。 |
| OLD-02 `acceptance/cell/08_later_dynasty_native.png` | 5,672,802；`7EA9399D015556A234B182D037AD02CD1EAC8ED6B93D77EFEFE35955DC9C674F` | PNG、2560×1440、rgb24；静态图片没有片长；探测器返回的 25/1 不代表录屏帧率 | 已打开确认是暂停的后宋角色与开封附近地图，带通知、角色面板与 tooltip。timeline 对应 1010.152 秒；这只是旧事件锚点，不是已审 clean span。本片不选。 |

同目录 `capture-report.json`（5,282 bytes）实测 SHA-256 为 `26727989A9B308A577C5A49C83A0D04D8F548F05077702A04B296675911BA125`；`capture-timeline.json`（16,434 bytes）为 `78A6BD097405DCCBFC7C783A85E557B351043908A92A3C58FC1C9989225E4EB9`。前者记录旧验收 GREEN 与 11 个非黑抽样，后者为截图／回执事件列表；检查的这两份文件未含 marks、clean spans 或 evidence index，不能假造为通用 CK3 adapter 已接纳的完整 capture bundle。历史成片批准也不适用于新战争片。

另打开了 `D:/workspace/ck3_eternal_recurrence_process_assets/tributary_expansion_directives/runs/tea_workshop_3801490405_R0010/cell/07_directed_war_live.png`。实际画面含“拓疆令遭拒”通知与验收专用决议；文件名不证明自然战争已发生，本片剔除，未为其做额外媒体哈希。

## 文档有记录、当前定位不可用的战争录像

[Robert MCP 连战采集合同](../../../docs/project-causality-robert-mcp-streak-capture.md)第 69–79 行记录 R30 母带与连续节选。当前主工作区 `D:/workspace/ck3_eternal_recurrence/artifacts/project-causality/2026-09-20-robert-mcp-streak-r30/` 不存在；`Z:/ck3_mod_rewrite` 亦不可访问。因此下列信息仅为历史文档登记，没有本轮媒体哈希或 ffprobe 复验：

| 记录文件 | 历史时长／SHA-256 | 边界 |
|---|---|---|
| `robert-1066-mcp-streak-continuous.mkv` | 27:18.666；`FECD2972DA7305EAF138BEFF6184ED94F804227278E035066973E68F58636D46` | 即使找回，也是我方 MCP 自动玩家控制 Robert 的录像；仅可按真实身份、操作与结果作现象素材。 |
| `robert-mcp-showcase-continuous-6m25s.mp4` | 06:24.967；`08C5A46300641CC0141AD1FDDD6BC22F93C61A8C92147E5036A8BDB65F469245` | 历史母带 95–480 秒连续节选，不是独立战役，也不能证明原生 AI 宣战候选评分或目标选择原因。 |

此为有界查找，未断言所有磁盘上不存在战争录像。范围仅含主工作区 artifacts、明确的项目 process_assets、旧宣传片 capture 路径及文档指向的 Z 路径；未搜索私人媒体目录。

## 本机新拍可行性

- 当前 Steam 注册路径为 `D:/Program Files (x86)/Steam`；其 `steamapps/libraryfolders.vdf` 指向该路径与 `C:/SteamLibrary`。
- 实际游戏可通过 `C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe` 访问；95,206,008 bytes，实测 SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，与研究绑定的 CK3 1.19.0.6 一致。长目录名由 Steam manifest 记录为 `Crusader Kings III`。
- `C:/SteamLibrary/steamapps/appmanifest_1158310.acf` 记录 appid 1158310、buildid 23530548、StateFlags 4。这证明本机 Steam 安装登记，不替代运行时授权验证。
- 只读取 `config/loginusers.vdf` 的离线字段：`WantsOfflineMode=1`、`SkipOfflineModeWarning=0`。这是持久偏好；未观察当前 Steam UI，不能据此宣称当前离线状态已经现场核实，也未尝试联网。一次 `tasklist` 过滤仅看到 `steam.exe` PID 27392，没有 `ck3.exe`；启动前须重新检查。
- `ffprobe` 实际为 9.0.1，路径见 JSON。未修改或核验本次捕获解释器／venv 依赖，未创建 session 或取得游戏排他锁。
- 主工作区 `ck3_autonomous_player/native_bridge/build-aub-cost-probe-20260920/` 有 DLL 与 injector；`build-fresh-20260915T110015Z-612b586b/` 搜到 DLL。这只是存在性发现，未资格化这些旧二进制供本片使用。

## 已存在的真实入口与使用边界

1. 普通受管游戏会话使用 `ck3_autonomous_player/agent.py` 的 `native-session`，同 state／pipe 的 `ck3_autonomous_player/mcp_server.py --driver native-headless --transport stdio` 负责 MCP。参数示例见 [自动玩家 README](../../../ck3_autonomous_player/README.md)第 251–254 行；[MCP 安装文档](../../../docs/ck3-portable-codex-mcp-setup.md)第 153–175 行给出 fresh build、无启动 doctor 与 matching session 生成路径。`native-session` 本身不是录像器，也不能从准备好的 profile 推断 `enabled_mods=[]`；新拍原版必须另行绑定并回读实际 profile、角色和规则。
2. 完整自动玩家战争录像的现有入口是 [run_project_causality_robert_mcp_streak.py](../../../tools/run_project_causality_robert_mcp_streak.py)。103–126 行的真实参数为 `--state-dir <全新目录> --artifact-dir <全新目录> --game-dir <CK3目录> --bridge-dll <DLL> --bridge-injector <injector> [--ffmpeg ffmpeg] [--fps 30] [--max-hours <正数>] [--max-turns <正整数>]`。默认 game-dir 仍指向当前不可访问的 Z 路径，必须显式覆盖。该脚本会创建状态、启动游戏、录屏及主动控制玩家；本轮没有执行。`--skip-recording` 仅诊断且不能 GREEN；此 CLI 不是原生 AI 观察专用入口。
3. 上述脚本 564–617 行的实际 recorder 使用 FFmpeg `gdigrab` 桌面输入、30 fps、H.264 与无音频输出；1175–1180 行检查既有 CK3 并取得 `exclusive_launch_lock` 和 `exclusive_state_lock`。锁实现见 [locking.py](../../../ck3_autonomous_player/src/xar_autoplayer/locking.py)第 22–44、66–103 行。直接调用 FFmpeg 不会自动获得游戏排他、角色语义或 clean span 证明。
4. 若需目标交互桌面 handoff，[operator-mcp.md](../../../docs/operator-mcp.md)第 18–45 行的真实工具为 `operator_get_capabilities`、`operator_get_status`、`operator_preflight_job`、`operator_handoff_job`、`operator_control_job`；只运行 profile 冻结的命令，CK3 job 必须声明 `ck3.exe` 排他。不能把现有只读 no-launch G2 profile 当可启动战争拍摄的 job。

新拍前按根 AGENTS 执行任务总线 poll、游戏排他、Steam 状态核实与已验证解释器检查；保全新 run 的原始录像、命令、报告、时间锚点及失败产物。[production-workflow](../production-workflow.md)第 78–95 行仍区分普通 raw media 与拥有真实 report/index/timeline/marks/clean spans 的 adapter bundle。不存在的证据字段继续留空。

## 下一轮有限取材目标

| 计划素材 | 建议镜头组 | 最小交付与允许讲法 |
|---|---|---|
| 原版普通战争地图／军队在地形中的画面 | S30-01、S30-11、S30-17 | 新 session 的真实角色、mod 列表、战争状态与 raw 时间锚点；只讲可见位置、数量或行动表象，不能为围城／掉头配上未经记录的 AI 动机。 |
| 同一战斗结束与对应战争界面 | S30-30、S30-31 | 同战斗、同战争身份与先后时间绑定；若只拍到一个窗口，只说明它可见的那项结果，不推算总战分。 |
| 提议／接收和平的界面与角色条件 | S30-34、S30-36、S30-37 | 明确玩家或 AI 身份与谁主动；玩家打开界面只能演示界面，不能代替 R03 自然白和。 |
| 可选自然个案 R01／R03 | S30-16、S30-39 | 仍按镜头表所需同帧候选／选中目标或实际和平事实绑定；没有足够证据即回到已规划教学图解，不为等候结果延长录像或编造回执。 |

这些均是下一轮计划，尚未拍摄或进入本片媒体绑定。

## 2026-09-23 后续无启动预检：RED，零新录像

已新增本片 [capture_session.py](../integration/capture_session.py)，默认只做无启动预检；显式 `--capture` 才进入受管会话分支。**本轮仅无启动路径真实运行，live 分支尚未验证，不能称拍摄已就绪。** 不移用 Robert 连战的战争失败终止合同，不运行 OODA、宣战、军队命令或自然白和研究。现有前端消费者只编译支持 Robert 或 Murchad 的一个固定入口，不能把形参描述成可任意启动 William／Harold。

依赖检查先查本工作区 `tools/.venv`，发现缺 `mcp` 与 `pywin32`；随后显式验证并借用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`：Python 3.14.7、mcp 2.0.0、pywin32 312、Pillow 12.3.0。本轮没有修改两个 venv。

正式 `codex_mcp_setup.py doctor --require-native-assets` 已运行：Python／MCP server import、无游戏的实际 MCP 知识查询、精确 EXE、DLL 与 injector 存在性均通过；总结果 RED，失败项为现有 Codex 注册与 layout marker 不匹配本次借用解释器配置。未改用户全局注册。该 doctor 的 native-assets 检查只核 EXE 哈希和 DLL／injector 是否存在，不能证明前端能力；本片 wrapper 使用既有官方 `Client(create_server(driver))` 接法，其余静态检查继续执行。

`D:/workspace/ck3_native_war_ai_promo_work/capture-preflight-a01/` 保存初次 RED。去除未使用的地图居中能力要求，并增加逐项缺口输出后，`capture-preflight-a02/command.json`、`static-capability-strings.json`、`entry-failure.json` 保存最终有界 RED：

- 当前 DLL 未含完整 `game.command.probe-frontend-bookmark-model-v1`、`game.command.activate-frontend-select-supported-1066-character-v1`、`game.command.query-frontend-selected-1066-feudal-candidate-v1` 三个要求的字符串。前两者只找到了私有 step 字符串，最后一个 typed query 的 step 也未找到；这是静态预检缺口，未把字符串检查冒充 live capability 回读。
- DLL 为 `D:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/native_bridge/build-aub-cost-probe-20260920/xar_ck3_bridge.dll`，3,212,800 bytes，实测 SHA-256 `2EB6E3265459CA3B2773D1A80E377A10F159592DAAEC77AC97C6E0CDB02807DC`。同目录 injector 为 39,936 bytes，实测 SHA-256 `579168D4CD7AFD48C635CE50D6DC3DE9A736F6AADEC3E3F97765D9E34E4C9E70`。
- DLL 只找到 `bookmark_rags_to_riches_petty_king_murchad`，没有 Robert key；另一份 9 月 15 日 DLL 也未找到这次需要的完整前端启动链。未重新编译 native、未修改 ABI／研究结论。
- 两次预检均在 CK3 启动与 live ID 分配之前失败：本包 **零启动、零新 raw、零已绑定 clean spans**；Steam 实时 UI 离线状态仍未核实。此前持久离线偏好与一次 process-zero 检查不代替以后启动时的检查或 mutex。

可复用无启动命令（换全新的 `--output-dir`，保留旧 RED）：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\integration\capture_session.py --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-dll D:\workspace\ck3_eternal_recurrence\ck3_autonomous_player\native_bridge\build-aub-cost-probe-20260920\xar_ck3_bridge.dll --bridge-injector D:\workspace\ck3_eternal_recurrence\ck3_autonomous_player\native_bridge\build-aub-cost-probe-20260920\xar_ck3_bridge_injector.exe --state-dir D:\workspace\ck3_native_war_ai_promo_work\capture-state-a01 --output-dir D:\workspace\ck3_native_war_ai_promo_work\capture-preflight-a03 --pipe-name \\.\pipe\xar_native_war_capture_a01
```

此命令的 a03 尚未执行；对同一旧 DLL 预计仍 RED，不应为消除结果反复运行。未来换合格资产后才继续 preflight／Steam 当前状态／process-zero／受管 mutex／实机取景。wrapper 中 `RAW_CAPTURE_COMPLETE_PENDING_VISUAL_REVIEW` 只描述有非空 raw、ffprobe 成功及受管清理的过程结果，仍不是 clean span 接纳或 1× 审片。

编号器新增 canonical `vanilla`，专用于实际 `enabled_mods=[]` 的原版会话，视频片名另记项目字段；本包未消耗生产编号。`py tools/test_ck3_live_run_id.py` 已一次运行，7 tests PASS，包含独立命名空间与共享 execution ID 的既有测试；没有新增镜像测试。本片实际取景的后续工作保留为缺口，GPU 排期已归还根任务。
