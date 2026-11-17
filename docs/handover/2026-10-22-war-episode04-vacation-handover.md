# 第四集战争机制视频：2026-10-22 度假交接

> machine_id: `desktop-3fevhd2-1c74096080`。交接日期 2026-10-22；全文时间用 UTC，北京时间为 UTC+8。身份以当次 `tools/ck3_live_run_id.py machine` 实读为准（Root 原工具回执 `25bed9`，2026-10-22T10:37:48Z），不是根据盘符判断。本文承接[10 月 20 日交接](2026-10-20-war-episode04-vacation-handover.md)，历史失败和旧进度保留，当前状态以本文及[本次闭场证据](evidence/2026-10-22-war-episode04-vacation-closeout.actual.json)为准。

## 先看结果

用户最新要求是“平稳收尾，编写交接文档，输出到 docs”。已停止新研究、新游戏、新录制及发布续跑；本次收尾只关闭原任务和交付这两份小文档。

- **当前审核片已生成，已放入 OneDrive，23:58.667，47 段。** 35 张选用图卡、字幕及衬底已改用本系列棕金黄色。此前蓝色来自误用通用模板；这次沿前几集的实际色板重做并重编完整影片。
- **正式动态主题仍为 9/11（81.8%）**，尚缺 R05 自然低补给损耗、R08 维护费实际付款归因。源码研究和运行链准备不能增加这个分子。
- 两个不同 B 驻点的补给正增长已有 **2/2**；完整同起点 A/B/C 对照仍 **0/3**。旧研究 10/14、业务 7/11 是不同分母的历史口径，不因本轮文稿补充自动升级。
- 研究已经整理成可供 CK3 游玩智能体**显式查阅**的版本绑定规则，含必要输入、准入条件、公式、取整和例子；**没有自动接入普通规划器，也没有实际自动消费资格**。
- 45 项机制/视频来源文档及 CI 修复已形成三笔**本地**提交，远端推送被 non-fast-forward 拒绝。不得说“已经全部合回 master 并发布”。

## 当前影片与可读入口

| 用途 | 当前入口 |
| --- | --- |
| 首选审核片 | [OneDrive 黄色机制审核片](C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-Episode04-Mechanics-Yellow-Review-20261022-a01.mp4) |
| 同内容本地保留原件 | [native 内容对象](C:/ck3-e04-resume-20261020-a01/r22-mechanics-full-a01/attempt-a02/native/runs/mechanics-full-a01/artifacts/derived/sha256/82/822963261DAD6ABDF63C42C66EFB13DE24F77A04F74E45A987CA0ADA18D8792F.mp4) |
| 智能体阅读规则，本地 W 已提交 | [第四集机制规则](C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree/docs/ck3-native-ai/episode04-20261022-mechanism-rules-12004.md) |
| 结构化规则与原版术语 | [mechanism-rules.json](C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree/docs/ck3-native-ai/evidence/episode04-mechanism-rules-20261022/mechanism-rules.json)、[terminology.v1.json](C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree/docs/ck3-native-ai/evidence/episode04-mechanism-rules-20261022/terminology.v1.json) |
| 最终黄色 47 段来源、可移植包入口 | [CURRENT-YELLOW47.json](C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree/docs/ck3-native-ai/evidence/episode04-mechanism-final-source-20261022/CURRENT-YELLOW47.json)、[SOURCE-MANIFEST.json](C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree/docs/ck3-native-ai/evidence/episode04-mechanism-final-source-20261022/SOURCE-MANIFEST.json) |
| R05 最新运行链源码交付 | [DELIVERY.actual-a02.json](C:/ck3-e04-resume-20261020-a01/r25-r05-runtime-source-a01/source/DELIVERY.actual-a02.json)、[OPERATOR-HANDOFF.md](C:/ck3-e04-resume-20261020-a01/r25-r05-runtime-source-a01/source/OPERATOR-HANDOFF.md) |
| 本次关闭、保留与恢复状态 | [闭场 JSON](evidence/2026-10-22-war-episode04-vacation-closeout.actual.json) |

审核片为 **72,484,128 B**，SHA-256：

```text
822963261dad6abdf63c42c66efb13de24f77a04f74e45a987ca0ada18d8792f
```

实际时间线 43,160 帧、30fps。完整 AV 解码、PTS/DTS、CRC/SHA、音轨非零和尾部对齐已通过；联合抽审 32 张最终 JPEG，Root 另看实际完整分辨率帧。**尚未完成整片人工 1× 听看及最终签收**；字幕分页偶有词中断开，后续人工听看应重点检查。技术通过不替代教学价值和用户审阅。

OneDrive CFAPI 于 **2026-10-22T08:11:16.640668Z** 对同一 FileID 返回 InSync=1，validated/on_disk 均为 72,484,128，modified=0。原件：[CLIENT-METADATA.actual-a03.json](C:/ck3-e04-resume-20261020-a01/r22-mechanics-onedrive-a01/CLIENT-METADATA.actual-a03.json)。这是已发生的客户端同步核验，**没有独立云网页下载后的 SHA，也没有发布到 B 站**。

旧 31:58.233 片仍在 `C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-Episode04-Full-Working-Review-Two-B-Sites-20261022-a03.mp4`，只作历史工作版。新片没有覆盖它。新片旧工作副本 `r22-mechanics-full-a01/attempt-a02/work/full/E04-MECHANICS-REVIEW.mp4` 已实际回收，当前不可读取；应使用上表 native 或 OneDrive 副本。

系列色板来源为 `promo/ck3_native_war_ai/integration/src/war_ai_promo/series_palette.py`：BG `#211813`、PANEL `#35291F`、INK `#F0E5CF`、GOLD `#CBA56A`。蓝色只可作为阵营辅助色，不再用作整卡背景。颜色问题与已退役的旧蓝色实时决策窗是两件事；新录制仍不得启动旧窗。

## 用户要求与内容修改原则

1. 核对 CK3 官方中文，不再把爵位层级无条件叫“县”，不把军队“补给”叫“库存”。Army=军队、Regiment=军团、Men-at-Arms=兵士、Levies=征召兵、Commander=将领；实际地理对象按地点/男爵领/海区区分。
2. 未查明的机制应继续查明并讲清。讲稿以游戏的条件、计算与结果为中心，避免反复讲制作流程或用“还要核实”填充解释。
3. 机制公式应给真实输入和可复算例子，不能把动作 ACK、窗口图或净差分当作完整因果证明。
4. 可复用知识应服务游玩智能体。现有规则可显式参考，自动规划器接入需要另做实际实现和验证，不能把文档存在说成系统已使用。
5. 用户此前允许提高并发；恢复后研究、剪辑、知识整理可并行，游戏/屏幕保持单一现场所有者，共用容量账。

## 已经查明、不要重做的机制

规则绑定 **CK3 1.20.0.4 / Steam build 25734779**，来源 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。源码、原版中文键、有限原生片段与历史实测按来源索引分别保留。不同版本和其他机器不能继承本机实机资格。

| 主题 | 已闭结论及例子 | 保留的边界 |
| --- | --- | --- |
| R07 登船费 | 普通本例 `round_half_up(max(0,N/100×rate×max(1+owner修正,0.1)))`。1162 人、rate=1、诺曼长船 −75%：2.905→**3 金币**；实际余额 260.10399→257.10399。 | 0.1 是倍率下限，不是至少付 1 金币；100 人可舍入到 0。不能先把人数按整百截断。海上维护费及陆海转换时间另算。 |
| 补给调度 | ArmyManager 以真实军队桶轮转 30 组，轮到并通过准入才计算完整变化，不逐日除以 30。集结后宽限必须已经超过 30 天；战斗等分支会拒绝。 | 公开 Army ID 不能直接猜真实桶；“回调未发生”“条件拒绝”“实际变化为 0”“到容量上限”须区分。 |
| 陆地补给 | 合格人数 U≤L 且友好条件成立时基础 +20；U>L 时基础 `−min(10,max(5,(U−L)×0.001))`。负变化才走持续时间修正，例如 −5/1.4。 | 同战争侧、所有者和原生关系链影响计数与准入，不把全地图所有军队都加起来。 |
| 补给容量/挨饿 | 容量按 `(基础+加值)×(1+比例)`。阈值是绝对值 60、10；低于 10 为挨饿，默认补给损耗 5%，补给不足默认 0%。 | 围攻默认 1% 是独立分量。海运宽限到期当日具备日期资格，但仍要轮到真实桶并通过其他条件；普通海上基础每次 −8。 |
| 补员 | 自然月初按每个实际兵力部分 `trunc0(min(满员×准备比例,缺额))`；小数不留到下月。R0221 的 69/68、4.02% 实际补 1。 | 不能把一个 ADD 当全军面板全部增长，也不能把已集结军队的当前补员率一概写成原版未集结 3%/10%。 |
| 损耗及敌境进入 | 199 人的 5% 与 1% 分别取整为 9+1=10。普通敌境跨伯爵领进入预算为 `min(N,max(trunc0(N×5%),100))`；1000 人拆两支 500 可由 100 变 200。 | 在实际进入时触发，不是 Move ACK；同伯爵领内移动不满足。R0217 已确认 17 笔扣兵共 236，仅是阳性记录小计，不冒充伯爵领损耗总额。 |
| 合军 | 两份权重、份额与补给分别定点截断，再受合后容量限制；100 补给按 1:2 合并可得 99.999。两方向人数权重不完全对称。 | 保留 A 与保留 B 可得 50/49.8504；不要人为删掉来源实际计入的角色行来制造理想平均。 |
| 角色财务 | CharID uint32%30 选角色日，净额 `wrap64(a−b−c−d)`；正额完整入账，不除以 30、不向整金币取整。c 为当前军费；d 的来源已闭到官职俸禄/宫廷舒适度/传奇分支。 | a/b 尚不能直接命名为所有税收/支出。不要从净 ADD 再扣一次军费；静态生产链闭合尚不等于 R08 已观察到实付。 |
| 行军路段权重 | D 为两端坐标差的整数欧氏距离；M 为两端通行系数平均；普通 M>0 时 Wraw=`trunc(D×Q×Q/Mraw)`，同介质路段用 W/V。D=30、M=.65、V=3 得约 15.38461 天。 | 跨陆海是替换该路段时间，不再把 W/V 额外加一遍。通行系数 getter/解析字段已闭，字段正式文本注册名尚未闭，讲稿用“端点通行系数”；不能把静态字符串表整数直接当解析器 ID。 |

详细分支、固定点算法及来源读[规则正文](C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree/docs/ck3-native-ai/episode04-20261022-mechanism-rules-12004.md)。最新行军权重、47 段稿、卡片及 N05 后继在最终可移植源包；先看 CURRENT-YELLOW47，而不要只读早期 46 段入口。

可移植包保存 **182 个无损来源成员**、来源清单、配方与矢量文本。4 个最终候选文件合计 204,686 B，包内有 37 张 SVG 历史/后继版本、实际选用 35 张。它不含 MP4、MP3、截图、EXE、字体、依赖或凭据。可复核知识和编辑来源；完整影片重建仍依赖外部已固定媒体与工具，TTS 文本不能重建完全相同的 MP3。

## 最后实机 R0237：到达暂停地图，未开拍

场次 `desktop-3fevhd2-1c74096080--vanilla--R0237`，场景根：

```text
C:/ck3-e04-resume-20261020-a01/r23-live-r08-phase23-a01
```

实际 Game PID **16768**，created FILETIME **134371374612846158**；10:11:02Z 启动，暂停地图 raw date **53146872**。10:15:17Z OS 只读采集核对同进程映射的 `C:/w/e04date32a01/build-a01/xar_ck3_bridge.dll`，14,397,440 B，SHA `062b2ae3639c230d2ca4552d5de67c9536605b1fbda2045c040d3fd6f25ca746`；这是模块文件关联核验，不是内存代码完整哈希或业务结果。证据：`root-a01/R0237-LOADED-BRIDGE-OS.actual-a01.json`。

Steam 离线已在本场重新实际看图：10:02:03Z 新采集含窗口位移/nonce，Root 10:02:42Z 直接审阅 Steam“离线模式”；回执为 `root-a01/STEAM-OFFLINE-ROOT-REVIEW.actual-a02.json`。背景托盘时间已知陈旧，没有拿它证明新鲜。普通实机没有切 Steam 在线。该证据只能证明此机器此时，下一场须新取。

**本场新增游戏日 0、observer Arm 0、Film Start 0。** 实际 Film card/config/manifest 没有生成，Film one-shot 甚至尚未启动；相机只做到源码预检和准备元数据。不能将“准备完成”写成“正在录像”，也不能拿 R0237 抵扣两项欠缺主题。

方法问题已经明确：金融/容量/身份等准备逐层通过后，没有在开局前把“单次 Film 预绑定→实际录制配置→Root 看图→连续 Start”整条路径跑通，暂停现场仍在等文件。后继应先完成整个入口的离线接线检查，给录制、正常退出留足实际时间；不能继续叠加等待文件或承诺开机后很快补镜头。准备源码与真实启动状态应分别汇报。

### 最终关闭状态

现场 owner 在 **10:40:37Z** 已封存 [R0237-OWNER-CLOSED.actual-a01.json](C:/ck3-e04-resume-20261020-a01/r23-live-r08-phase23-a01/control-a01/R0237-OWNER-CLOSED.actual-a01.json)，5,919 B，SHA `a81536efa7e9d7a0bfbc9f5f92dea51909dd8e583fc54a09ce00d9a373bdb6dd`。Root已读回该件；GUI图审由原operator完成，未冒称Root亲看退出图。

| 对象 | 真实终态 |
| --- | --- |
| 业务/public 原 session88090 | **exit2**。原冻结Film guard没有cancel结构，真实STOP reply触发 `Actual Film reply shape/run/reviewer differs`；错误保留，未伪造实际manifest。随后进入原 finally 正常关闭。 |
| 游戏 | 走菜单退出桌面、autosave实际取消勾选；正常GUI合格、原retained OS exit0、native0，无强杀。 |
| host33824 | 原wait0，10:31:33Z；与public2分别记。 |
| keeper36848 / allocator原session35632 | 原wait均0，keeper线程退出；无原链进程遗留。 |
| 屏幕资源 | 10:34:47Z，CAS序号8167，resources=[]。 |
| file-only相机等待 | 原57720/93673/26349自然exit1，保存其等待失败；无Film/FFmpeg启动。 |
| 恢复存档 | GUI关闭后由owner完整重算原SC21 Save的SHA，仍为e044…，没有提交新Save。 |

临时**本仓** Git HTTPS guard 已由原唯一timer session5009于 **10:37:23Z** 提前恢复，原wait0；唯一restorer28292原wait0。config精确恢复为12,174 B / `a4a0343ee9360e1786e6fb71c352c9678d254968b9b75b8537a48ed8d2bb2262`，lock不存在。**无11点后台timer、无待还原操作**。恢复的是临时guard之前的配置；该基线原有master窄fetch/skipFetchAll/blob:none仍在，未声称更早所有历史设置已恢复。见[独立恢复关闭回执](C:/ck3-e04-resume-20261020-a01/r23-storage-recovery-a01/capacity-a01/VACATION-GIT-GUARD1100-INDEPENDENT-CLOSED.actual-a01.json)。

Root metadata watcher 原工具 session **90991** 已主动停止：实际叶 PID25300、created FILETIME134371374045794005，owned handle wait=0；原 `write_stdin` 工具 `03996b` 返回 **125**，这是用户度假取消，不是自然成功 0。原件 `root-a01/ROOT-METADATA-WATCHER-STOP.actual-a01.json` 保留；不再发未来 Root 许可。

## R05 后继已经做到哪里

最终源包为：

```text
C:/ck3-e04-resume-20261020-a01/r25-r05-runtime-source-a01/source
```

[DELIVERY.actual-a02.json](C:/ck3-e04-resume-20261020-a01/r25-r05-runtime-source-a01/source/DELIVERY.actual-a02.json) 绑定了最终文件、8 组有意义检查、5 个生产文件严格类型检查，原等待均 0；独立 RAM 窄审通过。**没有实际投影新 runtime，没有 prepare/profile 材料化、Game、SDK transport、native 新构建或 Film，也没有自然低补给阳性。**

关键文件必须使用最终后继：

- `project_runtime_a02.py`，不是旧 `project_runtime.py`。
- `RUNTIME-SOURCE-INDEX.actual-a02.json`，不是 a01。
- `r05_runtime_public_a02.py`，不是旧 public.py。
- `SOURCE-FREEZE.actual-a02.json`，17,463 B，SHA `ec961ec910168288f0d90a5b6aa05a115260a662c2885db2fe8e4e567eb82a66`。

OPERATOR-HANDOFF 正文仍举旧 a01 文件名；阅读时必须应用 DELIVERY 的 `handoff_filename_successors`，不能直接照抄旧例子。a02 增补了实际 Selection/runtime/prepared/client-state 的来源绑定。

后继保留原 RecordingDriver 构造器/两项 override/正常关闭，用同一个真实 GameplayBridgeService 贯通完整普通 MCP 规划器和新增三项时钟 cap、完整 Army 结构化查询。一次普通 auto_turn 的全部嵌套动作共享绝对 +24 的上限；不是另建只跑研究的逐日循环。

实机还需要：新容量与 Root 范围、合格普通 Save、新 prepare、新 PID/birth/generation、真实 loaded DLL；先只读遍历全部可操控军队寻找自然 stock<10，再对候选按原 checkpoint/Root 图审启动实际连续 Film。**全局 512 条回调/扣兵环可能在一天内覆盖**，不能保证单日不会丢；缺口、覆盖、身份变化保留 UNKNOWN。

阳性必须连上同次 callback→调用父实例→对应补给 writer→物理正向扣兵，并且 writer 入场时实际补给低于 10。净兵数减少、sampler enable ACK、控制实验 stock=0 都不能替代自然正式阳性。没有候选是 NOT_PRESENT，不是把 null 当 0。旧 R24 SHA 大小写误拒已由共享 exact-build 校验修复，4 个窄案例与7文件 strict 通过，无需重跑旧全矩阵。

## Git、知识入库与剩余发布工作

| 对象 | 本次收尾状态 |
| --- | --- |
| D 主仓 `D:/workspace/ck3_eternal_recurrence` | 原 detached HEAD `bc63851081462413d0cc6ebe62e37490707ee6a9`；原源码 clean。本次仅新增本文与闭场 JSON，不更换运行源码、不提交/推送。 |
| 唯一文档发布工作树 W | `C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree`，master，HEAD `597b81bb3989db0fc04db1be90faa51a5d8df484`；收尾时 clean、无 rebase、无 index.lock、无 Git 子进程。 |
| 三个本地提交 | CI 修复 `8c1bdc08…` → 首41文档 `4739aaa5…` → 最后4文档 `597b81bb…`。45 项 tracked payload 共 1,559,077 B。 |
| 最后远端只读观察 | 10:04Z master=`caf5ff5bf81f102b7b1cf01d7ab074eb2d2943de`；不是未来远端状态承诺。 |
| 推送结果 | 原 push PID7252 non-fast-forward / fetch-first、原等待 1；没有强推。不能写45件已经远端交付、后推送读回或官方新 CI 通过。 |
| 复原边界 | 当前无在途 rebase，**无需 abort/reset**。不丢弃三笔本地提交，不重拷45文件，不重新执行已消费发布器。 |

精确源→目标清单在：

- [MINIMAL-COPYPLAN.prepared-a03.json](C:/ck3-e04-resume-20261020-a01/r23-mechanism-publication-a01/MINIMAL-COPYPLAN.prepared-a03.json)，首41项。
- [FINAL-FOUR-ADDENDUM.prepared-a01.json](C:/ck3-e04-resume-20261020-a01/r23-mechanism-publication-a01/FINAL-FOUR-ADDENDUM.prepared-a01.json)，最终4项。
- [PUB/R05 独立关闭](C:/ck3-e04-resume-20261020-a01/r23-storage-recovery-a01/capacity-a01/VACATION-PUB-AND-R05-SOURCES-INDEPENDENT-CLOSED.actual-a01.json)，rev979，释放未消费 C7,405,568/D16,777,216，不是物理文件删除。

CAF 尾段**未执行**：11 个原始 commit/tree 对象已有精确 OID 核对来源；2 个必要 blob 尚未通过 API 读取/import。原始 import 脚本、计划和 rebase 尾段源已冻结，但**实际尾段合同/派生 pin 及有效执行卡尚不存在**，不是可直接执行的完整运行包。10:30 的旧发布卡已消费/过期，只作历史。

恢复时先新鲜核对 W 和远端，再给最小尾段新用途/有效预算：取2个必要blob、按 Git OID 验原始对象并正常 import，普通 rebase 三笔本地提交，仅首批文档更新共享 daily 与三处来源 pin，接续第二批文档，正常非强推并读回。不要 fetch 全仓历史、重下大 blob、重打215成员包或重跑完整旧测试；变更范围有新失败才扩大验证。

## 存储、回收与保护

继续统一使用[策略](../storage-retention-policy.md)与[参数](../storage-retention-policy.json) v1.0.0；容量总账由 capacity 独占写入，不能按 agent 各领一份。既往有限 C 配额例外 **449,025,409,024 B / 截至本日12:00Z** 只属历史阶段，不授权度假后自动再开工或续期。

**10:42:26Z 闭场容量快照**已读回：[docs-held 快照](C:/ck3-e04-resume-20261020-a01/r23-storage-recovery-a01/capacity-a01/VACATION-DOCS-HELD-FINAL-CAPACITY-SNAPSHOT.actual-a01.json)。Game、录制、发布、研究源码、回收与临时guard的作者/进程均已关闭；[Game独立关闭](C:/ck3-e04-resume-20261020-a01/r23-storage-recovery-a01/capacity-a01/VACATION-R0237-INDEPENDENT-CLOSED.actual-a01.json)在rev982释放C1,640,510,454/D4,194,304未消费预留，**没有物理删除信用**。

| 卷 | 实读空闲 | 同次预算结果 |
| --- | ---: | --- |
| C | 67,394,166,784 B | 有限阶段配额下，修正保守上界的有效余量+1,493,913,600 B；项目精确完整占用仍未测定。 |
| D | 21,383,356,416 B | 策略所需21,609,152,512 B，余量 **−225,796,096 B**。全卷后续增长来源未归因；**新的重型写入BLOCKED**，不降低余量或再开清理。 |

快照时只余本交接MD+JSON的D96KiB和capacity最终记录C64KiB；这两个是已获准的小型必要关闭写入，不是新执行预算。两份文件固定pin后由capacity独立核验并释放最后预留，最终入口为 [VACATION-ALL-WORK-CLOSED.actual-a01.json](C:/ck3-e04-resume-20261020-a01/r23-storage-recovery-a01/capacity-a01/VACATION-ALL-WORK-CLOSED.actual-a01.json)。闭场JSON保留写入前的真实snapshot，最终零预留以该外置独立回执为准，避免文件自哈希循环。

本轮存储中两个有价值的结论：

1. **C 盘整卷 used 只是项目占用的保守上界。** 它超出阶段配额不能证明项目真实超额。最终模型在每次 fresh 验证27个不可变系统 DriverStore 单链接文件、持有拒写/删句柄及卷快照后，仅扣除已证明的非项目分配量下界512MiB；未知字节仍留在上界，另加32MiB不确定性。没有删除/修改系统文件、没有抬高配额，也没有冒充完整项目实测占用。
2. **D Git fetch 即使指定 blob:none，仍可能产生大 pack。** 09:36 两次 graph fetch 时间窗中 pack 目录正增长260,907,008 B；其中新 pack-383fd… 与已有 pack-fa12… 的索引 OID 覆盖关系已核对。只有时间共现，未证明具体 PID 写入归因。**未手删 .git、未运行 MIDX 回收、未获得这260MB释放量**。后续如需回收，先新预算/排他，走标准 Git 维护；禁止手动删 pack、重写历史或强推。

本轮已实际回收、不能再当可读原件的代表对象：

| 操作 | 实际结果 | 原件入口 |
| --- | --- | --- |
| R24 早期部分回收 | 19,062 个文件，分配量331,689,984 B；原等待1/部分完成保真，不冒充全成功。 | `r24-d-tail-efficient-a01` 原 final/wait |
| R24 TAIL2 | 新最短前缀6,804个/90,996,736 B，完整成功/原等待0；未选1,655个保留。 | `r23-storage-recovery-a01/capacity-a01/R24-TAIL2-INDEPENDENT-CLOSED.actual-a01.json` |
| R25 旧 build-e04-a35/a36 对象 | 精确150个 .obj /258,338,816 B，原等待0、路径不存在已独核；源码、配置、编译器、EXE/DLL/PDB及未选1,289个均保留。 | `r25-d-obj-recovery-a01/OBJ-DELETE-FINAL.actual-a01.json` |

上述三次不能与之前 ledger 历史回收再次相加当新信用。`CNEXT` R0223 shadercache 3,856个/164,062,080 B **本轮删除0**：早期计划因预算不可行未执行，后继 once/plan/index 未生成；R0236 shadercache只作候选。不要把旧计划、候选或过期一次卡当成已删，也不要为度假再开清理任务。

### 最小保留集合与复核

owner 为 Root/后继负责人；**下一用途复核 2026-10-24T10:00Z，必要输入保护截至 2026-10-29T10:00Z，不自动续期**。这只保护下列实际必要对象，不保护整棵 `C:/ck3-e04-resume-20261020-a01`：

- SC21 普通恢复存档及它的普通来源/构建/保存回执；用途是未来独立 R08/R05 正常准备。
- 当前 native/OneDrive 黄色审核片，47段实际选用媒体及已固定清单/配方、35张图卡和必要声音；用途是用户审阅后的修改。无须继续保留所有工作副本。
- W 三笔本地提交与45来源、215来源载体、最终182成员源包；用途是完成正常 rebase/push和跨机器知识复核。
- R24 source-a02 的底层规则与 R25 最终 a02 运行接线源/检查；用途是下一场自然低补给实机，不保护所有旧失败源码副本。
- R0237 代表性的启动/加载绑定、未开拍事实和本次实际关闭证据；用途是防止重放未知动作或把未录制记为成功。
- 目前尚未闭合问题只留最小代表失败及关键原件；其余按 derived48h、cache7d、build/checkpoint14d、raw/delivered30d分类复核。

超过1GiB对象7日内提前复核，不能用“仍在交接”无限保留。以上保护到期是重新判断用途，不是无条件删除；删除前须读永久单资产索引、核身份/无占用/替代证据/可读性。小型 record 默认180日复核归纳。用户明确永久保留的单资产与该机器5项Workshop禁回装/唯一DACL恢复备份不因本次度假失效。

普通恢复 Save 的精确身份：

```text
C:/ck3-e04-resume-20261020-a01/r21-live-r08-a01/state-a01/profile/save games/xar_checkpoint.ck3
71,616,553 B
e044593c6d1399499b37d50dfecb1cd36c8cbb23681635339be694174e236f63
```

该 pin 来自 R0237 `prepared-a01/prepared-case.json` 的真实 saved_campaign 输入；Root 未重复读取大存档正文或另复制；现场 owner 在 GUI 关闭后已完整重算 SHA 并确认仍相同。actor31254、raw date53146872；原 common-view 的 episode_projection 为 native_campaign、one_life_settlement 为 null，native_episode_id 字段实际缺失；缺字段不补成 null，**one-life 资格未授**。R0237取消后无新增游戏日，不制造新 Save 回执。

## 接手顺序与完成标准

1. 阅读本文和闭场JSON；核本机machine_id。跨机只复用代码/机制/来源，重新核目标机路径、Steam、EXE、DLL、容量、部署与权限。使用 Python，不运行 PowerShell。
2. 优先让用户能看到当前黄色审核片，人工完整听看并记录具体内容问题；不要先再写一批制作说明。补字幕词中分页等实际发现，不为文档改动重跑CK3或全仓测试。
3. 最小完成本地45文档发布尾段：fresh远端/新容量范围，普通重基/非强推/实际读回。保持D当前运行源码与W发布树的区别。
4. 新独立场次先补 R08：根据已闭角色日/军费生产链，绑定自然结算前后的上下文、同次入账和实际钱包后验，取得连续录制及正常关闭。不要再把getter相等、0样本或静态闭合称实付。
5. 再用 R25最终a02普通完整规划器路线找自然 stock<10，取得 R05 正向物理扣兵链与连续录像。不能沿旧R0237热续、改金币/补给、造one-life、另起只研究时钟循环；全局环覆盖则保留UNKNOWN并修实际观测问题。
6. 两项证据补齐后再替换对应章节，完整编片、必要AV/字幕/画面验证、人工1×和用户签收。只有实际这些结果出现才把9/11改成11/11；整片签收另列，不能用“百分比100%”代替。

恢复后首个可承诺节点应是“实际一场完成阳性证据、连续视频与正常关闭”，不按已完成源码推算还需十几分钟。若下一场没有候选或观测覆盖，要明确报实际结果、下一项最小修复与剩余分子；不再用研究比例代替视频进度。

## 交付边界

本次只交上述docs两小件与真实收尾记录；没有完成第四集最终签收、ABC三策略、普通自动知识加载或远端45文档发布。旧失败、手动取消125、public拒绝错误与正常关闭分层保留。已关闭的外置根保持只读；新执行一律建立新的有限用途、容量与身份绑定，不重跑旧一次卡。
