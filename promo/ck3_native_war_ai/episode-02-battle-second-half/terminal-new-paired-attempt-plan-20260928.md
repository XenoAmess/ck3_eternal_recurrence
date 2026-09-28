# E2-09：历史 DLL 不可得后的新配对取材

2026-09-28。此计划只为**新的**第 27 日来源回放安排终局 writer 与画面同步采集。R0271 当前占用 CK3 屏幕；本轮没有启动游戏、录制视频或重写既有 E2-09 卡。[静态输入](terminal-new-pair-inputs.json)、[无启动核验器](verify_terminal_new_pair.py)和[证据索引](terminal-new-pair-evidence-20260928.json)随文冻结。

## 旧 024 保持 RED；新候选另立身份

`episode01-denominator-live-attempt-024` 的旧 `preflight.json` 绑定 DLL **3,063,808 bytes / SHA-256 `5FA16EABCD2FD77730E96F11A3C030401EA14B58926E6504007008533B6929DE`**。本机旧路径如今同名同大小文件 SHA 为 `FCAFBA2A73E1EEF1E2651ADD40F71CE66B9FE16E4E61BD014DBA65C9965AEBD8`；它不能冒充旧 DLL。来源机的 `WAR/E2-09-024-DLL-20260928/RESPONSE.json` 明确 `status=unavailable`、`scope=sender_machine_only`，称该机旧路径不存在、所列冻结/build 根没有符合文件。响应 1,609 bytes、SHA `7AAB57A2DB34BE7735990E6ECC537A63ADF9317BF5075A06E9AF0CA9B497DD1D`，已在 `D:/ck3-research-artifacts/war-intake-20260928/e2-09-024-response-001/RESPONSE.json` 原字节保全；同目录 `receipt.json` 绑定 REQUEST/RESPONSE 的 bytes/SHA，`exact_dll_received=false`。这是来源机范围内的不可得响应，不能外推成所有机器均无该文件；本机旧 024 材料门仍 RED，不重标 GREEN。

新候选固定同一 **attempt-004 第 27 日**冻结源档 `trace-d27-immutable.ck3`，52,871,423 bytes / SHA `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3`。真实 `trace-d27-save.json` 回执 SHA `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`，其 native `save-checkpoint` 状态、字节、人物 `29829`、日期 raw `53146872`、原版 `enabled_mods=[]` 生命周期与 CK3 `1.19.0.6` exact-build hello 都吻合。候选**新二进制身份**为旧 build-007 目录目前可读的 DLL `FCAFBA2A…AEBD8` 与同目录 injector `3773042110D9E207FD02E00BF5376A033E71B70433B6B650088550A522B581C5`；游戏 EXE 仍为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

外置 `D:/ck3-research-artifacts/episode02-terminal-new-pair-preflight-20260928/attempt-001/` 是新的 append-only **纯静态**尝试；`preflight.json` SHA `818FAFA40B11BF0D43C5C059D8BBC5DDFD72DF5F7E2999FE415C0092ECD4AA51`，结果 `STATIC_MATERIAL_GREEN_LIVE_UNPROVEN`。核验器重算 EXE/save/真实回执/DLL/injector/不可得响应及外置副本 SHA；DLL 和 injector 都是 x64 PE32+，DLL 含 snapshot、map、played-character、`query-battle-terminal-transition-v1`、`denominator_inputs` 与 `selected_cb_battle_scale_raw_q100000` 静态字符串。**静态字符串不能证明注入成功、writer/denominator hook 安装、运行时字段可用或新终局数值。**这次没有调用 `capture_session.py`；R0271 释放前不再运行其全局空进程门禁。

## 新 run 的逐层准入

1. 等 R0271 明确释放 `ck3-screen`，和其他第 2 期拍摄者排一次屏幕顺序。每次真实运行前取得当次新鲜、可直接审阅“离线模式”的 Steam 原始桌面画面，领取 `ck3-screen:acquired`；确认没有 CK3/录制占用。画面陈旧或账号会话冲突按项目合同停止。当前 `STATIC_MATERIAL_GREEN_LIVE_UNPROVEN` 绝不代替此门。
2. 新建 `episode02-terminal-paired-attempt-<unique>` 的 append-only 工作目录、state/profile、output、pipe、raw、manifest/config snapshot；先保存本次将用的 CK3 EXE、候选 DLL/injector、源档与真实保存回执精确 bytes/SHA。**重新**运行 `capture_session.py` 的无 `--capture` 原生预检；只有无进程冲突且材料与 MCP 静态检查通过，才另起新 attempt 用 `--capture`。受管会话按[取材工具说明](../integration/README.capture-session.md)传 `--checkpoint-save` 与 `--checkpoint-receipt` 成对参数，纯原版 profile `enabled_mods=[]`，不拷旧 driver history；`--interactive-seconds 1200` 给 600 秒录像和清理留预算。不要复用 024 旧 pipe/output 或把当前 DLL 写回旧 build 目录。
3. 冷载后暂停，先保存原生身份：source save SHA、actor `29829`、日期 raw `53146872`、CombatID `16777218`、WarID `4`、省份 `2633`、phase/day、双方 army/participant/revision；游戏端 exact-build hello、所装观察钩子状态与 `failure_flags` 需要实际读回。任一关键身份不符、新 DLL 未安装 writer/denominator 采集、查询返回 `unavailable` 或 journal 有 gap，则该 run 只能保留为 RED/条件样本，不能拍成旧 024 算式的“实机证明”。
4. 在稳定暂停源帧把相机停在墨西拿，战斗面板和 WarID `4` 战争面板分别取前值截图、原生 control/v3 回执；打开面板后实际看图核可见性。外部唯一 recorder 从画面就绪后开始，沿用[两轨 600 秒方案](join-terminal-600s-capture-plan-20260928.md#600-秒-recorder-合同)的 `gdigrab` 参数，以**本次 run 独有** `-t 600` raw MKV、`-n` 防覆盖、独立 stderr/argv/开始时间/PID；不加 `--record-debug-desktop`。记录原始帧尺寸，不假定当前桌面仍是历史 `1024×768`。
5. 每日只推进一次并前后暂停/读回：源第 27 日、28、29、30、31 日各保留 control/截图/UTC/monotonic mark；第 32 日正常终局时同时取 terminal transition、writer 原生回执、war row、战斗结果、败方旧 CombatID 脱离和战争面板前后。把 native 请求/响应、截图和 raw 视频各自的 SHA 绑定至 `marks.jsonl`。**按真实录像帧 PTS**与可见 UI 转换锚对齐 mark，保存帧号、PTS 与不确定区间；不能按 UTC/monotonic 秒数直接冒充视频 PTS。第 32 日若被事件窗遮挡，把污染区间剔除，不把旁边的数据回执当作 clean span。
6. 600 秒到时原 recorder 自然结束，保留 exit/stderr、raw bytes/SHA、ffprobe stream/format 与逐帧 PTS/gap 报告。拟入片区间的首尾必须有同身份可见截图/视频帧、对应 control SHA、精确 PTS 和无遮挡 UI；按正式 CK3 adapter 的 report/timeline/evidence-index/clean-frame 合同建**新 bundle**并只读验证。`capture_session.py` 自身的旧式 `capture-report.json` 即使会话成功仍可能因外部 recorder 而 `raw_video=null`，不能改名造 GREEN。中断、提前退出或 600 秒未见终局均保持本 run 原样，补录另开 attempt。

## 数值与成片分支

新 run 的 E2-09 计算应从**本次** writer 的败方 hard-loss 分子、八桶战争参战者分母、已加载 CB 倍率、整数比例、未封顶 row、单场封顶、胜方和战争进攻方相对符号逐项复算，并核 `normal_result` 与同 WarID 行索引。新 run 若没有该正常终局，不能用历史 024 的 `-50` 填空。即使新回放重得旧数字，也要把新 attempt ID、当前 DLL SHA、source save/receipt SHA、新原生响应 SHA 与 raw 媒体 SHA 放进**新来源卡**；旧 [E2-09 卡](cards/e2-09-calculation.svg)仍标历史 024。若数值不同，依本次 writer 重做新卡的 JSON/生成 SVG，修订[旁白稿](narration-script-draft.md) E2-09 的分子/分母/比例/倍率/封顶/方向，以及[导演案](director-plan.md)的终局段数字，再重新录 TTS 与镜头节奏。不得只改字幕或把旧 024 的精确数字配新 run 画面。

最终机器 bundle 和媒体审计只证明各自明示的字节条件。实际 1× 全片观看、按最终成片 bytes/SHA 人工签核以及用户指定的 OneDrive 单文件视频交付仍是后续独立门；本计划没有完成这些交付。
