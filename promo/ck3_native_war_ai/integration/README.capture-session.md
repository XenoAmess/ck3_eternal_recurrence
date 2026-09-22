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
observer 只等待既有加载器产生 paused/map-ready snapshot，再核对保存的 actor、date 和 native build；
checkpoint 分支不调用 New Game 或 StartGame，也不把发出加载参数当成已成功恢复。
不带 checkpoint 参数时，原有 1066 bookmark 分支继续保留。

`--interactive-seconds 3600` 是显式一小时服务预算，上限没有放宽；不指定时仍为 1800 秒。
`--recovery-seconds`、同一 owner 的请求目录、失败后热诊断、显式 finish 与所有旧 attempt 保全保持原逻辑。
本改动的离线检查不等于 R0004 存档已在新 run 中成功加载，实际结果由下一次 live readback 决定。
