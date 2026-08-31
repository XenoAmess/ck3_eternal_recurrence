# Workforce #360 MCP-first 动作单元

状态：`static-ready + fixture-ready`；`not-live`

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
- 尚无 CK3 paused live artifact，因此状态仍是 `static-ready + fixture-ready`。
