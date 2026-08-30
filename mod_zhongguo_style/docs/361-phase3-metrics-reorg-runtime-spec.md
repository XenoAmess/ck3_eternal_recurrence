# 361 二期：指标、组织重构与需求交付 L0 语义模型

状态：2026-08-30，`python-l0-only`。本包是 35 项机制的可执行参考语义，不是 CK3 脚本接线、GUI、MCP 或实机证据；在对应运行时完成并通过 CK3 批量验收前，不得将这些机制标记为 `fixture-live` 或玩家闭环完成。

## 权威实现

- `tools/zg361_phase3_metrics_reorg_model.py`
- `tools/test_zg361_phase3_metrics_reorg_model.py`

模型把需求与交付拆成两类稳定对象：需求冻结 owner/cycle/case/version/deadline 以及提出者、执行者、受益方；进入 WIP 后才创建对应交付对象，并沿阻塞、跨周期、三方验收和上线→采用→价值成熟度递增版本。receipt 只证明命令提交，不能代替业务对象。

覆盖三个连续机制域：

- AA 229–241：指标字典、多源对账、分母版本、人工回填、看板访问权、领先/滞后信号、护栏、计分策略、时间窗审计、虚荣指标、失败实验、样本冲突与长尾归属。
- AG 301–311：核心业务光环、衰退逆风、孵化保护、双家长、校准静默期、双帽容量、利润/成本中心记分卡、管理/专业 HC、边远团队可见度、旧档映射与战略转向。
- AJ 334–344：统一需求入口、紧急插单、准入定义、变更税、范围—期限—质量签字、估算校准、WIP、跨周期债、阻塞归因、三方签收与上线/采用/价值三阶段结算。

## 共同合同

- 命令身份由 `model_id + owner_id + cycle_serial + case_serial + expected_revision + command_id` 冻结。
- 同一命令重放返回幂等 no-op；旧 revision 在校验业务 payload 前返回 stale no-op；同一 `command_id` 绑定不同 payload 是 typed RED。
- 每次有效变更产生连续的 parent/committed revision receipt；provenance ID 不得绑定多个实体。
- 所有 fallible 校验先于提交，RED 后不增加 revision、receipt、资源占用或业务记录。
- 样本槽、紧急插单槽、当期/下期容量、管理容量和 HC 必须守恒；份额统一以 10,000 basis points 或明确的百分比总和表示。
- 历史口径、旧目标、旧档和已接受成果保持不可变；新版本只能从明确生效日向后消费，不能倒改过去的绩效。

## 关键可玩后果

- 指标不能只留下一个最终数字：口径 owner、来源冲突、分母版本、回填签字、访问权和时间窗挑选都会形成可审计事实。
- 实验失败可获得有上限的学习分，但不能冒充成功价值；虚荣指标若没有采用或价值会被追回。
- 重组、双帽和远程管理都会消耗真实管理容量；HC 调整只在经理岗与专家岗之间守恒搬移。
- 需求从来源、准入、变更、施工、阻塞、验收到价值结算形成一条链；紧急插单和 WIP 例外必须显式交代牺牲项或责任人。
- 提出者、执行者、受益方必须由三个不同签字人验收；上线、采用、价值按顺序分段结算，累计不得超过 100%。

## 已验证边界

`test_zg361_phase3_metrics_reorg_model.py` 当前包含 48 个测试，逐项覆盖 35 个编号并检查：

- 精确编号集合与真实 callable 绑定；
- stale、重复、命令碰撞、provenance 冲突和 RED 原子性；
- 指标、样本、容量、WIP、HC、管理容量及分功守恒；
- 稳定需求/交付 identity、版本、期限、三方签名，重复开工与拒收后领 credit 的原子 RED；
- 三个域的关键 A/B 决策后果，以及一个贯穿全部编号的确定性场景。

本模型尚未证明：CK3 parser 可加载、角色/头衔作用域正确、事件期限真实触发、存读档保持、考核榜消费、MCP paused snapshot 或实机玩家可见闭环。后续 CK3 runtime 必须复用共享 case identity/receipt 合同，接入真实消费者后再成批启动游戏验收。

## 本地复验

```powershell
py -m py_compile mod_zhongguo_style/tools/zg361_phase3_metrics_reorg_model.py mod_zhongguo_style/tools/test_zg361_phase3_metrics_reorg_model.py
py -m unittest -v mod_zhongguo_style/tools/test_zg361_phase3_metrics_reorg_model.py
git diff --check -- mod_zhongguo_style/tools/zg361_phase3_metrics_reorg_model.py mod_zhongguo_style/tools/test_zg361_phase3_metrics_reorg_model.py mod_zhongguo_style/docs/361-phase3-metrics-reorg-runtime-spec.md
```
