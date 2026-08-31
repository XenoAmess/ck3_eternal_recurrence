# open_kaishek 目标架构

## 1. 总体设计

目标数据链如下：

原始字节 → lossless CST → profile-aware validation → strict IR → finite world runtime → execution trace/state delta → CK3 MCP differential certification。

其中 Quarkus 位于最外层，只提供集成入口。核心数据结构、编译器和执行器不能依赖 CDI、HTTP、数据库或 Quarkus 启动生命周期。

## 2. 计划模块

以下是未来实现的逻辑模块，不代表本次已经创建工程或源码：

| 逻辑模块 | 职责 | 框架约束 |
|---|---|---|
| `kaishek-syntax` | lexer、lossless CST、source span、错误恢复、原样回放 | 纯 Java |
| `kaishek-profile-api` | 游戏版本、目录 schema、scope 类型、opcode 与加载规则扩展点 | 纯 Java |
| `kaishek-validator` | schema、引用、scope、参数、覆盖、加载顺序诊断 | 纯 Java |
| `kaishek-ir` | 将已支持脚本降级为严格、可序列化、可审计的 IR | 纯 Java |
| `kaishek-runtime` | 有限世界、执行上下文、事件队列、随机带、trace、读写集 | 纯 Java |
| `kaishek-diff-contract` | snapshot、scenario、delta、fingerprint 与认证格式 | 纯 Java |
| `kaishek-ck3-11906-profile` | CK3 1.19.0.6 的目录、scope、opcode 与版本绑定 | 纯 Java |
| `kaishek-zg361-profile` | 361 DomainSpec、typed operation 与业务断言 | 纯 Java |
| `kaishek-cli` | CI、本地批处理、corpus 和差分任务入口 | 纯 Java，优先入口 |
| `kaishek-service-quarkus` | REST、配置、依赖装配、缓存、MCP orchestration | Quarkus |

模块名在 Phase 0 可以调整，但“核心纯 Java、Quarkus 外壳”的依赖方向不可反转。

## 3. Syntax 层

### 3.1 必须保留的信息

- 文件原始编码判定、UTF-8 BOM、CRLF/LF。
- 所有空白、注释、引号和转义形式。
- 重复键、裸值、成员原始顺序和源码位置。
- `= != < <= > >= ?=` 等分隔/比较符。
- `{}` block、裸列表和混合成员。
- `@variable`、scripted variable reference、`$PARAM$` 与默认参数。
- conditional block、inline conditional、inline math。
- `var:`、`scope:`、`flag:`、点链及 reader 指令。
- malformed token 与恢复节点，禁止把错误输入悄悄修正成另一棵树。

### 3.2 双表示

- CST 是源码真相，服务于回放、诊断、重构和精确 diff。
- Typed AST/IR 是语义真相，只容纳 profile 已识别的构造。
- CST 到 IR 的降级可能失败；失败必须携带 source span 和 unsupported 原因。
- 不允许先转换成普通 JSON/Map 再尝试恢复顺序和重复键。

## 4. Profile 与 Validator 层

profile 必须绑定：

- 游戏及版本标识。
- exact build fingerprint，包括 EXE SHA 和必要原生资产哈希。
- 目录 schema 与文件加载规则。
- scope 类型、scope link 和合法上下文。
- trigger/effect/script value/interface trigger 的注册与签名。
- scripted call 参数合同。
- overwrite/merge/load-order 规则。
- certified semantics 清单。

Validator 首批覆盖本项目实际使用目录：events、on_action、scripted effects/triggers/values、decisions、interactions、activities、scripted GUI、customizable localization、GUI registration 和 localization 引用。

## 5. Strict IR

IR 不是“解析后的任意 key/value 树”，而是执行器的白名单指令集合。每个 IR 节点必须具有：

- 稳定 opcode ID 与 profile 版本。
- 输入类型、scope 要求和参数合同。
- source span 与原始 CST 回链。
- 可见读集与可能写集描述。
- 确定性、随机性或 native port 分类。
- unsupported 与错误语义。

未经 profile 注册的脚本节点不能以通用动态调用的方式进入 Runtime。

## 6. Runtime Kernel

### 6.1 有限世界状态

首期世界模型只覆盖 361 需要的对象与字段：

- Character：稳定 ID、玩家/AI、存活、爵位层级、政府、直属关系及有限属性。
- Title/Organization：稳定 ID、层级、持有者、上司链及组织账本。
- Performance domain：owner、subject、cycle、case、stage、route、grade、receipt、deadline。
- Resources：个人金币、国库、HC、配额、晋升槽、债务与预留。
- Variables：scope/global 的 typed value、对象引用和有限列表。
- Time：当前日期、cycle、D+n deadline 与单调 revision。
- Events：已认证 hidden-event/on_action 子集的队列和上下文。

不为尚未执行的 CK3 系统预建完整对象模型。

### 6.2 执行上下文

上下文至少包含：

- `ROOT`、`THIS`、`PREV` 和已认证的其他 scope 槽。
- saved scope/value 与参数帧。
- 当前 profile、exact build fingerprint 和 feature flags。
- deterministic clock、draw tape 与事件队列。
- call stack、source span、read set、write set 和 trace sink。

### 6.3 事务与时序

- 每次执行产生候选 write-set，再按已认证的提交边界应用。
- delayed event 与 on_action 不能按普通函数调用擅自串行化；只实现差分证明过的有限调度模型。
- serial、nonce、cycle、case 和 revision 是一等 stale guard。
- 重复执行必须显式得到 replay/idempotent/conflict 结果，而非依赖偶然状态。

### 6.4 随机

- Runtime 不调用隐式系统随机数。
- 所有随机消费来自可记录的 `DrawTape`。
- trace 记录候选集合、权重、消费位置和选择结果。
- 未认证的 CK3 候选物化顺序通过 native port 或 unsupported 处理。

## 7. Native Port

Native port 是 Runtime 与 CK3 专有语义之间唯一通道。每个 port 都必须声明：

- 输入和返回类型。
- 是否纯查询、是否产生副作用。
- 支持 synthetic fixture、MCP live 或两者。
- exact build 与能力 flag。
- timeout、stale、unavailable 和 state-changed 结果。
- 可比较的规范化 delta。

禁止用默认值替代不可观测结果，也禁止把 command ACK 当成状态已经发生。

## 8. 361 业务 profile

361 profile 应优先消费 master 基线中已有的 DomainSpec、runtime spec 和 typed operation registry，而不是重新从大体量生成文本猜业务含义；但它仍必须把**实际生成 `.txt`** 走完 parser → validator → IR → VM，不能只执行从 DomainSpec 旁路生成的第二份 IR。长期目标是：

- 一份业务 schema 生成 CK3 脚本与 VM IR。
- 一份权限矩阵同时驱动静态验证和 Runtime 断言。
- 一份资源/收据合同同时驱动 CK3 MCP snapshot 与 VM state delta。
- 每个机制 ID 都能回链其脚本位置、IR、测试场景和 live artifact。

首个纵向切片定义为：

- B2 送达、申诉与首段 PIP：014–017、069–081、358–359。
- Workforce/endgame：AB 242–253、AC 254–265、AD 266–277、AL 355–356/360–361。

它们同时具备复杂状态、资源/期限语义，以及 `query-zhongguo-ai-owned-case-snapshot-v1`、`query-zhongguo-workforce-collective-snapshot-v1` 等专用 MCP provider 的 static/fixture 基础。provider 的真实 paused artifact 和能覆盖全部前后 delta 的字段仍须在 Phase 5 验收，缺字段时继续补观测口，不以 ACK 或默认值代替。

## 9. Quarkus 服务边界

计划提供的能力类别：

- parse：返回 CST、诊断和 round-trip 元数据。
- validate：返回按 profile 分类的错误、警告和引用结果。
- compile：返回 strict IR 或精确 unsupported 诊断。
- execute：在调用方提供的 world snapshot 上执行并返回 trace/delta。
- diff：编排 VM 与 CK3 MCP 场景差分。
- profiles：查询支持的游戏、版本、目录与能力。
- certified semantics：查询 exact-build 认证清单和证据索引。

初期不引入数据库；可使用内容 SHA 驱动的内存/磁盘缓存。MCP、named pipe、CK3 进程和 Windows 专有逻辑都放在适配器层。GraalVM native image 不是首期目标。

## 10. 可观测性与可复现性

每次执行输出至少包括：

- 输入脚本、profile、配置、world snapshot 和 draw tape 的哈希。
- 调用栈、分支、scope 转换和每条 IR 的结果。
- 读集、写集、调度事件和 native port 调用。
- 最终状态 delta、unsupported 列表和诊断。
- 执行器版本与 certified-semantics 版本。

失败现场应可作为 fixture 保存并完全重放。

## 11. 版本策略

- `ck3-1.19.0.6` 是独立 profile，不使用“兼容最新版”表述；当前基线 EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- CK3 升级时创建或派生新 profile，先重新生成 schema/日志差异，再重跑差分认证。
- EXE SHA、DLC/playset、mod tree 或关键配置哈希变化时，旧认证不得自动继承。
- Parser 的通用语法版本与 CK3 profile 版本分离，避免游戏升级迫使核心无意义改版。
