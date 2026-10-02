# CK3 1.20.0.3 适配计划

日期：2026-10-03。执行参考：仓库自动升级建筑产品的 [维护记录](../../docs/auto-upgrade-buildings-maintenance.md)、[来源冻结](../../docs/auto-upgrade-buildings-upstream.md)、[验收计划](../../docs/auto-upgrade-buildings-test-plan.md)。本产品独立验收，不能借用该产品的 GREEN。

| 步骤 | 当前状态 | 交付物 |
| --- | --- | --- |
| 公开功能及风险分析 | 完成页面层 | `functional-analysis.md` |
| 原始文件取得／来源冻结 | 完成 | 外置不可变 8 文件原始树、manifest、tree hash |
| 运行合同审阅 | 完成源码层 | 三档 CB、参与方与结算的源码分析 |
| 最小版本适配 | 完成候选 | 1.0.0 源码、变更记录与公开 ID 保留 |
| 离线解析／L0／可复现构建 | 完整16文件通过 | 正式九语format-certified、双构建manifest／ZIP一致；未tag发布 |
| 隔离 CK3 实机 | 未运行 | source／runtime／fixture hash 绑定报告 |
| 分别发布与公开回读 | 未运行 | 新物品 ID、缓存验证、Change Notes 与 changelog |

## 取得来源后的施工顺序

1. 独立列出所有 CB key、scripted effect／trigger、event、flag、变量、文件覆盖和本地化；对照冻结 build 原版 schema 与宗教／法理战争实现。
2. 复用现有 Clausewitz 结构 parser 做基础 parse；检查 `open_kaishek` 的覆盖子集并先运行支持项。不支持的引擎战争操作明确记录，不能把 parser GREEN 当成运行 GREEN。
3. 保留公开存档 ID；只给内部无公开合同 helper 增加本产品命名空间。禁止为统一风格无故改玩家现有政策、成本或地域范围。
4. 对真实过时 token、作用域错误、战前描述和参战者收集实施最小修复；尽量使用 exact-build 原版的战争和头衔交接路径，不把帝国征服简化成未经授权的普通单领主战争。
5. 新增入口必须双重保护：`ai = no` 与攻击者资格 `is_ai = no`；胜利 helper 绑定当前 CB 的战争，不能寻找攻击者任意战争。
6. 运行源码只用 UTF-8 BOM；descriptor 无 BOM、无路径和任何 remote ID。日常只创作简中／英文；其他语言如需保持完整结构则注明英文占位，正式发布语言评审按仓库要求另行完成。
7. 明确 release allowlist；产品 docs／tools／fixture 不进 staging。依照现有 manifest／ZIP 机制复用通用实现，新增本产品构建入口。
8. 按测试计划执行正负矩阵；每个失败 attempt 独立保留，不改写成 GREEN。游戏加载输入改变才重启，纯 runner 修复优先保留同一进程热重试。

## 接受标准

三档借口在对应威望等级解锁，成本一致；AI 无进攻入口；实际参战者集合和目标法理集合可读回；胜利、白和、战败及失效路径可结束；目标外土地保持产品承诺；并发战争不留下无法结束状态。全部结果绑定 CK3 1.20.0.3 exact build。

自动战斗能否兼容普通战争路径须用原生状态及实机验证决定；未证明前保留明确限制，不能只从 `is_great_holy_war` 开关推断修复。

## 当前施工状态

候选实现见 [implementation.md](implementation.md)。已生成外置 9 战争／72 断言夹具并通过结构 parser；尚未执行 CK3。原版 CB 的 Python parser 通过；Open Kaishek 工具探测与受支持子集由主执行者统一协调，不能冒充已完成。
