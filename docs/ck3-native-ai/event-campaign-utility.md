# 原版事件的 bounded campaign objective 与 utility

## 目的与状态

G2-M2 的最小验收要求 planner 对三个自然 production 事件明确记录目标和 utility，且至少两个多选事件不能靠固定首项继续。
当前三个 exact-build 目标事件现已发布 `xar.ck3.vanilla-event-campaign-utility/v1`，状态为
**source-structured / static-ready / live=false**。

该 profile 是 source-reviewed ordinal comparison。它回答“在这个已冻结事件和当前 bounded continuation 目标下，为何选择这一项”，
不把压力、金币、XP、trait 与时间成本强行换算成一个未经实测的数值。`cross_event_numeric_score` 因此必须为 `null`，
`calibration_status` 必须为 `not_calibrated`；planner 继续报告 `semantic_optimal=false`。

## v1 字段

```json
{
  "schema": "xar.ck3.vanilla-event-campaign-utility",
  "schema_version": 1,
  "selected_native_option_index": 1,
  "objective_id": "reduce_stress_without_delaying_travel",
  "comparison_kind": "source_reviewed_ordinal",
  "selected_rank": 1,
  "rank_count": 2,
  "selected_utility": {
    "material_direction": "benefit",
    "outcome_variance": "bounded",
    "persistent_state_risk": "none_authored",
    "time_cost": "none_authored"
  },
  "alternatives": [
    {
      "native_option_index": 0,
      "rank": 2,
      "reason": "source-reviewed reason"
    }
  ],
  "cross_event_numeric_score": null,
  "calibration_status": "not_calibrated",
  "decision_scope": "bounded_timeline_continuation"
}
```

`selected_rank=1` 表示当前 profile 下的首选，不代表效用值 `1`。`rank_count` 是 source 中被比较的合法路线数量；单选事件使用
`comparison_kind=sole_legal_route`、`selected_rank=rank_count=1` 和空 alternatives。`selected_utility` 使用离散事实描述结果方向、
方差、持久状态风险与直接成本，不承担未观测 runtime magnitude。

## 三个目标事件

| event | objective | source-reviewed choice | ordinal basis |
|---|---|---|---|
| `tgp_travel_events.0030` | `reduce_stress_without_delaying_travel` | authored2/native1 | 压力只减不增；避免五日延误和随机 duel 的 XP/trait/stress 分支 |
| `trait_specific.8001` | `increase_liquid_reserve_without_random_persistence` | authored2/native1 | 金币严格增加；避免随机永久 herbalist、十年 modifier 或无效果 |
| `death_management.1007` | `acknowledge_unavoidable_heir_death_event` | authored1/native0 | 唯一合法路线；接受不可避免的压力成本以继续 timeline |

前两个多选事件都选择第二个 native row，直接排除固定首项策略。第三个事件明确标记为 forced route，不把不可避免的负效用包装成
偏好胜利。

## Planner 与查询边界

现有只读 `ck3_query_vanilla_event_knowledge_v1.analysis` 加法发布 profile。registry policy 只在 event contract、scope、option
projection 与 selected native index 全部匹配时复制它，并输出：

- `campaign_utility_ready=true`；
- `campaign_utility_profile`；
- planner 顶层 `event_campaign_utility`；
- active-event summary 中相同的 readiness 标志。

未知事件、投影漂移或 profile/native index 不一致时不会生成 utility。没有 profile 的其它已登记事件仍可沿原有 bounded continuation
路径处理，但不能据此声称目标评分已完成。该数据不新增 native ABI、mailbox、MCP tool 或游戏动作。

## 完成边界

这项工作关闭三个目标事件的 **静态目标/utility 解释输入**。G2-M2 仍必须在 production 中对三个事件各完成一次
recommendation → action → instance advance → material postcondition，才能成为 production-live loop。通用 event-context-v2 effect
visitor、更多事件、基于实时压力/财政/继承风险的动态目标切换，以及跨域数值校准属于后续扩展；它们不能被当前 ordinal profile
冒充，也不需要阻断这三个 exact event 的最小 live 验收。

## 聚焦验证

- 三个 record 的 query/profile JSON 投影；
- registry 的 native-index 绑定、objective、rank 和 null numeric-score；
- `one-life-turn-v1` 的 `event_campaign_utility` 计划投影；
- normal/optimized 各 `26/26` GREEN；
- `py_compile` 与 `git diff --check` GREEN；
- 未启动 CK3、录屏器、注入器或桌面输入。
