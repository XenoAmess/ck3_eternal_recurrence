# P50R1：同一干净战役续行与恢复边界

`machine_id: xenoamess-full-tower-eb9d2c1186`。本页记录2026-10-18 CST的实际续行，
游戏观察截止2026-10-17T19:59:29.324518Z；离线小件核对封于2026-10-17T20:03:21.707197Z。
这是原1066干净战役在同一Game出生代上的继续，已经自然继承至40695；首次30年仍未到，
该节点的永久手动SAVE为0，完整视频尚未渲染，G2仍为 **6/8**。

本机路径缩写沿用交接：`N=D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep`，
`R=N/robert30-clean-campaign01/native25-cold-generation01`。
本页仅核对已封的小JSON、错误文本及小型源码，不读取活跃Driver、SAVE正文或媒体，不操作现场。
较晚状态须另取新鲜回执，不能把本页的PID、日期或NEXT当作当前准入。

## 同一Game与继承身份

P50R1的保留身份为Game PID51028／creation FILETIME134367033244212072、Native25，
原管道`\\.\pipe\xar-g2-robert-clean01-native25-20261017`。
`R/ROOT-P50R1-KNOWN-OWNER-LIFECYCLE-PIN.json`将该出生代与本机绑定；
`R/ROOT-ACTUAL-SDK-PROCESSES-PINNED-P50R1.json`记录启动时queue240520／FT134367375934821898、
app18280／FT134367375958766277。后者本身没有machine_id，须连同前者及本次来源封包阅读，
不能单独外推机器身份或当前存活。19:59的SEM901仍独立返回Game51028、connection12、
精确1.20.0.4适配ready，证明该次观察连接到原Game。

自然继承31254→40695及后继普通玩法已经实际发生，详见
[G2自然结果专题](g2-remaining-natural-outcomes-2026-10-18.md#1927z当前干净局自然继承与后继普通游玩已发生)。
原AUTO361不重放；364本地重消费、365原周期结算、Continue368、独立clear、SAVE374和FULL376的
证据边界保留原专题。AUTO361的7日与typed Close372内部另一次7日分别记录。
这是单次自然继承完成，M7的完整范围仍未通过；不能把本页修复与继续运行增加为第7项。

## 三次重入问题分别解决

统一小封包为`N/p50r1-feeder-epoch-amend01/ROOT-REENTRY-INCIDENTS-RESOLVED01.json`
（下称A），UTC2026-10-17T19:50:59.195323Z。
A明确只是`HISTORICAL_ROOT_POINTER_ONLY_NOT_A_RUNTIME_GATE`。
其中窗口17的169日running快照属于19:50:34的历史观察，不能覆盖后来219日失败事实；
toolsession92741是工具会话号，不当成OS PID。

| 问题 | 实际发生与修复边界 |
| --- | --- |
| FULL406发布后字节pin失败 | 请求确已唯一发布并执行30轮，cycles5574／raw53339784，结果为`bounded_loop_finished`。发布文件95 B、6个CRLF，与预验89 B LF不符，才报`actual published FULL differs from preverified intent`。修复先用同一实际文件writer落盘冻结意图字节，再发布核对；原406消费一次、没有重发。不能把pin失败说成没有游玩。 |
| 已发布FULL469遇feeder source epoch失败 | base import报`partial feeder source epoch changed: compatibility_slot`。失败runner新增发布0、ledger写入0；469原请求没有重发。旧feeder仍绑定旧settled_summary slot，新严格parser消费已明确安装的追加epoch，并保持其余旧source逐项精确绑定。实际完整`prepare_feeder`资格已通过。 |
| 首次安装amendment缺少R import | CLI报`ModuleNotFoundError: root_p50r1_sentinel_partial_feeder_gate`，新增发布0、runtime安装0。此前qualification的sys.path含R，实际安装入口缺少它；补入同一R后，fresh同入口测试、Root实际retry install及qualify03均通过。不能把本次0安装失败与469混作一次故障。 |

实际安装的feeder amendment为`R/ROOT-P50R1-SENTINEL-PARTIAL-FEEDER-EPOCH-AMENDMENT01.json`，
3894 B／SHA `bac1f5603c6de2061da14d816f98d6d48d4c7b40987fde8039f9dd2864c64aa8`。
A里的旧running状态不证明其后feeder仍健康。

## 窗口17：219日后停止，869结果未知且不重放

窗口17起点raw53342352，最后已结算raw53347608／cycles5765，差5256 raw，即219日。
FULL846于2026-10-17T19:51:23.807045Z报SDK error、保留原869结果且没有自动重试；
Root实际toolsession92741随后exit1，窗口需要修复。不能追认其为稳定完成。

AUTO869原计划是war100663323／army167772577／province2619驻留至raw53347776、speed5；
19:51:23.801065Z返回`is_error=true`、`structured_content=null`，错误为
`native tactical sentinel player-decision boundary did not stabilize on one fresh paused frame`。
这只能证明后验稳定条件失败，原动作可能已经产生物理推进，不能重发869。

紧接的control870于19:51:24.457431Z拒绝恢复：
`sentinel partial recovery denied: new generation source/owner closure changed: new_slot`。
这是runtime partial helper仍按旧epoch核new_slot，而该slot已由明确追加的source epoch替换。
它与前述469的feeder消费者是两处独立闭包检查；修了feeder，不等于runtime helper也已消费新epoch。
870没有重放869，也没有把原失败周期记为完成。

## 872两次独立只读恢复，再继续真实普通轮次

Root实际control872通过严格runtime source amendment恢复；请求名虽借用
`recover_known_owner_1024` transport，实际恢复kind是`sentinel_player_decision_boundary_partial`，
不是native reset。其source epoch SHA为
`84ffc7c6321bcba333ed173cc458855e80c84973925fb1224147313ba2da882c`。

SEM873于19:56:17.585575Z、SEM874于19:56:17.628799Z分别完成，均读到Native9572／public1039、
raw53347776、alive40695、原后继episode`native-40695-9cf747ffe1ee`、paused且map-ready、connection12。
两次独立decision identity相同：原生interaction实例-1761607550／sender59833／auto_accept false。
872审计于19:56:17.630257Z封定：

- 原869重放0、新游戏动作提交0，额外pause／resume／arm／cancel／UI提交均0；只读调用2。
- 原失败pending cycle／date／business信用均0，completed cycles保持5765，未声称原life advance完成。
- 与原before raw53347608相比已观察到168 raw，即物理7日；这来自原结果未知的869执行期间，
  不是872推进的7日，也不加入窗口17的219日稳定信用。

随后FULL875按max1真实完成，cycles5766、raw53347776不变；该轮AUTO876实际为
`query-war-results-window-v1`，不据此声称已处理上述interaction。
FULL878按max10真实完成，cycles5776、raw53348112、叙事8491日；最后AUTO899的驻留推进及MET900
于19:58:01.575775Z读回同日期。这比875新增14日，是恢复后真实推进，和原869已发生但无信用的7日分列。

SEM901于19:59:29.034626Z、MET902于19:59:29.324518Z继续独立读到Native9592／public1059、
raw53348112、alive40695、paused且map-ready、同episode。这是该截止点的观察checkpoint，非新SAVE。

## 首30年与下一批准入

该截止点Root报告NEXT903为只读occupation查询，尚未执行。本页不预填其结果。
Root已安装`R/root_p50r1_first30_sized_loop_feeder.py`，31757 B／SHA
`e4a6d7bc91153bb9dd8f0c4d80edeb0354ce52b39d7739ee03d215d18c1ce83a`；
文件字节已离线核对，Root当时明确尚未启动，文件存在不等于运行中。

这个COW只在未来新FULL的保守近目标区间改max_turns为1，保持原target gate、玩法、速度和目标，
已存在FULL仍按原实际max跟随，不能替换或重发。候选包
`N/p50r1-first30-sized-feeder01/DELIVERY.json`保留步长依据、边界与既有FULL保护的离线验证。
它须和实际runtime partial epoch消费者一起由新进程资格验证后采用；本页没有启动feeder或发布queue。

首30年目标仍为raw53407320；在raw53348112处尚余2467日，首次30年未达，连续稳定30年也未达。
用户指定该节点的MCP手动保存及独立命名永久保全尚未完成（节点SAVE计数0），普通继承SAVE374不代替它。
现有MCP只接受fresh revision，固定物化`xar_checkpoint.ck3`，没有命名参数；具体保全流程沿用
[现有保存合同](g2-remaining-natural-outcomes-2026-10-18.md#首次30年手动mcp保存与永久保留)。
到首cross turn先停止继续推进及后续自动SAVE，再显式MCP保存一次并独立读回；
按既有现场规则在Game实际退出后，将这份真实物化文件独立命名、核SHA并登记永久保护，之后完成全片。
原片分段与实际错误／修复照实保留。完整视频尚未渲染，下一轮1066重开尚未作为本页完成事实。

## 已封小件来源

本页离线投影`N/p50r1-continuation-topic01/CLOSED-CONTINUATION-FACTS.json`，46660 B，
SHA `b605bc422a9d81795c39857a012400c6b45c49fd47efc6143ad445b6cab50cec`，
保存下列完整path／bytes／SHA及UTC。它不是可执行准入，原件均留外置。

| 小件 | bytes／SHA-256 |
| --- | --- |
| A：三次重入事实封包 | 10572／`809c751c0bc2a2d8756c6e76afb9fe69645f293174572dcb1e9ebfb5dc504b88` |
| `R/p50r1-responses/0869-1-result.json` | 718／`91d923c0855533df4e1233b20d67fff795d5f5be05465dfa469364a4ad4b85b2` |
| `R/p50r1-responses/0870-1-result.json` | 550／`75bab8d0685b91b2233790d1a329406be42687f91626f190d235ff35be6b27b5` |
| `R/p50r1-queue/SENTINEL-PLAYER-DECISION-PARTIAL-RECOVERY-0872.json` | 3389／`5e8405befb11d4c734245996f9e09fd5e7be339c2af6385d69a5f616e959a1fd` |
| `R/p50r1-responses/0872-1-result.json` | 1094／`bbf7014d31038aa23e600af143e3f4d429707c01fbd832871abe589428b5be45` |
| `R/p50r1-responses/0878-1-result.json` | 1220／`0b60a6bc96d453ec29a9409ed51a9cfad07e09e47a3e99b49b5b70d9a9461822` |
| `R/p50r1-responses/0901-1-result.json` | 27258／`996a290a8e2dc3e174594302119944ccde3ae4b8276da6b06252f5023403f710` |
| `R/p50r1-responses/0902-1-result.json` | 1606／`f97519baeaf8fde046766f6439e83844ff8e6ebb28fa459e86ff9cc00765b181` |

## 20:08Z补注：903未执行查询，906清理后窗口18真实推进

`machine_id: xenoamess-full-tower-eb9d2c1186`。以上19:59截止事实保留；较晚依据为
`D=N/p50r1-runtime-feeder-closure01/ROOT-POST-903-CURRENT-FEEDER-HANDOFF01.json`，
UTC2026-10-17T20:08:03.900534Z，SHA
`07e64cdb3c13c07d311d82d215a0b8f3a670f7469fbe386898b1b847afa66d5b`。
D是`HISTORICAL_REENTRY_POINTER_NOT_RUNTIME_ADMISSION`，不授当前liveness。

903于20:02:16.289992Z被本地旧preflight拒绝，实际occupation query分发0、未完成、未重放。
关键原因是FULL的visual MRO：`full_loop`经继承的`SavedCampaignVisualQueue.require_camera_pixel_admission`
早在首个真实FULL5便import并缓存整个`root_saved_campaign_preflight`。
**没有某command请求，不代表其模块未被其他路径缓存。** 先前离线验证只compile/import queue，
再在隔离`sys.modules`中替换候选，没有复现真实FULL的visual admission导入历史，因而漏检。
候选随后归档，磁盘复原为已缓存旧版；owner readonly registry没有取得实机启用资格。

906于20:05:49.425886Z实际返回`query903_zero_mcp_local_rejection_cleared`：
新MCP／Native调用0、903未履行且未重放、business信用0；cycles5776、Native9592／public1059、
raw53348112及actor／episode不变。该修复消费已封SEM904／MET905作来源；不能称906重新查询了occupation。

随后Root实际采用已安装的e4a6 sized base，经`run_runtime_amended_feeder.py`与
`runtime_partial_feeder_gate.py`的新进程组合继续。原feeder追加epoch仍为bac1f560…，
实际runtime partial epoch是 **`84ffc7c6321bcba333ed173cc458855e80c84973925fb1224147313ba2da882c`**；
wrapper／gate及两层epoch的完整path、size、SHA均由D逐项绑定，没有改写旧epoch或原c754。
Root报告toolsession65514开始跟随；65514是工具会话号，worker未观察feeder OS PID。

`R/p50r1-responses/0907-1-result.json`实际为`bounded_loop_finished`、max30／30轮、cycles5806、
Native9672／public1139、raw53349552、同后继40695／episode，next968。
相对窗口18起点raw53348112又真实推进60日，叙事8551日，首30年仍未到。
D保存的following968及window18 running只证明其各自当时metadata，不能据此宣称当前运行健康，
也不把之后失败／恢复的FULL计作成功。节点永久手动SAVE仍未产生、成片未渲染、G2仍6/8。

另，下一局的SDK02／host02六consumer（frontend、ordinary war、succession、M6、source knowledge、performance）
已获Root源码与既有合同审阅，签字UTC2026-10-17T20:08:10.666241Z；证据为
`N/p51-fresh1066-v20261018-prepare01/host-compatibility02/ROOT-NATIVE25-CONSUMER-CLOSURE-REVIEWED01.json`，
SHA `dacb044c4a7fe325d55b083b513fa80b81d715a510bb0433d5ec3120887b5d9b`。
其资格仍为`PENDING_ACTUAL_NEW_GAME`，新Game／SDK／Native构建／录制／profile／SAVE调用0，
未安装到本场、没有新局runtime或M6终局信用；57项来源pin留在原小封包，不复制为新实机成绩。
