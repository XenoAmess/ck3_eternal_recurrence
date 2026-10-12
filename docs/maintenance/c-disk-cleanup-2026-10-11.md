# C 盘高优先级清理：2026-10-11

用户明确要求创建子线程清理 C 盘垃圾，并包含现行保留规则下的过旧历史证据。实际执行者为 `/root/c_cleanup_high_priority`，机器为 `XENOAMESS-FULL-TOWER`；Root 负责独有源码/知识的整合与提交。依据 [统一存储保留策略](../storage-retention-policy.md) 1.0.0 和同步 JSON，而非其他机器的空间台账。

## 第一阶段实际结果

截止 `2026-10-11T08:01:14.235519Z`：

| 项目 | 实际结果 |
| --- | ---: |
| 退役旧临时 Git clone/worktree | 66 份 |
| 删除文件 | 915,893 |
| 删除对象逻辑大小 | 33,934,426,119 B / 31.60 GiB |
| 已量测 allocation 子集，仅缓存和旧构建 | 423,716,512 B |
| 总物理回收量 | 未知，整份源码副本未做 allocation 量测 |
| C 可用空间：开始 | 407,527,424 B / 0.38 GiB |
| C 可用空间：截止 | 42,562,506,752 B / 39.64 GiB |

可用空间还受到系统和并发任务影响，不能将整个 free 增量归因于本次删除。数字按实际回收计一次，不把计划、Git 注册移除或只读重试重复相加。

旧缓存包含明确超过七天的软件缓存。旧 Git 副本按 clean 状态、补丁等价或已核实后继替代退役，正常使用所属仓库的 `git worktree remove`；独立 clone 作为已退役整份副本回收。副本中的过时日志、失败报告和归档随其退役，不因曾是证据而无限保留。

另外已实际删除 `C:/xar-wf-final-20260831`、`C:/xar-wf-final2-20260831`、`C:/xar-wf-native-20260831` 内 520 个旧 CK3 1.19 bridge 构建/测试证据文件，80,478,269 B logical、81,492,096 B allocation。项目归属和 8 月 31 日闭场时间来自旧 CMakeCache/LastTest 记录；它们已超过 build 保留期且被当前 1.20 路线替代。原 build/test payload 已不可读，闭场摘要和删除回执保留。本轮没有执行旧测试来刷新期限。

## 独有变更先处置，再回收副本

- `a4-faction-live-review`：唯一 R0054 历史诊断补入 [当前 faction 专题](../ck3-native-ai/ck3-1.20.0.4-faction-adopted-native.md)，`981d53b3` 已推送后才退役；未恢复过时实现或回退能力状态。
- `a4-lbf`：十八个相关文件的实现已被主线包含或后续修正替代，旧副本退役。
- `a4-report-exactday-h9635`：五份文档的十八行新增内容已全部在主线，旧副本退役。
- `g2-m7-raw-clock-units-12004`：新文档是主线文档的严格前缀；修改知识已被主线包含并扩展。Root 明确丢弃旧副本差异后退役。
- `g2-phase-effect-emptiness-source32`：两个修改仅 CRLF/LF 差异；206 个删除是临时副本内的瘦身，未镜像删除主线。Root 明确丢弃后退役。

四份 clone 的只读 Git object 首次删除失败后，在同一精确目标内重试完成，原失败记录保留。一条真实失效 alternates 链已最小修正到 Z 主仓 objects，Git 原生读回成功；为旧 child clone 提供对象的副本暂保留。一次 C-parent worktree 注册归类错误也已纠正后正常移除，没有重计文件回收。

## 第二阶段：24 份来源候选全部处置

截至 `2026-10-11T08:25:08.926360+00:00`，十个并行工作包已完成 40 个唯一旧提交的语义对照：38 个已经由 master 包含或由明确后继实现取代，直接舍弃旧副本；2 个独有知识提交先由 Root 补入 [Character detachment 专题](../ck3-native-ai/army-character-detachment-suffix-12004.md)，并推送 `master d0ae5581` 后退役来源。该小补丁保留 `28B1750` 的完整 203 B own-method 控制流和 Mermaid 分支图，未恢复旧接口、旧候选状态或 live 资格。

| 项目 | 第二阶段增量 | 本轮累计 |
| --- | ---: | ---: |
| 实际退役旧副本 | 24 | 90 |
| 删除文件 | 207,716 | 1,123,609 |
| 删除 logical B | 5,015,240,914 | 38,949,667,033 |
| 删除 logical GiB | 4.67 | 36.27 |

C 盘终点可用 `47,948,550,144 B / 44.66 GiB`；起点为约 0.38 GiB。完整物理回收总量仍未知，可用空间变化包含系统和其他任务影响。第二阶段删除失败、未决来源候选及延期对象父链均为 0；五条已知私有 objects 依赖按 child 先于 parent 处置，最后的等价 new-date parent 也已正常退役。

这里保留的是小结论和删除回执。24 份来源副本原文件已不可读，没有新建归档源码树；第一阶段冻结 `RESULT.json` 没有改写。原有错误/失败 attempt 及必要小摘要留在回执中，三个简写证据路径已更正到实际文件并保留原记录。单纯 `git cherry +` 不再构成旧副本的保留理由。

## 当前必要依赖

当前 Native84 必要 C 路径包括 `migration4-complete-domain-build/strict07/cache-observers`、同根 injector，以及 `migration4-entry-live-fix/joint-army-poet-runtime20` 的 host/attach_host，因此这两个实际依赖根保留。其他未分类范围继续按台账复核；无法访问的临时根未强行处理。当前 Native84/SDK84/Source594、D 上 SAVE6077 恢复链、用户存档/mod、Steam/游戏安装和当前工作现场均未清理。

本轮为纯后台文件/Git 副本清理；测试、项目导入、编译、Game/Steam/窗口/进程/RPC 操作均为零。没有新归档分支。G2 同时完成 `bf3697e1` 教育明确请求、`2805addc` common native end、`e227ab29` 非零教育选项正常复制源准入，均是源码交付，未提升 live 资格。

## 可核验回执

完整第一阶段结果：`D:/codex-ck3-background-spill/native71-continuation-20261010/c-cleanup-high-priority-20261011/RESULT.json`，66,835 B，SHA-256 `bf8bd47c142d13c771dd616def56af05adf7e58bf7fc6ac75fe30f624c580edf`；同目录 `RESULT.md` 为小摘要。`expired-build-closure-evidence.json`、`expired-build-result.json` 保存旧构建闭场摘要与实际删除结果。

三份旧提交 triage：`continuation-10/c-cleanup-three-copy-triage/TRIAGE-FINAL.json`；两份 dirty 副本 triage：`continuation-10/c-cleanup-two-dirty-copy-triage/TRIAGE-FINAL.json`，都在同一 D continuation 根。Root 的历史知识实际采用记录为 `ROOT-C-FACTION-HISTORY-SALVAGE-ADOPTION.json`。详细 ledger 按 30 天复核，小结果摘要按 180 天复核；没有声称自动 GC 已实现。


第二阶段最终小结果：`D:/codex-ck3-background-spill/native71-continuation-20261010/c-cleanup-high-priority-20261011/PHASE2-FINAL.json`，6,946 B，SHA-256 `7dfa2dceb967b19fd74c5cbaab20c282c3bdba388c373ffdd509b91aed63f633`；同目录 `PHASE2-FINAL.md` 为摘要。`RETIRED-SEMANTIC-PENDING-COPIES.json` 是 24 份实际退役 ledger；`ROOT-SEMANTIC-CLEANUP-DECISIONS.json` 是十个并行包、40 个提交和 24 份副本的 Root 明确裁决，SHA-256 `f7b74ebc64ad0db64476a3fa2770934d25a8e7358fe75f6de843a362fc801194`。独有知识实际采用回执为 continuation 根的 `ROOT-C-EXTENSION-ORIGIN-HISTORY-SALVAGE-ADOPTION.json`，对应已推送 `d0ae5581`。

## 2026-10-12 后台增量复核

继续用户授权的高优先级清理线程，按同一策略读取旧明确裁决后，对第二阶段
24 个精确 C 子根执行一次只读 metadata 入口；父树、个人文件、游戏与依赖不纳入。
实际命令 `py -3.13 -B -X utf8 readonly_c24_metadata_inventory.py` 退出 0，
工具回执为 `1908b8`。每个根都逐项在自身路径观察为 `MISSING_OBSERVED`；
没有扫描树、正文读取、哈希、C 写入或删除。实际发现文件/目录/错误均为 0。

这批现在没有现存回收候选，不把历史已删除量再次记为新回收。`released_bytes`
为 null；mtime 不构成 TTL，且观察不是原子全卷快照。原命令未采绝对解释器路径
或版本读回，不能补填这些事实。只保留原工具结果与此小结，不复制完整旧库存。

Native89 的新 DLL 仍沿用原 injector、host/attach_host 来源，前述两项 C 依赖根
继续按用途和既有期限保留。用户占用 CK3 期间，清理与研究均保持后台文件操作；
不会以新 DLL 或停用实机作为删除仍需依赖的理由。未分类对象继续精确复核，
没有扩大为 C 父树清扫或部署自动 GC。
