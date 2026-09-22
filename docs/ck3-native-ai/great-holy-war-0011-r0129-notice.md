# R0129 `great_holy_war.0011` 信仰解锁通知：静态边界

## 冻结身份与现场

- CK3 为 `1.19.0.6-steam23530548`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。原版 `events/religion_events/great_holy_war_events.txt` SHA-256 `E431A0E2FDFF5E49FB572B7184DE9B498F982B95AED875334AD1432D0F88CBA7`；`common/on_action/religion_on_actions.txt` SHA-256 `52D172C10A8164B007382F9DF79A48DE462CF6B390438158FD37C9B34DF8F75C`。这些值与既有共享记录相符；本次只核对该事件，不扩展信仰机制。
- R0129 用正式源码 `3559c0f297b4ce5e7147e9d625303f45716944be` 从 h2083 冷恢复，55/56 turn 后在 turn56/raw53392944 以 `planner_blocked` 停止；`great_holy_war.0011` instance25，玩家36403，`war_ids=[]`、`army_ids=[]`，**0 选项提交**。[原始 formal report](Z:/ck3_mod_rewrite/.task-tmp/RUN-001/war-h2083-continuation-source3559c0f-nolaunch-20260922/R0129-formal/formal-report.txt) SHA-256 `2707E485278965761879C60F6858988B0458CED27BB333391BF5E1F566B9AE2F`；原报告字节保留，字段提取遇非 UTF-8 段时使用替换解码，不重写报告。进程树及 owner 已回收。
- 最后持久 h2145/raw53392392 save SHA-256 `AA5D2294237EAC6CCC4DDAC83786AE9864265C5431733E06CBAD1D35B9FCE807`。R0129 的 driver SHA-256 `3B20E68C8AC03F3226A5D17FE869DB268883A4B473E171C609313D528D163E03` 在 checkpoint 后还有 #2146–2152 七条未配尾，含 #2151 成功 `life-advance` 和 #2152 事件查询；不能把 RED 观察帧当作持久配对或日期进度。后续恢复须走官方语义裁切。

## 原版调用链与选项

```mermaid
flowchart LR
    A["on_faith_monthly<br/>每个 faith 的月度 on_action"] --> B["隐藏 .0010<br/>解锁 GHW 宗教变量"]
    B --> C["every_player<br/>广播 .0011"]
    C --> D["五个互斥 trigger 的通知选项"]
    D --> E["共同 after：custom_tooltip"]
```

原版 `religion_on_actions.txt:578-588` 把隐藏 `.0010` 放在每个 faith 的月度事件列表；`great_holy_war_events.txt:989-1133` 在 `.0010` 的 immediate 内先设置解锁/冷却变量，随后通过 `every_player` 发送 `.0011`。原版将 `.0011` 标为 `#Flavor Fluff`；其五个 `option`（:1343-1390）只有展示 trigger 和名称，没有选项 effect，`after`（:1392-1395）仅有 `custom_tooltip`。因此选项本身是通知确认；它不证明玩家已参加圣战，也不证明任何战争物质结果。

同一暂停帧的原生事件查询为 `native:80`、instance25、authored `option_count=5`；唯一物化行是 rendered0/native4，`shown=true`、`enabled=true`。ROOT 为玩家 Character36403。保存作用域为 opaque `awakening_faith`、Character57718 的 `ghw_first_sponsor` 与 `background_temple_scope`，以及同一 Character57718 的 `other_pope`；后者来自 `.0011` immediate 的条件性本地化作用域。原生 effect indicator 空列表的 `complete_effect_set=false` **本身不证明无效果**；无选项 effect 的结论来自上述冻结原版脚本。

## 当前消费者缺口与授权边界

共享 registry 已有 `.0011` 的旧现场合同，但它对应先前 hostile-faith 的唯一 native3、三个保存作用域。R0129 是唯一 native4、四个作用域。当前 `vanilla_events/policy.py::recommend_registered_vanilla_event_option_v1` 首先因 `character_scope_matches_any`、`unique_character_scope_excludes` 尚未在该事件的 direct consumer 准入而返回 `registered_contract_requires_extended_consumer`；即使只开放这两个字段，旧 option/scope 投影也不能直接用于 R0129。`strategy.py` 在已注册事件返回 blocked 时保持 RED，不会转入唯一可选项的 degraded fallback。先前其他场景的 `.0011` typed 消费不能证明这次投影已经受支持。

此事件由信仰月度解锁广播，R0129 当帧无战争，不属于已经明确允许的“战争中的圣战/大圣战”窄例外。当前不提交宗教专用策略、typed 选项或手工点选，R0129 产品 RED 保持。若所有者允许**通用 exact-build 无效果单合法选项确认机制**处理这类通知，最小复用入口是共享 registry consumer：以冻结脚本哈希证明每个可选项与共同 after 的效果边界，并在同一 paused frame 严格匹配 event identity、ROOT、完整作用域、唯一 shown+enabled native index 和正确 typed step；随后仍须实机独立后置、下一 turn 与配对恢复。该方案不需要推导 faith/doctrine/tenet/fervor，也不能仅凭空图标启用。旧 R0118 WarID251658364 的战争 RED 另行保留。
