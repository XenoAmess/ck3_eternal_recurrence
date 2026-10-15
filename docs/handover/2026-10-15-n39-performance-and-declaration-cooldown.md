# N39 续录、性能优化与宣战查询月冷却

2026-10-15，证据时间使用 UTC。本机外置根 `B = D:/codex-ck3-demos/2026-10-14-robert-30year`，当前场次 `N = B/continuation39-cold-prep`，开发工作树 `W = B/war-results-worktree`。以下盘符和进程身份只描述这台执行机器。

## 当前事实与用户规则

第一场、第二场主动战争已经实际获胜；第二场后的领地持有证明是 `B/continuation38-cold-prep/ROOT-POST-SECOND-VICTORY-HELD-TITLE-PROOF.json`。30 年目标仍未完成。N39 首次续载为 raw `53200728`、1073-02-22；`p01-responses/0072-1-result.json` 已实际完成至 3474 周期、2433 天。完整普通规划和录制继续运行，不能以源码提交、测试或本交接代替目标完成。

用户最新要求：战争结果窗口改为 **10 个游戏日内清除的弱保证**，不为偶发小幅超时阻塞主流程；保留现有六日复查节奏。连续两轮宣战查询没有真正宣战，则冷却 30 个游戏日。查询返回候选只开一轮，后续实际推进且确认仍和平才算无操作；pending/同 ID collect 不重复计数。真实战争身份确认后重置计数。冷却只影响主动宣战机会，防御、正在进行的战争、事件与政务仍走完整规划。

其他既有要求继续有效：六项可选政务检查各自连续三次无真实操作后冷却 30 日；军力政策为 1.5 倍；未知事件采集后通过 MCP 选首个当前渲染选项，陌生交互选左项，再离线分析并存入已知库。只使用桌面 1；不切用户桌面 2。游戏会话、录像时长和单段容量均无上限，录像在 D 盘并包含决策悬浮窗。

## N38 中断与恢复

一次代理误将宴会补丁的三个文件写到冻结的 Z 开发树，触发 keeper 的 `screen task checkout has current tracked or untracked changes`。N38 实际于 01:55:52 强制关闭受管 Game202692，退出码 1；不是正常关闭，也不是录像进程自身崩溃。两个 P13 SDK 进程正常退出码 0，证据以 `ROOT-P13-OWNER-CLOSED.json` 为准，旧 supervisor 列出的 P08 进程不能替代它。Root 已精确保全误写内容、迁入 W 并恢复 Z 原字节；回执 `B/feast-frozen-tree-path-correction01/ROOT-PATH-CORRECTION.json`。

最新 SAVE 是 N38 `p13-responses/0578-1-result.json`：94,450,639 B，SHA `bb121505b62e8854a0ddcaab16ab8cd179c290c7ea30735b6baf9b24c7df9e26`，raw53200728，history index8000。之后579只是只读宣战查询，580未提交；未损失日期进度。新 seed 保留3413已结算周期，放弃未结3414的新增信用，不重放579。N39 完整 profile 校验、冷迁移和真实首帧核对已通过。

N38 录像正常完成：`B/continuation38-cold-prep/recordings/19730a3a-d565-4a9b-99d0-61f672f2a8a0.mkv`，19,963.566 s，11,994,007,991 B，SHA `3740ce39f3288f720a6453c321a5752ca9fae7f9342012530acbcd2e163b64c0`。不把中断伪装成连续无缺口录像。

为避免开发改动再终止游戏，N39 keeper 绑定独立干净的 detached 工作树 `B/runtime-source-00a70009`，HEAD `00a70009ebb0daca44e697d7373e771f752ed2ca`。只读运行输入与开发树分离；不要写这个目录。supervisor 接受实际冻结分支身份，包括 detached 空分支，继续核验 HEAD、干净状态、SDK、Native 和实际 owner 身份。更新 W 或 Z 不再是该 keeper 的监测对象。

新环境相对旧 profile 有一份运行源码和13份 production 文本的 CRLF/LF 差异，归一化内容相同。N39 对新来源诚实重取 fingerprint，并实际重投影新 profile 的13份 production 文件及 manifest/ZIP；原 profile、存档和构建来源保留。最终 manifest 文件 SHA 为 `d7072d8d04cda2acd591783750d1b9e8798674ee60f7f6399f6c4e5e5492c713`，不能与迁移回执中的语义 environment digest 混用。

## 当前实际进程与输入

- Game270044，creation `20261015022214.187404+000`，FILETIME134365045341874041，HWND23991364；桌面1 `964b3ff9-3cf7-4ba9-881b-47444f31cfbe`。
- supervisor owner 执行会话48889；screen task `g2-robert-continuation39-isolated-screen-20261015`。keeper运行后由它保活，Root不要另发 heartbeat 或释放。
- SDK启动器会话69767，实际 queue121644 / application210336。supervisor已为两者保留精确内核句柄；`ROOT-ACTUAL-SDK-PROCESSES-PINNED-P01.json` 是实际身份回执。
- feeder会话4688，`root_p01_loop_feeder.py` 从 Root 首控制4 full1 的原回执接续 full30；不要重复首控制。状态在 `ROOT-CONTINUOUS-FEEDER-STATUS-P01.json`。
- presentation owner82964，会话70306；overlay222328；录像worker212844。当前新段 `N/recordings/6dd55c22-18cd-4eb8-82f1-4ddaf57ba852.mkv`，02:23:34开始，2560×1440/30fps。已亲审录制场景中的地图与决策窗。
- 录制监护202328，交互离线worker202740，事件离线worker252524。三者精确身份与健康原件在 `ROOT-AUXILIARY-GENERATIONS-HEALTHY.json` 和 `ROOT-AUXILIARY-LAUNCH-DELIVERY.json`。新的故障恢复分支未触发，不能称已实机验收。
- Native仍为 B15，DLL SHA `146c05e88d94232cc898116b2331bdb4654855ba417e7e2e6da5d6597a6c001f`；pipe `\\.\pipe\xar-g2-robert-fresh20-20261013`。可见战争结果窗的 `closed_verified` 实机回执仍缺，空窗查询不能替代它。

`ROOT-FINAL-SDK-FREEZE.json` SHA `c18225872aca6ccced38a937562c7526f7c3de2b3d8f2ca97bcb7e85bcd80c41`，1290文件，实际源码 `N/sdk-p01/src`。queue SHA `d282ed6654a9857f169f70ad12332c36b410970da441005ea3faf23aa9812a4c`，entry SHA `8da2379c3b44f325131b0e1860f10dcd2ce06e62b72624b2ea35b10d4a365111`，supervisor SHA `42885457d4064eb1ee0596ba787d2962d72ba46df71d053dbce7819f89090d1c`。不要热改这些文件、硬链接源或 active freeze。

## 已实现与实测性能

队列容量扫描使用 `os.scandir` 复用目录元数据，保留四个根和 no-follow 语义；同一冻结目录从中位1.739 s降至0.0363 s。checkpoint到期状态穿过纯查询链，下一次原有实际动作/推进后保存，避免 SAVE 改变修订号导致整轮查询失效。精确只读 war-entry typed failure 保留原请求与证据，只短期抑制失败目标，不重放、不授业务信用。

纯 war-entry、declarable、faction、event 上下文和宴会诊断去掉未用的完整命令历史复制；实际宣战与有历史前缀依赖的 root 重试守卫保留。稳定P12为8.388 s/日，P13阶段混合窗口7.188 s/日。N39首个完整30回合实际推进40天/105.815 s，即2.645 s/日，含冷启动 root 查询和两轮完整选战；这还不是长期均值。

N39 faction seq26/50 实际0.158/0.180 s，P13中位7.419 s。CD首次实际 seq56：raw53201064启动，until53201784，正好30天；后续seq60/66/70跨日期继续推进，seq56–71没有 declarable、军力或 faction查询，SAVE63后CD仍保留。报告 `B/cold39-p01-performance01/FIRST30-ACTUAL.json`。事件与宴会首批没有自然触发，不授这两项实机提速结论。

永久源码已正常提交并推送 master：6685c3e6（只读恢复及war查询）、ff61576f（扫描及checkpoint carry）、348b534f（faction/event/feast）、5d6a1a1e（十日弱目标）、dbe8a3fe（两轮未宣战月冷却）。N39使用已逐字节核验的外置重合并源码，不能以W整文件覆盖冻结服务叶。

## 继续方式与剩余边界

先核实际进程、最新不可变回执和feeder状态；正常时让它继续。未知事件的离线库已迁入9事件、1交互和独立facts，包含N38关闭尾部三个已补分析事件；不要漏掉中断批次。不要重复宣战查询、事件选择、SAVE或Start来验证旧动作。

**不得普通读取活跃 `state/native-session/driver-state.json`**。曾因Windows共享删除冲突阻塞原子替换。优先读已完成的响应；必要小型可变状态使用 `CreateFileW(FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE)` 并限制大小。Driver只在SDK正常关闭后读取。

所有命令显式使用 `cmd.exe` 和 Python，所有写入使用绝对的N/W路径；环境默认shell和默认Z cwd不得作为执行入口。监护源码与开发提交分别保留，禁止向冻结runtime目录写入测试或文档。

容量继续使用通用策略1.0.0和 `B/STORAGE-ADMISSION.json`，复核时间2026-10-15T15:12:24.970124Z。复核不等于游戏/录像时长上限。当前必要恢复输入和录制保留；按策略复核已闭场派生物和大文件，不无限保留全部旧场次，也不删除个人资产。本轮没有作大规模回收。

继续目标是实际30年、战果、领地和发展，以及可复核的带决策窗录像。遇到真正终局、继承或业务错误时继续排查和恢复；不能因为单批完成就结束任务。
