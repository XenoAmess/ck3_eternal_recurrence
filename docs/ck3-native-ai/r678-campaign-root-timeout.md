# R678 campaign-root application-main timeout 取证

日期：2026-09-14（Asia/Shanghai）

工作包：`G2-M3-R678-DIAG1`

状态：**RED 保留**

范围：只读比较 R676、R677、R678 live artifact；没有启动或操作 CK3。

## 结论

R678 的首个失败发生在 campaign-root request 已进入 application-main mailbox 之后、executor 开始之前。8 秒 queued wait 到期时，mailbox 仍处于 `queued`，取消操作成功，因此 native bridge 返回 `timeout_cancelled_before_execution` 对应的 `application-main campaign-root query timed out`。本次没有执行 campaign-root reader，没有生成 campaign-root payload，也没有进入序列化或 partial-readiness 判定。

这次 RED 因而是 application-main 调度/取件 RED。artifact 能证明“已排队但未被 application-main executor 取走”，不能进一步证明为什么当时没有新的合格 pump。尤其不能把本次 RED 归因于 selected-game-rule 读取、serializer、载荷大小或刚引入的 partial contract。

同时存在一个确定、独立的下一道合同缺口：`campaign_root_context_v1_mailbox.cpp` 的 `typed_available` 仍要求聚合 `readiness.ready == true`。R678 候选 reader 的合法 partial 结果是顶层 `available`、`selected_game_rule_tokens_ready == false`、聚合 `ready == false`。一旦 executor 真正运行，旧 mailbox gate 会把这个合法 partial 结果改写成 `internal_error` unavailable。它不是本次 timeout 的原因，但必须在下一次 live replay 前修复，否则调度恢复后仍会撞到第二个 RED。

## 冻结输入

三轮使用相同的角色、日期和 checkpoint：

- 角色：`32904`
- episode：`native-32904-ab7cd2073b94`
- `date_raw`：`53789952`
- checkpoint SHA-256：`223E4C65FC618D0256FB2078CDD3A94EC3FB3FDABAB7382D848A32EC33716092`
- CK3 exact build：`1.19.0.6`
- CK3 EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

R678 候选：

- 上游 commit：`764e1c4fe0a33c670a4563c14ec98859390a091d`
- DLL SHA-256：`68E3746D35601C3197165A91ED85C5E5AA5C362C5EEF882123487E52B2ED2B76`
- PID：`155628`
- artifact：`Z:\ck3_mod_rewrite_process_assets\g2-m3-r678-partial-rule-tokens-candidate`
- `native-auto-run.log` SHA-256：`51D66A8DBC032B858B9C62351FF4FE30993CA2A6FE5863B2A65103B1111456BF`
- final `driver-state.json` SHA-256：`2CE3FA573E6A52AB586AD8E743FC3AFF09EBB9F902C0E3202C4DAA78FDE79BFD`

对照 artifact：

- R676：`Z:\ck3_mod_rewrite_process_assets\g2-m3-r676-bounded-succession-36469f2`
- R677：`Z:\ck3_mod_rewrite_process_assets\g2-m3-r677-celestial-scope-3f80e0f`

## command 621 差分

| 轮次 | command 621 | command 结果 | campaign-root payload | `query_sequence` | 首个业务阻点 |
|---|---|---|---|---:|---|
| R676 | `query-campaign-root-context-v1` | `ok: true` | typed `unavailable`，原因 `council_unavailable` | 1 | `turn_bundle is unavailable` |
| R677 | `query-campaign-root-context-v1` | `ok: true` | typed `unavailable`，原因 `selected_game_rule_tokens_unavailable` | 1 | `turn_bundle is unavailable` |
| R678 | `query-campaign-root-context-v1` | `ok: false` | **没有 payload**；只有 104-byte driver error 字符串 | 无 | `application-main campaign-root query timed out` |

为便于比较，对 R676/R677 `driver-state.json` 中 command `result` 对象按 UTF-8 compact JSON 重新编码，分别为 4,783 和 4,819 bytes。这不是 wire frame 的原始长度，只说明两轮都留下了完整、可解析的 typed result。R678 没有 `result` 对象，不能从本轮推断新 available payload 的实际 wire 长度。

R676 与 R677 的 artifact 没有保存单条 command 的开始/结束时间，所以只能确认它们均在首个 auto turn 内完成并发布了 `query_sequence: 1`，不能伪造毫秒级延迟。R678 同样没有独立 request timestamp，现有可核验时间如下：

- session 开始：`2026-09-14T04:42:48.524225+00:00`
- 首个 blocker 记录：`2026-09-14T04:47:17.337295+00:00`
- session 完成清理：`2026-09-14T04:47:21.969251+00:00`
- native queued wait 常量：`kCampaignRootContextV1QueuedWaitBudgetMilliseconds = 8000`

依据 8 秒 wait 与 blocker 时间，request 的 queued wait 大约从 `04:47:09.337Z` 持续到 `04:47:17.337Z`；这是由固定 budget 反推的近似区间，不是 artifact 直接记录的 request 时间戳。约 273 秒的整轮耗时主要包含 CK3 启动和 checkpoint 恢复，不能整体算成 query latency。

## mailbox 生命周期证据

R678 在进入首个 auto turn 前记录的 mailbox 状态为：

```json
{
  "installed": true,
  "stop": false,
  "failure": 0,
  "ready": true,
  "executor_submission_enabled": true,
  "date_raw": 53789952,
  "paused": true,
  "executed_requests": 0
}
```

R676 与 R677 在同一位置也记录了相同的布尔状态和 `executed_requests: 0`。该对象是 command 前的 readiness snapshot，只能证明 mailbox 已安装、没有已知 failure、已观察到可提交的 paused owner boundary；它不是 timeout 后的最终 mailbox dump。

代码路径进一步收紧了结论：

1. 如果 `TrySubmitMainThreadQueryV1` 没有返回 `submitted`，bridge 会返回 `executor is unavailable`、`boundary is not ready` 或 `executor is busy`，不会返回本次 timeout 文案。
2. 提交成功时，mailbox 发布 ticket 并将状态置为 `queued`。
3. `WaitForMainThreadQueryV1` 到 8 秒 deadline 后调用 `CancelMainThreadQueryV1`。
4. 只有 `queued -> cancelled` 的 compare-exchange 成功，wait 才返回 `timeout_cancelled_before_execution`。
5. 如果 application-main 已把状态改为 `executing`，返回值会是 `timeout_executor_already_running`，文案也会变成 `executor is still running`。

R678 的错误字符串只可能由 `timeout_cancelled_before_execution` 分支产生。因此 executor invocation 为零是由状态机语义确认的，不依赖对日志文字的猜测。

artifact 没有保存 timeout 后的 `state`、`published_sequence`、`completed_sequence`、`pump_epochs`、`paused_owner_verified_pump_epochs` 或 `executed_requests`。也没有 campaign-root 专属的 begin/end publish diagnostic。现有 `heartbeat_sequence: 983` 说明 worker/pipe 心跳持续存在，不能代替 application-main pump 计数。缺少这些字段时，不能判断“提交后的 8 秒内没有任何 pump”“有 pump 但不满足执行边界”或“hook 没在该阶段收到合格入口”三者中的哪一个。

## 被排除和仍待确认的假设

| 假设 | 判定 | 证据 |
|---|---|---|
| runner 的 21,600 秒总 deadline 到期 | 排除 | 首个 blocker 使用 native campaign-root timeout 文案，整轮仅 273.445 秒。 |
| 300 秒 readiness timeout 到期 | 排除 | readiness 已成功取得，首个失败阶段是 `opaque_auto_turn`。 |
| request 未提交 | 排除 | 未提交会走 submit error；本次文案只对应提交后的 queued wait。 |
| executor 已运行但 reader 卡死 | 排除 | 那会得到 `timeout_executor_already_running`，本次为 queued request 成功取消。 |
| reader 返回了 partial 后被 serializer 拒绝 | 排除（仅本次） | executor 未运行，command history 没有 campaign-root payload。 |
| 新 payload 太大或 pipe 写入超时 | 排除（仅本次） | 本次没有进入 result serialization/write；R676/R677 均成功发布约 4.8 KB 的 result 对象。 |
| application-main 在提交后没有取走 queued request | **确认** | `timeout_cancelled_before_execution` 的唯一状态机来源是 deadline 时仍可执行 `queued -> cancelled`。 |
| 为什么没有取走 request | 未查明 | artifact 缺少 timeout 后 pump epoch 和 owner-proof 诊断。 |
| mailbox 会接受合法 partial available | **确认存在缺陷** | `typed_available` 仍额外要求 `query->result.readiness.ready`；新 partial contract 明确允许顶层 available 且聚合 ready false。 |

## 最小修复入口与下一轮验收

先修复确定的 mailbox 合同缺口：`typed_available` 应接受经过 campaign-root v1 合同校验的顶层 `available` partial，而不再把聚合 `readiness.ready` 当成顶层 available 的必要条件。补一个 mailbox fixture，固定“selected rule tokens 不可用、其余 core 可用”的结果必须以 `completion=completed` 返回，不能改写为 `internal_error`。

随后只做一次短差分 replay，仍使用 3-turn bound 和同一 checkpoint：

- 若 request 被 executor 取走，要求观察到顶层 `available`、celestial council typed unavailable、`selected_game_rule_tokens_ready: false`，并继续生成 partial turn bundle 与 succession expectation。
- 若再次得到 `timeout_cancelled_before_execution`，保持 RED，并在 native command failure frame 中补充一次性必要诊断：request enqueue/deadline 时间、wait enum、ticket sequence、timeout 后 mailbox state、pump epochs、paused owner proof epochs、executed/completed sequence。用这些字段区分无 pump 与边界不合格，再修 drain 入口。

不应通过无限延长 8 秒 budget 或反复长跑来掩盖本次失败。R676/R677 已证明同一 checkpoint 的 campaign-root request 可以完成；R678 是一次真实调度 RED，下一轮只需验证 mailbox gate 修复和一次有界重放。

## 验收边界

R678 没有推进游戏日期，没有提交 gameplay command，没有捕获 succession expectation。cleanup 为 GREEN，进程树归零。该轮不能作为 partial campaign-root、partial turn bundle 或 natural succession 的 live 通过证据；它只冻结了 application-main queued timeout 和后续 mailbox gate 漏改两项证据。
