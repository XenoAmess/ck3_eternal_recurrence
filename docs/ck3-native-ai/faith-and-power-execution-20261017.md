# 信仰与权力：研究、智能体能力与首轮试拍

2026-10-17 开工。用户要求同时研究、拍摄和补强现有 CK3 游玩智能体：机制知识进入 `docs`，操作优先经现有 MCP 实现；视频素材消费同一条前态、决策、动作和独立后态链。

## 本轮范围与证据

本轮目标先完成拍摄交接规定的两条试拍：P01 采用既有圣地，对应 H01-01／H01-07；P02 供奉及移除圣物，对应 H02-04／H02-09。三期长片、试拍原片、静态研究和离线接口验证分别结算。

执行机器为 `machine_id: 4-8e1c2f1861`。2026-10-17T05:24:26Z 的实际安装读回为 CK3 **1.20.0.4 (Crozier)**、Steam build **25734779**、分支 `1.20.0`；EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。来源为外置 `C:/workspace/ck3-version-and-sync-20261017/inspect-01/result.json` 和 `executable-identity.json`，本轮研究线程再次核对机器身份与 EXE。仓库起点 `cc62e5515d3d6dc270d1e26cedcdea3f795e8222`；这不是一次已加载的游戏来源。

当前机器没有本轮 CK3 会话、基线存档、玩家／faith／rite 实例或已加载 DLC／mod 清单。未启动游戏，未取得新的 Steam 离线画面；不能挪用其他机器、旧截图或安装资源来填这些字段。仓库 `Crusader Kings III` 路径在 2026-10-17T05:32:27Z 被实际读回为指向 Steam 游戏安装的链接，应当保护，不能作为可删除的重复副本。

## 怎样帮助游玩智能体

共享规则和逐条来源见[圣地研究](faith-and-power-holy-sites-12004.md)。已在现有 `xar_autoplayer` 的生产 MCP server 注册只读工具 `ck3_query_holy_site_planning_knowledge_v1`，支持 `adopt`、`enshrine_relic`、`remove_relic`。首批六项验证及隐藏入口补充的一项实际 MCP 调用通过，完整原包 pins 与本机部署边界见[能力记录](faith-and-power-mcp-capabilities-12004.md)。它为智能体提供以下知识输入：

- 按动作返回原版候选来源、必要观察、资格条件、实际费用读取位置和独立后验。
- 区分圣地类型、地理实例、信仰关联及等级、圣物库存／认可、受益对象和特殊建筑。
- 对采用保留原版 `every_realm_county → every_county_holy_site` 候选来源；逐个相关 faith 判断兼容分支，不能以全球扫描或单一熟悉宗教替代。
- 区分个人信条与礼仪／信仰参数。缺失读取保持 unknown，不把“没有观测到”解释成 false，也不把静态规则解释成已通过原生合法性。
- 先保存决策和目标身份，单次提交后独立读取成员、等级、库存、所有权、实际费用及 Active／受益状态；ACK 不结算动作成功。

当前 native 宗教上下文可提供玩家、faith／rite 等部分输入；现有圣地库存、等级、Active／受益读口及采用／供奉专用动作尚无本轮资格。原生 GUI census 的现行 allowlist 不覆盖圣地窗口，也未提供任意语义 Invoke。采用决议在原版第 482 行声明 `is_invisible=yes`，入口是圣地窗口传递具体对象；现有 keyed 通用决议列表不保证能够触发它，通用确认也不能代替站点／宝物选择及业务后验。新增静态知识接口的离线通过不会改变这些边界。

## 拍摄准入的实际阻点

`machine_id: 4-8e1c2f1861`，2026-10-17T05:32:10.708110Z 的存储读回：C 卷总量 **511,776,722,944 B**、可用 **5,941,616,640 B**。按[统一存储策略](../storage-retention-policy.md)及其[参数](../storage-retention-policy.json)，本卷安全余量为 **21,474,836,480 B**，仅此项仍差 **15,533,219,840 B**，还未计录制／构建峰值、系统增长和其他未消费预留。

完整项目当前用量、有效额度、系统增长预留及全部其他预留尚未完成本机重新对账，不能以 null 当零。旧台账使用 hostname 身份且限期已经到达，只作定位线索，不自动续用。用户本轮明确答复“没有其他存储位置”；继续在 C 卷核查有明确用途、期限和替代依据的项目回收候选，不触及个人文件、其他任务或在用游戏。

首批只读 metadata 检查共 87,000 条／16.32 秒，未形成已核准的大资产精确删除清单，零删除。外置原件 `C:/workspace/ck3-faith-and-power-20261017/storage-review/FINAL-STORAGE-READONLY.json`，3,649 B，SHA-256 `fd6dc20d3e567f25093ce44ee14d4cb21029d28801fab0478142f95db2742b20`。后续增量复核另立回执，不改写首批结论。

低空间触发的增量 02 在同一机器 2026-10-17T05:37:06.179448Z 收口：47,028 条 metadata，完整核了五个旧项目资产根，实际观测分配合计 **1,278,680,056 B**。旧库存声称的数 GiB 大部分已退役，不能重复计算回收；另列 735 个 OBJ 也因完整重建来源、当前引用与期限未闭合而保持 PENDING。仍为 **0 verified 可删除／0 B**，未执行删除。此时可用 **5,936,361,472 B**，仅安全余量差 **15,538,475,008 B**。原件 `storage-review/increment-02/FINAL-INCREMENT-02.json`，6,048 B，SHA-256 `13dbe74dd35ffb19f292dc82cf8b587e82b043458d0951cf972156697cc8d8cc`，位于上述外置工作目录。

在真实准入完成前继续轻量研究、MCP 源码、镜头数据和工具链准备；不开 CK3、重型 native build 或录制。低码率与短片不能消除安全余量不足。P01／P02 当前均没有合格原片或完成后态。

## 工具链与下一步

2026-10-17T05:29:39Z 实际查询[官方最新 Release API](https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest)，得到 **v0.3.0**，发布于同日 05:11:16Z。旧 latest 网页缓存曾显示 0.2.1；实际 API 与[0.3.0 Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/tag/v0.3.0)优先。已更新 requirements、loader 及版本锁定测试，使用当前 `tools/.venv/Scripts/python.exe` 经 `pip --require-hashes` 安装官方 wheel；SHA-256 `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`。实际版本／帮助、依赖检查和 loader 回归通过。旧 source-lock 的 0.2.1 来源保留历史身份。

研究与 MCP 工作包已普通推送 `bf5d4d871f4a974339279a110693074df3aef406`，工具链更新为其前序 `399c9a495f2334718b69b0511ecbe4297be7d76f`。邻接原版事件知识 MCP 五项回归、Python-only 检查及提交字节核对均通过；源凭证使用精确换行保全，Git blob 与已核 SHA 一致。

同一机器 2026-10-17T05:42:56.604633Z 已实际创建 **authoring-only** run `faith-source-authoring-a01`，再次读取官方 latest API 后仍为0.3.0；12份必要输入保全、`validate --profile authoring` 返回0，完整run仅 **270,034 B**。外置路径 `C:/workspace/ck3-faith-and-power-20261017/authoring-01/run-manifest.json`，SHA-256 `ce667d99f485f613a5f27d6097e14836fedc26a3b4a9d8c40329300588f48bcb`；[入库索引](../../promo/ck3_faith_and_power/build-records/authoring-20261017-a01.json)绑定创建回执、机器身份、来源提交和有限保留期。原生phase记录明确 `pilot-capture=skipped`；这不是生产拍摄、媒体plan正向通过、宗教业务或成片。05:44:01Z闭场只读进程清单中没有CK3／FFmpeg／OBS进程，来源为外置`storage-and-process-close.json`。

后续按依赖顺序推进：交付共享研究与实际 MCP 知识调用；核出可合法回收的容量并重做准入；为缺失的圣地读写完成 exact-build producer／caller／consumer 研究及最小 native 接线；取得新鲜 Steam 离线证据和唯一现场租约；建立可回载、明确标识准备方式的母案，再拍两条完整试拍链。每条链绑定本机、加载来源、存档、对象、帧、动作、后态与原片时码。未知引擎边留在研究记录中，不能由旁白代填。

研究与记录回执按统一策略分别复核；本轮小型记录下一复核日为 2027-04-15，未完成试拍的必要输入保护必须另列用途和不超过七天的复核期限。
