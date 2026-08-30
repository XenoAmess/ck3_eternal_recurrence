# 361 三期事故、积弊与共享平台 Python L0 内核

状态：`python-l0-reference-complete`

CK3 运行时：`static-ready; central-hook-and-live-pending`

权威代码：`tools/zg361_phase3_incident_platform_model.py`

高密度测试：`tools/test_zg361_phase3_incident_platform_model.py`

Python `Behavior.ck3_wiring` 仍保留 `not-implemented`：它描述的是该参考模型自身不执行 CK3 接线，
不得因为旁路生成了一份尚未中央接线、尚未实机验证的投影而抬高 L0 模型声明。

## 精确范围

本包只覆盖机制 192–228，不认领其他 ID：

| 领域 | ID | 对象 | 可执行闭环 |
|---|---:|---|---|
| X | 192–204 | `IncidentCase` | 值守轮盘 → 告警 → 校正分级 → 临时授权 → 冻结时间线 → 分功/根因净额 → 补偿/减免 → 复盘行动项 → 复发管理责任 → 可靠性预算结算 |
| Y | 205–216 | `MaintenanceCase` | toil 快照 → 积弊本息 → 固定偿债预算 → 修补/重做路线 → 危险津贴 → owner 轮换 → 手册/自动化/审阅/质量 → 真实退役 → 四类交接 |
| Z | 217–228 | `PlatformCase` | 采用政策 → 客户/底座双分 → 价值指标 → 成本分摊 → 迁移出资 → 双跑退出 → 重复扫描/合并/合法分叉 → 内开源 → 三角色分功 → 爆炸半径分责 |

`BEHAVIORS` 对 37 个 ID 逐项登记中文标题、行为键与核心 invariant。导入时强制校验：

- ID 集合必须精确等于 `192..228`；
- 192–204 只能映射 X、205–216 只能映射 Y、217–228 只能映射 Z；
- 行为键不可重复；
- readiness 必须保持 `python-l0-only`，CK3 wiring 必须保持 `not-implemented`。

## 状态与原子命令

三个对象分别采用原生领域阶段：

```text
X: on-call -> alerted -> classified -> commanded -> timeline-frozen
   -> actions-open -> resolved

Y: registered -> owned -> funded -> worked -> closed

Z: proposed -> adopted -> migrating -> dual-running -> valued -> settled
```

每个跨阶段命令绑定：

```text
owner_id + subject_id + cycle_serial + case_serial + expected_state
```

五项任一不符返回 `stale-token`；同一 `action_serial` 重投返回
`duplicate-action`。两者都是零变更 no-op。

有效命令严格分两段：

1. `prepare` 只读校验并冻结规范化 payload、资源计划和结果来源；
2. 全部校验通过后才 `commit`，一次写入状态、账本和 provenance。

测试会深拷贝对象并证明钱、工时、状态、action set 和 provenance 在 RED 后完全不变。
所有无效值以带稳定 `RedCode`/`field_name` 的 `ModelRed` 返回；布尔值不能冒充整数。

## Provenance

每个成功命令必须携带至少一个冻结的：

```text
SourceRef(source_type, source_id, frozen_version)
```

成功后生成不可变 `ProvenanceReceipt`，包含机制 ID、action serial、actor、前后状态、
来源、结果 ID 以及 prepared payload 的 SHA-256。端到端测试要求 37 项各有且只有一张机制收据，
来源与结果均非空。

## 守恒与不可冒充

### 工时

`CapacityLedger` 满足：

```text
opening_hours = used_hours + available_hours
```

- toil 与新交付由同一总工时拆分；
- 偿债、业务、剩余工时合计等于周期容量；挪用只在两类间等量移动；
- 修补、重做、迁移、双跑、合并与 fork 都消耗真实工时；
- 积弊还款只能使用已冻结的偿债工时，债余额与投入等量减少。

### 金币

`MoneyLedger` 满足：

```text
opening_gold = available_gold + recipient_credits
```

值守津贴、危险津贴、平台中央/团队分摊都实际扣付款方并等额记入收款账。
展示成本本身不扣款；同周期 chargeback 只结算一次。

### 百分比与损失

- 事故功劳、客户权重、迁移三方份额、平台三角色功劳、爆炸半径责任均合计 100%；
- 严重度绩效读取冻结事实算出的校正等级，不读取 owner 自报等级；
- 高覆盖率最多贡献部分质量分，关键风险漏测可反转虚荣分；
- 平台客户体验与战略底座分开冻结，单个客户不能覆盖底座分；
- 爆炸半径总损失按责任份额只分配一次，舍入余数也进入同一冻结账。

## 端到端证据

测试文件提供一组统一 portfolio 场景：

- 一宗真实事故完整走到 `resolved`；
- 一份积弊/维护案完整走到 `closed`；
- 一个共享平台完整走到 `settled`。

三案合并后的 provenance 精确触达 192–228 全部 37 个 ID。除此之外，还动态注册
37 个独立 `test_mechanism_NNN`，逐项检查对应业务结果，而非只检查 receipt 存在。

## CK3 接线现状与待办

独立 Paradox 运行时已经生成，权威说明见
`docs/361-phase3-incident-platform-ck3-runtime-spec.md`：

- X/Y/Z 共 37 个编号 operation、A/B/C、五元回执和写→消费者已投影；
- 7/5/5 阶段由 14 个身份绑定的 hidden event 推进；
- 国库与管理者个人金币双付款、份额/容量守恒和下一轮 KPI consumer 已落地；
- 玩家与获授权 AI 的公爵及以上管理入口、伯爵/男爵 subject-only 边界由共享 case kernel 执行。

仍未完成：

1. 把独立 `zg361_ip_open_portfolio_effect` 接入中央正式考核链；
2. CK3 中角色、战争/灾害/财政急务、原生岗位、团队与国库的 exact-build 实机互证；
3. 考核榜中的事故时间线、积弊账和平台分账页面；
4. MCP 角色/头衔/国库/变量/时间查询与 paused snapshot；
5. fixture-live、production-live 或实机 CK3 GREEN。

静态生成文件存在不等于 live。只有完成统一接线、MCP-first CK3 批次并保存真实 paused artifact 后，
才能再次提升 readiness。
