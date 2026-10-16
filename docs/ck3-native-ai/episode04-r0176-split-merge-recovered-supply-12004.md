# R09：R0176 原件补回库存、容量和合军权重

本轮仅复核已闭场的 **R0176**：`desktop-3fevhd2-1c74096080`、正常 Robert31254、PID4992/create134365619855039955/gen1、episode `native-31254-ab05e6628183`、日期53146632、源码 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`、CK3 1.20.0.4/build25734779。R0175 的普通角色读取和旧 .3 B 合军不是这次拆合。没有新 SDK、游戏、EXE、原生夹具或拍摄动作。

旧小投影省略了 stock/cap/weight，不代表原生字段缺席。本轮一次顺序读取并核对三份具名 response-local Driver 原件（38,751,601 /46,590,523 /38,735,110B，合计124,077,234B），恢复以下实际 raw/Q100000。没有复制124MB原件。

| 阶段 | 原生身份/缓存人数 | 实际库存/容量 | 合军 D 角色权重 |
|---|---|---|---|
| F0 | CUnit93→CArmy85，250/250 | 100/100 | 250 |
| F1 | 93→85，75/75 | 100/100 | 75 |
| F1 | fresh sibling162→CArmy155，175/175 | 100/100 | 175 |
| F2 | 93→85存续，162消失，250/250 | 100/100 | 原始结果单独保留 |

split 两军都实际复制了库存100，没有除二。固定方向93←162的原生产 `compare_merge_supply` 得 wD=7,500,000、wS=17,500,000；share=30,000/70,000，term=3,000,000+7,000,000，preclamp=10,000,000；实际 postcap、poststock 同为10,000,000，`NATIVE_WEIGHTED_SUPPLY_MATCH`。**等于容量不是 upper clamp 阳性**；两军初始库存相同，也不把这个样本说成能独立区分所有加权算法。

strict unrelated freeze 的失败是实际变化：Army18 的空 DATA、cache1/1 ArRg59 消失，1196/1196→1195/1195；原生 Character predicate、完整角色叶及独立统帅读回关联 Character34232，其成为新162和合后93的实际统帅。原 strict=false 保留。全部 available 军的 unique physical DATA 和按 ArRg occurrence 都守恒；94/95不变。16777321始终 `native_carmy_not_found`，不能补零或声称全 roster 兵力完整。这不是缺少 fullidentity 或GUI造成的假失败，也不是一名实体士兵死亡。

原冻结 R09 卡允许解释合法换将/角色结果；它同时要求从原 baseline 独立反方向和实际30–60秒拆/合/存续军/统帅/队列/供给画面。二者仍缺，因此 **R09 未闭卡**，没有新增动态或 ABC 信用。旧失败不改，新的 stock/cap/weight 字面复核可单独使用。

便携证据：[ZIP](evidence/episode04-r09-r0176-recovered-supply-12004/r0176-recovered-supply.portable.zip) 含三个 stage 的精确 scalar byte slices、原件全 SHA/size、offset、production consumer 输入/结果及 typed agent decision；[验证器](evidence/episode04-r09-r0176-recovered-supply-12004/verify_recovered_supply.py)使用仓库中精确 SHA 的现有生产函数，不带 SDK，不执行 relay stage。slice 本身不能重新计算整原件 SHA；脚本明确区分 excerpt/算术复核与已完成的整 raw 来源校验。DATA/角色原件继续引用 [已有字面投影](evidence/episode04-r09-selected93-12004/actual-literal-projection.json)，不镜像复制。

```text
tools/.venv/Scripts/python.exe -B -O docs/ck3-native-ai/evidence/episode04-r09-r0176-recovered-supply-12004/verify_recovered_supply.py --repo . --archive docs/ck3-native-ai/evidence/episode04-r09-r0176-recovered-supply-12004/r0176-recovered-supply.portable.zip --output <新外置回执.json>
```

下一次最短正例：若不能证明旧 pre-split 正常存档与 F0 完全匹配，先保存一个新的正常同日同地 S0；两个独立正常加载的臂各只 split 一次、按预注册相反方向 merge 一次，共4动作/6个必要完整 ordinary 端点。每臂使用实际 fresh sibling、完整 CArmy generation、当前 stock/cap/weight/角色和独立 commander，保存一次性 claim 与原 ACK；未知动作不重发。S0 不能取一次 merge 的终态再声称复用了旧无统帅 F0。

当前 `split_merge/root_relay.py` 已有 explicit `--source-head/--run-sequence/--module-pins` 和 `--live-binding/--live-binding-sha256`：新的 actual 绑定可使用新准入期限，旧知识页“只能旧07:45硬截止”的描述已过时。既有 strict guard仍保留；必须先落 full packet 再判定，合法角色变化逐FullID解释，不能删行来通过。供给字段、角色叶和 source 已发布，**不需要新增 native 字段或重新基础逆向**。下一 Root-only 操作卡详见本轮外置交付。
