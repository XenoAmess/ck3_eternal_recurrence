# 现役战斗下一日非掷骰优势：缓存、来源与采集边界（2026-09-27）

## 结论及证据身份

本备忘录绑定 CK3 `1.19.0.6-steam23530548` 的 `ck3.exe`，SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
静态指令由只读的
[`extract_active_advantage_sources.py`](../../ck3_autonomous_player/native_bridge/research/extract_active_advantage_sources.py)
从此 EXE 重取。现役数值只来自第 086 次同暂停帧的
`c086-battle-control.json`（SHA-256
`6DFC287C42154486D78E2609AEE1C74B2A00F7E2E018C8FBC4B90D639CC4D550`）；该 attempt 原件位于外置
`D:/workspace/ck3_native_war_ai_promo_work/episode01-battle-control-composite-attempt-086/ck3-output/interactive-requests-responses/`。
没有在本研究中启动 CK3、推进日期或修改既有证据。

2026-09-27 追加复核：同一提取器的 `--verify-cache --expected` 对 18 个确切指令地址、操作数及 EXE SHA 做失败即停比对，冻结结果
[`active_advantage_cache_source_chain_11906.json`](../../ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_cache_source_chain_11906.json)
SHA-256 `D66844051D7601B2449FED0C89B0B7B9FBA49892711441686AAD3491BA6D05E5`。它校正了下文 `target` 条件在**当前缓存重算调用**中的可达性；没有改变 086 实机回执。

**当前可以精确算出“已缓存优势减去当前 roll 的算术残差”，但尚不能把它命名成真正的非 roll 来源。**
原版在独立的战斗管理器 pass 中重算 `CCombat+0x710`，主战日函数随后可能更新 roll，却读取这个优势缓存。
因此暂停查询中的 roll 未必是产生 `+0x710` 时的 roll。角色、效果、兵团、增援和选中将领也可在两次读取之间
改变；这个残差既不能作为已证当前来源，更不能复制为以后每天的常数。

## 原版 1.19.0.6 指令链

| 层 | 精确 RVA 与指令事实 | 可以推断的边界 |
|---|---|---|
| static/base | `0x23045F0` 按每条 `CCombatEffect*`、Q100000 scale、side 符号更新并逐条 clamp `CCombat+0x6C8`；原生还分别保存 attacker `+0x98/count+0xA4`、defender `+0x3E0/count+0x3EC` 的 16-byte 来源 row | `+0x6C8` 是当前持久的 signed static/base 累加器，不是将来所有增援或事件后的静态常数。各侧 ledger 单独存储，不能在可能发生逐条 clamp 的情况下从分侧数组擅自恢复全局追加次序。原生来源类别和 contact 顺序另见 [v3 advantage source trace](combat-simulation-inputs.md)。 |
| materialize and resolve | `0x2308D50`: `0x23CBCE0` 依次刷新两侧，`0x23CC2B0` 依次以 encounter Province 更新两侧；`0x2308D9A` 读 qword `+0x6C8`，`0x2308DAF/0x2308DC6` 调两次 `0x2307CB0`，`0x2308DCE` 写 qword `+0x710` | `resolved = base + side0_total - side1_total`，Q100000。不能在刷新前从未完成 materialization 的 side 值断言总和。 |
| dynamic total | `0x2307CD8..0x2307CE7` 先取 `+0x6D0/+0x6D4` 当前 roll 并乘 `100000`；`0x2307CEA/ED` 仅在 R9 target context 非空时进入 `0x2307CF3..0x2307E14` 的条件支路；`0x2307E2C..0x2307EBD` 取该侧选中将领 full CharacterID、relation、commander component `0x2307680` 和 `side+0x110` aggregator component `0x2307230` | **本页的 `0x2308D50` 缓存重算两次调用均把 R9 置零，因此跳过 target 条件支路**；将领与 side aggregator 仍执行，并收到 null context。仅靠 GUI generic advantage 或两个 roll 不能求下一日结果。其他非空 R9 调用不能从本缓存路径外推。 |
| manager schedule pass | 对 `0x2308D50` 的直接 callsites 精确为 `0x27FB4AC` 与 `0x27FB57A`。后者所属 `0x27FB4D0` pass 在 `0x27FB57A` 重算后，才在 `0x27FB58F/0x27FB5A7` 调两侧 `0x23C8750` phase-event preparation | 每次管理器该 pass 都可能刷新 `+0x710`；但现有静态证据没有闭合它与另一 manager、join 和每日 dispatcher 的全局时序，也不能把 phase-event preparation 误记为执行 effect。 |
| daily consume | `0x27FB5D0` dispatcher 在 `0x27FB683/0x27FB6A2` 重选并写两侧将领、增 phase-day，main 分支 `0x27FB6FD` 调 `0x2309E80`；该函数在两侧 `0x23CA2F0` refresh/event fire 和可选新 roll 后，以 `0x2309F55` 的 `0x23053B0` **读取**缓存 `+0x710` 计算倍率，`0x2309F5A` 再以其正负给一侧倍率，随后计算出伤 | 本 main tick 中没有 `0x2308D50` 调用；新 roll 可晚于优势重算，使暂停帧 current roll 与 cached advantage 不再配对。当天事件/新 roll 对同日伤害的影响应以原生边界 trace 判明，不能凭文案假定。 |

此前把 helper 内 `0x2307DA3..0x2307E19` 的可选 target 条件支路写成当前缓存的必有来源，属于把 helper 的一般能力误当成该 callsite 的实际参数。exact-build `0x2308DA6` 与 `0x2308DB4` 均为 `xor r9d,r9d`，分别在 `0x2308DAF` 与 `0x2308DC6` 调用前清空 context；`0x2307CED` 的条件跳转直达 `0x2307E19`。这个修正缩小了当前缓存的来源集合，**没有**消除将领和 side aggregator 的动态缺域，也没有证明另一原生函数不会在其他时刻更新 `+0x710`。

第 086 次真实战斗在 date raw `53146488`、CombatID `16777218`、ProvinceID `2633`、主战第 7 日，
双方**暂停时** roll 为 `7/8` 点，`base_advantage_raw=-300000`（-3 点），
`resolved_advantage_raw=-600000`（-6 点）。可验证的只是算术残差：

```text
cached_minus_current_roll_projection_raw
  = resolved_raw - base_raw - (side0_roll - side1_roll)*100000
  = -600000 - (-300000) - (7 - 8)*100000
  = -200000  // -2 点算术残差；不是已确认的非 roll 来源
```

如果 `+0x710` 的最近一次重算使用的恰好是这两个 roll，这个数才等于两侧非 roll 总和的净差；
目前缺该重算边界的 roll 取证，故不能作此升级。更不能从 `-200000` 反推出各侧 commander、
aggregator 各占多少，或证明它是下一主战日的差。086 的 v3 虽含 15 条 hypothetical-contact
constructor 来源，却标记 `explicit_hypothetical_fixed_at_contact_no_reinforcements`，且假定战宽
`1539/1385` 与真实 `1645/1480` 不同；那些来源不得拿来补这个现役战斗的来源行。

## 可验证的最小 production producer

1. **同帧只读观察层**：现有 `ReadBattleControlSnapshotSample` 已读 `base_advantage_raw`（`+0x6C8`）、`resolved_advantage_raw`（`+0x710`）、两侧 `current_roll_points`（`+0x6D0/+0x6D4`）、roll cadence、选中将领和真实双方 entry；Python `battle_control_contract.py` 对优势只校验这些标量，**不暴露**两侧 `0x2307CB0` 重算所得 total、独立 effect-ledger rows 或产生缓存时的 roll。最小新读口必须在取得 generation-valid `CCombat`、两侧顺序、
   `+0x6C8/+0x710` 和 roll 后，附一个独立 `active_advantage_sources` block：CombatID、revision、phase/day、
   原生两侧 ordered effect-ledger rows 的 loaded effect identity/points、scale，及上述 checked-int64 算术残差。
   `base/resolved/roll` 必须与 battle-control 现有字段全等；数组 count、effect pointer、loaded key、scale、
   identity 有任一不合格就整块 unavailable。阶段内分侧 ledger 只发布各自顺序，**不要制造全局追加次序**。
   这个 block 只能叫 `current_cached_observation`，不能命名 `non_roll_source_total` 或 `next_day_forecast`。
2. **原生日更时间对拍**：扩展现有有界、预分配的 phase-event trace ring，在同一 CombatID 的
   `0x27FB57A` 前/后（特别要保存该次重算实际使用的 roll）、两侧 `0x23C8750` 返回、两侧
   `0x23C9900` 返回、`0x27FB6FD` 主战入口和 `0x2309F55` 倍率读取前记录 date、phase/day、roll、
   selected commander、`+0x6C8/+0x710`、
   effect ledger count 与双侧 dynamic source 总额。hook 内只做有界复制，不回入 bridge、不调用原版
   resolver、不分配游戏内存。按单调序号保存边界并和当日真实出伤对拍；必须包含一次五日事件与一次增援，
   才能声明“下一日来源更新顺序”已验证。现有 [phase-event trace 合同](combat-phase-event-trace.md)
   已有部分边界，可复用同一传输/同一时钟。
3. **续算输入**：试算每一天时从 trial 的当日角色、两侧状态、effect/aggregator、选中将领及 roll cadence
   **重新求值**；按实测的 schedule/dispatch 顺序选择哪版缓存进入伤害。任何源 leaf、日内更新或
   `original-helper` 对拍缺失，就保留 `next_day_non_roll_advantage_sources` missing，不用当前净残差作长期
   替代。首个验收向量应重放 086 的 `-300000/-600000/7/8/-200000` 当前帧，并另建发生 event/增援
   的相邻日原生 pair；只有 hook 证实缓存和 roll 同代，才能把残差升级为该次重算的非 roll 净差。
   只比对同一日原生读数不算下一日验收。

因此此次静态研究闭合了“缓存从哪里来、何处重算、主战日何处读取”和 086 帧的算术残差，
**没有**关闭 `active_combat_resume_inputs_v1` 的 `next_day_non_roll_advantage_sources` 缺域，
也没有改变智能体的 `input_observation_ready` 或胜率门禁。

本轮未直接增加 bridge 字段：从暂停帧复制 `+0x6C8/+0x710/roll` 只能给算术残差，而现有代码没有在缓存重算调用边界保存两侧原生 total、当时 roll 和 loaded effect 身份。贸然把残差或对 `0x2307CB0` 的暂停查询调用暴露成真实 non-roll source，会跨越原生时序并可能执行条件/状态性 helper。先按第 2 项在受管 trace 的原调用边界只读复制，完成相邻日配对后，再决定可供智能体消费的 typed input；其间仍用带缺域标记的现有近似行动比较器。

追加的[第 12 日连续帧/重载帧对照](active-battle-fresh-load-frame-divergence-2026-09-27.md)进一步实测了缓存时序风险：099/106 从第 11 日连续推进后的第 12 日 `resolved_advantage_raw=-1100000`，而 100/104 独立载入该日存档后的同 CombatID、日期及反制输入为 `-600000`，且部分兵团有效属性也不同。两组各自重复一致；现有证据只证明观察条件不同，不单凭这些值断言是哪个载入或刷新函数造成。任何下一日算式必须绑定真实运行帧，不能跨这两种条件拼接。
