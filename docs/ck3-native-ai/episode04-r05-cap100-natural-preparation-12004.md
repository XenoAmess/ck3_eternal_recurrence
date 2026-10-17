# R05：正常降容量与一次自然库存裁剪准备

**可以用正常换将后的低容量，加一次成功自然供给更新，把仍为300的库存裁至100；不能由容量getter或任命ACK证明立即裁剪。** 这是准备入口，不是归零或饥饿扣兵验收。R197旧任命unknown/noRetry保持。本包不发SDK/UI、不构建、不改main、不读新EXE。

本轮新增只把既有已闭源码与Root提供的慢率条件组合，给出有限准备决策；没有新native body或实机事实。来源精确pin与条件算术见[索引](evidence/episode04-r05-cap100-natural-preparation-12004/source-index.json)和[计数](evidence/episode04-r05-cap100-natural-preparation-12004/conditional-counts.json)。本机来源记录machine_id为`desktop-3fevhd2-1c74096080`；原场次与观察时间沿各原件，不外推其他机器。

## max与current的两条真实路径

Actual4容量完整函数`2C53BF0..2C541F9`、1545B、SHA`b204d281bd06699cbd6863383696d131ff798c91168d79c7467e8879386c3873`已入库。null-details路径取当前Army120统帅及真实aggregate：`fixedmul(wrap64(loadedFULL+A467),wrap64(100000+M468))`。无效统帅走loadedFULL。输出store在`2C540FC/2C5414F`，不是Army180库存store；本getter不提供库存clamp。持有原始JSON57468B已核pin，仅摘取相关指令，未新读EXE。

[R196](episode04-r196-cap100-and-multiday-preparation-12004.md)确实观察过10名legal cap100候选，34232质量27；其capacity字段由loaded FULL100、A0、M0得出，不是把missing modifier补0。这个名单是历史当帧事实。R200必须fresh确认实际FullID、available、final eligibility、can_assign、条件叶来源和正容量；不能追认仍合法，也不能由467/468猜新统帅1A9或损耗率。

Actual4成功updater`24E4CF0`不同：准入→rate getter`24E5180`→`24E4E6F`向Army180加一次signed64 whole rate→调用当时容量`2C53BF0`→`24E4E8B..24E4EB6`写负值0或非负值与cap的signed最小值。故S300/C100且本笔S+r≥100时，poststock为100。这里确实写current，不是UI百分比。拒绝准入不更新库存；Army22=1在准入前已写，不能代替成功证据。

普通任命是否在没有该updater时另行立即clamp：**尚未证明**。已闭`.3` executor→setter写Army120→stat-cache refresh的知识不自动给`.4`完整后处理授资格；`.4`现有迁移记录主要闭factory/validator/正常队列，不能从中排除所有transitive effects。也不能把“没证明立即clamp”写成“证明绝不clamp”。

## 为什么这仍不是短场归零方案

仅在实际新统帅也读到r=-175438、每次cap固定、每次准入、无overflow时：

| 起点 | 首次<10的更新序号 | 首次0的更新序号 |
|---|---:|---:|
| S300/C300 | 166 | 172 |
| S300、已实际C100，首笔自然clamp | 53 | 59 |
| 已实际观察S100/C100 | 52 | 58 |

若再采用Root已有“首机会δ、后续每30日一笔”的clock前提，前两行<10为δ+4950与δ+1560日，到0为δ+5130与δ+1740日。没有从“月率”名称推调度。换将后的率未知，旧率不能直接继承；这些数值只解释规模，**不授权盲耗1560日**。cap降低的库存截断不是兵员损失，也不全算供给消耗。

## 最少正常准备步骤及停止点

1. Root现有normal queued18→2629照常推进；实际到达后绑定新鲜paused actor/episode/generation、双Army FullID、ordinary身份、当前统帅及S/C/r。93的special身份不替代ordinary S0。
2. fresh candidates选择真实合法低正条件cap候选；若实际已是该统帅，零重发。否则新scene新意图下正常assign一次，用PUBLIC revision与public CUnit FullID，随后独立typed统帅及完整Army读回实际S/C/r。R197未知动作不能成为自动续投依据。
3. 若实际C=100且S已≤100，准备已取得，正常checkpoint作为新的T0；不强求再造一次clamp。如果C仍300、身份/率不匹配或动作unknown，暂停该准备链并记录，不用条件容量补实际结果。
4. 若实际C=100、S>100，只给**一个source-derived当前军队的自然callback机会**的有限预算。使用现有受控自然窗口；到第一机会后读实际准入/stock。首机会需以当前时钟/实际occurrences定，不猜月初。预算不足、准入拒绝、modal或仍无有效读回时停止并正常闭场，不自动追加另一30日或上千天。
5. 若实际stock≤100，保存新正常checkpoint。若仅为合法prepare，实际独立S/C端点就可决定新起点；若要另授“该updater实际clamp”因果，还需同callback ADD/cap/store前后证据，不能拿端点差冒充抓到PC。

远离临界库存时可沿Root既有samplersOFF多日窗口；需要第一裁剪因果时只在该机会安排已准许的journal，不新开external observer。临界区/首零的采样与exact-day预算由后续独立R05场批准，不能借本卡扩大当前scene maxdays。

新T0只是更低库存准备。R05正例仍要同一自然callback的供给归因、完整unique physical before/after以及实际debit>0；stock0、getter、预算与围城扣兵均不替代。

## 可选源码缺口预算（未执行）

立即clamp不是推进上述一机会准备的先决条件。若Root另要闭此问题：先复用exact4现有缓存和constructor的secondary vtable`476A4C0`；仅在cell未持有时读`+8`一个8B cell，独立确定executor，禁止`.3`地址减常数。用已缓存pdata/unwind确定完整span，再决定body读取。

已有`.3`锚点executor`2971320..2971480`352B、setter`24DFA10`352B、refresh`24E8120..24E8206`230B。建议总新code上限1536B（只这三个实际映射body），metadata上限56B（8B cell+最多3个12B pdata/4B unwind头；缓存可复用则0）。任一跨度超界、CHAININFO或新未读callee均STOP，另报具名预算，不自动展开。这个计划没有为实际`.4`executor猜地址，也没有授予“无立即clamp”。
