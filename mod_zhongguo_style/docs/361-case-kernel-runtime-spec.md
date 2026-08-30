# 361 共享案卷内核

状态：**CK3 script static-ready；尚无实机证据**

生成器：`tools/gen_361_case_kernel.py`

生成结果：

- `common/scripted_effects/zg361_case_kernel_effects.txt`
- `common/scripted_triggers/zg361_case_kernel_triggers.txt`

L0 合同：`tools/test_zg361_case_kernel.py`

## 解决的问题

38 个领域不能各自手写一套 owner、subject、周期、案件号、状态、deadline、receipt 和退款规则。共享内核现在提供：

- 只允许天朝制公爵及以上在任领主开案；玩家与获授权的第二 AI 例外共用同一资格 trigger；
- 伯爵、男爵和其他受评对象只能消费绑定给自己的案卷，不由本内核获得任何管理、校准、PIP、HC 或晋升审批权；
- `owner + subject + cycle_serial + case_serial + expected_state` 五元 stale guard；所有变量读取均在存在性门内；
- 每次操作独立 receipt，重复提交为 no-op；机制操作不能自行推进共享 stage；
- stage dispatcher 是唯一状态迁移者，并在终态关闭 active case；
- deadline 保存同一五元身份并触发真实 delayed event；到期消费者先核对 ticket，旧事件只能 no-op；
- 任意资源统一使用原子 `reserve -> settle` 或 `reserve/settled -> exact refund` journal；一次 receipt 不能二次结算或二次退款；
- 每次有效变化递增 revision、timeline 与可见反馈 revision，供考核榜案卷和 MCP snapshot 后续消费。

## 38 个领域入口

生成器从 `zg361_domain_data.DOMAIN_SPECS` 为 A–AL 各生成一个固定开案 effect，并为状态图的每条合法边各生成一个
stage dispatcher wrapper。wrapper 使用固定变量名，不依赖长期隐式 `ROOT/PREV` 传播；调用方必须显式提供冻结 ticket。

编号机制仍需由各自领域生成器把 A/B/C 路径、业务对象、具体后果与 receipt 变量接入本内核。仅仅拥有共享内核不代表某一条机制
已经实现，也不会改变 manifest 的 `domain_runtime` readiness。

## 事务边界

通用 journal 只负责守恒、幂等与 receipt 状态。领域消费者仍必须在同一个成功分支中应用真实 CK3 后果，例如国库、经理个人金币、
角色 modifier、HC、职位、关系或容量变化。不能只写 journal 而不改玩法状态；也不能先改玩法状态再绕过 journal。

## 验收边界

当前 10 项 L0 测试覆盖生成可复现、BOM、38 域入口和全部状态边、权限、不短路变量读取、五元 guard、operation/state 分权、
deadline、事务原子性和退款封顶。`validate_local.py`、二期 CK3 wiring 与 release reproducibility 均已通过。

尚未完成：CK3 解析日志与真实 paused snapshot、MCP named action/query、跨存读档及长周期到期证据。因此当前只能写
`CK3 script static-ready`，不得写 fixture-live 或 production-live。
