# 1.20.0.2 当前压力材料 profile 的生产增量

2026-10-02，R11/L11fix 的真实文件读取确认：`death_management.1007` 与 `tgp_travel_events.0030` 的 registry 均 `available`，但 current `analysis.selected_choice_effect_profile.observable_postcondition` 仍为 `null`。先前自然事件包只交付外部独立压力比较器，没有把这个字段恢复进已提交的生产 policy；不能声称冻结 `9ce5e00` 已包含恢复。

这里不把静态原版输入改成无条件预测。`.1007` 的 grief-immunity personal-tenet 条件保持未观测，两个选项的完整 fulfillment 效果也保持未观测。最小增量在 production policy 已匹配合法当前 context、选择原 authored option 后，使用该选项**实际物化的主压力 facet**附上可比较的压力 postcondition。

| exact event / native choice | 必需的当前主压力方向 | 动态 `observable_postcondition` |
| --- | --- | --- |
| `death_management.1007 / 0` | `increase` | `metric=played_character.stress_points`, `expected_relation=non_decreasing`, `material_change_required_for_evidence=true` |
| `tgp_travel_events.0030 / 1` | `decrease` | 同一 metric，`expected_relation=non_increasing`，材料变化仍必需 |

输入使用 `effect_indicators.status=available`、current coverage、`complete_effect_set=false`，并匹配唯一 stress 或 `stress_and_fulfillment` 主压力 facet。secondary fulfillment direction 不参与此恢复。缺失 facet 时保留原 profile 的 `null`；合法无压力效果不被伪造为材料成功，也不阻止原 recommendation 本来允许的事件继续。

动态 profile 标注 `completeness=selected-option-stress-facet-only`、`complete_effect_set=false`，增加 `observation_binding.source=selected_option_same_frame_native_indicator`。原 conditional authored 输入、source hashes、`runtime_material_postcondition_proven=false` 及完整效果未知字段保持原义。真正材料变化仍须由未改的生产 material planner/comparator 消费独立同角色快照，零变化不关闭 M2 材料门。

生产落点是 `vanilla_events/policy.py` 的 `_current_selected_stress_observable_profile` 及现有 selected-profile 返回点的一次调用；不修改 registry 数据、ABI、shared bridge、server 或默认开关。shared Python owner `g2_python_routes` 已应用两处最小增量，生产源 SHA-256 为 `e0095313e6cbff3e54c231828cca9cbc7206232b60548bb7258d8bb2167dcf45`。root 收口提交此静态包；当前 L11 游戏不热更新，不开启新事件批次。下一正常实机阶段使用含此单文件增量的新冻结 Python runtime 后，才验收自然事件材料变化。

只新增一个真实 current-profile 测试方法，含两 key 的 stress、combined 与无 facet 六个分支。它从真实 current registry 取 profile，走候选 production policy，再走未改的 production material planner；**1 method / 6 subtests GREEN**。旧 case、SDK、provider、ABI 均未重跑，准备代理未接触 CK3。

证据与最小 patch 位于 `artifacts/g2-offline-2026-10-01/m2-natural-live-next/`：`r11-pressure-profile-readiness.json` 保留修复前字段，`policy-current-stress-profile-patch.json` 固定候选/输入哈希，`current-stress-profile-candidate-validation.json` 固定唯一新测试结果。实际应用状态与源文件 SHA 由 `current-stress-profile-delivery-result.json` 记录；这份静态增量不增加自然 live 或 G2 完成计分。
