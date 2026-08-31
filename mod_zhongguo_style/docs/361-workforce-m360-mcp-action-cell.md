# Workforce #360 MCP-first 动作单元

状态：`static-ready + fixture-ready + runner-fail-fast-wired`；`not-live`

实现入口：

- `tools/zhongguo_phase2_workforce_action.py`
- `tools/test_zhongguo_phase2_workforce_action.py`

本单元只负责把 #360 的玩家动作与 Workforce v1 只读事实接成一份可供 runner
调用的严格接口。它不修改产品脚本、不实现新的 provider、不使用 OCR、坐标或日志
猜测，也不把命令 ACK 当作业务完成。

## 1. 两种玩家身份不能混写

现有产品与 provider 有两个都正确、但不同的玩家绑定：

1. `zg361we.360` 的 root 是 AL case owner。事件 trigger 要求 `is_ai = no`、
   `this = scope:zg361_we_al_owner`，所以点击 A/B/C 时玩家是主持集体校准的 owner。
2. `query-zhongguo-workforce-collective-snapshot-v1` 是 received-self 查询。它把
   当前 `played_character_id` 固定为 AL case subject，只允许 caller 传入 owner 做
   equality filter。

因此同一个未切换玩家身份的暂停帧不能同时满足“点击 #360”和“以 subject 身份读取
该 #360 的业务回执”。正确的闭环是：

```text
owner paused frame
→ typed current-event context 精确确认 zg361we.360
→ 从 saved scope 冻结 exact owner/subject
→ 选择 A/B/C，保存 action ACK（只证明命令被接收）
→ runner 用真实、受管的身份/会话接缝切到 exact saved-scope subject
→ subject paused frame
→ Workforce v1 查询 owner equality filter
→ 证明 M360 receipt、路线对象、三周期历史与 #361 ready gate
```

若 runner 没有提供 owner→subject 接缝，组合 helper 固定返回：

```text
received_self_provider_requires_subject_player_rebind
```

这是一项产品编排/MCP 会话阻塞，不是可以用 ACK、OCR 或合成 CharacterID 绕过的
测试细节。

## 2. 接口与证据边界

### `submit_m360_route_action`

- 要求 paused + map-ready；
- 通过 `current_event_window_context_v1` 精确核对 definition key
  `zg361we.360`；
- 要求 root、played character、saved `zg361_we_al_owner` 三者一致；
- 从 saved `zg361_we_al_subject` 冻结 subject，禁止 caller 自报 subject；
- 要求三个可见、可用选项的 native index 严格为 `0/1/2`，按其选择 A/B/C；
- 只返回 `result=ACKED`，并明确 `business_receipt_claimed=false`；
- 若 immediate #361 出现，只把它记录为产品编排证据，不拿它代替 M360 receipt。

### `prove_m360_postcondition`

- 要求 paused + map-ready 且 played character 精确等于上一步 subject；
- 每次以当前 public revision 调用 Workforce v1；
- receipt 必须回连同一 owner/subject/cycle/case，`state=4`，choice 与 ACK 路线相同；
- A 路证明三 cohort 的 exception/quota/manager-cost 守恒；
- B 路证明 forced/quota 守恒、零 manager cost 与非批准语义；
- C 路证明不 materialize collective/cohort，只生成 due-cycle=`cycle+1` 的 debt；
- 三个历史槽必须按 cycle 严格递增，尾槽回连当前案，槽内 357/358/359
  receipt id/hash 互异；
- #361 gate 必须为 `ready`，evidence count=3、未消费、report/charter id 为正，
  effective cycle 精确为下一周期；
- 只有上述业务事实全部成立才返回 `GREEN`。

可选的 maturation loop 每步最多推进一次被观察到的日期变化：先 speed 1、resume，
日期变化后立即 pause，再发下一次 Workforce 查询。遇到任何 active event 会停止并
返回 blocker；helper 不会代替 runner 猜选无关事件。

## 3. A/B/C 批量矩阵

A/B/C 是互斥路线。正式实机矩阵必须分别从同一个权威 pre-#360 seed 的独立恢复现场
运行，不能在已经提交某一路的案卷里接着点另一路。`run_m360_action_and_postcondition`
只执行单一路线，并要求 runner 显式提供 `subject_service_factory`。恢复 PID、连接代次、
CharacterID 与 save lineage 仍由主 runner 保存和核对，本 helper 不伪造这些边界。

## 4. 当前验收

2026-09-01：

- normal Python：8/8 GREEN；
- `python -O`：8/8 GREEN；
- 覆盖 A/B/C option ACK、三路线业务事实、显式身份接缝、缺接缝 blocker、错误
  receipt 不得被 ACK 掩盖、received-self ACL、有界时间推进，以及 active event
  禁止自动点击；
- 尚无 CK3 paused live artifact，因此动作 helper 仍是
  `static-ready + fixture-ready`；主 runner 只新增诚实的 fail-fast 接线，不提升 live
  readiness。

### 4.1 主 batch 的动作前 RED

`--phase2-live-batch` 现已在完成既有 Incident、B2、AI-owned 动作及四域
pre-save/post-restore 查询后，进入 Workforce #360 专用 gate。该 gate 保存：

- `08_phase2_workforce_m360_gameplay_action_cell.json`；
- exact owner（seed selector）与 received-self subject（恢复后的 played character）；
- helper 入口、期望事件 `zg361we.360`、A/B/C 三条未运行路线；
- `gameplay_action_executed=false`、`checkpoint_created_for_workforce=false`、
  `helper_invoked=false`；
- 两个独立缺口：`exact_owner_subject_player_transition` 与
  `same_checkpoint_three_route_restore_lineage`。

这是 **pre-mutation typed RED**：当前 batch 不会因为缺接缝而先点某一路，再发现无法
以 subject 身份读回执。已有三项动作和四域恢复证据仍原样保留；Workforce 继续留在
`PHASE2_MISSING_GAMEPLAY_ACTION_CELLS`，scoreboard 也仍为 RED。

### 4.2 为什么现有切人路径不能复用

当前公开 `GameplayBridgeService` / native action surface 没有 revision-bound 的 exact
CharacterID 玩家切换命令。phase-two seed fixture 还显式禁止
`set_player_character`，只负责用真实人物和 shipped public effects 生成 seed。

普通一期验收 fixture 虽然包含一次 `set_player_character`，但它绑定“宋帝 → 既定排序
尾部官员”的固定宣传编排，依赖 fixture flag、延时事件与测试流程；它既不接受 #360
saved-scope subject，也不是 MCP 可调用的通用切换动作。把它当成 owner→subject
接缝会把测试编排冒充产品事实，因此 runner 明确记录
`legacy_fixture_switch_accepted=false`，不调用它。

此外，当前 phase-two lineage 的冻结合同是一次 save、一次 restore、两个 PID，且这次
restore 已用于 B2/AI-owned 后恢复。#360 的 A/B/C 互斥矩阵需要另一个共同的
pre-`zg361we.360` checkpoint，并让三条路线各自从该 checkpoint 独立恢复；现有
lineage 不能靠重复利用一条已消费的两 PID 证据来声称满足。

下一可施工接缝应提供以下最小真实能力：

1. 从 typed owner/subject scope 出发，通过 MCP 可观测、可选择的正式动作把玩家精确
   切到 owner，再在 option ACK 后精确切到 subject；每次切换后必须由 native
   `played_character.character_id` 验证，不能相信动作 ACK；
2. 保存一个共同 pre-#360 checkpoint，A/B/C 各自独立恢复并保存 PID、connection
   generation、checkpoint hash 和 route evidence；
3. 每一路只在 subject-side provider 同时证明 M360 receipt、路线对象、三周期历史和
   #361 charter ready 后 GREEN；最后再恢复冻结基线；
4. 全程不用 OCR、坐标、控制台或测试决议。若采用 acceptance-only 动作 fixture，它
   必须与 seed fixture 分离，并以 current-event MCP + exact option 暴露 typed scope
   切换，而不是增加不可审计的后台捷径。
