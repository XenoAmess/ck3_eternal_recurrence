# CK3 1.20.0.2：事件与待答互动实机迁移矩阵

本页维护新版原生迁移的实机矩阵及真实 attempt 结果。协调者已在一次性 fixture profile 完成 selection、六类 indicator/scope，以及 pending accept/reject/ACK/十成本矩阵。游戏和桌面由协调者独占操作；准备代理只读取磁盘 artifact，没有启动、注入、读取进程或写入当前存档、真实用户目录及工坊。

输入构建为 `1.20.0.2 (Crozier)`，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。生产 DLL、injector、消费者源码和实际存档的哈希由协调者在实机开始时冻结。旧版成功报告只能用于复用步骤，不能当作新版通过证据。

专用外部夹具位于 `artifacts/migrations/2026-09-30/post-update-1.20.0.2/live-1.20.0.2/fixtures/events/`。`selection/`、`window/`、`pending/` 分别是可合并进一次性 fixture mod 的内容目录，包含标准 `events`、`common` 和 `localization` 子目录。协调者将它们复制到所用隔离 profile 的短路径 mod 内容树并加载；本矩阵不修改 production staging 或工坊。新增夹具只允许由当前 human player 触发，NPC 仅作为被玩家触发的互动发送方。合成定义的证据口径为 **fixture-definition playset + production native bridge**。

## 每项共用的请求顺序

1. 游戏暂停后，调用 `ck3_take_snapshot {}`，保留原始结果、公开 `revision`、日期、玩家完整 Character ID、`active_event` 或 `pending_character_interaction` 的完整实例 ID。
2. typed 查询使用这次 snapshot 的公开 revision；相邻查询之间不推进日期。允许 query sequence 不同，其余语义字段应一致。稳定脚本 key 必须一致，calculated ID 和 runtime ordinal 只要求同进程相邻查询稳定，不能要求跨进程相等。
3. 动作必须先取得最新 snapshot，再携带它的 revision 和当前完整实例 ID。保存动作请求、完整响应和后继 snapshot。命令排队成功不足以证明动作发生；旧完整 ID 消失或事件更替以及对应 fixture outcome marker 才是本项结果。

具体 MCP 请求如下，`R`、`E`、`P` 在运行时替换为上一步真实整数：

```json
{"tool":"ck3_take_snapshot","arguments":{}}
{"tool":"ck3_query_current_event_window_context_v1","arguments":{"event_instance_id":"E","expected_revision":"R"}}
{"tool":"ck3_select_event_option","arguments":{"option_number":4,"event_instance_id":"E","expected_revision":"R"}}
{"tool":"ck3_query_pending_character_interaction_context_v1","arguments":{"pending_interaction_id":"P","expected_revision":"R"}}
{"tool":"ck3_reply_pending_character_interaction","arguments":{"accept":true,"interaction_instance_id":"P","expected_revision":"R"}}
{"tool":"ck3_reply_pending_character_interaction","arguments":{"accept":false,"interaction_instance_id":"P","expected_revision":"R"}}
{"tool":"ck3_acknowledge_pending_character_interaction","arguments":{"interaction_instance_id":"P","expected_revision":"R"}}
```

`ck3_select_event_option.option_number` 是脚本 authored native index **加一**，不是当前物化 row 的 rendered index 加一。下面的 selection 夹具中，第 3 条物化 row 的 native index 是 `3`，因此请求 `option_number=4`。

## 矩阵

| 项 | 触发与读取 | 通过条件 | 动作与后继条件 |
| --- | --- | --- | --- |
| S1：选项数量与取消映射 | 当前玩家 scope 触发 `xar_m120_event_selection.1`；snapshot 后 typed 查询两次 | stable key 精确匹配；authored 数量 `5`；物化 native indices `[0,1,3]`；enabled `[true,false,true]`；native `3` 的 cancel 为 true；隐藏 `2` 与未使用 fallback `4` 不出现在物化行中 | 发送 public option `4`；debug.log 新增 `XAR_M120:EVENT_SELECTION\|authored_index=3\|choice=cancel`；后继 snapshot 不再保留原完整 event ID |
| S2：首项选择 | 再触发同一事件，重新 snapshot/query | 本次完整实例 ID 使用新 snapshot；显示与 S1 一致 | 发送 public option `1`；新增 `authored_index=0\|choice=enabled` marker；原完整 event ID 消失 |
| W：六类 indicator 与 scope | 当前玩家触发 `xar_m120_event_window.1`，读取 typed context 两次 | 14 authored、11 materialized native indices `[0,3,4,5,6,7,8,9,10,11,12]`；11 个 enabled 超过原生禁用补位上限 `4`，故 native `1` 不显示；新 backend `ck3-1.20.0.2-native-event-window-v1`；coverage 为 `played-character-event-icon-indicators-1.20.0.2-v1`；真实行发布 trait/stress/fulfillment/stress_and_fulfillment/death/scheme 六种 `kind`，对应已固定的原生 ordinal `0..5`；scope 完整 ID、saved name 与 type key 符合夹具 | 仅选择 public option `1` 的无副作用取消项；不执行 death/scheme 等被观测选项来完成此只读项 |
| P1：普通 accept | 当前玩家触发 `xar_m120_pending.100`；typed query 两次 | 普通通知标记为 false；角色与当前玩家接收者一致；稳定定义 key `xar_m120_pending_reply_fixture_interaction`；原生 accept/reject 为 true、block/ack 为 false；十成本全部合法零值 | `accept=true`；旧完整 pending ID 消失；新增 `XAR_M120_PENDING:ACCEPT` marker |
| P2：普通 reject | 当前玩家触发 `xar_m120_pending.101`，取得新 P/R | 普通路由、角色、原生 reject 合法性正确；不复用 P1 的 ID/revision | `accept=false`；旧完整 pending ID 消失；新增 `XAR_M120_PENDING:REJECT` marker；没有 accept marker |
| P3：auto-accept notification ACK | 当前玩家触发 `xar_m120_pending.102`；typed query 两次 | 定义 key `xar_m120_pending_ack_fixture_interaction`；`auto_accept_notification=true`；接收者此刻为本地 human；auto-accept outcome 已发生，ACK 合法性为 true、普通 accept/reject/block 为 false | 固定 ACK 精确 ID；响应 `interaction_result.status=acknowledged` 且匹配旧 P；后继 snapshot 删除旧完整 ID；没有重复执行 auto-accept outcome |
| P4：十成本向量 | 当前玩家触发 `xar_m120_pending.103`；typed query 两次 | 定义 key `xar_m120_pending_cost_fixture_interaction`；新版十资源顺序的 raw vector 为 `[100000,200000,300000,0,0,0,0,0,0,0]`；`generic_costs_ready=true` | 本项只读；最后 root 可用已验证 reject 清掉该 fixture pending，避免遮挡后续测试 |

W 的详细 event ID、行预期和 scope 内容在 `window/` 的说明及 expectation 文件中。P 的 NPC 发送方创建/选择、事件 ID、成本和 markers 在 `pending/` 的说明及 expectation 文件中。现有 external fixture runner 的定义用于复用内容和合同，本轮不直接启动旧版 runner：其版本、DLL 与 profile 身份固定为旧构建，直接执行会产生不匹配的 harness 结果。

scope 夹具应发布真实 root Character 的完整 ID 以及可解析的 saved Character scope，保留 authored saved name；非 Character scope 按现有 typed envelope 的可观测字段核对，不把 opaque payload 升格为完整对象身份。每个 option indicator surface 的 `complete_effect_set` 仍为 false；`effect_preview_ready` 和 `semantic_decision_ready` 仍应为 false。这些旧能力边界不因六类行和 scope 的新版读口通过而消失。

`window/validate_window_observation.py` 可只读核对保存的完整 MCP query JSON。其 `--revision` 参数比较原生 context 的 `snapshot_revision`，应传 snapshot 的 **native_revision**；MCP 请求的 `expected_revision` 则始终使用公开 **revision**。例如 `py -3.13 <checker> --input <query.json> --player-id <player_id> --revision <native_revision> --event-id <E> --date-raw <date_raw> --output <validation.json>`。输出是对应实机 observation 的离线消费验证，不能代替原始 live query 归档。

P1 至 P4 每次都由玩家显式触发 seed event 创建专用 35 岁 NPC 发送方并给它 gold/prestige/piety 余额。无需固定角色、地图 province、玩家切换或旧存档身份。P4 使用当前已记录语法验证三类非零基础成本及七类合法零值；不把七类依赖政府/身份的非零成本称为已实机覆盖。十项顺序为 gold、prestige、piety、renown、influence、herd、treasury、treasury_or_gold、merit、barter_goods。

新版 fulfillment 两个 indicator 只读取事件选项已物化的显示数据。夹具最小 `change_spiritual_fulfillment` 使用不扩展通用宗教数据、判定或自动玩家策略。

## 保留证据与报告

协调者将每项原始 snapshot/query/action/post-snapshot、fixture 文件与哈希、日志中新增 markers、日志解析错误以及 DLL/build 身份放入同一 `live-1.20.0.2` artifact 根目录。失败 attempt 原样保留，并区分 fixture/加载/会话故障与原生能力故障；只有实际失败才修改本包新版代码。

本矩阵通过后可以分别把对应 primitive 标为本 fixture 范围的 `fixture-live`。它不自动证明 stock event、所有互动、完整 effect preview、非 Character payload 的完整对象身份或整局策略循环。只有根代理随后真实执行对应生产 OODA 并保存状态后继证据，才有对应的 production-live 结论。

## Attempt05 的定义加载结果

以下 attempt05/07 为保留的失败历史；当前实机进展见末尾 attempt09。未通过的 GUI transport 候选没有因此获得 live 状态。

协调者开始了真实 fixture attempt05，准备代理只读其 `C:\Users\xenoa\AppData\Local\XarAutoplayer-1.20.0.2-migration-fixtures\profile\logs\error.log`。日志有两条普通 pending definition 的 `ignores_pending_interaction_block=yes` 与 `auto_accept=no` 不一致，以及三条 `ai_potential` 未配置 AI frequency、不会用于 AI 调度的提示。其后 `CCharacterInteractionDatabase` 正常完成初始化；这些记录尚不能证明首次发送失败或新版 native reader 故障，不据此要求协调者重启当前 attempt。

本 fixture 每次创建不同 NPC actor，普通首发不依赖绕过该 actor 的旧 pending；由此推断 bypass 警告不应影响本矩阵的首次发送，须以真实 pending/marker 互证。另需关注 fixture 的 `ai_will_do=0`：旧 ACK 专题已记录脚本 `run_interaction` 被该值阻断的实机失败，当前构建尚待首次发送结果确认。若实际首发没有留下 pending 且无 SENT marker，最小修复只针对外部 fixture 的发送配置，保留失败 attempt，并在协调者下一次加载时复制新文件；不把 fixture 故障误归为 native 查询失败。

### Attempt05 的选择成功与后续 harness RED

真实 artifact 为 `live-1.20.0.2/attempt-05/mcp.json`。S1 的 trigger、两次 typed query、public `4` 选择及后继旧 ID 消失均已通过；debug.log 同时出现 `XAR_M120:EVENT_SELECTION|authored_index=3|choice=cancel`。这可以作为新版 selection primitive 在本 fixture 范围的 live 证据，不证明后续六类行或 pending 测试通过。

随后 W 的 inbox trigger 超时，未出现 `XAR_M120:TRIGGER|case=window`。日志仅在 `05:48:15/16` 出现两次旧 counter 重建，`05:48:19` 执行一次 inbox，`05:48:20` 出现选择结果；后续没有新的 run 或重建命令。MCP GUI、ExecuteConsoleCommand、GetPlayer、IsValid 的解析错误匹配为零。由此闭合的是重复 seed executor 没有继续；不能据此推断 GetPlayer 失效、选项选择删坏窗口或 native window reader 错误。诊断留在 `live-1.20.0.2/attempt05-events-harness-diagnosis.json`，不改写原 attempt05 RED。

协调者选择下一次 fixture 加载时只替换外部 `transport/gui/xar_mcp_bridge.gui`：两状态显式 `next` A↔B，A 等待 `0.4` 秒并执行 inbox，B 等待 `0.01` 秒后返回 A，同一 counter 持续存活。冻结输入为 `64750ECFA49EE5B8924B05E1DD77D86E9CE1886A7F23671B21863B18365CDE8A`；原版冻结 `gui/hud_notification_templates.gui` 的 `name=a/next=b`（约 `309..312`）与 `name=b/next=a`（约 `323..325`）是对应语法出处。下一次实际验收入口是在 map-ready/paused 后看到约一秒内至少两条 `Running console command: run xar_mcp_inbox.txt`，并在选择关闭后继续看到两条及第二个独立 trigger marker。该候选尚未实机加载，不提前记为修复成功。

协调者也明确授权复用旧 `ai_will_do=0` 发送失败实证作最小 fixture 修正。外部 pending revision 2 为三定义加入 `ai_frequency=0`、把 willingness 改为 `base=1`，保留 `ai_potential={always=no}` 和玩家显式 seed/fixture actor 限定；普通 reply/cost 去掉不适用的 pending bypass。新 definition SHA-256 为 `30EDA7A7B291AD87C9F8D5015FB01F96DA20C96AC86734E0003481C4C914FF0A`，新 plan 为 `C05FBC45D3EF146D1EEC5C6B4690809E59896B0E075F34CA9E380B2BE4FB31A8`。原始文件、计划和精确 patch 留在 sibling `pending-revisions/attempt05-to-next-load/`；准备代理未修改 attempt05 的已加载 profile、游戏或旧版 mod_bridge 源码。此次 pending 的真实首发结果仍未取得。

### Attempt07：timed poll 首次进入仍未发生

协调者加载了初版 A↔B GUI。该 attempt 的日志只有 GUI asset 加载，没有一次 inbox run；selection trigger 的 root marker 在 60 秒后超时。它没有实际执行 selection/window/pending 领域测试，不能认作这些 primitive 的失败。日志没有 MCP GUI、GetPlayer 或 IsValid 解析错误。尚不能在“菜单里创建时玩家无效”“空 state 缺少动画字段”“暂停帧不推进该 GUI timer”三个解释中判定根因；没有为此开展通用 GUI 审计。

下一次加载用同路径 revision 2 增加 `trigger_when="[GetPlayer.IsValid]"` 的 bootstrap，在 `on_start` 立即执行一次 inbox，再进入有 alpha 动画字段的 timed A↔B。冻结 SHA-256 为 `E868FC683492360050AB6E5FCAB0E5F95C8C7CA44363A57938F5334C695B38A6`。原版 `hud_notification_templates.gui:458..460` 使用条件触发并接 `next` 链，主 mod `xar_ironman_terminal.gui:16..17` 使用 GetPlayer 有效条件和 `on_start`；本候选将这两种已有语法用于外部 seed transport。

协调者同时要求优先排除 timer 依赖，故另冻结无 `duration/delay` 的 `transport-frame/gui/xar_mcp_bridge.gui`，SHA-256 `4413DF08D3B4916F2CA9B27E8CFD6B3E72E2F026B0524B6FF601C5ECD72DA927`。该候选在有效玩家 bootstrap 后通过 `next` A↔B、A 的 `on_start` 执行 inbox。其实际 next 调度是否逐帧仍待本次实机测量，不提前宣称 transport 已恢复。每次只加载一个候选，先在暂停地图证明约一秒至少两次 run，再执行领域矩阵，避免重复消耗完整矩阵等待。两份都没有修改当前 profile 或旧 mod_bridge 源码；旧 GUI、metadata 和 patch 留在 `transport-revisions/attempt07-to-next-load/`。

### Attempt09：真实内容回放与 pending seed 故障

新原生 inbox executor 已成功触发 selection 与 window；这次结果不证明前述 GUI poll 候选成功。冻结源为 `live-1.20.0.2/attempt-09/mcp.json`，SHA-256 `384FC487D4D5ED9AB0EDABD720DAF7DE5BB6630CD063FC1C5A1624B8947CB641`。只读[内容核对](../../artifacts/migrations/2026-09-30/post-update-1.20.0.2/live-1.20.0.2/attempt-09/events-live-assessment-native-rule.json)记载原生规则修正后的完整结果；原 12 行期望的 RED 与最初子集核对仍保留。

S1 完整通过：event `14`、native revision `3`；嵌套 typed context 的 native indices `[0,1,3]`、enabled `[true,false,true]`，两帧一致。public `4` 提交 native `3`，真实 debug marker 匹配，后继 active event 为 null。S2 尚未执行。

W 的六种 kind 与各自字段逐行匹配原期望：trait add/remove、stress 与 fulfillment 正反方向、组合 secondary direction、death subject、murder scheme key 均通过。root 为玩家 Character `29829`，saved target 为另一 Character `30784`；保存名称与 province 的 opaque identity 边界也匹配。两帧完全一致，public `1` 提交 native `0` 后旧 event `15` 消失。完整 W 矩阵与取消 primitive 为 fixture-live GREEN。初次 RED 来自夹具要求禁用 `1` 出现的错误假设；两种 fixture 的该 option 都是 `is_ai=yes`、`show_as_unavailable=always yes` 且无 effects，没有 source 差异。真实原因是原生先统计全部 enabled，再让 disabled 补到 `NGui.EVENT_OPTIONS_SHOWN_HIDE_UNAVAILABLE=4`：selection 的 2 个 enabled 允许显示 `1`，W 的 11 个 enabled 则省略 `1`。define 注册 `0xB50880`、全局 `0x5C67B18`、caller `0x1851722/0x1851732` 与 materializer `0x1852BD8/0x1852BDF` 已闭合；`scheme_preparations_event` 的特例上限 `8` 不适用本 default 窗口。

原 12 行期望、generator、RED 和精确 patch 留在 `fixtures/events/window-revisions/attempt09-native-disabled-limit/`，其中 `native-materialization-proof.json` 冻结上述 EXE 字节以及 stock `common/defines/graphic/00_graphics.txt:599`（SHA-256 `BE6151329A44E4C59242F432CD759146AAA6103A1F38368876E2E2749C60D526`）。修正 expectation 后对同一实机 JSON 回放一次，`events-window-validation-native-rule.json` 两帧完整 GREEN，其余字段断言没有放宽。三个 mod 内容文件哈希未变，没有 reader/runtime 改动，不需额外实机重跑。

只读 checker 原先把 MCP 顶层镜像 `schema` 当作纯 native frame，导致两次 `fields are invalid`；最小修复优先遍历 `current_event_window_context` 后，正确报告两次 `expected 12, observed 11`。第一次 RED、before bytes 和 patch 保留在 `fixtures/events/window-revisions/attempt09-checker-wrapper/`，原期望文件未改；后一次结果为 `attempt-09/events-window-validation-after-wrapper-fix.json`。

P1 的 root trigger marker 出现，但随后日志记录原生 `ALLOW_RANDOM_IN_SCOPE` 断言，mailbox failure `512` 对应 executor exception。未出现 seed 后置 marker 或正常 console completion；该 attempt 的日志只能把断点定位在 root marker 后、首次 pending marker 前，不能确定发生在 hidden event 派发、NPC 创建还是 `run_interaction`。因此 attempt09 没有 typed pending/query/action 的 live 证据，失败归为 seed harness RED。`pending-revisions/attempt09-diagnosis/` 保存区分 create/run 的最小标记候选；最终由原生 inbox 包修复随机上下文后在 attempt14 重试，没有修改 pending reader。

### Attempt14：pending 四项完整 GREEN

协调者修复 native inbox 的随机作用域后，四项真实内容核对一次通过。[pending-live-assessment.json](../../artifacts/migrations/2026-09-30/post-update-1.20.0.2/live-1.20.0.2/attempt-14/pending-live-assessment.json) SHA-256 为 `33AF790F4878FFFE7C54ECBC72A51EB664988AF33FCEAFA142CBE2918E5E3234`。四项共同的 played/recipient 为 `29829`，日期 `53168784`，始终 paused；同 case 的两次完整 typed payload、完整 ID/binding 及 native wire 均一致。

| 项 | 完整 pending ID | public/native revision | sender | 回复与真实 marker | 后继 public/native revision |
| --- | --- | --- | --- | --- | --- |
| P1 accept | `318767107` | `4/3` | `65742` | `accepted`；ACCEPT | `5/4` |
| P2 reject | `335544323` | `6/5` | `65743` | `rejected`；REJECT | `7/6` |
| P3 notification ACK | `352321539` | `8/7` | `65744` | `acknowledged`；AUTO_ACCEPT 与 AUTO_ACCEPT_ON_ACCEPT 各一次，ACK 不重放 outcome | `9/8` |
| P4 cost + cleanup | `369098755` | `10/9` | `65745` | `rejected`；COST_REJECT | `11/10` |

四项后继 snapshot 均为 `pending_character_interaction=null`，排队 ACK 与状态结果一致。普通/cost legality 为 accept/reject true、block/ACK false；通知为 auto_accept/notification true、仅 ACK true。P1 至 P3 的十成本全部零；P4 按 gold/prestige/piety/renown/influence/herd/treasury/treasury_or_gold/merit/barter_goods 的顺序严格为 `[100000,200000,300000,0,0,0,0,0,0,0]`。

pending 本矩阵达到 `fixture-definition playset + production native bridge` 范围的 `fixture-live primitive`。外层 attempt14 的 RED 发生在后续婚姻 query，不改变这四个已完成 case 的 GREEN。target absent、send options 为零的 fixture 不覆盖非空 target/options、block、特殊战争路由或其余七类非零成本；完整 effect/semantic decision 与 production OODA 仍独立未完成。attempt09 的原始随机断言与失败 artifact 保留。
