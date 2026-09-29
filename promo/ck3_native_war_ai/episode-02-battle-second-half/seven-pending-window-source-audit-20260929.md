# 第二期七个待审导航窗：来源与封装预审

2026-09-29；先以 Draft PR #451 HEAD `34239889eeefe04111d38f8dcfa06fbf3ffde8da` 做七窗只读核查，再在独立修复分支对 K04-a07 运行一次新的来源清单 `prepare`。初审复核了既有 `recorder-final.json`、`marks.jsonl`、真 `battle_control_snapshot` 外层结构、四份 `capture-report.json` 与会话清场回执；七窗表中的逐帧 PTS 来自仓库冻结的四 raw／K04／K05 审计，本轮没有重新解码原片。后述 `prepare` 对 K04-a07 的原 raw 和引用证据**逐字节重核**，不改写旧文件。没有启动 CK3、OBS、新 xar-promo 原生 run，也没有人工 1× 审片。七窗仍为 `0 s` 已认证 clean span。

## 共通门禁

四个受管 attempt 的 `ck3-output/capture-report.json` 均为 `ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO`，`raw_video=null`、`recording_complete=false`、`clean_spans=[]`、`adapter_bundle_validated=false`。各 recorder 独立封口为 `ENCODED_UNREVIEWED`、FFmpeg/FFprobe 返回 0；四份会话 `session-result.json` 均 `ok=true`、`shutdown.ok/tree_gone/cleanup_proven=true`。在这四个 attempt 内均未找到正式 bundle 的根 `report.json`、`cell/promo/capture-timeline.json` 或 `evidence-index.json`。外部录像封口与受管无录像报告必须经新 bundle 绑定，不能改名旧报告。

| 待审窗 | 同 recorder 原生控制 | 已知媒体边界 | 机器审计下一步；剩余缺口 |
| --- | --- | --- | --- |
| `A05-pursuit-d27-d28`，A05-1 `350.000–450.000` | d27 `native:3` / wrapper 4、d28 `native:6` / wrapper 7；两条 `battle_control_ready=true`，日期 `53146872→53146896`。 | 16,934 帧，raw SHA `C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B`；冻结窗内最大 PTS gap `0.067 s`。 | 可在新 release 核验后建独立 `PENDING_CLEAN_REVIEW` 来源清单；逐帧选真实入出点，审日期/HUD/遮挡与标注，并以原速看全 raw。`mark` 墙钟不是 PTS。 |
| `A05-pursuit-d28-d29`，A05-2 `60.000–170.000` | d28 `native:6` / 7、d29 `native:9` / 10；日期 `53146896→53146920`，两条真 control。 | 16,560 帧 raw SHA `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC`；本窗最大 gap `0.067 s`。 | 可与以下两窗共用 **A05-2 自己**的新 pending 来源清单，随后各自缩窗、抽原始首末帧和审完整连续画面。A05-1/A05-2 之间须显示剪辑切口。 |
| `A05-pursuit-d30`，A05-2 `200.000–250.000` | d30 `native:12` / 13，日期 `53146944`，真 control。 | 本窗最大 gap `0.067 s`；与上一窗之间另有 `179.600→180.067` 缺帧 `0.467 s`。 | 本窗自身可进 pending 清单；只审本窗，不跨该断档，也不把 d29 画面接成一条连续 raw 段。 |
| `A05-pursuit-d31`，A05-2 `300.000–349.967` | d31 `native:15` / 16，日期 `53146968`，真 control。 | 本窗最大 gap `0.067 s`；`271.267→278.833` 缺帧 `7.566 s`，`350.000` 不是本窗真实帧。 | 本窗自身可进 pending 清单；禁止跨 `250–300` 缺口，入出点必须选 FFprobe 中真实 PTS。 |
| `K05-d26-before`，K05-a02 `0.000–210.000` | d26 `native:3` / 4，日期 `53146848`，真 control SHA `D41E384CE022C261E15E3761980A0A78E26BA0B21C9FCF3F2393F062F03CEC1F`。 | raw SHA `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`；全片 12,656 帧、无已报 >0.2 s PTS gap。 | 可进 pending 清单，但搜片窗从 `0` 开始，必须排除加载/准备画面并缩到实拍 d26 前态。该 recorder 的 d27 `control` 实为 post-snapshot、名单 mark 为 null；不能把本窗 control 扩给次日死亡或 selector。 |
| `K04-a07-d05-before`，K04-a07 `0.000–411.167` | d05 `native:3` / 4，日期 `53146344`，真 control SHA `3BC180231A4EB38DF2F7CB0111D816BB0E28689BEA7A62F7A1F3A1C93D8408E0`。 | raw SHA `950D94FE20A937806A1A8976160D66D8BF04D5DE3C7CD85A67D7DF5ACE45D3C9`；`411.167→413.300` 缺帧 `2.133 s`。 | **#451 原 HEAD 的封装器源码硬拒绝整条 raw 的 prepare**：同 recorder 的 `d06-after` mark 截图指向同 run 屏幕租约 sibling `episode02-e2-04-d05-screen-lease-20260929-a07/d06-player-knights-hover-a01.png`，`checked_marks()` 对全部 mark 引用要求 `within=attempt`，`package()` 也不能按 attempt 相对路径复制。原 mark 未修改；本独立分支的严格 sibling 修复已取得下述真实 pending 清单。下一步缩掉开头加载画面，末帧不得跨 2.133 s 缺口；该 run d06 control 实为 trace-finish，不能证明后态。 |
| `K04-a08-d06-panel`，K04-a08-panel `8.133–239.967` | 独立 d06 冷载 `native:3` / 4，日期 `53146368`，真 control SHA `5469D9F7F066B805581038E8D9735CF51C3616823E5CAAFEF390059E73983C19`。 | raw SHA `44EC9EE794658C13B6CBAE5B13D9A0105CC0C4DB04F7918D51FEDB4DA43C15D9`；`0→8.133` 缺帧 `8.133 s`，整 raw PTS 审计仍 `RED_PRESERVED`。 | 可仅对断档后的实际连续子段推进 pending 清单与精确帧审阅；完整 raw 仍应 1× 观看。d05→d06 是两次会话，需明示冷载切口。V3 当前 CharacterID/团数值查询 RED，画面不能替该数值来源。 |

这里的“可进 pending 清单”对前六窗只评估现有来源路径及外层结构，**没有对它们运行 `prepare` 或证实逐字节复核通过**。在 #451 原 HEAD 上，7 窗中 6 窗具备下一步机器清单的静态候选条件；K04-a07 在本独立分支完成修复后实际取得下述 pending 清单。七窗全部仍缺原速全 raw 与精确首末帧审阅、无覆盖/来源标签证据、每段 PTS gap 的正式复算、人工回执及独立 CK3 adapter `report`/timeline/evidence index。没有正式 `package` 或可入片秒数。

## 独立修复候选的精确边界

本分支只让 `prepare_existing_capture_bundle.py` 接受原 mark 声明的**截图 PNG** 位于与 attempt 同父目录、同 run 名且由 `-live-` 唯一替换成 `-screen-lease-` 的 sibling **直属文件**；其它目录、子目录、外部 control/report 仍拒绝。原 sibling 截图本次 `certutil` SHA-256 回读 `943A34223CFE5C19FFEE5488C5D4C9F2F678B1CBD6A5DA21DBC37AA566E425BD`，与未改写 mark 相等。pending manifest 仍保存原绝对路径、大小和 SHA；后续复核仍从未改写的 marks 重建精确引用集合；未来满足真人审阅门后，`package` 才会将该截图复制到 bundle 的 `source/external-screen-lease/<sibling 名>/`，保全其 bytes/SHA。此修复不把 d06 的 trace-finish 变成 battle-control，也不批准 d05 的 clean span。聚焦 fixture 的正反例在普通和 `-O` 各通过 `15/15`。

### K04-a07 真实 pending 清单

从修复提交 `8d29d14097bf22193070394bf256da9e23376f82`、本 worktree 的 `tools/requirements-promo-toolchain.txt` 和显式 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，对原 K04-a07 attempt/recorder 运行项目 wrapper 的 `prepare`；输出到新外置目录 `D:/workspace/ck3_native_war_ai_promo_work/episode02-k04-a07-adapter-pending-20260929-a01/`。本轮开始前重新查询独立仓库 GitHub Latest 为 `v0.2.1`；解释器 `-m xar_promo --version` 为 `0.2.1`，精确 wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。清单 `source-manifest.json` **9066 bytes**，SHA-256 `67D2A09CE07B7195597C717F4371858CAD768E8B9E3871CD18465A6E5406D446`，状态 `PENDING_CLEAN_REVIEW`、`adapter_eligible=false`、`human_1x_review_performed=false`、`clean_spans=[]`。它重核原 raw `2459812208 bytes` / SHA `950D94FE20A937806A1A8976160D66D8BF04D5DE3C7CD85A67D7DF5ACE45D3C9` 与完整 FFprobe `12664704 bytes` / SHA `0AC16BCFD453DA10DF168E154EA0B67CA1EAB18CE08C8C17CA0EA7BF325C2A1F`，并将外部 sibling 截图 `4907043 bytes` / SHA `943A34223CFE5C19FFEE5488C5D4C9F2F678B1CBD6A5DA21DBC37AA566E425BD` 同时列入原 mark 投影和清单文件集合。外置目录目前仅有该清单；没有正式 `report.json`、timeline、evidence index 或 `package`。后续先由真人按原速审完整 raw、确定 d05 精确端点并审帧，再填真实审阅回执；不能为验证复制路径伪造真人 1×。

### 其余六窗来源清单：前五份实跑，末窗等待屏幕释放

在每个新外置 wrapper `prepare` 前，分别重新查询正式 [GitHub Latest](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest)，五次均为 `v0.2.1`；沿用已验证的主 worktree 解释器 `xar-promo 0.2.1` 和精确 wheel SHA `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。运行源码 HEAD 为 `d4d9ff6e693b8e3ce33252d1a8644438dce1d65b`。下表目录均相对 `D:/workspace/ck3_native_war_ai_promo_work/`，每个目录只创建 `source-manifest.json`；输出 SHA 由完成回执与随后 `certutil` 回读一致。每份为 `PENDING_CLEAN_REVIEW`、`adapter_eligible=false`、`human_1x_review_performed=false`、`clean_spans=[]`。

| 窗口 | 独立新目录 | 清单 bytes / SHA-256 | 精确原 raw 来源 |
| --- | --- | --- | --- |
| A05-1 d27→28 | `episode02-a05-a01-d27d28-adapter-pending-20260929-a01/` | `9111` / `E066640F592440003CB46260EA0C04DA2F84BDB735FC44C2AC054672D876572A` | 951186809 bytes / `C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B` |
| A05-2 d28→29 | `episode02-a05-a02-d28d29-adapter-pending-20260929-a01/` | `13924` / `8115562E7924F5C6C6A2E76AB886563AB16FD1188449930D72484716FD2AC043` | 840210967 bytes / `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC` |
| A05-2 d30 | `episode02-a05-a02-d30-adapter-pending-20260929-a01/` | `13924` / `8115562E7924F5C6C6A2E76AB886563AB16FD1188449930D72484716FD2AC043` | 同上 |
| A05-2 d31 | `episode02-a05-a02-d31-adapter-pending-20260929-a01/` | `13924` / `8115562E7924F5C6C6A2E76AB886563AB16FD1188449930D72484716FD2AC043` | 同上 |
| K05-a02 d26 前态 | `episode02-k05-a02-d26-adapter-pending-20260929-a01/` | `10268` / `EB987A4BF8C15B5BF0E93380BA22FE5F4D33E6355CFD07617BD6786623319F05` | 2451530594 bytes / `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F` |
| K04-a08 d06 panel | **未启动** | — | H3937 受管冷载优先；待屏幕实机和磁盘负载清场后再新建 attempt。 |

A05-2 三份清单的 bytes/SHA 相同是预期：`prepare` 只绑定整条相同 recorder 的原件，窗口选择与真实 clean span 尚未写入它。K05 d26 清单保全了后续 d27 错型 mark，但不使后态 battle-control 有效；正式使用范围仍仅 d26 前态。五份实跑均未抽精确首末帧、没有真人原速全 raw 审看，也没有 `package` 或 adapter 三件套。H3937 准备受管实机时，K05 当前 `prepare` 自然完成后暂停了 K04-a08 的大文件读取。

来源：[`control-known-gap-pregate-20260929.md`](control-known-gap-pregate-20260929.md)、[`six-chapter-clean-span-candidates-20260929.md`](six-chapter-clean-span-candidates-20260929.md)、[`four-raw-pts-candidates-20260929.md`](four-raw-pts-candidates-20260929.md)、[`existing-capture-adapter-bundle.md`](existing-capture-adapter-bundle.md)。所有原始文件位于上述表对应的 `D:/workspace/ck3_native_war_ai_promo_work/episode02-*/`；本页不覆盖它们。
