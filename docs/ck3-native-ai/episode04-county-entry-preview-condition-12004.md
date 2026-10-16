# 1.20.0.4 preview 第一条边的县条件

本增量在既有 `preview-move-army-N-to-N` 结果内增加可选 `route_preview.county_entry_condition_v1`，没有新增 MCP、Move 或目标选择器。适用源码基线 `c4992c304d196135d9590799d69ffb3c9f5510e6`；不依赖 a11 的 Move core-frame 修复。旧版本 adapter 不发布此 child。

机器相关记录：`machine_id: desktop-3fevhd2-1c74096080`；本轮离线行为检查时间和文件 pins 见外置交付的 `TEST.actual.json`、`ROOT-DELIVERY.actual-a12.json`。这些检查没有连接游戏。native 编译、collector/serializer 执行与实机验收均未运行，不能据此授 R04 positive。

## 实际读取和调用

沿用 `.4` 已绑定的 `ArmyBindings.county_entry_condition`，即 `24E2230`：`bool(CCharacter *actor, CProvince *source, CProvince *target, int32 mode)`。由现有 `WorldAccess` 和 Army resolver 得到对象，核对 CUnit/CArmy FullID 与 backlink、Unit+174 actor/Character+18、Unit+20 current Province，以及 Province ID/Prov magic。读 `Army+1D4`，按现有县执行 caller 的规则 `0→mode1，非0→mode0`。

`source_province_id` 是 preview origin；`target_province_id` 是 preview route 首个剩余 hop。route 若带 origin 前缀，只跳过这一项。`requested_target_province_id` 仍是原请求终点。多跳路线绝不把终点 predicate 冒充第一条边。没有剩余 hop 时 child 为 unavailable。

两项 `*_definition_1b_u8` 是 Province+8 definition 的 +1B 原始 byte。县对象来自 Province+848；发布 `*_county_present`、进程内 opaque `native:<address>` 和 `county_objects_differ`。这些身份只用于同一 child 的对象比较，不是 TitleID、法理父级或跨 query join key。目标县非 null 时读取 +3E0 raw magic。已读 null 和读取失败有不同结果。

输入完整后只调用一次原生 predicate；不自行调用、模拟或合并它内部重复的 target predicate。调用前后重读同一组身份、mode 和 raw gate 输入；读失败、变化或原生调用异常均只令 child unavailable，并保留原 preview 路线。外层既有 Driver paused-frame fence 继续有效。

## 严格合同与决策含义

`status=available` 必须同时具备 `inputs_observation_ready=true`、`native_condition_called=true`、`identity_before_after_match=true` 及实际 bool `native_condition_passes`；available false 是合法观测。unavailable 要有非空原因，`native_condition_passes=null`；不得补 false 或 0。部分已读 raw 字段可以保留，但不构成 condition 资格。

`source_county_present` 和 `target_county_present` 区分实际 null；unavailable 下 null 还可能表示尚未读到。ready 时 presence 必须与 opaque identity 一致，mode 必须与 Army1D4 一致。native true 必须满足源码已证的共同必要门：两项 definition byte 非0、源/目标县都非 null 且不同、目标 magic 为 `0x436F4461`。这些必要门全通过仍不能推导 native true；内部 actor/县关系等子谓词未发布。

`internal_subpredicates_observed=false` 和 `actual_loss_observed=false` 固定。不能用友方/敌方标签、owner 或 de_jure_parent 模拟 `2C09DF0`。available false 只证明该次同帧第一条边最终县条件 false，不授具体子门原因。B>0、两 byte 非0 和 native true 也只给县入境执行的前置条件；实际物理扣减仍要已有 R04 writer/DATA 证据 consumer。

智能体沿用同帧既有合法 preview 请求，例如 `preview-move-army-18-to-2645`。读取 `/route_preview/county_entry_condition_v1`，并保留结果外层的 `queried_*` identity 与 `/route_preview/previewed_date_raw`；不能把 R0180 历史的 2635→2645 false 当作下一场准入。多跳 child 只覆盖首边；下一边要在下一场新鲜 preview 再读。

## 源与验证边界

实际 `.4` predicate 完整420B `[24E2230,24E23D4)`，原件 source contract SHA `3e43b5d98b9e13c497c8437818c3fd24c028dd4a60f41814aae7f7d6ae8ab544`，body SHA `d011c6bb38172950e99324f1fa7157d0083cbe5316587b7945ed5b168f80370c`。持有包 `C:/ck3-e04-resume-20261015-a01/newcounty-condition24E2230-source-a01/SOURCE-CONTRACT.actual-a01.json`；无新 EXE 读取。其正式分支说明见 `episode04-county-entry-condition-12004.md`。native bindings 和 ABI 沿当前 `.4` binder/current-input reader复用。

聚焦离线检查只运行新四项：available false 穿过实际 Driver；unavailable child 保留成功路线和 unknown；多跳 child 错绑终点被实际 Driver 拒收；旧 child 缺席仍兼容且 available 缺 actual bool 被 strict normalizer 拒收。DTO、hello/state 和 endpoint 是显式夹具；没有声称它们来自生产 native serializer。

```text
python -B ck3_autonomous_player/tests/unit/test_county_entry_preview_condition_v1.py --source-root <repo> --candidate-root <repo-or-external-candidate> --receipt <external-test-receipt.json>
```

合入后的必要下一步是按项目正常 producer 构建并取得 fresh `.4` preview 的生产 wire，核 native bool、raw gates、first-hop IDs 与 strict Driver 一致。本增量不自行触发构建或实机。
