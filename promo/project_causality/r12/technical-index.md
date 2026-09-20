# r12 技术与证据索引

这份索引用于给希望继续深挖的观众和维护者定位术语。正片不删除专业内容，只把它们放在每章直观说明之后；本索引不替代正片中的论证。

## 时间索引

| 时间 | 深度内容 | 对应价值 |
|---|---|---|
| 00:00–01:59 | 因果链总命题、已有 Mod 与新作者两种入口 | 先让观众知道这套体系为谁解决什么问题 |
| 01:59–12:20 | Mod 产品、家徽编辑器与 CK3 本体研究价值 | 可见结果不是概念图，而是可使用的交付物 |
| 12:20–18:48 | 罗贝尔连续母带：主菜单、新游戏、选人、读取、择敌、宣战、战争、胜利、继续游玩 | 展示 MCP 与自动玩家在真实 CK3 中能走到哪里 |
| 18:48–21:15 | exact build、EXE/ABI 绑定、ACK 与状态、War ID、target ledger、OODA、production-live primitive / loop | 解释为什么这段实机可核验，而不只是看起来像自动化 |
| 21:15–33:20 | 权威定义、生成投影、open-kashek、MCP、OCR 边界、智能体、staging、manifest、WAL 与发行记忆 | 让一次修改从起点到终点都可追、可重复 |
| 33:20–39:37 | 文档高于测试、测试高于代码；状态高于 ACK；exact build；证据等级与诚实边界 | 防止工具、测试数或成功回执替代玩家结果 |
| 39:37–49:37 | Loop A–D、CURRENT / VISION、反馈回流与人的位置 | 把交付从一次性项目变成无限演进系统 |
| 49:37–50:27 | 两条接入路径与最终行动呼召 | 让观众能从自己当前的位置开始 |

## 罗贝尔实机证据

- 原始母带：`artifacts/project-causality/2026-09-20-robert-mcp-streak-r30/robert-1066-mcp-streak-continuous.mkv`
- r12 连续展示母带：`artifacts/project-causality/2026-09-20-r12/robert-mcp-showcase-main-menu-continuous.mp4`
- 剪辑合同：`promo/project_causality/r12/robert-continuous-edit.r30-main-menu.json`
- 专题说明：[`docs/project-causality-robert-mcp-streak-capture.md`](../../../docs/project-causality-robert-mcp-streak-capture.md)

连续展示母带从 R30 原始源的稳定主菜单开始。第一帧只被延长三秒以便观众建立场景；此后的游戏时间保持单调递增，没有源时间跳口、镜头重排或速度变化。十个旁白 cue 只是同一条母带上的语义分段。

本局证明动态候选评估、宣战、集结、行军、战况复核、胜利核验和胜利后的继续游玩。本局开场没有出现需要选择的事件，因此正片明确说“没有事件就不伪造”；它不把另一场录像拼进来证明事件决策。首胜之后进入新的防御战争，镜头在游戏仍继续时结束，不预言未记录的最终胜负。

## MCP 与 OCR 边界

- 人物、战争、军队、资源、合法候选与结果等可从游戏内部结构读取的事实，优先由 MCP 提供；
- OCR 只用于必须核对的可见呈现、渲染文本或 MCP 暂时没有语义入口的界面事实；
- 能补原生只读 bridge 的状态缺口，不长期以 OCR、像素坐标或 `unknown` 兜底；
- 动作 ACK 只说明请求被接收，结果必须由独立状态快照再次读到。

相关入口：

- [`docs/testing-workflow.md`](../../../docs/testing-workflow.md)
- [`docs/ck3-native-ai/README.md`](../../../docs/ck3-native-ai/README.md)
- [`docs/autonomous-agent-progress/goal-and-roadmap.md`](../../../docs/autonomous-agent-progress/goal-and-roadmap.md)

## 四层权威关系

1. 文档定义玩家承诺、状态语义和完成条件；
2. 测试证明实现满足已写明的承诺；
3. 代码是当前实现，不得反过来偷偷重定义承诺；
4. 真实 CK3 状态与冻结证据裁决运行时事实。

这里的“文档高于测试、测试高于代码”不是说文档永远正确，而是要求语义变更先修改权威定义，再让测试与代码显式追随。若真实游戏推翻假设，证据会返回文档，形成下一轮修订。

## 四个无限演进 Loop

- Loop A：玩家需求 → 权威定义 → 内容生成 → 实机验收 → 玩家反馈；
- Loop B：游玩 blocker → 原生 AI / exact-build 研究 → bridge / MCP 观察口 → OODA → 新 blocker；
- Loop C：新语义 → open-kashek 与静态验证 → CK3 runtime 互证 → 版本绑定认证；
- Loop D：GREEN 证据 → 可公开声明 → 发布物 → 下载、评论、故障与新需求 → 下一轮权威文档。

四环并不取消人的判断。系统承担机械生成、重复重放、结果回读和证据记忆；人仍负责玩家承诺、世界观、规则取舍、能力边界与是否发布。

## 媒体校验

- `50:27.639`，`2560×1440`，H.264/yuv420p，30 fps；
- AAC 48 kHz 双声道；综合响度 `-15.9 LUFS`，LRA `4.4 LU`，true peak `-1.5 dBFS`；
- 简体中文烧录字幕无替换字符；英文 SRT 共 214 个显示块，并封装为可选择的 `mov_text` 字幕轨；
- 7 个容器章节；114 个叙事 cue；
- SHA-256：`BB1CFD1AC6C286806205CD77053F6503F93C9B80EB61464A561DDF1620A50CC1`。
