# 361 B2 送达、申诉、反馈与 PIP 参考内核

状态：2026-08-30 建立。本文件冻结 B2 的 Python 参考合同和确定性状态不变量；权威批次范围仍以
[`361-phase2-full-implementation-program.md`](361-phase2-full-implementation-program.md) 为准。

## 边界与计数

- 本批新机制恰好 40 项：014–017、070–081、146–156、181–191、358–359。
- 018、069 只是 B2 要收口的既有跨域接口，`batch_role=interface-only`，不得计入 40 项新完成数。
- `tools/zg361_b2_runtime_data.py` 是 CK3 无关的可执行参考内核；它不生成或修改 Paradox 脚本。
- 本包固定 `CK3_IMPLEMENTED=false`、`runtime_evidence=python-reference-only`、`readiness_change=none`。
  单元测试 GREEN 不得写成 fixture-live、production-live，亦不得提升 `domain_runtime` 或
  `player_visible_loop`。

## 逐项冻结合同

42 行合同都必须冻结以下字段：

1. `owner / subject / cycle / case / state` 身份与状态绑定；
2. 实际消费该对象的 lifecycle hook；
3. `from_state → to_state`、meaningful write 与下游 consumer；
4. A/B/C 三路 typed operation；A、B 写业务案卷，C 只写一次有期限的 policy-debt receipt，业务状态不变；
5. target-bound deadline 与完整 stale guard：owner、subject、cycle、case、expected state；
6. transaction conservation、全局唯一 receipt、幂等 replay、`refund <= settled`；
7. 玩家可见 feedback 投影。

Python 表还逐行和冻结的 `361-mechanism-manifest.json`、runtime snapshot 对照 title、domain、object、operation、
owner/subject/cycle/case 与 hook，防止批次身份漂移。

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
py -m compileall -q zg361_b2_runtime_data.py test_zg361_b2_runtime.py
```

这些验证只证明 Python 合同、状态迁移、幂等与守恒，不替代 CK3 产品脚本、paused fixture 或实机验收。
