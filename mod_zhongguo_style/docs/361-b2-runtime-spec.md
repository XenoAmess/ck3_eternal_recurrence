# 361 B2 送达、申诉正义与首段 PIP 运行时

状态：2026-08-30 建立，2026-08-31 完成原生 B2 语义补强。本文件冻结 B2 的 Python 参考合同、CK3 静态产品边界和
确定性状态不变量；权威批次范围仍以
[`361-phase2-full-implementation-program.md`](361-phase2-full-implementation-program.md) 为准。

当前结论：19 个原生 B2 ID 已具备生成式 CK3 案卷、A/B/C 路由、幂等/过期保护和下游消费者；但 #069 的 C 路仍有一个
明确的 shared-hook RED（见下文），且整个批次尚无 paused fixture/实机证据。因此只能称 `static-ready/central-wired partial`，
不能称 fixture-live、production-live 或二期完成。

## 边界与计数

- 原生 B2 generator 的唯一权威范围恰好 19 项：014–017、069–081、358–359；其中 #069 仍是既有跨域接口。
- 146–156、181–191 已归 `zg361_feedback_promotion_pip_runtime` 独占实现。B2 generator 只保留负向 ID guard，禁止复制这些机制、
  生成同名案卷或宣称第二套 lifecycle owner。
- `tools/zg361_b2_runtime_data.py` 是早期 42 行跨包 typed contract，仍由 feedback-PIP 测试复用；它不生成或修改 Paradox
  脚本，也不代表 B2 generator 对 T/W 的所有权。
- `tools/zg361_b2_semantic_model.py` 只覆盖上述 19 个原生 ID，以可执行方式证明 choice→稳定案卷→consumer、C 路不建案、
  duplicate/stale no-op；它同样不是 CK3 live 证据。
- 本包固定 `CK3_IMPLEMENTED=false`、`runtime_evidence=python-reference-only`、`readiness_change=none`。
  单元测试 GREEN 不得写成 fixture-live、production-live，亦不得提升 `domain_runtime` 或
  `player_visible_loop`。

## 逐项冻结合同

19 个原生 CK3 对象及共享 typed contract 都必须冻结以下字段：

1. `owner / subject / cycle / case / state` 身份与状态绑定；
2. 实际消费该对象的 lifecycle hook；
3. `from_state → to_state`、meaningful write 与下游 consumer；
4. A/B/C 三路 typed operation；A、B 写业务案卷，C 只写一次有期限的 policy-debt receipt，业务状态不变；
5. target-bound deadline 与完整 stale guard：owner、subject、cycle、case、expected state；
6. transaction conservation、全局唯一 receipt、幂等 replay、`refund <= settled`；
7. 玩家可见 feedback 投影。

Python 表还逐行和冻结的 `361-mechanism-manifest.json`、runtime snapshot 对照 title、domain、object、operation、
owner/subject/cycle/case 与 hook，防止批次身份漂移。

## 原生 19 项产品语义

| ID | 稳定对象与真实消费者 | A/B/C 边界 |
|---:|---|---|
| 014 | 冻结原 owner/subject/cycle/case、理由与证据 revision；真实退款仍复用按实付 receipt 的共享改判链 | A 独立复核，B 原链快审并披露冲突，C 不建增强案卷 |
| 015 | 3.25 送达后开唯一 PIP；本人接受/协商一次/拒绝，D+365 仅一个终态 | A 可控目标，B 高压与拒绝风险，C 不建 PIP 案 |
| 016 | 导师、12 工时、1 容量与 25 国库支持预算原子核对；终态只释放容量一次 | A 全部齐备才扣国库，B 明示只给指标不给资源，C 不建支持包 |
| 017 | PIP 失败后才开处置案；首次末位只允许延长支持，更高阶处置读取连续末位/加速证据 | A 阶梯处置，B 有证据加速并留风险，C 不建处置案 |
| 069 | 正式送达、见证拒签、D+90 时钟与 actual settlement receipt | A/B 可结算；C 必须在任何资源写之前拦截，当前 shared caller 仍 RED |
| 070 | 申诉后 365 日观察对象；不含后续新事实的动作暂停，真实新事实另案送达 | A 独立审查，B 冒险管理并加权反转风险，C 不建观察期 |
| 071 | 私下/正式渠道耗尽后冻结公开证据包、哈希和 D+30 核查 | A 有界证据公开，B 追求传播并承担双边声誉成本，C 只记债 |
| 072 | 结果冻结时锁 ACL；送达前读取只记录一次来源、先手期与 D+30 调查 | A 拒绝越权读取，B 记录真实提前读取及来源，C 不建泄露案 |
| 073 | 举报来源、材料哈希、真伪与保护/处分终态 | A 分流真实吹哨与恶意泄密，B 一刀切并保留压案责任，C 不建举报案 |
| 074 | 组织原因、50 国库→50 个人金币、真实退出和 HC 释放、D+30 守恒审计 | A 诚实裁撤，B 披露洗成绩及翻案责任，C 不建裁撤案 |
| 075 | 可拒绝的退出包与 D+30 有效期；拒绝不扣钱、不改案、不释放 HC | A 有资金才签，B 零补偿胁迫转程序责任，C 连弹窗都不创建 |
| 076 | 翻案后 50/25/25 或 100/0/0 责任份额，总和固定 100；债落在真实管理链 | A 多级分责，B 直属背锅并保留系统缺陷，C 不建责任案 |
| 077 | 同级候选排除双方与近亲；真实 friend/lover/rival 冲突同步消费双方各一次回避 token | A 独立轮换，B 明示原席自纠，C 不指派复核人 |
| 078 | 每份冻结结果进入六维 cohort 分母；翻案只更新匹配分子，交叉乘法比较率 | A 只提示/解释，B 记录强制调整风险但不自动写 grade，C 不聚合 |
| 079 | 隔级席位容量、D+30 调查、证据 revision 和下一次直属结果 remand consumer | A 调查发回，B 现场承诺被标越权并撤销；任何路线都不直接改分，C 不占席 |
| 080 | 唯一 defect ID、type、证据 hash、D+90 修复/接受风险/压案及下一版本验证 | A 修复或具理由接受，B 压案后同缺陷复发落责任，C 不建缺陷单 |
| 081 | subject/直属/隔级/中央 ACL、读取 receipt、原始证据与摘要压缩标记 | 权限只改信息流；grade writer 永远保持冻结直属 owner；C 不建权限投影 |
| 358 | 原 grade 与国库/个人/贤能处分向量冻结；后续新事实只能另案送达 | A 同案不加重，B 加重必须显式披露并记报复风险，C 不建宪制案 |
| 359 | 预留位、边界人重审+新 case ID/新 D+90、或下一周期 quota debt 三路守恒 | A 可审计选择，B 暗调保留 audit diff 且强制重送，C 不建配额回流案 |

## #069 shared-hook ABI 与当前 RED

`zg361_b2_pre_notice_settlement_gate_effect` 是冻结的唯一前置 ABI。共享
`zg361_settle_delivered_325_effect` 必须在**第一笔** `remove_treasury` / 个人金币 / 贤能 / 降俸写入之前调用它，然后仅在
`zg361_b2_m069_settlement_allowed = 1` 时继续。callee 已满足：

- 完整核对 owner、subject、cycle、case、`notice_state=prepared`；
- A/B 返回 allowed=1；
- C 返回 allowed=0，只投递一张下周期 policy-debt receipt；
- 重放和 stale identity 均不得授权。

当前共享 effect 仍先完成结算，随后才调用 `zg361_b2_on_notice_delivered_effect`。B2 专属文件无权修改 shared，故该项必须保持
**RED：`shared-pre-settlement-hook-missing`**。在 shared owner 落钩并补对应静态/实机用例前，不得把 #069 或整个 B2 写成语义完成。

## 确定性状态链

### 送达、处罚与申诉

```text
PREPARED
├─ 本人签收 / 签收并异议 ───────────────→ APPEAL_OPEN
└─ 拒签 → REFUSED_PENDING_WITNESS ─D+7见证→ APPEAL_OPEN
                                               ├─ target-bound D+90 到期 → CLOSED_UPHELD
                                               └─ 本人对冻结上司申诉 → APPEAL_UNDER_REVIEW
                                                    ├─ A：不加重、按实付 receipt 纠正/退款 → CORRECTED
                                                    ├─ B：任何加重必须显式标记 → CLOSED_UPHELD
                                                    └─ C：案卷不动，只写一次 policy debt
```

- 拒签不能逃避送达和后续结算；见证人不得是案卷 owner 或 subject。
- 送达后才允许处罚 receipt 结算，并以实际可扣金额为准；重放不重复扣款。
- 退款逐 receipt 计算，不能超过该 receipt 的实际 settled amount；部分减罚只退差额。
- 新违纪只能链接新的 case identity，不能偷偷并入原申诉造成同案加重。
- 翻案后的配额回流只允许预留位、边界复核或下一周期债三条可审计路线；受影响边界对象必须重新送达并获得新的
  target-bound 申诉时钟。隐藏重排保留 audit diff，审计补救只重送一次。

### 反报复

申诉日起冻结一年观察期。窗口内不含申诉后新事实的负面动作先暂停，交独立复核人判定；有完整申诉后新事实的动作走普通管理。
同一 action ID 只记录一次，周年边界以外回到普通规则。

### 反馈与承诺

反馈会议只能投影冻结档位和证据，不能借话术改结果。签收、签收并异议、见证拒签均只证明送达；异议与拒签继续保留申诉资格。
会议承诺生成 owner、beneficiary、deadline、resource 绑定的 obligation。金币承诺通过真实 receipt 从国库转到个人金币，履行或违约
各只收口一次；存在未决 obligation 时反馈案卷不能关闭。

### PIP

```text
TRIAGED → EVIDENCE_MET → ACK_PENDING → EXECUTING → MIDPOINT
                                                    ├─ 达成关键里程碑、稳定期与独立复核 → GRADUATED
                                                    │    └─ 精确一周期复发观察 → RELAPSED / OBSERVATION_CLOSED
                                                    └─ 未达成 → FAILED
FAILED / RELAPSED → 新案号二次 PIP | 真实空缺转岗 | 有成本 receipt 的退出
```

- 红线违纪直接分流纪律案，不伪装成能力 PIP；拒签本身不等于失败。
- 开案前原子核对经理容量、支持工时、导师和支持预算；任一不足不得部分占用容量或扣款。
- 中期检查只执行一次；A 路线锁住无补偿的目标膨胀，B 路线必须留下违规标记。
- `no_support_liability` 只在“支持确实缺失且最终失败”时写入，不能在开案时预判。
- 毕业后只观察一个周期；同类别复发才升级原链，不同类别必须另建新问题案。
- 转岗要求真实 vacancy ID 与接收经理，只披露最小任务/支持/结果快照及本人陈述；退出成本由国库实际 receipt 支撑。
- 所有终态释放经理容量一次。

## 守恒账本

参考账本把金币和贤能分开守恒：国库、个人金币、金币 sink 属于 gold；贤能与贤能 sink 属于 merit。每次 move 都验证同币种
`debit = credit`，禁止资源跨币种、负数或凭空铸造。处罚允许按可用余额部分结算；承诺、支持与退出费用要求全额到账；退款只能
逆向原 receipt，且最多一次。

## L0 验证

在 `mod_zhongguo_style/tools` 下运行：

```powershell
py -m unittest -v test_zg361_b2_runtime.py
py -m unittest -v test_zg361_b2_semantic_model.py
py -m unittest -v test_gen_361_b2_runtime.py
py -m compileall -q zg361_b2_runtime_data.py zg361_b2_semantic_model.py test_zg361_b2_runtime.py test_zg361_b2_semantic_model.py
py gen_361_b2_runtime.py --check
```

这些验证证明 Python 合同、状态迁移、幂等、守恒与生成式 CK3 静态结构；它们不替代 paused fixture 或实机验收。
