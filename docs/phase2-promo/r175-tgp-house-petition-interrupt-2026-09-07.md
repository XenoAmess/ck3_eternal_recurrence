# R175：TGP 宅族请愿中断取证

## 结论

- 保留的 CK3 进程 `68028` 在 `date_raw=53158008` 停于原版
  `tgp_decision_events.0101`；未重启游戏，产品阻断诊断为 `0`。
- 本帧是原版 `tgp_decision_events.0100` 生成的宅族成员省制变更分支：
  `house_movement_member=province_change_recipient=28087`，同时保留独立的
  `other_movement_member=26378`。
- 完整已保存作用域为 8 个：`petitioner`、`actors_movement`、`hegemon`、
  `petition_recipient`、`province_metropolitan`、`house_movement_member`、
  `other_movement_member`、`province_change_recipient`。
- 三个原版选项均可见可用。固定选择 authored option 3 / native index 2；
  它拒绝请愿并清理请愿变量，不打开 option 2 的还价后续链。

## 修复边界

- 将这一事件的完整合同移至单用途文件
  `tools/zg361_phase2_promotion_manager_tgp_petition_contracts.py`。
- 新增精确 8-scope 变体，只接受宅族成员与省制接收人为同一角色；不会把
  任意继承角色作用域当作合法接收人。
- 保留已实证的 5-scope 法律、7-scope 省制和 9-scope 完整成员变体。

## 证据

- retained source：`Z:\p2r174promo_a\cell`
- reconnect report：`Z:\p2r175promo_resume\report.json`
- native state：`Z:\p2r174promo_a_native_state\native-session\driver-state.json`
- CK3 PID：`68028`
- 启动次数：`0`（本轮 reconnect）
- gameplay transport：native MCP；OCR/坐标未用于状态或选项判定
