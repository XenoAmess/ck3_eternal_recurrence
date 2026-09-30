# 第二期七窗：真人 1× 原片审阅执行单 v2（空白）

2026-09-30 冻结机器准备版。本单没有填写真人结果。14/14 导航端点为 EXTRACTED_UNREVIEWED；整条原片真人 1× 审阅 0/5、真人端点审阅 0/14、认证 clean span 0 秒、adapter GREEN 0。只读引用旧报告/清单；没有打开、播放、解码或重新哈希 GB raw。审片员须本人填写空栏，不能将未知或空栏写成通过。

2026-09-30 追加式勘误：此 v2 从 v1 原件复制，修正 A05-2 原片 SHA 少一个 A 的排印错误，并列出五个 OneDrive 目标文件名；v1 与传输首次 source_hash RED 原样保留。此表仍是空白真人执行单，不是已看回执。

仓库外 v1 冻结件 `D:/workspace/ck3_native_war_ai_promo_work/episode02-seven-window-human-review-execution-sheet-20260930-a01/REVIEW-SHEET.md` 把 A05-2 原片 SHA 误写为 `25A13691259215848D77EAAB8AED9C0E281AF59A8EB126E5D726EC6FE73A9BC`；首次传输因此在**复制前**按 source SHA 门拒绝，目标文件尚不存在。旧失败回执位于 `D:/workspace/ck3_native_war_ai_promo_work/episode02-five-raw-onedrive-transfer-20260930-a01/file-02-A05-2/failure.json`，勘误原件为同根 `ERRATA-A05-2-SHA.md`。下面表格和后文的正确 SHA 是 `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC`；它与既有 pending source manifest、PTS JSON 和原片实测一致。外置 v2 原件 SHA-256 `B2184BD18C40A26F6870A37EB6113C0D8FEB046044BFBA6156A6449C7268D339`；五份来源清单/PTS 与七窗时间码的只读交叉核验为 PASS。**两版原件及 RED 均保留，本文不是旧件覆盖。**

上传目标仅为下列五个视频本身；本执行单与回执均不放入 OneDrive。

| 顺序／组 | OneDrive 固定目录中的目标文件名 | 既有原片 bytes / 正确 SHA-256 | 1× 整片时长 |
| --- | --- | --- | --- |
| 1／A1 | e2-09-terminal-a01.mkv | 951186809 / C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B | 10:00.000 |
| 2／A2 | e2-09-terminal-a02.mkv | 840210967 / 25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC | 10:00.000 |
| 3／B1 | e2-04-d05.mkv | 2459812208 / 950D94FE20A937806A1A8976160D66D8BF04D5DE3C7CD85A67D7DF5ACE45D3C9 | 09:59.966 |
| 4／B2 | e2_04_d06_afterstate.mkv | 917883172 / 44EC9EE794658C13B6CBAE5B13D9A0105CC0C4DB04F7918D51FEDB4DA43C15D9 | 04:00.000 |
| 5／C | e2-05-d26.mkv | 2451530594 / 7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F | 10:00.000 |

整片 1× 总下限 43:59.966；七窗精确 PTS、观察疑点、空白签署栏见下文。目前真人全片审阅、首末帧人审与 clean span 仍均为零。

## 开始前：完整性与播放规则

基准目录 W = D:/workspace/ck3_native_war_ai_promo_work/。以表内绝对 raw 路径打开播放器，读回所选路径、大小、首末媒体时间，与对应 source-manifest.json 和冻结 SHA 身份核对。既有 pending 清单是在先前 prepare 时逐字节哈希 raw、FFprobe、marks 与证据所得；路径/大小仅作快速排错，不能证明字节仍相同。若身份有疑，停止，在受管 CK3 屏幕空闲时另做 SHA 复核。后续正式 package 会再次校验字节，但不替代审片员确认自己看的是哪条原片。

五条 raw 每条从首帧到末帧按 1× 完整看，不能只跳看七个导航窗。记录暂停与准确恢复位置，不快进略过未看区域。墙钟 mark 不是媒体 PTS。完整原片审阅与窗口缩窗是两项不同记录：看清每段中间画面、HUD、日期、身份、加载、遮挡、静止等待、外来叠层；再从完整 FFprobe 真 PTS 选择实际首末帧。内部 PTS 最大 gap 必须 ≤0.2 秒，最终首末 PNG 仍须真人亲看。机器导航端点只是定位材料。

| 组 | 原片绝对路径；既有 bytes / SHA-256 | pending source-manifest.json；既有 SHA-256 | 整片播放范围；时长 |
| --- | --- | --- | --- |
| A1 | D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a01/raw/e2-09-terminal-a01.mkv；951186809 / C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B | W/episode02-a05-a01-d27d28-adapter-pending-20260929-a01/source-manifest.json；E066640F592440003CB46260EA0C04DA2F84BDB735FC44C2AC054672D876572A | 首帧 PTS 0.000 至末帧 599.967；容器 600.000 秒 |
| A2 | D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a02/raw/e2-09-terminal-a02.mkv；840210967 / 25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC | W/episode02-a05-a02-d28d29-adapter-pending-20260929-a01/source-manifest.json；8115562E7924F5C6C6A2E76AB886563AB16FD1188449930D72484716FD2AC043 | 从 0 至 599.967 末帧，约 600.000 秒；三窗共用这一次整片观看 |
| B1 | D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-live-20260929-a07/recording-e2-04-d05-a07/raw/e2-04-d05.mkv；2459812208 / 950D94FE20A937806A1A8976160D66D8BF04D5DE3C7CD85A67D7DF5ACE45D3C9 | W/episode02-k04-a07-adapter-pending-20260929-a01/source-manifest.json；67D2A09CE07B7195597C717F4371858CAD768E8B9E3871CD18465A6E5406D446 | 0.000 至 599.933 末帧，约 599.966 秒；411.167→413.300 缺帧不可跨 |
| B2 | D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-v3-live-20260929-a08-a02/recording-d06-afterstate-a01/raw/e2_04_d06_afterstate.mkv；917883172 / 44EC9EE794658C13B6CBAE5B13D9A0105CC0C4DB04F7918D51FEDB4DA43C15D9 | W/episode02-k04-a08-d06-panel-adapter-pending-20260929-a01/source-manifest.json；856631970989D82932400C66E6C4977A6FF692F52DE0E15458C07DFCD46A1705 | 0.000 至 239.967 末帧，约 240.000 秒；0→8.133 原片缺帧 RED |
| C | D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/raw/e2-05-d26.mkv；2451530594 / 7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F | W/episode02-k05-a02-d26-adapter-pending-20260929-a01/source-manifest.json；EB987A4BF8C15B5BF0E93380BA22FE5F4D33E6355CFD07617BD6786623319F05 | 0.000 至 599.967 末帧，约 600.000 秒 |

五条原片原速下限 43:59.966。A 组两条 20:00，含笔记建议 30–40 分钟；B 组两条 13:59.966，建议 20–30 分钟；C 组一条 10:00，建议 15–20 分钟。独立真人与不占用受管 CK3 屏幕的合法环境可以三组并行；只有一人或一个屏幕则串行。时间预算不表示已观看。

导航用五份已核 PTS JSON 均在 W/episode02-seven-window-review-plan-20260930-a01/，按 A1、A2、B1、B2、C 顺序为 a05-a01-pts.json SHA 6B047387415616931E3560C7460A91340566A7588327A630CD1F2B72C1B3C256、a05-a02-pts.json SHA CE8A7C86A76B4F880ADEB325A955891349786A471D2E31169EBE05C06EBFEFE6、k04-a07-pts.json SHA 7E9F9F11C157B7B5570603993CAF7664FD104D29D3911D2018875DB5EA7DA402、k04-a08-pts.json SHA B59E960C76AE9208AE65DFE57771723C0278AAD8CB7039E5A411E79F453A656D、k05-a02-pts.json SHA D7C9296D37D437623ECFD3C2C116B72E949BA7F243EA40302C98F00A8DF7A9BC。它们绑定上述 pending 清单与整份 FFprobe，但没有重新哈希 raw；只作媒体 PTS 导航。

## 七窗逐段检查表

下表端点目录相对 W，每目录已有 frame.png 和 extraction-receipt.json。14 PNG、14 receipt 的精确 SHA 与 decoded index 已列在 #669 的 seven-window-endpoint-readback-20260930.md 并逐件回核 28/28；总报告 SHA 在本单结尾。若实际选中的端点不同，必须另开新外置抽帧 attempt，再由真人看新的两帧；不得把旧 PNG 改名充新端点。

| 组／窗口 | 机器导航首末 PTS / index；搜索长度 | 现有端点目录：begin → end | 真人需看清的事实与疑点 |
| --- | --- | --- | --- |
| A1 d27→28 | 350.000000 / 9887 → 450.000000 / 12679；100.000 秒 | episode02-a05-a01-d27d28-endpoints-20260930-a01/begin/ → end/ | 350 秒孤帧仅地图，450 秒已见战败、824 对 4575、撤退/追击。找面板真正打开、日期/身份与逐团数；A1→A2 是不同 recorder，须可见切口。 |
| A2 d28→29 | 60.000000 / 1648 → 170.000000 / 4726；110.000 秒 | episode02-a05-a02-d28d29-endpoints-machine-20260930-a02/begin-60/ → end-170/ | 暂停战败/追击面板，侧总数约 824→803；看连续动作和 HUD。早期战败文字不能当 d32 writer 或 −50 证据。 |
| A2 d30 | 200.000000 / 5558 → 250.000000 / 6966；50.000 秒 | episode02-a05-a02-d30-endpoints-20260930-a01/begin/ → end/ | 两端暂停 Jan 2、782 对 4575；核中间有无真实变化、逐团 soft/hard 与面板总数的统计口径。 |
| A2 d31 | 300.000000 / 8165 → 349.967000 / 9573；49.967 秒 | episode02-a05-a02-d31-endpoints-20260930-a01/begin/ → end/ | 两端暂停 Jan 3、761 对 4575；不能跨 d30→d31 间 271.267→278.833 的 7.566 秒缺帧。旁白原句“与此同时，三天可比兵团的当前战斗人数保持不变。”与大面板 824→803→782→761 的口径张力待同源账核实，不能凭孤帧断定稿错。 |
| B1 K04-a07 d05 | 0.000000 / 0 → 411.167000 / 9371；411.167 秒 | episode02-k04-machine-endpoints-20260930-a01/k04-a07-begin-a01/ → k04-a07-end-a01/ | 首孤帧有 HUD，尾端 11 人悬浮卡挡面板；核整个 raw 起点与无遮挡实际入出点。411.167→413.300 缺 2.133 秒；该 run 的 d06 mark 是 trace，不是 battle-control。 |
| B2 K04-a08 d06 panel | 8.133000 / 1 → 239.967000 / 4804；231.834 秒 | episode02-k04-machine-endpoints-20260930-a01/k04-a08-begin-a01/ → k04-a08-end-a01/ | 全 raw 0→8.133 缺帧 RED 必须实记；尾端骑士悬浮卡挡面板。与 B1 独立冷载，须标切口；34333 有效勇武/团61 当前 V3 值仍 RED，不能从孤帧推 11→7。 |
| C K05-a02 d26 | 0.000000 / 0 → 210.000000 / 4460；210.000 秒 | episode02-k05-a02-d26-endpoints-20260930-a01/begin/ → end/ | 两端战斗面板 11 对 4590、海域 tooltip；核首帧 HUD/加载、名单和可用动作。d27 post-snapshot 不是 battle-control，名单 mark control=null；死亡/selector 后态须新 capture。 |

A05-2 全 raw 另有 37.933→38.700（0.767 秒）、179.600→180.067（0.467 秒）、271.267→278.833（7.566 秒）缺帧。K04-a08 的 0→8.133 是全片 RED，即使候选区间内部 PTS 连续也不得抹去。K04-a07 端点后 411.167→413.300 不能跨。K05 d26 真 control 不能自动延伸到 d27。机器孤帧里长时间暂停/遮挡是否影响可用长度，必须由真人完整审阅决定。

## 真人填写空栏：每条 raw 一份，每个最终 span 另附一份

本单为冻结的空白模板；请将以下栏位复制到新的个人审阅记录，A1、A2、B1、B2、C 各一份，不改写本单或旧 run。A2 的三个窗口可共用一份整片审阅记录，但要分别填写三份窗口决定。不得从机器回执自动填“是”。

- 组／raw ID：________；播放器回读原片绝对路径：________；观察到的文件 bytes：________
- source-manifest 路径与 SHA 核对：________；是否另做 contemporaneous raw SHA、时间与结论：________
- 审阅者真实姓名/组织 ID：________；播放器及版本：________；播放环境：________
- 完整 raw 首帧播放 UTC：________；末帧播放 UTC：________；实际速率：________
- 暂停、恢复、任何跳播的精确媒体位置：________；是否亲自无遗漏看完整 raw：[ ] 是 [ ] 否 [ ] 未知
- 原片起点 HUD/日期/身份实际可见情况与证据：________
- 全程加载/黑屏/非 CK3 画面/外来叠层/悬浮遮挡/停顿/断帧及位置：________
- 窗口 ID：________；实际连续首末 PTS/index：________；内部最大相邻 PTS gap：________
- 区间中日期、WarID/CombatID、人物、面板、动作与来源 control 的逐项观察：________
- 实际 begin PNG 路径/SHA、receipt 路径/SHA、本人看图 UTC：________
- 实际 end PNG 路径/SHA、receipt 路径/SHA、本人看图 UTC：________
- 选段判断：[ ] 接受候选进入机器门 [ ] 缩窗后再审 [ ] 拒绝 [ ] 未知；理由/未解疑点：________
- 需补拍的具体镜头及 native 门：________
- 本人确认上述出自实际观察而非机器报告转录，签名/ID：________；签署 UTC：________

合并人按五条 raw 的绝对路径、bytes、冻结 SHA 和五份 pending 清单 SHA 去重，逐条核实际真人完整 1×、实际端点人审时间、身份、各 gap 和错型 control 是否记录。K04-a08 原片缺帧、K05 d27 控制缺口等已知 RED 不因视觉记录而转绿。只有实际完成人审且各项真实通过后，才按 existing-capture-adapter-bundle.md 的精确 schema 另建 human-review.json，再在新外置目录 package、adapter、clean-span 审计；本单不是 human-review.json。最终 reel 与整片还需独立 1× 精确 SHA 签核。新 xar-promo run 前重查当时最新正式 Release、wheel SHA、解释器和帮助。

冻结来源：W/episode02-seven-window-machine-endpoints-20260930-a01/REPORT.md SHA-256 CD0D3C4D4BBD170172FB3A5C2C9F1ACBD2760EFADF5AB8B20B5E4141E7DE3CFC；#669 七窗人审计划和 14 端点哈希回读；三份 AI 孤帧预筛报告 SHA 分别 CE58E4B0460C7A246D166C846EE42106900CD468CBA9CF9C4A3B1DA1D55D12BA、D2ADE3E59EBBAB6A3572A5139ACCEED6B3BCE657CC3C39F9F9ED0B4C08A8A791、EE1FABBE22E6380012C9C1EB3EB74689E096BEABCB0E76E59666731BAB2F2BDE。
