# R195/R196：同一 S0 的 32 日登船对照与实际 personal SUB（1.20.0.4）

R196 的原始付款段经生产消费者重新闭合出 **1 笔选定 Army18 的正额登船扣款**：payer31254、personal account_kind0，`amount_raw=300000`，原钱包 `26010399→25710399`，恰好减300000。游戏本场 gold scale 为100000，对应本次3金币。该结论取自完整 natural-return→transition→gateway→personal SUB 原始链及返回余额，未以两臂净现金差估计费用，也未把日32增量空数组解释为免费。

`machine_id: desktop-3fevhd2-1c74096080`。历史 source `611bc985ae95f477dd7314df11f8602cd1e595f3` / a33；control 为 R0195，treatment 为 R0196。R195 正常闭场与既有生产重放直接复用，原包不复制、不重跑；R196 本包在该冻结源码下完成一次生产重放。原文观察时间、进程身份与 exact pins 均在[便携清单](evidence/episode04-r196-r07-boarding-pair-12004/R196-TREATMENT-EVIDENCE.manifest-a01.json)；生产重放结果见 [PRODUCTION-PAIR-REPLAY](evidence/episode04-r196-r07-boarding-pair-12004/PRODUCTION-PAIR-REPLAY.actual-a01.json)。

## 独立两臂与日期边界

两次独立正常冷载均来自 R191 正常 checkpoint，73,689,246B / SHA `bc3d40861e908ba8b05d5c86094a0ff7a399216ef0e4d0c1a72f166559b40ca2` / 日期53148192。两臂 actor31254、Army18、commander31254、完整 DATA 稳定签名、1173/1195、supply30000000、初始 treasury25804687/100000、战争局面与 source/DLL/EXE 均独立核合。R195 PID29000/FT134366728035105406；R196 PID36072/FT134366756638003884，episode 各自独立，不能把旧 continuation 当 fresh treatment。

R195 完成32个精确日且全程驻2635/空 route；其两末段 natural/payment 为48/12、16/2，未出现该军的 source-qualified boarding callback。R196 同样完成32个原 Arm/status/complete，各日 tick1、overshoot0；仅一次新的正常 Move 指向原生合法首海1032，实际初始 edge cost3000000、rate100000、duration3000000/Q100000，陆→海定义1→0。

| R196 日期 | 实际后态 | 判读 |
| --- | --- | --- |
| 日29 / 53148888 | 2635，route[1032]，weight2900000/cost3000000，remaining100000 | 尚未入水 |
| 日30 / 53148912 | 2635，route[1032]，weight=cost3000000，remaining0，arrival provider0 | ETA归零仍不是已到达 |
| 日31 / 53148936 | 1032、embarked、空 route；本日增量首次包含正 SUB | 实际入水与实际付款 |
| 日32 / 53148960 | 仍1032、embarked、空 route | 稳定后态；不能因本日无新增扣款漏掉日31 |

本次30日 cost 的 arrival 仍须越过严格边界后在第31日观察到。该32日修订为 R07-v2，**不关闭原 R07-v1 的≤7日合同**，不改写 R0173/R0174 或旧 partial 证据。3金币只覆盖本次实测军队/来源/路径，不能推出所有军队固定收费、每百人费用或事件军通用公式。

## 原始付款闭包

R196 两段分别为 window/payment/natural epoch1与3，末包 natural/payment48/12与16/5；各段均完整、无覆盖、无 failed append/publication failure，换段前归档与实际 OFF/clear、后续空 admission 均保全。序号为同段父子链身份，不按 entry/return 完成顺序排序猜关系，也不跨 clear 拼链。

第二段完整末包重建的合格链为 writer_sequence3、gateway_sequence4、transition_sequence5；actor/payer31254，transition native Army18、requested public unit18、province1032。personal SUB 的300000与 gateway amount/resource0/component3、同 character/wrapper、original entry/return、自然父调用及返回均由 `normalize_journal` 再算匹配；account_kind0、land_id=null。本次没有 Land SUB 付款结论，也不能仅因 payer 恰好等于当前 commander 就断言总由 commander 支付。

`sampling.qualified_records`、raw4 child 的资格计数与 `qualified_boarding_debits` 是不同接口字段；某个计数为0不能替代生产完整链判定。本次末包仍含日31的序号3/4/5，reader 从本段 initial latest0 消费全部 retained records；日32的 `new_qualified_boarding_callbacks=[]` 仅表示 runner 已在日31消费，没有新增。日1–24的 generic wallet ADD205712与上下文另列，`maintenance_attribution=unclosed`；它不是已归因维护费，R08 不随本次登船研究自动关闭。

R07-v2 的共同 S0、两 fresh arms、同等32日、静止 control、一次合法30日首海 Move、真实31日入水、正额 source-qualified SUB 与无覆盖窗口证据均实际具备，下述正常闭场追加也已通过。因此本专题判定 **R07-v2研究核心与完整 fresh pair 闭合**。单窗 `consume_window` 的 `full_v2_qualified=false` 按其合同保留；该单窗标签不会自行作整卡判断。Root 的总账版本选择与最终媒体信用另有实际决策来源，本专题不制造其签核。

## 原卡逐项对照与计分建议

原始 `EXPERIMENT-CARDS.md` 为27,122B / SHA `dc1f06132109032d9ddef9316faacdb04bd2c1759a96ea38ec99c2d5f27bddab`；本包的 ORIGINAL-CARD-COMPARISON 原样保留其 R07 全节及 exact pin。

| 原 R07 要求 | 本次实际结果 | 是否授原 v1 |
| --- | --- | --- |
| 同正常T0独立两回放、一次新Move、驻地对照 | 两个新PID同S0，32日对称；control未入水，treatment一次Move后入水 | 此项通过 |
| actual producer/receiver/payer/amount 与同账户真实SUB | 原始链重新闭合，payer31254 personal SUB300000，返回余额严格减法 | 此项通过 |
| 收支独立，不用NET差归因；路径quote缺失则unknown | generic ADD另列，登船SUB独立；没有以旧quote或净差填付款 | 此项通过；quote仍不外推 |
| 单窗≤7实际日，避开实际经济结算机会 | 两臂32日、到第31日才入水；没有“避开经济结算”的来源资格 | **不通过** |

故 `original_R07_v1_qualified=false`。按已版本化 [R07-v2关闭合同](episode04-r07-v2-boarding-control-12004.md)，建议将本次记录为 **R07-v2研究/业务核心已闭**。若 Root 明确在当前修订总账采用 R07-v2 作为R07的现行研究合同，可各增加1卡；从本次复核读取的7/14、5/11基线计算是8/14=57.1%、6/11=54.5%。这是具名版本更新建议，不能静默写成原七日卡已经通过；坚持原 v1 分母时本次不给原卡加分。动态/正式ABC/影片签核不随研究加分。

## 拍摄、闭场与复用

本包保存实际单次 Start/Finish 的 FILM 原文：owned PID36072、1280×720 client region、day30–32 runner exit0、Finish `NORMAL_TREE_EMPTY`。它是桌面 client-region 捕获，`direct_hwnd_capture=false`。原 FILM 自身 `dynamic_qualified=false`、`payment_qualified=false`、`actual_PTS_endpoint_coverage_verified=false`；本研究包不替媒体 lane 授 continuous-clean、PTS覆盖、人工1×观看或最终成片 signoff。

实际正常终端已独立追加为 [R196-NORMAL-CLOSE](evidence/episode04-r196-r07-boarding-pair-12004/R196-NORMAL-CLOSE.manifest-a01.json)，纯元数据检查结果为 [CLOSED-PAIR-ASSESSMENT](evidence/episode04-r196-r07-boarding-pair-12004/CLOSED-PAIR-ASSESSMENT.actual-a01.json)。R196 终点仍53148960/1032/embarked/空route；正常 checkpoint74,482,297B / SHA `92237e6bee34b1cefac1b6ebe517d40055461c49fcba86cd1f4a2951d0e83f81`，实际 process exit0、tree/SDK/keeper/recorder收净、screen CAS释放且resources=[]。闭场追加不重放付款消费者，也不重跑旧control。

新包完整收录297件小原文共10,019,766B，使用 solid ZIP_LZMA 压至94,991B；不复制展开 Driver、大存档或视频 raw。原 baseline/anchor 的完整 Driver 只保留 exact references 与已生产验证的稳定 DATA 签名，不能声称 compact 包可重建未收录的大 Driver。两段付款的完整原文与独立 same-frame before 则均可在任意机器重新消费。

```text
python -B -X utf8 replay_treatment_pair.py --archive R196-TREATMENT-EVIDENCE.actual-a01.zip --manifest R196-TREATMENT-EVIDENCE.manifest-a01.json --repo <具有清单精确生产源码的checkout> --control-root <R195-control-evidence目录>
```

这是本场冻结历史重放入口：验证 ZIP/每件原字节、32个原 Arm/status、两末 payment、独立 baseline 与已封 R195 replay；不会重跑旧 control 生产 reader。原件绝对路径仅作 provenance，读取来自包内存切片；无 SDK、桌面、游戏、存档/native binary 访问。代码索引见同 evidence 根的 index；共用生产 reader 为 `r07_v2_contract.consume_window`、`war_payment_observations_v1.normalize_journal` 和 sentinel Arm/stop validators，六个 exact source pins 在 manifest。

跨机可复用知识、代码与历史原文，不据 producer 的运行/Steam/Defender/权限/容量状态授予 replay 机器任何本机资格。继续采用[统一存储策略](../storage-retention-policy.md)，本根≤1MiB、同128MiB共享池、不新增 reservation；manifest 中有有限复核日期与在用理由。
