# active-scheme semantic action v1（private）

状态：`static-ready private core`。本合同绑定 CK3 `1.19.0.6` 与
`ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
它消费 SCHEME4 binder 经 SCHEME3/SCHEME2 产生的、已复制且不含 native pointer 的
`ActiveSchemeStateV1PrivateObservation`。本工作包没有接入 shared heartbeat、公共
bridge/schema/MCP，也没有启动 CK3；因此不能标记为 production-live action。

## v1 动作范围

只允许通过现有 character-interaction validator 与 send-command 路径启动：

| interaction | 后置 scheme type | target | starter package |
| --- | --- | --- | --- |
| `sway_interaction` | `sway` | character | 不适用 |
| `start_murder_interaction` | `murder` | character | 必须恰好选择 `agent_focus_balance`、`agent_focus_success`、`agent_focus_speed`、`agent_focus_secrecy` 之一 |

core 不直接写 `CSchemeManager`/`CActiveScheme`，也不直接执行
`CStartSchemeEffect`。生产调用者只有在 exact-build character-interaction command
route 完整绑定后才能设置 `character_interaction_route_bound`；离线 fixture 使用独立的
`offline_fixture` 门。

## 提交事务

1. 请求固定 request ID、actor、character target、interaction、SCHEME4 capture epoch、
   container generation 与 date。
2. 读取一次 `active_scheme_state_v1`，核对 actor、轮次、容器代际，并拒绝已有同
   owner/type/target 的 active instance。
3. 在相同 paused epoch/date 读取 character-interaction precondition，核对 actor、target、
   interaction 与由 allowlist 推导的 scheme type。
4. 要求重新求值得到 `is_shown=true`、
   `is_valid_showing_failures_only=true` 和 `can_start_scheme=true`。murder 还要求原版四项
   send option 已确认为互斥，且请求选择与 validator 结果一致。
5. success/maximum-success/secrecy preview 各自必须明确为 `available` 或
   `explicitly_unavailable`；`unresolved` fail-closed。available 数值必须落在 0..100，
   success 不得高于 maximum。
6. 提交前再次读取 active observation 与全部 precondition；任一值变化就拒绝，submit
   调用次数为零。
7. 只调用一次 submit callback。返回 true 只产生
   `submitted_verification_pending` ACK，不代表游戏动作已生效；返回 false 记录 typed
   `submit_rejected`，同一事务不重试。

## fresh receipt

`VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh` 自行通过 SCHEME4 observation
callback 重读，不接受调用者塞入任意 post snapshot。post capture epoch 必须严格大于
pre capture epoch，played character 必须未变。验收成功需要恰好一个此前 identity 集合
中不存在的 active instance，且 owner、由 interaction 推导的 type、target kind 和 target
ID 全部匹配。ACK、旧实例、同轮次快照、错误目标或多个匹配实例都不能变成成功 receipt。

后置失败保留 `red`，并使用 `post_observation_unavailable`、
`post_observation_not_fresh`、`post_actor_changed`、`postcondition_missing` 或
`postcondition_ambiguous`。它们不能静默转为 warning，也不能由 submit ACK 覆盖。

## 仍需完成

- shared heartbeat/owning-thread glue 必须把 SCHEME4 observation callback 和已经冻结的
  character-interaction validator/send-command ABI 接到本 core。
- 先以 paused sway 验证 basic start 的新 instance 后置条件，再以 paused murder 验证
  complex scheme 与 starter package；两个 live artifact 都缺失时保持 static-ready。
- 公共 schema/MCP 只有在上述生产接线与 paused live 均闭合后才能发布 action readiness。
