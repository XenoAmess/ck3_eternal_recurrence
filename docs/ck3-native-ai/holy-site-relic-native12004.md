# 圣物只读缺口与原版供奉路径（1.20.0.4）

即使采用成功，也只证明 faith 与 HolySite 的关联发生变化；当前第一期尚未取得采用成功后态。规划器仍须单独核对 Active、认可圣物、有效等级和受益范围。现有 `ck3_query_player_holy_site_v1` 的 artifact 数组仅为完整引用；`artifact_objects_resolved=false` 不能解释成没有圣物，也不能解释成已经认可或已经取得收益。本专题把下一条供奉试拍的最窄施工入口固定下来；尚未实现新口、调用 native getter、执行供奉/移除或取得本专题 live 资格。

machine_id: `4-8e1c2f1861`。本轮重新执行 `tools/ck3_live_run_id.py machine`；静态读取实际时间为2026-10-17 09:13:22 UTC开始，后续来源的精确观察时间见每件原包，逐件时间见[原生来源包](evidence/holy-site-relic-native12004/source-pins.json)与[21份原版脚本来源](evidence/holy-site-relic-native12004/script-source-manifest.json)。目标 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，Steam build 25734779。复用本机此前冻结的 immutable `.text/.rdata` 缓存，未复制 EXE/DLL、未触碰游戏、屏幕、Steam、lease 或受管 checkout。09:13:22 UTC `shutil.disk_usage` 观察输出卷空闲134,059,683,840B；这只是小型研究输出的容量记录，不授录制写入资格。

## 下一步给既有智能体补什么

建议新建独立 `ck3_query_player_holy_site_relic_context_v1(expected_revision, holy_site_id)`，继续走现有 religion owner mailbox、Service/Driver/MCP 与 paused snapshot 绑定。单独的新 C++ reader/serializer/transport 可避免与正在验收的采用 DTO 互相覆盖。不要先改旧口的 `*_observed=false` 或把本文地址填入通用任意调用接口。

最小第一层只读结果是同一站点的原生 `is_active` 缓存、`total_active_artifact_rarity` 缓存、完整 artifact 对象身份/稀有度/实际 HolySite owner 与原生 slot 引用；第二层调用原版 `IsHolyRelicFor`，分别绑定玩家 faith 和县主持有者 faith，并读取原版窗口的供奉候选及当前选择。候选为空、读取 unavailable 和最终拒绝要分开。`actual_beneficiaries`、实际属性增益、动作费用与后果继续 `observed=false/value=null`，直到各自实际观察闭合。

| 可复用来源 | exact4 原生链 | 可报告的语义与限制 |
|---|---|---|
| Active | `HolySite.IsActive` wrapper `265AA30` →完整 leaf `22C34B0`（5B） | 读取 `uint8(site+18)`；是 GUI 同一缓存，不能声称此只读操作重新计算了世界状态。 |
| 有效圣物总等级 | registrar `520730`（name读取 `5207A3`）→ `24FC1F0` →完整 leaf `EDDB90`（4B） | 读取 `int32(site+1C)`；不得由库存数量、物品 rarity 总和或 faith 列表推造。 |
| Artifact 完整对象 | rarity producer `265A3F0..265A4C0` | storage `5D1DE68`，low24 index，rows+20、capacity+2C、16B槽；核对象+10全ID、+14 magic=`0x41727469`。原生 default `5D1DE30`不能当请求对象。 |
| 稀有度 | 同一 producer，`265A495` | 对有效 artifact 加 `int32(artifact+B0)`。这是对象本身值；“当前站点有效贡献”还须走有效判定。 |
| 按 faith 认可 | registrar `4F9A70` → `25363E0` → `2530EF0..25311CF` | ABI为 `bool(artifact*, uint32 faith_full_id, tooltip_or_null)`；callback先从实际 Faith对象+8取完整ID。只读候选第三参为null，不伪造tooltip对象。未实际调用，不授 ABI live 信用。 |
| 对此站点有效的圣物 | registrar `4F98E0` → `2536330` → `2531320..2531468` | artifact + site；先按县主faith核 site 关联，再调用认可。不能与下面仅认可过滤器混用。 |
| 按县主faith认可 | `2531200..2531320` | artifact + site + tooltip；解析相同县主faith后直接调用认可，没有站点成员测试。因此“可列候选”不等于“正给站点贡献”。 |
| 原版供奉候选缓存 | HolySiteWindow registrar `2D00D0` → `17D80F0` →完整 leaf `D93320`（8B） | 返回 `window+130` 的DWORD列表header。真正producer见下节；必须核 `window+C8`等于请求站点、真实窗口owner/root及前后frame。 |

以上 RVA 与完整代码字节 SHA 均在来源包。leaf无pdata记录时，以已确认的原版callback入口和RET证明完整性。`265A3F0` 与 `17D7CD0` 的一个 pdata range 都只覆盖第一段；本包按实际跳转把连续 reached chunks 补到最终RET。不能把早期孤立 range 的“完整包”字样当作完整语义，不能从某个不可解码/位于指令中间的探索打印取地址。

## Active producer 与认可的真实数据流

`265A3F0` 在 site+8C 为0时返回0；否则遍历嵌入 Inventory 的实际 slot 表 `site+68` / count `site+74`，每项24B，artifact完整引用在项+10。每个有效对象调用 `2531320`，只有true才累加其+ B0稀有度。原生 inventory 添加caller `22E5730..22E580C` 的 `22E57F1` 重算并写 site+1C，随后将 `sum>0` 写site+18；另一库存修改caller `22E4D00..22E5113` 的 `22E4F2B..22E4F38`同样重算。此外，原版 `CReligionManager` 的世界更新分成重评与落地两阶段，见下节；完整上游调度时刻仍未闭合，不能给缓存伪造“刚刚刷新”的时间。

`2531320` 的实际关系链是 site+B0 barony → Title+108 county → county+128 holder Character → Character+B4 rite → Rite+4B8 faith。每一步都按本域 fullID resolver核代际。它在 site+98 的关联faith列表做完整ID成员测试，再转 `2530EF0`。因此采用本faith、县主faith、原圣物对县主faith认可，是三条独立条件。

`2530EF0` 返回两条来源的 OR：artifact+498 的动态 sanctified-faith 全ID集合，或 artifact+490 的模板及其+380编译trigger。模板trigger以指定faith为root并绑定当前artifact scope（native scope tag31）。实际原版 `sanctify_artifact_interaction` 430–448行会 `add_sanctified_for_faith`；只扫描模板、宝物中文名或历史artifact定义会漏掉动态认可。模板/compiled trigger缺失不能由桥接自造false；直接调用原版函数并保留当前版本与对象身份。

读取缓存与调用认可只在已有 owner query 内借用指针；不保存跨 reload/generation 指针，不推进日期，不为“刷新Active”重算/写回缓存。返回应分开 `cache_observed=true`、`cache_refresh_time_known=false`；实际动作后必须再发独立query绑定新snapshot，不能把提交ACK填入after。

## 原版 GUI：候选、过滤、许可与提交

这是玩家 `CHolySiteWindow` 的路径：当前primary vtable `4592338`，handler+5D8、selected site+C8；`HolySiteCreationWindow` 同名getter在另一类，不能混接。下面只说明实际caller，不授新动作资格。

1. **生产候选。** `17D7CD0..17D7E7F`先清window+13C的数量，验证site及当前玩家，调用 `28AA890` 得玩家Inventory，按其+58数组/count+64遍历所有拥有的 artifact 全ID。每件解析并核magic后，用 `2531200(artifact,site,null)` 按**县主持有者faith**过滤，按原顺序append到window+130。不另外排序，不等同于“未装备”筛选，不替换成world registry roster。
2. **何时重建。** 原版setter `17D78D0..17D7CCE`在改变选中site后调用 `17D7810`并尾调用 `17D7CD0`；两个实际窗口刷新caller `17D4FC0` 与 `17D5150`也走这两步。完整上游调度频率仍unknown。观察器只读当帧已有缓存，窗口未选此site时返回unavailable，不擅自调用setter来制造只读结果。
3. **最终许可。** `CanEnshrineArtifact` registrar `2D12C0`→`17D85A0`→`17D53F0`，构建site/artifact/player/slot上下文调用原生 command validator `29AB4F0`。该validator先认可，再检查指定/可用slot与替换对象、`22E44A0`库存许可、脚本桥 `1D64FD0`，以及有替换物时的 `1D651F0`。`CanRemoveEnshrinedArtifact` registrar `2D15E0`→`17D8700`→`17D56F0`→`29ABB20`，先用 `22E4420`核实际库存成员，再走 `1D651F0`。因此 GetEnshrinableArtifacts 不能代替最终合法性，更不能只按脚本三条权限判断按钮。
4. **当前按钮再验。** `17D5970` / `17D5E40`读取window+108当前artifact、完整对象和artifact+7C当前圣地归属，拒绝相反语境，再调用相同command validator。供奉还绑定window+110的slot/替换上下文，不可猜“第一槽”。
5. **提交。** 原版 `OnEnshrineButtonClicked` `17D5DD0`与 `OnRemoveButtonClicked` `17D62F0`先重跑上项，再分别调用 `17D7580` / `17D76C0`。二者克隆0x30字节command（`29AC540` / `29AC640`）并经 `37F06D0`提交一次，随后清选择；这不证明command已执行业务。实际执行receiver、效果preview序列化、精确槽位选择与业务后态仍须后续窄包接通，当前不提供action-ready。

脚本桥的scope链也已保存：`1D64FD0` / `1D651F0`分别建立artifact root、holy_site scope(tag23)、actor scope(tag4)、替换artifact scope(tag31)，再求对应compiled rule。原版脚本供奉条件是actor为县主/县主最高领主/神职区域持有人任一，且actor.faith认此site；移除有同样三类地域权限但无这条同faith要求。脚本仅是完整command的一层，详见[脚本知识包](evidence/holy-site-relic-native12004/script-planning-contract.json)。

## 原版 AI 与我方计划分开

原版 `ai_enshrine_artifact_decision` 为AI专用。静态来源 `50_holy_site_decisions.txt:636–735`（SHA见manifest）先在actor artifact×本faith站点存在性搜索中确认至少一对合法；effect再从对actor.faith认可的自有artifact中按rarity取最高一件，然后优先随机选有效总等级为0的eminent站点，否则随机回退其他合法站点。AI调度定义county为24、duchy/kingdom/empire/hegemony为12、barony为0；这里记录定义值，不推断实际玩家窗口调度或自然调用频率。effect的最高物品选择与validity的存在性见证不是同一绑定，不能把它描述成全组合优化。GUI的县主faith过滤、AI的actor.faith选择和最终command各有范围。

我方planner应先确认经营目的，再比较个人装备机会成本、县级收益、eminent全信徒收益、认可范围和实际移除代价；不以“最高rarity”自动献出最有价值的个人装备。当前nadjaf输入没有被本专题实读，不能引用他线程库存ID就声称认可、Active或收益。第一期可冻结的旁白是“加入名单之后，还要问它是否生效、为谁生效”；nadjaf具体属性增益仍待后态。

## 最小实机与实现验收合同

新只读接口先增加独立C++文件和DTO，不改采用链；真实生产serializer→NativeDriver→GameplayBridgeService→MCP ClientSession测试需消费编译器实际输出，禁止Python伪造业务包。测试应区分相同low24不同generation、动态圣化命中/模板命中/均不命中、holderfaith与playerfaith不同、slot列表与artifact引用数组不一致，以及读取失败null。原版readonly调用若缺少有效同帧context，返回具体诊断。

第一次供奉试拍必须有可回载分支，分别保存before、一次动作、独立after：artifact owner/slot、site Active与sum、每个相关faith识别、actor资源及实际效果。先取原生合法性与preview；缺口未补完前继续第一期采用主链，不为此暂停有效游戏。移除不是免费undo；原版on_action可能扣虔诚并改变多方意见/借口，且供奉奖励的替换flag与注释存在待实测疑点，不能先写必得奖励。

[同源研究图](evidence/holy-site-relic-native12004/research-graph.md)只报告静态链。知识JSON的 `action_ready=false/native_legality=null` 保持；本包没有MCP部署、实机、视频素材或人工签核信用。研究小型来源于2026-10-24复核，继续保留理由是当前圣物读口施工；集成patch在owner应用核验48小时后按通用派生物策略复核，原始关键源码pin随代码合同保留并在版本变化时重核。


## 缓存重评、落地与瞬时查询（a03补充）

本节新证据由来源包中 `religion-manager-rarity-*` 两段与 `religion_manager_type_proof` 给出。RTTI直接读回 `.?AVCReligionManager@@`，primary vtable为 `4774888`。它不是相邻的 `TPdxRefDatabase<CHolySite>` vtable `4774778`，二者不可混用。

| 阶段 | 原版调用与数据 | 对只读口的含义 |
|---|---|---|
| 世界重评 | manager vtable+40 → `29D8890..29D8A38`。清manager+9C数量，遍历其+78/count+84的HolySite全ID列表，逐站调用 `265A3F0`；与site+1C不同才append `(siteID,newSum)` 到manager+90/count+9C。 | 该阶段计算新值，但尚未把每个新值写到站点GUI缓存。它不能与native getter读到的旧cache混成“同一已生效结果”。 |
| 世界落地 | manager vtable+50 → `29D8DD0..29D908B`，在 `29D8FA0` 后消费manager+90的8B pair。对真实fullID解析后的site写+1C=`newSum`、+18=`newSum>0`。 | 落地后GUI getter才读到此轮cache；本专题只读代码不可模拟写入，也不可主动调用manager phase刷新世界。 |
| 库存立即更新 | 添加/修改库存caller `22E57F1`、`22E4F2B`直接重算并写同两字段。 | 与世界phase是独立更新路径；供奉或移除是否已走完，要在动作后独立读。 |
| 按当前对象认可重评 | 原版 `2530EF0` / `2531320` 在owner callback内针对当前对象/faith求值。 | 这是当帧认可/有效性判定，不证明上次世界重评已经落地，也不证明最终角色modifier已经更新。 |

因此新接口的两个域必须分开：`cached_world_state`记录原版getter当帧读到的Active/sum；`current_relic_evaluation`记录本次逐artifact/faith原生只读判定。若两者不一致，返回 `cache_evaluation_disagreement` 与完整两套值，先继续观察；不能自动“修复”、挑较好看的结果或声称永久失效。`cached_world_state.refresh_time_known=false`、`world_effects_applied_observed=false` 保持，直至本次会话有独立来源。

目前仍未闭合统一更新调度对该manager的完整上游调用、每次触发与失效频率；不把方法的虚槽位置推断为日更/月更。候选实现可先只读取缓存并精确标明未知时效，或增加当前认可判定来展示差异；不得把任一种读口包装成永久属性、完整效果或供奉许可。对实际受益者的modifier读取仍是单独后续工作。
