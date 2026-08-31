# open_kaishek 阶段计划

## 1. 计划原则

- 先交付独立有价值的 parser/validator，再扩建 Runtime。
- 每一阶段必须有可执行退出门，不能靠文档宣称完成。
- Runtime 只按实际脚本与历史故障扩展，不以“覆盖整个 CK3”为目标。
- CK3 启动昂贵，因此差分验收按场景批量执行；开发期先用离线穷举筛掉普通错误。
- 正式实现开始后，每个阶段都要记录固定依赖版本、corpus 哈希、测试结果和遗留 unsupported。

## 2. Phase 0：合同冻结与工程决策

### 交付

- lossless CST schema。
- diagnostic 与 source span schema。
- profile API、opcode registry 和 unsupported 分类。
- strict IR schema。
- world snapshot、execution trace、state delta 和 differential scenario schema。
- exact-build fingerprint 与 certified-semantics 格式。
- 构建工具、Java 版本、Quarkus 版本、测试框架和正式开源许可证 ADR。
- 第一个目标 corpus 清单和哈希生成规则。

### 退出门

- 所有合同经过实例评审，能表达重复键、混合 block、scope、参数、事件、随机和 native port。
- 外部依赖均有许可证、固定版本和采用理由，并已写入 `THIRD_PARTY_LOCK`。
- 核心模块依赖方向证明不需要 Quarkus boot。

## 3. Phase 1：Lossless Parser

### 交付

- 原始字节输入、lexer、CST、malformed recovery 和原样 emitter。
- Paradox 基础属性、比较符、block、裸列表、注释、字符串和数字。
- scripted variable、参数、conditional block、inline conditional 和 inline math。
- CK3 项目出现的 scope chain 与 reader 指令。
- corpus test、round-trip test、property test 和 fuzz seed。

### 退出门

- 天朝 mod 目标 `.txt/.gui` corpus 100% 可解析。
- lossless 模式逐字节 round-trip。
- 重复键和源码顺序没有通过 `Map` 丢失。
- malformed 输入能稳定报告位置且不会崩溃或悄悄改写。

## 4. Phase 2：Schema-aware Validator

### 交付

- CWT/schema 导入与规范化层。
- 游戏/版本/目录/加载顺序 profile。
- 定义、引用、参数、scope 与 trigger/effect/value/interface 域验证。
- 首批目录支持：events、on_action、scripted effect/trigger/value、decision、interaction、activity、scripted GUI、custom localization。
- 来自本仓库历史故障的 mutation corpus。

### 首批必须捕获的历史类别

- effect iterator 被放入 trigger 域。
- trigger RHS 使用引擎不接受的算术 block。
- scripted effect 缺参数。
- `ordered_*` 默认数量误判。
- temporary event-target list 与 persistent variable list 混淆。
- `ROOT/THIS` 与 iterator scope 误判。
- on_action 重复 effect 或同名覆盖误解。
- producer/reset 缺失和伪 consumer。
- interface trigger 被放进游戏状态脚本。
- GUI/custom localization 读取被误算成状态 consumer。

### 退出门

- mutation corpus 的目标错误均被稳定捕获。
- 对目标项目无无法解释的大规模 false positive。
- parser/validator 已能独立进入 CI，即使 Runtime 后续止损仍有产品价值。

## 5. Phase 3：Strict Runtime Kernel

### 交付

- typed scope、参数帧、变量、对象引用、有限列表和执行上下文。
- 比较、布尔组合、if/else、基础定点 script value。
- set/change/remove/has variable 与保存 scope/value。
- 白名单 iterator、scripted effect/trigger 调用。
- deterministic clock、DrawTape、事件队列、trace、read/write set。
- stale、幂等、冲突和 unsupported 结果。
- synthetic world fixture 与 property/state-machine tests。

### 退出门

- 未注册 opcode 必然失败，不能 silent no-op。
- 同输入、同 profile、同 draw tape 得到相同 trace 和 delta。
- 资源不能凭空产生或消失，除非 opcode 合同明确声明 source/sink。
- 事件与变量时序具有明确、可测试的提交边界。

## 6. Phase 4：CK3 1.19.0.6 与 361 Profile

### 交付

- exact-build profile、目录 schema、scope 与首批 opcode。
- 从 361 DomainSpec/typed operation 到 IR 的映射。
- owner/subject/cycle/case identity 与权限矩阵。
- A/B/C 路线、资源、HC、配额、晋升槽、债务、期限、收据与多周期模型。
- 首个纵向切片：B2 送达/申诉/首段 PIP（014–017、069–081、358–359）与 Workforce/endgame（242–277、355–356、360–361）。

### 退出门

- 代表性链路必须执行“实际生成 `.txt` → parser → validator → IR → VM”；同一 DomainSpec 生成的规范化 IR 只作补充对照，不能旁路产品脚本。
- 关键状态图、资源守恒、幂等、ACL 和 stale mutation 均被离线测试抓住。
- 不通过手写第二套宽松业务逻辑制造假 GREEN。

## 7. Phase 5：CK3 MCP 差分认证

### 交付

- canonical pre/post snapshot、scenario 和 normalized delta。
- VM runner、CK3 MCP runner、checkpoint 恢复和批处理编排。
- 每个 opcode/组合的认证矩阵与 live artifact 索引。
- `certified-semantics` 账本及自动失效规则。

### 退出门

- 上述精确 B2 与 Workforce/endgame ID 范围取得真实 paused CK3 artifact。
- 正常、false trigger、缺失 scope、重复执行、stale、边界值和主要组合路径均完成差分。
- mismatch 会让对应语义保持 unsupported，而不是刷新 golden 掩盖。
- 能证明实际减少重复 CK3 启动或显著提高一次启动的批量覆盖。

## 8. Phase 6：CLI、Quarkus 与开源发布

### 交付

- 无 Quarkus 启动依赖的 CLI。
- Quarkus parse/validate/compile/execute/diff/profile/certification 服务。
- 内容寻址缓存、请求限额和可重放 artifact。
- 用户指南、profile 开发指南、贡献指南和版本支持矩阵。
- 可复现构建、SBOM、许可证/NOTICE 与首个开源 release。

### 退出门

- CLI 与核心测试不启动 Quarkus。
- 服务结果与直接核心调用一致。
- 发布包不含 CK3 专有文件、用户存档或未授权资源。
- 文档准确区分静态支持、fixture 执行、差分认证和 product-live。

## 9. Phase 7：按收益扩展

只有以下证据可以推动新增语义：

- 高频 CK3 启动成本集中在尚未支持的 opcode/组合。
- 已发生真实 RED，现有 parser/validator/runtime 无法捕获。
- 新 mod profile 提供明确客户、corpus、验收和维护者。

地图、战争、完整 AI、GUI、存档序列化及大规模原版事件默认不进入计划。

## 10. 里程碑总表

| 里程碑 | 可见结果 | 是否需要 CK3 |
|---|---|---|
| M0 | 合同、版本和许可证冻结 | 否 |
| M1 | 项目 corpus 逐字节 round-trip | 否 |
| M2 | 历史真实故障离线可捕获 | 否 |
| M3 | strict runtime 执行 synthetic 361 场景 | 否 |
| M4 | 精确 B2 + Workforce/endgame ID 范围离线闭环 | 否 |
| M5 | exact-build MCP 差分认证 | 是，批量 |
| M6 | CLI + Quarkus 首个开源版本 | 发布前需要 |

## 11. 首批待办清单

在用户授权开始实现后，严格按下列顺序启动：

1. 决定许可证和依赖治理。
2. 固定 JDK、Quarkus 和构建工具版本。
3. 冻结 Chronicle/CWT/PDXTools/Jomini 等参考 commit。
4. 统计目标 corpus 的语法构造和 opcode 使用频率。
5. 起草 CST、diagnostic、profile 和 differential JSON schema。
6. 选择 parser 技术路线并用同一小 corpus 做对比 spike。
7. 通过 M0 评审后才创建源码与构建工程。

## 12. 计划外事项

本立项阶段不包含：源码实现、Quarkus 初始化、依赖下载、第三方代码移植、CK3 启动、MCP 实机差分、CI workflow 或开源平台发布。
