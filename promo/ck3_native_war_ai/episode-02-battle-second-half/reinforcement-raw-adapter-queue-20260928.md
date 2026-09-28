# E2-06/07 A01 增援 raw 的第四条 adapter 队列

2026-09-28 屏幕外元数据复核。机器清单为 [JSON](reinforcement-raw-adapter-queue-20260928.json)；原来[三条 raw 队列](three-raw-adapter-queue-20260928.md)仍记录 E2-02/03 A01 和 E2-09 A05 a01/a02，本文件补入漏排的正式 E2-06/07 A01 增援原片。此轮只重新哈希小型 capture、session、recorder、PTS、marks 回执并检查原 raw/ffprobe 文件大小；**没有读取或重哈希 1.325 GB raw、15.9 MB ffprobe，没有解码、复制、审片、生成 clean span 或 adapter bundle**。raw 与 ffprobe 的 SHA 是原 recorder 回执声明，后续 `prepare` 必须逐字节重验。

| 原件 | 本轮依据与状态 |
| --- | --- |
| `episode02-e2-06-d11-live-20260928-a01/ck3-output/capture-report.json` | 本轮 SHA `F59CBFFA…51D4F2F`；受管会话清场，`ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO`，原报告明确 `adapter_bundle_validated=false`。 |
| 同 attempt 的 `ck3-output/session-result.json` | 本轮 SHA `3413FB08…941108C`；shutdown `tree_gone=true`、`cleanup_proven=true`。 |
| `recording-e2-06-d11-a01/recorder-final.json` | 本轮 SHA `F4EA84BC…3741F`；raw 1,325,156,480 B、原回执 SHA `501B4C2A…51024C7`，1920×1080 H.264，600.000 秒，`ENCODED_UNREVIEWED`。 |
| `recording-e2-06-d11-a01/pts-audit-a01.json` | 本轮 SHA `6BF5086B…ECBCDB`；16,691 帧，PTS 0.000–599.967 秒，缺失、倒退及大于 0.2 秒的断档各为 0；`PTS_CONTINUOUS_UNREVIEWED`。 |
| `recording-e2-06-d11-a01/marks.jsonl` | 本轮 SHA `B028F603…9C02E`；第 11 日前约 226.720 秒、第 12 日后约 374.067 秒是 recorder 墙钟导航值，**不是媒体 PTS**。不得以此造首末帧、证明逐团 UI 可见，或宣称时间段连续审片。 |

原始画面在 `GUI.scale=1.3` 下[裁掉战斗面板下部](e2-06-combat-panel-crop-readonly-20260928.md)。可见的上部状态仍须原速看片确认；下部逐团和战宽若用于论证，须后续同轨补拍，或清楚标示其来源为原生 trace/计算卡，不能说成这一原片的 UI 直接实证。正式 E2-06/07 卡已经绑定 A01 事实回执；这条 raw 不能和 A05 追击/终局混作同一次 cold load。

## 串行入队

先等受管 CK3/录制停止和 `ck3-screen` 释放；新 run 前再次查询独立 `xar-promo` 仓库的**最新正式 Release**，选定并验证对应 wheel、解释器和 CLI。新外置目录应在源 attempt 外，且必须尚不存在。已核的三 raw 队列列有 `prepare`、`extract-frame`、真实人工原速审阅及 `package` 的共同合同；第四条 `prepare` 命令为：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py prepare --attempt D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-live-20260928-a01 --recorder D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-live-20260928-a01/recording-e2-06-d11-a01 --output D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a01-reinforcement-pending-next01
```

从完整 ffprobe 选存在的真实首末 PTS，再抽帧；这两处 mark 只帮定位。原速看完整 600 秒和选中端点之后，审阅者才可填写与原 raw、PTS 帧、来源身份绑定的 `human-review.json`，由另一个新目录执行 `package`。`prepare` 的预期最多是 `PENDING_CLEAN_REVIEW`，绝非 adapter GREEN；终片还要另行完整 1× 人审和精确字节签核。

四条已封口 raw 的原回执合计 **4,421,454,290 B（约 4.12 GiB）**，完整 ffprobe 合计 **63,119,422 B（约 60.2 MiB）**。按四条各 600 秒，完整原速人工审片的理论下限是 **40 分钟**，不含端点复查、章节成片复看和剪辑。四条 `package` 若都合格，会仅因 raw 复制额外占约 4.12 GiB；预留至少 **6 GiB** 给其余证据和中间资产。任一原片不合格时不能为了时码硬填：六章目标 29:50 中实测旁白 22:30.384，[桥接预算](production-six-chapter-handoff-20260928.md)尚有 7:19.616，**其中增援章 3:02.288**；预算不是现成 clean span。骑士章合格原片仍缺，四条旧 raw 也不能补这一章的当次画面。
