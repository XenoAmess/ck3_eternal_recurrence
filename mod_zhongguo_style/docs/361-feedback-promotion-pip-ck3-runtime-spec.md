# 361 二期 T/U/V/W：反馈、晋升与 PIP CK3 运行时规格

状态：2026-08-31 `static-ready`。本批覆盖 **146–191，恰好 46 项**。它已经拥有可加载的 Paradox effects/events/localization 和 L0 测试，但尚未接中央 hook，也未做 MCP-first CK3 实机验收，因此不声称 fixture-live、production-live 或 361/361 完成。

## 一、权威输入与产物边界

语义输入按以下顺序解释：

1. [`361-expansion-options.md`](361-expansion-options.md) 的逐项玩法定义；
2. `tools/zg361_domain_data.py` 的 T/U/V/W 生命周期、资源和不变量；
3. `tools/zg361_b2_runtime_data.py` 对 T/W 的送达、反馈、承诺与 PIP typed contract；
4. `tools/zg361_phase2_career_model.py` 及其 tests 对 U/V 的确定性参考公式；
5. `tools/mechanism_acceptance/acceptance_121_240.json` 对 A/B/C receipt、C 路线和验收断言的补充。

本包只拥有以下独立文件：

- `tools/gen_361_feedback_promotion_pip_runtime.py`；
- `common/scripted_effects/zg361_feedback_promotion_pip_runtime_effects.txt`；
- `events/zg361_feedback_promotion_pip_runtime_events.txt`；
- 九语言结构文件 `localization/*/zg361_feedback_promotion_pip_l_*.yml`；
- `tools/test_zg361_feedback_promotion_pip_runtime.py`；
- 本规格。

它不修改 B1、B2、scoreboard、GUI、互动、on_action、共享 case kernel 或中央 dispatcher。简中、英文为本轮创作文案；法、德、日、韩、波、俄、西仅是英文结构占位，不算发布翻译。

## 二、唯一接线口与权限

中央未来只允许调用一个 manager-scope adapter：

```text
zg361_pp_manager_portfolio_adapter_effect
```

adapter 当前 scope 必须是：在世、有地、天朝制、公爵及以上领主，并已有真实 `zg361_review_serial`。它按 stewardship 稳定选择一名直属可受评官员，并按 T → U → V → W 每次只打开一个尚未完成的领域。中央接线不应直接同时调用四个内部 `open_*`。

- 玩家经理：每次只排入当前阶段的第一张决策卡；选完一张，所选 option 才会在 D+1 排下一张。
- 授权 AI 经理：这是项目所有者确认的第二 AI 例外；同样必须过天朝制公爵以上门槛，只走后台 resolver，绝不打开事件或 GUI。
- 伯爵、男爵：可以成为直属受评 subject；不能成为 adapter ROOT，不能提名、组评委、发起 PIP 或考核别人。
- #151、#166、#183、#190 另有 subject-self response，仅允许本人签收/撤包/拒签理由/转岗披露回应；这些 effect 不授予任何管理权限。

`zg361_pp_portfolio_queue_active` 在经理身上锁住当前可见队列。玩家路线在领域终态后仍保持锁，直到玩家确认唯一一张 completion card 才释放；AI 后台路线没有可见卡，领域终态立即释放。这样中央调用即使与终态同日发生，也不能把下一域首卡和完成卡叠在一起。因而即使本包包含 46 张玩家卡，任意时点也只会出现至多一张，不存在“一次弹 46 窗”。

每个领域重开前还必须满足：该 subject 上本领域所有旧 `audit_*_state != 1`。这是跨周期票据的防覆盖条件；否则 D+365 的旧事件可能读到复用后的新变量并提前消费新案。adapter 遇到仍有旧审计的领域时跳到其他可开的领域，中央调用者之后重试；旧审计终态前绝不 reset 其 receipt。

## 三、四条真实状态链

| 域 | ID | case kernel 状态 | 本包阶段 |
|---|---:|---|---|
| T 反馈谈判与承诺债 | 146–156 | `result_locked → feedback_held → receipt_recorded → actions_open → resolved` | `146–148 / 149–151 / 152–154 / 155–156` |
| U 晋升提名与预审 | 157–168 | `eligible → nominated → slot_reserved → prescreened → resolved` | `157–159 / 163–165 / 161–162、166 / 160、167–168` |
| V 晋升答辩与评委政治 | 169–180 | `panel_formed → recused → blind_reviewed → defended → voted → resolved` | `169–171 / 172–173 / 174–176 / 177–178 / 179–180` |
| W PIP 启动、毕业与复发 | 181–191 | `triaged → evidence_met → acknowledged → executing → midpoint → resolved` | `181–183 / 184–185 / 186–187 / 188–189 / 190–191` |

每一阶段同时有 target-bound case-kernel deadline。到期只把本阶段尚未处理的编号走 C，不重放已完成操作；旧 owner/subject/cycle/case/state 任一变化，hidden event 即 stale no-op。

U 的编号顺序特意不按自然数平均切段：#166 必须发生在 #160 预审之前，只有 `NOMINATED` 包才允许撤回；#163–165 先冻结观察窗、跨组贡献与试岗授权，#161/#162/#166 再完成席位前置，最后 #160 消费整包并由 #167/#168建立跨周期样本。V 则严格保持答辩语义：#176 仍属于 defense 阶段，#177/#178 才进入投票前的杠杆与双证据门。

## 四、A/B/C 合同

每项都暴露一个 typed manager operation：

- A：证据路线。写入该机制的业务 payload，再由同机制 consumer 和延迟 audit 消费；
- B：政治/压榨路线。仍写真实 payload 和后果，同时留下程序、公平、误判、拥塞或经理责任债；
- C：有界延期。**只写 owner/subject/cycle/case/state/route=3 的 policy-debt receipt 与 90/180 日 audit，不调用 `zg361_case_kernel_record_operation_effect`，不写 typed payload，不扣业务资源。**

这条 C 边界修复了旧 manifest 的危险泛化：C 可以让 dispatcher 收口“本阶段已经作出延期决定”，但不能伪造提名包、评委票、PIP 事实或其他 primary business object。

P1 的 C 审计为 D+90；P2 的 #147、#149、#154、#155、#161、#162、#166、#170、#172、#173 为 D+180。业务自身的 1/7/30/90/180/365 日期限仍单独保留；#151 同时拥有 D+7 见证/更正票据和 D+90 申诉票据。

## 五、逐项 write → consumer 账

### T：反馈、谈判、纪要与说明会

| ID | A/B 真实写入 | 下游 consumer |
|---:|---|---|
| 146 | 冻结档位不变、表达方式、理解回执 | 反馈会与申诉时钟读取同一档位 |
| 147 | 证据链接、褒贬句与套话数 | 反馈质量表只给有证据句记信用 |
| 148 | 证据/档位快照与会议步骤顺序 | 纪要、事实确认和异议行 |
| 149 | 当前低档不变的书面条款、owner、D+180 | 个人谈判页按实际付款 receipt 核销 |
| 150 | 团队牺牲标记、书面/口头承诺、D+365 | 承诺时间线结算履约或背约 |
| 151 | 送达、认同、异议、见证、申诉资格分列 | 收据、见证与申诉案卷分别消费 |
| 152 | 具体/可控/期限/资源四分量 | 经理反馈质量表按收件人一次回写 |
| 153 | action owner、原/现期限、验收证据 | 行动时间线只接受一个终态 |
| 154 | 完整/摘要模式、证据索引、追加更正 | 申诉投影只读版本与更正附录 |
| 155 | 获准公开字段、私人敏感字段、羞辱后果 | 团队公告与个人反馈分开投影 |
| 156 | 分布原则、共性问题、资源计划、完成回执 | 政策面板读取说明会或流言债 |

### U：提名、预审、撤包与 sponsor 信用

| ID | A/B 真实写入 | 下游 consumer |
|---:|---|---|
| 157 | self/manager 模式、sponsor、主管意见、一人一包 | #158 排序、#160 预审、#166 撤包 |
| 158 | 固定额度、排序、已用/归还/剩余 | 提名额度恒等式与下轮额度 |
| 159 | 接班人、交接资源、最迟提名日或雪藏债 | 逾期审计每周期只扣一次人才分 |
| 160 | 三维预审量表、席位、通过/淘汰理由 | V 域只接收真实出线包 |
| 161 | filler、准备工时、公平债 | 经理公平信用与主推包合法性 |
| 162 | 破格额、准入投票与能力评审分离 | 能力评审不把准入当通过 |
| 163 | 周期初冻结的统一观察窗 | #169 评委包消费同一窗口 |
| 164 | 旧 owner 共签/独立复核与贡献份额 | #169 与后续个人归因消费份额 |
| 165 | 真实授权、补偿、期限、退出条件 | #169/评委包消费试岗验收，不改当期绩效 |
| 166 | 预审前撤包、已验证材料、准备度风险 | 精确 refund #157 nomination receipt；撤包不复活 |
| 167 | sponsor 强度与下一周期观察 | #168/后续胜任只结算一次信用 |
| 168 | 难度加权通过+胜任、无故漏提 | 上司下轮辅导或收紧额度 |

#159 的 A 路线识别同一 subject 已在 #157 获得本轮提名，因此立即关闭雪藏义务；B 路线才在 manager scope 留下持久 `candidate/due_cycle/active/last_penalty_cycle`，后续 U 周期每周期至多扣一次，直到同一人被 #157 提名。#167/#168 的 D+365 样本在成熟审计前会阻止 U receipt 变量复用；#168 只写 manager 的 `next_quota_pending/delta`，下一次 U open 才一次性消费并把额度钳制在 1–3。

旧 Python 模型有一处已知缺陷：`withdraw_packet()` 把包留在 `packets`，而 `prescreen()` 会再次遍历它，可能把 WITHDRAWN 包“复活”并复制额度。本 CK3 runtime 不复用该行为；#166 只 refund #157 的唯一 nomination receipt，预审 consumer 只读取 active 包。

### V：评委、盲审、答辩与重试

| ID | A/B 真实写入 | 下游 consumer |
|---:|---|---|
| 169 | expert/external 权重合计 100，并消费 U 窗口/贡献/试岗 | #172 投票器分列专业深度与业务价值 |
| 170 | 冻结 pool/seed、无重复 selected、有限熟人席 | #171/#173/#172 使用同一 active panel；候选不得控制多数 |
| 171 | 冲突披露、同 kind 清洁替补、重审债 | #172 只接受回避后的 active panel |
| 172 | 事前规则、票值、veto 理由、最终决定 | 冻结规则下一人一票；规则只能写一次 |
| 173 | 去身份 blind score、解盲时间、live score | #178 和评委质量复盘消费不可变盲分 |
| 174 | 总时长、陈述、受保护质询 | #179/答辩记录校验陈述+质询=总时长 |
| 175 | 公共 coaching pool、分配、剩余、机会不均 | #178 只改变表达准备，不制造成果 |
| 176 | 候选与同伴份额合计 100、抢功债 | #178/晋升包只取候选自身份额 |
| 177 | 项目 scale 与个人 leverage 分列 | #178 目标级别同时消费两个维度 |
| 178 | artifact/narrative 双门槛与缺口 | 决定投票资格或补材料，不随机放行 |
| 179 | actual panelist owner、gap、next evidence/no-slot | #180/下轮材料沿用同一 gap；空话不可作 PIP 证据 |
| 180 | cooldown、材料版本、冻结差距、重试一次 | 到期或全 gap 完成才重开，不重复耗 slot |

参考 Python `PromotionPanel` 的多数方法没有调用 `GuardedCase.mutate()`，并允许若干字段二次覆盖；本运行时不能照抄。每项都走五元 guard + 独立 receipt，blind score、规则、归因、时间、材料版本等均由一次性 consumer 冻结。

### W：PIP 证据、支持、毕业与退出成本

| ID | A/B 真实写入 | 下游 consumer |
|---:|---|---|
| 181 | 唯一主分诊类别、证据、错岗/误诊 | PIP 入口选择训练、纪律、改目标或真实转岗 |
| 182 | 启动证据组合、误伤风险、违纪分流 | 正式开案门；3.25 本身不是充分条件 |
| 183 | 目标/资源/期限、双签/拒签理由、一次修订 | 任务页分开送达、认同与拒签；拒签不等于失败 |
| 184 | active case、pip capacity、导师/错峰、过载责任 | 终态一次释放容量 |
| 185 | 唯一中检、进度、资源交付、一次修正 | PIP 时间线；未做中检不得倒造更正 |
| 186 | 基线/当前工作量、替换/延期/复核、膨胀违规 | 变更账消费同一冻结基线 |
| 187 | 关键里程碑、稳定期、独立复核/延期 | 毕业释放容量；绝不直接写 3.75 |
| 188 | 一周期观察、问题类别、过度标签风险 | 只对同类复发升级；新问题另开案 |
| 189 | 二次 PIP/真实空缺转岗/退出三选一、成本 | 终局页只接受一个互斥终态 |
| 190 | 接收经理 ACL、最小字段、本人陈述 | 转岗包不改旧档位、不扩散私人 ID |
| 191 | 空缺、交接、加班、补员付款与净额 | 团队成本单和经理记分卡消费同一净成本 |

## 六、资源与原子性

每项 A/B 首先用 `operation_capacity` 留下一次确定性 transaction receipt；这只是本包防重/守恒账，不冒充业务稀缺资源。真正稀缺资源只在相应机制消费：

| 资源 | 消费点 | 不变量 |
|---|---|---|
| `capacity_hours` | T 的反馈工时；#161/#165；#171/#172/#175 | `available + reserved + settled = authorized` |
| `commitment_capacity` | #149/#150 | 一项承诺占一次，不能口头重复履约 |
| `nomination_slot` | #157；#161 的 B 路线另建真实 filler 包 | 一包一次；#166 只 refund #157 主包的同一 receipt，不退 filler |
| `tenure_exception_slot` | #162 | 破格准入先占独立额度，能力评审不等于准入投票 |
| `promotion_slot` | 仅 #160 | 预审席位不是 12 个机制各扣一次 |
| `panel_vote` | #169/#170/#173/#174/#176–180 | active panel、权重、盲分、答辩和反馈均引用同一冻结席位 |
| `pip_capacity` | 仅 #184 正式承载 | 每案预留、终态释放一次 |
| `exit_cost` | #189/#191 | 互斥终态与成本单各一次 |

其中 V 的资源绑定刻意区分：#172 冻结决策规则消耗 `capacity_hours`，#174 才消耗答辩 `panel_vote`；#180 重试不再扣 nomination slot。每笔 A 路线保持 `reserved/status=1`，B 路线同步 settle 为 `status=2`，C 路线不生成业务 transaction。新周期只在全部延迟审计终态后清零 amount/status/owner/cycle/case，因此跨周期不会把旧票据当新票据。

#149、#150、#165、#189、#191 的有资金 A 路线先原子核对经理国库 ≥5 且个人金币 ≥5，随后才同时扣国库 5、个人金币 5，并给 subject 10。任一不足则不发生部分付款。receipt 明列 `treasury_paid=5 + personal_paid=5 = subject_received=10`。这把“组织预算”和“经理自己画饼的成本”同时落到了 CK3 资源，而不是再造一枚 PPT 货币。

## 七、可见队列与本地化

玩家卡为 `zg361pp.146` 至 `zg361pp.191`。每张恰好三个 option；每个 option 最多排一个下一事件。阶段最后一张不自行排卡，而由 barrier 成功 advance 后只排下一阶段第一张。四个 completion event 为 `zg361pp.9001–9004`；AI 永不收到它们。

每个业务操作还调度一个精确延迟 audit；#151 有 D+7/D+90 两个，#180 有完成差距的 D+90 提前解锁与正常 D+365 两个，因此共 48 个。audit 保存并复核：

```text
owner + subject + cycle_serial + case_serial + expected_local_state
```

同票重复、旧上司、旧周期、旧案号、已消费或状态不符都只写 stale debug，不重复扣钱、占槽、写债或加经理责任。

## 八、L0 验证与下一道门

```powershell
py tools/gen_361_feedback_promotion_pip_runtime.py --check
py tools/test_zg361_feedback_promotion_pip_runtime.py -v
py tools/test_zg361_phase2_career_model.py -v
py tools/test_gen_361_b2_runtime.py -v
py tools/test_zg361_case_kernel.py -v
py tools/validate_local.py
```

`tools/test_zg361_b2_runtime.py` 仍可作为 T/W Python reference 回归运行；当前仓库基线为 45/46，唯一 RED 是该测试仍要求 146–156、181–191 的中央 manifest 为 `not-implemented`，而并行收口已把这些行标为 `partial`。它不是本独立包的 effect/event RED，本包也不越权修改 B2 或中央 manifest；最终中央合并时必须由对应 owner 统一 readiness 口径。

L0 固定检查：46/46、四域状态组、每项 manager/core/consumer、A/B/C、C 不碰业务 operation、48 个五元 audit、18 个 stage deadline、跨周期 pending-audit 防覆盖、资源恒等、#166 精确退额、五个双 payer、U 跨周期观察、V 评委/盲审/双门/重试链、manager/subject 权限、第二 AI 例外、单窗队列、九语言 BOM 与生成可复现。

下一步由中央代理接 `zg361_pp_manager_portfolio_adapter_effect`，与其他二期包一次性跑 MCP-first CK3 批量验收。必须同一启动覆盖：玩家公爵/国王/皇帝、授权 AI 公爵、伯爵/男爵 subject-only、非天朝 manager RED、A/B/C、资源不足、重复、stale、D+7/30/90/180/365、存读档与四域顺序队列。没有 paused snapshot、日志和玩家窗口证据前，本包保持 `static-ready`。
