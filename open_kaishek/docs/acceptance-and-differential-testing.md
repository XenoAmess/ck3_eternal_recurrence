# open_kaishek 验收与 CK3 MCP 差分策略

## 1. 验收原则

`open_kaishek` 的可信度不能来自“测试很多”，而必须来自不同证据层之间的清晰边界。Parser 正确不代表 schema 正确，schema 正确不代表执行语义正确，VM 与自身 golden 一致更不代表它等同于 CK3。

## 2. 证据等级

| 等级 | 含义 | 可以声明 | 不可以声明 |
|---|---|---|---|
| `parsed` | corpus 可生成 CST | 语法被接受并可回放 | CK3 会加载、语义正确 |
| `validated` | profile/schema 检查通过 | 静态结构与已知规则一致 | effect 会产生预期结果 |
| `runtime-fixture` | synthetic snapshot 上执行通过 | Runtime 合同内部一致 | 与 CK3 等价 |
| `differential-certified` | exact build 同场景前后 delta 一致 | 指定语义组合在指定构建上已认证 | 其他版本、其他组合也正确 |
| `product-live` | 真实 CK3 产品路径通过 | 对应实机路径已验证 | 整个 Runtime 可替代 CK3 |

## 3. Parser 验收

- byte-for-byte round-trip corpus。
- 注释、空白、BOM、换行、引号与转义专项测试。
- 重复键、混合 block 和原始成员顺序专项测试。
- malformed/unclosed 输入的稳定诊断与恢复测试。
- property-based token sequence 与结构 mutation。
- 目标 CK3/mod corpus 的全量 parse；原版 corpus 只引用本地路径和哈希，不进入开源发布包。

## 4. Validator 验收

- 每条规则至少包含正例、负例、边界例和错误 scope 例。
- CWT 导入前后做规范化 snapshot，避免上游 master 漂移。
- 历史真实 bug 建立最小 fixture，并记录原始实机/日志证据回链。
- false positive 必须分类为 profile 缺口、schema 缺口或引擎特例，不能简单加入全局忽略。
- CK3 加载测试仍保留，用于发现 validator 尚不知道的 parser/PostValidate 规则。

## 5. Runtime 验收

### 5.1 每个 opcode 的最小矩阵

- 正常路径。
- trigger false 或 no-op 合法路径。
- 缺失、死亡或错误类型 scope。
- 重复执行与幂等。
- stale serial/revision/cycle/case。
- 零值、负值、上下界和溢出附近数值。
- 与主要相邻 opcode 的组合。
- trace、read-set、write-set 和资源守恒。

### 5.2 状态机测试

- 从初始状态穷举合法转移。
- 对非法边做 mutation，必须得到拒绝而非隐式修正。
- 任意顺序重复、重放和中断恢复。
- owner/subject/cycle/case 身份不能串案。
- 权限覆盖玩家/AI、政府、爵位、直属关系和受评/管理边界。

### 5.3 随机与时间

- 所有随机均由显式 draw tape 提供。
- 同一 draw tape 完全可重放。
- D+n、同日、跨月、跨周期、死亡和上司变化有边界场景。
- 未认证的 CK3 scheduler 行为不得由普通队列直觉推断。

## 6. CK3 MCP 差分协议

每个差分场景执行以下固定流程：

1. 冻结游戏版本、EXE SHA、DLC、playset、mod tree、配置、源文件和 Runtime 版本。
2. 通过 MCP 暂停 CK3，并获取 canonical pre-snapshot。
3. VM 使用同一日期、身份、revision、输入和 draw tape 执行。
4. CK3 通过真实产品 effect、event、decision、interaction 或正式 GUI action 执行。
5. 通过 MCP 获取 canonical post-snapshot 和必要可见投影。
6. 两侧生成规范化 delta，比较状态、资源、期限、serial、receipt、事件身份和错误语义。
7. 保存原始 MCP envelope、VM trace、hash manifest、normalized diff 和 CK3 artifact。
8. 用 native checkpoint 恢复，批量运行下一场景。

没有真实 post-state 的 command ACK 不能作为差分通过。

## 7. Certified semantics 账本

每一条认证至少记录：

- profile、游戏版本和 EXE SHA。
- opcode 或 opcode 组合。
- 输入 shape、scope 类型和适用目录。
- 场景矩阵与 artifact 索引。
- 认证日期、Runtime commit、mod commit 和 MCP capability。
- 已知限制与未覆盖邻接组合。
- 失效条件。

以下变化使相关认证自动失效：

- EXE SHA、游戏版本或关键原版脚本变化。
- opcode 实现、IR schema、scope model 或 scheduler 改动。
- CWT/profile 配置变化影响同一节点。
- 差分出现无法解释的 mismatch。

## 8. 批量实机策略

CK3 启动一次成本高，差分 runner 应：

- 在同一冻结构建和 playset 下预编排尽可能多的独立场景。
- 每个场景从 checkpoint 恢复，而不是依赖上一个场景残留状态。
- 先离线跑 parser、validator、VM、mutation 和 schema gate，只把通过者送入 CK3。
- 一次启动集中覆盖同类 opcode 的正常、负例和边界矩阵。
- 对 harness RED 与 capability RED 分开记录，避免反复重跑已经通过的语义。

## 9. 361 首批差分范围

首个认证包选择 B2 送达/申诉/首段 PIP（014–017、069–081、358–359）与 Workforce/endgame（AB 242–253、AC 254–265、AD 266–277、AL 355–356/360–361）。它将依赖 `query-zhongguo-ai-owned-case-snapshot-v1`、`query-zhongguo-workforce-collective-snapshot-v1` 及 Phase 0/5 冻结的补充 pre/post 状态合同；已有 static/fixture provider 不自动等于 live-ready。至少比较：

- owner/subject/cycle/case identity。
- 玩家与 AI 管理路径及爵位/政府资格。
- stage、route、grade、receipt 与 readiness。
- 个人金币、国库、HC、配额、晋升槽和债务 delta。
- deadline、stale、重复消费、退款和幂等。
- 三周期历史、上司变化和下一周期债务。

GUI 的位置、按钮 hit-test、modal、文本和最终画面仍由现有 CK3 实机 runner 验收，不进入 VM 认证。

## 10. 发布边界

- Parser/validator release 可以只依赖 corpus、静态和性能验收。
- Runtime profile release 必须附 certified-semantics 清单和 exact-build 边界。
- 宣传和 README 不得把 fixture-ready 写成 CK3 live。
- 天朝 mod 正式发版仍执行现有完整 CK3 发布流程；`open_kaishek` 只能减少开发期重复启动，不能取消最终实机。
