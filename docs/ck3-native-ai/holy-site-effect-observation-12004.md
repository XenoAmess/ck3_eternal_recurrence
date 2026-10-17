# 圣地认可矩阵与实际角色聚合观测（1.20.0.4）

machine_id: `4-8e1c2f1861`；离线来源核对时间 2026-10-17 18:50 UTC。EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本补丁阶段 native 构建、新原生包消费和实机仍待验；synthetic SDK 测试不能替代它们。

现有只读 `ck3_query_player_holy_site_relic_context_v1(expected_revision, holy_site_id)` 可选增加 `recognition_matrix` 与 `modifier_aggregate_observation`；action-context 工具仅增加认可矩阵。工具名、私有权限、旧字段和旧计数保持原合同，不添加任意 actor/key 参数或动作权限。旧包缺字段兼容。action preview canonical/hash 排除这两个独立观察域。

## 原生认可与实际收益分层

认可矩阵取关联 Faith 原列表，再加当前玩家和该圣地县主 Faith；对象取实际非空槽、当前原版窗口 candidate cache，以及既有 action-context 请求物。fullID 保留 generation，去重结果另附原顺序/重复/source flags/indices。每格调用原版 `2530EF0`，available=false 时 value=null，不能转为 false。cached candidate 不是 rendered visibility。

新增矩阵 getter 上界 256，Faith/槽/candidate/去重对象各 64；越界先拒绝，不截断。此计数不冒充包含旧 rarity producer 内部调用的整个 query 成本。捕获后重读 player/rite/Faith、site、关联数组、槽、窗口根/候选和对象字段；漂移清除全部格结果。调用顺序明确但 `evaluation_atomic=false`；该原版 getter 的脚本分配/TLS、深层 RNG 未知边界沿既有 reader。

单份 site Active/rarity 缓存、每 Faith 认可和最终 modifier 消费是三层事实。矩阵不输出逐 Faith Active，也不由认可 true 推导收益。

## 实际聚合值使用真实加载键

`modifier_aggregate_observation` 仅复制当前 Type 的两个固定 PC：`faith_fixed`（type+58）和 `local_fixed`（type+218）。原生输入由 [固定 PC 消费合同](evidence/holy-site-effect-observation12004/SOURCE-CONTRACT.actual.json) 及其逐字节 ASM/RAW pin 绑定：`2438830 → 2303100` 使用 PC+0 的 uint16 keys、PC+C 的 count、PC+68 的 int64 Q64 values；本地分支也把 type+218 直接交 `2303100`。FFFF 按原版跳过；定义数组顺序/重复保留。

来源限定为这两个 PC 的 first-seen key union（每块最多 32、去重最多 64），绝不把字符串 token、旧 ABI sentinel 或未归因 A* 常量充作属性键。每个 definition entry 的 `property_name=null`、`definition_raw_q64` 只是实际定义值；type+418 动态分支可改变最终贡献，不能把定义数值直接宣称到账。

只允许当前玩家与 site→barony→county→holder 派生的最多两名角色，保留去重来源。复用既有 `ReadCharacterModifier2C4D1D012004` 的纯 guarded-copy 路线。必须有该 Character 自己的当前 aggregate model 与 owner backlink；初始化默认 aggregate 不当实际零值。输出 `aggregate_raw_q64` 是这个键**所有来源**的总聚合，`site_attribution_observed=false`、`scaled_effects_observed=false`、`names_bound=false`。

读后再次核对角色/rite/Faith、site/type、两个 PC 的原指针/键/值，以及 owned model 身份和同 key 值。漂移使本域 unavailable，清掉全部值；缺缓存使该 recipient 的整行 unknown，而不是零。没有调用 getter、rebuild、cache refresh 或原生 modifier writer。

## 规划与实拍使用

应保存普通空站点、主要但仍空站点、供奉后的三份独立 fresh 查询，绑定相同角色/full key、日期/native revision 和其它改变。真实前后差值是受控局面证据；聚合缓存刷新、clamp、其它来源仍应分别记录。未知名字不能自动贴“外交”或“教士好感”标签。

实际消费源码已证明：Faithwide `24FB270` 要求请求 Faith 的主要名单成员且 `2441F30` 县主 Faith 相同，其 primary 没有 Active18 门；local 固定消费者另有 Active/角色信仰与 title 来源条件。GUI effects 描述的 Active 空字符串不能代替该实际门。完整规则复用 major-grade-value 专题源，不由本 reader 改写。

替换/取回沿原工具执行一次并独立读两物 owner、player-owned 与实际槽。原版替换接收器把旧物交 command actor，不能仅看 ACK 或新槽就宣告返还；认可矩阵也不证明 Faithwide 或县域收益。

## 焦点资格与边界

仅新 target `xar_ck3_12004_holy_site_relic_recognition_matrix_test`：owned memory/injected recognition、实际 PC/角色 helper/生产 serializer；新目录参数禁止覆盖原包。包含矩阵正负/漂移/上界与实际聚合、默认缓存拒绝、PC 上界和聚合漂移。它不是 live 原版脚本效果资格。

后续一次构建 `xar_ck3_bridge` 与这个新 target，复用旧业务矩阵/source-bound 资格；通过实际 Driver/Service/MCP 消费新包后才记新 DTO 原生资格。CI 只在现有 Windows 构建/SDK job 增加这一个 native target 与两个新 SDK leaf，不扩大旧验收矩阵。所有新增编译/Defender 精确登记与实机状态另写实际 machine-bound 回执。
