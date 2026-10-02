# #451 第二期六章：原片 clean span 候选与缺口（只读）

2026-09-29，基于 #451 `85c627190` 已冻结的 recorder、逐帧 PTS、原尺寸抽帧、mark 和原生回执。此页未读取、解码或重新哈希 GB 原片，未占屏、启动 CK3 或覆盖旧报告；仅直接复看了现存 E2-04 d06 `t010.png` 和 E2-05 a02 PTS 233.000 原图。**已认证 clean span 为 0 秒，人工 1× 签核为 0。**下表的入出点是现有 FFprobe 原始帧上的机器搜片窗，不是已核准的剪辑端点；点位目视也不证明整个窗干净。所有 raw SHA-256 均引用当次 `recorder-final.json` 和已冻结的 PTS/来源报告，本轮没有重算媒体 SHA。

## 判级与精确来源

- `M`：只有封口/逐帧 PTS 搜片窗，区间画面内容尚未逐帧核对。
- `V`：区间内已有少数原尺寸截图目视，但截屏之间的画面、遮挡和正确入出点未知。
- `T`：相邻原始帧已目视确认某一可见变化；仅该变化具备帧级视觉定位。
- `R`：正式准入硬门为 RED；可继续保全和研究，不得计为正式可剪秒数。`V/R`、`T/R` 保留视觉发现，同时明确该后态的正式来源门未过。所有 `M/V/T` 也都仍待完整 1×、精确端点与 CK3 adapter/clean-span 审核。

| ID；完整 raw 相对 `D:/workspace/ck3_native_war_ai_promo_work/` 的路径 | 原片 SHA-256 | 精确来源与控制边界 |
| --- | --- | --- |
| `P-A01` `episode02-e2-02-03-live-20260928-a01/recording-e2-02-03-a01/raw/e2-pursuit-d27-d32.mkv` | `29D11C77ABCE92B79608F5E82E66D3949C08FE30BF6219626E526ECCA5698AAB` | F085 第 27 日源档/真实 sidecar 的**独立 A01 回放**；不能补成 A05 的连续媒体。 |
| `A05-1` `episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a01/raw/e2-09-terminal-a01.mkv` | `C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B` | F085 d27 save SHA `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3` / sidecar `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`；A05 会话第一段。 |
| `A05-2` 同根 `recording-e2-09-terminal-a02/raw/e2-09-terminal-a02.mkv` | `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC` | A05 会话第二段，**与第一段非连续**；第 32 日 writer 回执 SHA `3CAC1F8F89545C299A957EB49C1B8636BB9A14C2707680A458FA8104EF9B1782`。 |
| `K04-a07` `episode02-e2-04-d05-live-20260929-a07/recording-e2-04-d05-a07/raw/e2-04-d05.mkv` | `950D94FE20A937806A1A8976160D66D8BF04D5DE3C7CD85A67D7DF5ACE45D3C9` | attempt-010 d05 save `695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885`；**此 run 录到 d05→d06，但没有真实 d06 保存**。d05-before 真 battle-control SHA `3BC180231A4EB38DF2F7CB0111D816BB0E28689BEA7A62F7A1F3A1C93D8408E0`；d06-after mark 的 `control` 字段实际指向 private trace SHA `5D2DDED6A49E173418C9C93DF00FC5D832E1CE9303E76E665FEC3E5A548968B8`，不是后态 battle-control。 |
| `K04-a08-pre` `episode02-e2-04-d05-live-20260929-a08/recording-e2-04-d05-a08/raw/e2-04-d05.mkv` | `C44998E9FC9E6048C49F00DEECC9D9BA558281FFF1A0D6F51FCBBE0CFA96DE37` | 从同一 d05 源字节**重新运行**；这 600 秒 raw 只含 d05 前态，d05→d06 推进在录制停止后。a08 trace `E53502D300FC1FCE0807E5F239ED856A599C75DD886982C305FBC05665C14554`，后态真实 save 如下。 |
| `K04-a08-panel` `episode02-e2-04-d06-v3-live-20260929-a08-a02/recording-d06-afterstate-a01/raw/e2_04_d06_afterstate.mkv` | `44EC9EE794658C13B6CBAE5B13D9A0105CC0C4DB04F7918D51FEDB4DA43C15D9` | 从 a08 后存 d06 save `F05A48A0839E76DD05D053FACBA524405FD547DD0A6CA07396ADB8ABE42A0B5A` / sidecar `85C226E247AF4D32E246DCCF9F4C7323106D3A6BD0F12FCB883ABE843D3B785B` **独立冷载**；同帧 d06 battle-control SHA `5469D9F7F066B805581038E8D9735CF51C3616823E5CAAFEF390059E73983C19`。 |
| `K04-a08-list` 同根 `recording-d06-knight-list-a02/raw/e2_04_d06_knight_list.mkv` | `ED26DACABA0BF082663C0AB663273406D3CB38ADD8DE9D4417C487DCD0487C4B` | 与上一条同次 d06 冷载，独立第二条录制；该 recorder 的 `marks.jsonl` 只有 start/end，**没有 battle-control mark**。正式 capture 所需 `control` 须在本 recorder 的 `source-manifest.json.files`，不能借前一条 panel raw 的 control。 |
| `K05-a02` `episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/raw/e2-05-d26.mkv` | `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F` | attempt-010 d26 save `C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B` / receipt `78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C`；本 run d26→d27，不是 020/070/036 历史抽签。d26-before 有真 battle-control `D41E384CE022C261E15E3761980A0A78E26BA0B21C9FCF3F2393F062F03CEC1F`；d27-after 的 `control` 字段实际为 post-snapshot（`battle_control_snapshot_v1:null`），d27-player-knights 的 `control:null`。 |
| `J-A01` `episode02-e2-06-d11-live-20260928-a01/recording-e2-06-d11-a01/raw/e2-06-d11.mkv` | `501B4C2A8557DC2EBBE88FD0485A45265FDDC9BF8EF46F7A1E968F8EB51024C7` | attempt-004 d11 save `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953` / sidecar `DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5`；**marks 的 control=null 且该 run 从未发 battle-control**。 |

上述来源身份详见[镜头账](shot-list.md)、[四 raw a03 EDL](provisional-edl-four-raw-a03-20260929.md)、[a07](e2-04-a07-live-evidence-20260929.md)、[a08 d06](e2-04-a08-d06-coldload-media-boundary-20260929.md)、[E2-05 a02](e2-05-a02-adjacent-visual-transition-20260929.md)及[J-A01 审计](j-a01-old-raw-visual-audit-20260929.md)。

**逐轨 control 复核：**`P-A01` d27、`A05-1/2` 追击日、`K04-a07` d05、`K04-a08-pre` d05、`K04-a08-panel` d06、`K05-a02` d26 的 recorder marks 均引用真实 battle-control；这仅满足相应前态/日期的来源候选门，不证明完整画面已 clean。`K04-a07` d06、`K04-a08-list`、`K05-a02` d27 与 `J-A01` 的正式后态/名单控制缺失或类型不符，已在下表标 `R`。`A05-1` WarID 前图及 `A05-2` d32 mark 本身 `control:null`；同 recorder 其他日期的真 control 不自动补这两帧，正式使用须先按[reel capture 合同](reel-edit-production-contract-20260929.md)审其同源与控制用法。`marks.jsonl` 中字段名为 `control` 不保证其内容是 battle-control；`prepare_existing_capture_bundle.py` 仅从当次 recorder 固定原件和 mark 引用收集 `source-manifest.json.files`，不会从另一条 raw 借证。

## 六章搜片窗

| 章 / 候选 | 原片实际 PTS，秒 | 已见原生画面及边界 | 判级；还缺什么 |
| --- | ---: | --- | --- |
| 开场 `P-A01` | `30.000–120.000` | a03 的第 27 日地图/战斗上下文搜索窗；这是另一次 A01 回放，须明示来源。 | `M`；无逐帧内容/端点/1×。若开场要讲 A05 当前回放，需重新选 A05 画面并重排。 |
| 追击 `A05-1` | `350.000–450.000` | 第 27→28 日进入与 E2-02 起算搜索窗，a05 原生逐日 control 已有。 | `M`；端点、HUD 遮挡、日期切换和 control 对齐仍待逐帧。 |
| 追击 `A05-2` | `60.000–170.000`；`200.000–250.000`；`300.000–349.967` | 分别索引第 28→29、30、31 日的独立画面段。 | `M`；各段 1× 和真实内容；两条 raw 之间标可见切口。不可把 250–300 当一条连续窗。 |
| 骑士 E2-04 `K04-a07` d05 前态 | `0.000–411.167` 或 `413.300–599.933` 内待逐帧缩窗 | 2560×1440，d05-before 真 battle-control 与原尺寸截图 mark；墙钟 +172.542 s 不等于准确 PTS。 | `M`；相邻帧 `411.167→413.300` 缺 **2.133 s**，不得跨；待确认可用 d05 画面实际端点、无遮挡/1×。 |
| 骑士 E2-04 `K04-a07` d06 后态 | 同一两块 PTS 连续域内待逐帧缩窗；d06-after 墙钟 +459.990 s **不是 PTS** | 原生 trace 记录 `knight_maimed_by_enemy(34333,47032)`；d06 原图仅见 11 人未减员，没有 34333 有效勇武下降，也无 d06 save。 | **`M/R`**；d06-after 的 `control` 是 trace-finish 而非 battle-control，不能用 d05 前态控制证明 d06 后态。需要新录含真正 d06 同帧 control 的后态镜头，或先审定明确允许该来源的正式合同。 |
| 骑士 E2-04 `K04-a08-pre` | 原片首末 `0.000–599.933`，**尚无全帧断档审计** | 2560×1440，d05-before mark 墙钟 +57.744 s；录制期间没有 d05→d06 推进。 | `M`；该全长仅媒体边界，不是连续 clean 候选；须先补全量 PTS 与逐帧内容。不能把 a08 后态接成未标注的同一连续推进。 |
| 骑士 E2-04 `K04-a08-panel` | `8.133–239.967` | 独立冷载的 d06 战斗面板，battle-panel mark 约开录后 208 s **仅墙钟导航**。 | `M`；首帧 `0.000→8.133` 断 **8.133 s**，整片 PTS 审计 `RED_PRESERVED`；窗内尚无精确 PTS 的原尺寸截图、无遮挡/1× 判定。V3 当前数值查询 RED。 |
| 骑士 E2-04 `K04-a08-list` | `0.000–89.967` | 2560×1440 全帧 PTS 连续；从此 raw 请求 seek 10 s 的原图 SHA `D20B4F3D1B99126C6D985873018E2FEBD1467D7162EC4074722E898CD51369B2`，可读暂停 1066-12-09、11 人列表及第 5 行 **7 勇武**。 | **`V/R`**；视觉研究成立，但本 recorder 的 source manifest 无 control 原件，正式 capture RED。须新录带同 recorder 原生 battle-control mark 的名单，或先审定新的正式合同；不能借 panel raw。**seek 10 不等于该帧精确 PTS**。像素无 CharacterID；`34333↔第 5 行` 是名单对齐推断，不称“11→7 降了 4 点”或团 61 攻防已验。 |
| 骑士 E2-05 `K05-a02` | **相邻帧** `232.533–232.567`；通知可读点 `233.000`；后续名单点 `385.000` 等 | 冻结 frame 4918/4919 原图实见同日骑士 **11→10**、兵数 11/4590→2/4573；后一帧通知刚淡入且文字不可读。PTS 233.000 原图才可读“图尔吉塞…被阿姆鲁…击杀”，385 等稀疏图为 d27 十人列表。 | **`T/V/R`**；`T/V` 只评视觉定位，d27 后态 battle-control 仍 RED。d27-after 所谓 `control` 是 post-snapshot 且无 battle-control payload，名单 mark 为 null；不能借 d26 前态控制。先审 `232.233–234.033` 实际逐帧窗口；正式后态须新录同帧 control 或审定新合同。另缺本 run selector ID、死亡状态和 1×；trace event 行不自动补齐死亡。 |
| 增援 E2-06/07 `J-A01` | `200.000–255.000`；`350.000–410.000` | 第一窗稀疏图为 d11，893/1603、海上军旗 2570；第二窗 **355 s 请求 seek 仍为 d11，365 s 已是 d12**，827/4106、军旗切换后 1058。seek 整数不是准确帧 PTS。下半战斗 UI 裁切。 | **`R`**：同 run battle-control 缺失，不能正式入片。即使补控制回执已不可能追溯当次同帧；需要新的 d11 受管 attempt。旧 raw 只可按清楚标记的历史/探索素材研究，不能以画面反推 ArmyID 22、13 团或战宽可见。 |
| 终局 E2-08/09 `A05-1` | `245.000–269.967` | WarID 4 前态 0% 搜片窗；mark 墙钟 +256.988 s 的原图可见完整战争面板，附近 PTS 256.967 **仅导航**。 | `V`；该 mark `control:null`，但同 recorder 稍后有真实 d27 battle-control；正式装包仍须验证同日源绑定和允许的 control 用法，不能称此 mark 自带 control。另需真实无遮挡端点、1×。 |
| 终局 E2-08/09 `A05-2` | `385.000–500.000` | d32 writer/WarID 4 后态搜片窗；原生 writer 证 `normal_result`、winner side0、Army18 败退、战斗 row −50。mark 附近 PTS 397.333/487.700 仅导航；后态原图可读总战分/战斗项 −50%，但无关事件弹窗遮上半面板。 | `V` 且**后态控制待审**：d32 writer/war4-after 两条 mark 的 `control:null`，`report` 为 terminal writer；同 recorder d28–31 的 battle-control 不能自动证明 d32。正式装包需确认合同是否接受同 run 先前 control 加 d32 writer，若要求 d32 同帧 battle-control 则新录/新合同；另逐帧找无遮挡后态和真实 cut。 |
| 收束 | 暂无独立 raw 搜片窗 | 预留从前章**未来审核通过**的 A05 镜头作 95 s 有来源标签回顾。 | `M`；当前 0 s。若不复用另需 95 s 新画面；重复回顾不能计入不重复 raw 存量。 |

`A05-2` 的完整冻结 PTS 审计 SHA `6FDE20151A6E51EC760BB6CFFAA0B30DC21413363A74149100D949681FC16391`：相邻帧缺口 `37.933→38.700`、`179.600→180.067`、`271.267→278.833` 分别 0.767、0.467、7.566 s；任何新段均不能跨。`J-A01` 有 16,691 帧、0–599.967 s，机器无 >0.2 s 间隙，但这只过 PTS 门。E2-05 a02 的 12,656 帧、0–599.967 s 同样只有 PTS 连续；PTS 审计 SHA `A3A9243E48D987134664F1A0E951938E17A0CA36D86B50750AFAA6CA4BD8645A`。E2-04 d06 两条 PTS 审计 SHA 分别 `B9196B7B2F3F4338CAB9DD5246BBDDEC34850578E70F851BA4974D8679D4EC75` / `831E66A173E563C888635980A9CCB94B8EB7A7E19BACED02D55DE534ED95EFB9`。

## 缺口与最短下一步

六章目标 `1790.000 s`，卡独读暂留 `182.000 s`，画面需求 `1608.000 s`。四 raw a03 九窗在**全过门的乐观假设**下，计入收束 95 s 重复回顾，最多 `735.967 s`；条件性缺 `872.033 s`，并非当前已可剪时长。新 E2-05 a02 即使将来满足全部视觉/来源门，也最多抵骑士章 `360.000 s`，不能把 600 s 容器时长直接扣掉。当前经人工认证可剪量仍为 **0 s**。

| 章 | 乐观画面预算缺口 | 本轮结论与补拍门 |
| --- | ---: | --- |
| 开场 / 追击 | 账面各 0 s | 已有搜索面积，不等于实片。先审 `P-A01` 独立标签和 A05 日期/控制/遮挡；任何淘汰秒数重新入缺口。 |
| 骑士 E2-04/05 | 原 a03 为 360 s；新 K04/K05 素材尚未计入 | 先审 K05 `232.533→233.000` 的可见变化及 d27 名单；K04-a08 的 d05 与 d06 有真实 save 关联但跨冷载，需清楚切口。E2-04 34333 当前有效勇武、团61 数值和 E2-05 selector/death 如继续作为具体口播，必须补原生同帧读数；若取得不到，删改对应数字/死亡因果话术。 |
| **增援 E2-06/07** | **346.000 s**（461 需求 − J-A01 115 机器窗） | 旧 J-A01 同 run control 硬缺、面板裁切、现有画面大段静态，115 s 本身也不可计入正式画面；因此 **346 s 是过分乐观的账面下界**。新 d11 attempt 需同帧 battle-control、原图完整字段、Army22 接近/入场及一次 d11→d12 原速录制；若战宽/逐团 UI 不可见，以精确标注的原生 trace 计算板呈现。 |
| **终局 E2-08/09** | **166.033 s**（306 需求 − A05 139.967 机器窗） | 优先有界审 A05-2 `350–385`、`500–599.967` 和 A05-1 `200–245`、`269.967–350` 的**真实帧端点**，这些整数只是导航；A05-2 近 d32 的两段额外面积至多 134.967 s，即使全部通过仍差 31.066 s，须另找 A05-1 前态、重排章结构或补拍。若无无遮挡后态/败退画面，按 F085 精确源另起 attempt，并重新绑定新 writer，不能借 A05 数字。 |
| 收束 | 条件性 0 s；不用回顾则 95 s | 只从最终通过 1× 的前章 span 回顾，显式标来源；不能提前预支。 |

审片者下一步先针对上表的精确机器窗取首末实际帧和原尺寸画面，逐段 1× 记录日期、HUD、弹窗、停顿和控制绑定；每个要入剪的 raw 再用独立 append-only CK3 adapter `report`/timeline/evidence index 建立 clean-span 原件，最终 reel 另做人审和精确 SHA 签核。**不要把本页判级、PTS 连续、卡片/字幕审核或录制完成，升级成成片/交付 GREEN。**
