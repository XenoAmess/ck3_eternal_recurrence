# CK3 Autonomous Agent — Full Capability Showcase / CK3 自动游玩智能体全能力展示

状态：**2026-08 月报 canonical 成片已通过字幕安全区、媒体与内容抽检。**

原始脚本目标 `16:50`；为覆盖完整 21 项能力与新增 fresh 实机素材，最终展开为 27 个 compositor chapter、约 `20:28`。
画幅：`2560×1440`；目标帧率：`30 fps`；编码：H.264 `yuv420p` + AAC stereo。英语是唯一旁白语言和主要视觉层级，
简体中文必须作为画面内字幕及副标题同步出现。

canonical 成片路径：

```text
artifacts/demos/2026-08-27/ck3-autonomous-agent-2026-08-monthly-report-bilingual-20260827.mp4
```

最终媒体规格、字节数、SHA-256 与抽检结果统一登记在
[`2026-08 月报`](../monthly/2026-08.md)。本 storyboard 自身是成片 evidence source，因此不在这里反向嵌入成片哈希，
避免形成自引用哈希环。

本片的目的不是宣称智能体已经会玩 CK3 的全部内容，而是把当前已经取得的能力、证据等级和未完成边界一次性展示清楚。
任何没有真实 production OODA 支撑的内容都必须显示较低等级徽章。

## 画面与证据合同

### 固定分类徽章

| Badge / 徽章 | 建议颜色 | 画面含义 |
|---|---|---|
| `PRODUCTION-LIVE LOOP / 生产实机闭环` | green | 真实 CK3 中完成观察、动作、后置验证；持续能力通常还含 checkpoint 冷恢复。 |
| `PRODUCTION-LIVE PRIMITIVE / 生产实机原语` | blue | 真实 paused production frame 已验证，但只是完整策略的一部分。 |
| `FIXTURE-LIVE / 夹具实机` | amber | fixture definition 配 production native bridge；不是 stock gameplay 覆盖。 |
| `IMPLEMENTED / 已实现` | violet | 代码路径存在，只有部分结果或历史实机，尚无完整 production loop。 |
| `VISUAL-NARROW ARCHIVE / 固定场景视觉档案` | gray | 固定 1066 Robert 场景的历史视觉回归；可能使用 OCR、键鼠、快捷键或坐标。 |
| `DEFERRED / 暂缓` | dark red outline | 所有者明确暂缓或当前没有施工；不是已完成。 |

章节标题与分类色条保留在左上角，证据等级徽章保留在右下角。英文为主要字号，中文副标约为其 65–70%。不能只在章节卡
出现，游戏镜头和数据镜头中也要保留。

### 素材来源角标

右上角同时显示以下一种来源角标：

- `SAME-RUN LIVE / 同次实机`：画面与数据来自同一次 runner；
- `IMMUTABLE EVIDENCE / 冻结实证`：使用已冻结 JSON、checkpoint 或报告重建画面；
- `ILLUSTRATIVE ARCHIVE / 独立历史画面`：CK3 画面仅用于说明，不能剪成与右侧 JSON 同一次运行；
- `FIXTURE DEFINITION / 定义夹具`：必须明确告诉观众不是 stock event/notification；
- `DOCUMENTED LIVE / 文档化实机`：存在已记录实机事实，但没有同次视频素材，不得伪造同次录制。

### 通用版式

- Native 章节优先采用三栏：左侧 CK3 或地图示意，中间 typed JSON/highlight，右侧 postcondition 与证据 SHA。
- 历史视觉镜头与独立 native artifact 同屏时，中间必须有明显竖线，并显示
  `Illustrative gameplay — independent evidence / 游戏画面仅作说明——证据来自独立实机`。
- 每个动作都按 `OBSERVE → DECIDE → ACT → VERIFY` 高亮当前阶段；只有完整跑过的环节才点亮。
- 不以 schema、ACK、测试数量或命令列表冒充玩法闭环。ACK 镜头后必须出现真实新 frame/postcondition，或明确标注
  `ACK ONLY — NOT VERIFIED / 仅有 ACK，未验证`。
- Native-headless 章节可显示 `NO OCR • NO MOUSE • WINDOW MINIMIZED / 无 OCR・无鼠标・窗口最小化`；历史视觉 fallback
  章节不得使用这条标语。

### 原始 21 项能力到成片章节的映射

| 原矩阵项 | 本片章节 |
|---:|---|
| 1 exact-build 原生核心 | 1 |
| 2 固定开局与 UI 历史蒙太奇 | 2 |
| 3 会话、暂停、时间与进程管理 | 3 |
| 4 checkpoint、冷恢复与清理 | 3 |
| 5 campaign root 与 feature discovery | 4 |
| 6 数值事件查询与提交 | 5 |
| 7 当前事件窗 typed observation | 5 |
| 8 pending character interaction | 6 |
| 9 notification ACK | 5 |
| 10 婚姻关系与最小候选动作 | 6 |
| 11 固定候选宣战 | 7 |
| 12 既有战争移动、路线与围城 | 8 |
| 13 route contact 与真实接敌 | 8 |
| 14 战斗输入数据面 | 9 |
| 15 ongoing battle observation / hold | 9 |
| 16 主动撤退 | 10 |
| 17 reinforcement assignment 观测 | 10 |
| 18 battle normal terminal | 11 |
| 19 战争终止选项只读判断 | 11 |
| 20 一代结算、不可变 seed 与跨局记忆 | 12 |
| 21 诚实能力边界 | 13 |

## 总时间表

下表是叙事层的 14 段计划；最终 compositor 为了逐项绑定证据，将其展开为 27 个 chapter。最终逐章起止时间以同名
`.video.json` sidecar 为准。

| 章节 | Timecode | 时长 | 主徽章 |
|---|---|---:|---|
| 0. Cold open / 开场定调 | `00:00–00:40` | 0:40 | `VERIFIED CAPABILITIES / 已验证能力` |
| 1. Native core / 原生核心 | `00:40–01:30` | 0:50 | `PRODUCTION-LIVE PRIMITIVE` |
| 2. What the agent can visibly operate / 历史可见操作 | `01:30–02:50` | 1:20 | `VISUAL-NARROW ARCHIVE` |
| 3. Time, checkpoint and cold recovery / 时间、存档与冷恢复 | `02:50–04:05` | 1:15 | `PRODUCTION-LIVE LOOP` |
| 4. Campaign discovery / 战役根与功能发现 | `04:05–05:05` | 1:00 | `PRODUCTION-LIVE PRIMITIVE` |
| 5. Events and interruptions / 事件与中断 | `05:05–06:55` | 1:50 | mixed, per shot |
| 6. Interactions and marriage / 人物互动与婚姻 | `06:55–08:00` | 1:05 | mixed, per shot |
| 7. Entering war / 进入战争 | `08:00–09:05` | 1:05 | `PRODUCTION-LIVE PRIMITIVE` |
| 8. Movement, siege and contact / 行军、围城与接敌 | `09:05–10:35` | 1:30 | `PRODUCTION-LIVE LOOP` |
| 9. Combat data and hold loop / 战斗数据与持续观测 | `10:35–12:05` | 1:30 | mixed primitive/loop |
| 10. Retreat and reinforcement / 撤退与增援 | `12:05–13:35` | 1:30 | mixed loop/primitive |
| 11. Battle end and war exit / 战斗终局与战争退出 | `13:35–14:35` | 1:00 | mixed primitive/loop |
| 12. Death settlement and next episode / 死亡结算与下一局 | `14:35–15:35` | 1:00 | `PRODUCTION-LIVE PRIMITIVE` |
| 13. Evidence wall and honest frontier / 证据墙与真实边界 | `15:35–16:50` | 1:15 | `NOT COMPLETE / 尚未完成` |

## 逐镜 storyboard

### 0. Cold open / 开场定调 — `00:00–00:40`

Badge：`VERIFIED CAPABILITIES — NOT A COMPLETE GAME AGENT / 已验证能力——并非完整游戏智能体`

来源：战争、事件窗和历史视觉素材的快速剪影；每个剪影沿用自身来源角标，不得把它们伪装成一条连续 run。

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `00:00–00:10` | 黑场后快速闪现 paused map、CombatID、事件窗、checkpoint hash；标题英文居中，中文副题在下。 | “This is a working foundation for an autonomous Crusader Kings Three player: direct game-state observation, bounded decisions, native actions, and verified postconditions.” | “这是一套正在工作的 CK3 自动玩家基础：直接观察游戏状态、进行有界决策、执行原生动作，并验证真实后置状态。” |
| `00:10–00:24` | OODA 环：`OBSERVE → DECIDE → ACT → VERIFY → MEMORY`，已经闭合的节点变绿，缺失节点保持虚线。 | “The goal is a high-intelligence agent that can complete this loop across an entire campaign. Today, we will show everything that is genuinely available—and label everything that is not.” | “终极目标，是让高智商智能体在整场战役中持续完成这一循环。今天，我们展示所有真实可用能力，也明确标出尚未完成的部分。” |
| `00:24–00:40` | exact build 卡：`CK3 1.19.0.6`、EXE SHA；底部出现状态图例。 | “No capability in this film is called complete. Production loops, production primitives, fixtures, and historical visual regressions are kept separate on screen.” | “本片不会把任何玩法域称为完整。生产实机闭环、生产原语、夹具实机与历史视觉回归会在画面中严格分开。” |

绝不能声称：本片不能以标题、缩略图或旁白写“the complete CK3 AI”“plays the whole game”或“全游戏自治已经完成”。

### 1. Native core / 原生核心 — `00:40–01:30`

Badge：`PRODUCTION-LIVE PRIMITIVE / 生产实机原语`

来源：

- `docs/autonomous-agent-progress/goal-and-roadmap.md`
- `docs/ck3-native-ai/autonomous-capability-roadmap.md`
- `ck3_autonomous_player/README.md`
- exact build：CK3 `1.19.0.6`，EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `00:40–00:55` | 最小化 CK3 窗口图标、PID 与 native bridge 流程；显示 `NO OCR • NO MOUSE • MINIMIZED`。 | “On the frozen 1.19.0.6 build, the native bridge reads typed state and submits semantic commands while CK3 remains minimized. These chapters do not depend on OCR, mouse movement, or the foreground window.” | “在冻结的 1.19.0.6 版本上，原生桥能在 CK3 保持最小化时读取 typed 状态并提交语义命令。这些章节不依赖 OCR、鼠标或前台窗口。” |
| `00:55–01:12` | capability surface 滚动：pause/resume、speed、save/restore、event、marriage、war、army、combat。 | “The exact adapter advertises fifty-six state and command capabilities. They are templates. Only generation-bound literals derived from the current snapshot are eligible to execute.” | “Exact adapter 声明了 56 个状态与命令能力，但它们只是模板。只有从当前 snapshot 展开的 generation-bound literal 才可能执行。” |
| `01:12–01:30` | 一条典型 typed record：revision、date、player、paused；右侧显示 `ACK ≠ POSTCONDITION`。 | “The bridge binds actions to process generation, frame revision, and game identity. An acknowledgement is never presented as success until a new paused frame confirms the gameplay change.” | “原生桥把动作绑定到进程代次、帧 revision 与游戏身份。只有新的 paused frame 确认玩法变化后，ACK 才能成为成功证据。” |

绝不能声称：56 个 capability 不是 56 个随时可用动作，也不代表 56 个完整玩法域。

### 2. What the agent can visibly operate / 历史可见操作 — `01:30–02:50`

Badge：`VISUAL-NARROW ARCHIVE / 固定场景视觉档案`

来源角标：`ILLUSTRATIVE ARCHIVE / 独立历史画面`

整体 GREEN archives：

```text
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260822T102802Z-opening-4cc459ce
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260822T111130Z-opening-a27391b9
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260822T153549Z-opening-69644bad
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260822T162844Z-opening-33bdd96f
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260822T170117Z-opening-eaeef47a
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260822T172415Z-opening-d20b8adb
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260822T190656Z-opening-bfa943a7
```

每个目录只取 `report.json` 可回链的 `artifacts/*.png`。不要使用无法绑定 action receipt 的相邻帧。

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `01:30–01:50` | Robert 1066 开局、契约、祝福/诅咒选择到地图，快切但保留 archive 徽章。 | “The earlier visual runner can traverse the fixed Robert 1066 opening, accept the recurrence contract, resolve blessing and curse pages, and arrive on the map.” | “早期视觉 runner 能完成固定的 1066 罗贝尔开局，接受轮回契约，处理祝福与诅咒页面，并进入地图。” |
| `01:50–02:10` | 角色页、家庭信息、生活方式选择、时间推进。 | “It can open the player character, inspect visible family information, select a lifestyle in this regression path, and advance time while handling expected interruptions.” | “在这条回归路径中，它能打开玩家角色页、查看可见家庭信息、选择生活方式，并在处理预期中断后推进时间。” |
| `02:10–02:30` | 单事件与五页事件连锁；每段角标写 `VISUAL TEXT PATH`。 | “Archived runs also crossed one ordinary event and a five-page event chain. These were visible-text workflows, not native semantic understanding of arbitrary events.” | “历史 run 还处理过一个普通事件和五页事件链。它们属于可见文本流程，并非对任意事件的原生语义理解。” |
| `02:30–02:50` | F2/F3/F4/F8、空建筑槽、150 金 Level 1 pasture、月份进度。 | “The same fixed scene reached domain, military, council, and decision panels, then built a level-one pasture for one hundred fifty gold and verified construction progress.” | “同一固定场景还打开了领地、军事、内阁与决议面板，并花费 150 金建造一级牧场，验证了施工进度。” |

绝不能声称：这些画面不是通用经济、内阁、生活方式或事件策略；历史 visual fallback 可能使用 OCR、键鼠、快捷键与固定坐标。

### 3. Time, checkpoint and cold recovery / 时间、存档与冷恢复 — `02:50–04:05`

Badge：`PRODUCTION-LIVE LOOP / 生产实机闭环`

来源：

- `docs/testing-workflow.md`
- `docs/ck3-native-checkpoint-contract.md`
- `docs/ck3-native-ai/player-counterpolicy.md`
- `ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py`

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `02:50–03:06` | paused frame 中的 date/player/revision；速度 1 的一天切片，下一 paused frame。 | “The managed owner identifies a playable map, pauses the game, changes speed under control, advances only within a bounded budget, and re-observes the next paused frame.” | “受管 owner 能识别可玩地图、暂停游戏、受控调整速度，只在有界预算内推进时间，并重新观察下一个 paused frame。” |
| `03:06–03:25` | `native-auto-run --turns 6 --cold-start-checkpoint` 时间线；PID `81684`、日期 `53176104→53176176`。 | “In a production run, three verified one-day advances produced a 66,420,106-byte checkpoint at date 53,176,176. Query-only turns and acknowledgements did not count as gameplay progress.” | “一次生产 run 中，三次验证成功的一日推进，在日期 53176176 生成了 66,420,106 字节 checkpoint。纯查询和 ACK 不计为玩法进展。” |
| `03:25–03:45` | checkpoint SHA `E8041581...`；旧 PID 关闭，新 PID `34084`；恢复同日期/角色。 | “The first process was fully reclaimed. A fresh CK3 process restored the checkpoint to the same date and character, proving save materialization and cold recovery rather than a command acknowledgement.” | “旧进程被完整回收，全新的 CK3 进程把 checkpoint 恢复到相同日期与角色，证明的是存档物化与冷恢复，而不是命令 ACK。” |
| `03:45–04:05` | 大数字卡：`210/210 turns • 78 visible turns • 75 game days • 0 recovery`，checkpoint SHA `12FD30...F37D`。 | “The managed active-war continuation accumulated 210 successful turns, 78 visible gameplay turns, and 75 game days with periodic and final checkpoints and proven cleanup after every run.” | “既有战争的受管续跑累计完成 210 个成功回合、78 个可见玩法回合和 75 个游戏日，并在每轮验证周期与最终 checkpoint 以及完整清理。” |

绝不能声称：这不是全游戏覆盖率，也不能证明从任意 checkpoint 恢复后所有高层 intent 都已重建。

### 4. Campaign discovery / 战役根与功能发现 — `04:05–05:05`

Badge：`PRODUCTION-LIVE PRIMITIVE / 生产实机原语`

来源：

```text
C:\Users\xenoa\AppData\Local\Temp\xar-campaign-root-context-live-a-v2.json
C:\Users\xenoa\AppData\Local\Temp\xar-campaign-root-context-live-b-v1.json
C:\Users\xenoa\AppData\Local\Temp\xar-loaded-feature-manifest-live-v1.json
```

Runners：

```text
ck3_autonomous_player/native_bridge/research/run_campaign_root_context_live_acceptance.py
ck3_autonomous_player/native_bridge/research/run_loaded_feature_manifest_live_acceptance.py
```

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `04:05–04:25` | 两张角色/地图卡并排。A：Character `29829`、duchy `2141`、capital `2619`、independent。B：Character `36108`、liege `37011`。 | “The campaign-root query has been accepted on two distinct political positions: an independent ruler and a vassal. It binds player, primary title, tier, capital, liege, government flags, and game rules.” | “Campaign-root 查询已在两种不同政治位置上完成实机验收：独立统治者与封臣。它绑定玩家、主头衔、等级、首都、领主、政府标志和游戏规则。” |
| `04:25–04:43` | feature grid 动画：44 registry rows 逐一变亮；29 runtime keys 单独分组。 | “The loaded-feature manifest returned all forty-four registry rows and twenty-nine runtime `has_dlc` keys from the running process, giving the planner an exact feature-gating surface.” | “Loaded-feature manifest 从运行进程返回全部 44 个 registry row 和 29 个 runtime `has_dlc` key，为 planner 提供精确的功能门控表面。” |
| `04:43–05:05` | “Known now / Not yet” 双栏：root/rules/features vs bookmarks/governments/entitlements。 | “This is map-context discovery, not campaign setup intelligence. Bookmark choice, ruler comparison, all ranks and governments, and account entitlement provenance remain open work.” | “这属于地图内上下文发现，不是战役开局智能。Bookmark 选择、统治者比较、全部等级与政府，以及账号 entitlement 来源仍未完成。” |

绝不能声称：runtime feature key 不等于账号所有权；两个 feudal 样本不能代表所有政府、DLC 与 landless 场景。

### 5. Events and interruptions / 事件与中断 — `05:05–06:55`

本章逐镜切换徽章，不允许使用一个统一 GREEN 覆盖全部事件能力。

来源：

- 数值事件历史实机：`docs/ck3-native-ai/events-and-interactions.md`
- Current event runner：
  `ck3_autonomous_player/native_bridge/research/run_current_event_window_context_live_acceptance.py`
- 冻结 Attempt4：
  `C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-cea30a0-live-attempt4.json`
- 可直接裁切的同次双语视频：
  `artifacts/demos/2026-08-27/ck3-autonomous-agent-event-window-bilingual-20260827-004648.mp4`
- Notification ACK：
  `artifacts/pending-notification-ack-70bf8e6-live-attempt8-fixture-definition.json`

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `05:05–05:23` | Badge `PRODUCTION-LIVE PRIMITIVE`。数字事件 instance 14 五项，option 1 提交后 instance 15 三项。 | “The native command layer has historical production evidence for numeric event selection: instance fourteen exposed five options, and submitting option one produced a new instance with three options.” | “原生命令层已有数值事件选择的历史生产实证：instance 14 暴露五个选项，提交 option 1 后出现了拥有三个选项的新 instance。” |
| `05:23–05:45` | 切入现成双语视频的 seed PID 事件窗，Badge 改为 `FIXTURE-LIVE`，角标 `SAME-RUN LIVE + FIXTURE DEFINITION`。 | “The newer current-window query goes further. In a real CK3 process, it reads the canonical event key and the options that the window actually materialized, without selecting anything.” | “更新的 current-window 查询更进一步：它在真实 CK3 进程中读取 canonical event key 与窗口实际物化的选项，并且不执行选择。” |
| `05:45–06:10` | 视频中的 checkpoint handoff 与 fresh-cold PID；overlay：instance `17`、key、indices `[0,1,3]`、cancel `[3]`。 | “Across checkpoint handoff and a fresh cold process, full instance seventeen and the canonical key remain stable. The bridge recovers native indices zero, one, and three, the disabled reason, and the real cancel flag on index three.” | “跨 checkpoint 交接和 fresh-cold 新进程后，完整 instance 17 与 canonical key 保持稳定。原生桥恢复 indices 0、1、3、禁用原因，以及 index 3 上的真实 cancel 标志。” |
| `06:10–06:32` | option effect area 为空，旁边大字：`EMPTY SUBSET ≠ NO EFFECTS`；`semantic_decision_ready=false`。 | “The typed indicator subset is empty in this fixture. Empty does not mean harmless, and it does not mean complete. Structured effects, stable scopes, resource and relationship deltas, and semantic choice are still unavailable.” | “本 fixture 的 typed indicator 子集为空。空不等于无害，也不等于完整。Structured effects、稳定 scope、资源与关系变化，以及语义选择仍不可用。” |
| `06:32–06:55` | Badge 保持 `FIXTURE-LIVE`；notification full ID `738197506`，query/query/ACK 后消失；明确显示 `NOT STOCK`。 | “A separate non-religious notification fixture proves a generation-bound fixed acknowledgement: query, query, acknowledge, and the old full ID disappears. It is a fixture proof, not natural stock-notification coverage.” | “另一个非宗教 notification fixture 证明 generation-bound fixed ACK：query、query、acknowledge，随后旧 full ID 消失。这是夹具实证，不是自然 stock notification 覆盖。” |

绝不能声称：current event fixture 不是 stock event；空 indicator 不是完整 effect preview；本章没有证明多选事件的高质量语义决策，notification 也未覆盖普通请求、intermediary 或自然 stock 情况。

### 6. Interactions and marriage / 人物互动与婚姻 — `06:55–08:00`

来源：

```text
C:\Users\xenoa\AppData\Local\Temp\xar-pending-interaction-context-v1-live-20260826-04.json
C:\Users\xenoa\AppData\Local\Temp\xar-pending-special-war-binding-v1-live-attempt2.json
C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260823T032552Z-dev-session-b4ded92f
```

注意：最后一个 dev-session 整体 `ok=false, finalized=false`，只允许取可回链的单条成功婚约 receipt，不得显示整场 GREEN。

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `06:55–07:12` | Badge `PRODUCTION-LIVE PRIMITIVE`。pending interaction typed card：full ID、kind、五 roles、route、deadline。 | “The pending-interaction query reads a stable kind, five typed roles, routing, deadline information, send options, and four independent legality results from a paused production frame.” | “Pending-interaction 查询能从 paused production frame 读取稳定 kind、五个 typed role、routing、deadline、send options 与四路独立 legality。” |
| `07:12–07:28` | White-peace interaction card 连接到 WarID `16777290` 和 primary roles；OBSERVE 点亮，ACT 熄灭。 | “For the current white-peace request, the special binding resolves the exact interaction definition and outcome to war 16,777,290 and its primary sides. No reply was sent in this proof.” | “对于当前白和请求，special binding 把准确的互动定义与结果绑定到 WarID 16777290 及其 primary sides。本次实证没有发送回复。” |
| `07:28–07:46` | Badge `IMPLEMENTED` + `ILLUSTRATIVE ARCHIVE`。只取成功婚约前后画面与 spouse/betrothed CharacterID。 | “Marriage plumbing can read spouse and betrothal relations, enumerate legal Character IDs, submit a proposal, and wait for a relationship postcondition. A historical fixed-scene receipt arranged a Danish betrothal.” | “婚姻管线能读取配偶与婚约关系、枚举合法 CharacterID、提交求婚，并等待关系后置状态。固定场景的历史 receipt 曾成功安排丹麦婚约。” |
| `07:46–08:00` | 大字：`FIRST LEGAL CANDIDATE ≠ SMART MARRIAGE`；宗教边界小卡。 | “The current policy may still choose the first legal candidate. Faith may only be consulted when native legality, acceptance, cost, or result makes it unavoidable, and it remains an opaque minimal input.” | “当前策略仍可能选择第一个合法候选。只有原生合法性、接受度、费用或结果确实要求时，才允许最小调用信仰，并始终把它视作 opaque input。” |

绝不能声称：没有智能婚姻评分、完整接受度/遗传/联盟/继承评估，也没有 pending interaction 的语义 accept/reject policy。

### 7. Entering war / 进入战争 — `08:00–09:05`

Badge：`PRODUCTION-LIVE PRIMITIVE / 生产实机原语`；历史 Palermo 镜头另叠
`VISUAL-NARROW ARCHIVE / 固定场景视觉档案`。

来源：

- `ck3_autonomous_player/README.md`
- `docs/ck3-native-ai/war-entry.md`
- `docs/ck3-native-ai/player-counterpolicy.md`
- 历史 dev archive：
  `C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260823T032552Z-dev-session-b4ded92f`
- commit anchors：`5d7e2ba`、`4770382`、`9ff4be5`

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `08:00–08:17` | typed declaration：candidate/CB → command `declare-war-29097-11-0` → WarID `16777290`。 | “The exact bridge has mechanically submitted a fixed declaration candidate while CK3 remained minimized. The postcondition was a real new war identity: War ID 16,777,290.” | “Exact bridge 曾在 CK3 保持最小化时机械提交一个固定宣战候选，真实后置状态是新出现的 WarID 16777290。” |
| `08:17–08:34` | strategic power comparison 数据；planner stop reason `native_war_entry_evidence_required`。 | “The planner can read strategic power and compare targets, but it now stops when participant timing, combat forecast, campaign cost, exit outcome, and calibrated utility are missing.” | “Planner 能读取 strategic power 并比较目标，但当参战时间、战斗预测、战役成本、退出结果和校准效用缺失时会主动停止。” |
| `08:34–08:52` | Palermo 历史画面：宣战、战分 100%、enforce、disband；始终显示 `ILLUSTRATIVE ARCHIVE — FIXED SCENARIO`。 | “A development archive shows the fixed Palermo sequence reaching one hundred percent war score, enforcing the result, and disbanding. This is useful visual history, not a generic war-entry policy.” | “开发档案展示了固定巴勒莫流程达到 100% 战分、执行结果并解散军队。这是有价值的历史画面，不是通用宣战策略。” |
| `08:52–09:05` | 宗教例外卡，圣战图标只出现为战争标签，不打开 faith UI。 | “This holy-war clip is allowed only as a narrow war exception. The film does not inspect faith, doctrine, tenets, fervor, conversion, reform, or holy orders.” | “该圣战片段只属于狭窄的战争例外。本片不会探索信仰、教义、教条、宗教热忱、改宗、改革或骑士团。” |

绝不能声称：不是通用 CB 选择、智能开战、盟友预测、多战争规划或宗教玩法。不得利用圣战片段扩展为 faith-system 展示。

### 8. Movement, siege and contact / 行军、围城与接敌 — `09:05–10:35`

Badge：`PRODUCTION-LIVE LOOP / 生产实机闭环`

来源：

```text
docs/ck3-native-ai/player-counterpolicy.md
docs/ck3-native-ai/actual-contact-scope.md
C:\Users\xenoa\AppData\Local\Temp\xar-war-entry-production6b-state\logs\p0-actual-contact-first-live.json
C:\Users\xenoa\AppData\Local\Temp\xar-war-entry-production6b-state\logs\p0-actual-contact-cold-restore-live.json
```

Commit anchors：`17eca94`、`be9add4`、`e608afc`、`2d93a54`、`40f3589`。

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `09:05–09:23` | 地图路线示意：raise、objective、route preview、move；OODA 四节点依次亮。 | “Inside an existing war, the planner can raise troops, read objectives and enemy endpoints, preview routes, reject intersecting danger, and submit a generation-bound move.” | “在已经存在的战争中，planner 能集结军队、读取目标与敌军端点、预览路线、拒绝相交危险，并提交 generation-bound 行军。” |
| `09:23–09:40` | 围城 card：fort、garrison、siege progress、breach、assault state；一日节拍。 | “It observes fort, garrison, siege progress, breach, and assault state, and controls progress in bounded one-day slices. Split and merge recovery are available for covered scenes.” | “它能观察 fort、garrison、围城进度、breach 与 assault 状态，并用有界的一日节拍控制进度；覆盖场景中也能处理 split/merge 恢复。” |
| `09:40–09:57` | 210-turn 长跑图：路线 horizon、多次 checkpoint、移动至 `2600`。 | “The 210-turn managed run repeatedly evaluated contact horizons, advanced safely, previewed new candidates, moved toward province 2600, and materialized periodic checkpoints without recovery.” | “210 回合受管长跑反复评估接触 horizon、安全推进、预览新候选、向省份 2600 行军，并在无 recovery 的情况下物化周期 checkpoint。” |
| `09:57–10:16` | route ETA 时间线到 `53178264`，随后同日出现 CombatID `335544325`、Province `2586`、ordered sides。 | “The route-contact prediction reached date 53,178,264. The first real contact frame arrived on that exact date and exposed a new Combat ID, province, and native attacker-defender order.” | “Route-contact 预测抵达日期 53178264。第一个真实接敌帧恰好在同一日期出现，并暴露新的 CombatID、省份与原生攻守顺序。” |
| `10:16–10:35` | PID 切换，cold artifact 保留同 CombatID/Province/sides；显示 first/cold SHA。 | “A combat checkpoint was then cold-restored in a fresh process, and the same contact identity remained queryable. This closes the create-new contact path, not every possible joining topology.” | “随后战中 checkpoint 在全新进程中冷恢复，同一接敌 identity 仍可查询。这闭合的是 create-new 接敌路径，不是所有可能的加入拓扑。” |

绝不能声称：不覆盖完整 supply、attrition、embark、raid、盟友、多军团、多战争、`join_existing` 或多个 compatible combat。

### 9. Combat data and hold loop / 战斗数据与持续观测 — `10:35–12:05`

来源：

```text
docs/ck3-native-ai/combat-simulation-inputs.md
docs/ck3-native-ai/ongoing-battle-frame.md
C:\Users\xenoa\AppData\Local\Temp\xar-war-entry-production6b-state\logs\combat-v3-shared-main-thread-paused-live-acceptance.json
C:\Users\xenoa\AppData\Local\Temp\xar-war-entry-production6b-state\logs\battle-control-v1-cold-main-cache-fix-fresh-live.json
C:\Users\xenoa\AppData\Local\Temp\xar-planner-battle-control-live-20260826-0910.json
```

Runners：

```text
ck3_autonomous_player/native_bridge/research/run_battle_control_live_acceptance.py
ck3_autonomous_player/native_bridge/research/run_planner_battle_control_live_acceptance.py
```

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `10:35–10:52` | Badge `PRODUCTION-LIVE PRIMITIVE`。Combat v3 表：27 Character rows、3 Army rows、15 source families、132 refs。 | “The combat data plane reads a large typed input surface from the live battle: characters, armies, commanders, knights, men-at-arms, terrain, crossing, combat width, and native reference identities.” | “战斗数据面从真实战斗读取大规模 typed 输入：角色、军队、统帅、骑士、兵种、地形、crossing、战斗宽度与原生引用 identity。” |
| `10:52–11:08` | 双方 strength/power 数值与 hills 图；中央红条 `INPUTS — NOT A WIN PROBABILITY`。 | “These are measured inputs, not a victory probability. The current package has no calibrated Monte Carlo result and does not authorize an attack from this data alone.” | “这些是实测输入，不是胜率。当前包没有经过校准的 Monte Carlo 结果，也不会仅凭这些数据授权进攻。” |
| `11:08–11:27` | Badge 改 `PRODUCTION-LIVE LOOP`。Battle-control frame：CombatID、phase/day、ordered sides、current/soft/hard ledger。 | “The ongoing-battle query binds the same Combat ID and reads phase, day, ordered participants, retained entries, current strength, soft losses, hard losses, commander rolls, width, and advantage.” | “Ongoing-battle 查询绑定同一 CombatID，并读取 phase、day、有序参战者、retained entries、当前兵力、软硬损失、统帅点数、宽度与优势。” |
| `11:27–11:47` | 时间线 maneuver 1/2/3 → main 0/1/2；ledger delta 高亮；cold PID `80196`。 | “After cold recovery, bounded advances carried the battle from maneuver days one through three into main days zero through two. Real ledger deltas appeared while immediate repeated queries remained stable.” | “冷恢复后，有界推进把战斗从 maneuver 第 1 至 3 日带入 main 第 0 至 2 日。真实 ledger delta 出现，同时相邻重复查询保持稳定。” |
| `11:47–12:05` | planner hold：`53178264→53178288→53178312`，same CombatID，两次 `same_combat_advanced`。 | “The planner-integrated hold branch then performed query, one-day advance, and same-combat re-query twice. It verified progress instead of treating elapsed time or an acknowledgement as battle change.” | “接入 planner 的 hold 分支连续两次完成 query、一日推进与同一战斗 re-query，以真实状态验证进展，而不是把时间或 ACK 冒充战斗变化。” |

绝不能声称：没有校准胜率、损失分布或通用接战决策；动态 join/leave 和增援同日顺序仍未闭合。

### 10. Retreat and reinforcement / 撤退与增援 — `12:05–13:35`

来源：

```text
docs/ck3-native-ai/active-combat-retreat.md
docs/ck3-native-ai/active-combat-retreat-owner-subset-live-fixture.md
docs/ck3-native-ai/battle-reinforcement-and-join.md
C:\Users\xenoa\AppData\Local\Temp\xar-owner-subset-retreat-live-v13.json
C:\Users\xenoa\AppData\Local\Temp\xar-battle-reinforcement-assignment-live-v2.json
```

Runners：

```text
ck3_autonomous_player/native_bridge/research/run_active_combat_retreat_live_acceptance.py
ck3_autonomous_player/native_bridge/research/run_owner_subset_retreat_live_acceptance.py
ck3_autonomous_player/native_bridge/research/run_battle_reinforcement_assignment_live_acceptance.py
```

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `12:05–12:22` | Badge `PRODUCTION-LIVE LOOP`。day 0/14 `too_early` 红色，day 15/16 legal 绿色。 | “Retreat legality was observed across sixteen bounded days. Day fourteen was still too early. On day fifteen, while the battle remained in the main phase, the native validator became legal.” | “撤退合法性经过 16 个有界游戏日观测。第 14 日仍然 too early；第 15 日战斗仍处于 main phase 时，原生 validator 才变为合法。” |
| `12:22–12:40` | full-side：preview route `[2579]`、token、submit；post frame `retreating=true`，phase `main/12→pursuit/0`。 | “For the full player side, the planner previewed province 2579, consumed a battle-bound token, submitted the move, and verified retreating state, route, and the old combat’s transition into pursuit.” | “对于玩家整侧，planner 预览省份 2579，消费 battle-bound token，提交移动，并验证撤退状态、路线与旧战斗转入 pursuit。” |
| `12:40–12:58` | owner-subset：CUnit `357` 离开；`33554657` 留在原 CombatID；两行颜色分开。 | “A second production scene proved owner-subset behavior: CUnit 357 retreated, while CUnit 33,554,657 stayed in the same combat. The command did not incorrectly remove the entire side.” | “第二个生产场景证明 owner-subset 行为：CUnit 357 撤退，而 CUnit 33554657 留在同一战斗中；命令没有错误移除整侧。” |
| `12:58–13:17` | Badge 改 `PRODUCTION-LIVE PRIMITIVE`。Reinforcement row：asking=true、assigned=false、parent order、route、active CombatID。 | “The reinforcement query reads whether a unit is asking, whether assignment exists, its AI parent stored order, route, and active Combat ID. The accepted production sample was asking but not assigned.” | “增援查询能读取部队是否求援、是否已有 assignment、AI parent stored order、路线与 active CombatID。已验收生产样本是 asking=true、assigned=false。” |
| `13:17–13:35` | owner-subset 后 membership reopen 动画；右栏列出 missing：assigned ETA、join、reassign。 | “After subset retreat, independent army membership was observed reopening. Assigned-and-aligned arrival, real combat joining, and a player reassignment action are still missing.” | “Subset 撤退后，独立军队 membership 的 reopen 已被观测；assigned-and-aligned 抵达、真实加入战斗与玩家改派动作仍未完成。” |

绝不能声称：不代表原生 AI 通用撤退目的地评分或 cadence；增援尚未证明 assigned ETA、真实 join 或可执行改派。

### 11. Battle end and war exit / 战斗终局与战争退出 — `13:35–14:35`

来源：

```text
C:\Users\xenoa\AppData\Local\Temp\xar-battle-terminal-live-v6.json
docs/ck3-native-ai/battle-terminal-and-reentry.md
docs/ck3-native-ai/war-termination.md
```

Runner：

```text
ck3_autonomous_player/native_bridge/research/run_battle_terminal_journal_live_acceptance.py
```

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `13:35–13:52` | Badge `PRODUCTION-LIVE PRIMITIVE/LOOP — NORMAL BRANCH`。33 日时间线到 `normal_result`。 | “A dedicated terminal runner advanced the same battle one day at a time. On day thirty-three it observed a normal result through the production journal and successor query.” | “专用 terminal runner 对同一战斗逐日推进，并在第 33 日通过生产 journal 与 successor query 观察到 normal result。” |
| `13:52–14:07` | old CombatID 从 global/Province 双删除；ResultID 保留；warscore row `2135850`；player retreating。 | “The old Combat ID disappeared globally and from the province, the result identity remained, war score row 2,135,850 appeared, and the player subject was retreating.” | “旧 CombatID 从全局与省份中同时消失，ResultID 保留，战分 row 2135850 出现，玩家 subject 处于 retreating。” |
| `14:07–14:23` | Badge `PRODUCTION-LIVE PRIMITIVE — READ ONLY`。WarID `16777290` 三结果表：surrender `+860`、WP `+11`、victory `-58`。 | “Separately, a paused war-termination query read the current claim war, its plus-forty-one score, and three native outcome validators and acceptance values without changing the war.” | “另一个 paused 战争终止查询只读获取当前 claim war、+41 战分，以及三个原生结果的 validator 与接受度，未改变战争。” |
| `14:23–14:35` | 写动作上锁图标：`WHITE PEACE / SURRENDER WRITES FROZEN`。 | “White-peace and surrender writes remain frozen until structured terms and campaign-decision readiness are complete. Read-only evidence is not an autonomous exit policy.” | “在 structured terms 与 campaign-decision readiness 完成前，白和与投降写动作保持冻结。只读证据不是自动退出策略。” |

绝不能声称：normal terminal 不覆盖 no-normal、同省 residual 或 assignment-reopened；不能说智能体已能安全自动白和、投降或理解全部动态条款。

### 12. Death settlement and next episode / 死亡结算与下一局 — `14:35–15:35`

Badge：`PRODUCTION-LIVE PRIMITIVE / 生产实机原语`

来源：

- `docs/ck3-agent-one-life-terminal.md`
- `docs/ck3-native-settlement-contract.md`
- commit anchors：`f6bbff0`、`fdd760e`、`24ba8d0`

来源角标：`DOCUMENTED LIVE / 文档化实机`。没有同次视频时只使用 settlement 数据卡、PID 时间线和明确标注的独立 CK3 地图画面。

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `14:35–14:51` | episode Character `29829` → heir `38822`；planner action list 只剩 `death-terminal`。 | “When the played character changed from episode character 29,829 to heir 38,822, the one-life planner executed only the death-terminal path. It issued no marriage, war, save, or time-advance action to the heir.” | “当 played character 从本局角色 29829 切换到继承人 38822 时，一代制 planner 只执行 death-terminal，没有向继承人发送婚姻、战争、存档或时间推进动作。” |
| `14:51–15:05` | settlement payload：score raw `680000/100000 = 6.8`、candidate `6`、record_written=true、`xar_hs_ge_6` stable。 | “The native settlement returned a score of 6.8, candidate record six, one blessing, and a written record. The high-score bit was observed stable twice before the episode was recorded.” | “Native settlement 返回 6.8 分、候选纪录 6、一次祝福与已写纪录；高分位连续两次稳定后，episode 才被记录。” |
| `15:05–15:20` | PID `119628→110972`，run ID 变化，immutable `xar_episode_seed.ck3`；terminal flag 清零。 | “Start-next-episode stopped PID 119,628 and launched PID 110,972 from the immutable episode seed. The run identity changed, terminal state cleared, and the previous cross-run plan was carried forward.” | “Start-next-episode 停止 PID 119628，并从不可变 episode seed 启动 PID 110972。Run identity 改变，terminal 状态清零，上一局的跨局计划被带入。” |
| `15:20–15:35` | 新局 native move `2618→2615`，7 日后 paused/minimized；memory 卡只列少量 boolean。 | “The new minimized process submitted one native army move and advanced seven game days, from province 2618 to 2615. Cross-run memory remains a handful of outcomes, not a learned world model.” | “新最小化进程提交一次原生军队移动并推进 7 个游戏日，从省份 2618 到 2615。跨局记忆仍只是少量结果，不是学习型世界模型。” |

绝不能声称：这不是自然死亡完整 episode、无继承人死亡或普通 campaign 跨继承；一代制模式有意不继续扮演继承人。

### 13. Evidence wall and honest frontier / 证据墙与真实边界 — `15:35–16:50`

Badge：`NOT COMPLETE / 尚未完成`

来源：`docs/autonomous-agent-progress/goal-and-roadmap.md` 与本页末尾最终证据表。

| Time | Picture / 画面 | English narration | 简体中文字幕 |
|---|---|---|---|
| `15:35–15:50` | 绿色闭环卡：checkpoint/cold restore、部分既有战争、create-new contact、battle hold、两类 retreat。 | “The strongest current results are narrow production loops: managed recovery, portions of an existing war, create-new contact identity, bounded ongoing-battle observation, and full-side plus owner-subset retreat.” | “当前最强成果是狭窄的生产实机闭环：受管恢复、既有战争的部分流程、create-new 接敌 identity、有界战中观测，以及 full-side 与 owner-subset 撤退。” |
| `15:50–16:05` | 蓝/琥珀/紫三栏：campaign root、combat inputs、terminal、interaction；event/notification fixtures；marriage implemented。 | “Around those loops are production primitives, fixture-live observations, and implemented actions. The badge matters: a typed query, a fixture, or a successful fixed command is not an entire gameplay domain.” | “这些闭环周围还有生产原语、夹具实机观测与已实现动作。徽章非常重要：typed query、fixture 或固定命令成功，都不等于整个玩法域。” |
| `16:05–16:22` | 未完成域矩阵：economy/council/military prep、smart war entry、多战争、family/succession、diplomacy/vassals、schemes/prisoners、health/stress、culture/law、activities/court。 | “General economy, council and military preparation; intelligent war entry and multi-war control; family, succession, diplomacy, vassals, schemes, prisoners, health, culture, law, activities, court, and long-horizon learning remain unfinished.” | “通用经济、内阁与军备；智能宣战与多战争；家庭、继承、外交、封臣、谋略、囚犯、健康、文化、法律、活动、宫廷与长期学习都仍未完成。” |
| `16:22–16:35` | 宗教边界卡：`DEFERRED`；两条窄例外以细绿框标出。 | “Religion is intentionally deferred. Only minimal holy-war semantics required by war OODA, and minimal faith-dependent marriage legality or acceptance, are allowed. Faith stays opaque. Holy orders remain deferred.” | “宗教域由所有者明确暂缓。只允许战争 OODA 必需的最小圣战语义，以及婚姻合法性或接受度不得不依赖时的最小判定。Faith 保持 opaque，holy order 继续暂缓。” |
| `16:35–16:50` | 最终证据墙：关键 artifact 文件名、SHA 尾段、`NoCK3=true`；最后回到 OODA 图，未完成分支为虚线。 | “This is not the finish line. It is a measured base: exact observations, bounded actions, and evidence-backed loops that can now be extended domain by domain toward a genuinely intelligent CK3 player.” | “这不是终点，而是一套经过度量的基础：精确观测、有界动作与证据支持的闭环。下一步将按玩法域继续扩展，最终构建真正高智商的 CK3 自动玩家。” |

片尾必须停留至少 4 秒，显示：`No domain is COMPLETE / 当前没有任何玩法域达到 COMPLETE`。

## 宗教例外的剪辑红线

1. Palermo 历史画面只能标为 `Holy-war war-OODA exception / 圣战战争 OODA 例外`；不得打开或讲解 faith、doctrine、tenet、
   fervor、conversion、reformation 或宗教改革界面。
2. 不得把圣战成功称为“religion capability”；它只证明固定战争场景中的历史动作链。
3. 婚姻章节如果出现 faith，只允许显示原生最终 legality/acceptance/cost/result；faith identity 必须保持 opaque，不比较教义。
4. Holy order 继续 `DEFERRED`；great holy war、通用宗教 AI 树与任何改宗策略不得出现在“已有能力”蒙太奇。
5. 片尾用明确措辞 `Religion intentionally deferred / 宗教域按所有者要求暂缓`，不能把暂缓写成完成。

## 最终证据表

成片最后两张证据卡应从下表选取，不得混用不同 run 的 PID、SHA 或“同次实机”标签。Markdown 中保留全值，画面可显示
文件名、关键数值及 SHA 前后各 8 位。

| 能力 | 分类 | 最强 runner / artifact / 文档 | SHA-256 或关键事实 | Commit anchor | 画面边界 |
|---|---|---|---|---|---|
| exact-build native core | `production-live primitive` | `docs/ck3-native-ai/autonomous-capability-roadmap.md` | CK3 `1.19.0.6`; EXE `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` | `b80307a` | 56 declarations 不等于完整能力。 |
| fixed visual opening/UI | `visual-narrow archive` | 七个 `20260822T...opening...` GREEN run root | 每个 `report.json`: `ok=true, finalized=true` | `1dd7648` 等历史提交 | 固定 Robert 1066；可用 OCR/键鼠。 |
| checkpoint/cold restore | `production-live loop` | `native-auto-run --turns 6 --cold-start-checkpoint`; `docs/testing-workflow.md` | checkpoint `E8041581C789C21792280A893325082452F8A9717C8CDD421358FF9739189F07`; PID `81684→34084` | `40f3589` | 不是任意 checkpoint 的全局策略恢复。 |
| active-war long run | `production-live loop` | `docs/ck3-native-ai/player-counterpolicy.md` | `210/210`; 78 visible turns; 75 days; checkpoint `12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D` | `40f3589` | 不是全游戏覆盖。 |
| campaign root A | `production-live primitive` | `%TEMP%/xar-campaign-root-context-live-a-v2.json` | `DA5EB7F01A48A2869B8C9B6B2F6607825FA5319715F66D2C0D04AFFCF802CDDC` | `d67c8df` | independent feudal sample。 |
| campaign root B | `production-live primitive` | `%TEMP%/xar-campaign-root-context-live-b-v1.json` | `677C4FF9727A479B40D068EC7E62A7AC54EF2E21A3EF57649D624C7648B279F9` | `d67c8df` | vassal feudal sample。 |
| loaded features | `production-live primitive` | `%TEMP%/xar-loaded-feature-manifest-live-v1.json` | `2B1C8CA495A3A03F39C8C27351411B5AED2285D732946AACF5AFE89D8B3C2F2D`; 44/44 rows | `d67c8df` | 不证明 account entitlement。 |
| current event window | `fixture-live` | `%TEMP%/xar-current-event-window-context-cea30a0-live-attempt4.json` | `690EB5EA188B0903281E5F5DFDA343DA795117EE0FB1C83C3FCDC7F572170B7B` | `d44ea32` | 无 selection；不是 stock event。 |
| current event video | `fixture-live same-run` | `artifacts/demos/2026-08-27/ck3-autonomous-agent-event-window-bilingual-20260827-004648.mp4` | `873498C21BD2795ED185B00C0579C118D944E5CE4BE2592B49C4E232CCDF4A81`; `170.700s` | `d46a129`, `f33b546` | 只裁 event 章；保留 fixture 标签。 |
| notification ACK | `fixture-live` | `artifacts/pending-notification-ack-70bf8e6-live-attempt8-fixture-definition.json` | `E696C54F4A761C5BE29D00E7AA62C5529185F7D35F8F2D790BB2830CDBCB1308` | `6012983` | 非自然 stock notification。 |
| pending interaction | `production-live primitive` | `%TEMP%/xar-pending-interaction-context-v1-live-20260826-04.json` | `D20E339D56AFEFF8EB53F90FFD120AA8C42216AD214D38B7AC1B0EA9A2B8BC89` | `a667d55` | query only；未回复。 |
| pending WP binding | `production-live primitive` | `%TEMP%/xar-pending-special-war-binding-v1-live-attempt2.json` | `3140B47AD855DF50BE182CB41E5957D1041E2221496A7256C7FF903E660810EE` | `89b197b`, `adadaec` | 只闭合 white-peace binding。 |
| marriage | `implemented`, partial result live | `docs/ck3-native-ai/autonomous-capability-roadmap.md`; individual successful dev receipt | spouse/betrothed relation postcondition | `bb530ea`, `abe6cf4` | 首个合法候选不等于智能婚姻。 |
| declaration | `production-live primitive`, historical fixed candidate | `ck3_autonomous_player/README.md` | command `declare-war-29097-11-0` → WarID `16777290` | `5d7e2ba` | 不是通用宣战策略。 |
| exact contact first | `production-live loop`, create-new | `.../xar-war-entry-production6b-state/logs/p0-actual-contact-first-live.json` | `265D4FFCC644DCEFCFE192A273880DB6D37901B89AF733C12FA304B530597B5C` | `2d93a54` | 不覆盖 join-existing。 |
| exact contact cold | `production-live loop`, create-new | `.../xar-war-entry-production6b-state/logs/p0-actual-contact-cold-restore-live.json` | `0CFFD7BDC211F8723A2E0826617450F0808BA14AA757F6B884F217BA24DD3F2C` | `2d93a54` | 只证明同一 contact identity 冷恢复。 |
| combat inputs v3 | `production-live primitive` | `.../logs/combat-v3-shared-main-thread-paused-live-acceptance.json` | `EBEA36EC41811C7736B0819DC31A2D0B0ABE7205D4FBA76D1FBD7AE629535DA5` | `2d93a54` | 输入不是胜率。 |
| battle-control cold | `production-live loop` | `.../logs/battle-control-v1-cold-main-cache-fix-fresh-live.json` | `A0FC6BB7268E38026CC8EED6D6388BFD675AD5DCFB60A1A65FE1C1B64E816AC6` | `2d93a54` | 不覆盖动态 join/leave。 |
| planner battle hold | `production-live loop` | `%TEMP%/xar-planner-battle-control-live-20260826-0910.json` | `96CE25384517F0060A58623958DE071F43C3C2F7B68AEB6E668473E986C1DD57` | `2d93a54` | bounded hold，不是完整策略。 |
| retreat legality | `production-live primitive` | `logs/active-retreat-query-days-live.json` | `FB521B39AD5529434596212DB9ADC1EA27D4C270D28D13575B9A2D80913BCF40` | `9fb0c34` | 只读 legality，不是动作证据。 |
| full-side retreat | `production-live loop` | `logs/active-retreat-action-full-side-transition-live-v6.json` | `21D58737126CA4ED8B0B49DB7749EA4701F3BA6F94A8B8493698F8737E5784FA` | `9fb0c34` | 单一 fixture composition。 |
| owner-subset retreat | `production-live loop` | `%TEMP%/xar-owner-subset-retreat-live-v13.json` | `7780B619B2E7B90B8D5D5030D779F58F266585A6246A79B6C2FE20EF0F2701F9` | `9fb0c34` | 不代表通用 AI destination scorer。 |
| reinforcement query | `production-live primitive` | `%TEMP%/xar-battle-reinforcement-assignment-live-v2.json` | `F0A6F3C73D49AE93CC20680E23E787F28B54CA086DAD80392E27651DAB1DB9C6` | `9fb0c34` | 当前 `assigned=false`；无真实 join。 |
| normal battle terminal | `production-live primitive/loop` | `%TEMP%/xar-battle-terminal-live-v6.json` | `61D0D912206A90D9B34DDE3555AEC941EC3538C253DBC4DCEB9D177D7456FDB1` | `8451e2f` | 仅 normal branch。 |
| war termination options | `production-live primitive`, read only | `docs/ck3-native-ai/war-termination.md` | PID `93724`; date `53175816`; WarID `16777290`; query `1/2` | `4770382` 系列 | 没有 write；v2 dynamic terms 未闭合。 |
| one-life settlement | `production-live primitive` | `docs/ck3-agent-one-life-terminal.md`; `docs/ck3-native-settlement-contract.md` | score `6.8`; PID `119628→110972`; move `2618→2615` | `f6bbff0`, `fdd760e`, `24ba8d0` | 非自然死亡全局矩阵；无继承人待验。 |

## 最终媒体验收清单

成片只有同时满足以下各项，才能登记为本页 storyboard 的正式交付：

- 最终扩展版时长位于 `20:00–21:00`，分辨率 `2560×1440`，H.264 可解码且存在 AAC audio stream；
- 英文旁白可懂，所有旁白段落都有画面内简体中文字幕；中文字体无 tofu、乱码、裁切或超安全区；
- 开场、所有章节卡、lower-third、宗教边界卡与最终证据卡均为中英双语；
- 每个镜头的状态徽章与来源角标正确，fixture、archive 与 production 不发生混标；
- 历史 archive 与独立 JSON 同屏时明确写出 independent evidence，不暗示同一次运行；
- current-event 复用片段保留 `fixture-live`、零 selection 与 empty-indicator 边界；
- combat 输入片段持续显示 `INPUTS — NOT A WIN PROBABILITY`；
- war termination 持续显示 `READ ONLY — WRITES FROZEN`；
- Palermo 镜头持续显示 holy-war war-OODA exception，不探索宗教系统；
- 结尾至少停留 4 秒并显示 `No domain is COMPLETE / 当前没有任何玩法域达到 COMPLETE`；
- 生成 sidecar，记录最终视频 path、size、完整 SHA-256、时长、geometry、codec、语言、所用 artifact 与独立/同次来源；
- 用 FFprobe、定距 contact sheet 和关键帧原分辨率抽检；在月报登记前复核所有声明与本页证据表一致。
