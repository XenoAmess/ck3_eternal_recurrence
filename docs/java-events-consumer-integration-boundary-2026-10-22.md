# Java 事件域：消费者接入边界

本文件细化[下一代架构](java-next-generation-architecture-2026-10-22.md)的事件域，服务于 `event-policy` 与 `wave2-events` 的实际消费者接管。迁移目录、源码完成、旧生产者采样、Java 验证、生产路由切换及实机后态是分别验收的状态；本文件不把候选接口写成已切换。按用户最新要求停止新增迁移，首批固定九叶；`java/ck3-migration-staging/events/` 已实际编写的 mandatorybefore、interactionbefore、unhandledevent 是另外三项有限收尾范围，不再新开自然后继或扩大待构建闭包。

## 模块及依赖

`event-policy` 提供既有 mandatory selector、交互左侧 fallback 和已注册原版事件投影。`wave2-events` 在同一 JVM 内调用它与共享 `contracts`，不依赖服务宿主、原生连接、账本 writer 或测试 runner。Quarkus 宿主只在原有总提交权威内接入这些 consumer port，不为每个纯规则启动服务或 JVM。

| 组件 | 迁移的真实边界 | 接入前仍由原 owner 完成的工作 |
| --- | --- | --- |
| choiceplanning | 当前帧、原生 query、typed 优先级与 pending claim 的纯候选编排；复用 selector | SDK 历史输入投影、available typed 语义、已观察 UI 的磁盘原件复验、唯一 submit |
| uirecoveryidentity | 旧 stable source canonical JSON 与 SHA 指纹 | before/after/later/launch 原件身份与内容复验，registry 持久化 |
| mandatoryreceipt | 原 token ACK 与 exact original window 后态分开判断，组合 after body | 原 writer 的锁、写入一次、fsync、rename 与路径身份 |
| interactionregistry | 有来源绑定的交互登记投影与读取核对 | 当前 native 合法按钮、来源载荷核对与唯一 submit |
| interactionsourceblocks | 原交互源码块提取和效果目录 | 不授予 known、效果解释或动作权限 |
| interactionreceipt | 按响应来源解释 ACK、accept 参数与原 interaction 后态 | 原生读回与原 writer；无重试权限 |
| eventoutcome | scalar plan/evaluate/runner issue；消费既有已注册选项投影 | 同角色的独立后态、原 source/episode 绑定、实机效果验收 |
| occurrence | query identity 到 verified selection 的两遍归属、去重与次数 | 完整事件策略及其当前 native 输入，不以 ACK 增加次数 |
| sourcecatalog | 原事件 direct-child lexer 与实际 source index/hash/file/count 路径 | 当前安装载荷、build 与来源登记；不解释任意效果 |

生产类不导入兼容采样器。默认 JUnit 读取提交的完整旧生产者样本；显式采样器才在统一有界 Job 内调用旧 Python。Java 编译和差分通过后，仍须在原宿主路由里切换相应 consumer，保留本次实际 Java 调用、输入身份与回执，不能静默退回 Python 后称为 Java 验收。

## 一次选择的边界

当前 native 帧、Game/actor/episode、query ID、window ID/instance 及原始回执随候选保留。已有专用事件策略优先；普通角色通知继续使用专用左侧语义，左侧禁用时保存诊断。不能将 generic first-enabled selector 套到角色通知，以右侧 accept 代替被禁用的左侧拒绝。

候选经过原提交权威重验当前帧和合法 token，原 writer 先持久化 before，再由唯一提交者发起现有动作。after 将原响应 ACK、原窗口是否已推进和材料效果分开记录。结果未知时保留原 claim，不能因新 query、短历史输入或 JSON 重编码消失而重新发起动作。

`mandatoryreceipt` 处理原 native token 动作响应，其 `accepted` 是 native command ACK。交互 `Service.reply_pending_character_interaction` 会把 `accepted` 写成调用者的 accept 参数，合法 reject 的值为 false；`interactionreceipt` 用明确响应来源区分该含义。不能把这两种字段含义合并为共享的“成功”布尔。原 response SHA 和诊断必须保留。

稳定来源 key 只标识按原合同规范化的稳定字段。相同 key 不能证明当前 EXE/DLL、旧 evidence 原件仍可读取、原窗口消失、游戏日推进或效果已知。sourcecatalog 的 lexer 和 interaction source block scanner 也保留各自实际语义；名称相近不能作为统一实现后改变行为的理由。

## 首次生产接入的具体门槛

1. 统一构建消费有限九叶 freeze、实际 producer fixture 和跨 Java consumer 回归；缺资源、编译失败或差分失败均为真实 RED，不能跳过后计 PASS。
2. 宿主适配实际 SDK 输入。当前 choiceplanning wrapper 上限 64 KiB、history 上限 256 行；接入需要可证明保持相关历史的投影，至少保留最新 generic query、当前 episode 的原 submission claim 和同帧 typed context。不得截断未知 claim 以通过大小检查。无法满足边界时明确拒绝该调用，不能因此授予再提交。
3. `known_review_root/backend_sha256` 的旧文件复验、available typed event 完整语义以及唯一 writer 适配尚未随纯叶接管；这些路径须完成其真实闭包再分别切换。不能借 caller 传入的 known/qualified/GREEN 布尔代替资格检查。
4. 达到可运行条件后在原宿主实际使用 Java，保留真实失败与修复；不因担心报错长期停留在纯差分。Game、未知动作、保存接续和冻结 runtime 图仍按单一权威管理。

## 验收证据的机器范围

本工作包采样机器为 `machine_id: xenoamess-full-tower-eb9d2c1186`。每次实际采样、构建和实机回执分别记录观察时间、来源 SHA 与退出/Job 终态。旧 native fixture、历史 P09 与原版 source fixture 只证明其对应纯生产者行为，不外推为当前 build、游戏进度、30 年完成或秒/日改善。当前各叶状态以 `D:/codex-ck3-demos/2026-10-22-java-phase1/logs/*-SOURCE-FREEZE*.json`、对应 capture actual 和 M7 实际构建终态共同核对。
