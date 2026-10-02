# H2743 法理县投降条款 V2：动态作用域与因子只读门禁

本页接续 [V1 baseline 读口](h2743-dejure-exit-read-port-plan-2026-09-28.md)，只做 CK3 `1.19.0.6-steam23530548` 的静态研究。H2743 WarID `16777231`、Robert `29829` 主守方、Landolf `30097` 主攻方、CB `individual_county_de_jure_cb` index `17`、目标 TitleID 列表 `[2128]` 是查询身份；它们不是投降后的转移清单。本轮没有启动 CK3、调用 effect／preview 或提交退战。

## 精确构建新证据

[可重跑提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_title_scope_resolution_gate.py)只读取 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的磁盘字节。[V2 JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_title_scope_resolution_gate_v2_1_19_0_6.json) SHA-256 为 `6529A76BA638318863021D404C8236F765BB99449C6B516803C769209A10C23F`；前一条仅冻结标题解析器的 [V1 回执](../../ck3_autonomous_player/native_bridge/research/dejure_title_scope_resolution_gate_1_19_0_6.json) 保留为历史中间结果。

| 路径 | 已证的直接指令 | 尚不能推出 |
| --- | --- | --- |
| `scope:target` | setup effect 的预览调用点 `0x2E9FB8A/98` 与执行调用点 `0x2E9F5AF/B6` 都把 effect `+0x260` 的 `CJominiScriptScopeObject<CLandedTitle>` 交给 `0x995CB0`；解析器在 `0x995CD0` 调 `0x336AB40`，随后要求结果 tag `5` 并比较目标 Title 的 packed ID。 | H2743 本次作用域求值一定返回 Title `2128`；解析器可作为独立、无副作用的 live getter。 |
| 动态作用域遍历 | `0x336AB40` 在 `0x336AC47` 与 `0x336AC8B` 对脚本节点分别调用虚表 `+0x30`、`+0x20`。 | 这两条动态分派的真实目标、传递写集合、调用上下文生命周期和无副作用性。不能仅凭 `0x995CB0` 自身主要读取来批准调用整个解析链。 |
| `cb_prestige_factor` 输入路径 | 执行函数 `0x2E9F70B` 调共享 helper `0x2E9FF30`；`0x2E9F710` 读取其写入的栈上计数，`0x2E9F717` 乘以 Q100000 比例 `100000`，`0x2E9F722` 调 `0x2E9F2C0`，后者在 `0x2E9F319` 继续调 `0x33590D0`。 | helper 的计数在 H2743 的业务语义、最终写入的 factor 原值、是否有后续覆盖。不能把列表长度 1、历史 R0197 的 −30 威望或这个中间计数直接写成 `F`。 |

精确脚本在 `target_titles` 循环中仅保存临时 `target`，在循环**外**才调用一次 `setup_de_jure_cb(title=scope:target)`。因此即使当前战争目标列表只有 `[2128]`，仍需证明循环结束后的临时作用域如何绑定并成功解析。脚本在 `setup` 后调用 `resolve_title_and_vassal_change`；既有 [静态追踪](war-termination-war31-static-followup-2026-09-27.md)只确认若干 change 数组的 8/12 字节追加边和构造时 type `0`，没有穷尽传递写集合，也没有读到 resolve 时 type、数组字段业务含义或最终提交操作。

## V2 只读生产合同

V1 的同帧 war/CB/主将/目标和双方七种**行动前余额**继续可用。V2 只有在下列每个来源分别闭合后才能逐域增加字段；未闭合时保留 `null` 和明确原因，绝不把缺失当 `0` 或空操作集。

1. **目标作用域**：静态解析 `0x336AB40` 在此 effect 的实际虚方法目标及完整传递写集合，并证明可从现存暂停战争状态构造有效只读上下文。若无法证明，就不要调用 `0x995CB0`／`0x336AB40`。可以改为从已验证的原生只读战争上下文中读取**已存在**的作用域求值结果，但必须绑定 effect 身份、WarID、原生 revision、返回 TitleID 和对象 generation，再双采样；单纯 `targeted_title_ids` 仍只是输入列表。
2. **威望因子**：先证明 `0x2E9FF30` 输出计数的具体业务含义、`0x2E9F2C0→0x33590D0` 如何存入 identifier `82`，以及有无后续覆盖。可实现经审计的纯计算器，用同帧来源输入独立求 `F` 并与至少一个独立授权的真实结果校验；或者读取游戏状态中**已存在**的同帧 factor 槽。不能为取得 F 在原游戏态执行 `setup`，也不能重开旧版崩溃的广义 loaded-effect preview。任一条件缺失时 `cb_prestige_factor=null`、`factor_unavailable_reason=setup_count_semantics_or_storage_unproven`。
3. **转移图**：证明 `setup` 所写每种 change 记录的列、完整数组与 `resolve` 的分支/提交语义，取得 target 和相关 title／人物的同帧前态图，才运行纯计算器生成逐项 title holder、de-facto／de-jure 上级、人物 liege／vassal、claim 的 `old→new`。不能用 R0197 的历史终态填 H2743。不能从 `[2128]`、构造类型 `0` 或部分 8/12 字节记录推出完整操作。
4. **总资源和停战**：即使读到 F，也只可给带来源的**直接 prestige 分量公式**；Mandala、legitimacy、合同/佣兵、钩子等条件效果未闭合时，`signed_resource_delta` 仍为 `null`。休战方向 `30097→29829` 来自静态脚本，实际 days／expiry 还需同帧参数读回；二者都不能提前把总条款标为 complete。

每个新增字段携带 `source_layer`（`native_baseline`、`stock_script`、`pure_projection` 或 `observed_postcondition`）、EXE/脚本 SHA、WarID、双方 ID、日期、native revision、目标 TitleID，以及完整性与 unavailable 原因。V2 顶层 `material_complete` 只有所有 title／人物、双方签名资源、定向停战及其他即时效果均可证且同帧稳定时才能为 `true`；当前必须为 `false`。Python 消费器继续返回 `recommended_outcome=null`、`action_literal=null`，正式终战 selected-step 门禁继续生效。

拟议 V2 wire 只在有生产者时引入新 schema，不能把下例当作已交付 payload：

```json
{
  "schema": "xar.ck3.defender-de-jure-exit-terms.v2",
  "runtime_target_scope": null,
  "runtime_target_scope_unavailable_reason": "dynamic_scope_dispatch_write_set_unproven",
  "cb_prestige_factor": null,
  "factor_unavailable_reason": "setup_count_semantics_or_storage_unproven",
  "resolved_title_vassal_operations": null,
  "resolved_operations_unavailable_reason": "setup_resolve_graph_semantics_unproven",
  "signed_resource_delta": null,
  "directed_truce": null,
  "material_complete": false,
  "recommended_outcome": null,
  "action_literal": null
}
```

省略的 V1 身份和余额字段必须完整继承并按同帧复核。若 producer 只能证实某个中间表达式，另放 `static_trace`，不得借用 `cb_prestige_factor`、`resolved_title_vassal_operations` 这些表示实际结果的字段。

## 下一轮最小静态工作和验收

- 对 `0x336AB40` 两个实际虚分派、`0x2E9FF30` 的计数来源、`0x33590D0` 的 factor 写入与相关 change 追加器建立精确构建 call graph／别名边界；任何动态目标未枚举完都不声明纯读取。
- 为纯计算器先定义输入 provenance 与拒绝样本：错误 CB/WarID、目标数变化、scope tag/ID 不符、factor 缺失、change 类型或数组项未识别、条件效果未读、读前后原生 revision 变化均返回 typed unavailable。只在静态语义闭合后写数值投影测试。
- R0271/R0266 屏幕释放后先使用新外置 attempt 和当次 Steam 离线画面，对 V1 baseline 做只读双采样；V2 未过静态门的字段仍保留 unknown。不能通过这次 baseline live 把投降决策、风险比较或退出动作闭环标为完成。
