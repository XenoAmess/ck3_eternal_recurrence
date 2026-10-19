# 罗贝尔首轮三十年：影片、评分器与后续任务交接

交接机器：`machine_id: xenoamess-full-tower-eb9d2c1186`，由`tools/ck3_live_run_id.py machine`实际读回。交接核对时间：`2026-10-19T00:52:11.586760Z`—`00:52:56.348057Z`，北京时间10月19日08:52。用户本轮只要求编写交接、由同事接手；没有恢复下一局或新增媒体工作的指令。

**首轮本地成片、评分图/讲解视频、永久存档和六份无声素材已经交付；网盘尚未上传。暂不开下一局。** 评分器已有实现，但当前输入只确认50%权重，不能报告完整三十年总分。旧Game本次核到退出码1，不能沿旧交接写成仍在运行或正常退出。

## 1. 接手先读

1. 本文和[交接时的新鲜只读回执](../ck3-native-ai/evidence/first30-vacation-handoff-readback-2026-10-19.json)。这是本次文件身份、容量及旧Game退出状态的依据。
2. [首轮完整交付说明](../ck3-native-ai/first30-film-scored-delivery-2026-10-19.md)和[最终交付JSON](../ck3-native-ai/evidence/first30-scored-film-delivery-2026-10-19.json)。后者LF规范化身份为15,122 B、SHA-256 `cbc761524c200f794197a550c20560353fe2b4969ba1fcd616bb6462b7822cf9`。
3. [评分设计](../ck3-native-ai/campaign-development-scoring-v1-design-2026-10-19.md)、[离线实现及本场验证](../ck3-native-ai/campaign-scoring-offline-implementation-2026-10-19.md)、[图片/视频工具](../ck3-native-ai/campaign-score-presentation-v1.md)。
4. [永久资产清单](../maintenance/user-permanent-assets.json)、[统一存储策略](../storage-retention-policy.md)及[参数](../storage-retention-policy.json)。先确认自己的machine_id；其他机器不能继承本机文件存在、进程、容量、离线或部署事实。

历史续行入口为[10月18日度假交接](2026-10-18-robert30-clean-vacation-handoff.md)和[首轮影片闭场长记录](2026-10-18-robert-first30-film-closeout.md)。它们保留历史失败与当时状态；接手以本文后继观察为准，不能回到旧running/parked指针盲目续跑。

## 2. 本机交付位置

路径缩写仅用于该machine_id：

```text
N = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep
P = N/p50-presentation-prepare01
F = N/first30-final-film01
R = N/robert30-clean-campaign01
```

| 交付物 | 本机位置与结果 |
| --- | --- |
| 完整成片 | `F/render-output/robert-first30-scored-complete09.mp4`；13,485,902,026 B；2560×1440、30 fps；7小时47分13秒。SHA `153d8b55bc90557dc92ccc5e4d6db677498ef4dd63506415e23e86a5e98896e2`。 |
| 评分总览图 | `F/campaign-score-visual01/campaign-score.png`；253,852 B；SHA `48df267827725107d694a0142400b35bf0c4cf8dbf3375f7354a6582cbc7c434`。 |
| 独立评分讲解 | `F/campaign-score-visual01/score-explanation.mp4`；60秒、4,581,281 B；SHA `ebd6905130d237c87106452581d29bb376ecf78596330dcfb4e5a068234e326e`。同一视频已各拼入成片头部、尾部。 |
| 永久存档 | `R/first30-permanent-save01/Robert-first30-raw53407320.ck3`；143,852,966 B；SHA `331dc531a33ec74990edd3385574d055a7b946427aa20de10c231a6da73bce71`。 |
| 六份无声录制素材 | `F/recording-materials-video-only01/<UUID>-video-only.mkv`；总计51,611,217,473 B；逐份路径、SHA、视频包投影见交付JSON。 |

实际手动MCP SAVE168发生在`2026-10-18T08:21:29.889769Z`—`08:21:33.862513Z`，北京时间16:21。独立副本在08:50Z验证；不要混淆保存与复制时间。当前统治者Torf、character82925，保存raw53407320，对应1096.9.23。

本次重新核到：成片、永久SAVE、评分视频及六无声素材的device/inode/大小/mtime与已交付身份一致；评分PNG只复核大小。本次没有重新哈希大视频或SAVE，没有重新解码、渲染、查看桌面或操作游戏。SHA沿既有完整验证复用，不宣称本次再次全量验证。

01:11:43Z补做小型文件属性读回，修正未提交交接草稿经JavaScript Number转换造成的device/mtime_ns舍入；最终机读回执由Python直接写出完整整数，film/SAVE再次逐字段符合固定交付JSON。此项没有读取媒体或SAVE正文。

## 3. 影片与去音轨已经完成，不要重跑

最终成片840,990帧、28,033秒；合成外层session5944实际正常0。实际QA为871样本、55页总览、27个组间接缝邻域、21张指定原尺寸关键帧、片头/片尾18个评分章节及评分PNG，独立封定在：

`F/final-scored-output-QA09/ROOT-FINAL-SCORED-OUTPUT-QA-SEAL.json`，4,194 B，SHA `6584989251d003de236ceaf959afcf64ed910e2385dfb394f451bc49c2f372f0`。

这不是7小时47分的1×完整人工观看，也不是逐源帧相同声明。无需为了接手再跑整套抽帧、听音或媒体哈希。正常动作、真实失地、继承、失败与维修画面保留，没有回档掩盖AUTO193。

用户明确放弃原声及原声检查。最终音频唯一来源是`promo/ck3_native_war_ai/assets/music/quiet-courtly-tension.wav`循环；物化输入在`P/music-input01/quiet-courtly-tension.wav`，来源Git blob及SHA见既有交付回执。不要恢复桌面声音，不再调查历史采音或做PCM相等检查。

六份无声替代的6个copy、6个header和6个EOF/SHA/视频包检查均正常0，外层session85152实际0（`b61fa1`）。`VIDEO-ONLY-COMPLETE.json`保存复制完成时原件仍保留的真实状态；后继`ORIGINAL-DELETION-MANIFEST.json`记录六份带原声原件已在`2026-10-18T22:15:56.937756Z`精确删除，外层0（`f3401c`），目录删除0。旧原始MKV现在不可读取；不能拿旧SHA当原件仍存在，也不能制造同名替代。

`P/FIRST30-SCORED09-FINALIZE-RUNBOOK04.txt`及旧prepare/execute/delete命令只作历史配方。成片09、QA09、六复制与精确删除均已消费，禁止重发；删除授权与五分钟属性epoch早已到期。旧wholegraph、grouped、fragmented、composition08、diagnostic09失败保持真实1，不因09成功改写。旧派生片按统一存储策略复核，不因失败默认永久保留。

## 4. 评分现状与下一项施工

| 指标 | 固定权重 | 当前状态 |
| --- | --- | --- |
| L领地品质 | 25% | 14.6570448606；已确认。 |
| E财政偿付 | 25% | 未闭合；缺同口径总收支、动员费用、债务/承诺。 |
| M军事保障 | 15% | 未闭合；缺完整常规军名册、有效伤害/坚韧、同帧成本。 |
| U治理稳定 | 10% | 81.8274366197；已确认玩家战争范围。 |
| D宗族发展 | 15% | 42.7912772586；已确认。 |
| H继承韧性 | 10% | 未闭合；缺同帧合法player-heir及备用资格。旧SEM169的expectation绑定旧帧，不能冒充终点证明。 |

已知50%权重的加权贡献28.50→18.2656964659，下降10.2343035341分；当前局面A区间18.2656964659—68.2656964659/100，图中向外取整18.2—68.3。不能重新归一已知项目、给未知项中点或输出一个伪精确总分。

真实1066基线是1066.9.15/raw53144328、罗贝尔31254；三十周年是1096.9.15/raw53407128。最终SAVE晚8日，且缺360个月完整采样，S30尚不可完整计算。跨代始终固定创始家族/宗族与开局分母，不因31254→40695→82925或SDK重连重置评分。

实际统治县10→2，宗族持有县8→7，宗族土地K12.675→7.3875，现金239→251.85072、传承0→2级。治理U约81.8不能掩盖严重失地：当前184549379是玩家反抗领主要求的战争，不应误算为玩家自己领国内战。全部世界历史战争也不能当玩家内战分母。

已推源码入口：

```text
ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py
ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py
ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py
ck3_autonomous_player/tools/score_ck3_campaign.py
ck3_autonomous_player/src/xar_autoplayer/campaign_score_presentation_v1.py
tools/render_campaign_score.py
```

实现提交`cf1cfa1a`，18项定向测试通过；真实CLI06外层0。影片03数值输入不改；06曾有更宽战争未知区间，07仅用已存小JSON核玩家战争列表后与03精确一致。最小重算依据在`P/scoring-draft01/player-war-scope-cache-replay-07.json`及`final-scoring-validation-07-player-wars.json`。先复用这些小投影，不为接手再扫描两份完整SAVE或导出全世界正文。

**下一项施工是补E/M/H语义适配及准确的证据来源。** 先判断现有离线投影足否；不足则按exact-build原版字段/读取者研究补只读能力，不能长期只写unknown，也不能拿不等价缓存补分。新报告使用新attempt路径，保留03/06的历史值；新结论涉及影片更新时另做明确工作包。未来获准新局后，应从开局保留固定月度采样和准点终点，不能事后用稀疏MET或约90日checkpoint拼成360月史。

## 5. 游戏、进程与休假闭场

本次对旧Game PID51028取得新的只读查询句柄，GetProcessTimes核出生FILETIME仍是`134367033244212072`；GetExitCodeProcess为**1**，退出FILETIME`134368056149718956`，对应`2026-10-18T14:00:14.971895Z`（北京时间22:00）。这是新查询句柄读回，不是从启动一直持有的原owner回执；退出原因未知，禁止称正常exit0或归因某次旧WM_CLOSE。没有向它发送任何控制动作。

旧supervisor PID229304的OpenProcess返回87，本次未证明其正常结束。旧screen租约是否有效、其他owner是否实际占场未作资格核验；没有在本次释放租约、杀进程或重启服务。接手先看任务总线当前owner和出生身份，不能拿旧PID、运行指针、closed-source tuple或CAS直接重启。旧Game不再按仍在map/paused的驻留场接回。文档任务`ck3-first30-vacation-docs-20261019`使用本机实际`Z:/.codex-task-bus`登记、poll/list，仅声明origin/master；没有领取、续租或释放screen资源。旧文档示例中的D:/workspace安装CLI本次不存在，不能直接复制该命令。

本线程保留的媒体执行均已有实际闭场；本次`collaboration.list_agents`读回所有研究子线程均completed，未再派发研究。SDKR15与离线drain的既有闭场详见首轮长记录和交付回执，子线程早期“待STOP”消息不能覆盖Root后继实际闭场。没有新AUTO、SDK、录制、MCP、桌面或Steam操作。当前Steam离线、游戏安装版本、Defender及新部署资格没有在本次重新验证；未来必要实机仍先按当时机器合同核验，不能复用旧截图。

## 6. 低优先级并行成果及剩余能力

| 工作 | 已交付 | 接手必须保留的边界 |
| --- | --- | --- |
| 继承不中断 | 常驻App/Queue持久ledger、真实pre/post与goal/title绑定，一次dispatch许可先消费、finally撤销；37 tests/28 subtests通过。见[继承UI与owner专题](../ck3-native-ai/successor-ui-unresolved-observation-2026-10-18.md)。 | 冻结Host06未采用后继改动。源码支持同resident App处理合法继承，不等于本局已部署；未来先合批部署一次，不能每死亡重启智能体。UNKNOWN动作不能重发。 |
| 民粹失地防复发 | `23350d93`，已审来源的窄拒绝与跨calc-ID识别；[P50专题](../ck3-native-ai/p50-populist-loss-prevention-2026-10-18.md)回链[P43原审计](../ck3-native-ai/p43-populist-current-source-and-natural-audit-2026-10-17.md)。 | AUTO193授独立与当时两个持有ID移出有证；不能直接说全realm少40%，也不能外推全部后续失地归因闭合。没有回档/伪装。 |
| 战争预算/建设 | P80`9032c0dc`累计预算；P83`64b241e4`共用战时建设资金门。现款全付后需留军费缓冲、未付承诺及合格应急雇佣完整报价，缺输入延期新可选工程。 | [P83资金专题](../ck3-native-ai/p83-wartime-construction-cash-and-financing-gaps-2026-10-18.md)。400g/24月是政策参数，非引擎硬限；源码存在不能说本局每次实际拦截成功。 |
| 危机雇佣 | P87`fa0d46ee`绝境消耗现款，`d535ad56`政治生存风险；重大损失/恶化/条件兵数反转/完整报价/其他义务共同约束。 | [绝境](../ck3-native-ai/p87-crisis-spend-down-source-2026-10-18.md)、[政治生存](../ck3-native-ai/p87-political-survival-crisis-profile-2026-10-18.md)。不是无条件买兵，ACK不证明可用军队或战果；未证明冻结Host采用。 |
| 取消工程、显式借款 | 有原生GUI/关系与研究落点，见[P83能力分层](../ck3-native-ai/p83-financing-capability-stages-2026-10-18.md)及[贷款读器映射](../ck3-native-ai/p83-exact12004-loan-reader-source-map-2026-10-18.md)。 | 未完成专用动作、数值退款/完整条款及项目/钱包独立后验。未到账信用为0；不要写成已实现取消建造或欠钱雇佣的完整闭环。 |
| 性能 | 已交付薄文本、序列化/复制与历史展开等源码优化及软件验证。 | 现行master不等于冻结运行源已采用。下次同策略测秒/游戏日与零日轮占比、各步骤p50/p95/总墙钟、回包字节和Driver增长；不能以少打仗、早投降换吞吐。 |
| G2 | 仍**6/8**。 | M6缺自然具名收益→终态→后续普通消费；M7缺跨ruler/seed/government及新Game精确SAVE lineage。复用普通AUTO和既有小回执采证，不加额外RPC、不强制事件、不把同场两次继承填成多seed验收。 |

以上研究线程已完成当前工作包，没有托管一项仍在跑的新研究。后续同事可以沿既有授权继续不依赖开局的源码/离线工作；不要为了“保持并行”制造新功能、重复验证或恢复现场。

## 7. 网盘、容量与保留期限

云端未交付。当前本机OneDrive目标是`C:/Users/xenoa/OneDrive/CK3-War-AI-20260923`；目录存在不证明上传。00:52Z实读C卷free17,032,228,864 B，成片复制并留20 GiB安全余量至少需34,960,738,506 B，相差17,928,509,642 B。之前已评估的项目小清理不足以填补缺口；不能删个人文件、复制到C直到低于安全余量、改OneDrive映射或把D盘本地文件说成网盘链接。后续只能基于新鲜容量和当前有效上传能力安排独立交付。

同次D卷free892,300,042,240 B。沿既有保留账本作保守读数，完整OUT仍146,027,527,160 B，其他预留621,808,745,452 B，系统增长及安全余量各21,474,836,480 B；合计free下限810,785,945,572 B。这里没有给任何新重型写入准入，也不确认其他任务现时预留不变。原Root配额例外13,950,000,000,000 B截止`2026-10-19T10:47:56.081740Z`（北京时间18:47），到期不能自动沿用。

六原片删除前已用新无声da749实际分配空间替换原25,120,079,872 B信用，shortfall0；未新增信用、未释放全球OUT。旧account03不改且不能继续声称其旧8,014项都仍在。新的工作必须读取这项替换事实并重新核自己的预算，不复用已消费的旧epoch/卡。

永久SAVE是明确用户永久例外：禁止删除其精确副本或整体删除其祖先目录，常规复核不撤销保留。其他资产执行统一策略；当前用户审阅与复算输入的有限保护复核点仍为`2026-10-25T22:18:39.090194Z`，本次不刷新期限。成品媒体默认720小时，QA/失败派生物默认48小时，小记录4320小时；到期是回收候选，要核用途与替代证据，不能一键删整个N/F。未部署自动回收器。清理前先看永久清单和已有用途，保小摘要并如实标明旧原件是否仍可读取。

## 8. 同事接手顺序与禁止误用

1. `git fetch`后`git rebase origin/master`；不要merge或force push。核machine_id，读本文和两个交付/交接JSON，先做小回执/文件属性核对，不开游戏或重跑整片。
2. 沿本地交付文件向用户提供原路径；本地成片无需重制。若处理网盘，先解决容量/可用上传通道并独立验证实际上传，未上传就保持未上传状态。
3. 优先补评分E/M/H输入与语义适配；继承、战争预算及性能工作在不冲突范围低优先级推进。已有授权无需重复询问常规可逆源码工作；明确被锁的下一局仍不执行。
4. 用户重新允许下一轮后，才使用[下一局计划](../ck3-native-ai/p50-next-robert30-v20261018-start-plan-2026-10-18.md)，合批部署已验证新代码并记录实际Host/App/Queue/Native tuple，从1066罗贝尔开始新独立场次；当前没有可直接执行的已准入新局CLI。先核实际EXE/build、Steam离线、账号/现场owner及容量，使用完整规划器和新录制/采样，不接回已退出旧Game或冒充首轮成绩。
5. 实时决策窗是**画面右侧灰色“智能体实时决策”**。后续HUD禁止节目标题“罗贝尔的30年”；左侧蓝色独立窗不是本片game capture的决策窗，且旧蓝色面板已经退役，后续新录制不得启动或包含它。评分章节/影片标题不等于实时HUD。优先MCP与原生语义，不能为了接手切屏或用OCR/鼠标读取游戏状态。
6. 战争期间军费不充裕，不开新建筑/升级/地产；危急时按真实损失、战况、兵力反转及雇佣完整报价权衡。取消退款与借款尚未闭环，先施工能力，不假装已经拿到钱。性能优化保持战争策略中立。

本任务交付提交为`c4aa763c1598b3fe4f71aff40c4f0e42512f29e7`；评分实现源提交`cf1cfa1af12b68b78e9831eaab768be9c7b1d29d`。本次文档开始同步到`707f456bd318ba1fe7bb94b3be10dd6e1c3e2326`，后继实际当前主线见Git；其他工作包新提交不能授予本场部署/实机资格。本次只做文档、JSON/链接与小型身份核对，不重跑18项评分测试或旧媒体/游戏验收。交接实际commit/push按完成后报告，不预填成功或CI通过。
