# 2026-11-02 本地模型规范接入与宗教礼仪融合修复

`machine_id: 4-8e1c2f1861`；观察日期为本机自然日2026-11-02（Asia/Shanghai）。用户明确要求同步项目到最新，采用独立仓库规范并加强本地模型使用。本记录绑定本机路径，不覆盖其他机器的配置。

项目从`900922169`快进到`734a096cd`，保留远端后续正常推进。父目录新克隆`C:/workspace/local-model-operations`，共享来源为[`865161d5de1b6b35e63b35a5c3630350844c4842`](https://github.com/XenoAmess/local-model-operations/tree/865161d5de1b6b35e63b35a5c3630350844c4842)。本机没有`Z:/workspace/local-model-operations`；不把其他机器的绝对路径当作前提。

已读取该版本AGENTS、usage、executor、能力证据和运营规范。当前离线源码任务直接调用其`scripts/call.py`及唯一共享`config/executor.json`：`qwen38-coder`，固定system／当前完整源码与合同／具体任务三消息，有限输出、SSE和共享瞬时错误重试。未修改活跃Game、旧worker或本项目兼容配置。

每日维护首轮退出75：pnpm安装`opencode-ai@1.19.5`时跳过postinstall，`bin/opencode.exe`仍是479B文本占位。检查实际包和平台二进制后，以已验证的同包Windows二进制建立硬链接，遵循postinstall的copyBinary行为；没有执行其PowerShell CPU探测。03:39:06+08:00共享每日检查实际通过，registry latest与实际CLI均为1.19.5。维护修复由owner完成，不算模型生成能力。

三个真实工作流并行派发，首轮实际POST峰值3；增加一轮测试纠正，共4 POST，全部完整stop，无传输重试。未凑12–16请求。三个工作流分别为GUI修复、Java布局回归、相邻窗口同类缺陷检查。模型提供了融合影响一处有效fill修改，但遗漏同父层的另外两页；owner补齐。两版Java测试存在AST读取、错误层级替换和视口定位问题，全部拒绝，最终测试由owner实现。HTTP成功与代码采用分开记录。

原始REQUEST、SSE、模型回答、诊断和软件验证回执保存在本机`C:/workspace/rrf-ui-layout-20261102`，按通用存储策略复核，不提交原版游戏材料或未审原始回答。原始模型证据的下一次用途复核为2026-11-08T19:00:00Z；小型可复用结论留本记录及共享仓库能力条目。准备、审阅和纠错人工耗时未独立计量，保持unknown，不宣称净节时。

窗口修复与软件结果见[模组布局记录](../mod_religious_ritual_fusion/docs/ui-layout-2026-11-02.md)。按同步后最新授权，用户自行玩游戏期间保持离线；本轮不做CK3查询、部署、捕获或启动。后续只有新的真实任务才继续请求，不重复已闭合任务刷调用。

用户随后明确恢复本次CK3开发、测试和发布，以上为恢复前阶段。续工按现行共享规范继续调用，未修改活跃Game模型配置。共享仓库已多次正常同步，本轮新增经验推送至[`8189b6c119e9b1247926e8453c5ec32491c85fb1`](https://github.com/XenoAmess/local-model-operations/commit/8189b6c119e9b1247926e8453c5ec32491c85fb1)。

新增长名单输入及双语工坊文案为3个真实逻辑请求、4次POST，其中一次连接重置按共享策略重试；此样本四段不交叠，峰值为1，不外推为全机并发。两份seed候选语义错误被拒绝，owner另写四文件并通过实际Java fixture→FrozenReader及130项必要回归。文案部分采用，两个完整字段均经owner修订，修正旧／新缓存状态矛盾、中文遗漏及未验滚动过述；完整字段原样采用0/2。HTTP-GUI-002与脱敏证据已在共享仓库发布，原REQUEST/SSE仍留执行机器。

真实R0062 owner采样故障也交给本地模型进行一次完整候选任务，技术200/stop完成；候选保留了与实际发布中状态冲突的谓词，被owner拒绝，最小生产修复及26项最终回归由owner完成，未重复请求刷语义重试。修复的软件验证与后继实机分别记录，见[故障记录](ck3-scripted-widget-owner-sampling-2026-11-02.md)。

2026-11-02后继：独立规范已正常快进至`0fe3600`，已读更新后的HTTP能力及运营规则，沿用唯一共享config。最终Git三方合并审阅为一个真实逻辑请求、两次POST：首段连接重置按规则整次丢弃，第二次200/stop/DONE；模型保留双方AGENTS授权文字的建议经owner审阅部分采用，错误hunk行数被拒绝并机械重算，未制造无重叠的Python源码冲突。原件在`C:/workspace/rrf-ui-release-20261102/git-linear-sync-review-a01`；执行、采用和净节时仍分列，未测净节时。

R0064实际UI、后继发布和R0066缓存正常0已完成；共享模型HTTP成功不抵扣这些实机事实。所有请求均有具体代码、文案或合并任务，未按人数或次数凑调用。最终来源及原失败见[0.2.1发布记录](../mod_religious_ritual_fusion/docs/publication-0.2.1-alpha-2026-11-02.md)。

闭场已再同步规范仓库至`c4a27aa`并读取新的任务单位及准备成本规则；本次真实合并案例`HTTP-GIT-MERGE-001`及脱敏证据已正常发布至[`50903b08b6528d307c1fbb4f2c000f9ae9b3e622`](https://github.com/XenoAmess/local-model-operations/commit/50903b08b6528d307c1fbb4f2c000f9ae9b3e622)。该请求1次逻辑／2次POST，首截流整弃，完成段47,414输入／2,012输出tokens、TTFT0.979360秒；保留文档部分采用和owner纠正hunk，未授源码、Game或净节时信用。
