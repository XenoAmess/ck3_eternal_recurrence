# open_kaishek 参考仓库与复用目标

## 1. 使用原则

本清单是研究与选型账本，不代表已经引入依赖或复制代码。实施前必须对每个候选：

1. 固定 commit，不跟随可变 `master/main` 直接构建。
2. 记录许可证、NOTICE/attribution 要求和传递依赖。
3. 区分“借鉴设计”“导入数据”“复制/改写代码”“测试对照”四种用途。
4. 用本地 CK3 exact build 与目标 corpus 复核，不把任何上游当作执行语义权威。
5. 外部仓库更新必须经过 diff 与重新认证，不能自动刷新 golden。

## 2. 核心参考

| 仓库 | 计划目标 | 明确边界 | 初始评估基线 |
|---|---|---|---|
| [Paradox Chronicle / Paradox-Language-Support](https://github.com/DragonKnightOfBreeze/Paradox-Language-Support) | 研究 JFlex/BNF 语法覆盖、PSI 静态语义、scope/reference/index、inline script 与 parser corpus；必要时作为隔离的 IntelliJ fixture oracle | 不把完整 IntelliJ 插件嵌入核心；不把 inline-math evaluator 误当 trigger/effect Runtime；IntelliJ 平台与插件依赖另审 | MIT；`0883db37af7f43b8013a9706451bd947f392af50`，v3.0.1 |
| [DragonKnightOfBreeze/cwtools-ck3-config](https://github.com/DragonKnightOfBreeze/cwtools-ck3-config) | CK3 CWT schema、trigger/effect/scope/link/value 与目录规则的种子数据 | 配置存在 TODO/placeholder 且不是 CK3 1.19.0.6 oracle；必须与本地 logs/script docs 校正；游戏生成数据另记 provenance | MIT；`c9ed4e52d9e417941510c41b4cf9419239911626` |
| [cwtools/cwtools](https://github.com/cwtools/cwtools) | 研究 CWT 模型、schema 验证、错误报告、CLI/corpus 组织和 Paradox 文件处理经验；可作为隔离的外部静态 oracle | .NET/F# 体系，不作为 JVM 核心依赖；它是 parser/validator，不提供 CK3 世界执行语义 | MIT；`b377453dee803f9258be92cfc49896d09039702d` |
| [cwtools/cwtools-ck3-config](https://github.com/cwtools/cwtools-ck3-config) | 与 DragonKnight fork 做来源、差异和历史规则对照 | 历史快照明显早于当前 CK3；不能直接替换 exact-build profile，也不能称作官方执行语义 | MIT；`27db56f995af6b73baebae43e04d044f1a0a0bbe` |
| [iTitus/PDXTools](https://github.com/iTitus/PDXTools) | 研究 Java/JPMS 的 parser 对象模型、模块边界和有限 trigger framework 外形，提取反例测试 | 解释层面向 Stellaris，effects 与 CK3 world model 不完整，inline math 等仍有缺口；不能继承其执行正确性声明 | MIT；`a56c12a873b0e06fb0f99030f9fd3f1ccb7ab7be` |
| [rakaly/jomini](https://github.com/rakaly/jomini) | 高性能 Rust parser/deserializer/writer、文本/二进制输入和 benchmark 的差分参考 | 不提供 schema、scope 或 trigger/effect Runtime；二进制解析还依赖游戏 token 数据；不是 JVM 依赖 | MIT；`887d209d07cb4dba8aa15cb176957585089b108d`，crate 0.35.0 |
| [nickbabcock/jomini](https://github.com/nickbabcock/jomini) | 研究浏览器/Node/Wasm 字节解析、流式读取、重复键保存策略和 save/game corpus | 与 Rust crate 分开记名；普通对象/JSON 输出不等同于 lossless CST，不作为 JVM Runtime | MIT；实现期固定 |
| [pdx-tools/babblewitz](https://github.com/pdx-tools/babblewitz) | 复用 parser conformance/performance harness 思路与合成 corpus 协议 | 项目明确不标准化执行语义；通过 corpus 只证明语法样例可解析 | MIT；`40ceec5683a194dc7ea84f576fdc8a7f63301c59` |
| [amtep/tiger](https://github.com/amtep/tiger) | 作为隔离进程的 CK3 静态诊断差分 oracle，收集引用、loc、scope、history 类 fixture | Tiger clean 不等于 CK3 能加载或 Runtime 正确；许可证策略确认前不链接、不复制实现 | GPL-3.0-or-later；`9e3d3b25c7524cdcc86d5f4190f3f8cffbc4d630`，v1.19.0 |
| [quarkusio/quarkus](https://github.com/quarkusio/quarkus) | Quarkus 服务、配置、依赖装配、命令模式、测试和可观测性参考 | Quarkus 只存在于 service adapter；parser/runtime 单测不得依赖 Quarkus boot | 实现期选择受支持版本并固定 |

## 3. Java/JVM 语言工具候选

| 仓库 | 计划目标 | 决策点 |
|---|---|---|
| [JFlex](https://github.com/jflex-de/jflex) | 研究状态化 lexer、Unicode、错误 token 与 Chronicle lexer 的可移植部分 | 与 ANTLR/manual parser 做 Phase 0 小 corpus spike 后决定 |
| [antlr/antlr4](https://github.com/antlr/antlr4) | 对比 grammar 可维护性、错误恢复、visitor 与测试工具链 | 必须证明能自然保留 trivia、重复键和原始 token；否则不采用 |
| [JetBrains/Grammar-Kit](https://github.com/JetBrains/Grammar-Kit) | 理解 Chronicle BNF 的生成语义和测试 corpus | 绑定 IntelliJ PSI，不作为独立 Runtime 默认依赖 |
| [mmyers/eug](https://github.com/mmyers/eug) | 调查早期 Java Clausewitz parser/editor 的数据模型和历史兼容经验 | 陈旧项目，只作考古；采用任何代码前先确认许可证与维护状态 |
| [rikbrown/klausewitz-parser](https://github.com/rikbrown/klausewitz-parser) | Kotlin/ANTLR prototype 的 grammar 与 JVM 项目形状参考 | 主要面向 Stellaris 且自称 prototype；只列观察名单，不作为 parser 基座 |

## 4. 测试与规范参考

| 仓库 | 计划目标 | 边界 |
|---|---|---|
| [jqwik-team/jqwik](https://github.com/jqwik-team/jqwik) | JVM property-based parser、状态机、资源守恒和 mutation 测试 | 仅在 Phase 0 依赖评审后选择；不预先绑定 |
| [FasterXML/jackson](https://github.com/FasterXML/jackson) | snapshot、trace、IR 和 differential contract 的 JSON 序列化参考 | JSON 不是 CST；不得用普通对象映射替代 lossless parser |
| [networknt/json-schema-validator](https://github.com/networknt/json-schema-validator) | 对公开 contract 做 JSON Schema 验证的候选实现 | 只验证交换格式，不承担 Paradox 语义验证 |

## 5. 本仓库内的权威输入

这些输入比任何外部仓库更接近首个产品目标：

| 本地来源 | 用途 |
|---|---|
| `mod_zhongguo_style/` | 第一目标 corpus、生成脚本、361 DomainSpec、typed operation 和历史测试 |
| `mod_zhongguo_style/docs/` | 机制、状态、权限、资源、期限和实机边界 |
| `docs/grammar/` | 已实证 Paradox/CK3 语法与引擎陷阱 |
| `docs/testing-workflow.md` | CK3 runner、批量验收、日志与现场恢复规则 |
| `docs/ck3-native-ai/` | exact-build ABI、MCP capability、native 语义和 live artifact |
| `ck3_autonomous_player/` | MCP provider、snapshot、schema、checkpoint 与 OODA 集成入口 |
| 本地 CK3 1.19.0.6 安装 | 原版脚本、script docs/logs 和真实执行 oracle；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；不进入开源分发 |

## 6. 各仓库的目标优先级

### P0：立项后立即冻结

- Paradox Chronicle。
- 两套 CK3 CWT config。
- CWTools。
- PDXTools。
- 两个 Jomini 项目。
- Babblewitz。
- Quarkus。

### P1：Parser/validator 选型时比较

- JFlex。
- ANTLR4。
- Grammar-Kit。
- Tiger。
- EUG。

### P2：进入实现后按需要决定

- property testing 与 JSON Schema 候选。
- 性能 benchmark、fuzz 和 corpus 管理工具。
- 其他 Paradox 游戏 profile。

## 7. 禁止的复用方式

- 直接 fork Chronicle 并把 IntelliJ PSI 当作 Runtime AST。
- 直接使用可变 CWT `master` 作为 CI 或执行语义输入。
- 把 PDXTools 的 Stellaris trigger 语义改名为 CK3 语义。
- 把 Jomini 的普通 JS/JSON object model 当作 lossless CST。
- 根据 CWT 的合法 shape 推断 effect 的世界状态变化。
- 未经许可证核对直接复制任一仓库源码、测试数据或文档。
- 以第三方工具静态通过替代 CK3 exact-build 差分或正式发版实机。
- 混淆 `iTitus/PDXTools`、`pdx-tools/pdx-tools` 或两个不同的 Jomini 仓库。

## 8. 参考账本维护字段

Phase 0 创建 `THIRD_PARTY_LOCK`，并为每个实际采用的仓库补齐：URL、固定 commit/tag、获取日期、SPDX、许可证哈希、目标 CK3 build、用途分类、采用方式（代码/数据/外部进程/仅参考）、内容哈希、复制文件清单、本地 patch、上游链接、对应测试、更新策略和最后复核日期。

## 9. 第三方结果的证据上限

- parser corpus 只能提供语法一致性证据。
- Chronicle/CWT/Tiger/CWTools 只能提供静态语义与诊断证据。
- `open_kaishek` strict VM 只能提供项目白名单 Runtime 证据。
- 只有 exact-build CK3 MCP 差分和真实产品路径才能提供 CK3 实机证据。

任何上游工具不得越级为下一层背书。
