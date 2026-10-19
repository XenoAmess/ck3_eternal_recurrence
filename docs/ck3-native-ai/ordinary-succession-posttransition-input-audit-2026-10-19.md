# 普通继承后的经营输入：源码审计与唯一下一接线点

`machine_id: xenoamess-full-tower-eb9d2c1186`，由 `tools/ck3_live_run_id.py machine` 实际读回（chunk `28d576`）；源码核对完成 `2026-10-19T05:35:35Z`，审阅 HEAD `59a0cb4125df5b47a890eac7589608adb8619cad`。本记录只读仓库源码和已有交接；零现场、Game/RPC、活 Driver、SAVE、COW 或媒体操作，零共享代码改动，零矩阵重跑。当前 C4 固定业务版本 `6ebb` 是 Root 给定运行范围，本次没有重新读回或变更其部署。

## 结论

当前普通 planner 并非缺少一切继承后经济输入：原 root/turn-bundle 已有当前 ruler 的完整个人 title rows、直辖地理县、domain size/limit、现金和月收入，以及当前领主与直封臣。缺的是把这些现成事实与长期 goal 的继承摘要在实际决策消费点相连，以及 **全 subrealm 县集合、其他继承人的继承后上下级关系、可比的继承前财政基线**。个人头衔分给其他继承人，不能替代县离开领国的观测；当前月收入也不能替代继承造成收入变化的反事实。

M3 `matched` 只证明实际后继和已对账 title 分配符合预测。它不是保地、收入稳定或经营质量的 verdict；完全符合预测的分割同样可能给后继留下更小直辖。没有实际分割法、法律收益、动作费用与政治后果的同源证据时，本次不能从风险直接推出变法、加 Crown 或收复战争政策。

## 已有事实与真实缺口

| 输入 | 已有来源与消费 | 未闭合范围 |
| --- | --- | --- |
| 实际后继及个人 title 对账 | `succession_transition_contract.py:580` 的原 reconciliation，输出 matched/missing/other/additional IDs（约688—705） | 未输出县级地理归类、全领国县数、财务或实际其他继承人的领主关系 |
| 当前直辖地理县 | `turn_bundle_contract.py:294` 只从完整 root partition 识别 tier2 且有真实 province 的县 | 不是 domain holding 数，不是全 subrealm；该源明确将 `player_subrealm_county_title_ids` 与 `succession_realm_county_loss` 标 unavailable（364—369） |
| 当前现金、月收入、直辖上限 | 同文件385—435、464—477；可独立 available/unavailable | 没有继承前后同口径现金/收入 delta；title 数不能推税收、军费、债务或承诺。已有战争/建设预算通道应继续独立使用各自原输入，不能用继承事实覆盖 |
| 当前领主/直封臣 | 同文件514—524已有 immediate/top liege、independent、直封臣 IDs | ID向量不枚举其全部县，也没有证明每个分得前代 title 的其他 heir 仍在当前 ruler 的 subrealm |
| 长期 goal 继承记忆 | `strategy.py:6241` 原 `continue_ordinary_campaign_goal_v1`，将 matched/other/unknown IDs留在 `progress.last_succession`（6260附近） | 摘要未保完整title tier、原binding、继承前经济；不能把该无当前frame的历史摘要当后继当前estate |
| 当前逐title风险 | 原 `ordinary_succession_operating_context_v1.py:27` 严格核 living普通episode与完整expectation六字段，列个人分配和typed缺失 | 尚未被普通planner消费；它是当前ruler未来继承预测，不是跨代结果比较器。后继rebind会清前代两字段（`native_driver.py:23454—23471`），不能把前代expectation冒充新ruler当前事实 |

`strategy._same_frame_campaign_root_context`（703—780）已经从原 history/snapshot 找当前 actor/native revision/date 对齐的 root；战争入口也实际消费当前 domain 与 income（15553—15577）。因此不应另起每 AUTO 观察器，也不能声称整个 planner 从未使用经济输入。真正未消费的是 **普通 campaign goal 的继承经营 context**：`ordinary_campaign_goal_plan_v1:6271` 仍给 marriage100/review60；`_cross_run_focus:6298` 只按 action文本选择focus，`_choose_one_life_turn_core:8447` 只取得这个focus。给 goal 增加一个未读字段或只在 Service 最后挂到返回结果，不能算改变决策消费。

## 唯一下一接线点

选择现有 `Service.plan_from_view` 在实际 `choose_one_life_turn` 调用前的 **`next_run_plan=campaign_goal_plan or cross_run_plan` 接口**（`service.py:2180`、约2268—2282）。这里拥有经过原准备的 `planning_snapshot` 和当前原 history；应在这里生成这一次选择所用的普通 goal 输入，复用原 facts 与原已完成 root/turn-bundle，不新增查询。不要在2159用外层旧snapshot提前冻结后再将它当内层当前事实。

下一维护批只沿这一个既有接口接入：当前个人estate风险、现有当前domain/cash/income、各自source binding与typed缺失。原goal consumer必须精确读取这些事实并把被读值、缺失原因留在本次 decision 理由；初步可解释“已观察到个人直辖分割风险；全领国损失未知；本次沿原合法动作和现有资金条件处理”。保留原终态、窗口、战争、待定动作的先后与资格。没有新可证实收益时，不增加priority、动作候选或counter-policy；这种接线本身只获得“决策已消费事实”的软件信用，不能声称改善选招、保地或当前局经营收益。后续若要改变动作排序，必须由相应原动作的来源与真实局面另外支撑。

本轮未实施此共享接线；不新增框架、状态机、跨代财政持久化schema或查询门槛。原living facts叶按其现有合同复用，不能将已消失前代状态补造为新鲜来源。

## 10→2教训的适用边界

原[交接](../handover/2026-10-19-robert-first30-scoring-vacation-handoff.md:70)的10→2是实际统治县指标；不能用个人持有title数或domain holding数替换分母。交接同时明确：AUTO193授独立与当时两个持有ID移出有证，但不能把全部后续失地归因闭合（约100行）。因此本次继承接线只针对“忽略逐title分配与后继当前资源、把符合预测误当经营成功”的盲点；不声称10→2由partition造成，也不以它替换既有P50独立通知策略、战争止损或应急资金政策。其他heir持县可能仍在realm，且宗族保有县也不等于玩家统治县。

上游 `fe3f664fb974fac06f3796171d659be871b21825` 的 inherited building 是 `PresentationBuildingReadyModel12004` 沿GUI lexical context选择最近ready模型，有限读取、原provider语义；不是后继继承地产、税基或可负担新输入。clerical previews同样不增加上述继承财政能力，不授普通planner新变法或借款动作。

## 来源固定与信用

本次只记录来源，不重跑已通过M3矩阵。下列SHA在 `2026-10-19T05:35:35Z` 实际读回（chunk `6ffba7`）；后继共享修改可能改变文件SHA，旧记录不被追认为新代码或已部署结果。

| 路径（仓库相对） | bytes | SHA-256 |
| --- | ---: | --- |
| `ck3_autonomous_player/src/xar_autoplayer/ordinary_succession_operating_context_v1.py` | 8060 | `d8e4445b8d9ab9620cdad36c01bde377f820401976b1dceda6b9065ce68f372a` |
| `ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py` | 29634 | `e162678ea42e2ee89ae8c414eb35652d350e8e7398636ca47ff7b59971aaf33e` |
| `ck3_autonomous_player/src/xar_autoplayer/bridge/turn_bundle_contract.py` | 27516 | `0119ea8a1d41a0ab84ac6dd33f865b022f54595c8097bb6e55a70ba7bcff356a` |
| `ck3_autonomous_player/src/xar_autoplayer/strategy.py` | 1032678 | `ddc62e3093564f8b8126507ce7d0e2639a154ebffa15e6312a8fc74b45c9bf29` |
| `ck3_autonomous_player/src/xar_autoplayer/bridge/service.py` | 867830 | `9a22d369ffc245c7a26439a55819461a5c296a4fce015d1cf0ba85f86055e81e` |
| `ck3_autonomous_player/native_bridge/src/faith_power_presentation_receiver12004.inc` | 12339 | `367d429b666db4b8718959802efbf270a865bf00ec9e5c73382f55e76c3b4134` |

新知识文件小于20KB；没有重型写入、删除或stage/commit/push。按统一存储策略1.0.0，小记录复核点 `2027-04-17T05:35:35Z`。源码审计不新增自然继承、运行采用、保地或G2业务信用。
