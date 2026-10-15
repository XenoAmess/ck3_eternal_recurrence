# 第4期 C：当前中转选择与下一步决策适配器

[strategy_c_next_decision.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/strategy_c_next_decision.py)可从任意工作目录按文件路径导入，复用[既有 whole-via guard](episode04-strategy-c-12004.md)，供智能体生成下一步提案，也供视频整理“为什么继续、为什么暂缓”的同帧来源。它没有注册新 MCP/API，没有执行查询、Move、resume 或其他游戏命令。

本轮源码基线 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`，纯离线执行机器 `machine_id=desktop-3fevhd2-1c74096080`。实际观察时间、测试解释器和精确源SHA见外置 `next-a01/DELIVERY.actual.json`。该机器标签只绑定本次离线工作，不是读者的安装/部署/实机资格。Root独占R0175，本工作没有SDK、游戏、桌面、EXE读取/构建执行或新实机信用。

## 真实输入与完整 DATA

`read_inputs(plan, runtime, endpoint_record, evidence)`使用已有精确小文件 pins，经现有 `r10_compare.endpoint`与`strategy_c.read_observation`连接 snapshot、完整 Driver Army结果和当前完整CArmy身份，再保留原 `current_movement_progress`、全部实际regiment ID、全部DATA及来源pins。它不读取大存档、原片或历史路径，不以MCP摘要替代Driver原件。

适配器的完整性门同时检查原cohort仍在当前整军，以及当前整军的**全部**regiment都有对应DATA容器。每个容器必须为原生全records来源、available/ready，实际存储count与records长度一致，每条record available，ordinal连续、persistent/chunk身份和physical current/max可读。容器外层available而其中一个record unavailable仍为`hold_unknown`。缺physical current时不能用effective/prepared补齐。

明确native count0保留为空观察；不会把没读到的DATA当count0。重复persistent/chunk alias按原ordinal保留，不为“算净补兵”去重、删行或重复累计。新增团和原cohort的完整覆盖都保留；本适配器不产生physical ADD、损耗或费用归因。

## 先选草案，再执行冻结顺序

`choose_draft_via`只在草案阶段消费调用方**明确给出的有序候选ID**与其当次原生preview，不扫描或猜测省份。候选不得等于当前位置或最终目标。每个available preview必须匹配当前Army、origin、target、date、snapshot/public/native revision、connection generation及episode，路径末端确实到该候选。

选择标准明确为“给定顺序中首个fresh available native preview”。被拒、deferred、缺失和过期候选的原因保留在`candidate_diagnostics`；一个可用候选不证明它优于缺读数的其他候选。这只证明**当前Army→候选的首段路线**可预览；Army尚未到via，不能伪造via→最终目标的另一份native preview、总耗时或补给优势。输出`onward_leg_qualified=false`，不自动写入或冻结plan。

正式`status=frozen`后拒绝通过候选选择改换中转政策。`next_decision`仅使用既有`waypoint_province_ids`顺序和共同goal；实际到via且通过既有`c.observe`后，再取该时刻的新preview前往下一冻结目标。保持原三臂同T0、90日绝对截止及[比较合同](episode04-comparison-contract-12004.md)。

## 锁定首段与 hold/unknown

锁定判据仍是同帧原生`normalized_edge_progress.raw > loaded_movement_lock_cutoff.raw`，两者均为Q100000 signed64；不硬编码50000。等号只记为`not_above_cutoff`，不凭它宣称某个命令一定合法。缺source、progress、cutoff或scale时`locked=null`，明确`hold_unknown`。

已锁定表示**当前front要保留**，不能推导“全部改道都禁止”。`route_change_advice`在没有fresh preview时输出`hold_locked_front`并建议现有preview step；若实际preview保留原front且抵达desired target，可以记为原生preview可用的suffix，但仍不提交Move。绕开已知front的preview保留unknown并要求读回，不能当作即时取消首段成功。最终validator、独立实际route后态和真实到站区间仍按[锁定改道专题](episode04-locked-halt-reroute-12004.md)各自验证。

| 当前状态 | 适配器下一步 | 业务边界 |
| --- | --- | --- |
| ready，缺fresh preview | 现有`ck3_execute_step`的`preview-move-army-U-to-P`只读提案 | P是冻结的下一目标 |
| ready，preview同帧合格 | 现有`ck3_move_army`提案及新的pending state | 必须先持久保存pending，再最多提交一次 |
| pending，结果未知 | `hold_unknown`，现有scoped Army查询提案 | 不重发Move |
| 收到新snapshot/day | `needs_existing_observe` | 先交既有`c.observe`保全独立后态和一日时钟 |
| marching，实际路径仍为冻结段的后缀 | 既有date-only一日sentinel Arm提案 | 只提Arm；不替执行者resume或确认时钟完成 |
| 路径不符、锁定资料缺失或preview不合格 | hold/advisory，保留原因及source pins | 不私自换路线或填false/0 |
| arrived、真实D90截尾或显式stop | terminal | 不重新开局或重置预算 |

这里的hold是当前无法安全发出该次路线变更提案的决策状态，不是新增“等补给/补员达标”策略。临时hold不自行消耗游戏日；普通事件及战争局面继续由上游完整规划器与既定事件政策处理。

## 视频使用与验证

视频可以逐项取`source_frame/source_pins`、`frozen_next_target`、实际锁定读数、候选诊断、`reason`和`actual_arrival_intervals`，展示当时可知的决策输入与提案。提案不是动作已执行、preview不是已到站；画面与实际业务后果仍须自己的证据。适配器原样保留既有到站区间且`exact_arrival_tick=null`，旧`(75,77]`不能转写为精确第77日。

共同日期表继续由共享比较器生成：各臂各自抵达日的数值不拼作同日；费用、physical ADD和winner不由本模块补造。视频动态素材、TTS、成片及签核均不由这些离线检查增加完成信用。

新增验证只执行[新适配器compound](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/test_strategy_c_next_decision.py)：真实共享endpoint reader连接、逐record缺口、缺新增团DATA、ordinal、physical/effective反例、alias保留、fresh/stale候选、冻结拒换、pending未知、锁定front与合法suffix、缺值/等号、绝对一日Arm、旧区间保留及无cwd/sys.path依赖导入。数据全部显式synthetic；复用已有Fixture工厂但不执行旧comparison或原13个C测试。

```text
<verified-python-with-jsonschema> -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/test_strategy_c_next_decision.py -v
```

存储沿用统一策略1.0.0及协调者`continuation-a05/CAPACITY-ACCEPTED.actual-a01.json`。原C外置lane与本增量合计仍≤8MiB，已计入原512MiB池；准入/配额复核2026-10-16T07:45:01.597Z，不延长、不新预留，不清理其他工作包。

## coastal e6ee S0：停靠选择与到站再查询

2026-10-15离线增量基线`d9322bcfb3e17a3fe78607cea777bbfaf7be0a11`；执行机器`machine_id=desktop-3fevhd2-1c74096080`。本节只绑定下面两份小型实际记录。采集时间与离线读回时间分列于外置`high-parallel-C-coastal-choice-a04/S0-INTAKE.actual.json`，记录缺失的后续输入，不授予新实机信用。

| 实际来源 | 字节 / SHA-256 | 可证明范围 |
| --- | --- | --- |
| `live12004-logistics-source-a01/normalprepare93-stages/newstationary-commonS0.actual.json`，原记录`2026-10-15T20:25:31.384013Z` | 7236 / `90a78e0d242fd4bb9b7cee366c8576659d049851c43f2cd0474781c832d35590` | 正常checkpoint元数据：e6ee95c3184c00989af660c5d765a27622fd5b93f9e8930fdc5a5ed56e157d67、71631396字节、date53146848；Root完整Army摘要93→CArmy85、250/250、stock100、4regiment/4DATA、whole_DATA_ready=true |
| `live12004-logistics-source-a01/desktop-3fevhd2-1c74096080--vanilla--R0177/responses/035-coastal-commonS0-endpoint.json`，原envelope`2026-10-15T20:26:14.497489Z` | 139796 / `16c056bc00074e010f286f4207a8daaa1d292e0940683e11d1d377a32aa18794` | native:33/public revision34/native revision33，actor31254、Army93在Province2624、regular/controllable、无战斗撤退、complete_empty；原snapshot soldiers=null，不能用此字段伪称已读physical250 |

正常存档本体和7865022字节完整Driver原件本轮没有打开、重复hash或复制。250/250及DATA覆盖仅标为小型Root摘要的事实；正式开臂仍须现有paired reader读取当臂新鲜完整Driver。`move_target_observable=false/target=null`保留空route的原生语义。当前war objective2635不是默认共同goal。

**当前不能选定最短可区分C的实际停靠点。** 这两份来源没有Army93从2624至共同goal的direct preview，也没有该时刻的via preview与目标供给输入。不能借旧Army18的sea18、1036、30日或3金，也不能把较早Army93在2619的currentrate+20接到后置2624的S0。stock100本身不证明何处可以恢复补给。缺口交给Root的a08 fresh-load查询：先明确共同goal，读取同S0当前Army93全DATA/typed commander，再用现有`preview-move-army-93-to-P`逐个查询调用方明确候选。没有候选结果时只列缺失调用，不虚构候选ID、route、ETA或费用。

`compare_via_first_leg(plan, observation, via_province_id, direct_preview, via_preview)`是新增的只读consumer入口，直接消费已有完整观察和Driver原生preview body。它复用同帧身份及完整DATA门，不注册新接口、不改变冻结plan。输出可供智能体解释候选，也可直接用于视频的当前可知决策卡：

| 同帧实际preview关系 | 可说什么 | 仍不能说什么 |
| --- | --- | --- |
| via首段恰为direct到via的完整前缀 | `intermediate_stop_on_direct_prefix`：沿直达路径增加一次明确停靠 | 不能把停靠本身称为几何绕路，或声称补给改善 |
| 当前via首段与direct不符 | `current_first_leg_diverges`：首段实际分岔 | 不知道到站后via→goal的路径、总耗时或补给收益 |
| via preview在停靠前先经过goal | `goal_passed_before_via`：冻结前暴露实验设计冲突 | 不自动换目标或把经过goal记为正常到站 |
| 任何preview缺失、过期或Army/CArmy/owner不符 | 列明缺失只读调用或`hold_unknown`及原因 | 不拼接旧Army18或其他帧的目标/供给片段 |

preview hop数不是距离或行军日，不能按最少hop宣称“最短”。实际分段Move继续由既有`phased_relay.py`逐次提交；每次保留pending并最多执行一次，独立path-after和bounded daily实际到站区间合格后才进入下一段。前段已锁定时保持既有front/suffix规则，不借本函数直接改道。

目标字段保留已有`province_supply.target`及`captured_target_land_supply_inputs_v1`的实际内容与false/null含义。目标usage仍是当前捕获输入，不加上本军250人为制造抵达后usage；当前province component、resupply eligibility也不等于未来月度rate或stock。输出`future_usage_after_arrival/future_monthly_supply_rate/future_stock=null`、`positive_supply_recovery_guaranteed=false`。到站后必须重新读取暂停的当前Army/CArmy、全部physical/DATA、typed commander、实际stock/cap/rate，再读取实际via→冻结下一目标的新preview及当前target contributors/resupply输入；此前`onward_route/onward_target_inputs=null`。前路保持conditional而不无限挂空：输出给出具体缺失查询和到站重查清单，由Root在下一已授权runtime阶段执行。

本增量只新增`test_strategy_c_route_choice.py`的5个synthetic案例（缺实际pair、直达前缀停靠、分岔且false resupply保留、旧Army/帧/目标身份拼接、goal先于via）；不执行既有10个next-decision或13个C guard测试。旧`(75,77]`、三臂共同日期和D90边界保持原合同。本lane封存≤256KiB，计入既有active32MiB/metadata17池，沿用`continuation-r13-a06/CAPACITY-ACCEPTED.actual-a01.json`与2026-10-16T07:45:01.597Z截止，不续期。
