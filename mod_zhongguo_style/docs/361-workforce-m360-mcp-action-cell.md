# Workforce #360 MCP-first 动作单元

状态：`static-ready + fixture-ready + runner-wired`；`not-live`

实现入口：

- `tools/zhongguo_phase2_workforce_action.py`
- `tools/test_zhongguo_phase2_workforce_action.py`
- `tools/fixtures/zg361_phase2_workforce_action/`
- `tools/test_zg361_phase2_workforce_action_fixture.py`
- `tools/test_zg361_phase2_workforce_transition_runner.py`
- `tools/run_zhongguo_acceptance.py`

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
subject paused frame
→ typed current-event context 精确确认 fixture .1 及 owner/subject scopes
→ sole native option 切到 exact owner
→ native paused snapshot 精确确认 played CharacterID=owner
→ typed current-event context 精确确认真实 zg361we.360
→ 从 saved scope 冻结 exact owner/subject
→ 选择 A/B/C，保存 action ACK（只证明命令被接收）
→ typed current-event context 精确确认 fixture .3 及同一 owner/subject scopes
→ sole native option 切回 exact subject
→ native paused snapshot 精确确认 played CharacterID=subject
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
- 默认仍只接受 immediate `zg361we.361`，保持原 API 的逐字默认合同；
- runner 只有在独立 fixture 路径显式传入 allowlist 时才接受 `.3` switch-back，且
  仍不拿该事件或 option ACK 代替 M360 receipt。

### `select_typed_fixture_player_transition`

- 精确核对 fixture event definition、root、named owner/subject saved scopes；
- 要求恰好一个 shown+enabled 的 native option 0；
- option submission ACK 只表示提交；
- 随后轮询原生 paused snapshot，要求日期不前进、played CharacterID 精确变成目标；
- 任一 scope、事件、选项、日期或第三个 CharacterID 漂移均 fail closed。

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

A/B/C 是互斥路线。runner 先保存共同 pre-#360 checkpoint；A、B、C 各自在动作前
独立 restore 同一 size/SHA-256 的 checkpoint，不能在已经提交某一路的案卷里接着点
另一路。每路执行 `subject→owner → real #360 → owner→subject → provider`，最后再恢复
共同基线。恢复 PID、连接代次、CharacterID、checkpoint hash 与 route evidence 均由
主 runner 保存和核对，本 helper 不伪造这些边界。

动态加载 fixture 需要一次额外 activation restore。因此 Workforce 子谱系固定为：

```text
base restore 后的 subject PID
→ fixture activation restore
→ route A restore
→ route B restore
→ route C restore
→ final baseline restore
```

连同此前 phase-two base restore，完整受管 session 是 7 个互异 PID、6 次 restart，
connection generation 必须逐次 `+1`。cleanup 与 liveness 使用完整谱系，不再把最终
进程误认成第二个 PID；即使 Workforce 中途 RED，runner 也会保存已发生的 partial /
recovery restore 谱系供 shutdown 逐 PID 核对。

## 4. 当前验收

2026-09-01 静态/fixture 验收：

- 动作 helper normal Python：10/10 GREEN；
- 动作 helper `python -O`：10/10 GREEN；
- fixture isolation contract：normal / `python -O` 均 GREEN；
- runner transition/restore 专测：normal / `python -O` 均 4/4 GREEN；
- 全量 `test_run_zhongguo_promo_capture.py`：normal / `python -O` 均 GREEN；
- 覆盖 A/B/C option ACK、三路线业务事实、显式身份接缝、缺接缝 blocker、错误
  receipt 不得被 ACK 掩盖、received-self ACL、有界时间推进，以及 active event
  禁止自动点击；另覆盖独立 fixture 动态加载、一次 activation restore 与共享
  checkpoint 的 A/B/C/final 四次 restore、7-PID cleanup/liveness、真实 helper 默认
  allowlist 不漂移；
- 本轮按约束未启动 CK3，尚无 paused live artifact，因此只到
  `static-ready + fixture-ready + runner-wired`，不提升 live readiness。

### 4.1 主 batch 已接好的动作矩阵

`--phase2-live-batch` 现已在完成既有 Incident、B2、AI-owned 动作及四域
pre-save/post-restore 查询后，进入 Workforce #360 专用矩阵。它保存：

- `08a_phase2_workforce_action_fixture_install.json`；
- `08_phase2_workforce_m360_gameplay_action_cell.json`；
- fixture source/target tree hash 与 isolated `enabled_mods` 前后值；
- exact owner（seed selector）与 received-self subject（恢复后的 played character）；
- activation/shared checkpoint、A/B/C/final restore 的 hash、PID、generation、lifecycle；
- 每路双向 typed transition、真实 `zg361we.360` identity、option ACK 与 subject-side
  provider postcondition；
- 失败后的 best-effort baseline recovery 及已发生的 partial session lineage。

Workforce 已从 `PHASE2_MISSING_GAMEPLAY_ACTION_CELLS` 移除；当前主 batch 的动作缺项
只剩 scoreboard。此处仍只是 runner-wired，必须待首次 CK3 paused artifact 验证事件
排队顺序、动态加载与 7-PID 清理后才可写 `fixture-live`。

### 4.2 为什么现有切人路径不能复用

当前公开 `GameplayBridgeService` / native action surface 仍没有通用、revision-bound 的
exact CharacterID 玩家切换命令。这里没有放宽 seed fixture；它继续显式禁止
`set_player_character`，只负责用真实人物和 shipped public effects 生成 seed。

普通一期验收 fixture 虽然包含一次 `set_player_character`，但它绑定“宋帝 → 既定排序
尾部官员”的固定宣传编排，依赖 fixture flag、延时事件与测试流程；它既不接受 #360
saved-scope subject，也不是 MCP 可调用的通用切换动作。把它当成 owner→subject
接缝会把测试编排冒充产品事实，因此 runner 明确记录
`legacy_fixture_switch_accepted=false`，不调用它。

采用的窄接缝是第三个、独立的 acceptance-only mod：scripted widget 只在真实 AL
state 4 与中央 source 就绪时召唤 typed `.1`；`.1` sole option 切到 owner 并排隐藏
carrier；carrier 先调用 shipped public resume effect 排真实 `zg361we.360`，再排 typed
`.3`；每路选完真实 #360 后，runner 精确选择 `.3` 切回 subject，再读 provider。

该 fixture 有以下硬边界：

1. 与 seed fixture 为不同目录、namespace、descriptor；不修改 seed 的
   “禁止 `set_player_character`”合同；
2. 不写/删任何 `zg361_*` 产品变量，不造人、不造头衔、不造关系；业务 mutation 只由
   shipped public effect 与真实 #360 options 完成；
3. 没有决议、没有坐标/OCR/控制台入口，两个切换只能通过 current-event MCP 的 exact
   option 触发；
4. 只在 phase-two Workforce stage 动态追加到一次性 userdir；普通 acceptance/promo
   不加载，release builder 不引用，staging/宣传素材不得包含。
