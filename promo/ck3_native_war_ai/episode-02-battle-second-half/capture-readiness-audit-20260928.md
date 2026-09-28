# 《战斗后半笔账》旧素材复核与新录制准入

2026-09-28；只读媒体抽样与本地 CLI 检查。此页是录制前的证据清单，不是已完成的 capture bundle、完整 1× 审片或新实机验收。本次没有占用 CK3 屏幕。

## 现有素材的精确边界

| 素材 | 已核事实 | 可用于本片的范围 |
| --- | --- | --- |
| `D:/workspace/ck3_native_war_ai_promo_work/episode01-full-edge-attempt-004/gameplay-messina-pursuit-to-terminal.mkv` | 本次 `ffprobe`：100.000 秒、99,287,871 bytes、H.264、1024×768、30 fps；本次文件 SHA-256 `359BE5CF17D7D838E9A4E1049B0E85CBE5BF9ACF9668B0E43EF467AB4F68D27F`。原 `recorder-terminal-start.json` 有录像启动 UTC；`terminal-replay-d28-d32.jsonl` 给第 28–32 日的原生日期和截图 SHA，但尚无逐 PTS 对齐的 marks 或 clean span gate。抽查 PTS 2、20、40、60、80、95 秒，画面从 1066-12-31 到约 1067-01-02；所抽帧没有第 31 日或第 32 日终局。 | 这是与 attempt-004 追击计算同一回放的前段候选，须逐 PTS 核日期、CombatID/WarID 与可见性后才能剪。不能称三日全程或终局 clean span。第 28–32 日静帧存在，但静帧不是连续录像。 |
| `episode01-full-edge-attempt-005` 三段 raw：`gameplay-hotspot-follow-full-battle.mkv`、`resume-d17-r2.mkv`、`resume-d20-r3.mkv` | 原拼接收据记录三段 SHA-256 分别为 `3E086D8D871B0743EB2E294D3ECC2A6BF1233D8F78DCF57B1F8B4DFDB1E30171`、`F7B86E4C67C3E4767493CF9507763D3CAD7C36AB6B94A98959703BF15688F8B5`、`F6901C1AC991E14296123B2DB32EC6C118738B2E604E872904416D84136C907C`。首段第 17 日因鼠标触边滚屏而 RED，仅原编辑计划 `[0,130]` 秒入选；后两段候选 `[0,28.4]`、`[0,108]` 秒。 | 独立接战存档回放的场景与可见性素材，不能与原始 31 日的第 6 日后数值，或 004、020、040、085、024 的数据作为同一随机轨迹配对。 |
| `attempt-005/gameplay-messina-full-battle-clean-v1.mp4` | 266.4 秒、77,025,802 bytes；本次重算 SHA-256 `1BF6FD2E3B35DF5E0B43F8EE7D595422E3BE959F156409A33829133B8F6D9A02`。原每秒抽样审计 267/267 帧可见战斗标记。 | 可标注为“同存档独立重放”的上下文画面。这里的“clean”是该次战斗标记可见性筛选拼接，不等于通用 CK3 adapter 已接受的 capture bundle，也不等于人工 1× 完整观看。 |

`attempt-005/ck3-output/capture-report.json` 的原值为 `raw_video=null`、`recording_complete=false`、`clean_spans=[]`、`adapter_bundle_validated=false`，因为 `capture_session.py` 默认只管理受管 CK3 会话，录像由外部 recorder 完成。现行 xar-promo v0.2.1 的 CK3 adapter 读取根 `report.json`、`cell/promo/capture-timeline.json`、`evidence-index.json`，要求 GREEN 报告与索引、原始视频字节/SHA、按序 marks 及绑定两端干净帧的 GREEN `clean_frame_gates`。不能把旧 `capture-report.json` 改名，或仅凭拼接收据与 267 帧标记审计宣称 bundle GREEN；缺失的证据应明确标为未取得。

## 新录制 run 的输入与动作顺序

1. 先查远端 `master` 的战争请求；R0271 围城参与者判定直接阻塞 Robert，优先让出 CK3 屏幕。录制开始前取任务总线 `ck3-screen:acquired`，检查排他占用和本次新鲜 Steam“离线模式”画面。画面陈旧时按项目桌面恢复合同处理；未取得离线证据不启动 CK3。
2. 为每个目标轨迹创建全新外置 attempt/workdir、独立 state/profile/pipe 和 run manifest；冻结当前 ProjectConfig 精确字节、游戏 EXE SHA、DLL/injector SHA、原版 `enabled_mods=[]`、来源 `.ck3` bytes/SHA 与其真实 checkpoint 回执。先用选定解释器无启动预检，再显式 `--capture`。`capture_session.py` 不负责正式桌面录像，须另设唯一 recorder；启动、停止、失败 stderr 和 ffprobe 都永久保留。
3. 暂停源帧先保存原生身份：run/attempt ID、source save SHA、actor、WarID、CombatID、ProvinceID、日期 raw、phase/day、双侧 army/regiment/knight 身份和 revision。每次推进一日只发一次命令，前后均保存原始 MCP 请求/响应与截图；另存录像时间基准、命令 UTC/monotonic 时间及 PTS mark。战斗 UI、人物 UI 和战争面板都要前后同身份回读。鼠标停在非地图边缘；相机请求后的可见性需在镜头开始及停留末尾复核。
4. 分轨拍摄：004 的第 27 日源档可用于追击到终局候选；039 的第 5 日事件前源档用于致残，040 只读复载 039 的第 6 日后存档；020 的第 26 日源档用于击杀，085 的第 11 日源档用于增援与战宽，024 的第 27 日源档用于战分 writer。每次新加载都须核查是否仍走同一随机轨迹；若新 run 的具体事件、逐团伤亡、入场或战分与旧研究不同，保留新实况并重新计算新回执，不能给新画面配旧数字。085 本身已有 full-entry 与三点战宽/首次出伤，083 是另一次独立复证；两次不能剪成一个连续实况。
5. 每条拟入片区间保存原 raw SHA、PTS 起止、对应原生日期/控制回执 SHA、开始与结束的确切截图和可见性检查，形成按序 marks、clean spans 与 evidence index。执行 adapter 只读加载及精确字节检查；RED/中断保持原样，重试另开 run。机器 audit 与 review 包仅为待人工审阅；最终成片需实际 1× 完整观看后才可由审阅人对精确成片 bytes/SHA 签核。

## 已核工具入口

GitHub 正式 Releases 页面于本轮显示 v0.2.1 为 Latest；主工作树 `tools/.venv/Scripts/python.exe -m xar_promo --version` 返回 `xar-promo 0.2.1`，`direct_url.json` 的发布 wheel SHA-256 为 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`，与 `tools/requirements-promo-toolchain.txt` 一致。顶层以及 `start-run`、`validate`、`preserve`、`audit`、`review` 的 `--help` 均可调用；`capture_session.py --help` 确认默认无启动、正式 `--capture` 显式启用。此项只是环境与接口 probe，不是新 run 的 config 冻结或实机准入。
