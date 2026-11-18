# CK3 1.21 故事实体与报价作用域

2026-11-18，machine_id: 4-8e1c2f1861。来源为本机1.21.0/build26622941原版静态文件。本条沉淀金融Mod原型中可复用的脚本规则；没有启动游戏，不授保存、死亡回调或界面作用域实机通过。

## 静态来源已确认

- common/story_cycles/_story_cycles.info:15–23：on_owner_death 在故事作用域执行，可在此设置新 owner；visible 是布尔值。
- 同文件118–140：effect_group 可指定 days/weeks/months/years，triggered_effect 在故事作用域执行。
- common/scripted_effects/00_scripted_effects.txt:61–84：原版使用 create_story / save_scope_as 并给故事保存变量。
- common/story_cycles/ep3_story_cycle_restoring_rome.txt：原版用 make_story_owner 转交同一故事。
- common/script_values/_script_values.info:33：ceiling 向正无穷取整，不能与四舍五入混用。
- common/scripted_triggers/00_economic_triggers.txt:8：原版提醒链中使用的保存作用域需要清理，否则影响后续调用。
- common/scripted_effects/00_personal_details_effects.txt:429：原版主动 clear_saved_scope，防同一 effect 连续执行时复用旧对象。

## 对脚本实现的约束

create_story 或随机选取前先清理将接收结果的命名作用域。只有本次成功取得且类型、owner及业务身份匹配的对象才能初始化或付款；不能仅看到 exists 就把链中残留的旧对象重置。具体创建失败时引擎如何处理别名仍待实测，清理是防御做法。

用故事承载业务身份时，技术 owner 与法律受益人分开保存。转交技术托管不自动赠送资产；无继承人保留原受益人引用并冻结处置。继承后的公开发现入口也必须接线，不能只证明“故事还在”。死亡角色引用在长期存档裁剪中的行为仍待查明。

报价至少绑定资产实体和修订号。两个币都可以有 revision=1，所以只比较 revision 不能防止选币变量变化后交易了另一资产。界面事件上下文、当前资产和报价必须匹配，资金与库存要在实际执行时重验。事件链中保存作用域的持久边界须用实机并发/重载用例验证，不把静态组合当成保证。

每份持仓若恒以整手增减，可逐份成交；加入赠送碎币或分割后，要处理多份不足一手的聚合，不能让总余额足够却永远卖不出。

## 原版文件 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| common/story_cycles/_story_cycles.info | 0425928302aba86630575ee90b092317c0b155ea018461fee29733996e12aa04 |
| common/script_values/_script_values.info | 68f615a899a1690af01cfd233ab73acd096778d93d1f5227a6e8d5b80adf4310 |
| common/scripted_effects/00_scripted_effects.txt | 53aadb834f3f9c666fbb4f69dc9456dbbcf9d9ee01ad6302a8e44a40966723de |
| common/story_cycles/ep3_story_cycle_restoring_rome.txt | a603e0b00c9422d13e6a5fb6c33e9faef1477e1afb3331a9ebf4e700e3dd4ad9 |
| common/scripted_triggers/00_economic_triggers.txt | c4014ba0909237ffa2c562fc56d62d47bfacef53730dc04d3d80cc0c8b785622 |
| common/scripted_effects/00_personal_details_effects.txt | 259adcc14974d53a2423f1aadcb0f3a8708b7b37913f3157a307639d432fd41a |
