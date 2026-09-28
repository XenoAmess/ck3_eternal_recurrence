# 独立 vanilla 会话与 checkpoint 重载

`capture_session.py` 默认只管理有界 CK3 会话、MCP 请求服务、原生读回和必要截图，**不启动桌面录像器**。
主取材录像由独立的一个 recorder 负责，避免后台调试录制与正式录制同时争抢资源。
若确需记录启动故障，显式加入 `--record-debug-desktop`；其 `raw-desktop.mkv` 包含启动画面，不能当作已审核的 gameplay clean span。
无 recorder 的成功结果为 `ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO`，`recording_complete=false`、`raw_video=null`；
有调试录像时仍须保留 probe 与实际时序检查，不因元数据 30 fps 而声称逐帧连续。

## 已有保存档入口

- 正式 agent CLI 的 `native-session --cold-start-checkpoint` 要求完整 v2 driver-state、原 pipe、checkpoint/history/lifecycle 锚定。
  它不能被“只有一个 .ck3 文件”代替。`rebind-ordinary-seed-v1` 适用于既有标准单 mod `xar_off` 环境，也不能直接冒充本片的 `enabled_mods=[]` profile。
- 当前项目复用既有 library 参数 `native_session(..., frontend_first_load_save_name=...)`，
  由 managed session 完成前端预热和 `-loadsave=<basename>`。这不是新实现的原生加载函数，也不是通用 agent CLI 已有的选项。
- 前端预热与实际读档是**两个排他串行进程**：先启动不注入 bridge 的前端、读到既有 readiness 标记、确认它退出，
  再启动带最终 bridge 的存档加载进程。两次启动共用一个有界 session budget，失败和退出证据由原 manager 保留。

## 从 R0004 的 day-zero 副本建立新 run

新增 `--checkpoint-save` 与 `--checkpoint-receipt` 必须成对提供。
前者可以是已保存存档的精确复制品，不要求它仍位于旧 profile；后者使用实际 MCP `save-checkpoint` 回执，
包含 saved 状态、size/SHA、actor/date、ordinary/xar_off/pure-vanilla 生命周期和回执的 exact-build native hello。
本次 R0004 的 `checkpoint-response.json` 本来就有这些字段，不需要新造 receipt 或修改旧 history。

以下是命令形状；`NEW_*` 需要替换成全新的路径与 pipe。`--capture` 才会启动 CK3；省略它只运行静态 preflight。
真实启动仍按项目既有要求使用当前 Steam 离线 UI 收据。

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/capture_session.py --game-dir <exact-game-directory> --bridge-dll <current-dll> --bridge-injector <current-injector> --state-dir <NEW_STATE_DIR> --output-dir <NEW_OUTPUT_DIR> --pipe-name <NEW_PIPE> --checkpoint-save D:/workspace/ck3_war_film_research_20260923/robert-input-case-r1/day-zero.ck3 --checkpoint-receipt D:/workspace/ck3_war_film_research_20260923/robert-input-case-r1/checkpoint-response.json --interactive-seconds 3600 --steam-offline-receipt <fresh-offline-receipt> --capture
```

存档精确复制进新 profile 的 `save games/war_film_checkpoint.ck3`；保存来源、复制后 bytes/SHA 与原回执副本。
新 profile 保持 `enabled_mods=[]` 和固定 CK3 EXE SHA，不拷贝旧 driver history、不修改旧 run。
observer 等待既有加载器发布完整 actor/date，核对保存身份和 native build，并要求同一暂停身份稳定且后续 application-main pump 已推进。
`map_ready=true` 而 `played_character=null` 是加载中的不完整发布，继续有界等待；有效不同角色或日期仍拒绝。
稳定 snapshot 后才保存 `map-start.png`，其 HUD 状态仍须实际看图，不能把 native map_ready 本身当作 HUD 视觉证明；
checkpoint 分支不调用 New Game 或 StartGame，也不把发出加载参数当成已成功恢复。
不带 checkpoint 参数时，原有 1066 bookmark 分支继续保留。

`--interactive-seconds 3600` 是显式一小时服务预算，上限没有放宽；不指定时仍为 1800 秒。
`--recovery-seconds`、同一 owner 的请求目录、失败后热诊断、显式 finish 与所有旧 attempt 保全保持原逻辑。
本改动的离线检查不等于 R0004 存档已在新 run 中成功加载，实际结果由下一次 live readback 决定。

## GUI 缩放与录制前核验

需要缩小 UI 以拍全战斗面板时，新隔离 run 显式使用 `--gui-scale 1.0`。runner 先写入并读回该 profile 的
`pdx_settings.txt`，在 frontend warmup 退出且最终读档进程启动前再次只读核对，并在地图完整暂停后、
hold 结束后分别保存 `gui-settings-*.json`。默认门仍只认可唯一且精确的 `value="1.0"`；
磁盘读数缺失、重复、无法解析或其他字面值均为 RED，不能追认旧 attempt。未指定此选项时保持原设置写入和运行路径。

CK3 原生设置界面保存 100% 时可能把 `value="1.0"` 写成 `value="1"`。v2 磁盘回执同时保留
`observed_scale_serialized` 原字面、`observed_scale_token` 完整赋值 token 与 `observed_scale_ratio` 精确十进制规范化比率。
`"1"`、`"1.0"`、`"1.00"` 均为诊断比率 `1`，但默认只放行 `"1.0"`；仅未来经 UI 源文件、原图、热回读及
importer 收据绑定的新 run 可在函数级显式 `allow_native_ui_one=True` 后额外放行精确 `"1"`。`"1.00"` 即使数值相等仍不放行。
指数、符号、前导零、非数值、重复 GUI/scale/value 字段或未知结构继续拒绝。该参数本身不核对 importer 来源，
调用方必须在启用前完成来源门；a04 既有 RED、未录制结论保持原样。

2026-09-28 的 E2-04 a01 在预启动设置 1.0 后仍由 CK3 最终进程写回 1.3；a02 未指定该参数，最终读数也为 1.3。因此预启动回执、
warmup 后回执或磁盘上的 1.0 都不能单独证明正在运行的 UI 是 1.0。postmap RED 后，operator 可在原生设置
界面选择 1.0、保存，再向同一热服务提交 `{"action":"gui_scale_disk_readback"}` 请求；响应只说明当前隔离
profile 的磁盘读数，字段 `recording_authorized_by_this_gate=false`。开始正式录制还须审阅原始桌面截图，确认
当前游戏设置的缩放与完整无遮挡战斗面板；该请求不执行 UI 输入，也不签发画面审核或成片签核。

## R0005 的实际时序故障及保存档检查

2026-09-23 的 R0005 首次 `native:2` 已 `map_ready=true`、日期正确，但 `played_character=null`，
当时失败截图仍是加载 100%。旧代码过早判身份不符而进入 recovery；后续同一 owner 的独立 `native:3`
读回才完整发布 actor `29829`、date `53144328`，随后另行确认真实 HUD。原 RED 和 recovery 证据保持原样，
这次代码修正只影响新 run，不重启或重标 R0005。

R0005 还实测 `ck3_inspect_save_artifacts_v1` 因 server 未绑定 profile 而不可用。
当前新会话已使用既有 `create_server(driver, profile_dir=spec.profile_dir)` 参数启用原有只读 inspector，
没有修改 MCP 通用服务；已运行的旧 owner 不会因源码变更自动获得这个配置。
此可选工具不可用不推翻真实 `save-checkpoint` saved 回执或独立文件 bytes/SHA 复核，也不要求为了检查器重启游戏。
