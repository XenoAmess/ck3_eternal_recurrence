# 原生决策研究工具与操作流程

自 2026-09-22 起，新研究专题与新采样方案使用本流程。目标是提前发现无效观测条件、明确校验结果的证明范围，
并让图表、证据记录和即时摘要使用同一份数据。历史专题、ABI 和事件记录保持原样，不要求回填、改分或重判结论。

## 1. 开始研究时先建立问题与观测记录

[native_research_plan.py](../../tools/native_research_plan.py) 使用标准库，提供 `init`、`fingerprint`、`check`、`render`。
工具仅处理本地记录和文件字节，不启动或连接 CK3，不调用 native producer，不提交动作。

从仓库根目录运行以下命令，将示例文件名替换为工作包专用目录中的路径；目录需预先存在。
`init` 生成带空字段的草稿，空字段不能通过后续检查。
`--exe` 可省略；省略后需自行填写已核对的 EXE SHA。指定它也只表示读取并计算哈希，不等于识别了 CK3 语义。

```text
py tools/native_research_plan.py init --topic next-topic --build 1.19.0.6 --output research-plan.json
py tools/native_research_plan.py fingerprint path/to/evidence.json
py tools/native_research_plan.py check research-plan.json
py tools/native_research_plan.py check research-plan.json --for-observation
py tools/native_research_plan.py render research-plan.json --output research-graph.md
```

所有显式输出均排他创建：已有文件拒绝覆盖。作者可以编辑尚在工作的 plan；每次正式采样前保存本次精确 plan 与 check 输出，
下一次使用新的 attempt 文件名/目录，保留之前的记录。报告中的 `plan_sha256` 绑定读到的精确输入。
源文件路径相对于 plan 所在目录解析，也支持显式绝对路径。

填写的内容及其用途：

| 字段 | 填写要求 |
|---|---|
| `question` / `purpose` | 写一个可检验的问题；目的为 `npc-choice`、`player-legality`、`engine-transition` 或 `own-policy` |
| `build` | `version` 与 `exe_sha256`；不能用旧版本偏移代替新版本定位 |
| `actor_kind` / `owner_scope` | `ai`、`human` 或 `engine`，以及具体对象/所有者范围；玩家合法性与 NPC 排名分别研究 |
| `producer` / `caller` / `consumer` | 谁构造或写入、哪个实际入口传递、谁读取并分支；未确认时说明具体缺口，不先起一个确定的语义名称 |
| `producer_trigger` / `cache_lifetime` | 生产触发为 `paused-query`、`daily-tick`、`on-action`、`not-applicable` 或 `unknown`；另写缓存生成/失效条件 |
| `identity_kind` / `identity_lifetime` | `definition-key`、`generation-id`、`process-ordinal` 或 `none`；写清会话、对象与重载后的绑定范围 |
| `mode` | `offline-only`、`paused-snapshot` 或 `passive-runtime` |
| `expected_signal` | 哪个具体值、分支、候选或字段能够回答本次问题 |
| `zero_sample_meaning` | 零行/零调用能排除什么，不能排除什么；不能自动解释为“原生没有候选” |
| `stop_condition` | 明确只读次数、自然运行窗口或已有 runner 的边界，避免无信息重复等待 |
| `runtime_window_ref` | 被动运行采样必须引用独立授权的正式运行方案/窗口；该字符串本身不是授权证明 |

`check` 允许把尚未闭合的采样问题记录为 `observation_plan_issues`，便于先完成静态研究。
开始新采样前使用 `check --for-observation`，下列情况会失败：

- 要回答 NPC 选择问题却配置人类/引擎 actor；
- 要等待新的日更/动作生产，却只配置暂停采样；
- 真实 trigger 尚不明确，或被动运行没有引用已有授权窗口；
- 必填问题、身份、数据链或零样本解释缺失。

读取**已经生成的缓存**与等待**新一轮生产**应分别描述：前者记录真实只读入口及缓存生命周期，
后者需要已有授权运行中的被动观测窗口。检查通过不允许研究者自行推进日期、强制事件、触发脚本或接管游戏会话。
保留现有 README 的纯研究只读边界和各正式 runner 的授权/清理要求。

## 2. 用同一份边记录生成图和证据表

plan 的 `nodes`、`edges`、`evidence`、`cases` 是本工作包的小型记录，不是替换旧知识库的新平台。
`render` 先执行文件/结构检查，再从相同数据生成 Mermaid、边表、采样条件表与证据表；不要手改生成文件。

| 数组 | 每行字段 |
|---|---|
| `nodes` | 唯一 `id`、`label` |
| `edges` | 唯一 `id`、`from`、`to`、`label`、`status`、`evidence` ID 数组；unknown/inference 另需 `open_question` |
| `evidence` | 唯一 `id`、`layer`、`path`、文件 `sha256`、与 plan 一致的 `exe_sha256`、具体 `supports`；实机层另需 `session`、`frame`、`identity` |
| `cases` | 唯一 `id`、`question`、`status`、`evidence` ID 数组；`not-applicable` 另需 `reason` |

边状态沿用 `unknown`、`inference`、`static-confirmed`、`live-confirmed`、`counter-policy`。
未知边自动画虚线，我方策略从原生边数量中排除。案例状态独立为 `pending`、`observed`、`not-applicable`，
不会因为一条边标 live 就把所有案例算成已观察，也不生成“全 CK3 已完成百分比”。

证据层使用以下名称：

| `layer` | 说明 |
|---|---|
| `locator` | 字符串、RTTI、xref 等定位候选；按字节命中的 call/jump 仍须核对指令边界 |
| `exact-build` | 冻结文件/字节身份；单独不能支持字段语义 |
| `source-contract` | 人工审阅并记录的脚本条件或生产/调用/消费链合同；工具核对文件，不代替这项审阅 |
| `offline-fixture` | 对给定模型/冻结输入的实现验证；不证明自然触发或实机成功 |
| `live-observation` | 原有或新取得的具体实机观察文件，另绑定会话、帧、身份 |
| `action-postcondition` | 实际动作之后独立读取的结果文件；queue ACK 不能作为该层证据 |

检查器拒绝重复 ID、悬空引用、哈希/版本不一致；拒绝仅凭 locator/字节校验标静态语义确认，
也拒绝用 offline fixture 标 live 或 observed。**层次和结论依然由作者声明**：工具不解析报告正文来证明其真实性，
不自动判断 static/live 结论正确。输出明确为 `record-structure-and-file-integrity`、
`semantic_correctness_verified=false`、`live_execution_performed=false`。

新字段仍需人工对照写入、真实调用者与读取分支，记录排除过的相似类型/相邻字段。
涉及随机选择时分别记录权重公式、调用顺序和有限观察轨迹；一次选择不证明概率分布。

## 3. 事件修复先回放冻结输入的真实消费者

[replay_vanilla_event_research.py](../../tools/replay_vanilla_event_research.py) 直接调用生产函数：

- `recommend_registered_vanilla_event_option_v1`；
- 有合适 snapshot 时调用 `plan_registered_event_material_postcondition_v1`；
- 有已保存的 `event_selection` 时调用 `evaluate_registered_event_material_postcondition_v1`。

```text
py tools/replay_vanilla_event_research.py --input frozen-event-bundle.json --output replay-attempt-01.json
```

bundle 必填 `context`（原始 current-event context 对象）、`played_character_id`、`snapshot_option_count`、
`ck3_build`、`ck3_exe_sha256`。后两项也可在 context 中明确提供；所有已声明副本必须与 registry 一致。
`snapshot_option_count` 来自冻结 snapshot 的事件计数，不能以可见 options 数量猜测。
工具不自动搜索嵌套 artifact 中“看起来像”的 context，也不伪造缺失的 frame/revision。

可选 `snapshot` 至少含 `snapshot_id`、`revision`、`played_character`（含 `character_id`）；
按现有 outcome 需要保留真实 `stress_points`、`played_character_gold`、`played_character_prestige` 等输入。
context 带日期/native revision/事件 instance 时，snapshot 需提供相应绑定值。
可选 `event_selection` 必须来自已经保存的结果；禁止从脚本效果推造 after 值。
缺 snapshot/物质读取/选择结果时，只记录实际可完成的阶段和 `not_evaluated` 原因；未知事件或不支持的结果不补模拟。

报告绑定输入字节 SHA 与实际生产 Python 文件哈希；policy 结果可为 recommended、blocked 或 not_registered。
即使旧 receipt 重放得到 verified_change，顶层仍为 `offline-replay`、`new_live_evidence=false`，
只表示当前 evaluator 对所供旧记录的计算结果。它不是完整 planner 的同帧准入验证，也不会执行推荐动作。
由此先区分源模型缺口、投影/消费者缺口、缺后置读取与真正动作失败，再选择有新增信息的正式实机窗口。

## 4. 当前事件元数据摘要即时生成

[report_vanilla_event_research.py](../../tools/report_vanilla_event_research.py) 读取生产 registry 的三个 canonical 表，
输出实际工作树数据哈希和 Git HEAD 上下文，避免另建手工清单。它不修改 discovery API 的旧标签或既有分析记录。

```text
py tools/report_vanilla_event_research.py
py tools/report_vanilla_event_research.py --format markdown
py tools/report_vanilla_event_research.py --event-key health.1001 --format markdown
py tools/report_vanilla_event_research.py --namespace health --output health-metadata-01.json
```

默认输出聚合；明确筛选才附事件简表。key/namespace 可重复，同类取并集、两类取交集。
合法空交集的百分比为 null/N/A，未知筛选值报错。默认 stdout，显式输出拒绝覆盖。
摘要分别统计源哈希字段合法性、legacy/非 legacy 观察元数据；**这些不是语义审查完成率、分支覆盖率或实机成功率**。
旧报告作为当时快照保留，后续汇报直接运行工具读取当前值。

## 5. 修改校验器时明确输出范围，保留失败语义

本次在两个既有入口实施了范围输出：

- [建设定义源校验](../../ck3_autonomous_player/native_bridge/research/verify_player_world_building_definition_source_v1.py)：
  保留原成功行，追加 `EVIDENCE_SCOPE` JSON，声明 `exact-build-static-chain`；所有用于拒绝错误输入的 assert
  已换为普通/`-O` 都生效的显式失败判断。
- [婚姻 observer 合同校验](../../ck3_autonomous_player/native_bridge/research/verify_marriage_matchmaking_observer_v1.py)：
  保留原成功行，追加 `repository-contract`；明确不读取 EXE、不验证实机或完整决策语义。

后续新增/修改 verifier 按同样原则说明实际检查和未检查的层次。既有 ABI、偏移、评分、readiness 声明与原生结论未改。
这次没有批量包装其他历史 verifier，也没有把它们的旧成功结果重新评级。

## 6. 离线验证与持续检查

新工具只需标准库；PE verifier 的聚焦测试依赖 `pefile==2024.8.26`，已加入静态依赖。
这些测试已接入现有 Official Runner CI，只验证工具逻辑，不遍历旧专题或要求 CK3。

```text
py tools/test_native_research_plan.py
py -m unittest discover -s tools -p "test_*vanilla_event_research.py"
py ck3_autonomous_player/native_bridge/research/test_native_verifier_evidence_scope.py
```

新方案测试包含 actor/触发冲突、证据层误用、哈希漂移、图表同源和历史输出保护；事件工具测试包含
RED 元数据不晋升、空分母、真实生产函数回放、缺输入、不支持结果与输出保护。拒绝行为的关键子进程也覆盖 `-O`。
PE 测试默认不读游戏文件，两个真实 EXE 扩展检查显式 skip；有已核验本地 EXE 时才传 `--exact-exe` 单独执行。
依赖型检查使用相对 venv；如缺失，须先显式核验并记录主 worktree venv 的解释器和依赖，不静默回退后误报代码失败。
