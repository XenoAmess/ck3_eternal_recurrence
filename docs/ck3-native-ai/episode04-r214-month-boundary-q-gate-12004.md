# 战争四期 R214：月界前准备与补员 q 门禁（CK3 1.20.0.4）

`machine_id: desktop-3fevhd2-1c74096080`；实际运行 source `191568c281bbde92feeb9f96fe40736be1b63ca8`，run `desktop-3fevhd2-1c74096080--vanilla--R0209`。本专题是本机实证与源码条件模型的分层记录；[小原件索引](evidence/episode04-r214-month-boundary-q-gate-12004/index.json)含原路径、字节数和 SHA。外机可复用解析规则，不能继承此机的 CK3、Steam、构建或实机通过状态。

R214 原生准备从 1067-03-05（raw `53148432`）精确推进 **26 日**至 03-31（`53149056`），OFF/Save 成立。保存的 Mar31 checkpoint 为 **74,273,410 B / SHA-256 `42dfd2c0ceb1d004ac7b34d921dee174f86b0c854237d447b173ccbebbd1f0bc`**；原正常闭场来源与复制收据分开。[准备终态](evidence/episode04-r214-month-boundary-q-gate-12004/prep-terminal.json)、[保存保护回执](evidence/episode04-r214-month-boundary-q-gate-12004/checkpoint-preserved.json)保留原事实。后续月界 core 段停在同一 raw 日，实际推进 **0 日**、ADD **false**，OFF/Save 成立；[core 终态](evidence/episode04-r214-month-boundary-q-gate-12004/core-terminal.json)。[小 monitor](evidence/episode04-r214-month-boundary-q-gate-12004/monitor-terminal.json)独立核 CK3/native/host/launcher 返回 0 与正常关闭；任务总线 CAS 由 Root 原回执另证，不由 monitor 追认。

在 Mar31 同一 frame，next-day 来源给 `calendar_day=0`、完整 CDate64 ready；这只是**即将到来的月界输入**，没有执行 04-01。旧 `observed_prepared` 模式所选目标 prepared148 全为 0，实测 positive writes 0，因而不满足当场补员门禁。[q 原分析无损压缩](evidence/episode04-r214-month-boundary-q-gate-12004/q-gate.actual.json.gz)与[窄发现](evidence/episode04-r214-month-boundary-q-gate-12004/q-findings.json)另示：`fixed_chunk0_prepare` 在既有定义下能条件性选出 **6 个 q>0 物理槽**。这只是下一场可执行输入建议，**不是**本场实际 prepare、native ADD、兵员净增长或付款。不能把 observed-prepared 的零写外推为“没有补员 provider”。

本场窗口原片 **73.3 秒 / 43,617,360 B / SHA-256 `82ba7bbe7650d7302b48e379f0f7159bc7912b29a1675237b2fc82584c13b379`**，H.264 1280×720/30；单次全解码 0，三张原帧见暂停 03-31 的军队 **6679**、补给 **103/300**，无片内日推进。机器技术 QA 通过；连续 clean、全片 1×、人工签核与正式动态镜头均未通过。[媒体小回执](evidence/episode04-r214-month-boundary-q-gate-12004/media-review.json)有原片路径与 hash，原片没有复制进仓库。

**信用边界：**研究仍 **10/14（71.43%）**、业务 **7/11（63.64%）**、正式动态 **0/11**、ABC **0/3**。下一正例应从已保护的 Mar31 正常源独立加载，按实际 `fixed_chunk0_prepare` 模式重新取同帧资格并推进真实月界，再核 native writer/物理兵数/付款；R214 条件 q 不预定结果。
