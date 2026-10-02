# E2-06/07 与 E2-09：独立来源和 600 秒录制方案

2026-09-28，无屏幕取材准备。本文只冻结两条历史回放的输入和后续拍摄方案；没有启动 CK3、录制新视频、取得 clean span 或完成影片审阅。R0271 R0002 正在占用 CK3 屏幕，正式取材须排到其释放之后。[机器可读输入](join-terminal-capture-inputs.json)、[无启动材料核验器](verify_join_terminal_capture_inputs.py)和[本轮回执索引](join-terminal-preflight-evidence-20260928.json)均在本目录。外置 attempt 只追加，不覆盖。

## 两条来源不能接成同一次实况

| 镜头轨 | 历史独立回放 | 原始 `save-checkpoint` 与冻结源档 | 历史可复用二进制 |
| --- | --- | --- | --- |
| E2-06/07 增援/战宽 | 085，原版第 11→12 日，来源日期 raw `53146488`，玩家 `29829`，CombatID `16777218`，WarID `4`，候选 ArmyID `22` | attempt-004 `trace-d11-save.json` SHA `DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5` 的 `body.checkpoint.status=saved`、`size=52,408,560`、SHA `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`；`trace-d11-immutable.ck3` 同字节。 | DLL `1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F`；injector `34A1AB183F5173844A74E52A7F68195AAD859C380DFCA6B7E76F40611A51FB2D`。 |
| E2-09 战分 writer | 024，第 27→32 日，来源日期 raw `53146872`，同玩家/CombatID/WarID；它从另一日期检查点重新启动 | attempt-004 `trace-d27-save.json` SHA `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012` 的 `body.checkpoint.status=saved`、`size=52,871,423`、SHA `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3`；`trace-d27-immutable.ck3` 同字节。 | 历史 DLL 应为 `5FA16EABCD2FD77730E96F11A3C030401EA14B58926E6504007008533B6929DE`、3,063,808 bytes；injector `3773042110D9E207FD02E00BF5376A033E71B70433B6B650088550A522B581C5`。**DLL 原件待收，不能用同名当前文件。** |

两个真实保存回执都含原版 `1.19.0.6`、EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、`enabled_mods=[]` 的生命周期来源、玩家 `29829` 和对应日期。085/024 各自旧 `checkpoint-copy.json` 的 profile 副本、收据副本 SHA 与上表相同，且 `old_attempt_modified=false`。旧原始结果分别为 085 `jfull085-finish.json` SHA `A7F01C89BE66B34A6F2862BAEFC4354EF74507B6D5178E2949C381DEDC32FD88`，024 `d32-terminal.json` SHA `E55CEFA0AEB57D2F27A0EEF5D9516B85DB9FA5722551A4A83A5BB909DF5BE96F`。[研究证据索引](join-terminal-evidence-index.md)列出了可讲数字和不能外推的机制边界。

历史 085 `capture-report.json` SHA `FC28F0187369E49374553F1DCDFE5B22837B3AD447FB6DDB6A1D2FB9D10862E2`；024 为 `2759F2436729199F182D1C574C37D56F9786DA331D08D4C0501E324CF89AA22D`。两者原值都是 `raw_video=null`、`recording_complete=false`、`clean_spans=[]`、`adapter_bundle_validated=false`。原始回执可支持带 attempt 标识的[计算卡](cards/README.md)，不能当作连续游戏画面。085 的附带 battle-control 查询曾单独 RED；085 的 join/full-entry 局部捕获成功不覆盖这个失败。

## 本轮 append-only 无启动预检与 024 缺口

同一冻结配置依次检查本机 CK3 EXE、源档、**真实 MCP 保存回执**、DLL、injector、旧原始结果、capture-report、checkpoint-copy 的 bytes/SHA，并核保存状态、人物/日期、原版生命周期与 exact-build hello。两条外置 attempt 及 SHA 在[回执索引](join-terminal-preflight-evidence-20260928.json)。

| attempt | 材料结论 | 录制结论 |
| --- | --- | --- |
| `D:/ck3-research-artifacts/episode02-join-terminal-preflight-20260928/join-085-attempt-001/` | **GREEN**：冻结源档/回执/旧结果/历史 DLL/injector 全部精确匹配；DLL 静态含 snapshot/map/played-character 与私有 phase trace BEGIN/FINISH 字符串。 | 仅材料通过，未取得新鲜离线桌面、屏幕独占或运行时能力。 |
| `.../terminal-024-attempt-001/` | **RED**：旧 `preflight.json` SHA `228220733B3DF570CE5BB961FD362747708BF44826C11C2EAC0743255EFB98C8` 绑定 `5FA16EAB…B6929DE`，但旧路径当前同名、同大小 DLL 为 `FCAFBA2A73E1EEF1E2651ADD40F71CE66B9FE16E4E61BD014DBA65C9965AEBD8`。其余列明来源精确匹配。 | 不使用当前同名 DLL 冒充历史 024；本地已知归档未找到精确原件。 |
| `.../join-085-native-attempt-000/` | CLI 参数解析 RED：带空格游戏目录被调用 shell 拆开，未进入 `main()`；错误已补存。 | 未启动 CK3。 |
| `.../join-085-native-attempt-001/output/` | `capture_session.py` **无 `--capture`** 的正式预检 RED：`An existing CK3 process blocks capture`，`ck3_started_by_preflight=false`。 | 正符合 R0271 独占门禁；原回执保留，不在屏幕释放前重试。 |

024 只请求一份精确历史 DLL：`C:/Users/1/OneDrive/WAR/E2-09-024-DLL-20260928/REQUEST.json`，本机请求 SHA `7A434AB23D2087BD2FB650FFAB8515F24306BE7279B6690D7CFCBB992887FF5F`。发送方应在该独立子目录只放 `xar_ck3_bridge.dll`，3,063,808 bytes、SHA `5FA16EAB…B6929DE`；禁止覆盖旧本地路径，也无须重传已核源档/回执。当前仅证明本地请求文件存在，云端同步、他机看到与精确 DLL 接收均**未验证**。若原件已失，可另开新构建/新 run 取材，但旧 024 的数值和“同一回放”身份须重新证明，不能移植到新视频。

## R0271 释放后的两次独立录制

每条轨迹新建自己的不可变 attempt、state/profile、output、pipe、recorder、manifest 与 config snapshot。**先 085、后 024，绝不并行占同一桌面**；024 必须先收到精确 DLL 并复核 SHA，或明确切换成新研究 run。每次先领取 `ck3-screen:acquired`，取得当次新鲜、可见“离线模式”的 Steam 截图并人工审阅，核 CK3 进程与任务总线占用。桌面陈旧按项目恢复合同处理；未通过就停止。受管游戏只用 `capture_session.py --capture` 的新 output/state 和原版 `enabled_mods=[]` profile；085 需要其历史 `--enable-private-phase-trace`，024 不需要。只在相应来源存档与真实保存回执成对传入、同帧玩家/日期/CombatID/WarID 回读后进入拍摄。当前没有授权使用“只给一个 .ck3 文件”的冷启动捷径。

每条新 run 给 CK3 管理会话至少 `--interactive-seconds 1200`，使启动、定位 UI、600 秒录像和清理有不同预算。项目 `capture_session.py` 默认不录 gameplay；**只设一个外部 recorder**，不加 `--record-debug-desktop`。开始录制的条件是：源暂停帧身份稳定、墨西拿 `2633` 与战斗/战争面板实际可见、相机停稳，已经保存首帧原生 v3/control 请求响应及截图。历史原件 hash 只能作对照，新 run 的事件、入场或数值若不同，计算卡与旁白要跟新 run 回执重算。

### 600 秒 recorder 合同

两条轨迹各用一次独立、**新文件名**的 FFmpeg raw MKV；`recorder-start.json` 保存精确 argv、UTC 与 `time.monotonic_ns()`、PID、目标路径，stderr 独立保存。沿用已在本项目 100 秒实录验证过的参数，唯一时长改为 600 秒：

```text
ffmpeg -nostdin -n -hide_banner -loglevel warning -f gdigrab -framerate 30 -draw_mouse 0 -i desktop -t 600 -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -an <NEW_ATTEMPT>/raw/gameplay-<085-or-024>-600s.mkv
```

`-n` 防覆盖，600 秒到时自然退出；不能把“设了 30 fps”当成实际每帧连续。保存 exit code、stderr、文件 bytes/SHA、完整 `ffprobe -show_format -show_streams` 以及视频逐帧 `best_effort_timestamp_time` 的 sidecar。若进程提前退出、编码丢帧、游戏卡住或 600 秒未覆盖关键边界，当前 raw 和失败报告原样保留，补拍另开 attempt；不延长、覆盖、重命名为 GREEN。

| 轨迹 | 600 秒软预算与必须记录的 mark | 超时/分叉处理 |
| --- | --- | --- |
| 085 | `0–90s` 源第 11 日暂停/战斗面板/ArmyID 22 到场前；`90–240s` 同 CombatID phase day 7 join 入口、两侧旧 entry/cache；`240–390s` 一日有界推进与 join 返回，核 13 团起始 2570/current 2560、base/final `2467/2220`；`390–510s` phase day 8 首次 side0 出伤入参及战斗 UI；`510–600s` 持续显示同身份面板并保留余量。 | 时间是机位预算，不强迫事件按秒发生。若新 run 没有 ArmyID 22 同一入列或首次出伤，用其真实结果与时间标记记为分叉，085 旧卡不得贴在该画面上。 |
| 024 | `0–60s` 源第 27 日 CombatID/WarID、战争面板前值；`60–360s` 逐日暂停并各取一次第 28–31 日战斗/败方状态；`360–480s` 第 32 日 writer/`normal_result`/winner/败方脱离旧 CombatID；`480–570s` 同 WarID 战分面板前后及撤退状态；`570–600s` 终局稳定画面。 | 每日只推进一次、前后都回读。若 writer 分子/八桶分母或 CB 倍率与旧 024 不同，重新计算该 run 的 row；若 600 秒没见终局，不以旧 024 终局补洞。 |

所有 mark 按发生顺序**追加**到 `marks.jsonl`：`track/run_id`、recorder PID、`time.monotonic_ns()`、UTC、动作前后、源与当前 save SHA、`date_raw`、CombatID/WarID、phase/day、控制请求/响应 SHA、截图 SHA、UI 可见性、异常和对应说明。`time.monotonic_ns()` 不是视频 PTS；录完后从 raw 真正的帧 PTS 与可辨认的同步 UI 转换/战斗面板画面配准，每个 mark 写 `pts_alignment` 的帧号、PTS、可见锚、容差区间和审阅人。不能用“开始 UTC + 秒数”伪造帧对齐。若画面被事件窗遮挡，记录污染区间；不能把原生回执时间当作 clean span 边界。

正式拟入片 span 需要原 raw SHA、PTS 起止、起止视频帧/截图 SHA、战斗/战争 UI 可见、正确日期与 CombatID/WarID、对应原生回执 SHA 和逐帧 gap 检查。随后按已核 CK3 adapter 的 report/timeline/evidence-index 合同建立新 bundle 并做只读验证；旧 085/024 `capture-report.json` 不改名或改写成 GREEN。自动审计只是机器条件，成片还需实际 1× 全片观看后按精确成片 SHA 人工签核。鼠标坐标兜底遵守原始桌面截图、真实尺寸和 `desktop_coordinate_map.py --receipt`；键盘前确认目标窗口与英文 `LANGID=0x0409`，输入后读回。
