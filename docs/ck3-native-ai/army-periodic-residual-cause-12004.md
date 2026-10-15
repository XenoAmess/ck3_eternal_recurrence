# 1.20.0.4 周期 residual、围城与掠夺的最小归因

machine_id: `desktop-3fevhd2-1c74096080`。本轮离线观察起于 2026-10-15T18:35Z；封包时间见本轮 delivery 回执。
游戏来源：1.20.0.4 / Steam 25734779 / EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
源码基线 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`；preferred 的预算叶依赖
[a07 合同](army-siege-budget-writer-stack-12004.md)。这是下一次 coherent build 的外置候选，无新实机通过。

现有 hook 已经足够区分两种周期 residual 的阶段。现有 packet 没有记录 combined residual 的原围城/掠夺预算，因此其原因集合仍缺两个 DWORD；在已有 hook 上补读即可，不需要新 detour。原生代码将围城和掠夺合并后才分配损耗，混合事件不存在可观察的逐原因扣兵分账。

| writer 返回 | allocator 的外层返回 / flags | 机器可用的结论 | 新 native 字段 |
|---|---|---|---|
| `24E377C` | 直接 preferred | a07 两预算可得 siege-only、raid-only 或正预算贡献集合 | 无 |
| `2A958E8` | `24E3638` / 2 | actual periodic supply residual | 无 |
| `2A958E8` | `24E37B3` / 0 | actual periodic combined siege/raid residual；两预算区分贡献集合 | 两个 int32 |
| `2A958E8` | `24E2630` / 0 | county-entry，不能记成周期围城 | 无；本 consumer 拒收 |

## 已持有完整源码给出的不可区分反例

复用既有 `high-parallel-siege-source-a03/24E3410.asm`，没有重读游戏 EXE、1580B/212B/207B 原始字节。该 ASM 的 25 行 `24E346B` 保存原围城预算到 callback `RSP+80`；151–153 行 `24E3646/24E364E/24E3656` 将原掠夺预算与围城预算做 int32 ADD，结果写回 `RSP+88`。235 行 `24E3777` 是 combined preferred writer，249 行 `24E37AE` 是 combined residual allocator。供给 residual 的 CALL 位于 `24E3633`，返回 `24E3638`，flags=2。

保持供给预算、ArRg、当前兵力和其他参数相同，原预算 `(siege,raid)=(10,0)`、`(0,10)`、`(7,3)` 都在后续路径得到 combined=10。仅有完整 preferred/residual writer、残余 requested budget、callback token、库存和日期，仍无法区分这三组输入。增加更多同类 writer 历史也不能逆转已合并的值。当前 query 的地点或可见围城状态不是当次 callback 的原预算操作数。

复用 `high-parallel-county-a04/residual_allocator.source-reuse.asm`：`2A957E0–2A957E8` 在非零路径只有 TEST/JE，没有栈变化；`2A958D1–2A958E3` 只把合并后的份额做整数运算后送到同一个 `2634190` writer。它没有围城份额/掠夺份额两个物理写回。即使两个原预算都完整，按比例、先围城后掠夺或其他规则拆分实际损耗都属于新增规则，不能冒充原生观测。

## 仅补已有 residual hook 的 8 字节

[自然 hook](../../ck3_autonomous_player/native_bridge/src/ck3_12004_residual_parent_hook.cpp) 在真实入口取得 `_AddressOfReturnAddress()` 并显式传给 helper；helper 默认空指针以保持旧 fixture 源调用兼容。不能在 typed helper 或 allocator writer 里直接使用同一偏移。

当且仅当 source 已证 periodic、外层返回 `24E37B3`、flags=0，
[context](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_residual_parent_context.hpp)
在 original continuation 前从该 return slot 的 `+88`、`+90` 分别安全读 int32 原围城和 combined 预算。
CALL 压入 8 字节，所以 callback RSP=return slot+8；这正对应 callback `+80`、`+88`。
读取失败产生 null 和独立失败位，不推零。optional leaf 随既有 residual TLS payload 复制到 writer 的
`residual_parent_context_v1.siege_budget_at_allocator_v1`；外层仍要求 token/thread/depth、双 fullID、实际 ArRg 数组 membership 完整。

现有默认 OFF 旗标与既有启动安装位置保持。原 native continuation 的调用仍在 helper 中恰一次；TLS scope 寿命、nested 恢复、跨线程规则保持既有实现。没有导出裸指针，没有新增入口 detour、query 或通用追踪设施。内部 inline helper 增加默认参数，native 仍须 coherent 重编，不能混用旧对象。

## Agent 与视频验收合同

[独立 consumer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_periodic_loss_cause_evidence_12004.py)
消费已绑定同一进程/episode/journal lifetime 的完整、规范化 Army 行，使用相互独立的 writer/callback sequence fence。
每笔首先必须通过完整 unique physical slot 的 before-after 事实，再匹配唯一 actual daily callback `2A9AB4B` 的 copied token。residual 还须完整 direct allocator parent，父 token/thread/depth、实际双 ID、真实 roster membership 和精确 outer return/flags 均匹配。same-date、当前成员身份或 regular-core 净变化均不能替代这些条件。该版本保守复用现有 join 的 writer-entry stock 读取完整性门槛；库存本身不用来推断损耗原因。

combined 操作数完整且非负、无 signed overflow、合并值正时，`source_cause_set` 是该原生请求的正预算贡献集合：`[siege]`、`[raid]` 或 `[siege,raid]`。int32 wrap 或失败读取仍拒收原因归属，保留已证物理事实。纯 supply residual 不需要新预算叶。mixed 的 `actual_physical_soldier_debit` 只属于整笔原生 writer；`per_cause_physical_debit_soldiers=null`，`per_cause_physical_debit_split_observed=false`。

视频可表述“本次围城预算分支实际扣除 N 人”或“围城/掠夺合并预算阶段实际扣除 N 人”，必须与合格单笔观测和真实画面时段绑定。mixed 不能分别声称“围城损失 X、掠夺损失 Y”。Agent 可用已证 stage 和正贡献集合诊断本次扣兵；没有该事实时应请求下一自然采样，不能按总兵力净变化、低库存或静态地名猜原因。输出始终不授完整时间窗总损耗、未观测原因或新实机通过。

## 实际保存包与本轮验证

证据根：`C:/ck3-e04-resume-20261015-a01/high-parallel-r03-residual-a08/`，机器如上；精确条目 SHA、时间与拒收结果在 `ACTUAL-PACKET-REFUSALS.actual.json`，完整字段盘点在 `PACKET-FIELDS.actual.json`。

- R0173 tracked `original-receipts.zip/day21-final.json`：没有 required journals，拒收正周期损耗 claim。
- R0174 的 22 份、R0175 的 6 份已归档完整 query 中，Army writer events 都为空；各取一份完整输入实际运行新 consumer，均无合格正事件。不能由此推全局零损耗、无执行或未归档查询的状态。
- 六个新增 Python case 的行为最终均通过。首次外置 harness 错用已缓存 main contract，三 error；保留 RED，修正 import overlay 后只重跑三 error 和曾被旧 schema 掩盖的一个 leaf 拒收 case。未运行旧 a07 八例。
- 新 residual-hook TU `/Zs /W4 /WX` 通过；未产生对象/DLL/EXE、未执行 native EXE。源码资格与合成通过不等于下一 build 已部署或实机验收。
