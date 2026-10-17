# 第一期：把圣地操作补成收益比较

用户要求讲清采用、升降主要等级、共享圣地和圣物供奉／更换／返还的用途，而不止演示按钮。三份研究分别给出[主要等级比较](holy-site-major-grade-value12004.md)、[采用与新建的价值](faith-and-power-adoption-value-12004.md)、[共享圣物及退出](holy-site-shared-relic-value12004.md)。其中条件式源公式、历史实验与本次实际观测分别保存，不能互相替代。

## 游玩智能体已经可以查询什么

沿用 `ck3_query_holy_site_planning_knowledge_v1`，不增加操作许可或改变普通规划器路由：

| action | 新知识字段 | 帮助回答的问题 |
|---|---|---|
| promote / demote | `grade_value_comparison` | 普通地方层与主要Faith层、各类型原始系数、实际消费者条件、降旧升新损失、政治成本 |
| adopt / create | `value_analysis` | 收益给玩家还是封臣、已有站点的替代方案、特殊建筑与朝圣独立条件、完整后续预算 |
| enshrine_relic / remove_relic / abandon | `shared_relic_value` | 唯一共享库存、各教认可、按县主Faith求有效贡献、直接换物／单独取出／退出的不同接收者及费用 |

运行时使用随包发布的常量，不读取仓库docs或本机绝对路径。`tools/gen_holy_site_value_knowledge.py`从跟踪的研究JSON生成决策值模块；源定义变化后重新生成。查询返回深拷贝；`state_observed=false / native_legality=null / action_ready=false`继续有效。静态知识不授当前动作资格，实际操作仍需当前原生Can、报价和独立后态。

`rarity_source_boundary.native_algorithm_verified=true`表示精确1.20.0.4源码链已闭合；同时保留`current_value_observed=false / world_effects_applied_observed=false`。不能再把已有算法结论写成长期未知，也不能把源码确认变成当前属性到账。

## 本次验证和仍待补拍的部分

`machine_id: 4-8e1c2f1861`。2026-10-17T18:50:36.519975Z至18:50:42.735480Z，真实MCP `ClientSession`执行七种action、一次返回值污染后的重新查询及一次不支持build查询，共9次tool调用。新测试覆盖六项玩家决策差异、30条新增断言；实际游戏driver调用0，原PID5868正常退出0。生成器复现与编译已通过。此批只验证新增价值知识，没有重跑旧知识矩阵或启动CK3。

证据在`C:/workspace/ck3-faith-and-power-20261017/episode01/knowledge-value-mcp-candidate-a01/DELIVERY.json`。原SDK结果SHA为`4560fc1ff7b2bf39ebfa10153c7c9b689ae5680195c86cc6772fa84e1fd144be`，原退出收据SHA为`2e96d0269df68cd870880588074ecf17fc7dce9f548729b001c95466c6f17ffc`。路径只定位来源机器证据，不是MCP部署要求。

原生观察增量沿用已有圣地圣物context与action-context，增加全关联Faith认可矩阵；context另加按类型固定PC真实键读取的玩家／派生县主聚合。实现说明见[观察专题](holy-site-effect-observation-12004.md)。当前已应用候选源码，尚未编译及实机资格；没有新工具、编译开关或更宽动作范围。属性名绑定未闭时为null，类型定义值与角色总聚合分列，不拼造单站净贡献；scaled净到账仍未覆盖。

下一次独立实验补空主要固定项、非空槽直接更换、非空共享退出及最后关联退出。已有R7／R8不抵这些后态。新增中文稿按玩家目标讲解，音频、字幕和成片须随后重新制作；旧19:25审阅片尚未因此更新，也没有人工完整听审签核。
