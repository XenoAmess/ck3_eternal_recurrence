# E2-05 a02：录制封口后的独立无屏幕审计

2026-09-29 准备清单。目标原件预计为
`D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/raw/e2-05-d26.mkv`。
本清单写成时录制仍在进行；**尚未 stat、哈希、打开原 raw 或完整 ffprobe**，也未声称第
26→27 日镜头成功。旧 E2-05 a01 的无 raw/无推进 RED 保持原样。

## 放行门

两项缺一即停止于此，不读取 raw、`ffprobe.json` 或其它可能仍在写入的媒体文件：

1. 当次 screen owner 明确回执同一 `recording-e2-05-d26-a01` 的 FFmpeg 已自然退出，
   `recorder-end.json`、`recorder-final.json` 和完整 `ffprobe.json` 已写入且不再更新；
   未自然退出或只有 partial，保全 RED，不重命名成正式 raw。
2. 任务总线明确记录 E2-05 a02 的 `ck3-screen` lease 已 **RELEASE**，受管 CK3 的
   `session-result.json` 证明 cleanup `ok/tree_gone/cleanup_proven`，最终 CK3/录制进程
   inventory 为空。没有 owner 的明确信息，不凭文件时间、600 秒计时或旧屏幕截图推断释放。

放行后仍保持 Steam 离线。审计只访问原件，不启动 CK3、不操作桌面、不推进日期；审计输出
在旧 live attempt **以外**的新目录中创建并永久保留。任何失败另开新审计 attempt，绝不
修补或覆盖录制 attempt。

## 原始身份与事件边界

| 检查 | 必须读到的关系 |
| --- | --- |
| 录制器完整性 | `recorder-intent.json` 的 `workdir/session_output/raw_path` 指向这次 a02；`recorder-start.json`、`recorder-end.json` 的 PID、UTC/monotonic 时间与 `marks.jsonl` 首末行逐项匹配。`ffmpeg_exit_code=0`、`interrupted=false`；`recorder-final.json` 的 `result=ENCODED_UNREVIEWED`、`clean_spans_certified=false`、`human_review_completed=false`，`ffprobe_exit_code=0`。 |
| 逐字节绑定 | 原 raw 的实际 bytes/SHA 与 `recorder-end.raw` **和** `recorder-final.raw` 相同；完整 `ffprobe.json` 的实际 bytes/SHA 与 `recorder-final.ffprobe_output` 相同；`marks.jsonl` 的实际 bytes/SHA 与 `recorder-final.marks` 相同。审计前后再核原 raw 的 size/mtime，拒绝哈希期间变化。 |
| 按序 mark | 首行 `recorder-start`，末行 `recorder-end`，每行 monotonic 严格递增；中间 before/event/after 若有截图、control、report，逐个按当行 bytes/SHA 复核。墙钟 `approx_seconds_from_recorder_start` 仅供导航，**不是媒体 PTS**。不要仅凭 mark 宣称事件可见、击杀对象或同帧成员。 |
| 新 replay 身份 | 冷载来源日应是 `date_raw=53146848`，目标次日 `53146872`；玩家 `29829`、WarID `4`、ArmyID `18`、CombatID `16777218`、省份 `2633` 只能从**本次**原生 control/trace 与对应画面证明。旧 020/070/036→038 的数字不自动继承。若没有 event/after mark 或原生回执，状态应保留为缺证。 |
| 会话报告 | 旧式 `ck3-output/capture-report.json` 可是 `ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO`，因为录像器独立；不能把它改名为 adapter GREEN。`session-result.json` 的 shutdown 与零进程 inventory 要另核。 |

## 封口后机器 PTS 审计

在 `D:/w/e2` 使用已验证的
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`；新 run 前仍按
AGENTS 查询最新正式 `xar-promo` wheel，记录实际版本/SHA。本清单准备时已重新查询：
最新正式版仍为 v0.2.1，wheel SHA-256
`F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，选定
解释器实际报告 `xar-promo 0.2.1`。以下命令**仅在上面两项放行后**
执行。`audit_raw_video_pts.py` 逐字节核 raw/完整 ffprobe，读每一实际视频帧 PTS；只写新外置
报告，不解码画面或给 clean span。`-next01` 若已存在改新 suffix。

```text
mkdir D:/workspace/ck3_native_war_ai_promo_work/e2-05-a02-postrun-audit-20260929-next01
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/audit_raw_video_pts.py --recorder-workdir D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01 --output D:/workspace/ck3_native_war_ai_promo_work/e2-05-a02-postrun-audit-20260929-next01/pts-audit.json --min-duration 590 --max-frame-gap 0.2
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/audit_e2_05_postrun_links.py --recorder-workdir D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01 --session-output D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/ck3-output --pts-audit D:/workspace/ck3_native_war_ai_promo_work/e2-05-a02-postrun-audit-20260929-next01/pts-audit.json --output D:/workspace/ck3_native_war_ai_promo_work/e2-05-a02-postrun-audit-20260929-next01/postrun-links.json
```

第二条小文件关联器只使用前一条已完成的 raw/ffprobe SHA 报告，**不第二次重哈希原 raw**；
它重核 recorder intent/start/end/final、marks 首末 monotonic 与中间 screenshot/control/report、
session cleanup，并将结果固定为 `MEDIA_PTS_CANDIDATE_UNREVIEWED`、
`MEDIA_PTS_GAPS_OR_RED_UNREVIEWED` 或 `RED_PRESERVED`。它仅在前条报告真实产生后执行。

记录 `frame_count_with_pts`、首末实际 PTS、缺失/倒退帧数、`gap_count` 与前 20 处超过
0.2 秒的间隔；若超过 20 处，当前审计器不列出余下位置，须另开完整间隔索引后才能规划
覆盖全片的候选窗。若整条报告 `RED_PRESERVED`，仍可在后续单独挑选缺口两侧的连续候选窗；不能跨
缺口或把整条 RED 写成 clean。机器报告即使是 `PTS_CONTINUOUS_UNREVIEWED`，也只证明
该规则下的媒体时间轴，**不证明**目标 event、完整战斗 UI、字幕来源、原速观片或成片签核。

待原生会话完整结束后，可对该 recorder 另开 `prepare_existing_capture_bundle.py prepare`
外置目录，以原件清单进一步重核 capture/session、marks 与所有引用；它也会再完整哈希 raw，
需在低负载时**串行**执行。`prepare` 固定输出 `PENDING_CLEAN_REVIEW`，不写
`report.json`、timeline、evidence index。真正 exact frame 提取、视觉核对与人工 1×
审阅以后，才能再考虑 formal `package`。本次 postrun 审计只生成候选与缺口结论，不调用
`package`，不制造 review JSON 或 signoff。

## 审计回执最小结果

后续实际报告应保存：owner 封口消息/任务总线 RELEASE 的原件路径和 SHA、审计脚本与解释器
身份、三份 recorder 原件的 bytes/SHA、raw/ffprobe/marks 的复核 bytes/SHA、session cleanup、
新回放 before/event/after 的真实日期和身份证据、全视频 PTS 摘要及每个 candidate 的
`unreviewed` 标签。若因录像失败缺任何原件，写 `RED_PRESERVED` 和缺项，停止媒体准入；
不要凭本清单预填“通过”。
