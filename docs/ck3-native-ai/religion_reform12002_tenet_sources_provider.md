# 1.20.0.2 当前 Rite 草案：全部真实 Tenet sources 只读 provider

状态为 **static-ready**，不是 live。实现继承已冻结的 [Tenet sources 原生树](religion_reform12002_tenet_sources.md)，直接读取真实 registry、当前窗口的 inline category 和实际 Tenet slots；不构造 category／TenetItem，不调用 ShowWindow 或选择／创建／改革动作。游戏与 EXE SHA沿用原生树的 CK3 1.20.0.2 / `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。

公开 API 位于 [religion_reform12002_tenet_sources.hpp](../../ck3_autonomous_player/native_bridge/include/xar_bridge/religion_reform12002_tenet_sources.hpp)，冻结 SHA-256 `bf48e912647f0cee0817df9561da8ceed62e484b3f7402c8ad394dff5d43d077`：

```text
BindCurrentDraftTenetSources12002(module_base, executable_sha256)
ReadCurrentDraftTenetSources12002(bindings, capture_epoch, output)
SerializeCurrentDraftTenetSources12002(output)
```

调用仍归现有 paused application-main owner。窗口读取复用 [window primitive](religion-reform12002-window.md) 的真实身份／日期采样；所有输入地址从 exact-build native bindings 和同帧实际对象解析，API不接收 public actor、Faith、Rite、category地址或模拟草案。

## 实际观测与最后值

[实现](../../ck3_autonomous_player/native_bridge/src/religion_reform12002_tenet_sources.cpp) 遍历已存在 global `5D1DEB8` 数据库的 `EF0/EFC` pointer array/count，并对每个真实 definition 调原生 `14F2030(actualWindow+888,definition)`。所有 `window778/784` 实际 TenetItem 行发布其真实 `+20` slot index与 `+28` definition key。输出只保留一份共享 source集合；这些 slots不假冒多个独立 category。

源 Rite 来自实际 window `+C8`，其 Faith/main Rite分别按完整 generation解析。`24F88A0(sourceFaith.mainRite,definition)` 给 `native_status_raw`，不是 actor Faith的状态。角色的另一条真实链 Character `+B4` → Rite `+4B8` → Faith供 `24425B0` 发布 `actor_faith_status_raw`。角色 extra Tenet `C8` 与 perks原生 collection，经 `A11CC0` 取得知识与 Prophet值；`372DF30` 在同一实际 `window+D0` TopScope中查询 shown658／selectable4B8。完整原生最后门的等价表达式计算 `native_can_pick`，`source_can_materialize && native_can_pick` 给 `final_selectable`。

`passed_shown` 和 `passed_selectable_trigger` 是各自独立查询的原生布尔；即使某条原生最后门会短路，本观测仍报告这两个真实输入的结果。没有把过滤结果或知识不足冒充 trigger失败。候选集顺序保持真实 registry顺序，并保留 `source_index`；它不是 GUI排序顺序。

实际 `category+18` 为 null时输出 `raw_category_exemption_present=false/key=null`；否则复制该真实 definition key，原样用于 native filter的重复豁免。其它生命周期 setter的名称语义仍未查明，但不会据此猜 per-slot definition。字段读取与共享 predicate已闭合，不以该命名缺口阻塞观测。

| JSON字段 | 含义 |
| --- | --- |
| `scope` | `actual_current_draft_all_tenet_sources_shared_slot_predicate` |
| `slots_share_source_predicate` | 固定 true；实际 slots映射同帧共用 candidate结果 |
| `slots` | 每个实际 slot的原生 ID与当前选中 Tenet key |
| `sources` | 每个实际数据库 definition，保留 source/final与知识／trigger原生值 |
| `source_can_materialize`／`filtered_out` | 原生 `14F2030` 返回值／其否定 |
| `native_status_raw` | 来源 Faith.mainRite的 `24F88A0` 原始uint8 |
| `actor_faith_status_raw` | Actor Faith的 `24425B0` 原始uint8；与上项不同 |
| `knowledge` | 真实 actor extra C8 membership或 Prophet perk membership |
| `native_can_pick` | `EE0AD0` 完整输入的等价结果；未伪造item调用它 |
| `final_selectable` | source会物化且其原生最后值可选 |

## 空集合、无窗口与失败

有效实际窗口中 source count／slot count为0是合法观测：`available=true`、`draft_observed=true`、`tenet_gates_complete=true`、空数组。known absent/hidden currentwindow为 `available=true`、`draft_observed=false`、`tenet_gates_complete=false`、空数组。绑定、身份、native collection或读取失败为 `available=false`，返回具体 `unavailable_reason`，丢弃部分 source结果。

现存 perk数据库／Prophet definition在非空source情况下是 native filter的真实依赖；缺失返回 unavailable，不通过数据库getter初始化游戏registry。合法raw0保留为0，知识足够时可以得到true最后值，不用null覆盖已观测的零值。

## 一次必要验证与接入

[实际 C++ fixture](../../ck3_autonomous_player/native_bridge/src/religion_reform12002_tenet_sources_test.cpp) 与 [runner](../../ck3_autonomous_player/native_bridge/research/religion_reform12002_tenet_sources_run_tests.py) 进行了单次 **MSVC `/O2 /W4 /WX`** 构建／运行，8 cases GREEN，产生6份 **实际 serializer JSON**。native functions在离线 fixture中以typed callbacks替身提供；真实 provider、window reader、core resolver、Tenet definition key copier与serializer均参与执行。没有调用CK3，因此不能标fixture-live或production-live。

覆盖一个实际布局草案中的8 sources／2真实slot IDs（7、11）、sourceFaith/mainRite与actorFaith分离、已选重复、真实category18豁免、raw0且extra知识允许、actor Faith状态非零但最后knowledge不足、shown／selectable触发器拒绝、Prophet知识允许、合法空集合、无窗口和native collection读取失败。没有重复旧矩阵、旧EXE函数或 `/Od` 测试。

证据位于 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-reform/tenet-sources/fixture/result.json`。同目录有6份JSON、compiler/test日志与O2 objects，可由独占新transport owner复用编译对象／同一fixture输入；不得链接fixture原main或改已冻旧R7 producer。

剩余是新独立 wrapper/mailbox 接入、root联编，以及 paused真实窗口中至少两个 actual Tenet slots／已物化真实row `EE0AD0` 最后值互证。完成前不发G2 credit或完整reform OODA完成声明。接口和fixtures已经交协调者／传输层owner，可并行施工，Git由协调者提交推送。

当天／当周报告字段为 **2026-10-01 / 2026-W40**：新增全部当前草案实际 Tenet sources 只读provider／serializer；价值是解除“只有当前popup”的Tenet观测缺口；readiness从research提升至static-ready；5spans42anchors4旧pins原生树GREEN，O2实际provider8cases6serializerJSON GREEN；无CK3、无新liveartifact、无战争；剩余wrapper/mailbox/root paused等价验收，commit/push由协调者记录。原生树三源仍按先前tree receipt冻结，新增provider／fixture／本文的sourcepins另存 `tenet-sources/delivery-result.json`。
