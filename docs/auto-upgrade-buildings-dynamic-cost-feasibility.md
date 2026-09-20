# 自动升级建筑：实时费用减免可达性调研

状态：**CK3 1.19.0.6 的纯数据 Mod 中不可达，因此不施工、不发版。**

调研日期：2026-09-20。目标产品为“自动升级建筑（XenoAmess维护版）”，Workshop item ID `3800124956`；当前公开版本继续保持 `4.0.1`。

## 需求合同

“即时计算建筑花费减免”不能只处理一个 `build_gold_cost`。可接受实现必须在每次升级发生时，与原版施工按钮得到相同的最终费用，至少同时纳入：

- 付款角色当前的通用、地产类型与其他适用修正；
- 当前 county/province/holding 的修正；
- 建筑自身的金币、威望、虔诚及 scripted cost 形状；
- DLC、游戏更新和其他 Mod 新增的适用修正；
- 原版的取整、下限、可负费用和最终可负担性规则。

只识别一份已知 trait/modifier 清单，或只做 `基础价格 × (1 + build_gold_cost)`，都不满足这个合同。

## exact-build 证据

### 引擎拥有最终实时费用

原版 `game/gui/window_county_view.gui:2388-2458` 把候选建筑的 `GUIPotentialBuildingItem.GetCost` 投影为 `ValueBreakdown`，用 `CanAffordCost(GetPlayer.Self)` 判断能否支付，并由 `GUIPotentialBuildingItem.Construct` 执行施工。这个值属于 GUI/引擎 data model，不是事件脚本中的普通 script value。

同一 exact build 的原版内容同时证明费用来源并不限于人物：

- `common/traits/00_traits.txt:1562-1564` 在人物 trait 上提供 `build_gold_cost`、`holding_build_gold_cost`；
- `common/modifiers/00_county_modifiers.txt:135` 和 `00_province_modifiers.txt:62` 在地块侧提供 `build_gold_cost`；
- `common/modifiers/00_activity_tours_modifiers.txt:85` 等来源还提供 `castle_holding_build_gold_cost` 一类 holding-specific 修正；
- 曼荼罗内容自身的 `common/modifiers/tgp_mandala_modifiers.txt:38-39` 同时使用 `holding_build_gold_cost` 与 `build_gold_cost`。

仓库的 exact-build 私有只读观察器进一步闭合了引擎入口：`docs/ck3-native-ai/domain-construction-cost-direct-observer.md` 记录原版玩家 `CanConstruct` 在 RVA `0x295CD60` 调用费用构造器 `0x29190F0`；观察结果保留十个原生费用槽。离线 verifier：

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\verify_player_world_building_cost_direct_v1.py --exe C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
```

在 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 上返回 `GREEN exact stock player cost source; CK3 not launched`。

### 纯数据脚本缺少两座必要桥梁

对 exact 1.19.0.6 原版脚本、GUI 和本仓库运行脚本进行穷举检索后，没有发现下列公开能力：

1. 把人物或 province 当前聚合后的某个 modifier 数值导出为变量/script value；`export_modifier_to_variable`、`check_modifier_value` 等候选接口不存在。
2. 对一个普通建筑调用与原版 `GUIPotentialBuildingItem.Construct` 相同的施工入口，并让引擎自行计价、扣款和开始施工。

公开的相邻 effect 不能补上这个缺口：

- `add_building`/`upgrade_building_effect` 是即时改变建筑，当前产品必须自行检查和扣款；
- `generate_building` 走随机 AI 选择，不接受本产品已经选定的目标边；
- `begin_create_holding` 只创建新 holding，不建造 holding 内的普通/主/公国/特殊建筑；
- GUI 的 `GetCost`/`Construct` data context 不能从事件脚本或 scripted effect 中直接调用。

因此，即使脚本手工汇总当前已知的 `build_gold_cost` 与 holding-specific key，仍会遗漏作用域、条件式/scaleable modifier、其他 Mod 扩展以及引擎取整语义。它会制造“有时看起来正确”的静默错扣款，风险高于继续使用明确披露的原版基础费用。

## MCP-first 实机探针

研究工具 `tools/run_auto_upgrade_buildings_mcp_cost_probe.py` 只使用原生桥接语义接口；报告固定声明：

- `mcp_first = true`；
- `functional_assertions_by_ocr = 0`；
- `uses_ocr/uses_mouse/uses_keyboard = false`。

第二轮证据位于 `D:\workspace\ck3_eternal_recurrence_process_assets\aub-cost-probe-r0002\artifacts\report.json`。原生 GUI 树成功枚举 285 个节点，并识别 `frontend_bookmarks`、可见的 `dlc_list_overlay` 与 `button_close`；旧前端 route contract 因遮罩返回 `unavailable`，所以探针按 fail-closed 规则记为 RED，没有回退到 OCR 或桌面点击。自有 CK3 PID `28428` 已受控终止，`cleanup_proven = true`，最终进程清单为空。

这次 RED 只表示“未进入地图取得 live cost sample”，不否定静态闭合的原生费用入口，也不被冒充为产品功能 GREEN。它同时证明此类界面诊断可以由原生 GUI 树完成，无需 OCR。

## 决策

- 不实现不完整的修正白名单或手算近似。
- 不把私有 native DLL 变成 Workshop Mod 的运行依赖；那会改变产品类型、平台兼容性与发布安全边界。
- 不修改 `mod_auto_upgrade_buildings/`，不提升版本，不上传 Workshop，因此本轮没有 release changelog 或 Steam Change Notes。
- 当前玩家文案“费用采用 CK3 1.19.0.6 原版基础费用，不受减免影响”继续保持准确。

只有 Paradox 后续公开以下任一能力时才重新评估：可从事件脚本读取引擎聚合后的最终建筑费用；或可对指定普通建筑调用原版施工入口并让引擎自行计价和扣款。
