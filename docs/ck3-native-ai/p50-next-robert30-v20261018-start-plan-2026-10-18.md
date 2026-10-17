# 下一期罗贝尔三十年：已有入口与最小准备

下一期标题为“罗贝尔的30年_v20261018”，在本期首次三十年实际到达、MCP手动永久存档完成、完整视频及要求的复验完成后，再从1066开始独立战役。当前自动推进不等待此包。本包只读既有小文件并形成计划，没有创建新profile、复制SAVE或启动任何Game／SDK／录制／桌面操作。

`machine_id: xenoamess-full-tower-eb9d2c1186`；静态核对时间2026-10-17 19:10–19:16 UTC（10月18日03:10–03:16 CST）。[机器可读清单](evidence/p50-next-robert30-v20261018-start-plan.json)保存精确来源SHA、CLI模板、未取得的实际输入和退出fallback合同。历史证据仅证明本机当时状态；未来开局仍实际读回。

## 复用成功路径

本期从主菜单起录的实际会话是 `90e81184-8475-4053-9b83-d01c0f314e0e`。已封 `ROOT-FRONTEND-RECORDING-ADMITTED.json` 记录录制早于frontend动作、实际MainMenu游戏帧和scene帧审阅，且frontend动作在准入前为0；它没有声称地图已就绪。无需为下一期开局另造框架。

复用入口都在本机 `N=D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep`：

| 已有入口 | 复用范围 | 必须重绑定 |
| --- | --- | --- |
| `p37-clean-host-prep01/{prepare_clean_host,prepare_clean_profile,root_clean_profile,bind_clean_launch}.py` | 零mod、无旧SAVE／Driver、MainMenu启动、原owner保留 | 新campaign／profile／pipe、当前容量、新鲜Steam离线图、实际EXE／已资格DLL与完整consumer来源 |
| `p37-clean-campaign-prep01/{prepare_clean_harness,clean_controls,admit_initial_map}.py` | 已跑通frontend→1066 Robert→SEM／CAP／SAVE→零基线→完整普通规划器 | 新runtime、实际SDK freeze、零计数、最新合格修复及队列消费者 |
| `new-campaign-frontend-recording02/` | 新录制UUID／OBS profile、MainMenu准入、metadata EDL | 当前正式promo依赖、实际新Game、通用HUD标题与正文 |

这些旧builder硬编码 `robert30-clean-campaign01`、p37与Native22；原目录均保留为历史输入，不能原样重跑。最短方案是在新外置准备包中作可审核的有限COW重绑定，继续用既有入口和参数；隔离新runtime后可保留内部p37命名，减少无价值的全树改名，但实际Native／SDK身份必须重新绑定。暂拟新战役根为 `N/robert30-v20261018-campaign01`，本轮检查该目录不存在，也未物化。

本机已关闭Native25 CAP2回执有107项bridge capabilities，广告了frontend route、tree、new-game、bookmark-model、supported1066选择和start六项能力。它支持复用上述前端组合；旧Native22成功不自动变成Native25的新开局验收。Native25实际DLL／export／SOURCE-FREEZE和frontend、war、succession、M6等必要consumer仍须在未来新freeze闭合，不能把未资格DLL换入当前或新一期。

## 最短运行顺序

以下是**准备完成后的CLI模板**，尚无可立即执行的新入口。`PY`为届时实际核验的Python；`RNEW`为新runtime，`CLEAN`／`PRESENT`为重绑定后的既有清洁开局／录制入口。

1. 在当前Game、SDK、录制实际正常闭场后，沿统一容量策略复核并创建独立campaign／profile。取得届时新鲜Steam“离线模式”画面，启动新Game至MainMenu；核实际空mod profile和非空startup log。
2. 从Root合入后的公共commit冻结新SDK，包含已资格war、M6、来源知识和性能变更；差异和必要consumer闭包要与实际采用的Native25相容。已有完整普通规划器、战争处理和陌生事件MCP续行规则继续启用，不恢复任何nonwar-only路由。
3. 启动新录制、通用右侧灰色HUD和新EDL。HUD只出现“智能体实时决策”及状态／决策／理由，片名仅用于影片元数据。审阅实际MainMenu game／scene帧后，运行 `PY -B -X utf8 PRESENT/admit_frontend_recording.py --session RNEW --sdk-prefix p37 --review ACTUAL_NEW_MENU_REVIEW.json`，再启动 `RNEW/launch_clean_sdk.py --launch`。
4. 对同一 `CLEAN/clean_controls.py --root RNEW` 依次执行 `publish --kind frontend-query`、`publish --kind new-game`、`publish --kind robert-start`，逐个等待实际成功。Robert动作内部固定为 `ck3_activate_frontend_start_1066_bookmark_character_v1(character_name_key="bookmark_rags_to_riches_duke_robert")`。不硬编码runtime CharacterID31254或29829，Start结果未知时不重放。
5. 依次发布 `--kind semantic`、`--kind capabilities`；用新SEM和实际map／scene审阅运行既有 `admit_initial_map.py`。然后 `publish --kind save --semantic ACTUAL_NEW_SEM_SEQUENCE`，确认初始存档物化；初始化 `initialize-ledger`，要求新episode、cycles0、counts0、window1、day0。
6. `publish --kind full --max-turns 1`，核实际普通结果后发布下一批FULL，执行 `runner --first-control ACTUAL_NEW_FULL_SEQUENCE` 返回的精确feeder argv。采用当前共享批次验证及先发布后附着顺序，不重放旧control／SAVE／CAP编号。

新日数、战果、episode、Driver、pending动作和业务ledger全部独立。允许带入的是已分析的来源知识：白名单仅为 `state/evidence/event-source-registry` 条目及对应facts，保留源SHA与有效facts路径，不复制整棵旧state。旧clean manifest中“knowledge未继承”的笼统字段须拆成“旧玩法状态／信用未继承、已分析来源知识按白名单携带”，避免文档与实际不符。

来源知识的现成离线复验入口是 `tools/g2_saved_campaign/qualify_populist_source.py --package-root NEW_FROZEN_SRC --state-dir NEW_STATE --verify-cold-id-rebind --output NEW_RECEIPT.json`。这只验证既有冻结P43输入在选定新loader／policy的复用；不能给未来派系战争或新局土地保留授结果信用。当前SDK不等此命令。

## 本期结束时的正常退出

对当前Native25，已有MCP正常退出路线**不可直接复用**。已关闭P49 CAP2的实际107项清单不含 `normal-exit-map-v1`；公共 `normal_exit_map_driver_v1._prepare` 必须先看到该Native广告和受管来源inventory。SDK存在 `ck3_query_normal_exit_context_v1`／`ck3_request_normal_exit_v1`／`ck3_observe_normal_exit_v1` 同名工具，不补足Native实现。Frontend只接受main_menu／bookmarks／lobby等固定路由，普通ingame navigation也没有Resign操作，不能拿lobby返回充当退出。

本机原版 `window_resign_confirmation.gui` SHA `9b8ca6d2cc17ecb575c21f5a683719d4ce6472958e3bf311e2419db09c34d1c9`：117–123行的 `descktop_button`（原版拼写）文本为 `EXIT_TO_DESKTOP`，回调为 `ResignConfirmationWindow.OnDesktop`，没有shortcut；125–130行Cancel才绑定 `close_window`，实际shortcuts为Esc。UIA是否暴露可执行button尚无实证，不冒充已有Invoke能力。

这是来源已核的固定系统菜单，按既有MCP缺口与桌面坐标合同，届时可使用**一次受管、经原始截图映射的“退出桌面”点击**作为fallback。未覆盖游戏事件仍采集后经原生MCP选择，不扩展鼠标例外。最小执行合同为：

- 先完成目标MCP手动永久存档与物化核对，drain／停止当前普通consumer；保留同一Game PID／FILETIME／HWND及screen owner，记录缺少Native退出cap的实际依据。
- 保存并审阅届时的新原始桌面PNG，确认固定Resign菜单和“退出桌面”按钮；读取PNG真实宽高、当前 `pyautogui.size()`、实际预览内容矩形，X／Y独立映射，不复用旧点位或比例。
- 保持精确Game HWND前台，写一次性claim，再使用 `tools/desktop_coordinate_map.py` 的 `--source-image`、四项显式preview bounds、审阅点位、`--expected-foreground-hwnd`、`--click` 和新的 `--receipt AFTER.png`。可加120秒文件年龄限制，但mtime不证明像素新鲜。
- 鼠标动作无需键盘；若前序涉及键盘，仍须英语布局0409和目标／控件焦点确认。点击ACK与截图只证明UI输入；实际保留进程句柄的wait／exit code、supervisor cleanup、存档物化分别读回。结果未知时只观察，不盲点第二次、不force kill、不释放仍在用screen。

此处只准备合同，未点击、未发送键盘、未退出Game，也没有提前授“正常退出／自动存档通过”。后续若采用已资格的新Native正常退出能力，则优先走其现成MCP路线。

本包只新增小型文档／JSON，预算1MiB、无重型写入／删除；外置派生包48小时复核时点和空间读回见机器可读清单。`open_kaishek: not-applicable`，因为本次是静态入口／桌面合同整理，没有新增脚本语义或原生采样。

## 03:21后补充：已物化的可finalize／install源包

Root随后明确要求继续完成可执行准备。`N/p51-fresh1066-v20261018-prepare01` 已实际创建73个COW Python叶，共1136848 B；另有11个录制／通用HUD代码叶，共143535 B。只物化代码，不创建目标campaign／profile／Driver／SAVE／ledger，也没有启动进程或桌面操作。小代码／metadata预算为16MiB，实际占用及48小时限期保护见清单的 `source_only_COW_preparation`；这份补注覆盖上文“仅模板”的旧准备状态，不追认新运行已经开始。

`prepare.py prepare` 已执行。原P37的3条完整清洁开局合同已在COW临时目录通过：MainMenu允许尚无actor、按顺序选择Robert、SEM／CAP／SAVE后零计数、window1与不重复Start；它们使用既有P37 SDK做纯夹具复验，没有调用MCP，也不授未来新公共SDK／Native25资格。

源包已有下列具体后继入口，等待Root完成新公共源码commit和实际来源绑定后执行，不需要重新设计harness：

- `freeze_business_source.py`：将新commit的业务SDK源码独立冻结。业务来源commit与保留runtime host的commit分列，复用原干净host时不改其冻结树、不把旧host commit冒充新业务来源。先查实际容量，写入仅限Git跟踪SDK源码，拒绝已有输出。
- `prepare.py finalize`：接实际SDK freeze、干净host、既有Native25原pin、新consumer来源／测试审阅及新鲜容量；校验实际DLL、EXE、来源叶，生成新namespace的完整代码／metadata闭包。旧Native22文件名只作70叶harness的兼容文件名，实际label／SHA／exports绑定Native25，单独注明；不把命名当版本。
- `qualify_prepared.py --finalized`：对采用新SDK后的最终COW再运行现有3条清洁开局合同。当前仅初步COW资格已跑，最终命令尚未跑。
- `prepare.py install`：create-only安装到 `N/robert30-v20261018-campaign01/runtime`，调用已有纯文件profile builder；独立导入校验通过的source registry／facts。没有旧Driver、SAVE、history、pending动作或战果迁移；历史事件定义ID属于来源知识，不产生新action提交。
- 新runtime的 `bind_clean_launch.py`：消费届时真实的前场正常闭场与新鲜离线／screen准入，保留旧场事实，不再要求早已过去的P36固定PID。只有新鲜像素路线可准入，旧Steam用户口头确认路线不再采用。
- `presentation/start_clean_presentation.py`／`prepare_obs_profile.py`：沿成功MainMenu owner的既有控制流程，采用P50通用HUD四叶、当前正式0.3.0依赖及新session／UUID。读取新Game launch和SDK pair，不带当前Game51028常量；片名不进入HUD。

`finalize`、最终SDK合同复验、`install`及实际frontend录制／新Game均未执行。完整参数顺序、脚本SHA和后续所需实际输入在 `source_only_COW_preparation` 与外置 `DELIVERY.json`。本期FULL、首次三十年永久存档和成片继续优先，不等待这些后继准备。
