# P50R1：同一干净战役续行与恢复边界

`machine_id: xenoamess-full-tower-eb9d2c1186`。本页记录2026-10-18 CST的实际续行，
初版游戏观察截止2026-10-17T19:59:29.324518Z；离线小件核对封于2026-10-17T20:03:21.707197Z，较晚状态按下列带时点补记分别记录。
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

## 20:34Z补注：1548预测缺口与SDK单独正常轮换

`machine_id: xenoamess-full-tower-eb9d2c1186`。窗口18后来停于cycles6029、
raw53357976、Native10210／public1677，距原first30 target53407320仍有2056日。
这不是30年完成，也没有节点永久SAVE或完整成片。

AUTO1545实际只读combat-inputs V2调用耗127.2107817秒，外层响应189608765 B，
其中MCP结果投影189608443 B；时间为20:14:26.438499Z至20:16:33.649269Z。
该调用和随后的MET1546仍保正常1×，不能因缓慢将其伪装成修复等待。
AUTO1548随后规划40.730946秒，返回blocked、selected_step=null、没有提交游戏动作；
queue于20:17:23.378098Z记录halt。其拒绝为尚无准入的战斗预测，
不是战斗输入读取失败：formal producer缺失，旧研究profile守卫又不识别已经核实的原版XAR未加载合同；
即使修复后者，多守军研究仍有独立的接战资格门。不能清halt后循环重查或直接授攻击。

Root于20:32:38.055164Z实际执行1550，消费已观察的SEM1549，
仅清理原1548的无动作pending：新MCP／Native调用0、原AUTO不重放、cycles6029及日期不变。
随后创建`EXIT-SDK-P50R1`正常关闭旧SDK；保留句柄实际观察queue240520、app18280均wait0／exit0，
launcher0、normal=true，见`R/ROOT-P50R1-OWNER-CLOSED.json`。Game与录制没有收到停止请求。

本次唯一Driver seal为`N/p52-sdk-only-rotation01/CLOSED-DRIVER-SEAL.json`，2200 B，
SHA `93558b41f2a94ee36900e7f2229f5265812427ee2c3121abc16431cf8bb47519`。
旧双SDK正常退出后，Root仅stream-hash一次并建立保留hardlink，未parse或复制正文；
封存Driver为54058661 B、SHA `3ceff3dd32c8af604729ad77d4bdbb4793208d726da16809e69bbcfc879e9622`。
该方式依赖已核实的后续Driver临时文件加原子replace写入，不能外推给原地覆盖的生产器。

同Game录制仍由独立owner持有。SDK退出后的五秒只读观察得到媒体增长，
`N/p50-presentation-prepare01/SDK-ONLY-ROTATION-RECORDING-FRESH01.json`为5013 B，
SHA `c2662860232767735eb72939a480b0c20a6fd3b3302109d43db5730bd6e88507`；
这不代替新像素、暂停状态或新SDK业务资格。
新的SDK启动、补丁安装与恢复后的实际推进须以其后回执另记，不能把准备完成写成已恢复运行。

另，固定1200–1430性能样本实际179.230587秒推进101日；其中FULL1边界空档75.272003秒，
占42.0%。43.5%是所有gap合计，不能混称FULL1空档比例。
自适应feeder31979 B／SHA `68363a28369267a9ef6853dea4c16e99352004ba4abab6060b90719b4ab58de9`
已于20:25:12.732269Z由Root create-only安装，但当时未import或运行，尚无新性能成绩。
旧combat cache失效也不能证明历史大结果已消失；其持久化与复制成本另作有界来源修复。

## 21:12Z补记：R2实际启动、manual25闭合与265再次停窗

`machine_id: xenoamess-full-tower-eb9d2c1186`，本次通过稳定机器ID工具重新读回。
小件核对与录制metadata观察截止`2026-10-17T21:11:54.183305Z`；
独立原生MET267的截止为`21:10:36.710343Z`。以下补记保留前述R1闭场及其失败，不把新SDK启动追认为原1548成功。

**R2已实际启动并连接原Game。** `N/p52-sdk-only-rotation01/ROOT-P50R2-ACTUAL-STARTUP-READBACK01.json`
于20:54:56.077586Z封定SEM1／CAP2／MET3与FULL4只读健康结果；初始frame为
Native10211／public2、raw53357976、alive40695、同episode、connection13、paused且map-ready。
启动owner273900，保留queue194204／FT134367432621492817及app248096／FT134367432644529657；
它们是启动时的实际进程代，不授当前存活。Game仍是51028／FT134367033244212072，
Game、Native与录制keeper没有重启。FULL4实际完成1轮但日期增量0，不能把该健康查询记为1日推进。

### 24与28的真实错误，以及独立的manual25

24于20:51:00.007882Z返回`manual H1 denied: manual result unknown/rejected; do not retry`。
其本地接收器原先期待generic `accepted`，实际25返回的是stationary timeline DTO；
错误不证明25未执行，也不能据此重发。实际25及独立SEM26／MET27绑定
Native10217／public8、raw53358000，较raw53357976增加24 raw，即**手动1日**。
completed cycles仍为6036，普通cycle与普通稳定日期信用均为0。

28于20:55:06.598952Z另报`manual25 metadata denied: resident post27 frame differs`。
原24在resident cache赋值前失败，不能假定post27已经驻留。随后正常fresh SEM29刷新该帧，
30于20:58:08.937671Z完成metadata重消费审计：`new_MCP_or_native_calls=0`、
原AUTO与manual25重放0，确认已发生的1日并清理原blocked pending，cycles仍为6036。
24、28两份失败与原attempt audit均保留；30只闭合元数据，未推进游戏或补计普通信用。

完成后的来源链由`R/ROOT-P50R2-MANUAL25-COMPLETED-SOURCE-CLOSURE01.json`
（SHA `c7ccd06aa8fb5e5d7226830a8cb176639aa3d817a05ba4e47c0d72e282db44b0`）
在21:00:39.521720Z签字。它绑定三份追加epoch、三个已完成lazy transport叶与严格runtime-partial parser，
旧owner及base epochs保持原样；不是忽略其余来源差异的通配许可。

### 普通规划器真实恢复与25日的组成

FULL31实际`bounded_loop_finished`，10轮后cycles6046、Native10223／public14、raw53358048；
相对manual25后的raw53358000新增**普通2日**。Root用fresh SEM52／MET53及上述闭合来源完成54准入，
FULL54随后实际完成26轮，cycles6072、raw53358192，即再推进6日。
P53 handoff于21:05:59.954823Z保存窗口19当时的running快照；该历史状态不覆盖后来的248失败。

最新小cumulative及MET267分别核到**cycles6144、Native10292／public83、raw53358576**，
仍为alive40695、同episode、connection13、paused且map-ready；存在2场战争。
从R1闭场raw53357976到此相差600 raw，**同场实际日历推进共25日**：
manual25独立1日、FULL31普通2日、从54准入所在的窗口19起点raw53358048至今普通22日。
手动1日始终不计入普通cycle或稳定日期信用，不能把全部25日追认为无修复的连续稳定成绩。

### FULL248／AUTO265：blocked且没有游戏动作

FULL248原计划max26，于21:07:53.439910Z以
`auto-turn was not confirmed executed; stop with no replay`结束，并保留原AUTO265响应。
265耗44.6152006秒，返回`status=blocked`、`selected_step=null`，
phase为`native_war_siege_forecast_inputs_observed`；formal forecast仍`producer_unavailable`，
多守军研究结果仍是`research_only`、`active_attack_allowed=false`。
兵数1357对555与研究模拟均不等于有资格的战斗胜率或攻击授权。

该计划已经标出formal defender退出所需的
`query-war-termination-options-100663323`，但当前只是`current_native_options_required`，
`options/material_terms/recommended_outcome/action_literal`均为空；没有选择移军、攻击、停战或投降动作。
queue留下pending6145／`auto_unsettled`，已结算cycles保持6144，原265不重放。
窗口19已是`repair_required`，feeder为`halted_review_required`，不能把FULL248计为成功批次。

Root随后取得fresh266和MET267；266为47,432,514 B，本次有界读取明确跳过正文，
仅读小MET267核同帧。距首次30年目标raw53407320仍余**2031日**，目标未到，
该节点永久手动SAVE仍为0，完整成片未渲染，G2仍6/8。

### 录制仍在进行，metadata与像素审阅分别留证

本次实际运行`N/p50r2_compact_watch.py`，只读取小metadata并冻结输出至
`N/p50r1-continuation-topic01/P50R2-POST-265-COMPACT-METADATA-2111Z-a3d94f01.json`。
21:11:54.183305Z读回session `da74988f-a20d-428e-9877-f2bc9d39b133`仍为`recording`，
最新frame UTC21:11:00.302343Z、age53.880962秒、peak output logical bytes4,708,940,444，
`capture_closed=false`且`failed=false`；新Game／MCP／进程／桌面调用与SAVE／媒体正文读取均0。
这份metadata本身不授像素审阅通过。

同一frame的`R/recordings/da74988f-a20d-428e-9877-f2bc9d39b133/p50r2-pursuit265-paused01-FROZEN-PAIR.json`
在21:11:33.490897Z固定原图身份，2861 B／SHA
`259d95c191777d1988af1eb20a114260f31c8f5fb3a189ef3cae61a565d29984`。
Root随后在本会话实际view scene并报告：1091-03-01、暂停、1357对555，右侧灰色“智能体实时决策”无影片标题；
scene为1,507,065 B／SHA `2749f505ee6e4ab5da58e785d006e8ef4439a0a374a4e8d0e7e8a99452593f2d`。
封定回执原有`SOURCE_PAIR_FROZEN_NOT_PIXELS_REVIEWED`状态保留，后续Root审阅与封定阶段分别记录；
本专题作者只核小回执，未读取图像正文。该暂停帧也不代替265动作成功或全片完成。

## R2补记的小件来源pin

P53完整小handoff为`N/p53-manual-h1-once01/ROOT-P50R2-MANUAL25-CURRENT-FEEDER-HANDOFF01.json`，
11300 B／SHA `ae56c92b7654b5b15df0aa1eff58af086cfa0f61ec46c8a2a57ca5f5270c4436`，
保留startup、24／25／28／30、31、54及所有epoch的完整path／bytes／SHA。
本次已将下列SHA与对应小原件直接重核；没有读取Driver、SAVE或媒体正文，没有改动现场。

| 来源 | SHA-256 |
| --- | --- |
| `N/p52-sdk-only-rotation01/ROOT-P50R2-ACTUAL-STARTUP-READBACK01.json` | `bb6518b5a50e1899b997cc2d5705189369046b8cded7941ed5b50be2e5d2f878` |
| `R/p50r2-queue/MANUAL25-TIMELINE-METADATA-RECONSUME-0030.json` | `2057fa27e3ae2b45cdf3272e3b0f8feb3474677498bb552138078ab6339d2045` |
| `R/p50r2-responses/0031-1-result.json` | `31e40042c1087e76939ef1b0d9415aba02a2bb2a376c8fc9842110d926c73ac9` |
| `R/ROOT-P50R2-POST-MANUAL25-RESUME01.json` | `29cda338089aa04501734bfdcddcfebcf21d275f727c7b059c7e0c143075c0c5` |
| `R/p50r2-responses/0248-1-result.json` | `512e66c65f8b905dda5a49cc14443301f4c29a68d4346400c8473ad121d5e1e0` |
| `R/p50r2-responses/0265-1-result.json` | `0c0449395e8dd16069c13ad6f692b08d1c770b36d3183dcb862a0604c1cca9e2` |
| `R/p50r2-responses/0267-1-result.json` | `e9da8bef05d88303fd39d20ce685637947e719ebf6205499c6ec64ed8be1492c` |
| `N/p50r1-continuation-topic01/P50R2-POST-265-COMPACT-METADATA-2111Z-a3d94f01.json` | `22ccd170d4bfa79425aa57dc3a374ecff670696cec7b075f648573a3d75c5816` |

以上只到本次R2已发生的停窗；后继source-only准备没有取得本页的clear、SDK关闭／启动或恢复成绩。
