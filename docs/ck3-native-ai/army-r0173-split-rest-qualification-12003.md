# CK3 1.20.0.3：R0173 原生拆军与两处休整资格

R0173 已观察到合法拆军、两处驻点正补给月值、一次主军实际补给增加和独立的整数兵员增加。这里完成的是数字资格；正式 A/B/C 仍 **0/3**，成片、clean span、人工签核信用均 **0**。

[可移植原始证据索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0173-split-rest/index.json)与[只读复核代码](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0173-split-rest/review_frozen.py)一同保存。代码只读相对文件，无游戏、SDK、网络、C 盘来源或媒体依赖；stdout 是派生报告。原始 JSON 字节没有重新序列化。

## 同一有界资格时钟

Root 在 90 日协议中冻结原始 Jan20 起点 raw `53147376`，绝对终点 `53149536`。R0173 从原+44日的未拆整军保存冷载：73795635 bytes，SHA-256 `d052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a`，原始保存只提供小型 pin，不复制大存档。重新加载不重置预算。最后实读原+76日 raw `53149200`，还余14日；这不是后来 ABC 各臂的时钟。

本次资格协议与旧 R0171 的30日尝试各自保留。旧尝试并未推进日期。预冻结90日资格及录像续接的理由保存在 [Root 原协议](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0173-split-rest/inputs/protocol.json)。后续正式 ABC 必须另冻结同一**未拆整军**存档的 SHA、人物/战争/军团/统帅/现金及同一有限终点，逐臂冷载。不能把本次已经拆军后的资格端点当三路共同起点。

## 原生拆军与五个窗口

在原+44日，实际 `split-army-half-0` 把27军团、6679/6747兵分成主军 public/native `0/0` 的15军团3337/3371兵，以及子军 public/native `204/199` 的12军团3342/3376兵。两组 FullID 不重叠，完整37条 DATA 身份及全部原始字段守恒。库存绝对量均复制为110.37716；实际容量分别300、100。public204不能当native CArmy199使用。容量差不是统帅身份的替代证据。

| 原始时钟端点 | 原始包 | 实际变化 | 能说明的内容 |
| --- | --- | --- | --- |
| +45→+47 | q01→q02 | 主军库存110.37716→106.13988；月值−4.23728；更新标记到+46 | 负库存变化，27军团/37DATA完整行无变化 |
| +49→+50 | q03→q04 | 两军都成为 stationary regular，route空；分别在2174/2327；月值均−4.23728→+20；库存不变 | 正月值资格已经出现，不能提前说库存恢复 |
| +64→+66 | q10→q11 | 子军110.37716→100，容量100；月值+20；更新标记到+65 | 实际超容量封顶，方向是下降；没有补兵或低库存回升 |
| +70→+72 | q13→q14 | 主军3337→3344，子军3342→3345；六条DATA整数增加合计+7/+3 | 身份与max不变的兵员增长；库存及补给更新标记不变 |
| +74→+76 | q15→q16 | 主军106.13988→126.13988，容量300/月值+20；更新标记到+76；子军100不变 | 主军真实正库存写回；全部27军团/37DATA完整行无变化 |

数字固定点比例为100000；兵数比例为1。表内数值是清楚标识的派生展示，原 JSON 保留 raw 数字。

原+50日同一暂停帧的 typed commander 和 route preview 实读：主军在2174的当地limit4960/usage3337，子军在2327的limit4160/usage3342；统帅分别27357与33388。这只证明该帧，后续统帅稳定性需要新的独立查询。目标 London1527 的usage0不是 friendly/抵达后的总负担或将来正补给保证。

## 停止门禁与归因边界

原+52日外部1609围城/占领变化触发原 STOP；Root 保存差异与审阅后，只放行同一有限协议内的两处休整。子军超容量降至容量也保留了原 health STOP 和 Root 限定审阅。战争世界并非静止，旧 STOP 均未改为成功。Root 最终 coverage 勘误明确：2174/2327 未出现在 war objective rows，已读 Army/health/site inputs 相等不能证明完整 province occupation/controller/garrison 连续不变。未读取字段继续留空。Root 的 review 是端点审阅，不是人工观看成片签核。

全数组与更新标记只能证明保存端点的实际值变化；它们不提供执行时 producer PC、应用补员账本、精确结算时刻或死亡归因。+72日六条 DATA 增长与已知日历补员来源一致的独立小案包含完整 source 语义边界，但不能升级成调用栈证明。一次补给增加和兵员增加分别有实际端点，二者没有被拼成同一次结算。

原始 health.source 中 game_version/executable_sha256 为 null，继续原样保留。Root 协议独立 pin 匹配源码提交 `7f1db1a773e647b9f31378d4a9ccf57a60cf9e73`；离线复核不补造缺失版本/进程字段。

## 当前仍待完成

Root 实际保存并关闭本资格 session：split 资格备用保存74386976 bytes，SHA-256 `c43f71c4973e035e04fb44609ba86f04407beb7af1a775191e09fddb9e943b66`，不是 ABC 的未拆共同起点；该共同 whole 仍为 d052…。SDK/keeper 退出、GameJob0、tree gone、watchdog absent 及 native inventory 空已保存。owned Game termination exit1、supervisor exit0 与 GameJob0 是不同字段，原值没有改写。正式 ABC 共档选择、C 的不同实际路线、完整应用账本/死亡归因/加权合军封顶、录像范围及人工成片审阅仍是独立缺口。本包不读取、拷贝或扩大 raw 媒体共享范围。

Root 最后原图审阅小收据只记录实际暂停画面，且明确在已结束900秒原片之外、无 encoded timecode binding；不复制 PNG，也不授 clean span、1×人工观看或 signoff。
