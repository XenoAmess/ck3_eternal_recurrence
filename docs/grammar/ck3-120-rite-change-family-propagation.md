# CK3 1.20：婚后改宗会连带改变无地配偶

`machine_id: desktop-3fevhd2-1c74096080`；观察时间为 2026-10-23T20:35–20:44Z。实际 CK3 为 1.20.0.4 / Steam build 25734779，EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。来源是超人强 R0028 的真实失败基线存档及当前安装的原版脚本。此处记录可复用的测试准备陷阱，不给该产品的月度模拟或通知排查授予通过结论。

准备两个不同信仰的已婚角色时，不能假定对其中一人调用 `set_character_faith` / `set_character_rite` 只影响该角色。原版 `common/on_action/religion_on_actions.txt:998` 明确说明 `on_rite_change` 在信仰或礼仪改变时触发，出生、创建角色等初始赋值不触发；同文件 1261–1264 行把 `faith_conversion.0003` 加入事件链。

`events/religion_events/faith_conversion_events.txt:199–228` 的实际分支要求候选仍属于旧信仰；若新旧信仰同宗教，还须保留旧礼仪。候选还须在世、是 AI、没有 `ai_will_not_convert`，且不是宗教领袖或礼仪领袖。满足条件的无地配偶会执行 `set_character_rite = root.rite`。该事件也处理其他近亲，不能把“未显式写配偶转换效果”当作没有家庭传播的证据。

R0028 先把双方创建为操作者的信仰和礼仪，结婚后才转换妻子。独立解码的 1066.9.17 存档显示双方完整身份 65810、65811 均绑定礼仪 6；操作者 31254 和其余十个夹具角色绑定礼仪 0。实际存档数据库映射为：0 = `roman_rite` → faith 13 / `catholic`；6 = `byzantine_rite` → faith 14 / `orthodox`。跨信仰断言失败，其余十一项角色前提通过；十一名在世角色经验变量存在且为零，死者经验变量缺失。缺失不等同于零。该存档只证明最终状态，未捕获 `faith_conversion.0003` 的逐次执行 trace，不能区分两个 setter 中哪一次具体触发了传播，也未解释丈夫没有转换标记这一差异。

有原版来源依据的最小准备方式是：创建角色时直接指定需要的信仰与礼仪，再建立婚姻，保留实际日期推进后的双方信仰和婚姻断言。它避免本例的婚后转换入口；仍须新实机核验，静态解析或来源注释不能替代该后验。不要放松断言，也不要将失败存档作为成功基线或冷重载种子。

原版文件 SHA-256：

- `religion_on_actions.txt`：`ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d`
- `faith_conversion_events.txt`：`690962331397af4f0a0a4b9d92bf4b6f6c320f400e7c65c34716e8cbad488ec0`

精简独立来源回执为 `C:/ck3-superman-validation-20261023/ops/R0028-crossfaith-stock-chain-a01/EVIDENCE.actual.json`。真实 SAVE 为 68,341,621 B，SHA-256 `7625b154ed4967369020c0432b5ff8796563f2321638014300789016cee96264`。外置原始证据按共同存储策略 1.0.0 的 30 天期限评估；本知识条目于 2027-04-21 复核来源适用范围，不授权届时无条件删除必要原件。
