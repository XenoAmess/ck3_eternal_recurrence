# 第二期 A05/K04/K05：控制读数与已知 PTS 断档预门

2026-09-29，基于 #451 `a6aff14109c30e8b7b5ef5e17749a826e7042a8d` 的[六章原片账](six-chapter-clean-span-candidates-20260929.md)、[四 raw 精确帧审计](four-raw-pts-candidates-20260929.md)及[项目镜头账](shot-list.md)作屏幕外只读复核。**本页是严格“候选场景 mark 自带同 recorder battle-control”构片方式的预门；不是完整 CK3 adapter 判定。认证 clean span 为 0 秒，人工原速 1× 审片和成片签核均为 0。**

外置 append-only attempt：`D:/workspace/ck3_native_war_ai_promo_work/episode02-control-pregate-20260929-a01/`。逐项结果 `candidate-window-pregate.json` SHA-256 `22B655F4E3DFA066A27B59F123B9F71E2663E4C7F6911A4424465B41DFCEDC91`；只读脚本 `audit_candidate_windows.py` SHA-256 `A34704AB1536B843584F9AC79808A6854D44B4121D1FD54413AA266CF9354739`；解释报告 `pregate-report.md` SHA-256 `C0544AEBaf4A830E7D203FF37683ABA697939AE09A5C39A1A3164B91B8D940E0`。输入小回执 `episode02-review-queue-20260929-a01/small-receipt-audit.json` SHA-256 `9C284A618609FC21B79B087DB7803546E61472946373345B5D67CE1E1BAEB430`。这些本机路径是定位方式，来源身份与各 raw、control SHA 也冻结在本仓[六章原片账](six-chapter-clean-span-candidates-20260929.md)；不能仅凭机器报告自行晋升片段。

脚本重新核对六条 recorder-final、marks 和各引用控制 JSON 的实际 bytes/SHA，确认引用文件留在同一 recorder attempt。它只核 `body.battle_control_snapshot` 为对象、`source.snapshot_id` 非空、`source.native_revision` 和 `queried_revision` 为整数，并拒绝**已记录**的 PTS gap 交叉。raw SHA 沿用当次 recorder 声明，**本轮没有读、重新哈希或解码原片，也没有重读完整 FFprobe**。窗内首末时间为导航区间，即使原四 raw 审计已有对应真实帧，也未据此批准剪辑端点；wall-clock mark 不当作 PTS。

| 预门 | 6 条明确拒绝的导航窗 | 精确理由 |
| --- | --- | --- |
| `PRE_GATE_RED` | A05-1 WarID 4 前态 | `e2t-s01-war4-before.control = null`。同 recorder 其他日期的控制不自动填此 mark。 |
| `PRE_GATE_RED` | A05-2 d32 writer 与 WarID 4 后态 | `e2t-s02-d32-writer.control = null`，`e2t-s02-d32-war4-after.control = null`。同源 writer/暂停后态原生回执能支持数值，不能代替这两个场景的控制或人工审片。 |
| `PRE_GATE_RED` | A05-2 260–290 秒负例 | 横跨冻结的 `271.267–278.833` 秒、7.566 秒 PTS 断档；任何连续 clean span 均不得跨越。 |
| `PRE_GATE_RED` | K05-a02 d27 转场 | `d27-after.control` 实际是 post-snapshot，不含当日 battle-control body；`d27-player-knights.control = null`。232.533/232.567 相邻原图的 11→10 变化不能补原生后态控制或 selector 身份。 |
| `PRE_GATE_RED` | K04-a07 d06 后态 | `d06-after.control` 实为 managed trace finish，不是 battle-control；原片另有 `411.167–413.300` 秒断档，所列候选从断档后开始。 |
| `PRE_GATE_RED` | K04-a08 d06 名单 | 独立 90 秒 recorder 只有 start/end marks，没有场景控制 mark；不能从同冷载的 panel recorder 借 control。 |

| 预门 | 7 条仅待审导航窗 | 尚缺的核心动作 |
| --- | --- | --- |
| `PRE_GATE_PENDING_ADAPTER_AND_HUMAN_1X` | A05-1 第 27→28 日；A05-2 第 28→29、30、31 日（4 条） | 四日控制引用有外层结构，导航窗未交叉已知断档；仍须精确首末帧、画面和遮挡、同日身份、完整 adapter 与 1×。A05-1/A05-2 是两条独立录制，不可拼作一条未切开的连续镜头。 |
| 同上 | K05-a02 d26 前态（1 条） | 仅前态控制有外层结构；d27 death/selector/后态须单独补证。 |
| 同上 | K04-a07 d05 前态、K04-a08 d06 panel（2 条） | 前者须把准确末帧选在 411.167 秒断档前；后者准确首帧须落在开头 8.133 秒断档后。跨冷载须显式切口和来源标签；panel 的 V3 当前数值仍 RED。 |

上述 `PENDING` **不是 GREEN 或可用秒数**。`RED` 仅拒绝所列严格 mark-control/连续构片方式；A05 d32 画面等若要换用“同 recorder 较早控制 + writer”的另一合同，应先明确书面规则、证明精确同源和镜头内容，再创建新 adapter bundle 与人工审片回执，不得直接把旧 raw 或旧 mark 追认 GREEN。

## 下次占屏的最早可执行顺序

1. **E2-04 d06 有界 current read + 名单**：先完成新 Release DLL/injector 与源码身份门，再在新 attempt 拍同 recorder 的 d06 原生 Character 34333 / Regiment 61 当前值、battle-control、原尺寸面板和名单。已有画面第 5 行有效勇武 7 与 trace character core 11 为不同量，不说“11→7”或“减 4”。
2. **E2-05 d27 selector + post-control**：待精确 EXE ABI/Release/one-action 门后，新 run 同源读 selector、CharacterID、d27 后态 battle-control 和死亡通知/名单；旧 K05-a02 的可见转场可辅助定位，不能填这个原生缺口。
3. **R0107 d11 新 600 秒录制**：必须先用最新源码与新 Release DLL/injector、build report/JUnit/配对 manifest 建立新的 no-launch，再执行受管 live，不能沿用旧 J-A01 控制为 null 的 115 秒导航窗。当前 R0107 live 准入仍 RED，新增合格 raw 为 0。

屏幕之外，A05/K04/K05 原片可在 CPU 与审阅资源释放后按精确源 ID 逐段原速 1×、记录覆盖物和端点，形成 append-only 审片/adapter 原件。六章目标 29:50（1,790 秒），旁白 22:30.384；旧四 raw a03 的乐观画面候选 735.967 秒，加上 K05 最多 360 秒的条件预算、剔除 J-A01 不可准入的 115 秒后，仍有**至少 627.033 秒条件性画面缺口**。这不是当前可剪时长：认证可剪仍为 0 秒，任何候选淘汰会扩大缺口。正式六章 reel、候选 MP4、成片原速 1× 与按最终 MP4 bytes/SHA 的人工签核完成后，才可把用户授权的**单个视频文件**放入固定 OneDrive 交付目录；本页没有触发媒体构建或上传。
