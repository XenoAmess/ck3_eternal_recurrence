# G2 交付门增量台账（2026-09-15 19:35 Asia/Shanghai）

权威八项状态仍为 1/8，仅 G2-M1 complete；本表的预览包是额外交付切片，不替代正式里程碑。实机轮次按单实例持久台账 R{n} 追踪，缺证据的门保持未验证。

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 标准封建有界预览 | GO，已交付冻结 ZIP；仅已验组合 | native-auto-run / ck3_auto_turn | ZIP SHA 0e233dcb...eb2；Python d11268f；native 源 eefc88e；[操作文档](../ck3-native-ai/g2-preview-release.md) | R701 20/20：自然 pay_ransom 唯一 typed reject，独立 paused pending 清空，turn6 消费；R706 从 ZIP 解压目录 5/5，date_raw 53190696→53192304，无新增语义动作 | R702 stop-file 在 turn 边界 checkpoint/回收；R703 feudal paused 只读；R704 新进程同 episode/目标 5/5；R706 ZIP 冷恢复与配对存档 | 冻结范围外状态停止并保留 RED；整局主链另列，下游由 /root 调度 | d112 停止补丁和操作文档 144956e 已在 master；临时远端/集成分支已删；独立旧 clone 物理清理受自动审查阻塞 |
| 议会四类 final gate 与正式消费 | 未完成，query/action 未注册未广告 | 受控私有 gate；正式入口尚未接通 | master c31886f 既有 private glue/native；无正式广告制品 | R696 already-councillor typed 拒绝、合法替换；R700 新进程独立 incumbent 33433；guest-positive、候选 pending-positive、fireability-denial 未见；正式下一 turn 未证 | R700 仅 gate-only 冷查询，不是正式高层目标恢复 | 三个合法场景与 typed receipt/正式消费；/root 取景与议会包 | 既有补丁集成，原分支已删；部分独立 clone 物理清理阻塞 |
| GEN-034 战争战术/终局 C、D | R705 RED，GEN-034 仍 2/4 | native-auto-run；终局同帧三选一未就绪 | R705 B0 原 6769442→master f342232；旧 tactical DLL 与修复后版本不同 | R705 首 turn campaign-root 因封建空席 task 返回 council_unavailable，0 战术动作；最小 exact-build collector 修复已集成，待新 DLL 聚焦复验 | R705 原游戏存档 SHA 未变，driver 仅 restore/query；拟从原安全配对 checkpoint 新状态复验，不能盲续污染状态 | 修复后实机 root read/战术后置/下一 turn；终局 C、D 仍待；gen034_war 制品，/root 游戏 | 6769442 等价 rebase f342232，远端临时分支和 root worktree/引用已核验清理；原 clone 待 build 完成清理 |
| 自然事件与同战役自然继承 | 待实机自然触发 | 普通 production 正式策略 | 当前 master 既有合同，未新建专用能力广告 | tgp_travel_events.0030、death_management.1007 和自然死亡继承人续玩缺自然 paused 证据；fixture 不计 | 同一 campaign 自然继承后目标恢复待验 | 由普通 bounded/阶段长跑取景；/root | 无新工作分支 |
| 和平建设/生活方式/封臣派系 | M4 未完成 | 正式策略尚无建设消费 | c318 私有 player-view 候选 | 私有 closed-view receipt 缺失使旧候选确定性 evidence_insufficient；不能把空缓存写成无建设 | 建设后 checkpoint/下一 turn 未证 | 最小玩家 held holding 观测与合法性；peace_governance | 既有候选 runner master 886710f，工作分支和 clone 已清理 |
| 家庭外交、M6/M7 最小连续面 | 整局必要部分待实机 | 正式策略未闭环 | M5 private/static master 1d124f5；M6/M7 不擅改宽度 | 五个合法独立候选、自然婚姻结果、标准封建强制状态连续处理未证 | 同目标 cold restore 待验 | 实证到来再收 B0/B1；/root 调度 | 已集成 M5 分支清理；独立 clone 物理清理阻塞 |

100 游戏年、首条 1066→1453、第二独立种子与八项 G2 均未完成；RED、受控 stop、未执行和证据不足按各自类别记账。ZIP、日志和 checkpoint 位于独立制品目录，不依赖已清理工作分支。
