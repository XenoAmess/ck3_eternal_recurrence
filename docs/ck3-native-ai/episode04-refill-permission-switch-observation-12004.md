# 1.20.0.4：来源绑定的补员开关生产观察叶子

这是 future a07 候选：把已闭 262C6E0 的来源选择和 `Character+1C0 → military+4A9` 接到现有 ArmyStrengths 的 `scoped_ordered_refill_inputs_v1`，以及现有自然 regular-core entry/returned 物理观察。同一 typed DTO、序列化器和 strict consumer 共用；没有新增顶层 query、getter callback、命令、detour 或开关动作。候选尚未部署，R06 本轮没有实际游戏开关状态或 actual ADD 验收。

机器 `machine_id: desktop-3fevhd2-1c74096080`；本记录整理于 `2026-10-15T17:18:25.141013+00:00`。冻结依赖为 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`，主树写入由 Root 独占。本 lane 仅外置，未连接 SDK、CK3 或桌面。当前实际 .4 来源和开关分支依据[补员应用专题](episode04-refill-application-12004.md)及其完整 permission body 709B 保持不变，没有新增游戏 EXE 读取或重哈希。

## 从现有生产接口取值

现有 ArmyStrengths 普通查询（包括已有 ordered-refill 全量选项）的结果路径为：

```text
army_strengths[i].scoped_ordered_refill_inputs_v1
  .persistent_regiments[j].chunks[k].refill_permission_switch_v1
```

同一 chunk 类型位于自然 regular-core 已有 entry/returned 的 `persistent_objects[].physical_values.chunks[]`，因此那里也带相同叶子。普通查询继续走 `ReadScopedOrderedRefillInputs12003 → ReadOrderedRefillPersistent12003`；实际 .4 `PopulateArmySupportBindings12004` 仅在既有 exact-build guard 内绑定新 `refill_switch_image_base_12004`。旧 .3 binding 保持为零，不生成这个扩展；旧 inline packet 和不带新字段的自然观察仍由严格解析器接受。

新增字段只嵌在旧 chunk 对象内，未将全管理器输入另拷贝成新顶层结果。`army_ordered_refill_persistent_v1_serializer.hpp` 是普通叶子和自然帧的共同出口。`war_contract` 继续调用原 ordinary normalizer，`army_observed_core_validation_12004._physical` 对同一个可选叶子执行相同 strict normalizer，不丢掉来源字段。

开关是独立行政状态观察。它不改变当前 prepared148、q 计算、conditional projection、月结入队、实际 ADD 或既有 readiness。即使早期 guard138/Army 状态会让 permission 提前返回，也可读到已解析来源的底层开关；这不声称实际执行走到了开关分支。非 special definition 则忠实记录 `not_applicable`，不读取玩家或其他来源的开关。未解析的旧 owner 上下文可以没有这个可选叶子，absence 仍是未知，不能解释为关闭。

## 字段与真实来源顺序

叶子的固定 `source` 为 `native_regiment_permission_262C6E0_switch_12004`，状态只有 `available`、`not_applicable`、`unavailable`。

| 字段组 | 作用 |
| --- | --- |
| `persistent_full_id`, `definition_magic_38_raw` | 已解析实际 Regi receiver 与 definition 指纹。 |
| `character_ref_12c_raw`, `title_ref_130_raw` | 两个原始 DWORD 来源引用，保留 signed 表示的完整位。 |
| `source_branch`, `resolved_title_full_id`, `title_used_fallback` | 明确分支和 title 原生 fallback 证据。 |
| `selected_character_raw_full_id`, `resolved_character_full_id`, `character_used_fallback`, `character_magic_raw` | 原始所选 Character 和实际 resolved receiver；不折叠为 player ID。 |
| `military_component_present`, `raw_byte_4a9`, `enabled` | 实际 component 存在性、原始 byte 与 `byte != 0`。null component 或读失败不补默认 false。 |
| `identity_consistent`, `unavailable_reason` | 两次完整来源快照与接收者物理身份一致后才授值；变化时清掉 byte/enabled。 |

真实 262C6E0 顺序保持如下：

1. definition magic 不是 `0x4744624F`：`non_special_definition_bypass`，不制造 Character 或开关。
2. title+130 != -1 且 Character+12C == -1：解析原生 title registry/fallback，从实际 title+128 取得 Character raw ID。
3. title+130 == -1：直接使用 Character+12C；两者都为 -1 时仍保留原生 sentinel → Character fallback。
4. 两个引用都不是 -1：原生选 -1，再走 Character fallback；不能优先选其一。
5. Character registry 以 low24 索引、完整 DWORD generation 比较；失配后读取实际 fallback receiver。源引用和 fallback 后完整 ID 分开输出，不把失配伪装为解析成功。
6. 复用先前的严格 Character magic/identity/component 读原语，读取 +4A9，并重新收集相同来源快照。普通 collector 的新增读取有 SEH 边界；自然 core 经现有 Reader 的同一每帧 read-byte 上限，不绕开限制。预算耗尽可以使新叶子或后续帧 partial，不许补值。

所有读取只把 native bytes 复制到 owned DTO；没有向 game byte、组件或 registry 写入。生产绑定没有接受公开 caller pointer/RVA。这个叶子不是完整 permission result：government/resource/helper2657EF0 等后续条件继续不由它代替。

## 已完成的离线生产链验证

单独小型 native fixture 位于 `native_bridge/research/refill_permission_switch_12004/`，不加入默认生产构建图。它直接调用真实 `ReadOrderedRefillPersistent12003` 并使用同一个生产 `AppendArmyOrderedRefillPersistentV1`，原样输出 12 条 synthetic NDJSON；两条专用读失败/来源变化反例直接调用同一纯读解析器。全部成功项由 native 代码构造并序列化，Python 没有手写成功 wire packet。

实际外置根 `C:/ck3-war-episode04-research-20261004-a01/futurea07-refill-switch-fixture-a01`。`SOURCE-FREEZE.a01.actual.json`、`BUILD-START.a01.actual.json` 保存精确源码 SHA、dcda 依赖与标准 `tools/run_native_msvc.py` argv，仅一个目标、1 job。`build-a01/native-msvc-result.json` 为 build0；首个 EXE 执行前 `EXECUTION-GATE.actual.json` 校验 `S-1-5-18`、`admin_token=true`、SYSTEM 精确路径 fresh verified、manifest/source pins 与 EXE SHA。最终 EXE 为 `C:\ck3-war-episode04-research-20261004-a01\futurea07-refill-switch-fixture-a01\build-a01\refill_switch_fixture.exe`，SHA `8514685112c18d67aaca0dab818658a53de5f5abdc1e3476e50907f8b5e9ab4c`。只有通过门禁后才运行，没有把调用 ACK 当登记生效。

原始输出 `native-packets.actual.ndjson` 为 107592 bytes，SHA `313c42e4eab41f0539a8625dce9639fa8900152f21f3713068f136d597186c19`，运行返回 0。`consume_fixture.py` 对不可改写的这份输出检查实际 RUN 摘要，然后调用 ordinary strict normalizer 和自然 core 物理值 validator；12 项消费通过，6 个明确派生的失败反例被拒绝。

| native case | 验证意义 |
| --- | --- |
| direct_nonzero / direct_disabled | 原始 byte=2 仍 true；byte=0 为 false。 |
| title_holder_not_player | title holder full ID `0x81000002` 为关闭，独立 player 示例 CharA byte=2 为开启；没有套用 player 开关，完整 high-bit ID 保留。 |
| title_generation_fallback / character_generation_fallback | 同 low24 不同 generation 必须记录 native fallback。 |
| both_references_native_fallback / missing_references_native_fallback | 真实两引用优先级和 -1 sentinel 来源。 |
| non_special_bypass | 不读无关 Character，状态 not_applicable。 |
| missing_military_component / unreadable_switch | unknown 与 false 分开。 |
| source_changes_during_capture | 值失去稳定来源，byte/enabled 被清空。 |
| legacy_leaf_absent | 旧 wire shape 原样可消费。 |

六个 strict 派生反例为 player ID 替换、off 改称 on、删除来源 witness、只改 generation、给 direct 分支借 title、unavailable 却授 false。它们各自标为派生，不冒充实际发生的 native packet。普通 query 叶子与自然 core 适配的最后两个改动另以既有 MSVC 环境 `/Zs` 通过，未跑新 full native build、SDK 或注册 MCP 调用。

lane 的 source/strict/语法回执位于 `C:/ck3-e04-resume-20261015-a01/futurea07-refill-switch-a01/`。两个根合计使用同一 8 MiB 增量、原 512 MiB 共享池，截止 `2026-10-16T07:45:01.597Z` 复核，不自动续期；来源准入为 `continuation-a05/CAPACITY-ACCEPTED.actual-a01.json`。可重建派生 build 不作永久保护，后续按统一存储策略复核，小型 canonical 源和摘要则随补丁保留。

## 普通 toggle 的真实 GUI 与下一有限源码门

当前实际安装的 `window_military.gui`（Steam app1158310/build25734779，文件 SHA `4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac`）两处 checkbox 使用 `MilitaryView.OnMilitaryReinforcementClick`，checked 使用 `MilitaryView.IsMilitaryReinforcementsEnabled`。第一处 visible 为 `!GetPlayer.GetGovernment.HasRule('conditional_maa_refill')`，第二处为 `!landless_adventurer_government`。证据和机器/时间/[manifest 摘要](evidence/episode04-refill-switch-gui-12004.json)绑定；没有把 GUI 文件名或旧 .3 RTTI 当成 .4 callback 地址。

当前 MCP 的固定 ingame window/operation enum 没有 military reinforcement toggle；窗口 census 的固定 scope 也没有 MilitaryView。现有 legacy `ReadMilitaryOwner`/knights 导航不能平移为 actual .4 callback。已知资料路由未持有这两个方法的 .4 named registration descriptor/RVA，因此本轮不提交动作，不写 +4A9，也不声称 UI checked getter 已证与这个底层 byte 等价。

下一步[有限 source 计划](plans/episode04-military-reinforcement-toggle-12004.json)已实际 check/render 通过：仅这两个具名方法，metadata ≤1 KiB、两个 body 合计 ≤7 KiB，无 callee 扩展。RVA 必须先来自 exact .4 named-registration provenance，当前 admitted_bodies 为空；不能猜偏移、扫 EXE strings/邻域或拿旧 .3 vtable 推导。

源码闭合后才复用现有 main-thread mailbox 的 owner/TLS/paused/revision 门，提供固定 semantic toggle，验 typed MilitaryView receiver 与完整 owner/visible/enabled，原生 callback 恰一次。ACK 与新的 getter/read-only source-owner leaf 后验分开记录，结果未知不重交。若 Regi 的实际来源 Character 与这个 player MilitaryView owner 不同，不能用 player 的 checkbox 代表或修改那个来源。现场下一 R06 可以先通过本叶子看到实际来源和底层开关，再独立验 actual ADD。
