# R212：2170 到站后的首次自然 ADD 采样

这是已保留 1.20.0.4 源码/字节的静态续接，来源机器 `desktop-3fevhd2-1c74096080`。未执行 SDK、DR、GUI、native 构建或新 EXE 读取；R212 最终 source H、场次身份、抵达、正 q 和 ADD 均未预授。拟行程1506→2170、最多60自然日只是 Root 的场次范围，不是探针持续时间。

## 友地具体改变哪一环

已闭的 `24ACAA0` 从实际 Unit+20 取当前 Province，验证 `Province+85C=50726F76`，解析 Unit+174 owner 和真实 ProvinceHolder，再交给 `2C097F0`。其完整 owner/holder FullID 相等时立即 true；其余分支保留原方向和战争关系，不从地图颜色、通行权或“友方”字样推 true。现实现 `army_regular_core_passive_12004.cpp:224–283` 保留此顺序。旧 Z: 原生465B映射本轮只经已入库专题引用，没有读取旧盘或追认机器状态。

更靠前的原生 `2657EF0` 320B 原件给出如下路径。它说明为什么到友地有用，同时也说明到友地解决不了什么：

| 实际源位置 | 原始条件/分支 | 到2170会自动证明吗 |
|---|---|---|
| 2657EF4–7F08 | chunk maximum非0，signed current<maximum | 否，必须读实际七槽；state3/current0也不能当普通缺员 |
| 2657F4A–7F58 | 解析该 chunk owner 的**来源 Province**，+788必须为-1 | 否；与 Unit 当前所在 Province 是两个对象 |
| 2657F5E–7F6E | state3直接按current>0返回 | 独立原生支路，不人为与下面位置布尔再 AND |
| 2657F6F–7F76 | 非state3来源 Province+73C必须为-1 | 否，不给这两个 raw 槽臆造业务名称 |
| 2657F80–7F99 | 真正 ArRg 解析；无有效 ArRg 可走原生 true 快路 | Army probe 仍须其真实 ArRg/CArmy/CUnit/DATA 闭包，不借此放松身份 |
| 2657FDD–8014 | Army1D4/1EC为0、原生combat判据false、Unit170<=0 | 否，行军/交战/生命周期必须实际读回 |
| 2658016–8020 | `24ACAA0(actual Unit)` 的当前位置许可 | 这里才是友方目的地可能改变的门 |

因此，优先等待 county owner 的**到站实际完整查询**，不再依据旧q0卡盲挂探针。`player_armies[].current_province_id=2170` 与实际 Unit/完整角色身份是到站证据；`scoped_ordered_refill_inputs_v1.persistent_regiments[].chunks[].native_unit_position_eligible is True` 才是此帧补员位置证据，二者分开保留。

## 到站后只补齐这一条最小输入链

```mermaid
flowchart LR
 A[实际到站后暂停帧] --> B[同帧完整fullwire与DATA/七槽]
 B --> C[现有两种顺序投影分开计算]
 C --> D[选择正的最终共享q且position true的物理槽]
 D --> E[Root当前构建/SYSTEM/窗口/身份准入]
 E --> F[scoped regular_core启用并独立读回]
 F --> G[现prepare及launcher实际READY]
 G --> H[唯一获准未来自然机会]
 H --> I[暂停导出独立完整CoreEvent]
 I --> J[OFF/clear读回与DR恢复detach]
 J --> K[v4严格消费]
```

1. **当前身份与时间**：同一机器、当前 PID及创建时间、generation、episode、GameState、角色与 Army/CArmy/CUnit 完整 FullID；fresh暂停 frame、diagnostics、actual ready/retained-process 回执。完整 `queried_snapshot_id/revision/native_revision/date_raw/episode_run_id/connection_generation` 与这帧逐项相同。不能沿用1506或别场的pointer、PID、TID、Regi或 q。
2. **目标物理输入**：county owner 保留真实 fullwire 的 request/query-sequence和原件 pin，正常展开/normalize后保留 selected Army 完整 row、allDATA、七物理槽及manager occurrence顺序。公共 prepare 的 `select_positive_prepare_target` 已实现所有检查：`ordered_core_ready=true`、无missing；选 `occurrences[].writes[].q`，必须等于该 occurrence 的最终 `q_buffer[q_ordinal_raw]`，并为正signed32；position必须literal true；Regi/ArRg/CArmy/CUnit完整代次、七槽、observed148与DATA一致。物理槽与q-index分别保存。
3. **两模式不是两个真实执行**：`observed_prepared` 使用实际缓存148；`fixed_chunk0_prepare` 使用源码条件准备值。分开保留 `input_basis`，不相加、不把fixed模式当已发生的准备。若两者都正，优先观察已有正cached148的候选是减少时序不确定性的建议；不是新增准入门槛。真实写入仍以后面的 native EDX/stack q 与同core原件为准。
4. **四份 prepare 输入**：fresh frame、fresh diagnostics、完整 selected Army packet、既有 `live_owner_admission.v1`。后三者不是compact摘要。前三份各有2MiB上限；大 Driver 保留原件引用，可另存明确标为 derived consumer input 的完整 selected DTO，不能拼字段或冒充原始 MCP/native packet。
5. **Root authority仍走现合同**：当前source/产物q与SYSTEM、实际已加载carrier DLL身份、独立probe EXE/source-copy、机器/scene/run、获准observer窗口及自然机会。原19字段详见 `INPUTS.json`；a36 source epoch20261018不是运行时身份。最终H尚未冻结，本文不填 live gate true，不套旧R206 `probe.py` 的scene锁。
6. **最少 journal 控制**：现 `ck3_set_army_observer_research_sampling_v1` 启用 `regular_core` 并明确 `regular_core_full_carmy_ids=[实际CArmy]`，再用现query读回当前enabled/epoch/scope。Natural hook须实际已安装且来源吻合；`army_natural_phase_scope_12004.cpp:151–191` 不受其journal Permit的开关影响，真实回调仍建立TLS父scope，SavedC0/Mask224–256也无journal开关门。因此只为v4同core归因不必另开 natural_phase journal；所需parent_scope已在真实CoreEvent内。这里减少控制调用，不授权任何未准入安装。

现有CLI保持原样（大写参数代表待取得的**真实文件/值**，不是新API或当前资格）：

```text
python prepare_live_refill_add.py --repo R --frame F --diagnostics D --army-packet FULL --live-build-admission A --output-root NEW --army-id ACTUAL --regiment FULLREGI --slot PHYSICAL --ordered-refill-entry-mode MODE --timeout-ms 30000 --read-process-identity
python launch_live_refill_add.py --prepared NEW/PREPARED.actual.json --prepared-sha256 ACTUAL_SHA --output-root NEW_LAUNCH
python consume_live_refill_add.py --raw NEW/observer.raw.ndjson --binding NEW/owner-binding.json --core-observation ACTUAL_CORE_EVENT.json --output NEW_ITEM.json
```

Root应先完成慢hash/metadata、常规计划和CaseClient就绪，再异步启动launcher。独立读回 `READY.v3` 后，才执行原队列中**一次**获准自然机会。raw/ready位置始终是PREPARED.native_argv中的NEW，launcher的NEW_LAUNCH只收supervisor回执，不能改consumer路径。底层固定30秒，不是60天观察窗；原9组flags加`--enable`为20argv tokens，不能加不存在的CLI。READY含模块/path/base/export/address/epoch，真实64B header在raw.start，不在READY。当前外部DR0/DR1观察器与其它external硬件调试器不能同PID并用；DLL inline采样本身不占DR。

## 这一次实际结果怎样闭合、何时停

到站暂停时，造成抵达的 callback 已经过去，无法补录。真实 regular core 必须是 `2A9A570` post-date内 `2A9A8DD→2A98AC0`，返回PC2A9A8E2，实际saved mask02通过。同一天、同TID或当前q正值都不能代替这条父链；现有源也不保证任意下一日就进入它。30秒无hit/no-parent/timeout只表示本次未取得正例，不说无补员，不自动续日或重挂。

成功需要原6行raw、即时B88/B8B指令前后、相邻debug ordinal、真实Regi/slot/q-index/q DWORD、252B七槽和28B stack-q前后、两trap各双168B稳定active carrier、同非零token和全部parent/date/manager/TID/GameState约束；最后实际restore/detach/退出也必须成立。正 Army NET、cached current刷新或前后人数不能替代它。

独立CoreEvent从同一host完整 `observed_history_full_v1` 原生结果中的 `actual_army_regular_core_observations_v1.events[]` 导出一整条。公共compact结果使用已有mark/recover绑定actualrequest/query序号；不从NET或新dict补字段。单CoreEvent≤4MiB、raw≤128KiB、binding≤16KiB。**先在暂停/active0时导出，再OFF/clear**：`ReadableLocked=enabled&&active==0`；disable active0会清journal并推进epoch，不能OFF后才寻找记录。未取得独立CoreEvent即无v4同core闭环，不降v3假通过。

一条正ADD与同core自然归因通过，只闭该事件；完整NET的唯一原因、无漏采整窗总量、开关效果、全部R06业务/合格镜头仍分别待证。Root的60天移动上限、observer许可、录制与至少900秒正常退出余量保持各自原合同，不从本文扩额。
