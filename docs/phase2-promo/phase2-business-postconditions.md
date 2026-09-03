# 天朝二期宣传片业务 postcondition 合同

状态：**static/fixture-ready；未产生 live 证据，不提升任何 readiness。**

这份合同补的是“画面里发生的业务结果”，不是按钮有没有按下、命令有没有 ACK、revision 有没有跳。实现位于
`tools/zhongguo_phase2_business_postconditions.py`，正例 fixture 位于
`tools/fixtures/phase2_business_postconditions_v1.json`。

## 四个强语义门

| span | 必须由 paused provider 观测到的结果 | 明确不能替代它的证据 |
|---|---|---|
| `phase2_fact_quota_calibration` | `zg361.1` 校准事件真实可见且 identity-ready；事件绑定 result native revision；scoreboard 的 provider revision 上升、semantic fingerprint 改变、modal 最终可见 | action ACK；仅 public/native revision 上升；只有 scoreboard modal 没有校准事件 |
| `phase2_promotion_compensation` | `zg361pp.147` 与 `zg361comp.1` 都可见且 identity-ready；source/result event、frozen case、晋升选择 receipt、薪酬 receipt 的 owner/subject/cycle/case 完全一致；薪酬 receipt 已 posted | 只看到结果事件；跨 case 拼接；选择 receipt 或薪酬 receipt 只有脚本定义、没有 provider observation |
| `phase2_projects_metrics` | `zg361cp.26` 与 `zg361p3.229` 都可见且 identity-ready；事件、contribution、metrics 的 owner/subject/cycle/case 完全一致；metrics 明确回链同一个 contribution receipt ID | option ACK；不同项目/案件的贡献与指标画面拼接；只有事件名没有贡献 receipt |
| `phase2_cross_cycle_endgame` | `zg361we.356` 与 `zg361we.361` 是同一 terminal case；route-C debt 与 terminal owner/subject/cycle 一致且 `due_cycle=terminal_cycle+1`；charter/default change 在 terminal cycle adopted，并在同一个下一周期 effective | 只看到 361 尾卡；把当前轮 revision 上升当跨周期；没有 debt 与 charter/default-change provider observation |

四个门都要求 provider 明确标记 observed、`action_ack_only=false` 并绑定同一 connection generation / played character。三个 event path
还要求 snapshot ID 改变、public revision 严格上升、native revision 严格上升。scoreboard 是 paused world 上的 provider-local UI 变化，允许
public/native revision 不变，但必须由自己的 `observed_state_revision` 上升和 semantic fingerprint 改变作证。即便 revision 条件成立，只要
evidence 是 ACK-only 或业务 identity/receipt/cycle 不成立，结果仍是 typed `RED`。

## 接线边界

当前 verifier 只消费已经由真实 paused 查询构造好的 evidence packet，不自行读 CK3，也不写文件、推进时间或启动游戏。生产接线时：

1. `capture_fact_quota_calibration` 的 scoreboard action cell 在返回 GREEN 前，把校准事件 identity 及 action 前后 scoreboard state 组装成
   packet，调用 `verify_phase2_business_postcondition(SCOREBOARD_HANDLER, packet)`。
2. 其余三个 event handler 的 postcondition callback 在 source/result event 已分别查询后，再读取对应业务 provider，组装 packet，调用
   dispatcher；只有返回同时满足 `result=GREEN`、`provider_observed=true`、`postcondition_green=true` 才允许 clean hold。
3. verifier 输出应原样保存在 span receipt 的 `provider_postcondition`，不可只抄一个布尔值。

共享 runner 的最小替换形态如下（具体 provider packet builder 尚须由真实查询能力提供，不能用 fixture 代替）：

```python
proof = verify_phase2_business_postcondition(plan.handler, provider_packet)
return proof
```

`provider_packet` 不能由 action ACK、event wait 成功或 revision 差值反推。若真实 provider 尚未发布所需字段，应保持
`provider_postcondition_not_green`，继续补只读观测口，不得用 fixture 或脚本变量名把 span 标成 live。

## Production provider adapter 审计

`tools/zhongguo_phase2_provider_packets.py` 只接收 runner/service 已经规范化的真实查询响应或 action-cell artifact，不读取
`tools/fixtures/phase2_business_postconditions_v1.json`。当前四门状态如下：

| handler | adapter 状态 | 当前真实输入 | 结论 |
|---|---|---|---|
| scoreboard/calibration | 已实现 | verified scoreboard source/action/later artifact + `zg361.1` current-event query | action 必须为 `open`、production capability advertised、independent postcondition verified；event 与 later query 的 snapshot/public/native binding 及 played root 必须一致 |
| promotion/compensation | fail-closed adapter 已实现 | source/result current-event query；业务 query 尚不存在 | 明确返回缺少 `game.command.query-zhongguo-promotion-compensation-postcondition-v1` |
| projects/metrics | adapter 已实现；独立 native provider 与共享接线 static/fixture-ready | source/result current-event query；业务 query 的 reader/serializer/schema、mailbox 第 24 槽、bridge、driver/service/MCP 已实现，默认 adapter 不广告且没有 live 响应 | `game.command.query-zhongguo-projects-metrics-postcondition-v1` 已有 fixed allowlist 与 default-off 共享接线；在 paused live 验收前仍明确 fail-closed |
| cross-cycle endgame | 已实现 | source/result current-event query + action 前后 `query-zhongguo-workforce-collective-snapshot-v1` | 从已验证 `al_case`、`route_c_debt.due_cycle_serial` 与 `charter_gate.prepared_charter_id/adopted_cycle_serial/effective_cycle_serial` 构造，不增加任意变量读取 |

scoreboard 和 endgame 的“已实现”仅表示 adapter 能消费现有 provider；在取得真实输入并通过一次 live 前仍是 static/fixture-ready。
promotion/projects 的 future-query adapter 还会检查 `source_backend_id=native-headless`、readiness、source/result snapshot binding、connection
generation 与 player identity；缺字段或伪装成 fixture backend 都 fail-closed。

### 最小 bridge/query 增量

1. `query-zhongguo-promotion-compensation-postcondition-v1`：固定读取一个 allowlisted promotion case，返回 source/result identity、frozen
   case identity、m147 choice receipt、posted compensation receipt；四者都必须含 owner/subject/cycle/case，并绑定两帧与同一 connection。
2. `query-zhongguo-projects-metrics-postcondition-v1`：独立 reader/serializer/schema 已实现，固定读取一个 allowlisted project case，返回 source/result identity、contribution
   receipt ID/revision/value、metrics 对同一 receipt ID/revision 的回链、metrics revision/dictionary key；所有业务组绑定同一个 owner/subject/cycle/case。共享 mailbox 第 24 槽、bridge handler/result frame/query counter、driver/service/MCP 已按 default-off 接线；source/result event snapshot wrapper 与 paused live artifact 仍是缺口，故当前仍不得产出生产 GREEN。

两项都应采用 product-shaped closed projection，不开放 caller-selected 任意变量名；native unavailable 必须返回具体 reason，不能返回空值加
`ready=true`。

## 静态验证

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" tools/test_zhongguo_phase2_business_postconditions.py
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -O tools/test_zhongguo_phase2_business_postconditions.py
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" tools/test_zhongguo_phase2_provider_packets.py
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -O tools/test_zhongguo_phase2_provider_packets.py
```

测试覆盖四个 GREEN fixture，以及 ACK-only、revision-only、不可见校准事件、scoreboard fingerprint 未变、promotion 跨 case、未 posted
compensation、projects identity/receipt 漂移、endgame carried-cycle/default-cycle 漂移、event frame 漂移、额外字段和 bool/int 混淆等 RED。

## 真实字段施工入口

- promotion：`zg361_pp_m147_receipt_owner/subject/cycle/case/state/route` 是选择 receipt 的权威候选；compensation 仍需从
  `zg361comp.1` 对应 portfolio case 的原生只读投影取得，不能把 `zg361_comp_portfolio_cycle` 单独冒充完整 case identity。
- projects：CP #026 A/B 现在真实签发 `zg361_cp_m26_contribution_receipt_id/revision`；Phase 3 初始化器按当前 owner/subject/cycle 冻结其四元身份、receipt 与 value，#229 A/B 再把同一 ID/revision 回链到 metrics。固定 24 字段 native projection 与共享 bridge 第 24 槽已完成 static/fixture 验证；live paused artifact 与 source/result event wrapper binding 仍是下一入口。
- endgame：现有 Workforce collective provider 已有 route-C debt、rolling history 和 charter lifecycle；真实 packet builder 应从其已验证响应
  取 debt/history/charter cycle，而不是重新读取任意变量。
- scoreboard：现有 scoreboard state provider 提供 `observed_state_revision`、semantic fingerprint 与 widget visibility；还必须同时保留
  `zg361.1` current-event-window identity，二者绑定同一个 result native revision。

这些入口只是下一步施工指向，不是已经取得的 live observation。
