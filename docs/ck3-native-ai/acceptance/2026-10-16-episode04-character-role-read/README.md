# actual .4 新角色叶：暂停普通 query 发布资格

结果：**ACTUAL_PAUSED_ORDINARY_ROLE_LEAF_PUBLISHED_AND_CONSUMED**。它只确认已部署 a06/dcda 普通 strengths 查询真实发布并能严格消费角色叶，不授 split/merge 现场、出生 producer、物理补兵、现任统帅或 Knights 成员资格。

来源/复核机器均为 `machine_id: desktop-3fevhd2-1c74096080`。Root 既有 R0175 的暂停截图前原生 snapshot 采集时间 `2026-10-15T17:20:11.178986Z`，来源代码 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。本轮离线复核的时间和实际生产 Python 代码 SHA 见 [QUALIFICATION.actual-a02.json](QUALIFICATION.actual-a02.json)。本轮没有 SDK/游戏/桌面连接或 EXE 执行。

精确历史绑定来自获准 baseline 的 `binding`，并与两个指定原件核对：PID16512，process creation `134365577928096099`，connection generation1，actor31254，episode `native-31254-13a1253fe701`，public Army18/native CArmy18。creation 值是 Root baseline 的绑定字段，本校验器没有另外探测进程。snapshot `native:5`、revision6/native revision5、date53145552；query 回指全部吻合。snapshot hello 的 exact .4 adapter ready/build_match/SHA 也吻合。

完整22个 ArRg 的 all-DATA 和新叶都通过实际生产 `normalize_regiment_replenishment_records_v1` 与 `classify_current_regiment_character_role_12004`：

- 11个 `55..65` 是已观察到的有效 Character、空 DATA、缓存1/1，ArRg Army140、Character F8 与当前完整 ID 对应。
- 其余11个叶为已知 noncharacter。两种输出都不是缺字段补 false。
- 未读取实际 commander/Knights 查询，因此消费者如实传入 unavailable/None，输出保持未知。F4/F8 和 role predicate 不替代这两种独立业务资格。

[packet-minimum.json](packet-minimum.json) 是明确命名的最小字段 projection：保留两个获准原件中对应 JSON 值、完整22行 DATA 及新叶、基本 strength 行和 frame/binding；有原件大小/SHA和字段路径，绝不冒充原始完整响应。原 strength4738729B、snapshot143905B不重复复制；projection49862B。它不是新采集、两帧转换或 split 结果。

跨机器只读复放：

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-16-episode04-character-role-read/verify.py --repo-root <checkout> --machine-id <当前机器ID> --output <新的外置回执.json>
```

另一机器复放通过，只能验证这些历史字段与当前生产消费者兼容；不能把来源机器的安装、部署、进程或实机发布事实外推为目标机器事实。source-a04 的静态闭合及未来 split 后置断言见 [拆半源码专题](../../episode04-split-half-source-12004.md)，两类资格独立保留。
