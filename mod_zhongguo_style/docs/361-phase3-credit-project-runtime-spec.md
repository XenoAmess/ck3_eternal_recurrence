# 361 二期项目、功劳、汇报与矩阵协作 L0 内核

状态：**Python L0 model / static-ready only**

CK3 脚本接线：**未实现**

MCP / fixture / 实机证据：**无**

权威实现：`tools/zg361_phase3_credit_project_model.py`

逐项测试：`tools/test_zg361_phase3_credit_project_model.py`

## 范围

本内核精确覆盖 27 项机制：

| 领域 | ID | 本层冻结的核心规则 |
|---|---:|---|
| E | 026–031 | 真实贡献与上司可见度分账；贡献签字总和为 10000 bp；抢功和审计回拨各自净零；资源席位、指标审计与 sponsor 信用有界 |
| I | 054–061 | 汇报工时真实挤占交付容量；材料必须先签字再路由，路由不等于被阅读；注意力席位守恒；坏消息时间和版本签名可追溯 |
| J | 062–068 | 实线/虚线权重合计 100；交接必须双签；换老板不改写历史 case owner；取消项目与个人功劳分账；重复岗位只有一个终态 owner |
| R | 129–134 | 晋升排队与槽位守恒；PIP 倾倒责任回源；探索/承诺项目分轨；及时止损不自动算失败；复盘学习与具名责任分轨；共享指标唯一 owner |

`MECHANISM_BINDINGS` 为每个 ID 显式绑定一个或多个可执行行为。模块导入和测试会拒绝缺号、多号、无实现行为或 readiness 冒进。

## 事务与守恒

所有命令携带 `model_id + owner_id + cycle_serial + case_serial + expected_revision + command_id`。过期命令返回
`stale_noop`；已成功执行的同一命令返回 `idempotent_noop`；相同命令号指向不同机制则是稳定的 typed RED。
任何预检失败都必须原子退出，不得留下半条功劳、半个席位或半次签字。

核心守恒包括：

- 项目席位和交付容量不能凭空增加；汇报消耗的工时不会生成真实产出；
- 同一版本的签字贡献严格合计 10000 bp；抢功转移与审计反向转移都保持总贡献不变；
- 路由、可见度、注意力和真实产出是四笔不同的账；
- 实线/虚线经理权重严格合计 100，换老板只改变后续责任，不重写既有来源；
- 晋升、共享指标与重复岗位均只能有一个最终 owner；
- 战略取消保留已验证个人贡献，释放未花容量，不能把业务判断直接改写成个人失败。

## 测试合同

36 项 unittest 覆盖：27 个 ID 的单条确定性端到端场景、精确范围、行为可调用性、UTF-8 BOM、typed RED、原子预检、
stale/idempotent、资源与贡献守恒，以及 `READINESS = python-l0-only` 的诚实边界。

## 仍待 CK3 接线

本层没有 Paradox scripted effect/event/on_action、考核榜项目案卷、本地化、MCP 命名控件动作或实机证据。后续必须把项目、
角色、封臣关系和周期身份映射为可存档对象，再复用唯一考核榜窗口展示来源、签字、版本、争议和结算；不得另加顶层按钮。
只有 MCP 查询与动作闭环在真实 paused snapshot 中通过后，相关机制才能从 Python L0 提升为 fixture-live / production-live。
