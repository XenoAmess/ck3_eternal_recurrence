# a01 文案精确性补注

machine_id: `4-8e1c2f1861`。2026-10-18 UTC；本补注针对冻结的 `ai-callgraph-review.md`（SHA `5fa36b1bc1ba265f1168bce06c94ca3dbf1912018090e6844571923d93965f5a`）。原文与原 `DELIVERY.json` 不覆盖。

原稿两处“和平时期 AI 决议”应统一写为**圣地管理 AI 决议**。这只是与围攻事件区别，原定义没有 `is_at_war=no`，不能授予“战争中不会检查管理决议”的结论。`is_available_ai_adult` 中的 `in_army=no` 是执行角色可用性的一部分，也不等于整个领国和平。

静态链表里的 remove trigger entry factory `2B0D8A0` 只由注册入口的 RTTI/vtable 定位，本包没有审其构造体；`source-contract.json` 已明确 `factory_body_not_reviewed=true`。不要把图中的高层静态脚本合同宣称为每一条中间工厂指令都已逐条闭合。供奉 trigger factory、两个 effect factory、四个实际 trigger/effect consumer 的精确分段和分支检查范围以原 manifest 为准。
