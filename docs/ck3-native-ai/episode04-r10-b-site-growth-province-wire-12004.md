# R10 B：两处真实库存增长与事件发生省份

2026-10-17 追加。研究、代码和实测分开计数：两个真实正增长驻留点仍为 **0/2**，正式 ABC 为 **0/3**。R196 的 2619 当前 eligible／loaded gain +20、2644 月率 0、R198 maxdays0，以及 C 的路线分歧均不抵扣此资格。本文接续 [共同 T0 与三臂合同](episode04-r10-next-abc-t0-12004.md) 和 [总预算合同](episode04-r10-runtime-total-budget-12004.md)。

## 最小只读 wire

原先 callback 的 before/after 只有库存、更新时间与 updated byte，不能用事后驻留位置给历史事件归属省份。现候选增加可空 `before.province_id`、`after.province_id`，直接在原生 supply callback 进入、原函数返回时分别采样。

[journal](../../ck3_autonomous_player/native_bridge/src/ck3_12004_actual_supply_callback_journal.cpp) 复用既有 `ResolveArmyUnit`、`ResolveInternalArmy`、`ResolveObjectiveProvince`：完整 public/native ID 解析到的 Army 必须就是 callback receiver，Unit+0x178 backlink 相符，再读 Unit+0x20 的当时 Province 指针、Province+0x10 ID，并与既有 Province resolver 返回指针相等。绑定使用现 .4 Army binder 已有的 Unit/Army registry slots 与 `kGameStateSlotRva`，未扩地址研究范围。

解析失败只令省份为 null；原 stock/identity capture flags、journal 保留规则、原函数恰调用一次及原正常执行守卫不变。省份读取不调用 supply updater，不作 query 或动作。[owned DTO/serializer](../../ck3_autonomous_player/native_bridge/include/xar_bridge/army_actual_supply_callback_observations_v1.hpp) 只序列化捕获值。

[严格 parser](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_actual_supply_callback_observations_contract.py) 兼容旧三键 Values：旧缺省继续缺省，显式 null 保留未知；已知值只接受 signed int32，拒绝 bool 与溢出。summary 仅在原字段存在时透传 `province_before_id`、`province_after_id`，不从当前位置回填。

## 可复用语义 consumer

[strategy_b_site_growth.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_site_growth.py) 是普通离线 validator。它消费 frozen plan 的两个 site-input pins，并校两处 distinct Province 的原件、runtime、正常逐日 clock/endpoint 链、同 Army/native 实例、完整 ArRg/DATA/最大值/统帅身份、同省静止端点及实际正库存差分。新 callback 必须晚于 before 的 journal fence，日期与完整 CDate64 一致、无捕获失败，逐事件 stock 链对齐端点；**每个事件的 before/after Province 都须等于该驻点**。跨省、缺省、null、无实际正 delta、复用同一 callback 均拒绝。

该 validator 不证明未来安全、全程可通行、士兵 ADD、损耗或军费；现 B execution 原有 `site_stock_growth_semantically_qualified=false` 是明确能力边界，不能仅凭两份原件 pins 改成 true。正式 B 准备须先调用此语义 validator；只有两处真实正增长原件合格才可授予该项资格，返回结果本身不授 live/场次权限。

```text
python promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_site_growth.py --repo <repo> --evidence-root <root> --plan <plan.json> --plan-sha256 <sha256> --output <new-result.json>
```

所有路径由调用方显式传入；无机器、PID、run、scene、q 或容量默认值。site-input 使用 `xar.e04.B-rest-site-input.v1`，字段为 `province_id`、`army_id`、`runtime` 原件 pin、`normal_day` 原件 pin；不能放两份无地点/正增长语义的任意文件替代。

## 验证和部署边界

[可移植测试](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/test_strategy_b_site_growth.py) 保留两项本轮新增 compound：parser/summary 的缺省、null、已知省份、类型边界；真实 endpoint/DATA/clock consumer 的同省链接受与 before/after 跨省、缺失、null 拒绝。链测试只有原件 IO 为带 SHA 校验的 RAM fixture，所有数据均 synthetic，不是真实增长点。

机器记录：`machine_id: desktop-3fevhd2-1c74096080`；2026-10-17 本轮外置新增两项各实际 PASS，移植后只核 canonical import/相对路径，不重复旧 13 项或旧矩阵。**native 编译与实际 callback before/after Province 样本均 pending**；Python compound 不授予 native 资格。本轮未新增或运行 C++ 镜像 fixture。Root 计划在下一真实构建后，沿 R199 原定 one-day 前后 army-strengths 查询核实际事件省份和驻留 2635；这只是待执行验证，现有 a34b/R198 不能追认已运行该 wire。精确来源、postpins、命令和时间保存在本轮 `r10-b-callback-province-wire-a01` 小型交付回执；旧 sealed 包及历史原件保留不改。
