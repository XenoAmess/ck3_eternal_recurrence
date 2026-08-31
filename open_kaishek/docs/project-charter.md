# open_kaishek 项目立项报告

## 1. 立项信息

| 项目项 | 内容 |
|---|---|
| 项目代号 | `open_kaishek` |
| 立项日期 | 2026-08-31 |
| 项目性质 | 开源、版本感知、可嵌入的 Paradox 脚本工具链与有限语义 Runtime |
| 强制技术栈 | Java/JVM + Quarkus |
| 首个产品 profile | CK3 1.19.0.6 |
| 首个业务 profile | `mod_zhongguo_style` 的 361 绩效机制 |
| 当前阶段 | 立项文档完成，尚未开始编码 |

## 2. 执行摘要

当前 CK3 mod 开发存在一个长期瓶颈：静态校验能够检查文本、生成器和部分模型，却不能真正执行生成后的 Paradox 脚本；而每次依赖 CK3 启动、进入存档、触发事件再观察结果，耗时高、批量状态组合覆盖率低，也不利于在 CI 中快速定位问题。

`open_kaishek` 将建设以下完整链路：

1. 读取原始脚本字节并生成逐字节可回放的 lossless CST。
2. 按游戏、版本、目录、加载顺序和作用域进行 schema-aware 验证。
3. 将已支持语义编译为严格、可审计的 IR。
4. 在有限世界快照上确定性执行 trigger、effect、script value、scripted call 和事件调度子集。
5. 输出完整 execution trace、读写集、事件队列和规范化状态差异。
6. 通过现有 CK3 MCP 在同一快照和同一场景上执行差分验收。
7. 仅把通过 exact-build 差分的语义登记为 certified；其他语义保持 unsupported。

项目将覆盖“解析、验证、执行以及半套仿 CK3 Runtime”，但不宣称实现完整 CK3，也不取消正式版本的真实游戏验收。

## 3. 问题陈述

### 3.1 当前缺口

- 现有校验器大多验证源码形状、键集合、生成器输出和 Python 侧模型，没有执行实际 `.txt` 产物。
- Paradox 脚本存在重复键、顺序语义、动态 scope、文本参数、目录特定 schema、reader 指令和引擎时序，普通配置文件解析器不足以承载。
- 大量关键错误只有游戏加载或特定事件路径才暴露，导致一次 CK3 启动只能验证少量状态。
- 自写业务模型可能与真实生成脚本分叉，形成“模型 GREEN、游戏 RED”。
- 开源生态已有优秀 parser、IDE analyzer 和 schema 数据，但没有可直接嵌入的 CK3 trigger/effect Runtime。

### 3.2 机会

master 基线中的 361 机制已经具有结构化 DomainSpec、typed operation、生成式运行时规范，以及部分 static/fixture-ready 的 MCP snapshot provider 和大量历史实机结论，适合作为严格 Runtime 的首个真实客户。专用 pre/post snapshot 与差分 live artifact 仍是 Phase 0/5 要闭合的合同，不能把现有 provider 文件或单元测试冒充实机差分已经完成。该机制既足够复杂，可以证明工具价值，又能把边界限制在本项目真实使用的语义，而不必先复制整个 CK3 世界。

## 4. 产品定义

`open_kaishek` 是：

- 一个保留源码顺序、重复键、注释、空白、引号、BOM、换行和源码位置的 Paradox lossless parser。
- 一个按游戏 profile 与目录上下文运行的 schema、引用、scope、参数和加载顺序验证器。
- 一个只接受白名单 IR、具有确定性时钟和随机带的脚本执行内核。
- 一个可由 synthetic snapshot 或 CK3 MCP snapshot 驱动的有限世界 Runtime。
- 一个能把 VM 与真实 CK3 前后状态进行规范化差分并维护认证账本的测试平台。
- 一个以 CLI 为首要自动化入口、以 Quarkus 服务为集成入口的 JVM 工具。

`open_kaishek` 不是：

- 完整 CK3、Clausewitz 或 Jomini 引擎重实现。
- 用假世界模型替代 CK3 实机的发布验收器。
- GUI layout、hit-test、modal、字体或 localization 最终渲染器。
- 完整地图、战争、继承、经济、AI、活动或宗教系统模拟器。
- 第一阶段就兼容所有 Paradox 游戏的通用平台。
- 遇到未知 trigger/effect 后“尽量跑完”的宽松解释器。

## 5. 核心目标

### G1：Lossless 语言前端

覆盖项目实际出现的 Paradox 文本语法，保持重复键和源码顺序，并支持 parse → emit 逐字节一致的回放模式。

### G2：版本与目录感知验证

以 CWT、原版日志、本地游戏文件和项目实证为输入，识别 trigger/effect/value/interface 域、scope 类型、引用、参数、覆盖与加载顺序问题。

### G3：严格语义执行器

只执行已经注册且具有明确合同的 opcode。执行结果必须包含状态、读集、写集、分支、调度、随机消费和诊断；未知或版本不匹配时立即失败。

### G4：半套仿 CK3 Runtime

在有限角色、头衔、组织、变量、资源、关系、日历和事件队列快照上，执行本项目所需的 CK3 脚本子集。原生能力通过显式 port 注入、MCP 调用或返回 unsupported，不伪造成功。

### G5：361 首个纵向闭环

执行 361 状态机、A/B/C 路线、权限、期限、收据、资源守恒、配额、HC、晋升槽、多周期和上司变更等可离线语义，并与 CK3 1.19.0.6 批量差分。首个切片明确指向 B2 的 014–017、069–081、358–359，以及 Workforce/endgame 的 AB 242–253、AC 254–265、AD 266–277、AL 355–356/360–361；“B2”和“Workforce”不是泛称或自动游玩 blocker 等级。

### G6：Quarkus 集成面

提供解析、验证、编译、执行、差分、profile 查询和认证查询能力；核心库在不启动 Quarkus 的情况下仍可独立测试和运行。

### G7：开源可复用

公开语法合同、profile API、诊断格式、执行 trace、差分协议和认证边界，使其他 mod 能复用 parser/validator，并按证据逐步扩展自己的 runtime profile。

## 6. “半套 CK3 Runtime”的正式边界

### 6.1 Runtime 内部执行

- typed scope 与 `ROOT`、`THIS`、`PREV`、saved scope 等已认证上下文切换。
- scope/global variable 的数值、布尔、字符串和对象引用子集。
- temporary event-target list 与 persistent variable list 的已认证子集。
- 比较、布尔组合、条件分支、script value 基础定点算术。
- set/change/remove/has variable 与显式白名单 list/ordered iterator。
- scripted effect、scripted trigger 和文本参数展开。
- D+n 延迟事件、有限 on_action、serial/deadline/stale guard。
- 显式 `DrawTape` 驱动的确定性随机。
- 361 机制的有限角色、组织、考核周期、案卷、配额与资源模型。

### 6.2 通过显式 port 处理

- CK3 原生金币、职位、modifier、opinion 等 effect。
- 原生人物关系和派生属性查询。
- 引擎内部 callback、不可离线重现的候选物化与原生随机。

port 只有三种合法结果：由测试快照注入明确结果、通过 MCP 调用真实 CK3、明确返回 `UNSUPPORTED_NATIVE_OPERATION`。

### 6.3 明确不执行

- GUI 最终实例化、布局、点击、modal、动画和 tooltip 预演。
- localization、字体与文本最终渲染。
- 完整 CK3 AI、地图、军队、战争、继承、经济、活动和 save serializer。
- 任意原版/DLC 事件全集。
- 未完成 exact-build 认证的 native trigger/effect。
- 项目现阶段明确暂缓的通用宗教域。

## 7. 关键架构原则

1. **核心与框架隔离**：Quarkus 不能进入 syntax、validator、IR 或 runtime kernel。
2. **源码保真优先**：CST 不能使用会吞掉重复键或重排行为的普通 `Map`。
3. **版本不可漂移**：每个 CK3 profile 绑定游戏版本、EXE SHA、配置哈希和认证清单。
4. **未知即失败**：unsupported 是正常结果，silent no-op 是缺陷。
5. **执行必须可解释**：每次运行必须能回答读了什么、写了什么、走了什么分支、调度了什么、消耗了哪些随机值。
6. **同源语义优先**：361 应逐步从同一 DomainSpec/typed operation 生成 CK3 脚本与 VM IR，减少双实现漂移。
7. **真实 CK3 是差分 oracle**：VM 只能声明“该语义在某 exact build 上已认证”，不能声明“等同于 CK3”。
8. **按实际收益扩展**：只有真实高频启动成本或可复现缺口才能推动新增大块语义域。

## 8. 首期交付物

首期不是一次性交付完整 Runtime，而是依次交付：

- byte-preserving CST、diagnostic、profile、IR、snapshot、trace 和 differential contract。
- 能逐字节回放天朝 mod 目标 corpus 的 parser。
- 能捕获一批仓库历史真实故障的 validator。
- 能执行 B2 送达/申诉/首段 PIP（014–017、069–081、358–359）与 Workforce/endgame（242–277、355–356、360–361）代表场景的 Runtime Kernel。
- CK3 1.19.0.6 与 361 profile。
- MCP 差分 runner 与 `certified-semantics` 账本。
- 独立 CLI 和 Quarkus 服务壳。
- 可公开的架构、贡献、版本支持和证据文档。

## 9. 成功标准

### 9.1 Parser/validator

- `mod_zhongguo_style` 目标 `.txt`、`.gui` corpus 100% 可解析。
- lossless 模式 parse → emit 逐字节一致；任何允许的正规化必须另设显式模式。
- 重复键、顺序、BOM、CRLF/LF、注释、引号和 malformed recovery 均有 corpus 与 property test。
- validator 能稳定抓住一组来自本仓库历史实机问题的 mutation，而不依赖 CK3 启动。

### 9.2 Runtime

- 每个支持 opcode 有明确输入、scope、状态转换、错误和 trace 合同。
- 未支持 opcode、错误版本、缺失字段和不合法 scope 均 fail-closed。
- 361 试点覆盖状态迁移、资源守恒、权限、期限、幂等和跨周期组合。
- 同一快照和 draw tape 重放得到确定性相同结果。

### 9.3 差分与业务收益

- 上述 B2 与 Workforce/endgame 精确 ID 范围形成首个 CK3 MCP 前后快照差分闭环。
- 认证场景覆盖正常、false trigger、缺失 scope、重复执行、stale、边界值和相邻 opcode 组合。
- 项目日常语义回归中至少一半不再需要启动 CK3；该比例必须用实际 runner 记录验证，而非估算宣称。
- 正式发版仍完成真实 loader、GUI、localization、native effect、存读档和完整批量实机验收。

## 10. 主要风险与应对

| 风险 | 应对 |
|---|---|
| Runtime 自洽但与 CK3 不等价 | exact-build MCP 差分、认证账本、失配立即撤销认证 |
| CWT 配置陈旧或不完整 | 只作 schema 种子；以本地 script docs、日志和实机结论校正 |
| IntelliJ PSI 等上游架构难以嵌入 | 借鉴语法与测试，不把完整插件作为核心依赖 |
| scope、事件时序和随机语义膨胀 | 白名单、有限世界、显式 DrawTape、按收益扩展 |
| 361 CK3 脚本与 VM 形成双实现 | 逐步建立共享 DomainSpec/IR 生成路径 |
| Quarkus 污染核心或拖慢测试 | 核心纯 Java；CLI 与单元测试不启动 Quarkus |
| CK3 升级导致旧结论漂移 | 新版本新 profile；EXE SHA 变化使旧认证整体失效 |
| 外部代码许可证不兼容 | 采用前逐项审核；初期只研究，不复制源码 |

## 11. 开源与治理

- 项目计划采用宽松开源许可证；Phase 0 在复制任何第三方代码前正式决定并提交 `LICENSE`。当前优先候选为 Apache-2.0，最终选择需兼顾本仓库归属与第三方 MIT 代码的 attribution。
- 所有外部输入必须记录仓库 URL、许可证、固定 commit、用途和是否实际复制。
- 语义支持声明必须区分 `research`、`parsed`、`validated`、`runtime-fixture`、`differential-certified` 和 `product-live`。
- 对 CK3 专有文件只记录哈希、生成规则和测试结果；不得把游戏本体或未获授权资源发布进开源仓库。
- 参考仓库负责提供知识与测试思路，不自动获得架构决定权。

## 12. 止损条件

满足下列任一情况时，停止扩建 Runtime 语义层，但保留 parser/validator 成果：

1. 支持一个常见 opcode 必须复制大块 CK3 原生世界、GUI 或 AI。
2. 必要状态无法通过 MCP 或稳定 fixture 观测，差分只能比较 ACK/debug marker。
3. 同一语义连续三轮无法解释差分，且缺口来自不可观测原生行为。
4. 只有猜默认值、放宽检查或 silent no-op 才能跑完脚本。
5. 361 试点后仍无法覆盖大多数目标 typed-operation 普通路径。
6. 连续两个迭代中维护双实现的成本高于节省的 CK3 启动与定位成本。
7. Runtime GREEN、CK3 在同一已认证输入上 RED，且系统无法立即撤销相关认证。

## 13. 立项决定

项目正式批准进入文档与合同设计阶段。下一步只能启动路线图 Phase 0；本次立项不授权直接开始源码实现，也不改变天朝二期、G2 或现有 MCP 工作的优先级。
