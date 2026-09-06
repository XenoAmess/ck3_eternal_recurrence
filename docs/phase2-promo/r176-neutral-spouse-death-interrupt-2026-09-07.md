# R176：中立配偶死亡通知中断取证

## 结论

- R176 在同一 CK3 PID `68028` 上先后完成 TGP 宅族请愿与 `birth.1010`
  精确选项提交；两项后置事件实例均已推进。
- `date_raw=53159208` 停于原版 `death_management.1000`。玩家 32904
  仍存活，死亡角色是配偶 32797；这不是玩家死亡，也不是天朝产品错误。
- 原版事件有 3 个互斥创作选项。本帧无 like/dislike 标记，只显示 authored
  option 2 / native index 1；该分支只结算普通配偶记忆与性格相关压力并结束。
- 精确作用域是 `new_memory:character_memory`、
  `surviving_consort:character=32904`、`dead_character:character=32797`、
  `deceased_character_stress:value`、`realm:landed_title`。

## 修复与边界

- 新增单用途死亡通知合同文件，固定 5 个 scope、3 个创作选项、唯一可见
  native index 1，并拒绝把玩家本人当作 `dead_character`。
- 未给玩家或配偶追加新 buff；已有 survivability 夹具保持不变。
- 产品运行时阻断诊断数为 `0`，R176 reconnect 启动/重启次数均为 `0`。

## 证据

- report：`Z:\p2r176promo_resume\report.json`
- native state：`Z:\p2r174promo_a_native_state\native-session\driver-state.json`
- 原版源：`Crusader Kings III/game/events/death_events/death_management_events.txt`
