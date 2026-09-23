# CASE-W：玩家宣战之后，原版敌军集结、路线与实际移动（2026-09-23）

本轮在 CK3 **1.19.0.6、enabled_mods=[]** 的 R0005 中，观察到同一敌军公开 CUnit **22 / owner32231** 从 `gathering` 进入带路线的 `moving` 状态，随后当前位置由 **4598 变为 4599**。这是玩家发起战争后的一段原版 NPC 行为记录；它证明已发布的状态变化，没有把选目标的候选评分、调度原因和行动结果整条因果链都测到。

原准备合同仍保留：[观察计划](research-plans/war-film-case-w-20260923-r1/plan.json)。本页对应独立的[结果合同](research-plans/war-film-case-w-result-20260923-r1/plan.json)、[结果图](research-plans/war-film-case-w-result-20260923-r1/graph.md)、[冻结读回](research-plans/war-film-case-w-result-20260923-r1/readback.json)与[验证收据](research-plans/war-film-case-w-result-20260923-r1/validation.json)。新结果没有回填、覆盖旧计划的 pending 状态。

## 会话和证据边界

| 项目 | 实测绑定 |
| --- | --- |
| 正式编号 | `desktop-3fevhd2-1c74096080--vanilla--R0005` |
| CK3 PID / connection generation | `32356 / 1` |
| episode / 玩家 | `native-29829-fcaa3906d404 / CharacterID29829` |
| EXE SHA-256 | `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86` |
| 战争 | `WarID4`，玩家攻击方，主要对手31549，目标省份2638；操作意图中的 targeted TitleID2111 |
| 起点 / 末点 | `date_raw53144328 → 53144784`，19个游戏日，每日24 date_raw单位 |
| 末次暂停帧 | `snapshot_id=native:44 / public revision45 / native revision44 / paused=true` |
| 取样范围 | 7轮时间推进；离线去重后13个暂停发布帧；只提取正式响应 `w001..w131` |

`army_id` 在这里是正式公开投影的 **CUnit ID**，不把它默认等同内部 CArmy ID。专门的军力查询另有 `native_carmy_id`。跨样本只跟踪同一完整公开 ID 和 owner，不在对象消失、拆分或合并之后猜继任对象。

实机原件根目录为 `D:/workspace/ck3_war_film_research_20260923/`。下文的 `case-w-r1/`、`capture-live-live-r5/`、`case-w-r1-recording/` 均相对此根目录；冻结读回的 `sources` 保存原件绝对路径、字节数和 SHA-256。所有数据提取均只读既有文件；本包没有启动、附加、注入或控制 CK3。

## 先保留失败，再说明后来实际读到了什么

R5 原始 `capture-live-live-r5/hot-failure-state.json` 在 `2026-09-22T21:50:53.662050Z` 记录 `Loaded checkpoint actor/date differs from saved native receipt`。当时 snapshot 的 `played_character` 为 null，日期已是53144328。它仍是原始 RED，不能由后来出现 HUD 倒改为成功，也不能仅凭这个快照判定唯一故障原因。

后来 root 实际查看 `desktop-r10/desktop.png` 的暂停 Robert 地图 HUD；`case-w-r1/preparation.json` 和录像的 `recording-precondition.json` 记录这次查看，并以新正式读回绑定当前 actor/date。截图为5,209,007 bytes，SHA-256 `0627aa9614cb09fa3d453d9f62151e5800a84b8c4dce1d537564ad0aed890762`。这只说明该时间点确已到 HUD，不是本页作者重新执行了人工影片审阅。

`w006-inspect_save_artifacts_v1.json` 因服务未配置 artifact inspector 返回不可用，仍保留该 RED。当前宣战前保存的 `case-w-r1/pre-declaration.ck3` 实际文件为 **50,501,715 bytes**，SHA-256 **`a9c5d1c4b7646a956894bcbf22eaa2150dce9381531734f8fd944d93310b541c`**；准备收据另记实际文件读回、归档复制及 hash。文件落地成立，不把 inspector 说成通过。

R5 加载来源是 R4 `robert-input-case-r1/day-zero.ck3`（50,502,569 bytes，SHA-256 `a450f37ff62ea0375b9ae2f6549aa5a14baa9940fc57fa6f97f912f1c76447f8`），其复制记录在 `checkpoint-copy.json`。旧 R4 的 episode/revision 是来源身份，不能代替 R5 当前绑定；宣战前新存档与旧 seed 的不同 hash 也不应混写。

## 战争入口是操作员干预

操作员以当前合法 token 宣战，正式读回 War4；随后操作员升起玩家军队，并在第7日以后对玩家 U18 提交前往2638的移动命令。对应 `declaration-intent/result.json`、`raise-intent/result.json`、`move-intent/result.json` 与正式响应 w014、w018、w067。这些是明确记录的干预，不是 NPC 自然宣战、AI 自动集结我军或 AI 给我军下令的证据。以下敌军行均 `controllable=false`，属于同一 War4 的 enemy 列表。

本轮宣战前 `assessment-result.json` 绑定 **public5/native4/date53144328**，target/effective 都是31549：

| 原生字段 | raw | Q100000 展示 |
| --- | ---: | ---: |
| actor base / total | 3350000000 / 3350000000 | 33500 / 33500 |
| actor network contribution | 0 | 0 |
| target base / pre-adjustment / total | 1334000000 / 1334000000 / 1334000000 | 13340 / 13340 / 13340 |
| target network contribution / adjustment delta | 0 / 0 | 0 / 0 |
| actual power ratio | 39820 | 0.39820 |
| distance | 0 | 0 |

这些军力是原生估值，**不是兵数或胜率**。R4 CASE-R 的 actor数值不能抄进本轮：R4实际 actor为37860，本轮为33500；此处记录变化，不解释其未测原因。双方 network贡献为0，后面又观察到多个敌军owner；这不证明盟友为何加入，也不证明这里的 network 字段应等同后来所有参战军队的总和。

## 同一敌军从集结到路线再到位置改变

| 第几日 / date_raw | public / native | 同一 War4 的敌军公开变化 | 主要原件 |
| --- | --- | --- | --- |
| 1 / 53144352 | 12 / 11 | U16777221(owner31549)在2638、U16777231(owner32725)在4578，均gathering、空路线。首次看到公开行不等于已抓到原生raise命令。 | advance-01；enemy-observation-01 |
| 4 / 53144424 | 17 / 16 | U16777221转regular；U16777231为moving，仍在4578，目标2633，剩余路线8648→1033→1032→2633。U22(owner32231)出现在4598，gathering。 | advance-02；enemy-observation-02 |
| 7 / 53144496 | 22 / 21 | U22仍gathering；新增公开敌军U27(owner34320)在2646、U28(owner34474)在4552，均gathering。 | advance-03 |
| 10 / 53144568 | 29 / 28 | U22为moving，仍在4598，目标2619，剩余路线以4599开头；U27为moving，目标2627。 | advance-04 |
| 13 / 53144640 | 35 / 34 | U28也为moving，目标2628。至此这些军队已有路线，但所列敌军当前位置尚未改变。 | advance-05 |
| 16 / 53144712 | 40 / 39 | U22仍在4598，目标改为2633，剩余路线4599→4574→8648→1033→1032→2633。U16777231、U27、U28的目标字段变为2638，当前位置仍未改变。 | advance-06 |
| 19 / 53144784 | 45 / 44 | **同一U22由4598到4599**；剩余路线变成4574→8648→1033→1032→2633，前一帧的首省4599被移除。 | advance-07；enemy-observation-03；w126/128/131 |

最小成立链条是：**同一 U22/owner32231 → gathering → moving且有已提交路线 → 后续实际当前位置变化**。到第13日只有路线时不提前叫作移动进展；第16→19日的位置变化和剩余路线缩短共同支持本次进展。采样间隔内发生的中间时刻、各次目标重算的理由、候选分数和优先级分支没有被这些字段揭示。

第10日 U22 的完整剩余路线为 `4599,4574,8648,1033,1032,8645,2612,2616,2617,2618,2619`。第16日目标和路线都改变；这说明提交给执行端的路径发生改变，不能独凭路径反推该时刻是某个进攻、围城或协助目标评分胜出。

共观察到5个敌军owner：31549、32231、32725、34320、34474。这里是 **enemy rows 的owner集合**，不是完整参战角色网络或招盟过程。观察期内这些样本未显示实际战斗，末次 War4 分数仍0、目标未被占领；不以此推断AI拒绝交战。

## 兵数与 AI 估值是不同读数

末次 `enemy-observation-03.json` / w129 的专门军力查询与末次暂停 snapshot 同帧；snapshot 的 `soldiers` 仍为null，以下兵数来自军力查询，不能把null自动填成0：

| public CUnit / owner | regiment count | current / max soldiers | AI base raw | AI base ÷100000 |
| --- | ---: | ---: | ---: | ---: |
| 16777221 / 31549 | 6 | 330 / 330 | 1334000000 | 13340 |
| 16777231 / 32725 | 15 | 1172 / 1172 | 3304000000 | 33040 |
| 22 / 32231 | 13 | 2570 / 2570 | 7364000000 | 73640 |
| 27 / 34320 | 6 | 511 / 511 | 1754000000 | 17540 |
| 28 / 34474 | 5 | 1058 / 1058 | 2732000000 | 27320 |

第1日军力查询对当时两支gathering军队返回0个regiment、current/max均0；第4日分别已为330和1172。这是各次投影中的读数，不能据此声称知道每日招募、补员或集結完成的所有内部步骤。

## 支援查询有一次 available，仍有字段冲突

| 样本 | 原始结果 | 能说明什么 |
| --- | --- | --- |
| 第1日，U16777221 | typed unavailable：`subunit_backlink_mismatch` | 此次查询未取得有效窄域结果；不是求援失败或没有求援意愿。 |
| 第4日，U16777231 | typed unavailable：`route_timeline_unavailable` | 时间路线前提不满足；不能补出ETA或决定分支。 |
| 第19日，U22 | `available / ready=true / query_sequence3`，coordinator3 | 取到一次窄域读回；并非请求→分配→进战的连续证据。 |

末次 `enemy-observation-03.json` / w130 显示 `asking_for_help=false`、`assigned_to_help=false`、`asking_changed_last_evaluation=false`，assignment target为null、provenance为none，active combat为null，contact为not_applicable；route arrival dates是返回的时间线，不是这些未来位置已经到达。未观察到0.66/0.75阈值的跨越或请求到分配的行为序列。

**必须保留的同帧差异：** 在同一 public45/native44/date53144784，普通 snapshot 的 U22 `move_target_province_id=2633`，窄域结果的 `route.move_target_province_id=4598`；两者当前位置都为4599，剩余路线都为 `[4574,8648,1033,1032,2633]`。`ready=true` 不会消除这项矛盾，本结果未选一边作为已裁决的目标语义。

最小后续研究是对这两个投影的目标字段reader/来源做精确静态核对，区分写错字段、不同对象或不同语义；需要新观察时再另立合同。当前不把冲突解释成AI改主意，也不把普通援军机制包装成玩家支援。

## 录像已保存，尚不等于镜头已通过

`case-w-r1-recording/recording-result.json` 记录录制正常退出和probe退出码均0：

| 项目 | 记录 |
| --- | --- |
| raw | `D:/workspace/ck3_war_film_research_20260923/case-w-r1-recording/gameplay.mkv` |
| bytes / SHA-256 | 1440131934 / `b047268ca6a1e5478624a8991bcce74ddf549965bace92143417367726ecf885` |
| ffprobe | Matroska、H.264、2560×1440、397.663秒、yuv420p |
| 帧率字段 | header的r_frame_rate和avg_frame_rate均30/1；本包没有逐帧PTS/实际CFR审计，不能据此宣称CFR30素材已验 |
| 现场与审阅 | 回执foreground_always_ck3=true；clean_span_review=pending；native_ai_causality_proven=false |

录像可作为本局地图及战争环境的真实素材候选；本页没有把任一暂停读回绑定到精确视频帧，也没有产生人工1×签核。操作标记、可用干净片段、媒体规范化和镜头剪辑由后续制作包另验，必须保留原raw；不能只凭容器帧率字段套用严格CFR导入。

观察于 **2026-09-22T22:03:23.643654Z** 达到主目标后停止，未进入可选contact；录像回执时间为22:03:25.736102Z。录制后的 w131（22:04:16.082392Z）仍为相同末次暂停帧。停止的是CASE-W观察和本段录制，**不是声明CK3进程退出**。之后的存档、动作或CASE-C必须另立证据边界，本包排除w131以后的正式响应。

## 提取与验证

新增只读提取器 [`tools/war_film_case_w_readback.py`](../../tools/war_film_case_w_readback.py) 校验同一session身份和paused/map条件、查询revision绑定、同帧军队投影一致性，并分别输出公开行出现、状态变化、路线变化和实际省份变化；同时保留两种投影之间的未解字段差异。只读JSON，不联系游戏，也不重发任何原生命令。

一次聚焦验证：[`tools/test_war_film_case_w_readback.py`](../../tools/test_war_film_case_w_readback.py) **5测试通过**；实际离线提取exit0，13个去重暂停帧、20个敌军变化事件。合成测试覆盖“只有route不代表progress”、同一对象实际推进、偏离旧route不冒充沿线前进、ID/owner不一致拒绝比较、首次moving行不伪造之前进展。它们不测试游戏语义。

本次显式解释器为 `C:/Users/1/AppData/Local/Python/pythoncore-3.14-64/python.exe`，仅用标准库；实际argv/stdout/stderr在外置 `case-w-readback-extract-r1/validation.json` 及同目录文件，仓库[验证收据](research-plans/war-film-case-w-result-20260923-r1/validation.json)保存其副本与相关文件SHA。重提取必须改用新的output-dir，不能覆盖本次结果；完整原始argv在验证收据中。

```text
py tools/test_war_film_case_w_readback.py -v
py tools/native_research_plan.py check docs/ck3-native-ai/research-plans/war-film-case-w-result-20260923-r1/plan.json
```

结果plan的check只验证记录结构和所引用文件hash，不验证原生语义，也不执行新实机。该图里的live-confirmed边仅指这次明示的公开观察，不能换算为CK3战争AI全树覆盖率。

## 后续媒体整理（2026-09-23）

上文“镜头待审”描述的是本结果读回冻结时的状态。随后对同一原始录像做了逐帧 PTS 探测：14,873 个实际帧，最后 PTS 397.63 秒，最大相邻间隔 0.063 秒，属于可按原始时间采样的 VFR 素材，不称为 CFR30。探测原件为 `case-w-r1-frame-probe/frame-timestamps.json`，SHA-256 `651ed93cb3d2d409a2aededf3c61637115a76f4ddac832c4677a02273fc46ae8`。

从真实 PTS 5.013 秒与 389.988 秒抽取的两张画面已由 root 查看：首帧是暂停中的意大利南部 CK3 地图、Robert 头像及原生 HUD；末帧是暂停中的西西里地形图、敌军旗帜、玩家军队面板和路线。审图原件为 `case-w-frames-r1/root-review.json`。只读动态封装结果 `case-w-bundle-r1/report.json` 为 **GREEN**，表示原始视频、首尾画面、同会话正式读回和有界推进记录达到该 producer 的导入合同；原始视频 SHA-256 仍为 `b047268ca6a1e5478624a8991bcce74ddf549965bace92143417367726ecf885`。它没有做逐帧人工观看，也没有把 query 时间绑定到精确视频帧；`native_ai_causality_verified`、`human_1x_review_performed`、`signoff_granted` 均为 false。任何成片仍须单独审阅。
