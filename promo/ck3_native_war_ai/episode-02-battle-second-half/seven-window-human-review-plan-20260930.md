# 第二期七窗原片审阅包与逐帧执行顺序

2026-09-30。七个 `PENDING_CLEAN_REVIEW` 导航窗属于五条独立 raw。初版计划仅运行轻量的 `plan_review_windows.py`：按精确 SHA 核对五份 pending 清单与原 FFprobe JSON，检查原 raw 的路径和文件大小，读取帧 PTS；**该初版步骤没有打开、重新哈希、解码或播放 raw**。五个结果均为 `MACHINE_PTS_NAVIGATION_ONLY_UNREVIEWED`，七窗的候选 PTS 间隙均不超过 0.2 秒。这些窗只是审片导航范围，不是已批准的剪辑端点或 clean spans。已批准 clean span 仍为 `0 s`；没有真人 1× 原片审阅、审帧回执、正式 `package` 或 adapter GREEN。

**2026-09-30 机器端点进展**：上述是初版轻量计划的时间切片。随后在独立外置 attempts 对七窗 14 个导航首末帧全部完成原 raw 绑定的 `EXTRACTED_UNREVIEWED` 抽取；[逐件回读报告](seven-window-endpoint-readback-20260930.md)核对了七窗总汇、六份机器来源报告、三份孤帧视觉预筛，以及 **14/14 PNG、14/14 抽帧回执 SHA**。原 raw 没有在这次回读中再次打开。14 张孤帧的 AI 视觉预筛只定位审片重点，未观察中间帧或完成真人完整 raw 1×。`human_1x_full_raw_review_count=0`、人工审帧 `0`、已认证 clean span `0 s`、adapter GREEN `0`，以下所有 PTS 仍为未批准导航边界。

## 输入身份与审阅顺序

路径基准：`D:/workspace/ck3_native_war_ai_promo_work/`。下表的 pending 与 PTS 文件名分别相对此基准下的原 pending 目录和新只读结果目录 `episode02-seven-window-review-plan-20260930-a01/`。每个 pending 清单的 `source-manifest.json` 都已经在先前 `prepare` 中逐字节绑定整条 raw、FFprobe、marks 和证据；本轮 PTS 计划不重做那次 GB 级哈希。A05-2 的 d30、d31 独立 pending 目录与 d28→29 清单逐字节相同，审片时选择 d28→29 这一份作为**同一原片的单一身份入口**。

| 顺序／整条 raw 1× 时长 | pending 来源清单 SHA-256 | 导航窗：真实首末帧 PTS；帧号（0 起） | 本轮 PTS JSON SHA-256 |
| --- | --- | --- | --- |
| 1. A05-1，约 600 s | `episode02-a05-a01-d27d28-adapter-pending-20260929-a01/source-manifest.json` `E066640F592440003CB46260EA0C04DA2F84BDB735FC44C2AC054672D876572A` | d27→28：`350.000000–450.000000`，`9887–12679`，最大 gap `0.067 s` | `a05-a01-pts.json` `6B047387415616931E3560C7460A91340566A7588327A630CD1F2B72C1B3C256` |
| 2. A05-2，约 600 s；三窗只需完整看同一 raw 一次 | `episode02-a05-a02-d28d29-adapter-pending-20260929-a01/source-manifest.json` `8115562E7924F5C6C6A2E76AB886563AB16FD1188449930D72484716FD2AC043` | d28→29：`60.000000–170.000000`，`1648–4726`；d30：`200.000000–250.000000`，`5558–6966`；d31：`300.000000–349.967000`，`8165–9573`；各窗最大 gap `0.067 s` | `a05-a02-pts.json` `CE8A7C86A76B4F880ADEB325A955891349786A471D2E31169EBE05C06EBFEFE6` |
| 3. K04-a07，约 599.966 s | `episode02-k04-a07-adapter-pending-20260929-a01/source-manifest.json` `67D2A09CE07B7195597C717F4371858CAD768E8B9E3871CD18465A6E5406D446` | d05 前态：`0.000000–411.167000`，`0–9371`，最大 gap `0.167 s` | `k04-a07-pts.json` `7E9F9F11C157B7B5570603993CAF7664FD104D29D3911D2018875DB5EA7DA402` |
| 4. K04-a08，约 240 s，独立冷载 | `episode02-k04-a08-d06-panel-adapter-pending-20260929-a01/source-manifest.json` `856631970989D82932400C66E6C4977A6FF692F52DE0E15458C07DFCD46A1705` | d06 panel：`8.133000–239.967000`，`1–4804`，最大 gap `0.100 s`；整条 raw 的 `0→8.133 s` 缺帧仍为 RED | `k04-a08-pts.json` `B59E960C76AE9208AE65DFE57771723C0278AAD8CB7039E5A411E79F453A656D` |
| 5. K05-a02，约 600 s | `episode02-k05-a02-d26-adapter-pending-20260929-a01/source-manifest.json` `EB987A4BF8C15B5BF0E93380BA22FE5F4D33E6355CFD07617BD6786623319F05` | d26 前态：`0.000000–210.000000`，`0–4460`，最大 gap `0.100 s` | `k05-a02-pts.json` `D7C9296D37D437623ECFD3C2C116B72E949BA7F243EA40302C98F00A8DF7A9BC` |

五条 raw 全片最短审看时间约 `2639.966 s = 43 分 59.966 秒`，另需停顿记笔记、看七段连续画面及精确首末帧；实际排班建议给真人 `60–90 分钟`。这是工作量预算，不能据此填写已看回执。每条独立 raw 先从头到尾以 1× 完整看一遍，记录审阅者、时间、是否有加载/黑屏/外部遮挡/非 CK3 画面、HUD 与日期、精确可用候选区间。A05-2 三窗在同一次整条 raw 审看中分别标记；A05-1→A05-2 与 K04-a07→K04-a08 均为不同 recorder，中间必须作为可见剪辑切口处理。

### 三组并行分配

下表是**待分配工作包**，不是已发生审片。三位真实审阅者在各自可用、互不占用受管 CK3 屏幕的审阅环境中，且原片仍按既定来源身份只读访问时，三组可以同时开始；如只有当前这块受管屏幕或一位审阅者，则先等屏幕释放，再按上表顺序串行。不得以把原片传输到未授权位置或挤占 CK3 屏幕换取并行。

| 工作包 | 独占的 raw／窗口 | 完整原片 1× 下限；含笔记排班 | 已完成的机器导航端点数；真人仍待审 | 特别判定 |
| --- | --- | --- | --- | --- |
| A：追击 | A05-1 d27→28；A05-2 d28→29、d30、d31，共两条 raw、四窗 | `20:00`；建议 `30–40` 分钟 | 4 段 × 首末帧 = **8 次** | A05-2 三窗只看同一整条 raw 一次；逐窗避开原片窗外的 `0.767/0.467/7.566 s` 缺口。两 recorder 间保留切口。 |
| B：K04 | K04-a07 d05 前态；K04-a08 d06 panel，共两条 raw、两窗 | `13:59.966`；建议 `20–30` 分钟 | 2 段 × 首末帧 = **4 次** | a07 端点不得跨 `411.167→413.300 s`；a08 整条 raw 前 `0→8.133 s` 仍 RED。检查首帧 HUD、冷载切口；当前 V3 数值真读回仍缺。 |
| C：K05 | K05-a02 d26 前态，一条 raw、一窗 | `10:00`；建议 `15–20` 分钟 | 1 段 × 首末帧 = **2 次** | 检查 `0 s` 起始画面是否加载；d27 错型 post-snapshot／null roster 不可当 battle-control。 |

若三组确实有独立审阅者和设备，原片播放的理论墙钟下限由 A 组决定，为 `20:00`；含记录的排班参考 `30–40` 分钟，再加端点解码、审帧与合并门禁时间。单审阅者仍按五条原片共 `43:59.966` 的理论下限及 `60–90` 分钟排班。每组必须保留原片全程 1× 的真实审阅事实与不确定项；一个组的结果不能代替另组，更不能提前生成真人回执。

**机器抽帧队列**：A／B／C 可以并行完成小型 SHA、PTS 和审阅记录的准备，但每个 `extract-frame` 会重新逐字节验证原来源清单（其中包含 GB 级 raw），随后才解码目标帧；8＋4＋2＝14 次导航端点大文件读取已在独立外置目录完成。最终真人选定的精确入出点若与现有导航端点不同，还须为新 PTS 分别新建外置抽帧目录。受管 CK3 冷载及屏幕独占期间不启动新增命令；可见 I/O 争用时保持一次一端点。旧失败与成功输出均保留。三组可各自复核 exact FFprobe PTS、decoded index、FFmpeg `showinfo`、PNG 和 command/stdout/stderr SHA；审阅者亲看最终首末帧后才填写实际结果。A05-2 d28→29 两端点试跑约 53 秒，K04 四端点合计约 503 秒；来源与系统负载不同，不能以此推定新端点的固定耗时。

**合并门禁**：协调者按五条 raw 的绝对路径、bytes、SHA 和五份 pending 清单 SHA 去重，核对每组实际审阅者/时间、完整原片 1×、录制起始 HUD、每个最终区间连续画面、无加载/外来覆盖和精确首末帧。逐段重算 `≤0.2 s` 的内部 PTS gap，并检查抽帧回执时间早于对应真人审帧时间；A05-2 的三段可在同一 raw 回执中列多段，不能将不同 recorder 合为一个 raw 回执。任何条件 RED／未知就隔离该段或 raw，保留原文件及失败记录；各组单独由真实审阅者形成符合合同的回执后，才按每条通过的 raw 各建新 `package` 目录。汇总只引用各 bundle 的 `report.json`、timeline、evidence index、bundle 回执及各自 SHA；仍缺的 K04 V3／K05 d27 后态与整片 1× 成片签核保持独立门禁。当前三组全为待审，`clean_spans=[]`。

## 原片审阅时必须判明的条件

1. 先核对播放器打开的是 pending 中的绝对 raw 路径与预存 SHA 身份；播放完整 raw 的起止及全过程按 1× 观察。若播放器不可靠地呈现 PTS，用保存的 FFprobe PTS JSON 导航，但不得把墙钟 `mark.approx_seconds_from_recorder_start` 当媒体时间。记录加载、冻结、跳帧、切屏、遮挡、非原生 HUD、来源身份标签和任何不能承诺的画面；未知填未知，不能填通过。
2. 对七个候选窗逐段观察连续画面，并从实拍内容缩到真实入出点。`0.000` 是 K04-a07/K05 的搜索起点，不能自动视作无加载的片头。正式 `package` 还要求 `gameplay_hud_visible_at_recording_start=true`；若任一 raw 的真实首帧不满足该条件，即使后面有可看的子段，也不能如实走当前合同，需保留 RED 并重新取景或修订合同。K04-a08 首帧到第二帧 `8.133 s` 的断档必须保留在全片观察记录，不能以断档后的候选窗掩盖全 raw RED。
3. A05-2 避开 `37.933→38.700`、`179.600→180.067`、`271.267→278.833 s` 三处窗外 PTS 缺口；尤其不得把 d30、d31 连成跨越 `7.566 s` 缺帧的一段。K04-a07 的 `411.167→413.300 s` 缺口在导航窗外，最终端点不得跨越。每个最终独立区间都须重新计算内部最大相邻 PTS gap `≤0.2 s`。
4. K04-a07 只证 d05 前态，不能把该 run 的 d06 trace-finish 当 battle-control。K04-a08 只可评审 d06 panel 画面；当前 V3 CharacterID 34333／prowess／regiment 61 数值读回 RED，不能由截图补足。K05-a02 只证 d26 前态；d27 mark 是错型 post-snapshot 且名单 mark 为 null，不能延伸至 d27 死亡或 selector。

14 张端点孤帧的 [AI 视觉预筛与逐件 SHA 回读](seven-window-endpoint-readback-20260930.md) 给真人审片增加三个优先问题：其一，A05-1 的 `350 s` 样本尚无详细战斗面板，后续 A05 四窗样本出现 **战败／撤退中／追击中**，须找到真实面板进入过程，并避免把追击期的“战败”剪作 d32 writer 证据。其二，大面板战斗侧数从 `824→803→782→761`，与现有旁白草稿第 40 行“可比兵团当前人数不变”存在观众可见的口径张力；先核同源逐团账及两种人数的分母，再决定是否说明或修订文案，**本计划未改原稿，也不据孤帧断言数值矛盾**。其三，K04-a07/a08 的骑士悬浮卡挡住战斗面板，K05 样本为 `11 对 4590` 且有海域 tooltip；都需真人看完整 raw 才能决定真实无遮挡画面。K04-a08 `0→8.133 s` 与其他窗外缺帧继续保留 RED。

## 端点机器复核与真人回执的顺序

受管 CK3 占屏期间不播放原片或新增大文件 FFmpeg/录屏。现有 14 个导航端点已机器抽取且处于 `EXTRACTED_UNREVIEWED`，可供真人日后定位；它们没有获准成为最终剪辑边界。屏幕释放后，真人须按 1× 完整看五条 raw 并缩窗。对**每个最终拟用的独立 span**，从原 FFprobe 列表选两个真实帧 PTS；若不同于现有端点，分别以全新的外置目录执行 `prepare_existing_capture_bundle.py extract-frame`（使用已验证解释器，例如 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`）：

```text
<verified-python> promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py extract-frame --source-manifest <EXACT_PENDING_SOURCE_MANIFEST> --pts-seconds <EXACT_EXISTING_BEGIN_OR_END_FRAME_PTS> --output <NEW_EXTERNAL_ENDPOINT_DIRECTORY>
```

每个命令产生 `EXTRACTED_UNREVIEWED` PNG、实际 decoded index／PTS、命令、stdout、stderr 与 SHA 回执；失败目录和原件保留，重试新目录。现有 14 份导航端点回执已逐字节回读，新增端点仍会读 GB 级原片，须待屏幕任务不受 I/O 干扰时运行。比较每次解码回执 PTS 与 FFprobe 中相应真实帧，再由真人审看最终 PNG 对应的入出点和区间连续画面。抽帧完成时间必须早于实际人工审帧签回执时间。

真人完成审看后，才按 [`existing-capture-adapter-bundle.md`](existing-capture-adapter-bundle.md) 的 `human-review.json` 合同写实际审阅者、UTC 时间、整条 raw 1×、每段真实精确 PTS／首末帧 SHA、连续观察和布尔判定；不要复制其中的示例 `true` 值。任何不符合同的 raw/区间保留 RED，不得写 `human_1x_full_raw_review_performed=true` 或制造 clean span。随后每条通过的 raw 可用新外置目录运行一次正式 `package`，由项目 wrapper 重核原件、端点、间隙和审阅时间，复制约 `7.62 GB` 五条 raw 的相应通过子集并调用独立 CK3 adapter；新 run 前重新核最新正式 `xar-promo` wheel、同解释器版本及相关 `--help`。封装 I/O 耗时应以首条实测为准。adapter GREEN 也只覆盖所声明的机器绑定条件，不能取代整部成片的真人 1× 签核。

## 仅凭现有文件能做与新 capture 依赖

| 目标 | 现有文件离线可做 | 仍需新 capture／其他条件 |
| --- | --- | --- |
| 七窗画面及已录的同 recorder control | 五条 raw 的完整 1×、七窗可用画面缩窗、精确 PTS／端点解码、实际真人回执及符合合同时的新 adapter bundle | 无需启动 CK3 才能**审现有画面**；但审片可能判出加载或叠层而拒绝。 |
| K04 d05→d06 强度数值对照 | 分别审 K04-a07 d05 与 K04-a08 d06 panel，并在剪辑中标出跨冷载切口 | d06 当前 V3 CharacterID／prowess／regiment 数值真读回仍 RED，须有新的受管控制取证；旧画面不能代理数值。 |
| K05 d26→d27 伤亡／selector 后态 | 审 d26 前态画面与 control | d27 后态真 battle-control、死亡/selector 同 recorder 证据缺失，须新 capture。 |
| A05 d32 writer、war4 后态及 E2-06/07 J-A01 d11 | 现有七窗不能扩大为这些日期或章节的真控制 | 需新 capture 的 battle-control、对应 GUI／无遮挡 raw，再各自建新 pending。 |

本计划引用 [`seven-pending-window-source-audit-20260929.md`](seven-pending-window-source-audit-20260929.md) 的来源审计及五个外置 PTS JSON。新 PTS JSON 仅保存已有小文件与预存 raw 身份的只读派生；旧 mark、raw、capture report 和 pending 清单均保持原样。
