# R07-v2：同一静止 S0 的自然登船与驻地对照（待实采）

本修订于 2026-10-16 在当前战争四期研究授权内提出。它替换未来 R07 的不可达“≤7日完成自然登船”设计假设，**不改写 R07-v1 未闭、R0173 正例或 R0174 的21日补充对照历史**。v2 实采尚未开始；设计通过不算业务关闭。

原问题仍是：同一正常存档、同一实际军队与条件下，正常 Move 自然登船会触发哪些真实扣款？驻地分支同期发生什么？回答基于每笔源资格扣款；两臂最终余额差不能回答此问题。

## 为什么改为30日，最多2日余量

R0175 正常存档 S0 日期53145552（1066.11.5），Army18静止于2624；提交新正常 Move 后实际 scoped native 包给出第一边权重3000000/Q100000、movement rate100000/Q100000、remaining duration3000000/Q100000，实际30日。其原始引用为 query2：`army-query-ca47f2751ba24f2782f2ecf81d00379f.json`（4,738,729B，源dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb）。这是本次.4实机字段，不把1.19偏移或截图估算冒充它。

同机实际安装 `game/common/defines/00_defines.txt` SHA256 `8e430d77eb6e8767030f34b1c53d5dae84277fb354bd73cc42f93dc500be8982` 的1189行 `EMBARK_COST = 30` 对应陆海路径成本。613行 `DISEMBARK_PENALTY_DAYS` 和1677行人物旅行参数不是该登船路径合同。法定 preview 本身不返回ETA；短海岸几何不能推翻真实30日。

v2 两臂各最多32个真实自然日：实际30日入水，加最多2日验证余量。若所选军的实际新边不是30日，记录其精确来源并停止执行本时间合同，不能靠“又延几天”补齐。若第32日仍未真实入水，本次不关闭；保全实际后态和原因。

## 共同 S0 与本土军队筛选

优先沿用 R0175 已有正常保存，不让Army18返岸重走：

- 正常007保存 SHA256 `0abc39664ad69759bb882f1ec275dd43f848d06b3fc2dbba5f83b2c8961a8c0e`，69,732,402B，date53145552；007回执 SHA256 `d82314012a6ff12d3cbc12ffa0f063bcfad45ef75724d245987370e3c06772ac`。
- 该S0普通snapshot的Army93/94/95均在2619、owner31254、可控且空route。snapshot士兵数为null；“事件250军”只是待核提示，不能填成native人数或套用Army18的1196/3金币。
- 两臂都必须**新PID、正常加载同一个S0**；R0175保存后继续的现成场次不能替代fresh-load treatment。若实际加载后这些军队不在或不同，直接保全差异，不改存档或临时造军。

Root先在可关闭的筛选场或第一臂加载后，snapshot核owner/controllable/陆地静止/非战斗非撤退；以现有 `ck3_query_army_strengths(army_ids=[93,94,95], profile='ordinary_core_v1', ordered_refill_entry_mode='observed_prepared', ordered_besieging_entry_mode='observed_prepared', expected_revision=R)` 取明确 `army_history_evidence.raw_result_reference`，保全完整Driver JSON，不能只用public摘要。

筛选必须读 `native_carmy_id_observable/native_carmy_id`、原生resolution、regiment数量与当前/上限、全部 `regiment_replenishment_records_v1`。用现有 `normalize_regiment_replenishment_records_v1` 检查available完整stored DATA及chunk association；比较两臂同序的ArRg ID、persistent ID、record/chunk索引、current/max、state和事件/角色来源，不比较跨进程裸指针。`regiment_replenishment`只取首DATA，`owned_regiments_v1`是玩家全部直接持有库存，二者都不能冒充选定Army完整构成。若事件军没有该闭包，保留这个适用性缺口并筛其他候选，不能放宽归因器。

对唯一入选U，用原生 `preview-move-army-U-to-P` 查看实际法定陆海路线。目标P取当场native可达海区；已证海1036可作首个preview候选，但不承诺从2619可达或首边就是海。先确保实际相邻首海，避免把内陆路程算入30日。若没有满足条件的候选，保留未入选原因，不能用Army18返岸假装最短方案。

事件军与普通军差异必须公开：结论仅覆盖实测军队种类、DATA/人数、actor及该路径，不外推“所有军队每百人固定费用”。现有付款资格要求transition前后Army/requestedUnit一致、native入水分支、真实natural父链；是否适用于事件军最终由实际回包授予，源码支持不等于已发生。

## 可逐步执行的两臂准备

1. 固定同一actual source commit、生产DLL SHA和原版EXE SHA。两个fresh profile/pipe/assets复用现有capture_bootstrap prepare/check与正常checkpoint输入；PID/createTime/episode/自己的window仅正常启动后从真实回包填入，不作为启动前凭空门禁。先核新Steam离线/现场租约/容量已有流程。
2. 两臂分别独立读取正常身份、S0日期、actor、Army U、owner、全DATA、supply、空route、无move_target、非embarked、战争与初始钱包；两份结果按字段比较，不能把一臂baseline复制给另一臂。prepared checkpoint必须指向同一上述S0 SHA/大小。新DLL不同于创建S0时可用，但两新臂必须相同，normal load后重新验来源。
3. control全程不发Move，也无需Halt（本来已静止）；treatment只提交**一次新的正常 `ck3_move_army`**。这是新场新动作，不是R0175旧Move的未知重放。ACK后独立snapshot/ordinary确认真实route、movement rate和首边duration；异步旧同帧只读恢复，不重发Move。锁定实际30日合同并记录actual sea target；不宣称preview已有ETA。
4. 两臂均natural_phase ON，另外8族OFF；现有payment enable contract `same_owned_process_no_load_v1`，随后独立query/readback与actual admission。每臂每段有自己的process/create/generation/episode/window/payment epoch/natural epoch。不同臂或不同段绝不共用sequence。
5. 复用已验逐日runner：fresh paused同身份→Arm +24一次→fresh→Resume一次→真实自动暂停→独立sentinel ticks1/overshoot0→fresh cash(query)→scoped普通Army U与独立final route。每一天双方都是实际自然日，同等N日；未知事件按用户策略采集、原生选择第一项（通知左侧拒绝）、保留ACK和后验；记录分歧，不能假装两分支事件完全相同。
6. cash每天保留完整原始响应；ordinary全DATA只在S0、Move真实后态、转换前后和终态做必要检查。public普通摘要与full原始引用分别保留，不用glob/latest找“看起来最新”的JSON。文件须等成功发布的同一reference，并核其bytes/SHA/query/date/gen/episode/actual scope；partial不是重发动作的理由。
7. 建议actual remaining<=5日才开一次360s/≤1.5GiB raw，Root显式start/end绑定实际场次/日期；此前纯证据推进不能倒造镜头。新重型写入必须另经当前容量实际准入。此设计小包占原R07 4MiB slot内、总≤1MiB；不是未来两个32日数据/视频自动获足额容量。

## 30日 ring 的显式分段

R0174实际约2个natural records/day；30日约60已逼近64槽。读取或复制不会drain。继续使用natural56/payment384先止线；natural48或payment320即要求Root在**暂停同日**评审换段，通常不晚于第24日。若计数增长较快提前换段，不能死等第24日或假定每天最多2条。

换段仅在无pending action、无active capture、完整raw已归档时：先完整只读cash+natural状态保留本段末点和父链；Root显式payment disable，独立确认OFF/clear_completed；显式natural disable并query确认OFF/clear；natural enable→独立all-family真读回（其余8OFF）；payment enable→独立新admission/query。在两次完整端点之间不推进日期、不发Move/Halt。`war_payment_window_12004.cpp:53–82`已有这些显式控制；natural禁用会使原付款窗失效，所以顺序不能当作同一旧窗继续。

各段都保留首/末baseline、clear实际回执、双侧相同日期/暂停后态，**新段的previous_latest从实际新baseline设定**。不跨段拼序号、TLS父链或natural returns；每笔qualified debit的transition/gateway/SUB/自然返回须完整落在一个段内。若自然动作正在跨边界、任一clear pending/末包不完整、日期变化、身份变化，先停卡，不能为了让窗新鲜而丢弃未知证据。分段只避免后续覆盖，不追认旧partial包。

## v2 关闭标准与消费边界

以下均实际满足才计R07-v2核心关闭：

- 两个fresh正常加载同一静止S0、同实际source/native、同actor/军队完整DATA及真实独立baseline；各自身份与每个付款段独立绑定。
- 两臂同等N（≤32）个exact自然日；control始终驻地、空route且未入水；treatment一次正常Move、真实30日边和实际入水前后独立后态。若control自行移动/战斗，保存冲突，此pair不合格。
- treatment至少一笔**正额**付款经既有 `normalize_journal` 重新闭合natural-return→transition→gateway→personal/Land SUB的全原始链；再以transition.requested_unit_id绑定选定U，保留account/amount/returned wallet/actor/window/序号。金额为当场实测，可能不同于R0173的3金币。
- control同期完整每段/每日中没有该U的qualified boarding callback，同时未发生入水；这仅是本驻地分支未观测登船扣款，不是零总支出或免费登船。其他军队的付款必须另列，不能归给U。
- 月度普通wallet ADD/其他收支与每笔登船SUB独立列原始事件；余额净变化仅作描述，不用于归因、配平或扣除“估计维护费”。本设计不再要求避开月结。generic context的maintenance_attribution仍unclosed，R08军队维护实际结算另卡关闭；R07-v2可以在R08仍未闭时回答直接登船扣款。
- 全部段无覆盖/丢样/失窗、完整引用可复读，事件处置与可用真实镜头来源明确。v1≤7、R17421日partial及R01commander ABC仍各自原状态。

新 `r07_v2_contract.py` 只负责可移植设计预检和**一个明确原始response的付款段摘要**；复用生产normalizer，输出永远 `full_v2_qualified=false`，不会把几个JSON通过升格为全pair验收。它输出selectedArmy与otherArmy的source-qualified扣款、独立generic context、storage_u64日期与low32，以及换段预警；不搭新runner、不连接SDK。最终完整pair仍须按上表用已入库common-S0准备/身份/raw-ref/exactday检查器逐项审，旧checker硬编码21日/2624分支不能直接套v2或改旧回执来PASS。

```text
py promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/r07_v2_contract.py --design <explicit-v2-design.json> --for-observation
py promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/r07_v2_contract.py --repo-root <repo> --response <one-cash-response.json> --snapshot <its-before-snapshot.json> --binding <actual-own-segment.json>
```

`binding`显式提供producer machine_id、PID/create_filetime/generation、episode、actor_id、unit_id、date_raw、segment_id、window_id、payment_epoch及本段previous_latest_sequence；没有本机/盘符默认值。复制到其他机器离线验证不要求其拥有producer机器身份。

下一节点：Root可先审设计与筛军argv，预计5–10分钟完成两候选的只读筛选；每个32日arm按既有exactday历史速度约6–12分钟纯推进，事件/正常启动/换段/转换镜头另留5–10分钟。两arm约25–45分钟是工程估计，尚非承诺或已完成事实。先止线是source筛选失败、实际边非30日、32日未入水、任一lost window/丢样/超容量/事件缺少原生通道。固定quota复核截止仍 `2026-10-16T07:45:01.597000+00:00`，不续期。
