# actual .4：合军S端flags0权重包含哪些ArRg

**合军被吸收军S的权重不是“允许补员/供给损耗eligible的实体人数”。** actual `2A95720(vector,flags0)`在完整有效ArRg roster上直接求缓存current38之和；空DATA但cache1/1的Character记录贡献1，另有来源证明当前不可补员的special也不因这个事实被排除。D端仍使用两个独立native getter，不能照搬此结论。

来源机器 `desktop-3fevhd2-1c74096080`，EXE1.20.0.4/build25734779，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本增量复用county owner在2026-10-15T17:15:44.821131Z已持有的187B完整body，三元数据分片 `[2A95720,2A95740)`、`[2A95740,2A957D3)`、`[2A957D3,2A957DB)`，逻辑SHA `41a9ed726a77ad4e72fa486b16b6dda4a941d1c94dc6d0972e6d10b94dec8ea5`。本次机器身份重新由 `tools/ck3_live_run_id.py machine` 读回；本次读held文件时间与source base记在相对 [source-index.json](evidence/episode04-merge-source-weight-flags0-12004/source-index.json)。0新EXE读取/哈希，0游戏/SDK/桌面/构建，旧检查不重跑。

函数RCX指向ArRg FullID向量descriptor：data在0，count在C，元素宽4。它逐occurrence解析低24位索引，再核对象完整generation ID、`ArRg+14 == 0x41725267`及ID不是-1。解析失败走原生fallback，再按同样magic/ID判定；无效记录跳过。它不把物理persistent/chunk token当循环元素，也不对ArRg ID或DATA token去重。正常生产reader必须仍保留完整roster、generation/backlink和重复拒收；不能把原生无效对象跳过路径解释为“该军兵数合法为0”。

| flags路径 | actual指令 | 对计数的作用 |
|---|---|---|
| `flags & 0x01`非零 | `2A95797/9B`；从ArRg18取定义，`2A957A1/A8`查定义2A0>0 | 命中时跳过该ArRg；本增量不把定义2A0命名成某个玩家军种。 |
| `flags & 0x02`非零 | `2A957AA/AE`；`2A957B3→2A956B0`，false在BA跳过 | 这是现有provider绑定的 `is_regiment_supply_loss_eligible`；它与补员Can是不同入口。 |
| `flags == 0` | 9B跳AA，AE直接跳BC | 两个过滤都不执行，BC直接`add ebx,[ArRg+38]`，D3把和放EAX返回。 |

因此flags0没有可达的下级CALL：唯一CALL `2A956B0`在被绕过的flags2分支。为了回答flags0不需要新增其body读取，更不需要扫描writer/constructor。getter只累加寄存器和局部栈，不遍历ArRg DATA20/28/2C，不读persistent138/141，不调用 `262C6E0`、`2657EF0`或fresh fraction getter，也不根据当前commander重新解释每个ArRg。

实际merge caller是已持有的 `2C55180`：`2C5576F lea rcx,[S+38]`、`2C55773 xor edx,edx`、`2C55775 call2A95720`、`2C5577A movsxd rcx,eax`、`2C5577D imul rbx,rcx,100000`。相对索引保存这7条原指令及其已有完整caller source pin。即：

```text
S_count = sum(每个有效ArRg vector occurrence的缓存current38)
S_weight_raw = sign_extend_int32(S_count) * 100000
```

EBX是32位累加，未观察到饱和/溢出修正；普通已验证DTO范围使用其非负、与完整ArRg sum吻合的原生current。越界、负值、部分覆盖或generation错误不由消费者伪造正常值。生产 `ck3_12002_army.cpp` 读每条ArRg current38/max3C，并将完整sum与同flags0 native current getter交叉核验；所以既有merge消费者用S的 **合军前** `current_soldiers*100000` 是正确的数据路径，不需新增字段或重写公式。

| 观察对象 | 应使用的现有数据 | 不能替代为 |
|---|---|---|
| 军队current/cache总量 | 完整ArRg cache与native flags0 current交叉核验 | unique physical DATA合计 |
| merge S端weight | 原S的上述native current×100000 | `native_supply_loss_eligible`筛完的和，或S作为D的weight |
| merge D端weight | `merge_supply_destination_weight_raw`，actual24E0140+24E0280 | 本页flags0规则或任意人数等式 |
| 物理兵数及实际补员 | 完整DATA中的persistent FullID/chunk、值、backlink/occurrence与独立阶段证据 | 角色cache1/1或permission/rate本身 |
| 供给损耗/Province usage资格 | 独立 `native_supply_loss_eligible`与真实Province/owner/roster上下文 | flags0 current、Character writer-skip或CanReplenish |
| 补员资格 | persistent138与独立Can/chunk门、prepared/cache及实际ADD后验 | 此函数是否把某ArRg计入merge权重 |

空DATA Character若已独立证cache1/1，会给S_count贡献1、S_weight贡献100000，同时对unique physical DATA贡献0。这个结论来自真实flags0代码，不需要将其识别为Knight或现任统帅；角色身份和actual current commander仍分别读。R0176的ArRg59就是已证空DATA/cache1/1角色，但本增量未查询其作为S时的实际weight，不将源码条件值冒充新实机。该记录的移除可改变后续cache与S权重，不能据此宣称一名实体士兵死亡或被补回。

对不可补员special同样如此：只要它作为有效ArRg出现在S实际向量且缓存current>0，这个sum就加入其current；permission false、guard138=1、uses_supply条件或全局refill开关都不是flags0排除条件。任何关于split/merge/换统帅是否改变persistent类别或可补员性的结论，必须另查对应writer/真实DATA与permission，不从“计入权重”倒推其可补员。详见 [补员入口](episode04-special-troop-refill-eligibility-12004.md) 与 [库存顺序及fast域](episode04-split-merge-stock-weight-order-12004.md)。

给agent的规则是：保留ArRg缓存、physical DATA、S weight、D weight、供给eligible和补员门六类真实值；不要在计算S权重前按“看起来像特殊兵/1名角色/不能补员”删行。当前消费者已走正确S字段，本次只补source/决策知识，没有新protocol、API、业务测试或动作。视频可说“这个1/1不是实体补兵，但它在被吸收军的缓存权重里确实算1”；不能说“所以所有省级供给、D权重或补员规则也都算它”。
