# J-A01 增援原片：无屏幕 adapter 准入准备

2026-09-29 CST。核对基准为 #451 `e4957f17e` 的
`four-raw-pts-candidates-20260929-a03.json`、正式 E2-06/07 卡索引与
`reel-edit-production-contract-20260929.md`。本轮只读小型 JSON、marks 与代码，未打开
1,325,156,480 B 原始 MKV 或 15,862,058 B 完整 ffprobe，未启动 CK3、FFmpeg 或审片。
结果仍是 **机器候选、adapter_eligible=false**。

本轮先查独立 `xar_promo_toolchain` 最新正式 GitHub Release，仍为 `v0.2.1`（非 draft、
非 prerelease），wheel SHA-256
`F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`；
当前 requirements pin 相符，显式主工作树解释器
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 报 `xar-promo 0.2.1`。
本隔离工作树 `D:/w/e2adapter` 无相对 `.venv`，没有运行新工具链 attempt。

## 能直接引用的封口身份

下列相对路径均以
`D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-live-20260928-a01/`
为根。这里列的 raw/ffprobe SHA 取自既有完整 PTS 审计和 recorder 回执，本轮**没有重验
它们的内容字节**；其他 SHA 取自既有绑定回执/正式卡索引。

| 原件 | 已知 bytes / SHA-256 / 含义 |
| --- | --- |
| `ck3-output/capture-report.json` | 8,643 B / `F59CBFFACCA88C59D158A6196CD2994BAFF0D6FD22A1E051FD167C2BC51D4F2F`；`ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO`，`adapter_bundle_validated=false`。 |
| `ck3-output/session-result.json` | 7,489 B / `3413FB08D3496F41988F225C9DAAFCE5443C3A4CDD41FA8BBBB1B8AB6941108C`；shutdown `ok/tree_gone/cleanup_proven=true`。 |
| `recording-e2-06-d11-a01/recorder-final.json` | 1,927 B / `F4EA84BCF8BF42149F80BAFB8820B3FC4BB87C0A23653353D7FE535109F3741F`；`ENCODED_UNREVIEWED`、1920×1080 H.264、600.000 s，FFmpeg/ffprobe exit 0。 |
| `recording-e2-06-d11-a01/raw/e2-06-d11.mkv` | 1,325,156,480 B / 历史 SHA `501B4C2A8557DC2EBBE88FD0485A45265FDDC9BF8EF46F7A1E968F8EB51024C7`。 |
| `recording-e2-06-d11-a01/ffprobe.json` | 15,862,058 B / 历史 SHA `FE062858E759D29CEA538FB3AD7F300812AB410DF0C02B8A0544A9D09B0310F0`。 |
| `recording-e2-06-d11-a01/pts-audit-a01.json` | 1,694 B / `6BF5086B8AF8E2CB2E7261989487F52A3E57D2B43A7204B474340B29B7ECBCDB`；16,691 帧，PTS 0–599.967，缺失、倒序、>0.2 s 间隙均 0，仍为 `PTS_CONTINUOUS_UNREVIEWED`。 |
| `recording-e2-06-d11-a01/marks.jsonl` | 1,940 B / `B028F603784512C6013095735DE3A9F1AEA7971F57E69AA86BFDAEBD8E99C02E`；首末 PID 5732，墙钟 mark +226.7199571/+374.0667917 s，仅供导航。 |

冷载 save 是 `episode01-full-edge-attempt-004/trace-d11-immutable.ck3`，52,408,560 B，
SHA `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`；
随存档的原生保存回执，即本任务的 source-save sidecar，是该旧 attempt 的
`ck3-output/interactive-requests-responses/trace-d11-save.json`，13,397 B，SHA
`DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5`。
当次 `ck3-output/checkpoint-copy.json` 证明这两份精确字节复制到隔离 profile：
`ck3-state/profile/save games/war_film_checkpoint.ck3` 与
`ck3-output/checkpoint-source-receipt.json`；`recorder-intent.json` 同时绑定原 save、回执、
当次 preflight 与 native-start-readback。preflight SHA
`7876B3C75253A2CFC48F1D584EB45124A71C8EFAD66AE5E974578BA1DCC3D0A0`；
readback SHA `B6C619930060FC521E0F84B9966BE771D8BF78FE177422344DB52A2F13FD5DF0`。
preflight 记录 exact CK3 1.19.0.6、DLL SHA
`1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F` 与 injector SHA
`34A1AB183F5173844A74E52A7F68195AAD859C380DFCA6B7E76F40611A51FB2D`。

当次原生步骤可填引用：前态 snapshot
`ck3-output/interactive-requests-responses/e2-06-d11-snapshot.json` SHA
`2709EB87D3C5420510BFBF3092B9E324D20BA3B5ACF8A6204F1A572501E1D1A6`；
private trace begin SHA `0475E133E989AE9A5C83A2FA805C26FF2541E37B522B0E0FC239CE9721629437`；
trace finish SHA `A688CC0C656364914BE5E42457C0DCCE94415A83163950BF68F1021D9A907CA5`；
后态 snapshot SHA `23A38AFB71F660695793CE04E3CF433E6BF0A93A7C590A6CD41D502EB083337A`；
`operator-steps/e2-06-d11-advance.json` SHA
`8A2DDB58464E3206304C80B03B38FC23BA832E762C52A256EBE05C1210A321B5`。
它们支持同一新回放 actor 29829、WarID 4、ArmyID 18 的第 11→12 日状态，
日期 raw `53146488→53146512`，以及 A01 私有 join/width 的局部读数。
正式 E2-06/07 卡的 `source_preflight` 就指向上述当次根，因而来源路径前提可填。

## 搜片窗与视觉边界

#451 a03 机器 PTS 清单在完整 ffprobe 中核过两处真实**搜索窗**：

| 搜索用途 | 原始帧 PTS / 帧索引 | 机器最大相邻 gap |
| --- | --- | ---: |
| 第 11 日前态 | 200.000–255.000 s；5500–7040 | 0.067 s |
| 第 12 日后态 | 350.000–410.000 s；9714–11385 | 0.067 s |

这四个端点只说明可定位，不能直接作为最终 clean span。mark 的 +226.720/+374.067
秒是墙钟值，也不能替换这些媒体 PTS。原始 1920×1080、`GUI.scale=1.3`
截图已证明战斗面板下部裁切；此 raw 不能作为逐团清单或战宽控件在 UI 中直接可见的实证。
原生 private trace/计算卡可以清楚标注其来源，但不能宣称这些下半 UI 字段被拍到。

## adapter 与正式 reel 尚缺的字段

| 层 | 能填 / 必须另取 |
| --- | --- |
| `prepare` 的 `source-manifest.json` | 上表 capture/session/recorder/marks 和标记截图给出了来源候选；正式脚本仍需重新逐字节核原 raw、完整 ffprobe 与原件。当前没有 J-A01 的 `PENDING_CLEAN_REVIEW` 清单。 |
| `extract-frame` / `human-review.json` | 先由人按 1× 完整看 600 秒，选每段真正无遮挡、同源且有用的内容；每个最终起止 PTS 各生成脚本所需 raw-derived PNG、exact decoded frame index、showinfo、argv/stdout/stderr 和 `EXTRACTED_UNREVIEWED` 回执，然后由同一真实审阅者核端点和连续画面并填写真实时间。两段如全用至少四个端点，但窗口边界不预定最终端点。 |
| `package` 的 `report.json` / `cell/promo/capture-timeline.json` / `evidence-index.json` | 目前全无。正式输出需 raw 复制件 bytes/SHA、`schema=2` timeline 的 clean begin/end marks、每段两枚 frame gate（PNG、抽帧回执、命令、stdio、人工 review、真实 PTS/无加载/来源可见声明）、所有文件的 evidence index，再实调 `load_capture_bundle(...).verify_unchanged()`。这些 GREEN 字段只能在完成上述步骤后由封装器生成。 |
| reel `clean_span_audit` 与 `control` | bundle GREEN 之后仍需单独 GREEN clean-span 审计和 1× reel/来源标签复核。更关键的是，**当次原生 battle-control 原件缺失**：`operator-steps/e2-06-d11-observe.json`、`advance.json` 都写 `control=null`、`subject_combat_membership_verified=false`，marks 两行也 `control=null`；前后 snapshot 的 `battle_control_snapshot_v1=null`。private trace 有 CombatID 16777218，但不能证明 ArmyID 18 的正式同帧 combat membership。#451 reel-edit 对每条 capture 的 `control` 要求是同 attempt 且在 source manifest 的 `files` 中；现有 `prepare` 只收固定原件与 marks 的 report/screenshot/control 引用，空 control 无法补。 |

为排除“原 run 其实另有 control 回执”，本轮列过该 attempt 的全部
`ck3-output/interactive-requests/` 与 `interactive-requests-responses/` 文件名：没有
`battle-control` 请求或响应。再搜索 `initial-snapshot.json`、`final-snapshot.json`、
`native-start-readback.json` 及全部同 run snapshot response，实际
`battle_control_snapshot_v1` 值均为 `null`；`query_supported=true` 只说明能力存在，
不代表执行了查询。`e2-06-d11-one-day.json` 和 private trace 可以哈希，但没有合法的
同帧 battle-control 结果。正式卡索引本身也写
`army18_exact_battle_control_membership_proven=false`。

因此，J-A01 **媒体 adapter** 将来或可在真人视觉证据齐备后独立封包；但按当前
`e4957f17e` 正式 E2-06/07 reel 的 capture 准入为 **RED**，不能直接入剪。
不得把前后 snapshot、private trace、旧 085 RED 或在旧 attempt 外新造的 JSON
冒充本次 battle-control。

若坚持正式同 attempt 的增援卡镜头，最小重录清单是：

1. 从**同一精确第 11 日源 save 和保存回执**冷载到新的隔离 attempt，冻结 CK3/DLL/injector
   与 readback 身份；若换源则卡片事实与口播重新核对。
2. 第 11 日暂停前态、单次推进到第 12 日暂停后态，各自取得合法原生
   `battle-control-snapshot-v1` 请求与响应，响应须在同帧绑定 actor 29829、ArmyID 18、
   CombatID 16777218、WarID 4、date、snapshot/revision 和真实 combat membership；
   把相应 control 原件的路径/bytes/SHA 放进该新 recorder 的 mark 引用，供
   `prepare` 的 source manifest 收录。查询返回不确定或 RED 时不拍成正式同源控制证据。
3. 同一新运行里保存 private join/width trace begin/finish 与单次 one-day 控制回执：
   ArmyID 22 入场、13 个 RegimentID、starting 2570/current 2560、侧缓存重算、
   width `1480→2220` 与首次伤害参数须同 CombatID/date 对应；若实测数变，
   E2-06/07 卡、旁白及字幕按新事实重算。
4. 在开新 raw 前，以原始桌面截图证明战斗面板**下半逐团与战宽**所需字段实际完整可见，
   并核 GUI scale 的磁盘读回、真实 GDI/桌面尺寸和 HUD 身份。此后新 raw 自己封口、
   FFprobe/marks 与人工原速审片；不从旧 1920×1080 裁切录像补出下半 UI。

高磁盘与 CK3 屏幕占用结束之前，不运行 `prepare`（当前实现对 GB 级 raw 重复 SHA）、
`extract-frame`（解码并复核 raw）或 `package`（再复制 raw）。所有新输出目录必须外置、
append-only，原会话、失败记录和媒体原样保留。
