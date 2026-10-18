# 一期 V5：把机制研究接入圣地规划知识

现有 `ck3_query_holy_site_planning_knowledge_v1` 的参数和七个 action 保持原有合同，
`knowledge.v5_clarifications` 增补本轮研究。数据作为手写 Python 常量随代码交付，运行时不读取研究机路径或游戏文件。
旧 V4 知识继续返回。

| action | 新增决策材料 |
|---|---|
| adopt | 基督教与伊斯兰教双向综摄主义路线；同一 F 同时满足关系与敌对度、另一个 G 可满足全局伯爵领信众条件；教改产生新信仰或新礼仪后的身份复核；特殊建筑条件 |
| create | 特殊建筑的建造与启用条件、男爵领持有者作用域、六组原版例子 |
| enshrine_relic / remove_relic | AI 清理的具体人类保护、两分支合并条件、圣物宣战理由的 AI 门槛；好感度的角色、方向、数量与叠加规则 |
| abandon | 最后关联与其他关联仍在时的逐项结果；确定收件人为预先保存的伯爵领持有者；无持有者时的缺省分支；与专用取出回调的费用区别 |
| promote / demote | 沿用 V4 等级、收益域、容量、当前值与缓存值合同，提供 V5 来源导航 |

`state_observed=false`、`native_legality=null`、`action_ready=false` 保持明确。
历史成功案例、源码保证的目标、当前许可和新增实拍是四种不同的证据，知识查询不会把它们合并为可执行许可。
`R(self)` 的保护条件只属于独立 AI 清理决议，不能据此宣称 AI 供奉替换也受相同保护。

来源与精确原件 SHA 在 `source_payloads`，机制正文分别见：
[双向采用](holy-site-cross-religion-adoption-12004.md)、
[AI 清理与宣战理由](holy-site-relic-ai-cleanup-conditions12004-v5.md)、
[好感度条件](holy-site-relic-opinion-conditions12004-v5.md)、
[放弃圣地的收件人](holy-site-abandon-relic-recipient12004-v5.md)、
[特殊建筑](special-building-religion-holy-site-gates12004.md)。

验证在 machine_id `4-8e1c2f1861`、2026-10-18 执行：
`tests/unit/test_holy_site_v5_clarifications_mcp.py` 经真实 MCP Client/ClientSession/server/service，
覆盖五个新增业务域、重复查询的深拷贝隔离、错误 build 拒绝，共七次工具响应。
禁止游戏调用的 driver 实际调用数为零。这只授予知识和传输合同验证，不授予原生写入、当前许可、自然 AI 或双向教改实拍资格。

当前保留构建的 CMake cache 中，五个教改草案 reader、hostility 等开关为 OFF；
源码 reader 存在与某份已部署构建可用须分别记录。
教改写端正基于原版 `RiteCreationWindow` 和真实确认弹窗施工，候选源码不等于已构建或已部署。
